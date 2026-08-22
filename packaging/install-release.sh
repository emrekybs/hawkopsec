#!/usr/bin/env bash
# Install HawkOpsec from the compiled release bundle. No Python / no source.
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Run as root:  sudo ./install.sh" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"

echo "[*] Installing binaries"
install -Dm0755 "$HERE/hawkopsec" /usr/local/bin/hawkopsec
install -o root -g root -Dm0755 "$HERE/hawkopsec-helper" \
        /usr/local/lib/hawkopsec/hawkopsec-helper

echo "[*] Installing polkit policy + desktop entry"
install -Dm0644 "$HERE/com.hawkopsec.helper.policy" \
        /usr/share/polkit-1/actions/com.hawkopsec.helper.policy
install -Dm0644 "$HERE/hawkopsec.desktop" \
        /usr/share/applications/hawkopsec.desktop
install -o root -g root -Dm0755 "$HERE/uninstall.sh" /usr/local/lib/hawkopsec/uninstall
install -Dm0644 "$HERE/hawkopsec-uninstall.desktop" \
        /usr/share/applications/hawkopsec-uninstall.desktop

echo "[*] Installing menu icons"
mkdir -p /usr/local/share/hawkopsec
install -Dm0644 "$HERE/share/hawkopsec_icon.png" /usr/local/share/hawkopsec/hawkopsec_icon.png
for d in "$HERE/share/icons/"*x*/; do
    sz="$(basename "$d")"
    install -Dm0644 "$d/hawkopsec.png" "/usr/share/icons/hicolor/$sz/apps/hawkopsec.png"
done
install -Dm0644 "$HERE/share/icons/256x256/hawkopsec.png" /usr/share/pixmaps/hawkopsec.png
command -v gtk-update-icon-cache  >/dev/null 2>&1 && gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database || true

echo
echo "[✓] Installed. Launch 'HawkOpsec' from the menu or run: hawkopsec"
echo
echo "Runtime tools it USES (installs nothing itself — install what you want to use):"
echo "  sudo pacman -S --needed tor nftables polkit iproute2 rfkill systemd-resolvconf"
echo "  optional: mat2 firejail torbrowser-launcher secure-delete"
