#!/usr/bin/env bash
# HawkOpsec — full uninstall.
# 1) reverts every system change, 2) removes ALL installed files (binaries,
# helper, polkit, desktop entry, every menu icon size, state), 3) refreshes the
# icon/desktop caches so nothing lingers in the application menu.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root:  sudo ./uninstall.sh   (or sudo ./packaging/uninstall.sh)" >&2
    exit 1
fi

# 1) revert system changes via whichever helper is installed
for H in /usr/local/lib/hawkopsec/hawkopsec-helper; do
    if [ -x "$H" ]; then
        echo "[*] Reverting all HawkOpsec system changes ..."
        "$H" reset-all || true
    fi
done
# drop the shutdown RAM-wipe unit if it is still around
systemctl disable hawkopsec-ramwipe.service >/dev/null 2>&1 || true
rm -f /etc/systemd/system/hawkopsec-ramwipe.service
systemctl daemon-reload >/dev/null 2>&1 || true

echo "[*] Removing binaries and data"
rm -rf /usr/local/lib/hawkopsec        # source pkg + helper
rm -rf /opt/hawkopsec                  # compiled (install-compiled/-release)
rm -f  /usr/local/bin/hawkopsec        # launcher / symlink
rm -rf /usr/local/share/hawkopsec      # assets + fonts
rm -rf /var/lib/hawkopsec              # state + backups + log

echo "[*] Removing menu integration"
rm -f  /usr/share/applications/hawkopsec.desktop
rm -f  /usr/share/applications/hawkopsec-uninstall.desktop
rm -f  /usr/share/polkit-1/actions/com.hawkopsec.helper.policy
rm -f  /usr/share/pixmaps/hawkopsec.png
# every hicolor size we may have installed
for d in /usr/share/icons/hicolor/*/apps/hawkopsec.png; do
    [ -e "$d" ] && rm -f "$d"
done

echo "[*] Refreshing desktop / icon caches"
command -v gtk-update-icon-cache  >/dev/null 2>&1 && gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database || true
command -v xdg-desktop-menu        >/dev/null 2>&1 && xdg-desktop-menu forceupdate >/dev/null 2>&1 || true

# per-user language config (works under sudo AND pkexec)
U="${SUDO_USER:-}"
[ -z "$U" ] && [ -n "${PKEXEC_UID:-}" ] && U="$(getent passwd "${PKEXEC_UID}" | cut -d: -f1)"
if [ -n "$U" ]; then
    HOMEDIR="$(getent passwd "$U" | cut -d: -f6)"
    [ -n "$HOMEDIR" ] && rm -rf "$HOMEDIR/.config/hawkopsec" 2>/dev/null || true
fi
rm -rf /root/.config/hawkopsec 2>/dev/null || true

echo
echo "[✓] HawkOpsec fully removed. If the menu icon still lingers, log out/in "
echo "    once (some desktops cache the menu until the next session)."
