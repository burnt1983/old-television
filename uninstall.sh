#!/usr/bin/env bash
set -euo pipefail
rm -f \
  "${HOME}/.local/bin/old-television" \
  "${HOME}/.local/share/applications/lee-old-television.desktop" \
  "${HOME}/.local/share/icons/hicolor/256x256/apps/lee-old-television.png"
rm -rf "${HOME}/.local/share/old-television"
echo "Removed Old Television. The window position in ~/.config/lee-old-television was left in place."
