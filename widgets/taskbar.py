# taskbar.py

import os
import errno
import socket
import math
from gi.repository import Gtk, Gdk, GLib, GObject
from widgets.app_button import AppButton
from window_manager import get_windows

class Taskbar:
    PAGE_SIZE = 10

    def __init__(self, config):
        self.config = config
        self.buttons_map = {}
        self.task_order = []
        self.current_page = 1

        # Haupt-Container mit Spacer für rechtsbündige Icons
        self.container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.container.append(spacer)

        # Box für App-Buttons
        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.container.append(self.tasks_box)

        # Pfeil-Buttons für Seitenwechsel
        btn_width = config.get("button_width", 36)
        btn_height = config.get("button_height", 36)
        self.page_up_button = Gtk.Button(label="▲")
        self.page_up_button.set_size_request(btn_width, btn_height)
        self.page_up_button.add_css_class("page-arrow")
        self.page_up_button.connect("clicked", lambda _: self.on_page_up())
        self.page_up_button.set_visible(False)
        self.container.append(self.page_up_button)

        self.page_down_button = Gtk.Button(label="▼")
        self.page_down_button.set_size_request(btn_width, btn_height)
        self.page_down_button.add_css_class("page-arrow")
        self.page_down_button.connect("clicked", lambda _: self.on_page_down())
        self.page_down_button.set_visible(False)
        self.container.append(self.page_down_button)

        # Power-Button (Shutdown)
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown")
        power_icon.set_pixel_size(config.get("icon_size", 32))
        power_button = Gtk.Button()
        power_button.set_child(power_icon)
        power_button.add_css_class("power-button")
        power_button.connect("clicked", lambda _: Gtk.Application.get_default().quit())
        self.container.append(power_button)

        self.container.add_css_class("taskbar")
        self.widget = self.container

        # Initiale Buttons: zuerst gepinnte in gespeicherter Reihenfolge, dann laufende
        pinned = [p["class"] for p in config.get("pinned_apps", [])]
        running = [w.get("class") for w in get_windows() if w.get("class") not in pinned]
        all_initial = pinned + running

        for cls in all_initial:
            btn = AppButton(
                app_class=cls,
                exec_cmd=cls,
                pinned=(cls in pinned),
                config=config,
                taskbar=self
            )
            btn.set_running(cls in running)
            btn.set_focused(any(w.get("class") == cls and w.get("focused") for w in get_windows()))
            self.tasks_box.append(btn)
            self.buttons_map[cls] = btn
            self.task_order.append(cls)

        # Drag & Drop Controller
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        self.tasks_box.add_controller(drop_target)

        # Hyprland-IPC Socket einrichten
        runtime = os.environ.get("XDG_RUNTIME_DIR")
        hypr_root = os.path.join(runtime or "", "hypr")
        try:
            sig_dirs = [d for d in os.listdir(hypr_root) if os.path.isdir(os.path.join(hypr_root, d))]
            his = sig_dirs[0]
            socket_path = os.path.join(hypr_root, his, ".socket2.sock")

            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            self.sock.connect(socket_path)
            GLib.io_add_watch(self.sock, GLib.IO_IN, self._on_ipc_event)
        except Exception as e:
            # Ignoriere falls Socket nicht verfügbar
            pass

        # Erste Anzeige aktualisieren
        self._update_page_display()

    def on_page_up(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._update_page_display()

    def on_page_down(self):
        total = len(self.task_order)
        pages = math.ceil(total / self.PAGE_SIZE)
        if self.current_page < pages:
            self.current_page += 1
            self._update_page_display()

    def _update_page_display(self):
        total = len(self.task_order)
        pages = max(1, math.ceil(total / self.PAGE_SIZE))
        if self.current_page > pages:
            self.current_page = pages

        start = (self.current_page - 1) * self.PAGE_SIZE
        end = start + self.PAGE_SIZE
        visible = self.task_order[start:end]

        # Entferne Buttons, die nicht auf dieser Seite liegen
        for child in list(self.tasks_box):
            if isinstance(child, AppButton) and child.app_class not in visible:
                self.tasks_box.remove(child)

        # Füge fehlende Buttons in korrekter Reihenfolge ein
        for idx, cls in enumerate(visible):
            btn = self.buttons_map.get(cls)
            if btn and btn.get_parent() is None:
                if idx == 0:
                    self.tasks_box.prepend(btn)
                else:
                    prev = visible[idx - 1]
                    self.tasks_box.insert_child_after(btn, self.buttons_map[prev])

        # Seiten-Pfeile steuern
        if pages > 1:
            self.page_up_button.set_visible(True)
            self.page_down_button.set_visible(True)
            self.page_up_button.set_sensitive(self.current_page > 1)
            self.page_down_button.set_sensitive(self.current_page < pages)
        else:
            self.page_up_button.set_visible(False)
            self.page_down_button.set_visible(False)

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
        current = get_windows()
        running = {w.get("class") for w in current if w.get("class")}

        if event == "openwindow":
            _, _, cls, _ = args.split(",", 3)
            if cls not in self.buttons_map:
                btn = AppButton(cls, exec_cmd=cls, pinned=False, config=self.config, taskbar=self)
                self.buttons_map[cls] = btn
                self.task_order.append(cls)
            self.buttons_map[cls].set_running(True)

        elif event == "closewindow":
            for cls, btn in list(self.buttons_map.items()):
                if cls not in running:
                    pinned = any(p.get("class") == cls for p in self.config.get("pinned_apps", []))
                    if pinned:
                        btn.set_running(False)
                    else:
                        self.tasks_box.remove(btn)
                        del self.buttons_map[cls]
                        self.task_order.remove(cls)

        elif event in ("activewindow", "activewindowv2"):
            cls = args.split(",", 1)[0]
            for c, btn in self.buttons_map.items():
                btn.set_focused(c == cls)

        self._update_page_display()

    def on_drop(self, drop_target, value, x, y):
        class_name = value.get_string() if isinstance(value, GObject.Value) else str(value)
        if class_name not in self.buttons_map:
            return False

        children = [c for c in self.tasks_box if isinstance(c, AppButton)]
        dragged = self.buttons_map[class_name]
        if dragged in children:
            children.remove(dragged)

        # Bestimme neue Position
        new_idx = len(children)
        for idx, child in enumerate(children):
            alloc = child.get_allocation()
            if x < alloc.x + alloc.width / 2:
                new_idx = idx
                break

        old_idx = self.task_order.index(class_name)
        if old_idx < new_idx:
            new_idx -= 1
        self.task_order.remove(class_name)
        self.task_order.insert(max(0, new_idx), class_name)

        # Visuell neu anordnen
        self.tasks_box.remove(dragged)
        if new_idx == 0:
            self.tasks_box.prepend(dragged)
        else:
            prev = self.task_order[new_idx - 1]
            self.tasks_box.insert_child_after(dragged, self.buttons_map[prev])

        self._update_pinned_config_order()
        self._update_page_display()
        return True

    def _update_pinned_config_order(self):
        from config_loader import config_data, save_config
        pinned = config_data.get("pinned_apps", [])
        if not pinned:
            return
        ordered = [cls for cls in self.task_order if any(p["class"] == cls for p in pinned)]
        new_list = []
        for cls in ordered:
            for entry in pinned:
                if entry["class"] == cls:
                    new_list.append(entry)
                    break
        config_data["pinned_apps"] = new_list
        save_config()

    def remove_app(self, class_name):
        btn = self.buttons_map.get(class_name)
        if btn and btn.get_parent():
            self.tasks_box.remove(btn)
        self.buttons_map.pop(class_name, None)
        if class_name in self.task_order:
            self.task_order.remove(class_name)
        self._update_page_display()
