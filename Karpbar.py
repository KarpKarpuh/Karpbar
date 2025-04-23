#!/usr/bin/env python3
from ctypes import CDLL
import os
import subprocess
import gi

# Layer Shell lib laden
try:
    CDLL("libgtk4-layer-shell.so")
except OSError as e:
    print(f"⚠️ LayerShell konnte nicht geladen werden: {e}")

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gio, Gtk4LayerShell as LayerShell

from config import PINNED_APPS

ICON_SIZE = 24
BUTTON_SIZE = 40

running_procs = {}

def on_app_button_clicked(button, app_index):
    app_info = PINNED_APPS[app_index]
    if app_index in running_procs and running_procs[app_index].poll() is None:
        print(f"{app_info['name']} läuft bereits.")
        return
    try:
        proc = subprocess.Popen(app_info["exec"])
        running_procs[app_index] = proc
        print(f"{app_info['name']} gestartet mit PID {proc.pid}.")
    except Exception as e:
        print(f"❌ Fehler beim Start von {app_info['name']}: {e}")

def on_shutdown_clicked(button):
    print("⏻ Karpbar wird geschlossen.")
    Gtk.Application.get_default().quit()

def refresh_icons():
    for idx, proc in list(running_procs.items()):
        if proc.poll() is not None:
            print(f"🛑 {PINNED_APPS[idx]['name']} wurde beendet.")
            del running_procs[idx]
    return True

def on_activate(app):
    window = Gtk.ApplicationWindow(application=app)
    window.set_title("Karpbar")
    window.set_decorated(False)

    # LayerShell Setup
    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.BOTTOM)
    LayerShell.set_anchor(window, LayerShell.Edge.BOTTOM, True)
    LayerShell.set_anchor(window, LayerShell.Edge.LEFT, True)
    LayerShell.set_anchor(window, LayerShell.Edge.RIGHT, True)
    LayerShell.auto_exclusive_zone_enable(window)

    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    window.set_child(hbox)

    # App Buttons
    for idx, app in enumerate(PINNED_APPS):
        button = Gtk.Button()
        button.set_size_request(BUTTON_SIZE, BUTTON_SIZE)
        button.set_margin_start(3)
        button.set_margin_end(3)

        icon_path = app.get("icon", "")
        if icon_path and os.path.isfile(icon_path):
            image = Gtk.Image.new_from_file(icon_path)
            image.set_pixel_size(ICON_SIZE)
            button.set_child(image)
        else:
            label = Gtk.Label(label=app["name"][:2].upper())
            button.set_child(label)

        button.connect("clicked", on_app_button_clicked, idx)
        hbox.append(button)

    # Spacer
    spacer = Gtk.Box()
    spacer.set_hexpand(True)
    hbox.append(spacer)

    # Power Button
    power_button = Gtk.Button()
    power_button.set_size_request(BUTTON_SIZE, BUTTON_SIZE)
    power_button.set_child(Gtk.Label(label="⏻"))
    power_button.connect("clicked", on_shutdown_clicked)
    hbox.append(power_button)

    # CSS
    css = Gtk.CssProvider()
    css.load_from_data(b"""
        button {
            border: none;
            padding: 4px;
        }
    """)
    display = Gdk.Display.get_default()
    Gtk.StyleContext.add_provider_for_display(display, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    window.present()
    GLib.timeout_add(1000, refresh_icons)

app = Gtk.Application(application_id="com.example.Karpbar")
app.connect("activate", on_activate)
app.run(None)
