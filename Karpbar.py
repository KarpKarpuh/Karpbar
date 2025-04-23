#!/usr/bin/env python3
import os
import subprocess
from ctypes import CDLL
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

# ─── Konfigurierbare Größen ────────────────────────────────────────────────────
ICON_SIZE               = 22    # Breite/Höhe des Icons oder Fallback-Labels
BUTTON_WIDTH            = 36    # Breite des Buttons
BUTTON_HEIGHT           = 30    # Höhe des Buttons (inkl. Indikator unten)
SPACING_BETWEEN_BUTTONS = 3     # Horizontaler Abstand zwischen den Buttons
ICON_INDICATOR_SPACING  = 1     # Vertikaler Abstand Icon → Indikator
INDICATOR_HEIGHT        = 3     # Höhe des Indikators
INDICATOR_WIDTH         = 14    # Breite des Indikators
# ────────────────────────────────────────────────────────────────────────────────

display    = Gdk.Display.get_default()
icon_theme = Gtk.IconTheme.get_for_display(display)
running_procs: dict[str, subprocess.Popen] = {}


def on_app_button_clicked(button, exec_cmd: str):
    key = exec_cmd.split()[0].lower()
    proc = running_procs.get(key)
    if proc and proc.poll() is None:
        return
    try:
        running_procs[key] = subprocess.Popen(exec_cmd.split())
    except Exception as e:
        print(f"❌ Fehler beim Start von {key}: {e}")


def on_shutdown_clicked(button):
    Gtk.Application.get_default().quit()


def create_app_button(app_name: str, is_running: bool = False) -> Gtk.Widget:
    """Variant 1: kein Spacer, Abstand via spacing und margin_top."""
    name     = app_name.lower()
    cfg      = APP_CONFIG.get(name, {})
    exec_cmd = cfg.get("exec", name)

    # Button-Größe setzen
    button = Gtk.Button()
    button.set_size_request(BUTTON_WIDTH, BUTTON_HEIGHT)
    button.set_margin_start(SPACING_BETWEEN_BUTTONS)
    button.set_margin_end(SPACING_BETWEEN_BUTTONS)
    button.set_hexpand(False)
    button.set_vexpand(False)

    # VBox mit spacing = ICON_INDICATOR_SPACING, keine Expansion
    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=ICON_INDICATOR_SPACING)
    vbox.set_halign(Gtk.Align.CENTER)
    vbox.set_valign(Gtk.Align.CENTER)
    vbox.set_hexpand(False)
    vbox.set_vexpand(False)

    # Icon oder Fallback-Label
    icon_path = cfg.get("icon", "")
    if icon_path and os.path.isfile(icon_path):
        icon_widget = Gtk.Image.new_from_file(icon_path)
        icon_widget.set_pixel_size(ICON_SIZE)
    else:
        icon_widget = None
        for key in (name, exec_cmd.split()[0].lower()):
            if icon_theme.has_icon(key):
                icon_widget = Gtk.Image.new_from_gicon(Gio.ThemedIcon.new(key))
                icon_widget.set_pixel_size(ICON_SIZE)
                break
        if icon_widget is None:
            icon_widget = Gtk.Label(label=name[:2].upper())

    icon_widget.set_size_request(ICON_SIZE, ICON_SIZE)
    icon_widget.set_halign(Gtk.Align.CENTER)
    icon_widget.set_valign(Gtk.Align.CENTER)
    vbox.append(icon_widget)

    # Indikator direkt nach Icon mit margin_top
    indicator = Gtk.Box()
    indicator.set_size_request(INDICATOR_WIDTH, INDICATOR_HEIGHT)
    indicator.set_margin_top(ICON_INDICATOR_SPACING)
    indicator.set_halign(Gtk.Align.CENTER)
    indicator.add_css_class("indicator")
    if is_running:
        indicator.add_css_class("active")
    vbox.append(indicator)

    button.set_child(vbox)
    button.connect("clicked", on_app_button_clicked, exec_cmd)
    return button


def build_taskbar_box() -> Gtk.Box:
    hbox    = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    running = {w['class'].lower() for w in get_windows()}

    for name in PINNED_APPS:
        btn = create_app_button(name, name.lower() in running)
        hbox.append(btn)

    pinned = {n.lower() for n in PINNED_APPS}
    seen   = set()
    for w in get_windows():
        cls = w.get('class', '').lower()
        if cls and cls not in pinned and cls not in seen:
            seen.add(cls)
            hbox.append(create_app_button(cls, True))

    spacer = Gtk.Box(); spacer.set_hexpand(True); hbox.append(spacer)

    power_btn = Gtk.Button()
    power_btn.set_size_request(BUTTON_WIDTH, BUTTON_HEIGHT)
    power_btn.set_hexpand(False)
    power_btn.set_vexpand(False)
    power_btn.set_child(Gtk.Label(label="⏻"))
    power_btn.connect("clicked", on_shutdown_clicked)
    hbox.append(power_btn)

    return hbox


def on_activate(app: Gtk.Application):
    win = Gtk.ApplicationWindow(application=app)
    win.set_decorated(False)

    LayerShell.init_for_window(win)
    LayerShell.set_layer(win, LayerShell.Layer.BOTTOM)
    for edge in (LayerShell.Edge.BOTTOM, LayerShell.Edge.LEFT, LayerShell.Edge.RIGHT):
        LayerShell.set_anchor(win, edge, True)
    LayerShell.auto_exclusive_zone_enable(win)

    css = Gtk.CssProvider()
    css.load_from_data(b"""
        button { border: none; margin: 0; padding: 0; }
        .indicator { background-color: rgba(128,128,128,0.5); border-radius: 1px; }
        .indicator.active { background-color: rgba(0,160,0,0.8); }
    """)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    win.set_child(build_taskbar_box())
    win.present()
    GLib.timeout_add(1000, lambda: (win.set_child(build_taskbar_box()), True))


if __name__ == '__main__':
    app = Gtk.Application(application_id="com.example.Karpbar")
    app.connect('activate', on_activate)
    app.run(None)
