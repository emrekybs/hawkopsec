"""
HawkOpsec — GUI-side backend.

Bridges the unprivileged GUI to the root helper via pkexec, reads the
world-readable state file for module flags, and performs cheap read-only status
checks that don't need root (MAC, IPv6, hostname, resolvers, Tor/IP).
"""
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

STATE_FILE = "/var/lib/hawkopsec/state.json"

# Installed (root-owned) location; the copy shipped inside the package is only
# used when it is root-owned and not writable by anyone else (e.g. a system-wide
# source install). A pip --user copy is user-writable — running it as root would
# let any process of this user escalate, so it is refused.
SYSTEM_HELPER = "/usr/local/lib/hawkopsec/hawkopsec-helper"
_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hawkopsec-helper")
HELPER_CANDIDATES = [SYSTEM_HELPER, _LOCAL]


def _root_owned(p: str) -> bool:
    try:
        st = os.stat(p)
        return st.st_uid == 0 and not (st.st_mode & 0o022)
    except OSError:
        return False


def helper_path() -> str:
    for p in HELPER_CANDIDATES:
        if os.path.exists(p) and _root_owned(p):
            return p
    return ""


def system_integrated() -> bool:
    return bool(helper_path())


def run_priv(verb: str, *args) -> tuple[int, str]:
    """Run a privileged verb through pkexec. Blocking — call from a worker."""
    h = helper_path()
    if not h:
        return 1, ("system helper not installed — run: sudo hawkopsec-setup "
                   "(or accept the setup prompt at start-up)")
    cmd = ["pkexec", h, verb, *[str(a) for a in args]]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "pkexec not found — install polkit (policykit-1)."


def run_setup(launcher: str) -> tuple[int, str]:
    """First-run: install root helper/polkit/menu entry via pkexec."""
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_system.py")
    cmd = ["pkexec", sys.executable, script, "--src",
           os.path.dirname(os.path.abspath(__file__))]
    if launcher:
        cmd += ["--exec", launcher]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "pkexec not found — run: sudo hawkopsec-setup"


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


# --------------------------------------------------------------------------- #
#  exit-IP check (multi-endpoint, retries, readable errors)
# --------------------------------------------------------------------------- #
UA = "Mozilla/5.0 (Windows NT 10.0; rv:128.0) Gecko/20100101 Firefox/128.0"


def explain_error(e) -> str:
    """Turn urllib/socket exceptions into a short human-readable reason.

    The old code printed f"URLError: {e}" — str(URLError) is "<urlopen error …>",
    which the HTML console swallowed as a tag, so users only saw "URLError: ".
    """
    r = getattr(e, "reason", e)
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(r, socket.gaierror):
        return "DNS resolution failed (network or resolver not ready)"
    if isinstance(r, (socket.timeout, TimeoutError)):
        return "timed out"
    if isinstance(r, ConnectionRefusedError):
        return "connection refused (Tor/firewall blocking?)"
    if isinstance(r, ConnectionResetError):
        return "connection reset (endpoint blocked or Tor circuit dropped)"
    if isinstance(r, ssl.SSLError):
        return f"TLS error: {getattr(r, 'reason', None) or r}"
    if isinstance(r, OSError) and getattr(r, "strerror", None):
        return r.strerror
    msg = str(r).strip()
    return msg or type(e).__name__


