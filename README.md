<p align="center">
  <img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/hawkopsec/assets/hawkopsec_mark.png" alt="HawkOpsec" width="380">
</p>

<h1 align="center">HawkOpsec</h1>

<p align="center">
  <b>One-tap Linux OPSEC hardening & anonymity toolkit</b><br>
</p>

<p align="center">
  <img alt="pypi" src="https://img.shields.io/pypi/v/hawkopsec?color=0b0d10">
  <img alt="platform" src="https://img.shields.io/badge/platform-Linux%20(Arch%20%7C%20Debian)-0b0d10">
  <img alt="ui" src="https://img.shields.io/badge/UI-PyQt6-16C784">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

---

HawkOpsec turns a pile of manual privacy commands into **security profiles you apply with one tap**.
Pick a profile — the tool starts Tor, configures DNS, randomizes your identity and hardens the
kernel for you. **Reset system** rolls every change back from snapshots to your original state.

The GUI never runs as root; privileged actions go through a small helper via **polkit/pkexec**.

<p align="center"><img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/docs/dashboard.png" alt="Overview" width="850"></p>

## Architecture

<p align="center"><img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/docs/arch.png" alt="Architecture" width="850"></p>

## Install

**1. System dependencies**

```bash
# Arch
sudo pacman -S --needed tor nftables polkit iproute2 rfkill systemd-resolvconf
# Debian / Ubuntu / Kali / Mint
sudo apt install -y tor nftables policykit-1 iproute2 rfkill systemd-resolved
# optional: torbrowser-launcher firefox mat2 xsel (or wl-clipboard) firejail
```

**2. HawkOpsec from PyPI**

```bash
pipx install hawkopsec          # recommended (isolated)
# or: pip install --user hawkopsec
sudo "$(command -v hawkopsec-setup)"   # one-time: root helper, polkit policy, menu entry
hawkopsec
```

If you skip `hawkopsec-setup`, the app offers to run it on first start (it asks for
your password once). The root helper is copied to `/usr/local/lib/hawkopsec/` and owned by root —
HawkOpsec never runs a user-writable file as root.

**From source** (unchanged): `python3 run.py`, or `sudo ./packaging/install.sh`.

## Uninstall

```bash
sudo "$(command -v hawkopsec-setup)" --remove   # reverts every change + removes system files
pipx uninstall hawkopsec                        # or: pip uninstall hawkopsec
```

The **Uninstall** button in the app does the same system cleanup.

## What's new in 2.0

**Fixes**
- *IP check* — the console swallowed the real error (`<urlopen error …>` was parsed as HTML), so
  failures showed only `URLError:`. Errors are now escaped and explained. The check waits for the
  network after a profile switch, retries, falls back across four endpoints and verifies Tor via the
  official exit list when `check.torproject.org` is unreachable.
- *Baseline* no longer restarts NetworkManager unless MAC/NetworkManager settings were changed —
  this was dropping the link right before the IP check.
- *Tor DNS* — queries to `127.0.0.1:53` skipped the redirect rule, so DNS died in Tor mode on
  systems without systemd-resolved. Fixed rule order.
- *Tor start* waits for `Bootstrapped 100%`, not just an open port.
- *Tor Browser* uses the system Tor (SOCKS 9050) when Tor routing is on — no more Tor-over-Tor.

**Leak test (new tab)** — read-only, one click
- Exit IP (Tor confirmed / real IP visible), DNS leak (bash.ws, matched against your real ISP),
  IPv6 leak, UDP kill-switch test, `.onion` mapping, Tor service health.
- Your real ISP is remembered in BASELINE as a name + salted hash — never the raw IP.

**Dark-web pre-flight** — Tor Browser installed + Security Level, WebRTC, Firefox wipe-on-close,
browser history on disk, timezone, clock sync, hostname, MAC, firewall, open ports,
identity-linked apps (Discord, Telegram, Dropbox …), webcam, disk encryption, swap, non-root
session, VPN. Verdict: *Ready / Risky / Not ready*, with a **Fix** button where possible.

**Leave no browser traces**
- **RAM-only browser** — Firefox with a throw-away profile in `/dev/shm`; history, cookies, cache
  and sessions never touch the disk, the profile is deleted on close.
- **Clean browser traces** — history, cookies, cache, sessions, site storage and form data of
  Firefox and Chromium-family browsers; bookmarks and saved passwords are kept.
- **Firefox: wipe on close** — your normal Firefox clears everything on exit, no disk cache.
- **Clear clipboard** (also done by **Panic**), DNS cache flush in *Clean system traces*.
- Panic now also kills Tor Browser, LibreWolf, Brave and Vivaldi.

**Hardening** — *Disable webcam* (UVC driver unloaded and blocked); part of GHOST / PARANOID.

**UI** — IBM Plex Sans for text, JetBrains Mono only for machine data; sentence-case labels,
profile cards, console with clear button, Turkish terminology throughout. Window fits 1000×700.

**Packaging** — published on PyPI (`pip install hawkopsec`); assets moved into the package
(`hawkopsec/assets`, `hawkopsec/data`); new `hawkopsec-setup` command; `python -m hawkopsec` works.

## Publishing to PyPI (maintainers)

The package is defined in `pyproject.toml` (setuptools). The version comes from
`hawkopsec/__init__.py`.

```bash
python -m pip install --upgrade build twine
rm -rf dist && python -m build          # -> dist/hawkopsec-X.Y.Z.tar.gz + .whl
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*   # optional dry run
python -m twine upload dist/*                          # needs a PyPI API token
```

One-time setup: create an account on pypi.org, enable 2FA, create an API token and put it in
`~/.pypirc` — or use *Trusted Publishing*: `.github/workflows/pypi.yml` publishes automatically on every `v*` tag once you add the GitHub publisher on pypi.org. For each release bump
`__version__`, tag `vX.Y.Z` and upload — PyPI never accepts the same version twice.

## Security note

HawkOpsec hardens the **network and system layers**. It does **not** make a normal browser
fingerprint-resistant — for real anonymous browsing use **Tor Browser** at the *Safest* level,
never log into personal accounts while anonymous, and remember that behavioural patterns are out
of scope for a system tool. You are hardening *your own* machine.

## License

MIT — see [LICENSE](LICENSE).
