"""HawkOpsec — panels (borderless list layout, ready-made modes)."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFileDialog, QPlainTextEdit,
)

from . import theme as T
from . import backend
from .i18n import tr
from .widgets import (
    SettingRow, StatusCell, SegmentedModes, SectionHeader,
)

MODES = [("BASELINE", "TEXT_MUTED"), ("SECURE", "CYAN"), ("PUBLIC", "CYAN"),
         ("HARDENED", "AMBER"), ("GHOST", "RED"), ("PARANOID", "RED")]

MODE_C = {name: getattr(T, ck) for name, ck in MODES}

MODE_DESC = {
    "BASELINE": "Everything off. Reverts all changes and restores your original "
                "configuration — identical to RESET SYSTEM.",
    "SECURE":   "Everyday hardening: kernel hardening, default-deny firewall, "
                "encrypted DNS (DoT), IPv6 off, no crash reports, logs kept in RAM. "
                "No Tor — fully usable for daily work.",
    "PUBLIC":   "SECURE plus MAC randomization (incl. persistent via NetworkManager) "
                "and Bluetooth off. Built for untrusted / public wifi. Still no Tor.",
    "HARDENED": "PUBLIC plus random machine-id and hostname, swap off and USB "
                "lockdown. Strong anti-fingerprinting without routing through Tor.",
    "GHOST":    "HARDENED plus UTC timezone and system-wide Tor routing with a leak "
                "kill-switch. Full anonymity — the tool starts Tor for you.",
    "PARANOID": "GHOST plus RAM wipe on shutdown (cold-boot mitigation). Maximum "
                "protection; heaviest profile.",
}


def _page(eyebrow, title):
    body = QWidget(); body.setObjectName("PanelBody")
    lay = QVBoxLayout(body)
    lay.setContentsMargins(30, 26, 30, 26); lay.setSpacing(6)
    lay.addWidget(SectionHeader(eyebrow, title))
    lay.addSpacing(10)
    return body, lay


def _ghost(text, slot=None):
    b = QPushButton(tr(text)); b.setObjectName("Ghost")
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if slot: b.clicked.connect(slot)
    return b


def _group(text):
    l = QLabel(tr(text).upper()); l.setObjectName("GroupLabel"); return l


class ButtonsRow(QWidget):
    """Borderless row: title + mono value on the left, ghost buttons on right."""
    def __init__(self, title, value, buttons):
        super().__init__()
        self.setMinimumHeight(56)
        lay = QHBoxLayout(self); lay.setContentsMargins(2, 11, 2, 11); lay.setSpacing(14)
        col = QVBoxLayout(); col.setSpacing(3)
        t = QLabel(tr(title)); t.setObjectName("RowTitle")
        self.value = QLabel(value); self.value.setObjectName("Mono")
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
        body, lay = _page("system status", "Operations Board")

        lay.addWidget(_group("security mode"))
        self.modes = SegmentedModes(MODES)
        self.modes.selected.connect(self.win.apply_mode)
        lay.addWidget(self.modes)
        tap = QLabel(tr("One tap applies a full profile — the tool starts Tor and "
                        "everything else itself."))
        tap.setObjectName("MonoMuted"); lay.addWidget(tap)
        lay.addSpacing(6)
        self.mode_desc = QLabel(""); self.mode_desc.setObjectName("RowDesc")
        self.mode_desc.setWordWrap(True); self.mode_desc.setMinimumHeight(46)
        lay.addWidget(self.mode_desc)
        lay.addSpacing(14)

        lay.addWidget(_group("live status"))
        grid = QGridLayout(); grid.setHorizontalSpacing(28); grid.setVerticalSpacing(0)
        self.cells = {}
        for i, (k, label) in enumerate([
            ("tor", "CONNECTION"), ("ip", "PUBLIC IP"),
            ("dns", "DNS"), ("fw", "FIREWALL"),
            ("v6", "IPV6"), ("mac", "MAC"),
            ("mid", "MACHINE-ID"), ("bt", "BLUETOOTH")]):
            c = StatusCell(label); self.cells[k] = c
            grid.addWidget(c, i // 2, i % 2)
        lay.addLayout(grid)
        lay.addSpacing(18)

        lay.addWidget(_group("operations"))
        bar = QHBoxLayout(); bar.setSpacing(10)
        bar.addWidget(_ghost("CHECK IP", lambda: self.win.check_ip()))
        bar.addWidget(_ghost("ANON BROWSER", self._browser))
        bar.addStretch(1)
        bar.addWidget(_ghost("RESET SYSTEM", self._reset))
        panic = QPushButton(tr("PANIC")); panic.setObjectName("Danger")
        panic.setCursor(Qt.CursorShape.PointingHandCursor); panic.clicked.connect(self._panic)
        bar.addWidget(panic)
        lay.addLayout(bar)

        lay.addStretch(1)
        self.setWidget(body); self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

    def _browser(self):
        self.win.run_callable("Anonymous browser", backend.launch_anon_browser)

    def _reset(self):
        if self.win.confirm(tr("Reset system"),
                            tr("Revert every change and return to the original state?")):
            self.win.apply_mode("BASELINE")

    def _panic(self):
        if self.win.confirm(tr("Panic"),
                            tr("Cut all network, kill sensitive apps and drop caches now?")):
            self.win.run_action("PANIC", "panic")

    def set_ip(self, text, color): self.cells["ip"].set_state(text, color)

    def refresh(self, st):
        mode = st.get("mode", "BASELINE")
        self.modes.set_active(mode)
        col = MODE_C.get(mode, T.TEXT_MUTED)
        self.mode_desc.setText(
            f'<span style="color:{col};font-weight:700">{tr(mode)}</span>'
            f'<span style="color:{T.TEXT_MUTED}">  —  {tr(MODE_DESC.get(mode, ""))}</span>')
        tor = st.get("tor")
        self.cells["tor"].set_state("TOR ROUTED" if tor else "DIRECT",
                                    T.SECURED if tor else T.EXPOSED)
        if tor:
            self.cells["dns"].set_state("VIA TOR", T.SECURED)
        elif st.get("dns"):
            self.cells["dns"].set_state(st["dns"].upper() + " DoT", T.SECURED)
        else:
            rs = backend.resolvers()
            self.cells["dns"].set_state(rs[0] if rs else "SYSTEM", T.PARTIAL)
        self.cells["fw"].set_state("ACTIVE" if st.get("firewall") else "OFF",
                                   T.SECURED if st.get("firewall") else T.EXPOSED)
        v6 = backend.ipv6_disabled()
        self.cells["v6"].set_state("DISABLED" if v6 else "ENABLED",
                                   T.SECURED if v6 else T.PARTIAL)
        macs = st.get("mac_spoofed", {})
        self.cells["mac"].set_state("SPOOFED" if macs else "HARDWARE",
                                    T.SECURED if macs else T.PARTIAL)
        self.cells["mid"].set_state("SPOOFED" if st.get("machineid") else "REAL",
                                    T.SECURED if st.get("machineid") else T.PARTIAL)
        self.cells["bt"].set_state("BLOCKED" if st.get("bluetooth_off") else "ON",
                                   T.SECURED if st.get("bluetooth_off") else T.PARTIAL)


# --------------------------------------------------------------------------- #
class _DnsControl(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(8)
        self.combo = QComboBox(); self.combo.addItems(["quad9", "cloudflare", "mullvad"])
        self.combo.setFixedWidth(120)
        lay.addWidget(self.combo)
        lay.addWidget(_ghost("APPLY", lambda: self.win.run_action(
            "DNS-over-TLS", "dns-set", self.combo.currentText())))
        lay.addWidget(_ghost("RESTORE", lambda: self.win.run_action("DNS restore", "dns-restore")))


class NetworkPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("anonymity & perimeter", "Network")

        self.row_tor = SettingRow("Tor transparent proxy",
            "Route all TCP through Tor with a kill-switch, IPv6 block and per-destination stream isolation.",
            control="toggle")
        self.row_tor.toggled.connect(
            lambda on: self.win.run_action("Tor", "tor-on" if on else "tor-off"))
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

        lay.addWidget(SettingRow("Harden Firefox (WebRTC off, anti-fingerprint)",
            "Write a user.js: disable WebRTC, resistFingerprinting, WebGL and geo. "
            "Tor Browser is still the real fix for browser fingerprinting.",
            control=_ghost("APPLY", self._harden_ff)))

        lay.addStretch(1)
        self.setWidget(body); self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

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
        body, self._lay = _page("machine fingerprint", "Identity")
        self._lay.addWidget(_group("network interfaces — MAC"))
        self.iface_box = QVBoxLayout(); self.iface_box.setSpacing(0)
        self._lay.addLayout(self.iface_box)
        self._lay.addSpacing(14)
        self._lay.addWidget(_group("host identity"))

        self.host_row = ButtonsRow("Hostname", backend.hostname(), [
            _ghost("RANDOMIZE", lambda: self.win.run_action("Hostname", "hostname-random")),
            _ghost("RESTORE", lambda: self.win.run_action("Hostname", "hostname-restore"))])
        self._lay.addWidget(self.host_row)

        self.mid_row = ButtonsRow("Machine-ID", "—", [
            _ghost("RANDOMIZE", lambda: self.win.run_action("Machine-ID", "machineid-random")),
            _ghost("RESTORE", lambda: self.win.run_action("Machine-ID", "machineid-restore"))])
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
            lambda on: self.win.run_action("NM MAC", "nm-mac-on" if on else "nm-mac-off"))
        self._lay.addWidget(self.row_nm)

        self._lay.addStretch(1)
        self.setWidget(body); self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self._rows = {}; self.rebuild_ifaces()

    def rebuild_ifaces(self):
        while self.iface_box.count():
            it = self.iface_box.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        self._rows = {}
        for i in backend.interfaces():
            r = ButtonsRow(i["name"], i["mac"], [
                _ghost("RANDOMIZE", lambda _c=False, n=i["name"]:
                       self.win.run_action(f"MAC {n}", "mac-random", n)),
                _ghost("RESTORE", lambda _c=False, n=i["name"]:
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
        self.mid_row.set_value("SPOOFED" if st.get("machineid") else "hardware id",
                               T.SECURED if st.get("machineid") else T.TEXT_MUTED)
        self.row_tz.set_checked(bool(st.get("tz")))
        self.row_nm.set_checked(bool(st.get("nm_mac")))


# --------------------------------------------------------------------------- #
class HardeningPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("kernel · services · hardware", "Hardening")

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
            "journald to RAM (volatile)", "Keep system logs in memory, not on disk.")
        add("bluetooth_off", "bluetooth-off", "bluetooth-on", "Disable Bluetooth",
            "rfkill-block Bluetooth to remove a wireless attack surface.")
        add("swap_off", "swap-off", "swap-on", "Disable swap",
            "swapoff to stop secrets and keys leaking to disk.")
        add("usb_lock", "usb-lock", "usb-unlock", "USB lockdown",
            "Block newly-connected USB devices (BadUSB defense); existing stay working.")
        add("ramwipe", "ramwipe-on", "ramwipe-off", "RAM wipe on shutdown",
            "Drop caches, swapoff and wipe memory at shutdown (cold-boot mitigation).")

        lay.addStretch(1)
        self.setWidget(body); self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

    def refresh(self, st):
        for key, r in self.rows.items():
            r.set_checked(bool(st.get(key)))


# --------------------------------------------------------------------------- #
class TracesPanel(QScrollArea):
    def __init__(self, win):
        super().__init__(); self.win = win
        body, lay = _page("forensic hygiene", "Traces")

        lay.addWidget(SettingRow("Clean user traces",
            "Shell history, recent files, thumbnails and trash in your home.",
            control=_ghost("CLEAN", self._clean_user)))
        lay.addWidget(SettingRow("Clean system traces",
            "Vacuum journald, wipe coredumps, login records and package cache.",
            control=_ghost("CLEAN", lambda: self.win.run_action("System clean", "clean-system"))))

        lay.addWidget(SettingRow("Strip file metadata (EXIF)",
            "Remove EXIF/metadata from selected files (mat2 or exiftool).",
            control=_ghost("SELECT", self._strip)))

        lay.addWidget(SettingRow("Secure-delete (shred)",
            "Overwrite then delete selected files/folders so they can't be recovered.",
            control=_ghost("SELECT", self._shred)))

        warn = QLabel(tr("One-shot operations — not reverted by RESET."))
        warn.setObjectName("RowDesc"); lay.addWidget(warn)
        lay.addStretch(1)
        self.setWidget(body); self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)

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
        lay.setContentsMargins(30, 26, 30, 22); lay.setSpacing(10)
        lay.addWidget(SectionHeader("change log", "Activity"))
        tb = QHBoxLayout(); tb.addStretch(1)
        tb.addWidget(_ghost("REFRESH", self.reload))
        lay.addLayout(tb)
        self.view = QPlainTextEdit(); self.view.setReadOnly(True)
        self.view.setStyleSheet(
            f"QPlainTextEdit{{background:{T.SURFACE_1};border:1px solid {T.HAIRLINE};"
            f"color:{T.TEXT};font-size:11px;padding:10px;}}")
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
