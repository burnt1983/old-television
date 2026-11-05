#!/bin/bash
# Open the old television. Starts a local page so the live streams can play.
# Resolve symlinks so the dock launcher finds this folder, not ~/bin.
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
cd "$(cd -P "$(dirname "$SOURCE")" && pwd)"
if [ ! -f hls.min.js ]; then
  cat vendor/hls.part-* > hls.min.js
fi
PORT=8765
URL="http://127.0.0.1:${PORT}/"
if ! curl -fsS -o /dev/null --max-time 1 "$URL"; then
  python3 -m http.server "$PORT" --bind 127.0.0.1 >/tmp/old-television.log 2>&1 &
  echo $! >/tmp/old-television.pid
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    curl -fsS -o /dev/null --max-time 1 "$URL" && break
    sleep 0.15
  done
fi
if python3 -c 'import gi; gi.require_version("Gtk","3.0"); gi.require_version("WebKit2","4.1"); from gi.repository import Gtk, WebKit2' >/dev/null 2>&1; then
  python3 "$PWD/window.py" "$URL" >/tmp/old-television-window.log 2>&1 &
else
  google-chrome --app="$URL" --class=lee-old-television --window-size=1280,860 >/dev/null 2>&1 &
fi
