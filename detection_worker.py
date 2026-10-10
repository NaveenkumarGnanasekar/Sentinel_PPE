"""
detection_worker.py
--------------------
Runs the live camera capture + YOLO inference loop on a background
QThread so the PyQt UI never freezes.

The detection / tracking / alerting logic is a direct, faithful port
of the original `VideoStreamConsumer` from app1/consumers.py:

  * same confidence-threshold gate
  * same optional class-id filter
  * same greedy IoU (> 0.3) object tracker assigning incrementing track ids
  * same "sustained violation" alert rule: class_id in {1, 2}
    (No Vest / No Helmet) held by the same track id for more than
    ALERT_TIME_THRESHOLD seconds triggers a sound alert
  * same SQLite logging of every detection

Only the transport changed: instead of pushing base64 JPEG frames over
a Django Channels WebSocket, frames + detections are emitted as Qt
signals straight into the GUI.
"""

import time
from collections import deque
from datetime import datetime

import cv2
import numpy as np

try:
    import pytz
except ImportError:  # pragma: no cover - optional dependency
    pytz = None

from PyQt5.QtCore import QThread, pyqtSignal

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover
    YOLO = None

try:
    import pygame
except ImportError:  # pragma: no cover
    pygame = None

# Classes considered PPE *violations* -- mirrors the original project's
# README class map: 1 = No Vest, 2 = No Helmet.
VIOLATION_CLASS_IDS = {1, 2}
ALERT_TIME_THRESHOLD = 3  # seconds a violation must persist before alerting
IOU_MATCH_THRESHOLD = 0.3
LOCAL_TIMEZONE = "Asia/Kolkata"


class DetectionWorker(QThread):
    """Background worker: camera -> YOLO -> tracker -> UI signals -> DB."""

    frame_ready = pyqtSignal(np.ndarray, list)      # annotated RGB frame, detections
    alert_triggered = pyqtSignal(str, int)          # class_name, track_id
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    fps_updated = pyqtSignal(float)

    def __init__(self, model_path, alert_sound_path, db, camera_index=0, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.alert_sound_path = alert_sound_path
        self.db = db
        self.camera_index = camera_index

        self._running = False
        self.confidence_threshold = 0.3
        self.active_class_ids = []      # empty list == "all classes"
        self.sound_enabled = True

        self.tracked_objects = {}       # track_id -> deque[bbox]
        self.object_entry_time = {}     # track_id -> first-seen timestamp
        self.object_counter = 0

        self.model = None
        self.alert_sound = None
        self.cap = None

    # ------------------------------------------------------------------
    # Live-tunable settings (called from the UI thread; ints/floats are
    # safe to mutate without locking in CPython for this use case)
    # ------------------------------------------------------------------
    def set_confidence(self, value: float):
        self.confidence_threshold = max(0.0, min(1.0, value))

    def set_class_filter(self, class_ids):
        self.active_class_ids = list(class_ids)

    def set_sound_enabled(self, enabled: bool):
        self.sound_enabled = enabled

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _load_resources(self):
        if YOLO is None:
            raise RuntimeError(
                "The 'ultralytics' package is not installed.\n"
                "Run:  pip install ultralytics"
            )
        self.status_message.emit("Loading YOLO weights...")
        self.model = YOLO(self.model_path)

        if pygame is not None:
            try:
                pygame.mixer.init()
                self.alert_sound = pygame.mixer.Sound(self.alert_sound_path)
            except Exception as exc:  # pragma: no cover
                self.status_message.emit(f"Audio alerts disabled ({exc})")

        self.status_message.emit("Opening camera...")
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

    # ------------------------------------------------------------------
    # Tracking (ported 1:1 from consumers.py)
    # ------------------------------------------------------------------
    @staticmethod
    def _iou(box1, box2):
        x1, y1, x2, y2 = box1
        x1b, y1b, x2b, y2b = box2
        inter_x1, inter_y1 = max(x1, x1b), max(y1, y1b)
        inter_x2, inter_y2 = min(x2, x2b), min(y2, y2b)
        inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x2b - x1b) * (y2b - y1b)
        union_area = area1 + area2 - inter_area
        return inter_area / union_area if union_area else 0

    def _assign_tracking_ids(self, results):
        detections = []
        current_time = time.time()

        for result in results[0].boxes:
            x1, y1, x2, y2 = map(int, result.xyxy[0])
            confidence = result.conf[0].item()
            class_id = int(result.cls[0].item())

            if confidence <= self.confidence_threshold:
                continue
            if self.active_class_ids and class_id not in self.active_class_ids:
                continue

            bbox = (x1, y1, x2, y2)
            detection = {
                "bbox": bbox,
                "confidence": confidence,
                "class_id": class_id,
                "class_name": self.model.names[class_id],
            }

            assigned = False
            for track_id, history in list(self.tracked_objects.items()):
                if self._iou(bbox, history[-1]) > IOU_MATCH_THRESHOLD:
                    history.append(bbox)
                    detection["track_id"] = track_id
                    assigned = True
                    break

            if not assigned:
                self.object_counter += 1
                track_id = self.object_counter
                self.tracked_objects[track_id] = deque([bbox], maxlen=60)
                detection["track_id"] = track_id

            self._log_detection(detection)

            if class_id in VIOLATION_CLASS_IDS:
                track_id = detection["track_id"]
                if track_id not in self.object_entry_time:
                    self.object_entry_time[track_id] = current_time
                else:
                    duration = current_time - self.object_entry_time[track_id]
                    if duration > ALERT_TIME_THRESHOLD:
                        self.alert_triggered.emit(detection["class_name"], track_id)
                        if self.sound_enabled and self.alert_sound is not None:
                            self.alert_sound.play()
                        del self.object_entry_time[track_id]

            detections.append(detection)

        return detections

    def _log_detection(self, detection):
        if pytz is not None:
            timestamp = datetime.now(pytz.timezone(LOCAL_TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.db.insert(
            detection["class_id"],
            detection["class_name"],
            detection["confidence"],
            detection["track_id"],
            detection["bbox"],
            timestamp,
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        try:
            self._load_resources()
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            return

        self._running = True
        self.status_message.emit("Live monitoring started")

        frame_count, fps_timer = 0, time.time()

        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                self.error_occurred.emit("Failed to read from camera.")
                break

            results = self.model(frame, verbose=False)
            detections = self._assign_tracking_ids(results)

            for det in detections:
                x1, y1, x2, y2 = det["bbox"]
                is_violation = det["class_id"] in VIOLATION_CLASS_IDS
                color = (255, 60, 60) if is_violation else (60, 220, 130)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                label = f"{det['class_name']}  {det['confidence']*100:.1f}%"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                cv2.rectangle(frame, (x1, y1 - th - 12), (x1 + tw + 8, y1), color, -1)
                cv2.putText(frame, label, (x1 + 4, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (15, 15, 20), 2)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame_ready.emit(rgb_frame, detections)

            frame_count += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                self.fps_updated.emit(frame_count / elapsed)
                frame_count, fps_timer = 0, time.time()

            self.msleep(15)

        if self.cap is not None:
            self.cap.release()
        self.status_message.emit("Live monitoring stopped")

    def is_running(self):
        return self._running
