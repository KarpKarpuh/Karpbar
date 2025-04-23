#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkX11, GLib

class Karpbar(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self)

        # Fenster-Grundkonfiguration
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.stick()
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        monitor = screen.get_primary_monitor()
        geometry = screen.get_monitor_geometry(monitor)
        self.set_size_request(geometry.width, 35)
        self.move(0, geometry.height - 35)

        # Layout (horizontal)
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.box.set_margin_top(2)
        self.box.set_margin_bottom(2)
        self.box.set_margin_start(10)
        self.box.set_margin_end(10)

        # Beispiel-Button
        btn = Gtk.Button(label="🐣 Hello Karpbar")
        self.box.pack_start(btn, False, False, 0)

        self.add(self.box)
        self.show_all()

        # Rechtsklick-Menü
        self.connect("button-press-event", self.on_right_click)

    def on_right_click(self, widget, event):
        if event.button == 3:  # Rechte Maustaste
            menu = Gtk.Menu()

            close_item = Gtk.MenuItem(label="Karpbar schließen")
            close_item.connect("activate", lambda _: Gtk.main_quit())
            menu.append(close_item)

            menu.show_all()
            menu.popup_at_pointer(event)

def main():
    win = Karpbar()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == "__main__":
    main()
