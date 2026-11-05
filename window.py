#!/usr/bin/env python3
"""Borderless television. Drag the cabinet anywhere on the desktop."""
import json
import os
import sys

sys.path[:0] = [
    os.path.dirname(os.path.abspath(__file__)),
    os.path.expanduser("~/.local/lib"),
]
from desklet_geometry import prefer_xwayland

prefer_xwayland()

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gdk, GLib, Gtk, WebKit2

GLib.set_prgname("lee-old-television")

PLACE = os.path.expanduser("~/.config/lee-old-television/place.json")
FRAME_ANCHOR = 16
EDGE_TUCK = 24
ICON = os.path.expanduser("~/.local/share/icons/hicolor/256x256/apps/lee-old-television.png")


def free_insets(width, height, strut_left=0, strut_top=0):
    """Keep a small anchor in the work area so the set can cross the panels."""
    width = max(int(width), 2)
    height = max(int(height), 2)
    frame_w = max(1, min(FRAME_ANCHOR, width - 1))
    frame_h = max(1, min(FRAME_ANCHOR, height - 1))
    budget_w = width - frame_w
    budget_h = height - frame_h
    left = min(max(0, int(strut_left)) + EDGE_TUCK, budget_w)
    top = min(max(0, int(strut_top)) + EDGE_TUCK, budget_h)
    return int(left), int(budget_w - left), int(top), int(budget_h - top)


