"""
HawkOpsec — theme tokens and stylesheet.

Two bundled typefaces with clear jobs:
  * IBM Plex Sans  — every piece of readable UI text (titles, rows, buttons)
  * JetBrains Mono — machine data only (IPs, MACs, hostnames, console, log)
Sentence-case labels, no tracked-out uppercase eyebrows, no glow, no gradients.
Matte surfaces, 1px hairlines, small 3px radii. The logo red is reserved for
danger / exposed states; a muted steel-cyan marks "secured".
"""

# ---- Color tokens (matte, low-gloss) ---------------------------------------
BG          = "#0D0F12"
SURFACE_1   = "#13161A"
SURFACE_2   = "#1A1E23"
SURFACE_3   = "#232830"
HAIRLINE    = "#1F2329"
HAIRLINE_HI = "#2E343C"

TEXT_HI     = "#E1E4E8"
TEXT        = "#A9AFB7"
TEXT_MUTED  = "#737A83"
TEXT_FAINT  = "#4C535B"

RED         = "#C7333A"
RED_DIM     = "#8E272C"
RED_FAINT   = "#241416"

CYAN        = "#6A9EA6"
CYAN_DIM    = "#456C73"

AMBER       = "#B8935A"

# Semantic mapping
SECURED  = CYAN
EXPOSED  = RED
PARTIAL  = AMBER
NEUTRAL  = TEXT_MUTED
ACCENT   = RED   # active-mode accent, updated live by the GUI

STATUS_COLOR = {"pass": CYAN, "warn": AMBER, "fail": RED,
                "info": TEXT_MUTED, "skip": TEXT_FAINT, "pending": TEXT_FAINT}

# ---- Fonts -----------------------------------------------------------------
SANS_FAMILY = "IBM Plex Sans"
MONO_FAMILY = "JetBrains Mono"
SANS = f'"{SANS_FAMILY}","Inter","Noto Sans","DejaVu Sans",sans-serif'
MONO = f'"{MONO_FAMILY}","DejaVu Sans Mono",monospace'
# legacy aliases
DISPLAY_STACK = UI_STACK = SANS
MONO_STACK = MONO


def stylesheet() -> str:
    return f"""
* {{
    outline: none;
    font-family: {SANS};
    color: {TEXT};
}}

QWidget#Root, QMainWindow, QStackedWidget {{ background-color: {BG}; }}
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
    padding: 0 14px;
    min-height: 82px;
    font-size: 14px;
    font-weight: 500;
    color: {TEXT_MUTED};
}}
QPushButton#Tab:hover {{ color: {TEXT_HI}; }}
QPushButton#Tab:checked {{
    color: {TEXT_HI};
    font-weight: 600;
    border-bottom: 2px solid {RED};
}}
QPushButton#LangBtn {{
    background: transparent; border: none;
    padding: 4px 7px; font-size: 12px; font-weight: 600;
    color: {TEXT_FAINT};
}}
QPushButton#LangBtn:hover {{ color: {TEXT}; }}
QPushButton#LangBtn:checked {{ color: {TEXT_HI}; }}
QPushButton#Uninstall {{
    background: transparent; border: 1px solid {HAIRLINE_HI}; border-radius: 3px;
    padding: 5px 11px; font-size: 12px; font-weight: 500;
    color: {TEXT_MUTED};
}}
QPushButton#Uninstall:hover {{ border-color: {RED_DIM}; color: {RED}; }}

/* ---- Headers -------------------------------------------------------------- */
QLabel#PanelTitle {{ font-size: 22px; font-weight: 600; color: {TEXT_HI}; }}
QLabel#PanelSub   {{ font-size: 13px; color: {TEXT_MUTED}; }}
QLabel#GroupLabel {{
    font-size: 13px; font-weight: 600; color: {TEXT};
    padding-top: 6px;
}}
QLabel#Hint {{ font-size: 12px; color: {TEXT_MUTED}; }}

/* ---- Setting rows --------------------------------------------------------- */
QLabel#RowTitle {{ font-size: 14px; font-weight: 500; color: {TEXT_HI}; }}
QLabel#RowDesc  {{ font-size: 12px; color: {TEXT_MUTED}; }}
QLabel#Mono     {{ font-family: {MONO}; font-size: 12px; color: {TEXT}; }}
QLabel#MonoMuted{{ font-family: {MONO}; font-size: 11px; color: {TEXT_FAINT}; }}
QLabel#CellLabel{{ font-size: 13px; color: {TEXT_MUTED}; }}
QLabel#Tag      {{ font-family: {MONO}; font-size: 11px; font-weight: 700; }}

/* ---- Verdict block -------------------------------------------------------- */
QLabel#Verdict  {{ font-size: 20px; font-weight: 600; }}

/* ---- Buttons -------------------------------------------------------------- */
QPushButton#Ghost, QPushButton#Primary {{
    background-color: transparent;
    border: 1px solid {HAIRLINE_HI};
    border-radius: 3px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
    color: {TEXT_HI};
}}
QPushButton#Ghost:hover {{ border-color: {TEXT_MUTED}; background-color: {SURFACE_1}; }}
QPushButton#Ghost:pressed {{ background-color: {SURFACE_2}; }}
QPushButton#Ghost:disabled, QPushButton#Primary:disabled {{
    color: {TEXT_FAINT}; border-color: {HAIRLINE}; background: transparent; }}

QPushButton#Primary {{ background-color: {SURFACE_3}; border-color: {SURFACE_3}; font-weight: 600; }}
QPushButton#Primary:hover {{ background-color: #2B313A; border-color: #2B313A; }}

QPushButton#Danger {{
    background-color: transparent;
    border: 1px solid {RED_DIM};
    border-radius: 3px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    color: {RED};
}}
QPushButton#Danger:hover {{ background-color: {RED_DIM}; color: {TEXT_HI}; }}

/* ---- Combo ---------------------------------------------------------------- */
QComboBox {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    border-radius: 3px;
    padding: 5px 10px;
    font-size: 13px;
    color: {TEXT_HI};
}}
QComboBox:hover {{ border-color: {TEXT_MUTED}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    selection-background-color: {SURFACE_3};
    color: {TEXT_HI};
    outline: none;
}}

/* ---- Console -------------------------------------------------------------- */
QWidget#ConsoleWrap {{ background-color: {SURFACE_1}; border-top: 1px solid {HAIRLINE}; }}
QLabel#ConsoleTitle {{ font-size: 12px; font-weight: 600; color: {TEXT_MUTED}; }}
QPlainTextEdit#Console {{
    background-color: {SURFACE_1};
    border: none;
    font-family: {MONO};
    font-size: 12px;
    color: {TEXT};
    padding: 0 18px 6px 18px;
}}
QPushButton#Link {{
    background: transparent; border: none; padding: 0 2px;
    font-size: 12px; color: {TEXT_FAINT};
}}
QPushButton#Link:hover {{ color: {TEXT}; }}

QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {HAIRLINE_HI}; min-height: 24px; border-radius: 3px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

QToolTip {{
    background-color: {SURFACE_2};
    border: 1px solid {HAIRLINE_HI};
    color: {TEXT_HI};
    padding: 4px 8px;
    font-size: 12px;
}}
QMessageBox {{ background: {SURFACE_1}; }}
"""
