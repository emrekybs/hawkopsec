"""
HawkOpsec — GUI-side backend.

Bridges the unprivileged GUI to the root helper via pkexec, reads the
world-readable state file for module flags, and performs cheap read-only status
checks that don't need root (MAC, IPv6, hostname, resolvers, Tor/IP).
"""
import json
import os
import shutil
import subprocess
import urllib.request

STATE_FILE = "/var/lib/hawkopsec/state.json"

# Installed location; falls back to the copy shipped next to this module.
_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hawkopsec-helper")
HELPER_CANDIDATES = ["/usr/local/lib/hawkopsec/hawkopsec-helper", _LOCAL]


def helper_path() -> str:
    for p in HELPER_CANDIDATES:
        if os.path.exists(p):
            return p
    return HELPER_CANDIDATES[0]


def run_priv(verb: str, *args) -> tuple[int, str]:
    """Run a privileged verb through pkexec. Blocking — call from a worker."""
    cmd = ["pkexec", helper_path(), verb, *[str(a) for a in args]]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "pkexec not found — install policykit-1."


# --------------------------------------------------------------------------- #
#  state + read-only status
# --------------------------------------------------------------------------- #
def run_pkexec(path) -> tuple[int, str]:
    """Run an arbitrary script as root via pkexec (used by the in-app uninstaller)."""
    try:
        p = subprocess.run(["pkexec", path], capture_output=True, text=True)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "pkexec not found"


def read_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


_VIRT = ("lo", "docker", "veth", "br-", "virbr", "vmnet", "vboxnet", "tun", "tap",
         "wg", "tailscale", "zt", "ifb", "dummy", "sit", "gre", "bond", "kube",
         "cni", "flannel")


def _real_iface(name: str) -> bool:
    return not any(name == p or name.startswith(p) for p in _VIRT)


def interfaces() -> list[dict]:
    """Each: {name, mac, spoofed}. Virtual/bridge interfaces are excluded."""
    st = read_state()
    spoofed = st.get("mac_spoofed", {})
    out = []
    base = "/sys/class/net"
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        if not _real_iface(name):
            continue
        try:
            mac = open(f"{base}/{name}/address").read().strip()
        except OSError:
            mac = "??"
        out.append({"name": name, "mac": mac, "spoofed": name in spoofed})
    return out


def ipv6_disabled() -> bool:
    try:
        return open("/proc/sys/net/ipv6/conf/all/disable_ipv6").read().strip() == "1"
    except OSError:
        return False


def hostname() -> str:
    try:
        return open("/etc/hostname").read().strip()
    except OSError:
        return os.uname().nodename


def resolvers() -> list[str]:
    out = []
    try:
        for line in open("/etc/resolv.conf"):
            if line.strip().startswith("nameserver"):
                out.append(line.split()[1])
    except OSError:
        pass
    return out


def tor_check(timeout: float = 8.0) -> dict:
    """Query check.torproject.org. Returns {is_tor, ip} or {error}."""
    try:
        req = urllib.request.Request(
            "https://check.torproject.org/api/ip",
            headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        return {"is_tor": bool(data.get("IsTor")), "ip": data.get("IP", "?")}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}" or "no network"}


# --------------------------------------------------------------------------- #
#  user-space trace cleaning (no root)
# --------------------------------------------------------------------------- #
def clean_user_traces() -> list[str]:
    home = os.path.expanduser("~")
    cleaned = []

    def rm(path, label):
        try:
            if os.path.isdir(path):
                for f in os.listdir(path):
                    fp = os.path.join(path, f)
                    shutil.rmtree(fp, ignore_errors=True) if os.path.isdir(fp) \
                        else os.remove(fp)
                cleaned.append(label)
            elif os.path.exists(path):
                open(path, "w").close()
                cleaned.append(label)
        except OSError:
            pass

    rm(os.path.join(home, ".bash_history"), "bash history")
    rm(os.path.join(home, ".zsh_history"), "zsh history")
    rm(os.path.join(home, ".python_history"), "python history")
    rm(os.path.join(home, ".local/share/recently-used.xbel"), "recent files")
    rm(os.path.join(home, ".cache/thumbnails"), "thumbnails")
    rm(os.path.join(home, ".local/share/Trash/files"), "trash")
    rm(os.path.join(home, ".local/share/Trash/info"), "trash metadata")
    return cleaned


