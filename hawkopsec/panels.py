"""HawkOpsec — panels (hairline list layout, one-tap profiles, leak audit)."""
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFileDialog, QPlainTextEdit,
)

from . import theme as T
from . import backend
from . import audit
from .i18n import tr, mode_label
from .widgets import (
    SettingRow, StatusCell, ModeCards, SectionHeader, CheckRow,
)

# (name, one-line purpose, accent)
MODES = [("BASELINE", "Everything off",      T.TEXT_MUTED),
         ("SECURE",   "Daily use",           T.CYAN),
         ("PUBLIC",   "Untrusted Wi-Fi",     T.CYAN),
         ("HARDENED", "Less fingerprint",    T.AMBER),
         ("GHOST",    "Tor + kill-switch",   T.RED),
         ("PARANOID", "Tor + RAM wipe",      T.RED)]

MODE_C = {name: c for name, _h, c in MODES}

MODE_DESC = {
    "BASELINE": "Everything off. Reverts all changes and restores your original "
                "configuration — identical to Reset system.",
    "SECURE":   "Everyday hardening: kernel hardening, default-deny firewall, "
                "encrypted DNS (DoT), IPv6 off, no crash reports, logs kept in RAM. "
                "No Tor — fully usable for daily work.",
    "PUBLIC":   "SECURE plus MAC randomization (incl. persistent via NetworkManager) "
                "and Bluetooth off. Built for untrusted / public Wi-Fi. Still no Tor.",
    "HARDENED": "PUBLIC plus random machine-id and hostname, swap off and USB "
                "lockdown. Strong anti-fingerprinting without routing through Tor.",
    "GHOST":    "HARDENED plus UTC timezone, webcam off and system-wide Tor routing "
                "with a leak kill-switch. The tool starts Tor for you.",
    "PARANOID": "GHOST plus RAM wipe on shutdown (cold-boot mitigation). Maximum "
                "protection; heaviest profile.",
}


def _page(title, subtitle=""):
    body = QWidget(); body.setObjectName("PanelBody")
    lay = QVBoxLayout(body)
    lay.setContentsMargins(36, 22, 36, 20); lay.setSpacing(5)
    lay.addWidget(SectionHeader(title, subtitle))
    lay.addSpacing(10)
    return body, lay


def _scroll(panel, body):
    panel.setWidget(body); panel.setWidgetResizable(True)
    panel.setFrameShape(QScrollArea.Shape.NoFrame)


def _btn(text, slot=None, kind="Ghost"):
    b = QPushButton(tr(text)); b.setObjectName(kind)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if slot: b.clicked.connect(slot)
    return b


_ghost = _btn


def _group(text):
    l = QLabel(tr(text)); l.setObjectName("GroupLabel"); return l


class ButtonsRow(QWidget):
    """Row: title + mono value on the left, buttons on the right."""
    def __init__(self, title, value, buttons):
        super().__init__()
        self.setMinimumHeight(62)
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 12, 0, 12); lay.setSpacing(10)
        col = QVBoxLayout(); col.setSpacing(3)
        t = QLabel(tr(title)); t.setObjectName("RowTitle")
        self.value = QLabel(value); self.value.setObjectName("Mono")
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value.setStyleSheet(f"color:{T.TEXT_MUTED};")
        col.addWidget(t); col.addWidget(self.value)
        lay.addLayout(col, 1)
        for b in buttons: lay.addWidget(b)

    def set_value(self, text, color):
        self.value.setText(text)
        self.value.setStyleSheet(f"color:{color};")

    def paintEvent(self, _):
        from PyQt6.QtGui import QPainter, QPen, QColor
        p = QPainter(self); p.setPen(QPen(QColor(T.HAIRLINE), 1))
        p.drawLine(0, self.height() - 1, self.width(), self.height() - 1); p.end()