def http_get(url: str, timeout: float = 8.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def http_json(url: str, timeout: float = 8.0):
    return json.loads(http_get(url, timeout).decode("utf-8", "replace"))


def wait_for_network(timeout: float = 20.0, host: str = "check.torproject.org") -> bool:
    """After a mode change (NetworkManager/resolved/Tor restarts) DNS is briefly
    down. Poll name resolution until it works or we give up."""
    end = time.time() + timeout
    while time.time() < end:
        try:
            socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
            return True
        except OSError:
            time.sleep(1.0)
    return False


# (url, parser) — parser returns {"ip", "is_tor"?, "country"?, "org"?}
def _p_torproject(d): return {"ip": d.get("IP"), "is_tor": bool(d.get("IsTor"))}
def _p_ipinfo(d):     return {"ip": d.get("ip"), "country": d.get("country"), "org": d.get("org")}
def _p_ifconfig(d):   return {"ip": d.get("ip"), "country": d.get("country_iso"),
                              "org": d.get("asn_org")}
def _p_ipify(d):      return {"ip": d.get("ip")}


IP_ENDPOINTS = [
    ("https://check.torproject.org/api/ip", _p_torproject),
    ("https://ipinfo.io/json",              _p_ipinfo),
    ("https://ifconfig.co/json",            _p_ifconfig),
    ("https://api.ipify.org?format=json",   _p_ipify),
]

_exit_list_cache = {"t": 0.0, "ips": set()}


def tor_exit_list() -> set:
    """Tor Project bulk exit list (cached 30 min) — used to verify is_tor when
    check.torproject.org itself is unreachable."""
    if time.time() - _exit_list_cache["t"] < 1800 and _exit_list_cache["ips"]:
        return _exit_list_cache["ips"]
    try:
        txt = http_get("https://check.torproject.org/torbulkexitlist", 12).decode()
        ips = {l.strip() for l in txt.splitlines() if l.strip() and not l.startswith("#")}
        _exit_list_cache.update(t=time.time(), ips=ips)
    except Exception:
        pass
    return _exit_list_cache["ips"]


def ip_check(retries: int = 3, timeout: float = 10.0, wait: bool = True) -> dict:
    """Return {ip, is_tor (True/False/None), country, org, source} or
    {error, tried}. Tries several endpoints, retries transient failures."""
    if wait:
        wait_for_network(20.0)
    errors = []
    res = None
    for attempt in range(retries):
        for url, parse in IP_ENDPOINTS:
            try:
                r = parse(http_json(url, timeout))
                if r.get("ip"):
                    r["source"] = url.split("/")[2]
                    res = r
                    break
            except Exception as e:
                errors.append((url.split('/')[2].split('?')[0], explain_error(e)))
        if res:
            break
        time.sleep(2.0 * (attempt + 1))
    if not res:
        uniq = list(dict.fromkeys(errors))
        return {"error": uniq[-1][1] if uniq else "no network",
                "tried": [f"{h}: {r}" for h, r in uniq]}
    # enrich: geo/org when the primary (torproject) answered, Tor status otherwise
    if "org" not in res:
        try:
            g = _p_ipinfo(http_json("https://ipinfo.io/json", 8))
            if g.get("ip") == res["ip"]:
                res["country"], res["org"] = g.get("country"), g.get("org")
        except Exception:
            pass
    if "is_tor" not in res:
        ex = tor_exit_list()
        res["is_tor"] = (res["ip"] in ex) if ex else None
    return res


def tor_check(timeout: float = 10.0) -> dict:
    """Backwards-compatible wrapper."""
    return ip_check(timeout=timeout)


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
    """Launch Tor Browser if present, else a firejail-sandboxed Firefox.

    When HawkOpsec's system-wide Tor routing is active, Tor Browser is told to
    use the system Tor SOCKS port instead of starting its own Tor — otherwise
    its traffic would go Tor-over-Tor (slower, and not recommended)."""
    env = dict(os.environ)
    system_tor = bool(read_state().get("tor"))
    if system_tor:
        env.update(TOR_SKIP_LAUNCH="1", TOR_PROVIDER="none", TOR_SKIP_CONTROLPORT="1",
                   TOR_SOCKS_HOST="127.0.0.1", TOR_SOCKS_PORT="9050")
    for c in (["torbrowser-launcher"], ["tor-browser"], ["torbrowser"]):
        if shutil.which(c[0]):
            subprocess.Popen(c, start_new_session=True, env=env)
            return 0, f"launched {c[0]}" + (" (using system Tor on :9050)" if system_tor else "")
    if shutil.which("firejail") and shutil.which("firefox"):
        subprocess.Popen(["firejail", "--private", "firefox", "--no-remote"],
                         start_new_session=True)
        return 0, ("launched firejail firefox — traffic goes through system Tor"
                   if system_tor else
                   "launched firejail firefox — NOT anonymous: enable Tor or install Tor Browser")
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


# --------------------------------------------------------------------------- #
#  browser traces: RAM-only browser, wipe-on-close, cleaning, clipboard
# --------------------------------------------------------------------------- #
FF_WIPE_MARK = "// >>> HAWKOPSEC-WIPE >>>"
FF_WIPE = """// >>> HAWKOPSEC-WIPE >>>
user_pref("privacy.sanitize.sanitizeOnShutdown", true);
user_pref("privacy.clearOnShutdown.cache", true);
user_pref("privacy.clearOnShutdown.cookies", true);
user_pref("privacy.clearOnShutdown.downloads", true);
user_pref("privacy.clearOnShutdown.formdata", true);
user_pref("privacy.clearOnShutdown.history", true);
user_pref("privacy.clearOnShutdown.offlineApps", true);
user_pref("privacy.clearOnShutdown.sessions", true);
user_pref("privacy.clearOnShutdown_v2.cache", true);
user_pref("privacy.clearOnShutdown_v2.cookiesAndStorage", true);
user_pref("privacy.clearOnShutdown_v2.historyFormDataAndDownloads", true);
user_pref("browser.cache.disk.enable", false);
user_pref("browser.sessionstore.privacy_level", 2);
user_pref("browser.formfill.enable", false);
user_pref("signon.rememberSignons", false);
user_pref("browser.download.manager.addToRecentDocs", false);
// <<< HAWKOPSEC-WIPE <<<
"""

AMNESIC_PREFS = FF_PREFS + FF_WIPE + """
user_pref("browser.privatebrowsing.autostart", true);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.enabled", false);
user_pref("app.normandy.enabled", false);
user_pref("extensions.pocket.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.telemetry", false);
user_pref("geo.provider.network.url", "");
user_pref("network.http.referer.XOriginPolicy", 2);
user_pref("media.navigator.enabled", false);
"""

FF_ROOTS = ("~/.mozilla/firefox/*", "~/.librewolf/*",
            "~/snap/firefox/common/.mozilla/firefox/*",
            "~/.var/app/org.mozilla.firefox/.mozilla/firefox/*")
CHROMIUM_ROOTS = ("~/snap/chromium/common/chromium", "~/.config/chromium", "~/.config/google-chrome", "~/.config/BraveSoftware/Brave-Browser",
                  "~/.config/vivaldi", "~/.config/microsoft-edge", "~/.config/opera")
BROWSER_PROCS = {"firefox", "firefox-esr", "firefox-bin", "librewolf", "chromium",
                 "chrome", "brave", "vivaldi-bin", "msedge", "opera"}


def _ff_profiles():
    import glob
    out = []
    for g in FF_ROOTS:
        out += [p for p in glob.glob(os.path.expanduser(g))
                if os.path.isfile(os.path.join(p, "prefs.js"))]
    return out


def running_browsers() -> list[str]:
    import glob
    found = set()
    for c in glob.glob("/proc/[0-9]*/comm"):
        try:
            n = open(c).read().strip()
        except OSError:
            continue
        if n in BROWSER_PROCS:
            found.add(n)
    return sorted(found)


FF_CANDIDATES = ["firefox", "firefox-esr", "librewolf", "firefox-bin", "waterfox"]
FF_PATHS = ["/snap/bin/firefox", "/usr/lib/firefox/firefox", "/usr/lib/firefox-esr/firefox-esr",
            "/usr/lib64/firefox/firefox", "/opt/firefox/firefox", "/usr/local/bin/firefox",
            "/var/lib/flatpak/exports/bin/org.mozilla.firefox",
            os.path.expanduser("~/.local/share/flatpak/exports/bin/org.mozilla.firefox")]


def find_firefox():
    """Return (argv_prefix, kind) — kind is 'native', 'snap' or 'flatpak'.
    Menu-launched apps often lack /snap/bin in PATH, so known paths are tried too."""
    cands = [shutil.which(n) for n in FF_CANDIDATES] + FF_PATHS
    for c in cands:
        if not c or not os.path.exists(c):
            continue
        real = os.path.realpath(c)
        if "/snap/" in c or real.endswith("/usr/bin/snap"):
            return [c], "snap"
        if "flatpak" in c:
            return ["flatpak", "run", "org.mozilla.firefox"], "flatpak"
        return [c], "native"
    if shutil.which("flatpak"):
        r = subprocess.run(["flatpak", "info", "org.mozilla.firefox"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return ["flatpak", "run", "org.mozilla.firefox"], "flatpak"
    return None, None


def launch_amnesic_browser() -> tuple[int, str]:
    """Firefox with a throw-away profile in RAM (/dev/shm): no history, cache,
    cookies or session ever touch the disk; the profile is deleted on exit.
    Snap / Flatpak Firefox can't read /dev/shm, so they get a profile inside
    their own sandbox directory instead (still deleted on close)."""
    cmd, kind = find_firefox()
    if not cmd:
        return 1, "Firefox not found (checked PATH, /snap, /usr/lib, Flatpak) — install firefox"
    if kind == "snap":
        base = os.path.expanduser("~/snap/firefox/common")
    elif kind == "flatpak":
        base = os.path.expanduser("~/.var/app/org.mozilla.firefox/cache")
    else:
        base = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else None
    if base:
        os.makedirs(base, exist_ok=True)
    prof = tempfile.mkdtemp(prefix="hawkopsec-ram-", dir=base)
    os.chmod(prof, 0o700)
    with open(os.path.join(prof, "user.js"), "w") as f:
        f.write(AMNESIC_PREFS)
    env = dict(os.environ, MOZ_CRASHREPORTER_DISABLE="1")
    if kind == "flatpak":
        cmd = cmd[:2] + [f"--filesystem={prof}"] + cmd[2:]
    cmd = cmd + ["--no-remote", "--new-instance", "--profile", prof, "--private-window"]
    try:
        proc = subprocess.Popen(cmd, start_new_session=True, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        shutil.rmtree(prof, ignore_errors=True)
        return 1, f"could not start Firefox: {e}"

    def _reap():
        proc.wait()
        shutil.rmtree(prof, ignore_errors=True)
    threading.Thread(target=_reap, daemon=True).start()
    where = "RAM (/dev/shm)" if prof.startswith("/dev/shm") else f"a temp folder ({kind} Firefox)"
    via = " — traffic goes through system Tor" if read_state().get("tor") else ""
    return 0, f"RAM-only browser started; profile lives in {where} and is deleted on close{via}"


def firefox_wipe_on_close() -> tuple[int, str]:
    done = 0
    for prof in _ff_profiles():
        uj = os.path.join(prof, "user.js")
        try:
            existing = open(uj).read() if os.path.exists(uj) else ""
            if FF_WIPE_MARK not in existing:
                with open(uj, "a") as f:
                    f.write(("\n" if existing else "") + FF_WIPE)
            done += 1
        except OSError:
            pass
    if done:
        return 0, f"{done} Firefox profile(s) now wipe history/cookies/cache on close — restart the browser"
    return 1, "no Firefox profile found (open Firefox once first)"


def _rm(path):
    try:
        if os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.lexists(path):
            os.remove(path)
        else:
            return False
        return True
    except OSError:
        return False


def _ff_clear_history(prof):
    """Delete visit history but KEEP bookmarks (places.sqlite holds both)."""
    import sqlite3
    db = os.path.join(prof, "places.sqlite")
    if not os.path.exists(db):
        return False
    try:
        con = sqlite3.connect(db, timeout=2)
        cur = con.cursor()
        cur.execute("DELETE FROM moz_historyvisits")
        cur.execute("DELETE FROM moz_inputhistory")
        cur.execute("DELETE FROM moz_annos")   # download history lives here
        cur.execute("DELETE FROM moz_places WHERE id NOT IN "
                    "(SELECT fk FROM moz_bookmarks WHERE fk IS NOT NULL)")
        con.commit(); cur.execute("VACUUM"); con.close()
        return True
    except sqlite3.Error:
        return False


def clean_browser_traces() -> tuple[int, str]:
    """History, cookies, cache, sessions, site storage and form data of every
    Firefox / Chromium-family profile. Bookmarks and saved passwords are kept."""
    import glob
    run = running_browsers()
    if run:
        return 1, "close these browsers first: " + ", ".join(run)
    n_ff = n_ch = 0
    for prof in _ff_profiles():
        for f in ("cookies.sqlite", "cookies.sqlite-wal", "formhistory.sqlite",
                  "webappsstore.sqlite", "sessionstore.jsonlz4", "sessionstore-backups",
                  "storage/default", "storage/temporary", "cache2", "thumbnails",
                  "favicons.sqlite", "favicons.sqlite-wal", "places.sqlite-wal",
                  "SiteSecurityServiceState.bin", "content-prefs.sqlite",
                  "datareporting", "crashes", "minidumps", "downloads.json"):
            _rm(os.path.join(prof, f))
        _ff_clear_history(prof)
        _rm(os.path.join(os.path.expanduser("~/.cache/mozilla/firefox"),
                         os.path.basename(prof)))
        n_ff += 1
    for root in CHROMIUM_ROOTS:
        root = os.path.expanduser(root)
        if not os.path.isdir(root):
            continue
        profs = [p for p in glob.glob(os.path.join(root, "*"))
                 if os.path.basename(p) == "Default" or os.path.basename(p).startswith("Profile ")]
        for prof in profs:
            for f in ("History", "History-journal", "Cookies", "Cookies-journal",
                      "Network/Cookies", "Network/Cookies-journal", "Web Data",
                      "Web Data-journal", "Visited Links", "Top Sites", "Top Sites-journal",
                      "Shortcuts", "Shortcuts-journal", "Favicons", "Favicons-journal",
                      "Sessions", "Current Session", "Current Tabs", "Last Session",
                      "Last Tabs", "Local Storage", "Session Storage", "IndexedDB",
                      "Service Worker", "Cache", "Code Cache", "GPUCache",
                      "Network Action Predictor", "Network Action Predictor-journal"):
                _rm(os.path.join(prof, f))
            n_ch += 1
        cache = root.replace("/.config/", "/.cache/")
        _rm(cache)
    _rm(os.path.expanduser("~/.cache/mozilla"))
    if not (n_ff or n_ch):
        return 0, "no browser profiles found"
    return 0, f"cleaned {n_ff} Firefox and {n_ch} Chromium-family profile(s); bookmarks & passwords kept"


def clear_clipboard() -> tuple[int, str]:
    done = []

    def q(cmd):
        # DEVNULL + timeout: xclip forks and keeps a captured pipe open forever
        try:
            subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            pass
    if os.environ.get("WAYLAND_DISPLAY") and shutil.which("wl-copy"):
        q(["wl-copy", "--clear"]); q(["wl-copy", "--primary", "--clear"])
        done.append("wayland")
    if os.environ.get("DISPLAY"):
        if shutil.which("xsel"):
            q(["xsel", "-bc"]); q(["xsel", "-pc"]); done.append("x11")
        elif shutil.which("xclip"):
            for sel in ("clipboard", "primary"):
                q(["xclip", "-selection", sel, "-loops", "1", "-i", "/dev/null"])
            done.append("x11")
    # the GUI additionally clears Qt's clipboard on the main thread
    return 0, "clipboard cleared" + (f" ({', '.join(done)})" if done else "")


def strip_metadata(paths) -> tuple[int, str]:
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