# --------------------------------------------------------------------------- #
#  anonymous browser / browser hardening / metadata / secure delete / log
# --------------------------------------------------------------------------- #
def launch_anon_browser() -> tuple[int, str]:
    """Launch Tor Browser if present, else a firejail-sandboxed Firefox."""
    import subprocess
    for c in (["torbrowser-launcher"], ["tor-browser"], ["torbrowser"]):
        if shutil.which(c[0]):
            subprocess.Popen(c, start_new_session=True)
            return 0, f"launched {c[0]}"
    if shutil.which("firejail") and shutil.which("firefox"):
        subprocess.Popen(["firejail", "--private", "firefox", "--no-remote"],
                         start_new_session=True)
        return 0, "launched firejail firefox (set SOCKS 127.0.0.1:9050 for Tor)"
    if shutil.which("firefox"):
        subprocess.Popen(["firefox", "--private-window"], start_new_session=True)
        return 0, "launched firefox — install Tor Browser for real anonymity"
    return 1, "no browser found; install torbrowser-launcher"


FF_MARK = "// >>> HAWKOPSEC >>>"
FF_PREFS = """// >>> HAWKOPSEC >>>
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("media.peerconnection.enabled", false);
user_pref("media.peerconnection.ice.default_address_only", true);
user_pref("webgl.disabled", true);
user_pref("geo.enabled", false);
user_pref("dom.battery.enabled", false);
user_pref("beacon.enabled", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.predictor.enabled", false);
user_pref("privacy.firstparty.isolate", true);
// <<< HAWKOPSEC <<<
"""


def harden_firefox() -> tuple[int, str]:
    """Write a hardening user.js (WebRTC off, resistFingerprinting) into every
    Firefox profile found. Best-effort; Tor Browser is still recommended."""
    import glob
    roots = glob.glob(os.path.expanduser("~/.mozilla/firefox/*")) \
        + glob.glob(os.path.expanduser("~/.librewolf/*"))
    done = 0
    for prof in roots:
        if not os.path.isdir(prof) or not os.path.exists(os.path.join(prof, "prefs.js")):
            continue
        uj = os.path.join(prof, "user.js")
        try:
            existing = open(uj).read() if os.path.exists(uj) else ""
            if FF_MARK not in existing:
                with open(uj, "a") as f:
                    f.write(("\n" if existing else "") + FF_PREFS)
            done += 1
        except OSError:
            pass
    if done:
        return 0, f"hardened {done} Firefox profile(s) — restart the browser"
    return 1, "no Firefox profile found (open Firefox once first)"


def strip_metadata(paths) -> tuple[int, str]:
    import subprocess
    tool = None
    if shutil.which("mat2"):
        tool = lambda p: ["mat2", "--inplace", p]
    elif shutil.which("exiftool"):
        tool = lambda p: ["exiftool", "-all=", "-overwrite_original", p]
    if not tool:
        return 1, "install 'mat2' (recommended) or 'perl-image-exiftool'"
    n = 0
    for p in paths:
        r = subprocess.run(tool(p), capture_output=True, text=True)
        if r.returncode == 0:
            n += 1
    return 0, f"metadata stripped from {n}/{len(paths)} file(s)"


def secure_delete(paths) -> tuple[int, str]:
    import subprocess
    n = 0
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p, topdown=False):
                for f in files:
                    subprocess.run(["shred", "-u", "-z", "-n", "3", os.path.join(root, f)],
                                   capture_output=True)
            try:
                shutil.rmtree(p, ignore_errors=True); n += 1
            except OSError:
                pass
        elif os.path.exists(p):
            r = subprocess.run(["shred", "-u", "-z", "-n", "3", p], capture_output=True)
            if r.returncode == 0:
                n += 1
    return 0, f"securely deleted {n}/{len(paths)} item(s)"


def read_log(lines: int = 400) -> str:
    for p in ("/var/lib/hawkopsec/helper.log",):
        try:
            data = open(p).read().splitlines()
            return "\n".join(data[-lines:])
        except OSError:
            continue
    return ""
