"""HawkOpsec — main window and application entry point."""
import os, sys, time, json

from PyQt6.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QPlainTextEdit, QButtonGroup, QMessageBox,
    QFrame,
)

from . import theme as T
from . import backend
from .i18n import tr, lang, set_lang, load_lang
from .panels import (
    DashboardPanel, NetworkPanel, IdentityPanel, HardeningPanel, TracesPanel,
    ActivityPanel, MODE_DESC,
)


def _base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(name):
    for p in (os.path.join("/usr/local/share/hawkopsec", name),
              os.path.join(_base_dir(), "..", "assets", name),
              os.path.join(_base_dir(), "assets", name)):
        if os.path.exists(p):
            return p
    return ""


def load_fonts():
    for d in (os.path.join("/usr/local/share/hawkopsec/fonts"),
              os.path.join(_base_dir(), "..", "assets", "fonts"),
              os.path.join(_base_dir(), "assets", "fonts")):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith(".ttf"):
                    QFontDatabase.addApplicationFont(os.path.join(d, f))
            return


# ---- ready-made security modes (verb sequences applied after a reset) ------ #
def mode_sequence(name):
    """Each mode is a full profile applied in one tap (after a reset)."""
    SECURE = [("Kernel hardening", "harden-sysctl"), ("Firewall", "firewall-on"),
              ("DNS-over-TLS", "dns-set", "quad9"), ("IPv6 off", "ipv6-off"),
              ("Crash reporting off", "telemetry-off"),
              ("journald volatile", "journald-volatile")]
    PUBLIC   = SECURE + [("Persistent MAC", "nm-mac-on"), ("Bluetooth off", "bluetooth-off")]
    HARDENED = PUBLIC + [("Machine-ID", "machineid-random"), ("Hostname", "hostname-random"),
                         ("Swap off", "swap-off"), ("USB lockdown", "usb-lock")]
    GHOST    = HARDENED + [("Timezone UTC", "tz-utc"), ("Tor routing", "tor-on")]
    PARANOID = GHOST + [("RAM wipe", "ramwipe-on")]
    table = {"BASELINE": [], "SECURE": SECURE, "PUBLIC": PUBLIC,
             "HARDENED": HARDENED, "GHOST": GHOST, "PARANOID": PARANOID}
    seq = list(table[name])
    if name in ("PUBLIC", "HARDENED", "GHOST", "PARANOID"):
        for i in backend.interfaces():
            seq.append((f"MAC {i['name']}", "mac-random", i["name"]))
    return seq


class _Signals(QObject):
    done = pyqtSignal(str, int, str)


class Worker(QRunnable):
    def __init__(self, label, fn):
        super().__init__(); self.label, self.fn = label, fn
        self.signals = _Signals()

    def run(self):
        try:
            rc, out = self.fn()
        except Exception as e:
            rc, out = 1, str(e)
        self.signals.done.emit(self.label, int(rc), str(out))


MODE_COLOR = {"BASELINE": T.TEXT_MUTED, "SECURE": T.CYAN, "PUBLIC": T.CYAN,
              "HARDENED": T.AMBER, "GHOST": T.RED, "PARANOID": T.RED}


