import os
import errno
from gi.repository import Gtk, GLib, GObject
from widgets.app_button import AppButton
from window_manager import get_windows, focus_window_by_class, close_window_by_class

class Taskbar:
    """
    Karpbar Taskbar – event-getrieben mit Hyprland-IPC (.socket2.sock), inkl. automatischem Retry bei Verbindungsfehlern.
    """
    def __init__(self, config):
        self.config = config
        self.buttons_map = {}

        # Box für App-Buttons
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

        # Initial Buttons für bereits geöffnete Fenster
        for win in get_windows():
            cls = win.get("class")
            if not cls or cls in self.buttons_map:
                continue
            btn = AppButton(
                app_class=cls,
                exec_cmd=cls,
                pinned=any(p.get("class") == cls for p in config.get("pinned_apps", [])),
                config=config
            )
            btn.set_running(True)
            btn.set_focused(win.get("focused", False))
            self.tasks_box.append(btn)
            self.buttons_map[cls] = btn

        # IPC-Socket initialisieren (mit Retry bei Fehler)
        GLib.timeout_add_seconds(1, self._init_ipc_watch)

    def _init_ipc_watch(self):
        runtime = os.environ.get("XDG_RUNTIME_DIR")
        hypr_root = os.path.join(runtime, "hypr")
        try:
            sig_dirs = [
                d for d in os.listdir(hypr_root)
                if os.path.isdir(os.path.join(hypr_root, d))
            ]
            his = sig_dirs[0]  # Nimm erste gefundene Instanz-Signatur
            socket_path = os.path.join(hypr_root, his, ".socket2.sock")
            fd = os.open(socket_path, os.O_RDONLY | os.O_NONBLOCK)
            GLib.io_add_watch(fd, GLib.IO_IN, self._on_ipc_event)
        except OSError as e:
            # ENOENT (2) = Datei fehlt, ENXIO (6) = kein Listener / keine Adresse
            if e.errno in (errno.ENOENT, errno.ENXIO):
                # versuche in 1 Sekunde erneut
                return True  # Timeout bleibt aktiv
            else:
                print(f"⚠️ Fehler beim Öffnen des IPC-Sockets: {e}")
        return False  # Timeout entfernen, wenn erfolgreich oder bei anderem Fehler

    def _on_ipc_event(self, fd, condition):
        try:
            data = os.read(fd, 4096).decode().splitlines()
        except BlockingIOError:
            return True
        for line in data:
            if "\u003e\u003e" not in line:
                continue
            event, args = line.split(">>", 1)
            self._handle_event(event, args.strip())
        return True

    def _handle_event(self, event, args):
        if event == "openwindow":
            addr, ws, cls, title = args.split(",", 3)
            if cls in self.buttons_map:
                self.buttons_map[cls].set_running(True)
            else:
                btn = AppButton(app_class=cls, exec_cmd=cls, pinned=False, config=self.config)
                btn.set_running(True)
                self.tasks_box.append(btn)
                self.buttons_map[cls] = btn

        elif event == "closewindow":
            current = {w["class"] for w in get_windows()}
            for cls, btn in list(self.buttons_map.items()):
                if cls not in current and not any(
                    p.get("class") == cls for p in self.config.get("pinned_apps", [])
                ):
                    self.tasks_box.remove(btn)
                    del self.buttons_map[cls]

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
