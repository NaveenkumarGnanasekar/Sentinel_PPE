"""
analytics_page.py
------------------
Reproduces (with a very different visual language) the statistics the
original Django "Detection Log Dashboard" showed: total detections,
class counts, class distribution pie chart and detections-by-time-of-day
chart -- now as native Qt + matplotlib widgets, refreshed on a timer.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from ui import theme
from ui.widgets import BarChart, DonutChart, SectionHeader, StatCard


class AnalyticsPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(18)

        root.addWidget(SectionHeader(
            "Analytics", "Detection trends, class distribution and site activity"))

        # KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        self.card_total = StatCard("Total Detections", "0", "since log start", theme.ACCENT)
        self.card_violations = StatCard("Violations", "0", "No Vest / No Helmet", theme.DANGER)
        self.card_classes = StatCard("Classes Tracked", "0", "distinct PPE classes", theme.INFO)
        self.card_compliance = StatCard("Compliance Rate", "0%", "compliant vs. total", theme.SAFE)
        for c in (self.card_total, self.card_violations, self.card_classes, self.card_compliance):
            kpi_row.addWidget(c)
        root.addLayout(kpi_row)

        # Charts row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)
        self.donut = DonutChart("Class Distribution")
        self.bars = BarChart("Activity by Time of Day")
        charts_row.addWidget(self.donut, stretch=1)
        charts_row.addWidget(self.bars, stretch=1)
        root.addLayout(charts_row, stretch=1)

    def refresh(self):
        stats = self.db.compute_stats()

        self.card_total.set_value(stats["total_detections"])
        self.card_violations.set_value(stats["violations"])
        self.card_classes.set_value(stats["total_class_names"])

        total = stats["total_detections"]
        compliant = total - stats["violations"]
        rate = int((compliant / total) * 100) if total else 0
        self.card_compliance.set_value(f"{rate}%")

        self.donut.update_data(dict(stats["most_frequent"]))
        self.bars.update_data(stats["time_buckets"])