NAV = [("DASHBOARD", DashboardPanel), ("NETWORK", NetworkPanel),
       ("IDENTITY", IdentityPanel), ("HARDENING", HardeningPanel),
       ("TRACES", TracesPanel), ("ACTIVITY", ActivityPanel)]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HawkOpsec")
        self.setMinimumSize(980, 700)
        self.pool = QThreadPool.globalInstance()
        self._queue = []
        self._logo = asset_path("hawkopsec.png")
        icon = asset_path("hawkopsec_icon.png") or self._logo
        if icon: self.setWindowIcon(QIcon(icon))

        self.setStyleSheet(T.stylesheet())
        self._build_central()
        self.log(tr("HawkOpsec ready. Actions request elevation via polkit."), "info")
        self.refresh_now()
        self.timer = QTimer(self); self.timer.setInterval(4000)
        self.timer.timeout.connect(self.refresh_now); self.timer.start()

    def _build_central(self):
        root = QWidget(); root.setObjectName("Root")
        rv = QVBoxLayout(root); rv.setContentsMargins(0, 0, 0, 0); rv.setSpacing(0)
        rv.addWidget(self._topbar(self._logo))
        self.stack = QStackedWidget(); self.panels = []
        for _, cls in NAV:
            p = cls(self); self.panels.append(p); self.stack.addWidget(p)
        rv.addWidget(self.stack, 1)
        rv.addWidget(self._console())
        self.setCentralWidget(root)
        self._mode_now = None            # force accent re-apply

    def _relang(self, l):
        set_lang(l)
        self._build_central()
        self.log(tr("HawkOpsec ready. Actions request elevation via polkit."), "info")
        self.refresh_now()

    # -- top bar ----------------------------------------------------------- #
    def _topbar(self, logo):
        wrap = QWidget()
        wv = QVBoxLayout(wrap); wv.setContentsMargins(0, 0, 0, 0); wv.setSpacing(0)
        self.top_accent = QFrame(); self.top_accent.setFixedHeight(3)
        self.top_accent.setStyleSheet(f"background:{T.TEXT_MUTED};")
        wv.addWidget(self.top_accent)

        bar = QWidget(); bar.setObjectName("TopBar"); bar.setFixedHeight(84)
        lay = QHBoxLayout(bar); lay.setContentsMargins(0, 0, 22, 0); lay.setSpacing(0)

        mark = asset_path("hawkopsec_mark.png") or logo
        if mark:
            pic = QLabel()
            pic.setPixmap(QPixmap(mark).scaledToHeight(
                84, Qt.TransformationMode.SmoothTransformation))
            pic.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            lay.addWidget(pic, 0, Qt.AlignmentFlag.AlignVCenter)
            lay.addSpacing(20)
        lay.addStretch(1)

        self.nav_group = QButtonGroup(self); self.nav_group.setExclusive(True)
        for i, (name, _) in enumerate(NAV):
            b = QPushButton(tr(name)); b.setObjectName("Tab"); b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _c, idx=i: self._go(idx))
            self.nav_group.addButton(b, i); lay.addWidget(b)
        self.nav_group.button(0).setChecked(True)
        lay.addStretch(1)

        self.lang_btns = {}
        for code in ("EN", "TR"):
            lb = QPushButton(code); lb.setObjectName("LangBtn"); lb.setCheckable(True)
            lb.setCursor(Qt.CursorShape.PointingHandCursor)
            lb.clicked.connect(lambda _c, c=code: self._relang(c.lower()))
            self.lang_btns[code] = lb; lay.addWidget(lb)
        self.lang_btns["TR" if lang() == "tr" else "EN"].setChecked(True)

        un = QPushButton(tr("UNINSTALL")); un.setObjectName("Uninstall")
        un.setCursor(Qt.CursorShape.PointingHandCursor)
        un.clicked.connect(self._uninstall)
        lay.addSpacing(8); lay.addWidget(un)
        wv.addWidget(bar)
        return wrap

    def _uninstall(self):
        import os
        if not self.confirm(tr("Uninstall HawkOpsec"),
                tr("Revert all changes and remove HawkOpsec completely? The app will close.")):
            return
        cand = ["/usr/local/lib/hawkopsec/uninstall",
                os.path.join(_base_dir(), "..", "packaging", "uninstall.sh")]
        script = next((c for c in cand if os.path.exists(c)), None)
        if not script:
            self.log("uninstall script not found", "err"); return
        self.log(tr("Uninstalling — reverting changes and removing files …"), "info")
        self._dispatch(tr("UNINSTALL"), lambda: backend.run_pkexec(script),
                       on_done=lambda rc, out: QApplication.quit())

    def _set_accent(self, color):
        T.ACCENT = color
        self.top_accent.setStyleSheet(f"background:{color};")
        # recolor the active-tab underline; repaint pulls the new tick color too
        self.setStyleSheet(T.stylesheet()
                           + f"\nQPushButton#Tab:checked{{border-bottom:2px solid {color};}}")

    def _go(self, idx):
        self.stack.setCurrentIndex(idx); self.refresh_now()

    # -- console ----------------------------------------------------------- #
    def _console(self):
        self.console = QPlainTextEdit(); self.console.setObjectName("Console")
        self.console.setReadOnly(True); self.console.setFixedHeight(132)
        return self.console

    def log(self, msg, level="info"):
        color = {"ok": T.CYAN, "err": T.RED, "info": T.TEXT_MUTED}.get(level, T.TEXT)
        ts = time.strftime("%H:%M:%S")
        self.console.appendHtml(
            f'<span style="color:{T.TEXT_FAINT}">{ts}</span> '
            f'<span style="color:{color}">{msg}</span>')
        sb = self.console.verticalScrollBar(); sb.setValue(sb.maximum())

    # -- dispatch ---------------------------------------------------------- #
    def _dispatch(self, label, fn, on_done=None):
        self.log(f"▶ {tr(label)} …", "info")
        w = Worker(label, fn)
        w.signals.done.connect(
            lambda l, rc, out, cb=on_done: self._finished(l, rc, out, cb))
        self.pool.start(w)

    def _finished(self, label, rc, out, on_done):
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        self.log((f"✔ {tr(label)} — " if rc == 0 else f"✗ {tr(label)} — ") + tail,
                 "ok" if rc == 0 else "err")
        self.refresh_now()
        if on_done: on_done(rc, out)

    def run_action(self, label, verb, *args):
        self._dispatch(label, lambda: backend.run_priv(verb, *args))

    def run_callable(self, label, fn, on_done=None):
        self._dispatch(label, fn, on_done)

    def run_sequence(self, seq, on_complete=None):
        self._queue = list(seq)
        self._seq_done = on_complete
        self._seq_next()

    def _seq_next(self, *_):
        if not self._queue:
            self.log("✔ " + tr("Done."), "ok"); self.refresh_now()
            cb = getattr(self, "_seq_done", None)
            if cb:
                self._seq_done = None; cb()
            return
        step = self._queue.pop(0)
        label, verb, args = step[0], step[1], step[2:]
        self._dispatch(label, lambda v=verb, a=args: backend.run_priv(v, *a),
                       on_done=self._seq_next)

    # -- modes ------------------------------------------------------------- #
    def apply_mode(self, name):
        if name != "BASELINE" and not self.confirm(
                f"{tr('Apply')} {tr(name)}",
                tr(MODE_DESC.get(name, "")) + "\n\n" + tr("Reset to baseline and apply now?")):
            self.refresh_now(); return
        seq = [("Baseline reset", "reset-all")]
        seq += mode_sequence(name)
        seq.append(("Mode", "set-mode", name))
        self.log((f"▶ {tr(name)} modu uygulanıyor …" if lang()=="tr"
                  else f"▶ Applying {name} mode …"), "info")
        self.run_sequence(seq, on_complete=self.check_ip)

    # -- IP check ---------------------------------------------------------- #
    def check_ip(self):
        self.log("▶ " + tr("Checking exit IP …"), "info")
        def job():
            return 0, json.dumps(backend.tor_check())
        def done(rc, out):
            res = json.loads(out); dash = self.panels[0]
            if "error" in res:
                dash.set_ip("UNREACHABLE", T.PARTIAL)
                self.log(f"✗ {tr('IP check failed')} — " + res["error"], "err")
            else:
                is_tor = res.get("is_tor")
                dash.set_ip(res.get("ip", "?"), T.SECURED if is_tor else T.EXPOSED)
                self.log(f"✔ {tr('Exit IP')} {res.get('ip')} — "
                         + (tr("Tor confirmed") if is_tor else tr("NOT via Tor")),
                         "ok" if is_tor else "err")
        self._dispatch("IP check", job, on_done=done)

    # -- helpers ----------------------------------------------------------- #
    def confirm(self, title, text):
        box = QMessageBox(self); box.setWindowTitle(title); box.setText(text)
        box.setIcon(QMessageBox.Icon.NoIcon)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        box.setStyleSheet(
            f"QMessageBox{{background:{T.SURFACE_1};}}QLabel{{color:{T.TEXT};}}"
            f"QPushButton{{background:{T.SURFACE_2};color:{T.TEXT};"
            f"border:1px solid {T.HAIRLINE_HI};padding:6px 18px;}}"
            f"QPushButton:hover{{border-color:{T.TEXT_MUTED};}}")
        return box.exec() == QMessageBox.StandardButton.Yes

    def refresh_now(self):
        st = backend.read_state()
        for p in self.panels: p.refresh(st)
        mode = st.get("mode", "BASELINE")
        if mode != getattr(self, "_mode_now", None):
            self._mode_now = mode
            self._set_accent(MODE_COLOR.get(mode, T.TEXT_MUTED))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("HawkOpsec")
    load_lang()
    load_fonts()
    app.setFont(QFont("JetBrains Mono", 10))
    win = MainWindow(); win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
