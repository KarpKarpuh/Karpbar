import os
import errno
import socket
from gi.repository import Gtk, GLib, GObject
from widgets.app_button import AppButton
from window_manager import get_windows

class Taskbar:
    """
    Karpbar Taskbar: Event-getrieben über Hyprland-IPC (.socket2.sock).
    Dynamische Updates: Open, Close und Focus mit set_running und set_focused.
    """
    def __init__(self, config):
        self.config = config
        self.buttons_map = {}

        # Container für App-Buttons
        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Power-Button rechts
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown")
        power_icon.set_pixel_size(config.get("icon_size", 32))
        power_button = Gtk.Button()
        power_button.set_child(power_icon)
        power_button.add_css_class("power-button")
        power_button.connect("clicked", lambda _: Gtk.Application.get_default().quit())

        # Zentriertes Layout
        self.container = Gtk.CenterBox()
        self.container.set_start_widget(None)
        self.container.set_center_widget(self.tasks_box)
        self.container.set_end_widget(power_button)
        self.container.add_css_class("taskbar")
        self.widget = self.container

        # Initial Buttons für bereits geöffnete Fenster (inklusive gepinnter)
        current_windows = get_windows()
        current_classes = {w.get("class") for w in current_windows if w.get("class")}
        for cls in current_classes.union({p.get("class") for p in config.get("pinned_apps", [])}):
            if not cls:
                continue
            btn = AppButton(
                app_class=cls,
                exec_cmd=cls,
                pinned=any(p.get("class") == cls for p in config.get("pinned_apps", [])),
                config=config
            )
            is_running = cls in current_classes
            btn.set_running(is_running)
            focused = any(w.get("class") == cls and w.get("focused") for w in current_windows)
            btn.set_focused(focused)
            self.tasks_box.append(btn)
            self.buttons_map[cls] = btn

        # Hyprland-IPC Socket2: als Unix-Domain-Stream verbinden
        runtime = os.environ.get("XDG_RUNTIME_DIR")
        hypr_root = os.path.join(runtime, "hypr")
        try:
            sig_dirs = [d for d in os.listdir(hypr_root)
                        if os.path.isdir(os.path.join(hypr_root, d))]
            his = sig_dirs[0]  # erste gefundene Instanz-Signatur
            socket_path = os.path.join(hypr_root, his, ".socket2.sock")

            # Unix-Domain-Stream-Socket öffnen & verbinden
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            self.sock.connect(socket_path)

            # Callback bei eingehenden Daten
            GLib.io_add_watch(self.sock, GLib.IO_IN, self._on_ipc_event)
        except OSError as e:
            if e.errno in (errno.ENOENT, errno.ENXIO):
                print(f"⚠️ Hyprland-IPC Socket nicht bereit: {socket_path}")
            else:
                print(f"⚠️ Fehler beim Öffnen des IPC-Sockets: {e}")

    def _on_ipc_event(self, source, condition):
        try:
            data = source.recv(4096).decode().splitlines()
        except BlockingIOError:
            return True
        for line in data:
            if ">>" not in line:
                continue
            event, args = line.split(">>", 1)
            self._handle_event(event, args.strip())
        return True

    def _handle_event(self, event, args):
        current_windows = get_windows()
        running_classes = {w.get("class") for w in current_windows if w.get("class")}

        # Neues Fenster geöffnet
        if event == "openwindow":
            _, _, cls, _ = args.split(",", 3)
            if cls not in self.buttons_map:
                btn = AppButton(app_class=cls, exec_cmd=cls, pinned=False, config=self.config)
                self.tasks_box.append(btn)
                self.buttons_map[cls] = btn
            self.buttons_map[cls].set_running(True)

        # Fenster geschlossen
        elif event == "closewindow":
            addr = args
            # Für alle Buttons prüfen
            for cls, btn in list(self.buttons_map.items()):
                pinned = any(p.get("class") == cls for p in self.config.get("pinned_apps", []))
                if cls in running_classes:
                    # weiterhin laufend
                    btn.set_running(True)
                else:
                    if pinned:
                        # gepinnt, aber nicht mehr laufend -> nur Indikator ausschalten
                        btn.set_running(False)
                    else:
                        # nicht gepinnt und nicht laufend -> Button entfernen
                        self.tasks_box.remove(btn)
                        del self.buttons_map[cls]

        # Fokus geändert
        elif event in ("activewindow", "activewindowv2"):
            cls = args.split(",", 1)[0]
            for c, btn in self.buttons_map.items():
                btn.set_focused(c == cls)

    def on_drop(self, drop_target, value, x, y):
        class_name = value.get_string() if isinstance(value, GObject.Value) else value
        print(f"Drag-and-Drop: {class_name} auf Taskbar gefallen")
        return True

    def on_power_clicked(self, button):
        Gtk.Application.get_default().quit()
