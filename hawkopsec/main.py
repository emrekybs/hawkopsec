"""HawkOpsec — main window and application entry point."""
import html, os, shutil, sys, time, json

from PyQt6.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QPlainTextEdit, QButtonGroup, QMessageBox,
    QFrame,
)

from . import theme as T
from . import backend
from .i18n import tr, lang, set_lang, load_lang, mode_label
from .panels import (
    DashboardPanel, NetworkPanel, IdentityPanel, HardeningPanel, TracesPanel,
    ActivityPanel, AuditPanel, MODE_DESC,
)
from . import audit


def _base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(name):
    for p in (os.path.join(_base_dir(), "assets", name),
              os.path.join("/usr/local/share/hawkopsec", name)):
        if os.path.exists(p):
            return p
    return ""


def load_fonts():
    for d in (os.path.join(_base_dir(), "assets", "fonts"),
              "/usr/local/share/hawkopsec/fonts"):
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
    GHOST    = HARDENED + [("Timezone UTC", "tz-utc"), ("Disable webcam", "webcam-off"),
                           ("Tor routing", "tor-on")]
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


NAV = [("Overview", DashboardPanel), ("Network", NetworkPanel),
       ("Identity", IdentityPanel), ("Hardening", HardeningPanel),
       ("Leak test", AuditPanel), ("Traces", TracesPanel), ("Activity", ActivityPanel)]
