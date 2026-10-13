#!/usr/bin/env python3
"""
HawkOpsec — system integration for pip installs.

`pip install hawkopsec` only puts Python files in site-packages. The root
helper must NOT be run from there: a user-writable file executed as root is a
privilege-escalation hole. This command copies the helper to a root-owned
location and installs the polkit policy, menu entry, icons and uninstaller.

    sudo hawkopsec-setup              # install / update system integration
    sudo hawkopsec-setup --remove     # revert all changes + remove integration

The GUI also offers to run it on first start (via pkexec). This file has no
package-relative imports on purpose so it can be executed directly by path
under pkexec, where the user's site-packages are not on sys.path.
"""
import argparse
import os
import shutil
import subprocess
import sys

PKG = os.path.dirname(os.path.abspath(__file__))
LIBDIR = "/usr/local/lib/hawkopsec"
SHAREDIR = "/usr/local/share/hawkopsec"
HELPER = os.path.join(LIBDIR, "hawkopsec-helper")
POLICY = "/usr/share/polkit-1/actions/com.hawkopsec.helper.policy"
DESKTOP = "/usr/share/applications/hawkopsec.desktop"
UN_DESKTOP = "/usr/share/applications/hawkopsec-uninstall.desktop"


def _install(src, dst, mode):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    os.chown(dst, 0, 0)
    os.chmod(dst, mode)


def _quiet(cmd):
    if shutil.which(cmd[0]):
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def install(pkg, exec_path):
    a, d = os.path.join(pkg, "assets"), os.path.join(pkg, "data")
    print(f"[*] root helper -> {HELPER}")
    _install(os.path.join(pkg, "hawkopsec-helper"), HELPER, 0o755)
    _install(os.path.join(d, "uninstall.sh"), os.path.join(LIBDIR, "uninstall"), 0o755)

    print(f"[*] assets + fonts -> {SHAREDIR}")
    for f in ("hawkopsec.png", "hawkopsec_mark.png", "hawkopsec_icon.png"):
        _install(os.path.join(a, f), os.path.join(SHAREDIR, f), 0o644)
    for f in os.listdir(os.path.join(a, "fonts")):
        if f.endswith(".ttf"):
            _install(os.path.join(a, "fonts", f), os.path.join(SHAREDIR, "fonts", f), 0o644)

    print("[*] menu icons")
    for sz in os.listdir(os.path.join(a, "icons")):
        _install(os.path.join(a, "icons", sz, "hawkopsec.png"),
                 f"/usr/share/icons/hicolor/{sz}/apps/hawkopsec.png", 0o644)
    _install(os.path.join(a, "icons", "256x256", "hawkopsec.png"),
             "/usr/share/pixmaps/hawkopsec.png", 0o644)

    print("[*] polkit policy + desktop entries")
    _install(os.path.join(d, "com.hawkopsec.helper.policy"), POLICY, 0o644)
    desk = open(os.path.join(d, "hawkopsec.desktop")).read()
    if exec_path:   # pip --user / venv: the launcher may not be on the menu's PATH
        desk = desk.replace("Exec=hawkopsec", f"Exec={exec_path}")
    os.makedirs(os.path.dirname(DESKTOP), exist_ok=True)
    with open(DESKTOP, "w") as f:
        f.write(desk)
    os.chmod(DESKTOP, 0o644)
    _install(os.path.join(d, "hawkopsec-uninstall.desktop"), UN_DESKTOP, 0o644)

    _quiet(["gtk-update-icon-cache", "-f", "/usr/share/icons/hicolor"])
    _quiet(["update-desktop-database"])
    print("[✓] System integration installed. Start HawkOpsec from the menu or run: hawkopsec")


def remove():
    if os.path.exists(HELPER):
        print("[*] reverting every HawkOpsec system change ...")
        subprocess.run([HELPER, "reset-all"])
    script = os.path.join(LIBDIR, "uninstall")
    if not os.path.exists(script):
        script = os.path.join(PKG, "data", "uninstall.sh")
    subprocess.run(["bash", script])
    print("[i] Python package itself: pip uninstall hawkopsec")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="hawkopsec-setup",
                                 description="Install HawkOpsec's root helper, polkit policy and menu entry.")
    ap.add_argument("--remove", action="store_true", help="revert changes and remove system integration")
    ap.add_argument("--exec", dest="exec_path", default=None,
                    help="absolute path of the hawkopsec launcher for the menu entry")
    ap.add_argument("--src", default=PKG, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if os.geteuid() != 0:
        me = shutil.which("hawkopsec-setup") or sys.argv[0]
        print(f"Run as root:  sudo {me}" + (" --remove" if args.remove else ""), file=sys.stderr)
        return 1
    if args.remove:
        remove(); return 0
    exec_path = args.exec_path
    if not exec_path:   # sudo keeps argv[0]; the GUI launcher sits next to us
        cand = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "hawkopsec")
        exec_path = cand if os.path.exists(cand) and not cand.startswith("/usr/bin") else None
    install(os.path.abspath(args.src), exec_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
