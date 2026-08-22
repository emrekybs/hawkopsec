#!/usr/bin/env bash
# Build distributable single-file binaries — no source needed to run.
# Output: release/hawkopsec-<ver>-<arch>.tar.gz  (upload to GitHub Releases)
#   contains: hawkopsec (GUI ELF), hawkopsec-helper (root helper ELF),
#             install.sh, polkit policy, .desktop, icons, README.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
VER="$(python3 -c 'import hawkopsec;print(hawkopsec.__version__)' 2>/dev/null || echo 1.0.0)"
ARCH="$(uname -m)"
OUT="$ROOT/release"; DIST="$OUT/hawkopsec-$VER-$ARCH"
rm -rf "$OUT" build; mkdir -p "$DIST"
export PATH="$HOME/.local/bin:$PATH"

echo "[*] Build deps (nuitka[onefile] + patchelf)…"
PIPU=""; [ -z "${VIRTUAL_ENV:-}" ] && PIPU="--user --break-system-packages"
python3 -m pip install $PIPU --upgrade "nuitka[onefile]" patchelf >/dev/null

echo "[*] Compiling GUI → single ELF (bundles Qt + JetBrains Mono + logo/icons)…"
python3 -m nuitka --onefile --assume-yes-for-downloads \
    --enable-plugin=pyqt6 --include-package=hawkopsec \
    --include-data-dir=assets=assets \
    --output-dir=build --output-filename=hawkopsec run.py

echo "[*] Compiling root helper → single ELF…"
cp hawkopsec/hawkopsec-helper build/helper_main.py
python3 -m nuitka --onefile --assume-yes-for-downloads \
    --output-dir=build --output-filename=hawkopsec-helper build/helper_main.py

echo "[*] Assembling release bundle…"
install -m0755 build/hawkopsec        "$DIST/hawkopsec"
install -m0755 build/hawkopsec-helper "$DIST/hawkopsec-helper"
mkdir -p "$DIST/share"
cp -r assets/icons "$DIST/share/icons"
install -m0644 assets/hawkopsec_icon.png             "$DIST/share/hawkopsec_icon.png"
install -m0644 packaging/com.hawkopsec.helper.policy "$DIST/com.hawkopsec.helper.policy"
install -m0644 packaging/hawkopsec.desktop           "$DIST/hawkopsec.desktop"
install -m0755 packaging/install-release.sh          "$DIST/install.sh"
install -m0755 packaging/uninstall.sh                "$DIST/uninstall.sh"
install -m0644 packaging/hawkopsec-uninstall.desktop "$DIST/hawkopsec-uninstall.desktop"
cp README.md "$DIST/README.md"

( cd "$OUT" && tar czf "hawkopsec-$VER-$ARCH.tar.gz" "hawkopsec-$VER-$ARCH" )
echo
echo "[✓] Release archive: $OUT/hawkopsec-$VER-$ARCH.tar.gz"
echo "    Upload it to GitHub Releases. Users then:"
echo "      tar xzf hawkopsec-$VER-$ARCH.tar.gz && cd hawkopsec-$VER-$ARCH"
echo "      sudo ./install.sh          # helper + polkit + menu icon"
echo "      hawkopsec                  # or run ./hawkopsec directly"
