"""
HawkOpsec — leak tests and dark-web pre-flight audit.

Everything here runs unprivileged and is read-only, except for a tiny local
cache of the *real* ISP fingerprint (ASN/org name + a salted hash of the IP —
never the raw IP) captured while the machine is in BASELINE. That fingerprint
lets later tests detect "my real ISP shows up in DNS / exit IP" leaks even
while Tor or a VPN is active.

Each check returns a dict:
    {"id", "group": "leak"|"preflight", "title", "status", "detail"}
status ∈ pass / warn / fail / info / skip
"""
import glob
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import threading
import time

from . import backend

CFG_DIR = os.path.expanduser("~/.config/hawkopsec")
REAL_FP = os.path.join(CFG_DIR, "real_fingerprint.json")

PASS, WARN, FAIL, INFO, SKIP = "pass", "warn", "fail", "info", "skip"

# apps that tie a session to a real identity / phone home constantly
IDENTITY_APPS = {
    "discord": "Discord", "Discord": "Discord", "telegram-deskto": "Telegram",
    "Telegram": "Telegram", "signal-desktop": "Signal", "slack": "Slack",
    "dropbox": "Dropbox", "steam": "Steam", "spotify": "Spotify", "zoom": "Zoom",
    "skypeforlinux": "Skype", "whatsapp": "WhatsApp", "teams": "Teams",
    "megasync": "MEGA", "onedrive": "OneDrive", "nextcloud": "Nextcloud",
    "insync": "Insync", "anydesk": "AnyDesk", "teamviewer": "TeamViewer",
}


def _c(cid, group, title, status, detail="", **params):
    """detail is an English template; the GUI translates it, then .format(**params)."""
    return {"id": cid, "group": group, "title": title, "status": status,
            "detail": detail, "params": {k: str(v) for k, v in params.items()}}


