"""
settings_page.py
-----------------
Deployment-level configuration: which camera to use, where the YOLO
weights / alert sound live, and the sustained-violation alert window.
Mirrors the "Model Path / Alert Sound / Confidence" configuration
block described in the original project's README.
"""

from PyQt5.QtWidgets import (
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ui import theme
from ui.widgets import SectionHeader, shadow


class SettingsPage(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(18)
        root.addWidget(SectionHeader("Settings", "Camera source, model weights and alert configuration"))

        card = QFrame()
        card.setProperty("class", "Card")
        shadow(card)
        form_wrap = QVBoxLayout(card)
        form_wrap.setContentsMargins(24, 22, 24, 22)
        form = QFormLayout()
        form.setSpacing(14)

        self.camera_index_box = QSpinBox()
        self.camera_index_box.setRange(0, 8)
        self.camera_index_box.setValue(self.controller.camera_index)
        form.addRow("Camera index:", self.camera_index_box)

        self.model_path_edit = QLineEdit(self.controller.model_path)
        browse_model_btn = QPushButton("Browse...")
        browse_model_btn.setProperty("class", "Ghost")
        browse_model_btn.clicked.connect(self._browse_model)
        model_row = QHBoxLayout()
        model_row.addWidget(self.model_path_edit)
        model_row.addWidget(browse_model_btn)
        form.addRow("YOLO weights (.pt):", model_row)

        self.sound_path_edit = QLineEdit(self.controller.alert_sound_path)
        browse_sound_btn = QPushButton("Browse...")
        browse_sound_btn.setProperty("class", "Ghost")
        browse_sound_btn.clicked.connect(self._browse_sound)
        sound_row = QHBoxLayout()
        sound_row.addWidget(self.sound_path_edit)
        sound_row.addWidget(browse_sound_btn)
        form.addRow("Alert sound (.mp3):", sound_row)

        info = QLabel(
            "Changes apply the next time monitoring is started.\n"
            "Class map (from the trained model): 1=No Vest, 2=No Helmet, "
            "3=Safety Vest, 4=Helmet."
        )
        info.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 11px;")
        info.setWordWrap(True)

        form_wrap.addLayout(form)
        form_wrap.addWidget(info)

        save_btn = QPushButton("Save Settings")
        save_btn.setProperty("class", "Primary")
        save_btn.clicked.connect(self._save)
        form_wrap.addWidget(save_btn)

        root.addWidget(card)
        root.addStretch()

    def _browse_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select YOLO weights", "", "PyTorch Weights (*.pt)")
        if path:
            self.model_path_edit.setText(path)

    def _browse_sound(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select alert sound", "", "Audio Files (*.mp3 *.wav)")
        if path:
            self.sound_path_edit.setText(path)

    def _save(self):
        self.controller.camera_index = self.camera_index_box.value()
        self.controller.model_path = self.model_path_edit.text().strip()
        self.controller.alert_sound_path = self.sound_path_edit.text().strip()
        QMessageBox.information(self, "Settings saved", "Configuration updated for the next session.")
