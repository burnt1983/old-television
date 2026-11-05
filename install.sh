#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SHARE="${HOME}/.local/share/old-television"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$SHARE" "$BIN" "$APPS" "$ICON_DIR"
install -m 0644 "$ROOT/index.html" "$ROOT/hls.min.js" "$ROOT/desklet_geometry.py" "$SHARE/"
install -m 0755 "$ROOT/open.sh" "$ROOT/window.py" "$SHARE/"
base64 -d "$ROOT/icon.b64" > "$ICON_DIR/lee-old-television.png"
ln -sfn "$SHARE/open.sh" "$BIN/old-television"

sed "s|^Exec=old-television$|Exec=${BIN}/old-television|" \
    "$ROOT/data/old-television.desktop" > "$APPS/lee-old-television.desktop"
chmod 0644 "$APPS/lee-old-television.desktop"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f "${HOME}/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPS" >/dev/null 2>&1 || true
fi

echo "Installed Old Television."
echo "  Run: old-television"
echo "  It does not start at login."
