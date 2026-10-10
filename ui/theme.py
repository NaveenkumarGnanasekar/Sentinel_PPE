"""
theme.py
--------
Single source of truth for the "Sentinel" visual identity:
a dark, industrial-safety inspired theme (charcoal + safety amber +
alert red + compliant green) used across every page.
"""

BG_DARK = "#0e1420"
BG_PANEL = "#141b2b"
BG_PANEL_ALT = "#1a2338"
BORDER = "#26314a"
TEXT_PRIMARY = "#eef2f9"
TEXT_MUTED = "#8993ab"
ACCENT = "#ffb020"          # safety amber
ACCENT_SOFT = "#ffb02033"
SAFE = "#31d17b"            # compliant green
DANGER = "#ff4d4f"          # violation red
INFO = "#3ea6ff"

FONT_FAMILY = "Segoe UI, Inter, Arial, sans-serif"

STYLESHEET = f"""
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

QMainWindow {{
    background-color: {BG_DARK};
}}

/* ---------- Sidebar ---------- */
#Sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER};
}}

#SidebarLogo {{
    color: {ACCENT};
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 1px;
}}

#SidebarSubtitle {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 2px;
}}

QPushButton#NavButton {{
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 10px;
    color: {TEXT_MUTED};
    font-size: 13px;
    font-weight: 600;
    background-color: transparent;
}}
QPushButton#NavButton:hover {{
    background-color: {BG_PANEL_ALT};
    color: {TEXT_PRIMARY};
}}
QPushButton#NavButton:checked {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
}}

/* ---------- Top bar ---------- */
#TopBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}
#PageTitle {{
    font-size: 18px;
    font-weight: 700;
}}
#PageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}

QLabel#StatusPill {{
    border-radius: 10px;
    padding: 4px 12px;
    font-weight: 700;
    font-size: 11px;
}}

/* ---------- Cards ---------- */
QFrame.Card {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame.CardFlat {{
    background-color: {BG_PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}

QLabel.CardTitle {{
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QLabel.CardValue {{
    font-size: 26px;
    font-weight: 800;
}}
QLabel.CardHint {{
    color: {TEXT_MUTED};
    font-size: 11px;
}}

/* ---------- Buttons ---------- */
QPushButton.Primary {{
    background-color: {ACCENT};
    color: #17130a;
    font-weight: 700;
    border-radius: 8px;
    padding: 10px 18px;
    border: none;
}}
QPushButton.Primary:hover {{ background-color: #ffc250; }}
QPushButton.Primary:disabled {{ background-color: #4a4230; color: #8a8570; }}

QPushButton.Danger {{
    background-color: {DANGER};
    color: white;
    font-weight: 700;
    border-radius: 8px;
    padding: 10px 18px;
    border: none;
}}
QPushButton.Danger:hover {{ background-color: #ff7375; }}
QPushButton.Danger:disabled {{ background-color: #4a2c2d; color: #9a8080; }}

QPushButton.Ghost {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 9px 16px;
}}
QPushButton.Ghost:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}

/* ---------- Inputs ---------- */
QSlider::groove:horizontal {{
    height: 6px;
    background: {BG_PANEL_ALT};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 3px;
}}

QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}

QComboBox, QLineEdit {{
    background-color: {BG_PANEL_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    color: {TEXT_PRIMARY};
}}
QComboBox:hover, QLineEdit:hover {{ border-color: {ACCENT}; }}

/* ---------- Table ---------- */
QTableWidget {{
    background-color: {BG_PANEL};
    alternate-background-color: {BG_PANEL_ALT};
    gridline-color: {BORDER};
    border: 1px solid {BORDER};
    border-radius: 10px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {ACCENT};
}}
QHeaderView::section {{
    background-color: {BG_PANEL_ALT};
    color: {TEXT_MUTED};
    padding: 8px;
    border: none;
    font-weight: 700;
    font-size: 11px;
    border-bottom: 1px solid {BORDER};
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollArea {{ border: none; }}
"""
