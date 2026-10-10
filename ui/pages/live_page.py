"""
live_page.py
------------
The "Live Monitor" page: real-time camera feed with YOLO overlays,
tunable confidence / class filters (mirrors the original web UI's
set_class_ids / set_confidence_threshold controls) and a rolling
live-event feed of the most recent detections.
"""

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QSlider, QVBoxLayout, QWidget, QSpacerItem,
)

from ui import theme
from ui.widgets import LedDot, SectionHeader, shadow

CLASS_MAP = {
    1: ("No Vest", theme.DANGER),
    2: ("No Helmet", theme.DANGER),
    3: ("Safety Vest", theme.SAFE),
    4: ("Shoes", theme.SAFE),
}


class LivePage(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self._wire_events()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(20)

        root.addWidget(self._build_video_panel(), stretch=3)
        root.addWidget(self._build_side_panel(), stretch=1)

    # ------------------------------------------------------------------
    def _build_video_panel(self):
        panel = QVBoxLayout()
        panel.setSpacing(14)

        header = QHBoxLayout()
        header.addWidget(SectionHeader(
            "Live Monitor", "Real-time YOLO PPE detection feed"))
        header.addStretch()

        self.led = LedDot(theme.TEXT_MUTED)
        self.status_label = QLabel("OFFLINE")
        self.status_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: 700; font-size: 11px;")
        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        status_box.addWidget(self.led)
        status_box.addWidget(self.status_label)
        header.addLayout(status_box)
        panel.addLayout(header)

        # Video surface
        video_frame = QFrame()
        video_frame.setProperty("class", "Card")
        shadow(video_frame)
        video_layout = QVBoxLayout(video_frame)
        video_layout.setContentsMargins(4, 4, 4, 4)

        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 420)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            f"background-color: #05070c; border-radius: 12px; color: {theme.TEXT_MUTED};"
        )
        self.video_label.setText("Camera feed will appear here\nPress \u25B6 Start Monitoring")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        video_layout.addWidget(self.video_label)
        panel.addWidget(video_frame, stretch=1)

        # Bottom control strip
        controls = QFrame()
        controls.setProperty("class", "CardFlat")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(16, 12, 16, 12)

        self.start_btn = QPushButton("\u25B6  Start Monitoring")
        self.start_btn.setProperty("class", "Primary")
        self.stop_btn = QPushButton("\u25A0  Stop")
        self.stop_btn.setProperty("class", "Danger")
        self.stop_btn.setEnabled(False)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: 600;")

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.fps_label)
        panel.addWidget(controls)

        wrapper = QWidget()
        wrapper.setLayout(panel)
        return wrapper

    # ------------------------------------------------------------------
    def _build_side_panel(self):
        panel = QVBoxLayout()
        panel.setSpacing(16)
        panel.addSpacing(38)  # align with video header

        # --- Detection settings card ---
        settings_card = QFrame()
        settings_card.setProperty("class", "Card")
        shadow(settings_card)
        s_layout = QVBoxLayout(settings_card)
        s_layout.setContentsMargins(18, 16, 18, 16)
        s_layout.setSpacing(10)

        s_title = QLabel("DETECTION SETTINGS")
        s_title.setProperty("class", "CardTitle")
        s_layout.addWidget(s_title)

        self.confidence_value_label = QLabel("Confidence threshold: 30%")
        self.confidence_value_label.setStyleSheet("font-weight: 600;")
        s_layout.addWidget(self.confidence_value_label)

        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(5, 95)
        self.confidence_slider.setValue(30)
        s_layout.addWidget(self.confidence_slider)

        s_layout.addWidget(QLabel("Filter classes:"))
        self.class_checks = {}
        for class_id, (name, color) in CLASS_MAP.items():
            cb = QCheckBox(f"{name}")
            cb.setChecked(True)
            cb.setStyleSheet(f"QCheckBox::indicator {{ border: 1px solid {color}; }}")
            self.class_checks[class_id] = cb
            s_layout.addWidget(cb)

        self.sound_check = QCheckBox("Enable audio alert")
        self.sound_check.setChecked(True)
        s_layout.addWidget(self.sound_check)

        panel.addWidget(settings_card)

        # --- Alert banner ---
        self.alert_banner = QFrame()
        self.alert_banner.setProperty("class", "Card")
        self.alert_banner.setStyleSheet(
            f"QFrame {{ border: 1px solid {theme.DANGER}; background-color: #2a1416; }}"
        )
        self.alert_banner.setVisible(False)
        ab_layout = QVBoxLayout(self.alert_banner)
        self.alert_text = QLabel("")
        self.alert_text.setStyleSheet(f"color: {theme.DANGER}; font-weight: 700;")
        self.alert_text.setWordWrap(True)
        ab_layout.addWidget(QLabel("\u26A0  SAFETY ALERT"))
        ab_layout.addWidget(self.alert_text)
        panel.addWidget(self.alert_banner)

        # --- Live feed list ---
        feed_card = QFrame()
        feed_card.setProperty("class", "Card")
        shadow(feed_card)
        f_layout = QVBoxLayout(feed_card)
        f_layout.setContentsMargins(18, 16, 18, 16)
        f_title = QLabel("LIVE EVENT FEED")
        f_title.setProperty("class", "CardTitle")
        f_layout.addWidget(f_title)

        self.event_list = QListWidget()
        self.event_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; }} "
            f"QListWidget::item {{ padding: 6px 2px; border-bottom: 1px solid {theme.BORDER}; }}"
        )
        f_layout.addWidget(self.event_list)
        panel.addWidget(feed_card, stretch=1)

        wrapper = QWidget()
        wrapper.setLayout(panel)
        wrapper.setMaximumWidth(340)
        return wrapper

    # ------------------------------------------------------------------
    def _wire_events(self):
        self.start_btn.clicked.connect(self.controller.start_monitoring)
        self.stop_btn.clicked.connect(self.controller.stop_monitoring)
        self.confidence_slider.valueChanged.connect(self._on_confidence_changed)
        for cb in self.class_checks.values():
            cb.stateChanged.connect(self._on_class_filter_changed)
        self.sound_check.stateChanged.connect(
            lambda state: self.controller.set_sound_enabled(state == Qt.Checked)
        )

    def _on_confidence_changed(self, value):
        pct = value / 100
        self.confidence_value_label.setText(f"Confidence threshold: {value}%")
        self.controller.set_confidence(pct)

    def _on_class_filter_changed(self):
        active = [cid for cid, cb in self.class_checks.items() if cb.isChecked()]
        # empty selection == show nothing; controller decides "all" vs subset
        self.controller.set_class_filter(active)

    # ------------------------------------------------------------------
    # Slots called by MainWindow / controller
    # ------------------------------------------------------------------
    def set_running_state(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.led.set_color(theme.SAFE if running else theme.TEXT_MUTED)
        self.status_label.setText("LIVE" if running else "OFFLINE")
        self.status_label.setStyleSheet(
            f"color: {theme.SAFE if running else theme.TEXT_MUTED}; font-weight: 700; font-size: 11px;"
        )
        if not running:
            self.video_label.setText("Camera feed will appear here\nPress \u25B6 Start Monitoring")
            self.video_label.setPixmap(QPixmap())
            self.fps_label.setText("FPS: --")

    def update_frame(self, rgb_frame):
        h, w, ch = rgb_frame.shape
        qimg = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    def update_fps(self, fps):
        self.fps_label.setText(f"FPS: {fps:.1f}")

    def push_detections(self, detections):
        for det in detections:
            ts = datetime.now().strftime("%H:%M:%S")
            color = theme.DANGER if det["class_id"] in (1, 2) else theme.SAFE
            item = QListWidgetItem(
                f"[{ts}]  {det['class_name']}  \u2022  {det['confidence']*100:.0f}%  \u2022  ID {det['track_id']}"
            )
            item.setForeground(Qt.white)
            self.event_list.insertItem(0, item)
        while self.event_list.count() > 60:
            self.event_list.takeItem(self.event_list.count() - 1)

    def show_alert(self, class_name, track_id):
        self.alert_text.setText(
            f"{class_name} sustained for object #{track_id} beyond the safe time limit."
        )
        self.alert_banner.setVisible(True)

    def clear_alert(self):
        self.alert_banner.setVisible(False)

    def show_status(self, message):
        self.status_label.setToolTip(message)
