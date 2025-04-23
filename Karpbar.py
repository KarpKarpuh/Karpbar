#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import subprocess
import os
from taskbar_data import generate_taskbar_data

ICON_SIZE = 24
BAR_HEIGHT = 35

class Karpbar(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Karpbar")
        self.set_decorated(False)
        self.set_skip_taskbar_hint(True)
        self.set_keep_above(True)
        self.stick()
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)

        screen = self.get_screen()
        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)

        self.set_size_request(geometry.width, BAR_HEIGHT)
        self.move(geometry.x, geometry.y + geometry.height - (BAR_HEIGHT*1.325))

        # Rechteckiger Stil (kein Schatten, keine Rundung)
        rgba = Gdk.RGBA()
        rgba.parse("#2b303b")  # dunkelgrau
        self.override_background_color(Gtk.StateFlags.NORMAL, rgba)

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.box.set_margin_start(10)
        self.box.set_margin_end(10)
        self.add(self.box)

        self.load_buttons()
        GLib.timeout_add(1000, self.refresh)

        quit_btn = Gtk.Button(label="⏻")
        quit_btn.set_relief(Gtk.ReliefStyle.NONE)
        quit_btn.connect("clicked", Gtk.main_quit)
        self.box.pack_end(quit_btn, False, False, 5)

        self.show_all()

    def load_buttons(self):
        self.buttons = []
        apps = generate_taskbar_data()

        for app in apps:
            btn = Gtk.Button()
            btn.set_tooltip_text(app.get("tooltip", app["name"]))
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.set_size_request(30, 30)

            content = self.create_icon_or_label(app)
            btn.add(content)

            btn.connect("clicked", self.on_app_click, app)
            self.box.pack_start(btn, False, False, 0)
            self.buttons.append(btn)

    def create_icon_or_label(self, app):
        if app["icon"] and os.path.exists(app["icon"]):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename=app["icon"],
                    width=ICON_SIZE,
                    height=ICON_SIZE,
                    preserve_aspect_ratio=True
                )
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                return image
            except Exception as e:
                print(f"⚠️ Fehler beim Laden von {app['icon']}: {e}")
        fallback = app["name"][:2].upper()
        label = Gtk.Label(label=fallback)
        label.set_margin_top(6)
        label.set_margin_bottom(6)
        return label

    def on_app_click(self, button, app):
        print(f"🔘 Klick auf {app['name']}")
        subprocess.Popen(["python3", "focus_or_launch.py", app["exec"]])

    def refresh(self):
        for btn in self.buttons:
            self.box.remove(btn)
        self.load_buttons()
        self.show_all()
        return True

if __name__ == "__main__":
    Karpbar()
    Gtk.main()
