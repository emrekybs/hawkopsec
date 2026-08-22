"""HawkOpsec — custom widgets (borderless, flat, no status lights)."""
from PyQt6.QtCore import (
    Qt, QRectF, pyqtSignal, QPropertyAnimation, pyqtProperty,
)
from PyQt6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QFont
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QAbstractButton,
)

from . import theme as T
from .i18n import tr


def chamfer_path(w, h, cut, inset=0.0):
    x0, y0, x1, y1 = inset, inset, w - inset, h - inset
    p = QPainterPath()
    p.moveTo(x0, y0)
    p.lineTo(x1 - cut, y0)
    p.lineTo(x1, y0 + cut)
    p.lineTo(x1, y1)
    p.lineTo(x0 + cut, y1)
    p.lineTo(x0, y1 - cut)
    p.closeSubpath()
    return p


class ToggleSwitch(QAbstractButton):
    """Flat sliding toggle. OFF = steel, ON = cyan (or red for danger)."""

    def __init__(self, parent=None, danger=False):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(44, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._on = QColor(T.RED if danger else T.CYAN)
        self._pos = 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(110)
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
        track = QColor(self._on) if on else QColor(T.SURFACE_3)
        border = QColor(self._on) if on else QColor(T.HAIRLINE_HI)
        path = chamfer_path(w, h, 5, inset=1)
        p.fillPath(path, QBrush(track))
        p.setPen(QPen(border, 1)); p.drawPath(path)
        kw = h - 8
        x = 4 + self._pos * (w - kw - 8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(T.TEXT_HI if on else T.TEXT_MUTED)))
        p.drawRect(int(x), 4, int(kw), int(kw))
        p.end()


class SectionHeader(QWidget):
    """Eyebrow + title with a small red chamfer tick (the only signature mark)."""

    def __init__(self, eyebrow, title, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        tick = QWidget(); tick.setFixedSize(10, 34)
        tick.paintEvent = lambda e, wdg=tick: self._tick(wdg)
        lay.addWidget(tick)
        col = QVBoxLayout(); col.setSpacing(2)
        eb = QLabel(tr(eyebrow).upper()); eb.setObjectName("Eyebrow")
        tt = QLabel(tr(title)); tt.setObjectName("PanelTitle")
        col.addWidget(eb); col.addWidget(tt)
        lay.addLayout(col); lay.addStretch(1)

    @staticmethod
    def _tick(wdg):
        p = QPainter(wdg)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(Qt.PenStyle.NoPen)
        acc = QColor(getattr(T, 'ACCENT', T.RED))
        path = chamfer_path(6, wdg.height(), 3)
        p.fillPath(path, QBrush(acc))
        p.end()


class SettingRow(QWidget):
    """Borderless row: title + description left, a control right, hairline under."""
    toggled = pyqtSignal(bool)

    def __init__(self, title, desc, control=None, danger=False, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(58)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 12, 2, 12)
        lay.setSpacing(18)
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
            self.control.blockSignals(False)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(QPen(QColor(T.HAIRLINE), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class StatusCell(QWidget):
    """Borderless HUD readout: LABEL left (muted), VALUE right (colored)."""

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(34)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(10)
        self.lbl = QLabel(tr(label)); self.lbl.setObjectName("MonoMuted")
        self.val = QLabel("—"); self.val.setObjectName("Mono")
        self.val.setStyleSheet(f"color:{T.TEXT_MUTED};")
        lay.addWidget(self.lbl)
        lay.addStretch(1)
        lay.addWidget(self.val)

    def set_state(self, value, color):
        self.val.setText(tr(value))
        self.val.setStyleSheet(f"color:{color}; font-weight:600;")

    def paintEvent(self, _):
        p = QPainter(self)
        p.setPen(QPen(QColor(T.HAIRLINE), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        p.end()


class SegmentedModes(QWidget):
    """Ready-made security modes as underlined segments (no boxes)."""
    selected = pyqtSignal(str)

    def __init__(self, modes, parent=None):
        super().__init__(parent)
        self._modes = modes
        self._active = None
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, name):
        self._active = name
        self.update()

    def _seg_width(self):
        return self.width() / max(1, len(self._modes))

    def mousePressEvent(self, e):
        idx = int(e.position().x() // self._seg_width())
        idx = max(0, min(len(self._modes) - 1, idx))
        self.selected.emit(self._modes[idx][0])

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        sw = self._seg_width()
        for i, (name, color_key) in enumerate(self._modes):
            x = i * sw
            active = (name == self._active)
            col = QColor(getattr(T, color_key)) if active else QColor(T.TEXT_MUTED)
            f = QFont("JetBrains Mono"); f.setPixelSize(13)
            f.setWeight(QFont.Weight.DemiBold if active else QFont.Weight.Normal)
            f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.5)
            p.setFont(f)
            p.setPen(QColor(T.TEXT_HI) if active else col)
            p.drawText(QRectF(x, 8, sw, 24),
                       Qt.AlignmentFlag.AlignCenter, tr(name))
            # underline: red-accent for active, hairline otherwise
            p.setPen(Qt.PenStyle.NoPen)
            bar = QColor(getattr(T, color_key)) if active else QColor(T.HAIRLINE)
            p.fillRect(QRectF(x + sw * 0.18, 40, sw * 0.64,
                              3 if active else 1), QBrush(bar))
        p.end()


def hline(parent=None):
    f = QWidget(parent); f.setFixedHeight(1)
    f.setStyleSheet(f"background:{T.HAIRLINE};")
    return f
