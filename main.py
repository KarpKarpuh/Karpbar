#!/usr/bin/env python3
import gi
import os
import sys
try:
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gtk4LayerShell", "1.0")
except ValueError as e:
    print("GTK4 oder GtkLayerShell nicht verfügbar. Bitte sicherstellen, dass Gtk 4 und gtk4-layer-shell installiert sind.", file=sys.stderr)
    sys.exit(1)
from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell as GtkLayerShell
# Lokale Modul-Imports
from config_loader import load_config
from widgets.taskbar import Taskbar

def main():
    # Konfigurationsdatei laden
    config = load_config()
    # GTK Application initialisieren
    app = Gtk.Application(application_id="de.example.karpbar")
    # Callback zur App-Aktivierung definieren
    def on_activate(app):
        # Hauptfenster erzeugen (Layer-Shell Panel-Fenster)
        window = Gtk.ApplicationWindow(application=app)
        window.set_title("Karpbar")
        window.set_decorated(False)  # Kein eigenes Fensterdekor, da Panel
        # GtkLayerShell-Einstellungen für Panel: am unteren Bildschirmrand, ganze Breite, oberste Ebene
        GtkLayerShell.init_for_window(window)
        GtkLayerShell.set_layer(window, GtkLayerShell.Layer.TOP)  # oberste Layer, über normalen Fenstern
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.BOTTOM, True)  # unten verankern
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.LEFT, True)    # links verankern (Panel erstreckt sich)
        GtkLayerShell.set_anchor(window, GtkLayerShell.Edge.RIGHT, True)   # rechts verankern (über gesamte Breite)
        GtkLayerShell.auto_exclusive_zone_enable(window)  # Panel reserviert Platz entsprechend seiner Höhe
        # CSS-Stylesheet laden
        css_provider = Gtk.CssProvider()
        css_path = os.path.join(os.path.dirname(__file__), "styles", "style.css")
        try:
            css_provider.load_from_path(css_path)
        except Exception as e:
            print(f"Fehler beim Laden der CSS-Styles: {e}", file=sys.stderr)
        # Styles global anwenden
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # Taskbar-Widget erstellen und dem Fenster hinzufügen
        taskbar = Taskbar(config)
        # Das Taskbar-Hauptwidget in das Fenster einsetzen
        # Hinweis: Taskbar ist ein eigenes Widget oder Container, den wir hier hinzufügen
        if isinstance(taskbar.widget, Gtk.Widget):
            window.set_child(taskbar.widget)
        else:
            # Falls Taskbar selbst ein Gtk.Widget ist (z.B. falls als Unterklasse implementiert)
            window.set_child(taskbar)
        # Fenster anzeigen
        window.present()
    # on_activate verbinden und App starten
    app.connect("activate", on_activate)
    app.run(None)

if __name__ == "__main__":
    main()