AUDIT_IDX = 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HawkOpsec")
        self.setMinimumSize(1000, 700)
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
        if not backend.system_integrated():
            QTimer.singleShot(400, self._offer_setup)

    # -- first run (pip install) ------------------------------------------ #
    def _offer_setup(self):
        self.log(tr("System helper not installed — privileged actions are disabled."), "warn")
        if not self.confirm(tr("Finish installation"),
                tr("HawkOpsec needs to install its root helper, polkit policy and menu "
                   "entry once (same as: sudo hawkopsec-setup). Do it now?")):
            return
        launcher = shutil.which("hawkopsec") or ""
        self._dispatch("System setup", lambda: backend.run_setup(launcher))

    def clear_clipboard(self, quiet=False):
        cb = QApplication.clipboard()
        if cb is not None:
            cb.clear(cb.Mode.Clipboard)
            if cb.supportsSelection(): cb.clear(cb.Mode.Selection)
        if quiet:
            backend.clear_clipboard()
        else:
            self.run_callable("Clear clipboard", backend.clear_clipboard)

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
        self.top_accent = QFrame(); self.top_accent.setFixedHeight(2)
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
            lay.addSpacing(18)

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

        un = QPushButton(tr("Uninstall")); un.setObjectName("Uninstall")
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
                os.path.join(_base_dir(), "data", "uninstall.sh")]
        script = next((c for c in cand if os.path.exists(c)), None)
        if not script:
            self.log("uninstall script not found", "err"); return
        self.log(tr("Uninstalling — reverting changes and removing files …"), "info")
        self._dispatch("Uninstall", lambda: backend.run_pkexec(script),
                       on_done=lambda rc, out: QApplication.quit())

    def _set_accent(self, color):
        T.ACCENT = color
        self.top_accent.setStyleSheet(f"background:{color};")
        # recolor the active-tab underline; repaint pulls the new tick color too
        self.setStyleSheet(T.stylesheet()
                           + f"\nQPushButton#Tab:checked{{border-bottom:2px solid {color};}}")

    def _go(self, idx):
        self.stack.setCurrentIndex(idx)
        self.nav_group.button(idx).setChecked(True)
        self.refresh_now()

    def open_audit(self, run=False):
        self._go(AUDIT_IDX)
        if run: self.panels[AUDIT_IDX].run()

    # -- console ----------------------------------------------------------- #
    def _console(self):
        wrap = QWidget(); wrap.setObjectName("ConsoleWrap")
        v = QVBoxLayout(wrap); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        head = QHBoxLayout(); head.setContentsMargins(18, 8, 14, 4)
        t = QLabel(tr("Console")); t.setObjectName("ConsoleTitle")
        head.addWidget(t); head.addStretch(1)
        clr = QPushButton(tr("Clear")); clr.setObjectName("Link")
        clr.setCursor(Qt.CursorShape.PointingHandCursor)
        head.addWidget(clr)
        v.addLayout(head)
        self.console = QPlainTextEdit(); self.console.setObjectName("Console")
        self.console.setReadOnly(True); self.console.setFixedHeight(100)
        clr.clicked.connect(self.console.clear)
        v.addWidget(self.console)
        return wrap

    def log(self, msg, level="info"):
        color = {"ok": T.CYAN, "err": T.RED, "warn": T.AMBER,
                 "info": T.TEXT_MUTED}.get(level, T.TEXT)
        ts = time.strftime("%H:%M:%S")
        # escape! raw '<urlopen error …>' used to be eaten as an HTML tag
        self.console.appendHtml(
            f'<span style="color:{T.TEXT_FAINT}">{ts}</span>&nbsp;&nbsp;'
            f'<span style="color:{color}">{html.escape(str(msg))}</span>')
        sb = self.console.verticalScrollBar(); sb.setValue(sb.maximum())

    # -- dispatch ---------------------------------------------------------- #
    def _dispatch(self, label, fn, on_done=None, quiet=False):
        self.log(f"› {tr(label)} …", "info")
        w = Worker(label, fn)
        w.signals.done.connect(
            lambda l, rc, out, cb=on_done, q=quiet: self._finished(l, rc, out, cb, q))
        self.pool.start(w)

    def _finished(self, label, rc, out, on_done, quiet=False):
        if not quiet:
            tail = out.strip().splitlines()[-1] if out.strip() else ""
            if tail.startswith("[") and "] " in tail[:12]:
                tail = tail.split("] ", 1)[1]          # drop helper's own timestamp
            self.log((f"✓ {tr(label)}" if rc == 0 else f"✗ {tr(label)}")
                     + (f" — {tail}" if tail else ""), "ok" if rc == 0 else "err")
        self.refresh_now()
        if on_done: on_done(rc, out)

    def run_action(self, label, verb, *args, on_done=None, then_check_ip=False):
        cb = on_done
        if then_check_ip:
            cb = lambda rc, out: (rc == 0 and self.check_ip())
        self._dispatch(label, lambda: backend.run_priv(verb, *args), cb)

    def run_callable(self, label, fn, on_done=None, quiet=False):
        self._dispatch(label, fn, on_done, quiet)

    def run_sequence(self, seq, on_complete=None):
        self._queue = list(seq)
        self._seq_done = on_complete
        self._seq_next()

    def _seq_next(self, *_):
        if not self._queue:
            self.log("✓ " + tr("Done."), "ok"); self.refresh_now()
            cb = getattr(self, "_seq_done", None)
            if cb:
                self._seq_done = None; cb()
            return
        step = self._queue.pop(0)
        label, verb, args = step[0], step[1], step[2:]
        self._dispatch(label, lambda v=verb, a=args: backend.run_priv(v, *a),
                       on_done=self._seq_next)

    # -- modes ------------------------------------------------------------- #
    def apply_mode(self, name, confirm=True):
        if confirm and not self.confirm(
                f"{tr('Apply')}: {mode_label(name)}",
                tr(MODE_DESC.get(name, "")) + "\n\n" + tr("Reset to baseline and apply now?")):
            self.refresh_now(); return
        seq = [("Baseline reset", "reset-all")]
        seq += mode_sequence(name)
        seq.append(("Mode", "set-mode", name))
        self.log(tr("Applying profile: {m}").format(m=mode_label(name)), "info")
        self.run_sequence(seq, on_complete=self.check_ip)

    # -- IP check ---------------------------------------------------------- #
    def check_ip(self):
        self.dashboard().set_ip(tr("checking …"), T.TEXT_MUTED)
        def job():
            res = backend.ip_check()
            if "error" not in res:
                audit.maybe_store_real_fp(res, backend.read_state())
            return 0, json.dumps(res)
        def done(rc, out):
            try:
                res = json.loads(out)
            except ValueError:
                res = {"error": out.strip()[-200:] or "unknown"}
            if "error" in res:
                self.dashboard().set_ip(tr("Unreachable"), T.PARTIAL,
                                        "\n".join(res.get("tried", [])))
                self.log(f"✗ {tr('IP check failed')} — {tr(res['error'])}", "err")
                for t in res.get("tried", [])[:-1]:
                    self.log(f"    {t}", "info")
            else:
                self.show_ip(res, log=True)
        self._dispatch("Checking exit IP", job, on_done=done, quiet=True)

    def show_ip(self, res, log=False):
        is_tor = res.get("is_tor")
        where = " · ".join(x for x in (res.get("country"), res.get("org")) if x)
        color = T.SECURED if is_tor else (T.PARTIAL if is_tor is None else T.EXPOSED)
        self.dashboard().set_ip(res.get("ip", "?"), color, where)
        if log:
            status = (tr("Tor confirmed") if is_tor else
                      tr("Tor status unknown") if is_tor is None else tr("NOT via Tor"))
            self.log(f"✓ {tr('Exit IP')} {res.get('ip')}"
                     + (f" ({where})" if where else "") + f" — {status}",
                     "ok" if is_tor else ("warn" if is_tor is None else "err"))

    def dashboard(self):
        return self.panels[0]

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
    f = QFont(T.SANS_FAMILY); f.setPixelSize(13)
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    app.setFont(f)
    win = MainWindow(); win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
