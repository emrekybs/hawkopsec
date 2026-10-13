"""HawkOpsec — custom widgets (flat, hairline rows, no status lights)."""
from PyQt6.QtCore import (
    Qt, QRectF, pyqtSignal, QPropertyAnimation, pyqtProperty, QSize,
)
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QAbstractButton, QSizePolicy,
)

from . import theme as T
from .i18n import tr, mode_label


def sans(px, weight=QFont.Weight.Normal):
    f = QFont(T.SANS_FAMILY); f.setPixelSize(px); f.setWeight(weight)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return f


def _hairline(widget):
    p = QPainter(widget)
    p.setPen(QPen(QColor(T.HAIRLINE), 1))
    p.drawLine(0, widget.height() - 1, widget.width(), widget.height() - 1)
    p.end()


class ToggleSwitch(QAbstractButton):
    """Flat sliding toggle. OFF = steel, ON = cyan (or red for danger)."""

    def __init__(self, parent=None, danger=False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._on = QColor(T.RED if danger else T.CYAN)
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(120)
        self.toggled.connect(self._animate)

    def _animate(self, on):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def get_knob(self): return self._pos
    def set_knob(self, v): self._pos = v; self.update()
    knob = pyqtProperty(float, fget=get_knob, fset=set_knob)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        on = self.isChecked()
        r = QRectF(0.5, 0.5, w - 1, h - 1)
        p.setPen(QPen(QColor(self._on if on else T.HAIRLINE_HI), 1))
        p.setBrush(QBrush(QColor(self._on if on else T.SURFACE_2)))
        p.drawRoundedRect(r, h / 2, h / 2)
        kd = h - 8
        x = 4 + self._pos * (w - kd - 8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(T.TEXT_HI if on else T.TEXT_MUTED)))
        p.drawEllipse(QRectF(x, 4, kd, kd))
        p.end()


class SectionHeader(QWidget):
    """Plain title + one-line subtitle. No eyebrow, no decorative tick."""

    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0); col.setSpacing(4)
        tt = QLabel(tr(title)); tt.setObjectName("PanelTitle")
        col.addWidget(tt)
        if subtitle:
            st = QLabel(tr(subtitle)); st.setObjectName("PanelSub"); st.setWordWrap(True)
            col.addWidget(st)


class SettingRow(QWidget):
    """Borderless row: title + description left, a control right, hairline under."""
    toggled = pyqtSignal(bool)

    def __init__(self, title, desc, control=None, danger=False, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(62)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 13, 0, 13)
        lay.setSpacing(24)
        left = QVBoxLayout(); left.setSpacing(3)
        t = QLabel(tr(title)); t.setObjectName("RowTitle")
        d = QLabel(tr(desc)); d.setObjectName("RowDesc"); d.setWordWrap(True)
        left.addWidget(t); left.addWidget(d)
        lay.addLayout(left, 1)

        self.control = control
        if control == "toggle":
            self.control = ToggleSwitch(danger=danger)
            self.control.toggled.connect(self.toggled.emit)
            lay.addWidget(self.control, 0, Qt.AlignmentFlag.AlignVCenter)
        elif control is not None:
            lay.addWidget(control, 0, Qt.AlignmentFlag.AlignVCenter)

    def set_checked(self, on):
        if isinstance(self.control, ToggleSwitch):
            self.control.blockSignals(True)
            self.control.setChecked(on)
            self.control._pos = 1.0 if on else 0.0
            self.control.update()
            self.control.blockSignals(False)

    def paintEvent(self, _): _hairline(self)


class StatusCell(QWidget):
    """Readout row: sans label left, mono value right (colored by state)."""

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(34)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        self.lbl = QLabel(tr(label)); self.lbl.setObjectName("CellLabel")
        self.val = QLabel("—"); self.val.setObjectName("Mono")
        self.val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.lbl)
        lay.addStretch(1)
        lay.addWidget(self.val)

    def set_state(self, value, color, tooltip=""):
        self.val.setText(tr(value))
        self.val.setStyleSheet(f"color:{color}; font-weight:600;")
        self.setToolTip(tooltip)

    def paintEvent(self, _): _hairline(self)


class ModeCard(QAbstractButton):
    """One security profile: name + short purpose line. Active = colored frame."""

    def __init__(self, name, hint, color, parent=None):
        super().__init__(parent)
        self.name, self.hint, self.color = name, hint, color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(66)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._hover = False

    def sizeHint(self): return QSize(140, 66)
    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        active = self.isChecked()
        bg = T.SURFACE_2 if active else (T.SURFACE_1 if self._hover else T.BG)
        border = self.color if active else (T.HAIRLINE_HI if self._hover else T.HAIRLINE)
        path = QPainterPath(); path.addRoundedRect(r, 3, 3)
        p.fillPath(path, QColor(bg))
        p.setPen(QPen(QColor(border), 1)); p.drawPath(path)
        if active:
            p.fillRect(QRectF(1, 1, 3, self.height() - 2), QColor(self.color))
        p.setPen(QColor(T.TEXT_HI if active else T.TEXT))
        p.setFont(sans(14, QFont.Weight.DemiBold if active else QFont.Weight.Medium))
        p.drawText(QRectF(14, 12, self.width() - 20, 22),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, mode_label(self.name))
        p.setPen(QColor(T.TEXT_MUTED))
        p.setFont(sans(12))
        p.drawText(QRectF(14, 34, self.width() - 20, 20),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, tr(self.hint))
        p.end()


class ModeCards(QWidget):
    """Row of ModeCards. Emits the mode name on click."""
    selected = pyqtSignal(str)

    def __init__(self, modes, parent=None):
        """modes: [(name, hint, color)]"""
        super().__init__(parent)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.cards = {}
        for name, hint, color in modes:
            c = ModeCard(name, hint, color)
            c.clicked.connect(lambda _c=False, n=name: self._click(n))
            self.cards[name] = c; lay.addWidget(c)
        self._active = None

    def _click(self, name):
        self.set_active(self._active)      # don't flip until the mode is applied
        self.selected.emit(name)

    def set_active(self, name):
        self._active = name
        for n, c in self.cards.items():
            c.setChecked(n == name)


class CheckRow(QWidget):
    """Audit result row: status tag | title + detail."""
    TAGS = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "info": "INFO",
            "skip": "SKIP", "pending": "—", "running": "…"}

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(52)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 10, 0, 10); lay.setSpacing(16)
        self.tag = QLabel("—"); self.tag.setObjectName("Tag"); self.tag.setFixedWidth(64)
        self.tag.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.tag.setContentsMargins(0, 3, 0, 0)
        lay.addWidget(self.tag, 0, Qt.AlignmentFlag.AlignTop)
        col = QVBoxLayout(); col.setSpacing(2)
        self.title = QLabel(tr(title)); self.title.setObjectName("RowTitle")
        self.detail = QLabel(tr("Not run yet.")); self.detail.setObjectName("RowDesc")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        col.addWidget(self.title); col.addWidget(self.detail)
        lay.addLayout(col, 1)
        self.set_status("pending")

    def set_status(self, status, detail=None):
        color = T.STATUS_COLOR.get(status, T.TEXT_FAINT)
        self.tag.setText(tr(self.TAGS.get(status, status.upper())))
        self.tag.setStyleSheet(f"color:{color};")
        if detail is not None:
            self.detail.setText(detail)

    def paintEvent(self, _): _hairline(self)


def hline(parent=None):
    f = QWidget(parent); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{T.HAIRLINE};")
    return f
