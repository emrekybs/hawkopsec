#!/usr/bin/env bash
# HawkOpsec — compile the GUI into a standalone binary with Nuitka.
# The root helper stays a plain script (invoked via pkexec by path) and is
# installed separately by install-compiled.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[*] Ensuring Nuitka is available"
PIPU=""; [ -z "${VIRTUAL_ENV:-}" ] && PIPU="--user --break-system-packages"
python3 -m pip install $PIPU --upgrade nuitka patchelf >/dev/null

echo "[*] Compiling (this takes a few minutes) ..."
python3 -m nuitka \
    --standalone \
    --assume-yes-for-downloads \
    --enable-plugin=pyqt6 \
    --include-package=hawkopsec \
    --include-data-dir=assets=assets \
    --output-dir=build \
    --output-filename=hawkopsec \
    run.py

echo
echo "[✓] Binary: build/run.dist/hawkopsec"
echo "    Install it system-wide with:  sudo ./packaging/install-compiled.sh"
