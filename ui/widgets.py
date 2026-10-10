"""
widgets.py
----------
Small, reusable presentation widgets shared by every page:

  * StatCard        - KPI card with icon, big number and trend hint
  * DonutChart       - matplotlib donut for class distribution
  * BarChart         - matplotlib bar chart for time-of-day activity
  * shadow()          - helper to attach a soft drop shadow to a card
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout,
)

import matplotlib
matplotlib.use("QT5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ui import theme


def shadow(widget, blur=24, y_offset=6, color="#000000", alpha=140):
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    widget.setGraphicsEffect(effect)
    return effect


class StatCard(QFrame):
    """A compact KPI tile used across the Analytics and Live pages."""

    def __init__(self, title, value="0", hint="", accent=theme.ACCENT, parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        self.setStyleSheet(f"QFrame {{ border-left: 3px solid {accent}; }}")
        shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("class", "CardTitle")

        self.value_label = QLabel(str(value))
        self.value_label.setProperty("class", "CardValue")
        self.value_label.setStyleSheet(f"color: {accent};")

        self.hint_label = QLabel(hint)
        self.hint_label.setProperty("class", "CardHint")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.hint_label)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))

    def set_hint(self, hint):
        self.hint_label.setText(hint)


class _MplCanvas(FigureCanvas):
    def __init__(self, width=4, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=theme.BG_PANEL)
        super().__init__(self.fig)
        self.setStyleSheet("background: transparent;")


class DonutChart(QFrame):
    """Donut chart showing the relative share of each detected class."""

    PALETTE = [theme.DANGER, theme.SAFE, theme.ACCENT, theme.INFO,
               "#c98bff", "#ff9f68"]

    def __init__(self, title="Class Distribution", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        shadow(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 12)

        header = QLabel(title.upper())
        header.setProperty("class", "CardTitle")
        outer.addWidget(header)

        self.canvas = _MplCanvas(width=4, height=3.4)
        outer.addWidget(self.canvas)
        self.ax = self.canvas.fig.add_subplot(111)
        self.update_data({})

    def update_data(self, counts: dict):
        self.ax.clear()
        self.ax.set_facecolor(theme.BG_PANEL)
        if not counts:
            self.ax.text(0.5, 0.5, "No data yet", ha="center", va="center",
                          color=theme.TEXT_MUTED, fontsize=10, transform=self.ax.transAxes)
            self.ax.axis("off")
            self.canvas.draw_idle()
            return

        labels = list(counts.keys())
        values = list(counts.values())
        colors = [self.PALETTE[i % len(self.PALETTE)] for i in range(len(labels))]

        wedges, _ = self.ax.pie(
            values, colors=colors, startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=theme.BG_PANEL, linewidth=2),
        )
        total = sum(values)
        self.ax.text(0, 0.05, f"{total}", ha="center", va="center",
                      color=theme.TEXT_PRIMARY, fontsize=20, fontweight="bold")
        self.ax.text(0, -0.18, "detections", ha="center", va="center",
                      color=theme.TEXT_MUTED, fontsize=8)
        self.ax.legend(
            wedges, [f"{l} ({v})" for l, v in zip(labels, values)],
            loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2,
            frameon=False, fontsize=7.5, labelcolor=theme.TEXT_MUTED,
        )
        self.ax.axis("equal")
        self.canvas.fig.tight_layout()
        self.canvas.draw_idle()


class BarChart(QFrame):
    """Bar chart showing detection activity across time-of-day buckets."""

    def __init__(self, title="Activity by Time of Day", parent=None):
        super().__init__(parent)
        self.setProperty("class", "Card")
        shadow(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 12)

        header = QLabel(title.upper())
        header.setProperty("class", "CardTitle")
        outer.addWidget(header)

        self.canvas = _MplCanvas(width=5, height=3.4)
        outer.addWidget(self.canvas)
        self.ax = self.canvas.fig.add_subplot(111)
        self.update_data({})

    def update_data(self, buckets: dict):
        self.ax.clear()
        self.ax.set_facecolor(theme.BG_PANEL)
        labels = list(buckets.keys()) or ["--"]
        values = list(buckets.values()) or [0]

        bars = self.ax.bar(labels, values, color=theme.ACCENT, width=0.55, zorder=3)
        for bar in bars:
            h = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2, h, f"{int(h)}",
                          ha="center", va="bottom", color=theme.TEXT_PRIMARY, fontsize=8)

        self.ax.grid(axis="y", color=theme.BORDER, linewidth=0.6, zorder=0)
        self.ax.set_ylabel("")
        for spine in ("top", "right", "left"):
            self.ax.spines[spine].set_visible(False)
        self.ax.spines["bottom"].set_color(theme.BORDER)
        self.ax.tick_params(colors=theme.TEXT_MUTED, labelsize=8)
        self.canvas.fig.tight_layout()
        self.canvas.draw_idle()


class SectionHeader(QFrame):
    """Reusable page header: big title + muted subtitle."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 20px; font-weight: 800;")
        layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 12px;")
            layout.addWidget(s)


class LedDot(QLabel):
    """Small colored status dot (e.g. camera live/offline indicator)."""

    def __init__(self, color=theme.TEXT_MUTED, size=10, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(
            f"background-color: {color}; border-radius: {self._size // 2}px;"
        )
