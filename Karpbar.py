#!/usr/bin/env python3
from ctypes import CDLL
import subprocess
import gi

# Layer Shell laden
try:
    CDLL("libgtk4-layer-shell.so")
except OSError as e:
    print(f"⚠️ LayerShell konnte nicht geladen werden: {e}")

# GI-Versionen festlegen
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LayerShell

from config import PINNED_APPS
from window_manager import get_windows

# Konstanten für Größen
ICON_SIZE = 20
BUTTON_SIZE = 36
SPACING_BETWEEN_APP_BUTTONS = 3

# IconTheme für das Display holen
display = Gdk.Display.get_default()
icon_theme = Gtk.IconTheme.get_for_display(display)

running_procs = {}

def on_app_button_clicked(button, app_info):
    exec_key = app_info["exec"].split()[0].lower()
    proc = running_procs.get(exec_key)
    if proc and proc.poll() is None:
        print(f"{app_info['name']} läuft bereits.")
        return
    try:
        new_proc = subprocess.Popen(app_info["exec"].split())
        running_procs[exec_key] = new_proc
        print(f"{app_info['name']} gestartet mit PID {new_proc.pid}.")
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

    # Icon aus IconTheme laden: zuerst Name, dann exec-Befehl
    exec_cmd = app_info["exec"].split()[0].lower()
    icon_candidates = [app_info["name"].lower(), exec_cmd]
    image = None
    for icon_name in icon_candidates:
        if icon_theme.has_icon(icon_name):
            themed_icon = Gio.ThemedIcon.new(icon_name)
            image = Gtk.Image.new_from_gicon(themed_icon)
            image.set_pixel_size(ICON_SIZE)
            break
    # Fallback: Label mit Kürzel
    if image is None:
        image = Gtk.Label(label=exec_cmd[:2].upper())

    image.set_valign(Gtk.Align.CENTER)
    image.set_halign(Gtk.Align.CENTER)
    button.set_child(image)
    button.connect("clicked", on_app_button_clicked, app_info)
    return button


def build_taskbar_box():
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

    # Pinned Apps
    for app in PINNED_APPS:
        hbox.append(create_app_button(app))

    # Dynamische Fenster hinzufügen
    running_windows = get_windows()
    pinned_names = {a["name"].lower() for a in PINNED_APPS}
    seen = set()
    for win in running_windows:
        cls = win.get("class", "").lower()
        if cls and cls not in pinned_names and cls not in seen:
            seen.add(cls)
            hbox.append(create_app_button({
                "name": cls,
                "exec": cls
            }))

    # Spacer nach rechts
    spacer = Gtk.Box()
    spacer.set_hexpand(True)
    hbox.append(spacer)

    # Power-Button
    power_btn = Gtk.Button()
    power_btn.set_size_request(BUTTON_SIZE, BUTTON_SIZE)
    power_btn.set_child(Gtk.Label(label="⏻"))
    power_btn.connect("clicked", on_shutdown_clicked)
    hbox.append(power_btn)

    return hbox


def refresh(window):
    window.set_child(build_taskbar_box())
    return True


def on_activate(app):
    win = Gtk.ApplicationWindow(application=app)
    win.set_title("Karpbar")
    win.set_decorated(False)

    LayerShell.init_for_window(win)
    LayerShell.set_layer(win, LayerShell.Layer.BOTTOM)
    for edge in (LayerShell.Edge.BOTTOM, LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT):
        LayerShell.set_anchor(win, edge, True)
    LayerShell.auto_exclusive_zone_enable(win)

    win.set_child(build_taskbar_box())

    # Einfaches CSS für Buttons
    css = Gtk.CssProvider()
    css.load_from_data(b"button { border: none; padding: 4px; }")
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win.present()
    GLib.timeout_add(1000, lambda: refresh(win))

if __name__ == '__main__':
    app = Gtk.Application(application_id="com.example.Karpbar")
    app.connect("activate", on_activate)
    app.run(None)