# --------------------------------------------------------------------------- #
class DashboardPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("Overview",
                          "Pick a profile — HawkOpsec resets to baseline, then applies "
                          "every step itself, including starting Tor.")

        lay.addWidget(_group("Security profile"))
        lay.addSpacing(4)
        self.modes = ModeCards(MODES)
        self.modes.selected.connect(self.win.apply_mode)
        lay.addWidget(self.modes)
        lay.addSpacing(8)
        self.mode_desc = QLabel(""); self.mode_desc.setObjectName("RowDesc")
        self.mode_desc.setWordWrap(True); self.mode_desc.setMinimumHeight(34)
        lay.addWidget(self.mode_desc)
        lay.addSpacing(6)

        lay.addWidget(_group("Live status"))
        grid = QGridLayout(); grid.setHorizontalSpacing(40); grid.setVerticalSpacing(0)
        self.cells = {}
        for i, (k, label) in enumerate([
            ("tor", "Connection"), ("ip", "Public IP"),
            ("dns", "DNS"), ("fw", "Firewall"),
            ("v6", "IPv6"), ("mac", "MAC address"),
            ("mid", "Machine ID"), ("host", "Hostname"),
            ("tz", "Timezone"), ("cam", "Webcam")]):
            c = StatusCell(label); self.cells[k] = c
            grid.addWidget(c, i // 2, i % 2)
        lay.addLayout(grid)
        lay.addSpacing(16)

        bar = QHBoxLayout(); bar.setSpacing(8)
        bar.addWidget(_btn("Check IP", lambda: self.win.check_ip(), "Primary"))
        bar.addWidget(_btn("Run leak test", self._audit))
        bar.addWidget(_btn("Open Tor Browser", self._browser))
        bar.addWidget(_btn("RAM browser", lambda: self.win.run_callable(
            "RAM-only browser", backend.launch_amnesic_browser)))
        bar.addStretch(1)
        bar.addWidget(_btn("Reset system", self._reset))
        bar.addWidget(_btn("Panic", self._panic, "Danger"))
        lay.addLayout(bar)

        lay.addStretch(1)
        _scroll(self, body)

    def _audit(self):
        self.win.open_audit(run=True)

    def _browser(self):
        self.win.run_callable("Anonymous browser", backend.launch_anon_browser)

    def _reset(self):
        if self.win.confirm(tr("Reset system"),
                            tr("Revert every change and return to the original state?")):
            self.win.apply_mode("BASELINE", confirm=False)

    def _panic(self):
        if self.win.confirm(tr("Panic"),
                            tr("Cut all network, kill sensitive apps and drop caches now?")):
            self.win.clear_clipboard(quiet=True)
            self.win.run_action("Panic", "panic", force=True)

    def set_ip(self, text, color, tooltip=""):
        self.cells["ip"].set_state(text, color, tooltip)

    def refresh(self, st):
        mode = st.get("mode", "BASELINE")
        self.modes.set_active(mode)
        col = MODE_C.get(mode, T.TEXT_MUTED)
        self.mode_desc.setText(
            f'<span style="color:{col};font-weight:600">{mode_label(mode)}</span>'
            f'<span style="color:{T.TEXT_MUTED}"> — {tr(MODE_DESC.get(mode, ""))}</span>')
        tor = st.get("tor")
        self.cells["tor"].set_state("Tor routed" if tor else "Direct",
                                    T.SECURED if tor else T.EXPOSED)
        if tor:
            self.cells["dns"].set_state("Via Tor", T.SECURED)
        elif st.get("dns"):
            self.cells["dns"].set_state(st["dns"].capitalize() + " DoT", T.SECURED)
        else:
            rs = backend.resolvers()
            self.cells["dns"].set_state(rs[0] if rs else "System", T.PARTIAL)
        on = bool(st.get("firewall") or tor)
        self.cells["fw"].set_state("Active" if on else "Off", T.SECURED if on else T.EXPOSED)
        v6 = backend.ipv6_disabled()
        self.cells["v6"].set_state("Disabled" if v6 else "Enabled",
                                   T.SECURED if v6 else T.PARTIAL)
        macs = st.get("mac_spoofed", {}) or st.get("nm_mac")
        self.cells["mac"].set_state("Spoofed" if macs else "Hardware",
                                    T.SECURED if macs else T.PARTIAL)
        self.cells["mid"].set_state("Spoofed" if st.get("machineid") else "Real",
                                    T.SECURED if st.get("machineid") else T.PARTIAL)
        self.cells["host"].set_state(backend.hostname(),
                                     T.SECURED if st.get("hostname") else T.PARTIAL)
        tzc = audit.check_timezone()
        self.cells["tz"].set_state("UTC" if tzc["status"] == "pass"
                                   else tzc["params"].get("tz", "?"),
                                   T.SECURED if tzc["status"] == "pass" else T.PARTIAL)
        cam = audit.check_webcam(st)
        self.cells["cam"].set_state("Off" if cam["status"] == "pass" else "Available",
                                    T.SECURED if cam["status"] == "pass" else T.PARTIAL)


# --------------------------------------------------------------------------- #
class _DnsControl(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.combo = QComboBox(); self.combo.addItems(["quad9", "cloudflare", "mullvad"])
        self.combo.setFixedWidth(124)
        lay.addWidget(self.combo)
        lay.addWidget(_btn("Apply", lambda: self.win.run_action(
            "DNS-over-TLS", "dns-set", self.combo.currentText())))
        lay.addWidget(_btn("Restore", lambda: self.win.run_action("DNS restore", "dns-restore")))


class NetworkPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("Network", "Anonymity and perimeter: Tor routing, encrypted DNS, "
                                     "inbound firewall.")

        self.row_tor = SettingRow("Tor transparent proxy",
            "Route all TCP and DNS through Tor with a kill-switch, IPv6 block and "
            "per-destination stream isolation.",
            control="toggle")
        self.row_tor.toggled.connect(
            lambda on: self.win.run_action("Tor", "tor-on" if on else "tor-off",
                                           then_check_ip=on))
        lay.addWidget(self.row_tor)

        lay.addWidget(SettingRow("DNS-over-TLS",
            "Encrypt DNS via systemd-resolved (ignored while Tor routing is on).",
            control=_DnsControl(win)))

        self.row_fw = SettingRow("Firewall — default-deny inbound",
            "Drop all unsolicited inbound; keep established/related.", control="toggle")
        self.row_fw.toggled.connect(
            lambda on: self.win.run_action("Firewall", "firewall-on" if on else "firewall-off"))
        lay.addWidget(self.row_fw)

        self.row_v6 = SettingRow("Disable IPv6",
            "Remove a common deanonymization leak path system-wide.", control="toggle")
        self.row_v6.toggled.connect(
            lambda on: self.win.run_action("IPv6", "ipv6-off" if on else "ipv6-on"))
        lay.addWidget(self.row_v6)

        lay.addWidget(SettingRow("Harden Firefox",
            "Write a user.js: WebRTC, WebGL and geolocation off, resistFingerprinting on. "
            "Tor Browser is still the real fix for browser fingerprinting.",
            control=_btn("Apply", self._harden_ff)))

        lay.addWidget(SettingRow("DNS / IP leak test",
            "Check which resolvers see your queries and whether your real IP or IPv6 "
            "escapes the tunnel.",
            control=_btn("Run", lambda: self.win.open_audit(run=True))))

        lay.addStretch(1)
        _scroll(self, body)

    def _harden_ff(self):
        self.win.run_callable("Harden Firefox", backend.harden_firefox)

    def refresh(self, st):
        self.row_tor.set_checked(bool(st.get("tor")))
        self.row_fw.set_checked(bool(st.get("firewall")))
        self.row_v6.set_checked(backend.ipv6_disabled())


# --------------------------------------------------------------------------- #
class IdentityPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, self._lay = _page("Identity", "Machine fingerprint: what the local network "
                                            "and the sites you visit can tie back to you.")
        self._lay.addWidget(_group("Network interfaces"))
        self.iface_box = QVBoxLayout(); self.iface_box.setSpacing(0)
        self._lay.addLayout(self.iface_box)
        self._lay.addSpacing(18)
        self._lay.addWidget(_group("Host identity"))

        self.host_row = ButtonsRow("Hostname", backend.hostname(), [
            _btn("Randomize", lambda: self.win.run_action("Hostname", "hostname-random")),
            _btn("Restore", lambda: self.win.run_action("Hostname", "hostname-restore"))])
        self._lay.addWidget(self.host_row)

        self.mid_row = ButtonsRow("Machine ID", "—", [
            _btn("Randomize", lambda: self.win.run_action("Machine ID", "machineid-random")),
            _btn("Restore", lambda: self.win.run_action("Machine ID", "machineid-restore"))])
        self._lay.addWidget(self.mid_row)

        self.row_tz = SettingRow("Force timezone to UTC",
            "Report UTC everywhere to shrink your locale fingerprint.", control="toggle")
        self.row_tz.toggled.connect(
            lambda on: self.win.run_action("Timezone", "tz-utc" if on else "tz-restore"))
        self._lay.addWidget(self.row_tz)

        self.row_nm = SettingRow("Persistent MAC (NetworkManager)",
            "Randomize MAC on every connect via NetworkManager, so it survives reconnects.",
            control="toggle")
        self.row_nm.toggled.connect(
            lambda on: self.win.run_action("Persistent MAC", "nm-mac-on" if on else "nm-mac-off"))
        self._lay.addWidget(self.row_nm)

        self._lay.addStretch(1)
        _scroll(self, body)
        self._rows = {}; self.rebuild_ifaces()

    def rebuild_ifaces(self):
        while self.iface_box.count():
            it = self.iface_box.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self._rows = {}
        for i in backend.interfaces():
            r = ButtonsRow(i["name"], i["mac"], [
                _btn("Randomize", lambda _c=False, n=i["name"]:
                     self.win.run_action(f"MAC {n}", "mac-random", n)),
                _btn("Restore", lambda _c=False, n=i["name"]:
                     self.win.run_action(f"MAC {n}", "mac-restore", n))])
            self._rows[i["name"]] = r
            self.iface_box.addWidget(r)

    def refresh(self, st):
        spoofed = st.get("mac_spoofed", {})
        cur = {i["name"]: i for i in backend.interfaces()}
        if set(cur) != set(self._rows):
            self.rebuild_ifaces()
        for name, r in self._rows.items():
            info = cur.get(name)
            if info:
                r.set_value(info["mac"], T.SECURED if name in spoofed else T.TEXT_MUTED)
        self.host_row.set_value(backend.hostname(),
                                T.SECURED if st.get("hostname") else T.TEXT_MUTED)
        self.mid_row.set_value(tr("spoofed") if st.get("machineid") else tr("hardware ID"),
                               T.SECURED if st.get("machineid") else T.TEXT_MUTED)
        self.row_tz.set_checked(bool(st.get("tz")))
        self.row_nm.set_checked(bool(st.get("nm_mac")))


# --------------------------------------------------------------------------- #
class HardeningPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("Hardening", "Kernel, services and hardware. Every toggle is "
                                       "reverted by Reset system.")

        self.rows = {}
        def add(key, verb_on, verb_off, title, desc, danger=False):
            r = SettingRow(title, desc, control="toggle", danger=danger)
            r.toggled.connect(lambda on, a=verb_on, b=verb_off, t=title:
                              self.win.run_action(t, a if on else b))
            lay.addWidget(r); self.rows[key] = r

        add("sysctl", "harden-sysctl", "unharden-sysctl", "Kernel / sysctl hardening",
            "rp_filter, no redirects, SYN cookies, kptr/dmesg restrict, ptrace_scope=2, full ASLR.")
        add("telemetry", "telemetry-off", "telemetry-restore", "Disable crash reporting",
            "Set systemd-coredump Storage=none and stop any apport/whoopsie services.")
        add("journald_volatile", "journald-volatile", "journald-persistent",
            "Keep journald in RAM", "System logs stay in memory, never on disk.")
        add("bluetooth_off", "bluetooth-off", "bluetooth-on", "Disable Bluetooth",
            "rfkill-block Bluetooth to remove a wireless attack surface.")
        add("webcam_off", "webcam-off", "webcam-on", "Disable webcam",
            "Unload the UVC camera driver and block it from loading again.")
        add("swap_off", "swap-off", "swap-on", "Disable swap",
            "swapoff to stop secrets and keys leaking to disk.")
        add("usb_lock", "usb-lock", "usb-unlock", "USB lockdown",
            "Block newly-connected USB devices (BadUSB defense); existing stay working.")
        add("ramwipe", "ramwipe-on", "ramwipe-off", "RAM wipe on shutdown",
            "Drop caches, swapoff and wipe memory at shutdown (cold-boot mitigation).")

        lay.addStretch(1)
        _scroll(self, body)

    def refresh(self, st):
        for key, r in self.rows.items():
            r.set_checked(bool(st.get(key)))


# --------------------------------------------------------------------------- #
LEAK_ROWS = [("exit_ip", "Exit IP"), ("dns_leak", "DNS leak"), ("ipv6_leak", "IPv6 leak"),
             ("webrtc_leak", "WebRTC (STUN)"), ("pub_iface", "Local addresses"),
             ("udp_leak", "Kill-switch (UDP)"), ("onion", ".onion resolution"),
             ("tor_svc", "Tor service")]
PREFLIGHT_ROWS = [("tb", "Tor Browser"), ("webrtc", "WebRTC (Firefox)"),
                  ("ffwipe", "Firefox wipe on close"), ("btrace", "Browser history on disk"),
                  ("tz", "Timezone"), ("clock", "Clock sync"), ("host", "Hostname"),
                  ("mac", "MAC address"), ("fw", "Firewall"), ("listen", "Open ports"),
                  ("apps", "Identity-linked apps"), ("cam", "Webcam"),
                  ("crypt", "Disk encryption"), ("swap", "Swap"),
                  ("root", "Session user"), ("vpn", "VPN")]

# one-click fixes for failed/warned checks: id -> (label, verb | callable)
FIXES = {
    "ipv6_leak": ("IPv6", "ipv6-off"),
    "tz":        ("Timezone", "tz-utc"),
    "host":      ("Hostname", "hostname-random"),
    "mac":       ("Persistent MAC", "nm-mac-on"),
    "fw":        ("Firewall", "firewall-on"),
    "cam":       ("Disable webcam", "webcam-off"),
    "swap":      ("Disable swap", "swap-off"),
    "webrtc":    ("Harden Firefox", backend.harden_firefox),
    "ffwipe":    ("Firefox wipe on close", backend.firefox_wipe_on_close),
    "btrace":    ("Clean browser traces", backend.clean_browser_traces),
}

VERDICT_TXT = {
    "READY":     ("Ready", T.CYAN),
    "RISKY":     ("Risky — review the warnings", T.AMBER),
    "NOT READY": ("Not ready", T.RED),
}


class AuditPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("Leak test",
                          "Run before every dark-web session. Read-only — nothing on the "
                          "system changes until you press Fix.")

        top = QHBoxLayout(); top.setSpacing(10)
        vcol = QVBoxLayout(); vcol.setSpacing(2)
        self.verdict = QLabel(tr("Not run yet")); self.verdict.setObjectName("Verdict")
        self.verdict.setStyleSheet(f"color:{T.TEXT_MUTED};")
        self.summary = QLabel(tr("Takes 10–30 seconds; uses bash.ws for the DNS test.")); self.summary.setObjectName("Hint")
        vcol.addWidget(self.verdict); vcol.addWidget(self.summary)
        top.addLayout(vcol, 1)
        self.run_btn = _btn("Run all checks", self.run, "Primary")
        top.addWidget(self.run_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(top)
        lay.addSpacing(18)

        self.rows = {}
        self.fix_btns = {}
        lay.addWidget(_group("Leak tests"))
        for cid, title in LEAK_ROWS:
            self._add_row(lay, cid, title)
        lay.addSpacing(18)
        lay.addWidget(_group("Dark-web pre-flight"))
        for cid, title in PREFLIGHT_ROWS:
            self._add_row(lay, cid, title)

        lay.addSpacing(14)
        foot = QHBoxLayout()
        note = QLabel(tr("Your real ISP is remembered as a name + salted hash (never the "
                         "raw IP) while in BASELINE, so leaks can be recognised later."))
        note.setObjectName("Hint"); note.setWordWrap(True)
        foot.addWidget(note, 1)
        foot.addWidget(_btn("Forget", self._forget, "Link"))
        lay.addLayout(foot)
        lay.addStretch(1)
        _scroll(self, body)
        self._running = False

    def _add_row(self, lay, cid, title):
        r = CheckRow(title)
        if cid in FIXES:
            b = _btn("Fix", lambda _c=False, i=cid: self._fix(i))
            b.setVisible(False)
            r.layout().addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
            self.fix_btns[cid] = b
        self.rows[cid] = r
        lay.addWidget(r)

    def _fix(self, cid):
        label, act = FIXES[cid]
        if cid == "btrace" and not self.win.confirm(tr("Clean browser traces"),
                tr("Delete history, cookies, cache and sessions of all browsers? "
                   "Bookmarks and saved passwords are kept. Close your browsers first.")):
            return
        if callable(act):
            self.win.run_callable(label, act, on_done=lambda *_: self.run())
        else:
            self.win.run_action(label, act, on_done=lambda *_: self.run())
        self.fix_btns[cid].setVisible(False)

    def _forget(self):
        audit.forget_real_fp()
        self.win.log(tr("Saved ISP fingerprint deleted."), "info")

    def run(self):
        if self._running:
            return
        self._running = True
        self.run_btn.setEnabled(False)
        self.verdict.setText(tr("Running …")); self.verdict.setStyleSheet(f"color:{T.TEXT};")
        for cid, r in self.rows.items():
            r.set_status("running", tr("Checking …"))
        for b in self.fix_btns.values(): b.setVisible(False)
        self.win.run_callable("Leak test", lambda: (0, json.dumps(audit.run_all())),
                              on_done=self._done, quiet=True)

    def _done(self, rc, out):
        self._running = False
        self.run_btn.setEnabled(True)
        try:
            res = json.loads(out)
        except (ValueError, TypeError):
            self.verdict.setText(tr("Audit failed")); self.verdict.setStyleSheet(f"color:{T.RED};")
            self.summary.setText(out[-300:]); return
        for c in res["checks"]:
            r = self.rows.get(c["id"])
            if not r: continue
            try:
                detail = tr(c["detail"]).format(
                    **{k: tr(v) for k, v in c.get("params", {}).items()})
            except (KeyError, IndexError):
                detail = c["detail"]
            r.set_status(c["status"], detail)
            if c["id"] in self.fix_btns:
                self.fix_btns[c["id"]].setVisible(c["status"] in ("warn", "fail"))
        txt, col = VERDICT_TXT.get(res["verdict"], (res["verdict"], T.TEXT))
        self.verdict.setText(tr(txt)); self.verdict.setStyleSheet(f"color:{col};")
        self.summary.setText(tr("{p} of {t} checks passed · {f} failed · {w} warnings · {ts}")
                             .format(p=res["passed"], t=res["total"], f=res["fails"],
                                     w=res["warns"], ts=res["ts"]))
        self.win.log(f"{tr('Leak test')}: {tr(txt)} — "
                     f"{res['passed']}/{res['total']}", "ok" if res["verdict"] == "READY"
                     else "err")
        for c in res["checks"]:
            if c["status"] in ("fail", "warn"):
                tag = tr("FAIL") if c["status"] == "fail" else tr("WARN")
                self.win.log(f"    {tag}  {tr(c['title'])}",
                             "err" if c["status"] == "fail" else "warn")
        ip = res.get("ip", {})
        if ip and "error" not in ip:
            self.win.show_ip(ip)

    def refresh(self, st): pass


# --------------------------------------------------------------------------- #
class TracesPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("Traces", "Forensic hygiene. These are one-shot operations — "
                                    "Reset system does not undo them.")

        lay.addWidget(_group("Browser"))
        lay.addWidget(SettingRow("RAM-only browser",
            "Firefox with a throw-away profile in memory: history, cookies, cache and "
            "sessions never touch the disk and the profile is deleted on close.",
            control=_btn("Open", lambda: self.win.run_callable(
                "RAM-only browser", backend.launch_amnesic_browser))))
        lay.addWidget(SettingRow("Clean browser traces",
            "History, cookies, cache, sessions, site storage and form data of Firefox and "
            "Chromium-family browsers. Bookmarks and saved passwords are kept.",
            control=_btn("Clean", self._clean_browser)))
        lay.addWidget(SettingRow("Firefox: wipe on close",
            "Make your normal Firefox delete history, cookies, cache and form data every "
            "time it closes, and stop writing the cache to disk.",
            control=_btn("Apply", lambda: self.win.run_callable(
                "Firefox wipe on close", backend.firefox_wipe_on_close))))
        lay.addWidget(SettingRow("Clear clipboard",
            "Copied .onion links, addresses and passwords stay in the clipboard until "
            "overwritten. Panic clears it too.",
            control=_btn("Clear", self.win.clear_clipboard)))
        lay.addSpacing(14)
        lay.addWidget(_group("System"))
        lay.addWidget(SettingRow("Clean user traces",
            "Shell history, recent files, thumbnails and trash in your home.",
            control=_btn("Clean", self._clean_user)))
        lay.addWidget(SettingRow("Clean system traces",
            "Vacuum journald, flush the DNS cache, wipe coredumps, login records and package cache.",
            control=_btn("Clean", lambda: self.win.run_action("System clean", "clean-system"))))
        lay.addWidget(SettingRow("Strip file metadata",
            "Remove EXIF and other metadata from selected files (mat2 or exiftool).",
            control=_btn("Select files", self._strip)))
        lay.addWidget(SettingRow("Secure delete",
            "Overwrite then delete selected files so they can't be recovered. "
            "On SSDs this is best-effort — full-disk encryption is the real protection.",
            control=_btn("Select files", self._shred)))
        lay.addStretch(1)
        _scroll(self, body)

    def _clean_browser(self):
        if self.win.confirm(tr("Clean browser traces"),
                tr("Delete history, cookies, cache and sessions of all browsers? "
                   "Bookmarks and saved passwords are kept. Close your browsers first.")):
            self.win.run_callable("Clean browser traces", backend.clean_browser_traces)

    def _clean_user(self):
        def job():
            c = backend.clean_user_traces()
            return 0, "cleaned: " + (", ".join(c) if c else "nothing")
        self.win.run_callable("Clean user traces", job)

    def _strip(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("Select files to strip metadata"))
        if files:
            self.win.run_callable("Strip metadata", lambda: backend.strip_metadata(files))

    def _shred(self):
        files, _ = QFileDialog.getOpenFileNames(self, tr("Select files to shred"))
        if files and self.win.confirm(tr("Secure delete"),
                tr("Permanently shred the selected item(s)? This cannot be undone.")):
            self.win.run_callable("Secure delete", lambda: backend.secure_delete(files))

    def refresh(self, st): pass


# --------------------------------------------------------------------------- #
class ActivityPanel(QWidget):
    """Change log — what HawkOpsec actually did to the system (from helper.log)."""
    def __init__(self, win):
        super().__init__(); self.win = win
        self.setObjectName("PanelBody")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 30, 36, 24); lay.setSpacing(12)
        head = QHBoxLayout()
        head.addWidget(SectionHeader("Activity", "Every change HawkOpsec made to this "
                                                 "system, from the helper log."), 1)
        head.addWidget(_btn("Refresh", self.reload), 0, Qt.AlignmentFlag.AlignBottom)
        lay.addLayout(head)
        self.view = QPlainTextEdit(); self.view.setReadOnly(True)
        self.view.setStyleSheet(
            f"QPlainTextEdit{{background:{T.SURFACE_1};border:1px solid {T.HAIRLINE};"
            f"border-radius:3px;color:{T.TEXT};font-family:{T.MONO};font-size:12px;"
            f"padding:10px;}}")
        lay.addWidget(self.view, 1)
        self.reload()

    def reload(self):
        txt = backend.read_log()
        self.view.setPlainText(txt or tr("No changes recorded yet. Applied actions "
                                          "will appear here with timestamps."))
        sb = self.view.verticalScrollBar(); sb.setValue(sb.maximum())

    def refresh(self, st):
        if self.isVisible():
            self.reload()
