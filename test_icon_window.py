#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf

ICON_PATH = "/usr/share/icons/hicolor/256x256/apps/kitty.png"  # Ändere bei Bedarf

class IconTestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Icon Test")
        self.set_default_size(200, 200)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_border_width(20)

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(ICON_PATH)
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            print("✅ Icon erfolgreich geladen!")
        except Exception as e:
            print(f"❌ Fehler beim Laden des Icons: {e}")
            image = Gtk.Label(label="Fehler beim Laden")

        box.pack_start(image, True, True, 0)
        self.add(box)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

if __name__ == "__main__":
    win = IconTestWindow()
    Gtk.main()
