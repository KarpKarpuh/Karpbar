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

# GI-Versionen festlegen
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gtk4LayerShell', '1.0')
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell as LayerShell

from config import PINNED_APPS, APP_CONFIG
from window_manager import get_windows

# Größen-Konstanten
ICON_SIZE = 20
BUTTON_SIZE = 36
SPACING_BETWEEN_APP_BUTTONS = 3

# IconTheme für das aktuelle Display
display = Gdk.Display.get_default()
icon_theme = Gtk.IconTheme.get_for_display(display)

# hält laufende Prozesse
running_procs: dict[str, subprocess.Popen] = {}

def on_app_button_clicked(button, exec_cmd: str):
    """Startet oder fokussiert die Anwendung."""
    key = exec_cmd.split()[0].lower()
    proc = running_procs.get(key)
    if proc and proc.poll() is None:
        print(f"{key} läuft bereits.")
        return
    try:
        new_proc = subprocess.Popen(exec_cmd.split())
        running_procs[key] = new_proc
        print(f"{key} gestartet mit PID {new_proc.pid}.")
    except Exception as e:
        print(f"❌ Fehler beim Start von {key}: {e}")

def on_shutdown_clicked(button):
    """Beendet die Taskbar und die Anwendung."""
    print("⏻ Karpbar wird geschlossen.")
    Gtk.Application.get_default().quit()

def create_app_button(app_name: str) -> Gtk.Widget:
    """
    Erzeugt einen Button für die angegebene App.
    Nutzt APP_CONFIG für Overrides (icon, exec).
    """
    name = app_name.lower()
    cfg = APP_CONFIG.get(name, {})
    exec_cmd = cfg.get("exec", name)

    # Button-Grundstruktur
    button = Gtk.Button()
    button.set_size_request(BUTTON_SIZE, BUTTON_SIZE)
    button.set_margin_start(SPACING_BETWEEN_APP_BUTTONS)
    button.set_margin_end(SPACING_BETWEEN_APP_BUTTONS)

    # 1) Icon-Override aus config
    icon_path = cfg.get("icon", "")
    if icon_path and os.path.isfile(icon_path):
        image = Gtk.Image.new_from_file(icon_path)
        image.set_pixel_size(ICON_SIZE)
    else:
        # 2) ThemedIcon per Name oder Exec-Befehl
        image = None
        for key in (name, exec_cmd.split()[0].lower()):
            if icon_theme.has_icon(key):
                themed = Gio.ThemedIcon.new(key)
                image = Gtk.Image.new_from_gicon(themed)
                image.set_pixel_size(ICON_SIZE)
                break
        # 3) Fallback: Kurz-Label
        if image is None:
            image = Gtk.Label(label=name[:2].upper())

    image.set_valign(Gtk.Align.CENTER)
    image.set_halign(Gtk.Align.CENTER)
    button.set_child(image)
    button.connect("clicked", on_app_button_clicked, exec_cmd)
    return button

def build_taskbar_box() -> Gtk.Box:
    """Erzeugt die horizontale Taskbar mit Pinned- und dynamischen Apps."""
    hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

    # Pinned Apps
    for name in PINNED_APPS:
        hbox.append(create_app_button(name))

    # Dynamische Fenster (neben Pinned)
    running_windows = get_windows()
    pinned_set = {n.lower() for n in PINNED_APPS}
    seen: set[str] = set()
    for win in running_windows:
        cls = win.get("class", "").lower()
        if cls and cls not in pinned_set and cls not in seen:
            seen.add(cls)
            hbox.append(create_app_button(cls))

    # Spacer für rechtsbündige Elemente
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

def refresh(window: Gtk.Window) -> bool:
    """Ersetzt den Inhalt des Fensters mit aktueller Taskbar."""
    window.set_child(build_taskbar_box())
    return True

def on_activate(app: Gtk.Application):
    win = Gtk.ApplicationWindow(application=app)
    win.set_title("Karpbar")
    win.set_decorated(False)

    LayerShell.init_for_window(win)
    LayerShell.set_layer(win, LayerShell.Layer.BOTTOM)
    for edge in (LayerShell.Edge.BOTTOM, LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT):
        LayerShell.set_anchor(win, edge, True)
    LayerShell.auto_exclusive_zone_enable(win)

    win.set_child(build_taskbar_box())

    # Einfaches CSS für saubere Buttons
    css = Gtk.CssProvider()
    css.load_from_data(b"button { border: none; padding: 4px; }\n")
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
