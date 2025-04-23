from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')  # stellt sicher, dass LayerShell vor Wayland geladen wird&#8203;:contentReference[oaicite:14]{index=14}

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gtk4LayerShell as LayerShell

# Anwendung und Fenster erstellen
app = Gtk.Application(application_id='com.example.gtk4layershell')
def on_activate(app):
    # Hauptfenster erzeugen
    window = Gtk.ApplicationWindow(application=app)
    window.set_default_size(400, 100)
    # Layer-Shell initialisieren und Eigenschaften setzen
    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.TOP)          # z.B. oberste Schicht (Panel)
    LayerShell.set_anchor(window, LayerShell.Edge.BOTTOM, True) # am unteren Bildschirmrand verankern
    LayerShell.auto_exclusive_zone_enable(window)               # automatische Exclusivzone (verhindert Überlappung)
    # Inhalt (z.B. Button) hinzufügen
    button = Gtk.Button(label='Beenden')
    button.connect('clicked', lambda btn: window.close())
    window.set_child(button)
    window.present()  # Fenster anzeigen (GTK4 verwendet present() statt show_all())
app.connect('activate', on_activate)
app.run(None)
