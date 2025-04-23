#!/usr/bin/env python3
from ctypes import CDLL
import os
import subprocess
import gi

# Layer Shell laden
try:
    CDLL("libgtk4-layer-shell.so")
except OSError as e:
    print(f"⚠️ LayerShell konnte nicht geladen werden: {e}")

gi.require_version('Gtk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, GLib, Gio, Gtk4LayerShell as LayerShell

from config import PINNED_APPS
from window_manager import get_windows

ICON_SIZE = 20
BUTTON_SIZE = 36
SPACING_BETWEEN_APP_BUTTONS = 3

running_procs = {}

def on_app_button_clicked(button, app_info):
    if app_info.get("exec") in running_procs and running_procs[app_info["exec"]].poll() is None:
        print(f"{app_info['name']} läuft bereits.")
        return
    try:
        proc = subprocess.Popen(app_info["exec"])
        running_procs[app_info["exec"]] = proc
        print(f"{app_info['name']} gestartet mit PID {proc.pid}.")
    except Exception as e:
        print(f"❌ Fehler beim Start von {app_info['name']}: {e}")

def on_shutdown_clicked(button):
    print("⏻ Karpbar wird geschlossen.")
    Gtk.Application.get_default().quit()

def create_app_button(app_info):
    button = Gtk.Button()
    button.set_size_request(BUTTON_SIZE, BUTTON_SIZE)
    button.set_margin_start(SPACING_BETWEEN_APP_BUTTONS)
    button.set_margin_end(SPACING_BETWEEN_APP_BUTTONS)

    icon_path = app_info.get("icon", "")
    if icon_path and os.path.isfile(icon_path):
        image = Gtk.Image.new_from_file(icon_path)
        image.set_pixel_size(ICON_SIZE)
        image.set_valign(Gtk.Align.CENTER)
        image.set_halign(Gtk.Align.CENTER)
        button.set_child(image)
    else:
        label = Gtk.Label(label=app_info["name"][:2].upper())
        label.set_valign(Gtk.Align.CENTER)
        label.set_halign(Gtk.Align.CENTER)
        button.set_child(label)

    button.connect("clicked", on_app_button_clicked, app_info)
    return button

def build_taskbar_box():
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

    # Pinned Apps
    for app in PINNED_APPS:
        hbox.append(create_app_button(app))

    # Dynamische Apps
    running_windows = get_windows()
    pinned_names = {a["name"].lower() for a in PINNED_APPS}
    added_classes = set()

    for win in running_windows:
        cls = win["class"].lower()
        if cls not in pinned_names and cls not in added_classes:
            added_classes.add(cls)
            hbox.append(create_app_button({
                "name": cls,
                "icon": "",
                "exec": cls
            }))

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

    return hbox

def refresh(window):
    new_box = build_taskbar_box()
    window.set_child(new_box)
    return True

def on_activate(app):
    window = Gtk.ApplicationWindow(application=app)
    window.set_title("Karpbar")
    window.set_decorated(False)

    LayerShell.init_for_window(window)
    LayerShell.set_layer(window, LayerShell.Layer.BOTTOM)
    LayerShell.set_anchor(window, LayerShell.Edge.BOTTOM, True)
    LayerShell.set_anchor(window, LayerShell.Edge.LEFT, True)
    LayerShell.set_anchor(window, LayerShell.Edge.RIGHT, True)
    LayerShell.auto_exclusive_zone_enable(window)

    taskbar_box = build_taskbar_box()
    window.set_child(taskbar_box)

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
    GLib.timeout_add(1000, lambda: refresh(window))

app = Gtk.Application(application_id="com.example.Karpbar")
app.connect("activate", on_activate)
app.run(None)
