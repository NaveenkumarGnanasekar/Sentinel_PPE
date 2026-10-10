"""
main_window.py
---------------
Top-level window: left sidebar navigation + stacked content pages
(Live Monitor / Analytics / Detection Logs / Settings), plus the
"controller" glue that owns the DetectionWorker thread and routes its
signals into whichever page needs them.
"""

import os

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from database import DetectionDB
from detection_worker import DetectionWorker
from ui import theme
from ui.pages.analytics_page import AnalyticsPage
from ui.pages.live_page import LivePage
from ui.pages.logs_page import LogsPage
from ui.pages.settings_page import SettingsPage

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "assets", "best.pt")
DEFAULT_SOUND_PATH = os.path.join(BASE_DIR, "assets", "alert.mp3")

NAV_ITEMS = [
    ("live", "\U0001F4F9  Live Monitor"),
    ("analytics", "\U0001F4CA  Analytics"),
    ("logs", "\U0001F4CB  Detection Logs"),
    ("settings", "\u2699\uFE0F  Settings"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HelmGuard \u2014 PPE Compliance Command Center")
        self.resize(1360, 840)

        # Controller state consumed by SettingsPage / LivePage
        self.camera_index = 0
        self.model_path = DEFAULT_MODEL_PATH
        self.alert_sound_path = DEFAULT_SOUND_PATH

        self.db = DetectionDB()
        self.worker = None

        self._build_ui()
        self._start_dashboard_refresh_timer()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())

        self.pages = QStackedWidget()
        self.live_page = LivePage(self)
        self.analytics_page = AnalyticsPage(self.db)
        self.logs_page = LogsPage(self.db)
        self.settings_page = SettingsPage(self)

        self.pages.addWidget(self.live_page)
        self.pages.addWidget(self.analytics_page)
        self.pages.addWidget(self.logs_page)
        self.pages.addWidget(self.settings_page)
        right.addWidget(self.pages, stretch=1)

        right_widget = QWidget()
        right_widget.setLayout(right)
        outer.addWidget(right_widget, stretch=1)

        self.nav_buttons[0].setChecked(True)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 26, 20, 20)
        layout.setSpacing(4)

        logo = QLabel("\U0001F6E1\uFE0F  HelmGuard")
        logo.setObjectName("SidebarLogo")
        subtitle = QLabel("PPE COMPLIANCE SYSTEM")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(logo)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        self.nav_buttons = []
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked, k=key: self._navigate(k))
            self.nav_group.addButton(btn)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        footer = QLabel("YOLO + PyQt5 Desktop Edition\nBuilt on the original\nDjango/Channels detection engine")
        footer.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 10px;")
        footer.setWordWrap(True)
        layout.addWidget(footer)

        return sidebar

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(64)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 24, 0)

        self.title_label = QLabel("Live Monitor")
        self.title_label.setObjectName("PageTitle")
        layout.addWidget(self.title_label)
        layout.addStretch()

        self.clock_label = QLabel()
        self.clock_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-weight: 600;")
        layout.addWidget(self.clock_label)

        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self._tick_clock)
        clock_timer.start(1000)
        self._tick_clock()

        return bar

    def _tick_clock(self):
        from datetime import datetime
        self.clock_label.setText(datetime.now().strftime("%A, %d %b %Y  \u2022  %H:%M:%S"))

    def _navigate(self, key):
        mapping = {
            "live": (0, "Live Monitor"),
            "analytics": (1, "Analytics"),
            "logs": (2, "Detection Logs"),
            "settings": (3, "Settings"),
        }
        index, title = mapping[key]
        self.pages.setCurrentIndex(index)
        self.title_label.setText(title)
        if key == "analytics":
            self.analytics_page.refresh()
        if key == "logs":
            self.logs_page.refresh()

    # ------------------------------------------------------------------
    # Dashboard auto-refresh (mirrors the original "updates every 2s")
    # ------------------------------------------------------------------
    def _start_dashboard_refresh_timer(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_current_page)
        self.refresh_timer.start(2000)

    def _refresh_current_page(self):
        current = self.pages.currentWidget()
        if current is self.analytics_page:
            self.analytics_page.refresh()
        elif current is self.logs_page:
            self.logs_page.refresh()

    # ------------------------------------------------------------------
    # Controller: DetectionWorker lifecycle (used by LivePage)
    # ------------------------------------------------------------------
    def start_monitoring(self):
        if self.worker is not None and self.worker.isRunning():
            return

        if not os.path.exists(self.model_path):
            self.live_page.show_status(f"Model not found: {self.model_path}")
            self.live_page.video_label.setText(
                f"YOLO weights not found:\n{self.model_path}\n\nSet the correct path in Settings."
            )
            return

        self.worker = DetectionWorker(
            model_path=self.model_path,
            alert_sound_path=self.alert_sound_path,
            db=self.db,
            camera_index=self.camera_index,
        )
        self.worker.set_confidence(self.live_page.confidence_slider.value() / 100)
        active = [cid for cid, cb in self.live_page.class_checks.items() if cb.isChecked()]
        self.worker.set_class_filter(active)
        self.worker.set_sound_enabled(self.live_page.sound_check.isChecked())

        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.alert_triggered.connect(self._on_alert)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.fps_updated.connect(self.live_page.update_fps)
        self.worker.status_message.connect(self.live_page.show_status)
        self.worker.finished.connect(self._on_worker_finished)

        self.live_page.clear_alert()
        self.live_page.set_running_state(True)
        self.worker.start()

    def stop_monitoring(self):
        if self.worker is not None:
            self.worker.stop()

    def _on_worker_finished(self):
        self.live_page.set_running_state(False)

    def _on_worker_error(self, message):
        self.live_page.video_label.setText(f"\u26A0 {message}")
        self.live_page.set_running_state(False)

    def _on_frame_ready(self, rgb_frame, detections):
        self.live_page.update_frame(rgb_frame)
        if detections:
            self.live_page.push_detections(detections)

    def _on_alert(self, class_name, track_id):
        self.live_page.show_alert(class_name, track_id)

    # Live-tunable setters exposed to LivePage widgets
    def set_confidence(self, value):
        if self.worker is not None:
            self.worker.set_confidence(value)

    def set_class_filter(self, class_ids):
        if self.worker is not None:
            self.worker.set_class_filter(class_ids)

    def set_sound_enabled(self, enabled):
        if self.worker is not None:
            self.worker.set_sound_enabled(enabled)

    # ------------------------------------------------------------------
    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        self.db.close()
        event.accept()