def load_place():
    try:
        with open(PLACE, encoding="utf-8") as handle:
            data = json.load(handle)
        return int(data["x"]), int(data["y"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def save_place(x, y):
    try:
        os.makedirs(os.path.dirname(PLACE), exist_ok=True)
        with open(PLACE, "w", encoding="utf-8") as handle:
            json.dump({"x": int(x), "y": int(y)}, handle)
    except OSError as err:
        print("place", err, file=sys.stderr)


def with_host(url):
    if "host=1" in url:
        return url
    return url + ("&" if "?" in url else "?") + "host=1"


class Host(Gtk.Window):
    def __init__(self, url, check=False):
        super().__init__(title="Old Television")
        self.check = check
        self._drag = None
        self._placed = False
        self._user_moved = False
        self._shadow_for = None
        self._wanted = (780, 680)
        self._fixing = False
        self._saved = load_place()
        self._js_screen = None
        self._retries = 0
        self._check_done = False
        try:
            self.set_icon_from_file(ICON)
        except Exception:
            pass
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_accept_focus(True)
        self.set_default_size(780, 680)
        self.set_opacity(0)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)
        css = Gtk.CssProvider()
        css.load_from_data(b"window { background-color: transparent; }")
        Gtk.StyleContext.add_provider_for_screen(
            screen, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.connect("draw", self.clear)
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)
        self.connect("configure-event", self.on_configure)

        view = WebKit2.WebView()
        rgba = Gdk.RGBA()
        rgba.parse("rgba(0,0,0,0)")
        view.set_background_color(rgba)
        settings = view.get_settings()
        settings.set_enable_javascript(True)
        settings.set_media_playback_requires_user_gesture(False)
        for name, value in (
            ("enable-mediasource", True),
            ("enable-media", True),
            ("enable-webgl", True),
        ):
            try:
                settings.set_property(name, value)
            except Exception as err:
                print("setting", name, err, file=sys.stderr)
        manager = view.get_user_content_manager()
        manager.register_script_message_handler("host")
        manager.connect("script-message-received::host", self.on_host)
        view.connect("key-press-event", self.on_key)
        view.load_uri(with_host(url))
        self.add(view)
        self.realize()
        self._sync_shadow()
        self.show_all()
        GLib.timeout_add(2500, self._reveal)
        if check:
            GLib.timeout_add(8000, self._check_gave_up)

    def clear(self, _widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(1)  # SOURCE, so the frame is actually clear
        cr.paint()
        cr.set_operator(2)  # OVER
        return False

    def on_key(self, _widget, event):
        if event.keyval == Gdk.KEY_q and event.state & Gdk.ModifierType.CONTROL_MASK:
            Gtk.main_quit()
        return False

    def on_configure(self, *_args):
        # Shadow insets make get_size report the frame only. Put the set back.
        if self._fixing or self._wanted is None:
            return False
        width, height = self._wanted
        current_w, current_h = self.get_size()
        if int(current_w) != int(width) or int(current_h) != int(height):
            self._fixing = True
            self.resize(int(width), int(height))
            self._fixing = False
        return False

    def _monitor(self):
        display = self.get_display() or Gdk.Display.get_default()
        if display is None or display.get_n_monitors() < 1:
            return None
        gdk_window = self.get_window()
        monitor = display.get_monitor_at_window(gdk_window) if gdk_window is not None else None
        if monitor is None:
            monitor = display.get_primary_monitor() or display.get_monitor(0)
        return monitor

    def _struts(self):
        try:
            monitor = self._monitor()
            if monitor is None:
                return 0, 0
            geo = monitor.get_geometry()
            work = monitor.get_workarea()
            return max(0, int(work.x - geo.x)), max(0, int(work.y - geo.y))
        except Exception:
            return 0, 0

    def _sync_shadow(self):
        gdk_window = self.get_window()
        if gdk_window is None or self._wanted is None:
            return
        width, height = self._wanted
        if self._shadow_for == (width, height):
            return
        insets = free_insets(width, height, *self._struts())
        self._shadow_for = (width, height)
        self._insets = insets
        try:
            gdk_window.set_shadow_width(*insets)
        except Exception as err:
            print("shadow", err, file=sys.stderr)
            return
        self._fixing = True
        self.resize(int(width), int(height))
        self._fixing = False

    def _reveal(self):
        if self.get_opacity() < 1:
            self._place_once()
        return False

    def _place_once(self):
        if self._placed:
            self.set_opacity(1)
            return
        self._placed = True
        if self._saved is not None:
            self.move(int(self._saved[0]), int(self._saved[1]))
            self._retries = 0
            GLib.timeout_add(200, self._retry_place)
        else:
            self._center()
        self.set_opacity(1)

    def _retry_place(self):
        if self._user_moved or self._saved is None:
            return False
        self._retries += 1
        x, y = self.get_position()
        if abs(int(x) - self._saved[0]) > 12 or abs(int(y) - self._saved[1]) > 12:
            self.move(int(self._saved[0]), int(self._saved[1]))
        return self._retries < 8

    def _center(self):
        monitor = self._monitor()
        if monitor is None:
            return
        geo = monitor.get_geometry()
        width, height = self.get_size()
        self.move(
            int(geo.x + (geo.width - int(width)) / 2),
            int(geo.y + (geo.height - int(height)) / 2),
        )

    def _monitor_size(self):
        monitor = self._monitor()
        if monitor is None:
            return 0, 0
        geo = monitor.get_geometry()
        return int(geo.width), int(geo.height)

    def _to_gdk(self, dx, dy):
        sw, sh = self._js_screen or (0, 0)
        mw, mh = self._monitor_size()
        if sw > 1 and sh > 1 and mw > 1 and mh > 1:
            return dx * mw / sw, dy * mh / sh
        return dx, dy

    def apply_size(self, width, height):
        width = int(max(220, min(1600, round(float(width)))))
        height = int(max(180, min(1400, round(float(height)))))
        if self._wanted != (width, height):
            self._wanted = (width, height)
            self._shadow_for = None
            self._sync_shadow()
            GLib.idle_add(self._after_size, width, height)
        elif not self._placed:
            self._place_once()
        if self.check and not self._check_done:
            self._check_done = True
            print("size", width, height, "insets", getattr(self, "_insets", None), flush=True)
            GLib.timeout_add(400, self._run_check)

    def _after_size(self, width, height):
        self._sync_shadow()
        current_w, current_h = self.get_size()
        if int(current_w) != int(width) or int(current_h) != int(height):
            self.resize(int(width), int(height))
        if not self._placed:
            self._place_once()
        return False

    def handle(self, msg):
        op = msg.get("op")
        if op == "error":
            print("page", msg.get("msg"), flush=True)
            return
        if op == "hello":
            try:
                self._js_screen = (float(msg.get("sw") or 0), float(msg.get("sh") or 0))
            except (TypeError, ValueError):
                self._js_screen = None
            print(
                "hello",
                self._js_screen,
                "monitor",
                self._monitor_size(),
                "scale",
                self.get_scale_factor(),
                flush=True,
            )
            return
        if op == "size":
            self.apply_size(msg.get("w") or 0, msg.get("h") or 0)
            return
        if op == "down":
            wx, wy = self.get_position()
            self._drag = (float(msg["x"]), float(msg["y"]), int(wx), int(wy))
            self._user_moved = True
            return
        if op == "move" and self._drag is not None:
            x0, y0, wx, wy = self._drag
            dx, dy = self._to_gdk(float(msg["x"]) - x0, float(msg["y"]) - y0)
            self.move(int(round(wx + dx)), int(round(wy + dy)))
            return
        if op == "up":
            self._drag = None
            x, y = self.get_position()
            save_place(x, y)
            return

    def on_host(self, _manager, value):
        text = ""
        try:
            if hasattr(value, "is_string") and value.is_string():
                text = value.to_string()
            elif hasattr(value, "get_js_value"):
                js = value.get_js_value()
                text = js.to_string() if js is not None else ""
            elif hasattr(value, "to_string"):
                text = value.to_string()
            else:
                text = str(value)
        except Exception as err:
            print("message", err, file=sys.stderr)
            return
        try:
            msg = json.loads(text)
        except (ValueError, TypeError):
            print("bad message", text, file=sys.stderr)
            return
        if not isinstance(msg, dict):
            return
        self.handle(msg)

    def _jump(self, x, y):
        wx, wy = self.get_position()
        self.handle({"op": "down", "x": 0, "y": 0})
        self.handle({"op": "move", "x": int(x) - int(wx), "y": int(y) - int(wy)})

    def _run_check(self):
        mon_w, mon_h = self._monitor_size()
        width, height = self._wanted
        self._spots = [
            ("nudge", None),
            ("origin", (8, 8)),
            ("past-corner", (-36, -28)),
            ("top-bar", (80, 0)),
            ("bottom-right", (mon_w - 70, mon_h - 70)),
            ("fitted-corner", (mon_w - int(width), mon_h - int(height))),
        ]
        self._seen = [("start", tuple(int(v) for v in self.get_position()))]
        before = self._seen[0][1]
        self.handle({"op": "down", "x": 0, "y": 0})
        self.handle({"op": "move", "x": 240, "y": 130})
        GLib.timeout_add(160, self._check_step, before)
        return False

    def _check_step(self, before):
        if self._spots and self._spots[0][0] == "nudge":
            self._spots.pop(0)
            now = tuple(int(v) for v in self.get_position())
            self._seen.append(("nudge", now, (before[0] + 240, before[1] + 130)))
        if not self._spots:
            self._finish_check()
            return False
        name, xy = self._spots.pop(0)
        self._jump(*xy)
        GLib.timeout_add(160, self._check_landed, name, xy)
        return False

    def _check_landed(self, name, xy):
        self._seen.append((name, tuple(int(v) for v in self.get_position()), xy))
        GLib.timeout_add(40, self._check_step, None)
        return False

    def _finish_check(self):
        print("CHECK", json.dumps({"seen": self._seen, "wanted": list(self._wanted), "insets": list(getattr(self, "_insets", []))}), flush=True)
        # Leave the saved place where the user had it. This check dragged.
        if self._saved is not None:
            save_place(*self._saved)
        elif os.path.exists(PLACE):
            try:
                os.remove(PLACE)
            except OSError:
                pass
        Gtk.main_quit()
        return False

    def _check_gave_up(self):
        if self._check_done:
            return False
        print("CHECK timeout", flush=True)
        Gtk.main_quit()
        return False


if __name__ == "__main__":
    check = "--check" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--check"]
    Host(args[0] if args else "http://127.0.0.1:8765/", check=check)
    Gtk.main()
