#!/usr/bin/env bash
# HawkOpsec — install the Nuitka-compiled binary (run build.sh first).
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root:  sudo ./packaging/install-compiled.sh" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/build/run.dist"

if [ ! -x "$DIST/hawkopsec" ]; then
    echo "Compiled binary not found. Run ./packaging/build.sh first." >&2
    exit 1
fi

echo "[*] Installing compiled app -> /opt/hawkopsec"
rm -rf /opt/hawkopsec
cp -r "$DIST" /opt/hawkopsec
ln -sf /opt/hawkopsec/hawkopsec /usr/local/bin/hawkopsec

echo "[*] Installing root helper"
mkdir -p /usr/local/lib/hawkopsec
install -o root -g root -m 0755 "$ROOT/hawkopsec/hawkopsec-helper" \
        /usr/local/lib/hawkopsec/hawkopsec-helper

echo "[*] Installing assets, fonts, menu icons, policy, desktop entry"
mkdir -p /usr/local/share/hawkopsec /usr/local/share/hawkopsec/fonts
install -m 0644 "$ROOT/assets/hawkopsec.png"      /usr/local/share/hawkopsec/hawkopsec.png
install -m 0644 "$ROOT/assets/hawkopsec_mark.png" /usr/local/share/hawkopsec/hawkopsec_mark.png
install -m 0644 "$ROOT/assets/hawkopsec_icon.png" /usr/local/share/hawkopsec/hawkopsec_icon.png
cp "$ROOT/assets/fonts/"*.ttf /usr/local/share/hawkopsec/fonts/ 2>/dev/null || true
for d in "$ROOT/assets/icons/"*x*/; do
    sz="$(basename "$d")"
    install -Dm 0644 "$d/hawkopsec.png" "/usr/share/icons/hicolor/$sz/apps/hawkopsec.png"
done
install -Dm 0644 "$ROOT/assets/icons/256x256/hawkopsec.png" /usr/share/pixmaps/hawkopsec.png
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
install -m 0644 "$ROOT/packaging/com.hawkopsec.helper.policy" \
        /usr/share/polkit-1/actions/com.hawkopsec.helper.policy
install -m 0644 "$ROOT/packaging/hawkopsec.desktop" \
        /usr/share/applications/hawkopsec.desktop
install -o root -g root -m 0755 "$ROOT/packaging/uninstall.sh" /usr/local/lib/hawkopsec/uninstall
install -m 0644 "$ROOT/packaging/hawkopsec-uninstall.desktop" \
        /usr/share/applications/hawkopsec-uninstall.desktop

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database || true
echo "[✓] Installed. Launch from the menu or run: hawkopsec"

echo "Uninstall anytime:  sudo ./packaging/uninstall.sh"
