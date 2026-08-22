"""
HawkOpsec — theme tokens and stylesheet.

Terminal/HUD identity: a single bundled typeface (JetBrains Mono) across the
whole UI, weighted for hierarchy. Flat surfaces, 1px hairlines, borderless
rows (no card boxes), no status lights, no glow, no gradients. The logo red is
reserved for danger/exposed states; a muted steel-cyan marks "secured".
"""

# ---- Color tokens (matte, low-gloss) ---------------------------------------
BG          = "#0C0E11"
SURFACE_1   = "#12151A"
SURFACE_2   = "#191D23"
SURFACE_3   = "#212630"
HAIRLINE    = "#1E2228"
HAIRLINE_HI = "#2C323A"

TEXT_HI     = "#CBD0D5"
TEXT        = "#969DA6"
TEXT_MUTED  = "#666D76"
TEXT_FAINT  = "#454C54"

RED         = "#C7333A"
RED_DIM     = "#93262B"
RED_FAINT   = "#2A1417"

CYAN        = "#5C8E96"
CYAN_DIM    = "#456C73"

AMBER       = "#AD8A4E"

# Semantic mapping
SECURED  = CYAN
EXPOSED  = RED
PARTIAL  = AMBER
NEUTRAL  = TEXT_MUTED
ACCENT   = RED   # active-mode accent, updated live by the GUI

# ---- Fonts (bundled JetBrains Mono; loaded at startup) ----------------------
MONO      = '"JetBrains Mono","DejaVu Sans Mono","monospace"'
DISPLAY_STACK = MONO
UI_STACK      = MONO
MONO_STACK    = MONO


def stylesheet() -> str:
    return f"""
* {{
    outline: none;
    font-family: {MONO};
    color: {TEXT};
}}

QWidget#Root {{ background-color: {BG}; }}
QMainWindow {{ background-color: {BG}; }}
QStackedWidget {{ background-color: {BG}; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background-color: {BG}; }}
QWidget#PanelBody {{ background-color: {BG}; }}

/* ---- Top bar -------------------------------------------------------------- */
QWidget#TopBar {{
    background-color: {SURFACE_1};
    border-bottom: 1px solid {HAIRLINE};
}}
QPushButton#Tab {{
    background-color: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 0 16px;
    min-height: 84px;
    font-size: 12px;
    font-weight: 500;
    color: {TEXT_MUTED};
}}
QPushButton#Tab:hover {{ color: {TEXT}; }}
QPushButton#Tab:checked {{
    color: {TEXT_HI};
    font-weight: 600;
    border-bottom: 2px solid {RED};
}}
QPushButton#LangBtn {{
    background: transparent; border: none;
    padding: 5px 9px; font-size: 11px; font-weight: 700;
    color: {TEXT_FAINT};
}}
QPushButton#LangBtn:hover {{ color: {TEXT}; }}
QPushButton#LangBtn:checked {{ color: {TEXT_HI}; }}
QPushButton#Uninstall {{
    background: transparent; border: 1px solid {HAIRLINE_HI};
    padding: 5px 10px; font-size: 10px; font-weight: 700;
    color: {TEXT_MUTED};
}}
QPushButton#Uninstall:hover {{ border-color: {RED_DIM}; color: {RED}; }}

/* ---- Headers -------------------------------------------------------------- */
QLabel#PanelTitle {{
    font-size: 18px;
    font-weight: 600;
    color: {TEXT_HI};
}}
QLabel#Eyebrow {{
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    color: {TEXT_FAINT};
}}
QLabel#GroupLabel {{
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 1px;
    color: {TEXT_FAINT};
}}

/* ---- Setting rows --------------------------------------------------------- */
QLabel#RowTitle {{ font-size: 13px; font-weight: 500; color: {TEXT_HI}; }}
QLabel#RowDesc  {{ font-size: 11px; color: {TEXT_MUTED}; }}
QLabel#Mono     {{ font-size: 12px; color: {TEXT}; }}
QLabel#MonoMuted{{ font-size: 11px; color: {TEXT_FAINT}; }}

/* ---- Buttons -------------------------------------------------------------- */
QPushButton#Ghost {{
    background-color: transparent;
    border: 1px solid {HAIRLINE_HI};
    padding: 7px 14px;
    font-size: 11px;
    font-weight: 500;
    color: {TEXT};
}}
QPushButton#Ghost:hover {{ border-color: {TEXT_MUTED}; color: {TEXT_HI}; }}
QPushButton#Ghost:pressed {{ background-color: {SURFACE_2}; }}
QPushButton#Ghost:disabled {{ color: {TEXT_FAINT}; border-color: {HAIRLINE}; }}

QPushButton#Danger {{
    background-color: transparent;
    border: 1px solid {RED_DIM};
    padding: 7px 14px;
    font-size: 11px;
    font-weight: 600;
    color: {RED};
}}
QPushButton#Danger:hover {{ background-color: {RED_DIM}; color: {TEXT_HI}; }}

/* ---- Combo ---------------------------------------------------------------- */
QComboBox {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    padding: 6px 10px;
    font-size: 12px;
    color: {TEXT};
}}
QComboBox:hover {{ border-color: {TEXT_MUTED}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    selection-background-color: {SURFACE_3};
    color: {TEXT};
    outline: none;
}}

/* ---- Console -------------------------------------------------------------- */
QPlainTextEdit#Console {{
    background-color: {BG};
    border: none;
    border-top: 1px solid {HAIRLINE};
    font-size: 11px;
    color: {TEXT};
    padding: 8px 20px;
}}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {HAIRLINE_HI}; min-height: 24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QToolTip {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    color: {TEXT_HI};
    padding: 4px 8px;
    font-size: 11px;
}}
"""