def _run(cmd, timeout=5):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def _norm_org(s):
    """'AS9121 Turk Telekom' / 'Turk Telekom' -> 'turk telekom'"""
    s = (s or "").lower()
    s = re.sub(r"^as\d+\s*", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def _hash_ip(ip, salt):
    return hashlib.sha256((salt + ip).encode()).hexdigest()


# --------------------------------------------------------------------------- #
#  real-identity fingerprint (captured only in BASELINE, direct connection)
# --------------------------------------------------------------------------- #
def load_real_fp():
    try:
        return json.load(open(REAL_FP))
    except (OSError, json.JSONDecodeError):
        return {}


def maybe_store_real_fp(ipres, state):
    """Called after a successful direct IP check in BASELINE mode."""
    if state.get("tor") or state.get("mode", "BASELINE") != "BASELINE":
        return
    if not ipres.get("ip") or ipres.get("is_tor"):
        return
    if any(n.startswith(("wg", "tun", "tailscale", "proton", "mullvad"))
           for n in os.listdir("/sys/class/net")):
        return   # a VPN is up — this is not the real ISP
    salt = load_real_fp().get("salt") or secrets.token_hex(8)
    fp = {"salt": salt, "ip_hash": _hash_ip(ipres["ip"], salt),
          "org": ipres.get("org") or "", "country": ipres.get("country") or "",
          "ts": int(time.time())}
    try:
        os.makedirs(CFG_DIR, exist_ok=True)
        with open(REAL_FP, "w") as f:
            json.dump(fp, f)
        os.chmod(REAL_FP, 0o600)
    except OSError:
        pass


def forget_real_fp():
    try:
        os.remove(REAL_FP)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
#  LEAK TESTS (network)
# --------------------------------------------------------------------------- #
def check_exit_ip(state, ipres):
    tor_on = bool(state.get("tor"))
    fp = load_real_fp()
    if "error" in ipres:
        return _c("exit_ip", "leak", "Exit IP", FAIL if tor_on else WARN,
                  "Could not reach any IP service: {err}", err=ipres["error"])
    ip, org = ipres["ip"], ipres.get("org") or "?"
    where = f"{ip} · {ipres.get('country') or '?'} · {org}"
    if fp.get("ip_hash") and _hash_ip(ip, fp["salt"]) == fp["ip_hash"] and tor_on:
        return _c("exit_ip", "leak", "Exit IP", FAIL,
                  "Your REAL IP is visible while Tor mode is on: {where}", where=where)
    if tor_on:
        if ipres.get("is_tor"):
            return _c("exit_ip", "leak", "Exit IP", PASS,
                      "Traffic exits through Tor: {where}", where=where)
        if ipres.get("is_tor") is None:
            return _c("exit_ip", "leak", "Exit IP", WARN,
                      "Tor status could not be verified: {where}", where=where)
        return _c("exit_ip", "leak", "Exit IP", FAIL,
                  "Tor mode is on but the exit is NOT a Tor relay: {where}", where=where)
    if ipres.get("is_tor"):
        return _c("exit_ip", "leak", "Exit IP", PASS,
                  "Traffic exits through Tor: {where}", where=where)
    return _c("exit_ip", "leak", "Exit IP", INFO,
              "Direct connection — this IP is visible to every site: {where}", where=where)


def _bash_ws_dnsleak():
    """bash.ws DNS leak test: resolve unique subdomains through the system
    resolver, then ask bash.ws which resolver IPs asked for them."""
    tid = backend.http_get("https://bash.ws/id", 10).decode().strip()
    if not re.fullmatch(r"[A-Za-z0-9]+", tid or ""):
        raise RuntimeError("bad test id")

    def resolve(h):
        try:
            socket.getaddrinfo(h, 80)
        except OSError:
            pass   # NXDOMAIN is expected — the query reaching bash.ws is what counts

    ths = [threading.Thread(target=resolve, args=(f"{i}.{tid}.bash.ws",), daemon=True)
           for i in range(1, 11)]
    for t in ths: t.start()
    for t in ths: t.join(5)
    time.sleep(1.0)
    return backend.http_json(f"https://bash.ws/dnsleak/test/{tid}?json", 12)


def check_dns_leak(state, ipres):
    tor_on = bool(state.get("tor"))
    fp = load_real_fp()
    real_org = _norm_org(fp.get("org"))
    try:
        rows = _bash_ws_dnsleak()
    except Exception as e:
        return _c("dns_leak", "leak", "DNS leak", WARN if tor_on else INFO,
                  "DNS leak test service unreachable: {err}", err=backend.explain_error(e))
    servers = [r for r in rows if r.get("type") == "dns"]
    if not servers:
        return _c("dns_leak", "leak", "DNS leak", WARN,
                  "No resolver reached the test server — DNS may be broken.")
    names = sorted({f"{s.get('ip')} ({s.get('asn') or '?'}, {s.get('country_name') or '?'})"
                    for s in servers})
    listing = "; ".join(names[:4]) + (" …" if len(names) > 4 else "")
    leaked = [s for s in servers if real_org and real_org in _norm_org(s.get("asn"))]
    if leaked:
        return _c("dns_leak", "leak", "DNS leak", FAIL,
                  "Your real ISP's resolver answered: {servers}", servers=listing)
    exit_org = _norm_org(ipres.get("org"))
    if not tor_on and not state.get("dns") and exit_org and \
            any(exit_org in _norm_org(s.get("asn")) for s in servers):
        return _c("dns_leak", "leak", "DNS leak", WARN,
                  "Queries go to your ISP's resolver in plain text: {servers}",
                  servers=listing)
    if not real_org:
        return _c("dns_leak", "leak", "DNS leak", INFO,
                  "Resolvers seen: {servers}. Run a check once in BASELINE so "
                  "HawkOpsec can recognise your real ISP.", servers=listing)
    return _c("dns_leak", "leak", "DNS leak", PASS,
              "No resolver belongs to your ISP: {servers}", servers=listing)


def _global_v6_addrs():
    out = []
    try:
        for line in open("/proc/net/if_inet6"):
            p = line.split()
            if len(p) >= 6 and p[3] == "00" and p[5] != "lo":
                out.append(p[5])
    except OSError:
        pass
    return out


def check_ipv6_leak(state):
    tor_on = bool(state.get("tor"))
    addrs = _global_v6_addrs()
    if backend.ipv6_disabled() or not addrs:
        return _c("ipv6_leak", "leak", "IPv6 leak", PASS,
                  "No global IPv6 address — nothing can leak over IPv6.")
    try:
        ip6 = backend.http_get("https://api6.ipify.org", 6).decode().strip()
    except Exception:
        return _c("ipv6_leak", "leak", "IPv6 leak", WARN if tor_on else INFO,
                  "Global IPv6 present on {ifs} but outbound IPv6 is blocked.",
                  ifs=", ".join(sorted(set(addrs))))
    return _c("ipv6_leak", "leak", "IPv6 leak", FAIL if tor_on else WARN,
              "IPv6 traffic bypasses Tor/VPN and exposes {ip6}. Disable IPv6.",
              ip6=ip6)


def check_udp_leak(state):
    """In Tor mode only TCP + DNS can be anonymised. Send one NTP packet to a
    public server: any reply means UDP escapes the kill-switch."""
    if not state.get("tor"):
        return _c("udp_leak", "leak", "Kill-switch (UDP)", SKIP,
                  "Only meaningful while Tor routing is on.")
    pkt = b"\x1b" + 47 * b"\0"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.sendto(pkt, ("162.159.200.1", 123))
        s.recvfrom(64)
        return _c("udp_leak", "leak", "Kill-switch (UDP)", FAIL,
                  "A UDP packet left the machine outside Tor (NTP reply received).")
    except OSError:
        return _c("udp_leak", "leak", "Kill-switch (UDP)", PASS,
                  "Non-Tor UDP is dropped by the kill-switch.")
    finally:
        s.close()


def check_onion_dns(state):
    if not state.get("tor"):
        return _c("onion", "leak", ".onion resolution", SKIP,
                  "Only tested in Tor mode — resolving .onion without Tor leaks it to your ISP.")
    host = "duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion"
    try:
        ip = socket.getaddrinfo(host, 80, socket.AF_INET)[0][4][0]
    except OSError as e:
        return _c("onion", "leak", ".onion resolution", WARN,
                  ".onion names do not resolve through Tor: {err}", err=backend.explain_error(e))
    if ip.startswith("10.") and 192 <= int(ip.split(".")[1]) <= 255:
        return _c("onion", "leak", ".onion resolution", PASS,
                  ".onion names are mapped by Tor ({ip}).", ip=ip)
    return _c("onion", "leak", ".onion resolution", FAIL,
              ".onion resolved outside Tor's virtual range ({ip}).", ip=ip)


def check_tor_service(state):
    rc, act = _run(["systemctl", "is-active", "tor"])
    if act != "active":
        rc, act = _run(["systemctl", "is-active", "tor@default"])
    socks = False
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(("127.0.0.1", 9050)); socks = True
    except OSError:
        pass
    finally:
        s.close()
    if act == "active" and socks:
        return _c("tor_svc", "leak", "Tor service", PASS,
                  "tor.service running, SOCKS 127.0.0.1:9050 open.")
    if state.get("tor"):
        return _c("tor_svc", "leak", "Tor service", FAIL,
                  "Tor mode is on but the Tor service is not answering.")
    return _c("tor_svc", "leak", "Tor service", INFO, "System Tor is not running.")


# --------------------------------------------------------------------------- #
#  PRE-FLIGHT (local, before going onto .onion / darknet)
# --------------------------------------------------------------------------- #
TB_PREFS_GLOBS = [
    "~/.local/share/torbrowser/tbb/*/tor-browser*/Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
    "~/tor-browser*/Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
    "~/.tor-browser*/Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
    "~/.local/opt/tor-browser*/Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
    "/opt/tor-browser*/Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
]
SLIDER = {"1": "Safest", "2": "Safer", "4": "Standard"}


def _tor_browser_prefs():
    for g in TB_PREFS_GLOBS:
        hits = glob.glob(os.path.expanduser(g))
        if hits:
            return hits[0]
    return None


def check_tor_browser():
    prefs = _tor_browser_prefs()
    installed = prefs or any(shutil.which(b) for b in
                             ("torbrowser-launcher", "tor-browser", "torbrowser"))
    if not installed:
        return _c("tb", "preflight", "Tor Browser", FAIL,
                  "Not installed. Use Tor Browser for .onion — never a normal browser.")
    if not prefs:
        return _c("tb", "preflight", "Tor Browser", WARN,
                  "Installed but never started — open it once, then set Security Level to Safest.")
    level = "4"
    try:
        m = re.search(r'"browser\.security_level\.security_slider",\s*(\d)', open(prefs).read())
        if m: level = m.group(1)
    except OSError:
        pass
    name = SLIDER.get(level, "Standard")
    if level == "1":
        return _c("tb", "preflight", "Tor Browser", PASS,
                  "Installed, Security Level: {lvl} (JavaScript off).", lvl=name)
    return _c("tb", "preflight", "Tor Browser", WARN,
              "Security Level is {lvl}. Set it to Safest before visiting .onion sites.",
              lvl=name)


def check_webrtc():
    profs = [p for p in glob.glob(os.path.expanduser("~/.mozilla/firefox/*"))
             + glob.glob(os.path.expanduser("~/.librewolf/*"))
             if os.path.exists(os.path.join(p, "prefs.js"))]
    if not profs:
        return _c("webrtc", "preflight", "WebRTC (Firefox)", SKIP, "No Firefox profile found.")
    bad = []
    for p in profs:
        txt = ""
        for f in ("user.js", "prefs.js"):
            try: txt += open(os.path.join(p, f)).read()
            except OSError: pass
        if not re.search(r'"media\.peerconnection\.enabled",\s*false', txt):
            bad.append(os.path.basename(p))
    if bad:
        return _c("webrtc", "preflight", "WebRTC (Firefox)", WARN,
                  "WebRTC can reveal your real IP in {n} profile(s). Use “Harden Firefox”.",
                  n=len(bad))
    return _c("webrtc", "preflight", "WebRTC (Firefox)", PASS,
              "WebRTC disabled in every Firefox profile.")


def check_browser_traces():
    """Visit history already sitting on disk in normal browsers."""
    import sqlite3
    visits, chrom = 0, 0
    for prof in backend._ff_profiles():
        db = os.path.join(prof, "places.sqlite")
        if not os.path.exists(db):
            continue
        try:
            con = sqlite3.connect(f"file:{db}?immutable=1", uri=True, timeout=1)
            visits += con.execute("SELECT count(*) FROM moz_historyvisits").fetchone()[0]
            con.close()
        except sqlite3.Error:
            pass
    for root in backend.CHROMIUM_ROOTS:
        for h in glob.glob(os.path.join(os.path.expanduser(root), "*", "History")):
            if os.path.getsize(h) > 64 * 1024:
                chrom += 1
    if not visits and not chrom:
        return _c("btrace", "preflight", "Browser history on disk", PASS,
                  "No browsing history stored by regular browsers.")
    parts = []
    if visits: parts.append(f"Firefox: {visits}")
    if chrom: parts.append(f"Chromium: {chrom}")
    return _c("btrace", "preflight", "Browser history on disk", WARN,
              "Regular browsers keep history on disk ({where}). Clean it or use the RAM-only browser.",
              where=", ".join(parts))


def check_ff_wipe():
    profs = backend._ff_profiles()
    if not profs:
        return _c("ffwipe", "preflight", "Firefox wipe on close", SKIP, "No Firefox profile found.")
    ok = 0
    for p in profs:
        try:
            if backend.FF_WIPE_MARK in open(os.path.join(p, "user.js")).read():
                ok += 1
        except OSError:
            pass
    if ok == len(profs):
        return _c("ffwipe", "preflight", "Firefox wipe on close", PASS,
                  "Every Firefox profile clears history, cookies and cache on close.")
    return _c("ffwipe", "preflight", "Firefox wipe on close", WARN,
              "{n} Firefox profile(s) keep history and cookies after closing.",
              n=len(profs) - ok)


def check_timezone():
    _, tz = _run(["timedatectl", "show", "-p", "Timezone", "--value"])
    if not tz:
        try: tz = os.path.realpath("/etc/localtime").split("zoneinfo/")[-1]
        except OSError: tz = "?"
    if tz in ("UTC", "Etc/UTC", "Universal", "Zulu", "Etc/Universal"):
        return _c("tz", "preflight", "Timezone", PASS, "System clock reports UTC.")
    return _c("tz", "preflight", "Timezone", WARN,
              "Timezone is {tz} — it narrows down your location. Force UTC.", tz=tz)


def check_clock():
    _, sync = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"])
    if sync == "yes":
        return _c("clock", "preflight", "Clock sync", PASS,
                  "Clock is NTP-synchronised (Tor rejects skewed clocks).")
    return _c("clock", "preflight", "Clock sync", WARN,
              "Clock is not synchronised — Tor may fail and skew is a fingerprint.")


def check_hostname(state):
    if state.get("hostname"):
        return _c("host", "preflight", "Hostname", PASS,
                  "Randomized ({h}).", h=backend.hostname())
    return _c("host", "preflight", "Hostname", WARN,
              "Real hostname “{h}” is broadcast on the LAN (DHCP, mDNS).",
              h=backend.hostname())


def check_mac(state):
    if state.get("mac_spoofed") or state.get("nm_mac"):
        return _c("mac", "preflight", "MAC address", PASS, "Hardware MAC is hidden.")
    return _c("mac", "preflight", "MAC address", WARN,
              "Hardware MAC is visible to the local network / Wi-Fi operator.")


def check_firewall(state):
    if state.get("firewall") or state.get("tor"):
        return _c("fw", "preflight", "Firewall", PASS, "Inbound default-deny is active.")
    return _c("fw", "preflight", "Firewall", WARN, "No HawkOpsec firewall is active.")


def check_listeners():
    found = set()
    for fn, v6 in (("/proc/net/tcp", False), ("/proc/net/tcp6", True)):
        try:
            lines = open(fn).read().splitlines()[1:]
        except OSError:
            continue
        for ln in lines:
            p = ln.split()
            if len(p) < 4 or p[3] != "0A":           # 0A = LISTEN
                continue
            addr, port = p[1].split(":")
            port = int(port, 16)
            loop = (addr == "0100007F" or addr.endswith("0100007F")
                    or addr == "00000000000000000000000001000000"
                    or (not v6 and addr.endswith("7F")))
            if not loop:
                try: name = socket.getservbyport(port)
                except OSError: name = ""
                found.add(f"{port}{'/' + name if name else ''}")
    if not found:
        return _c("listen", "preflight", "Open ports", PASS,
                  "No service listens on a network interface.")
    return _c("listen", "preflight", "Open ports", WARN,
              "Services reachable from the network: {ports}",
              ports=", ".join(sorted(found, key=lambda x: int(x.split('/')[0]))))


def check_identity_apps():
    running = set()
    for c in glob.glob("/proc/[0-9]*/comm"):
        try: n = open(c).read().strip()
        except OSError: continue
        if n in IDENTITY_APPS:
            running.add(IDENTITY_APPS[n])
    if running:
        return _c("apps", "preflight", "Identity-linked apps", WARN,
                  "Close these before the session: {apps}", apps=", ".join(sorted(running)))
    return _c("apps", "preflight", "Identity-linked apps", PASS,
              "No messenger / sync / remote-desktop app is running.")


def check_webcam(state):
    cams = glob.glob("/dev/video*")
    if state.get("webcam_off") or not cams:
        return _c("cam", "preflight", "Webcam", PASS, "No camera device available.")
    return _c("cam", "preflight", "Webcam", WARN,
              "{n} camera device(s) active. Disable the webcam or cover it.", n=len(cams))


def check_disk_crypto():
    rc, out = _run(["lsblk", "-J", "-o", "NAME,TYPE"])
    if rc != 0:
        return _c("crypt", "preflight", "Disk encryption", SKIP, "lsblk not available.")
    if '"crypt"' in out:
        return _c("crypt", "preflight", "Disk encryption", PASS,
                  "A LUKS/dm-crypt volume is in use.")
    return _c("crypt", "preflight", "Disk encryption", WARN,
              "No encrypted volume found — a seized disk exposes everything.")


def check_swap(state):
    try:
        rows = open("/proc/swaps").read().splitlines()[1:]
    except OSError:
        rows = []
    plain = [r.split()[0] for r in rows if r and "zram" not in r.split()[0]
             and not r.split()[0].startswith("/dev/dm-")]
    if not plain:
        return _c("swap", "preflight", "Swap", PASS, "No unencrypted swap on disk.")
    return _c("swap", "preflight", "Swap", WARN,
              "Unencrypted swap ({dev}) can write RAM contents to disk.", dev=", ".join(plain))


def check_root():
    if os.geteuid() == 0:
        return _c("root", "preflight", "Session user", WARN,
                  "HawkOpsec GUI is running as root — browse as a normal user.")
    return _c("root", "preflight", "Session user", PASS, "Running as an unprivileged user.")


def check_vpn():
    ifs = [n for n in os.listdir("/sys/class/net")
           if n.startswith(("wg", "tun", "tailscale", "proton", "mullvad", "nordlynx"))]
    if ifs:
        return _c("vpn", "preflight", "VPN", INFO,
                  "VPN interface up: {ifs}. Tor runs on top of it.", ifs=", ".join(ifs))
    return _c("vpn", "preflight", "VPN", INFO,
              "No VPN — your ISP can see that you connect to Tor (use bridges if that matters).")


# --------------------------------------------------------------------------- #
def run_all() -> dict:
    st = backend.read_state()
    ipres = backend.ip_check(retries=2, wait=True)
    if "error" not in ipres:
        maybe_store_real_fp(ipres, st)
    checks = [
        check_exit_ip(st, ipres),
        check_dns_leak(st, ipres),
        check_ipv6_leak(st),
        check_udp_leak(st),
        check_onion_dns(st),
        check_tor_service(st),
        check_tor_browser(),
        check_webrtc(),
        check_ff_wipe(),
        check_browser_traces(),
        check_timezone(),
        check_clock(),
        check_hostname(st),
        check_mac(st),
        check_firewall(st),
        check_listeners(),
        check_identity_apps(),
        check_webcam(st),
        check_disk_crypto(),
        check_swap(st),
        check_root(),
        check_vpn(),
    ]
    scored = [c for c in checks if c["status"] in (PASS, WARN, FAIL)]
    fails = sum(c["status"] == FAIL for c in scored)
    warns = sum(c["status"] == WARN for c in scored)
    passed = sum(c["status"] == PASS for c in scored)
    tor_ready = bool(st.get("tor")) or checks[6]["status"] == PASS
    if fails or not tor_ready:
        verdict = "NOT READY"
    elif warns > 2:
        verdict = "RISKY"
    else:
        verdict = "READY"
    return {"checks": checks, "verdict": verdict, "passed": passed,
            "total": len(scored), "fails": fails, "warns": warns,
            "ip": ipres, "ts": time.strftime("%H:%M:%S")}
