"""
main.py
-------
Entry point for the Sentinel PPE Compliance Command Center
(PyQt5 desktop rebuild of the original Django/Channels PPE dashboard).

Run with:
    python main.py
"""

import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    app.setApplicationName("Sentinel PPE Dashboard")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
