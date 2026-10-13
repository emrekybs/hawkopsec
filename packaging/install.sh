#!/usr/bin/env bash
# HawkOpsec — source install (uses system python3-pyqt6).
# Run from the project root:  sudo ./packaging/install.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root:  sudo ./packaging/install.sh" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIBDIR=/usr/local/lib/hawkopsec
SHAREDIR=/usr/local/share/hawkopsec

echo "[*] Installing package -> $LIBDIR"
rm -rf "$LIBDIR/hawkopsec"
mkdir -p "$LIBDIR"
cp -r "$ROOT/hawkopsec" "$LIBDIR/hawkopsec"

echo "[*] Installing root helper"
install -o root -g root -m 0755 "$ROOT/hawkopsec/hawkopsec-helper" \
        "$LIBDIR/hawkopsec-helper"

echo "[*] Installing assets, fonts and menu icons"
mkdir -p "$SHAREDIR" "$SHAREDIR/fonts"
install -m 0644 "$ROOT/hawkopsec/assets/hawkopsec.png"      "$SHAREDIR/hawkopsec.png"
install -m 0644 "$ROOT/hawkopsec/assets/hawkopsec_mark.png" "$SHAREDIR/hawkopsec_mark.png"
install -m 0644 "$ROOT/hawkopsec/assets/hawkopsec_icon.png" "$SHAREDIR/hawkopsec_icon.png"
cp "$ROOT/hawkopsec/assets/fonts/"*.ttf "$SHAREDIR/fonts/" 2>/dev/null || true
for d in "$ROOT/hawkopsec/assets/icons/"*x*/; do
    sz="$(basename "$d")"
    install -Dm 0644 "$d/hawkopsec.png" "/usr/share/icons/hicolor/$sz/apps/hawkopsec.png"
done
install -Dm 0644 "$ROOT/hawkopsec/assets/icons/256x256/hawkopsec.png" /usr/share/pixmaps/hawkopsec.png
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true

echo "[*] Installing polkit policy"
install -m 0644 "$ROOT/hawkopsec/data/com.hawkopsec.helper.policy" \
        /usr/share/polkit-1/actions/com.hawkopsec.helper.policy

echo "[*] Installing desktop entry"
install -m 0644 "$ROOT/hawkopsec/data/hawkopsec.desktop" \
        /usr/share/applications/hawkopsec.desktop

echo "[*] Installing uninstaller (menu entry)"
install -o root -g root -m 0755 "$ROOT/hawkopsec/data/uninstall.sh" "$LIBDIR/uninstall"
install -m 0644 "$ROOT/hawkopsec/data/hawkopsec-uninstall.desktop" \
        /usr/share/applications/hawkopsec-uninstall.desktop

echo "[*] Creating launcher /usr/local/bin/hawkopsec"
cat > /usr/local/bin/hawkopsec <<'EOF'
#!/bin/sh
export PYTHONPATH=/usr/local/lib/hawkopsec${PYTHONPATH:+:$PYTHONPATH}
exec python3 -m hawkopsec.main "$@"
EOF
chmod 0755 /usr/local/bin/hawkopsec

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database || true

echo
echo "[✓] Installed. Launch from the menu (HawkOpsec) or run: hawkopsec"
echo
echo "Runtime dependencies (install what you're missing):"
echo "  Arch  : sudo pacman -S --needed python-pyqt6 tor nftables polkit iproute2 rfkill systemd-resolvconf"
echo "  Debian: sudo apt install python3-pyqt6 tor nftables policykit-1 systemd-resolved iproute2 rfkill"
echo
echo "Uninstall:  sudo /usr/local/lib/hawkopsec/uninstall"
