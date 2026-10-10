"""
logs_page.py
------------
Tabular view of every detection stored in SQLite -- equivalent to the
original "Recent Log History" table in detection_logs.html, but with
added search, class filtering, CSV export and log clearing.
"""

import csv

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from ui import theme
from ui.widgets import SectionHeader


class LogsPage(QWidget):
    COLUMNS = ["ID", "Class ID", "Class Name", "Confidence", "Track ID", "Bounding Box", "Timestamp"]

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._all_rows = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        header_row.addWidget(SectionHeader("Detection Logs", "Full historical record of every logged detection"))
        header_row.addStretch()

        self.refresh_btn = QPushButton("\u21BB  Refresh")
        self.refresh_btn.setProperty("class", "Ghost")
        self.export_btn = QPushButton("\u2913  Export CSV")
        self.export_btn.setProperty("class", "Ghost")
        self.clear_btn = QPushButton("Clear Log")
        self.clear_btn.setProperty("class", "Danger")
        for b in (self.refresh_btn, self.export_btn, self.clear_btn):
            header_row.addWidget(b)
        root.addLayout(header_row)

        # Filter row
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by class name, track id or timestamp...")
        self.class_filter = QComboBox()
        self.class_filter.addItem("All classes")
        filter_row.addWidget(self.search_box, stretch=3)
        filter_row.addWidget(self.class_filter, stretch=1)
        root.addLayout(filter_row)

        # Table
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        root.addWidget(self.table, stretch=1)

        self.summary_label = QLabel("0 records")
        self.summary_label.setStyleSheet(f"color: {theme.TEXT_MUTED};")
        root.addWidget(self.summary_label)

        self.refresh_btn.clicked.connect(self.refresh)
        self.export_btn.clicked.connect(self.export_csv)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.search_box.textChanged.connect(self._apply_filters)
        self.class_filter.currentTextChanged.connect(self._apply_filters)

    # ------------------------------------------------------------------
    def refresh(self):
        self._all_rows = self.db.fetch_all()

        current = self.class_filter.currentText()
        self.class_filter.blockSignals(True)
        self.class_filter.clear()
        self.class_filter.addItem("All classes")
        for name in sorted({row[2] for row in self._all_rows}):
            self.class_filter.addItem(name)
        idx = self.class_filter.findText(current)
        self.class_filter.setCurrentIndex(idx if idx >= 0 else 0)
        self.class_filter.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self):
        query = self.search_box.text().strip().lower()
        class_name = self.class_filter.currentText()

        rows = self._all_rows
        if class_name != "All classes":
            rows = [r for r in rows if r[2] == class_name]
        if query:
            rows = [r for r in rows if query in " ".join(str(v).lower() for v in r)]

        self._populate_table(rows)
        self.summary_label.setText(f"{len(rows)} of {len(self._all_rows)} records")

    def _populate_table(self, rows):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            class_id = row[1]
            is_violation = class_id in (1, 2)
            for c, value in enumerate(row):
                if c == 3 and isinstance(value, float):
                    text = f"{value * 100:.1f}%"
                else:
                    text = str(value)
                item = QTableWidgetItem(text)
                if is_violation:
                    item.setForeground(Qt.red)
                self.table.setItem(r, c, item)

    # ------------------------------------------------------------------
    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export detection log", "detections.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.COLUMNS)
            writer.writerows(self._all_rows)
        QMessageBox.information(self, "Export complete", f"Log exported to:\n{path}")

    def clear_logs(self):
        confirm = QMessageBox.question(
            self, "Clear all logs",
            "This permanently deletes every detection record. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            self.db.clear()
            self.refresh()
