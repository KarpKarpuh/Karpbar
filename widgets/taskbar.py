import os
import errno
import socket
from gi.repository import Gtk, Gdk, GLib, GObject
from widgets.app_button import AppButton
from window_manager import get_windows

class Taskbar:
    def __init__(self, config):
        self.config = config
        self.buttons_map = {}
        self.task_order = []
        self.overflow_button = None
        self.overflow_popover = None

        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        power_icon = Gtk.Image.new_from_icon_name("system-shutdown")
        power_icon.set_pixel_size(config.get("icon_size", 32))
        power_button = Gtk.Button()
        power_button.set_child(power_icon)
        power_button.add_css_class("power-button")
        power_button.connect("clicked", lambda _: Gtk.Application.get_default().quit())

        self.container = Gtk.CenterBox()
        self.container.set_start_widget(None)
        self.container.set_center_widget(self.tasks_box)
        self.container.set_end_widget(power_button)
        self.container.add_css_class("taskbar")
        self.widget = self.container

        current_windows = get_windows()
        current_classes = {w.get("class") for w in current_windows if w.get("class")}
        all_initial_classes = list(current_classes.union({p.get("class") for p in config.get("pinned_apps", [])}))
        for cls in all_initial_classes:
            if not cls:
                continue
            btn = AppButton(
                app_class=cls,
                exec_cmd=cls,
                pinned=any(p.get("class") == cls for p in config.get("pinned_apps", [])),
                config=config,
                taskbar=self
            )
            is_running = cls in current_classes
            btn.set_running(is_running)
            focused = any(w.get("class") == cls and w.get("focused") for w in current_windows)
            btn.set_focused(focused)
            self.tasks_box.append(btn)
            self.buttons_map[cls] = btn
            self.task_order.append(cls)

        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        self.tasks_box.add_controller(drop_target)

        self._update_overflow()

        runtime = os.environ.get("XDG_RUNTIME_DIR")
        hypr_root = os.path.join(runtime, "hypr")
        try:
            sig_dirs = [d for d in os.listdir(hypr_root) if os.path.isdir(os.path.join(hypr_root, d))]
            his = sig_dirs[0]
            socket_path = os.path.join(hypr_root, his, ".socket2.sock")

            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.setblocking(False)
            self.sock.connect(socket_path)

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

        if event == "openwindow":
            _, _, cls, _ = args.split(",", 3)
            if cls not in self.buttons_map:
                btn = AppButton(app_class=cls, exec_cmd=cls, pinned=False, config=self.config, taskbar=self)
                self.tasks_box.append(btn)
                self.buttons_map[cls] = btn
                self.task_order.append(cls)
            self.buttons_map[cls].set_running(True)

        elif event == "closewindow":
            addr = args
            for cls, btn in list(self.buttons_map.items()):
                pinned = any(p.get("class") == cls for p in self.config.get("pinned_apps", []))
                if cls in running_classes:
                    btn.set_running(True)
                else:
                    if pinned:
                        btn.set_running(False)
                    else:
                        self.tasks_box.remove(btn)
                        del self.buttons_map[cls]
                        if cls in self.task_order:
                            self.task_order.remove(cls)

        elif event in ("activewindow", "activewindowv2"):
            cls = args.split(",", 1)[0]
            for c, btn in self.buttons_map.items():
                btn.set_focused(c == cls)

        self._update_overflow()

    def on_drop(self, drop_target, value, x, y):
        class_name = value.get_string() if isinstance(value, GObject.Value) else str(value)
        if not class_name or class_name not in self.buttons_map:
            return False

        children = [child for child in self.tasks_box if child != self.overflow_button]
        dragged_btn = self.buttons_map[class_name]
        if dragged_btn in children:
            children.remove(dragged_btn)

        new_index = len(children)
        for idx, child in enumerate(children):
            alloc = child.get_allocation() if hasattr(child, "get_allocation") else None
            if alloc:
                child_x = alloc.x
                child_width = alloc.width
            else:
                child_x = idx * (self.config.get("button_width", 36) + self.tasks_box.get_spacing())
                child_width = self.config.get("button_width", 36)
            if x < child_x + child_width / 2:
                new_index = idx
                break

        old_index = self.task_order.index(class_name) if class_name in self.task_order else None
        if old_index is None:
            return False

        if old_index < new_index:
            new_index -= 1
        self.task_order.remove(class_name)
        if new_index < 0:
            new_index = 0
        self.task_order.insert(new_index, class_name)

        self.tasks_box.remove(dragged_btn)
        if new_index == 0:
            self.tasks_box.prepend(dragged_btn)
        else:
            prev_class = self.task_order[new_index - 1]
            prev_btn = self.buttons_map.get(prev_class)
            if prev_btn and prev_btn.get_parent() is self.tasks_box:
                self.tasks_box.insert_child_after(dragged_btn, prev_btn)
            else:
                self.tasks_box.append(dragged_btn)

        self._update_overflow()
        self._update_pinned_config_order()
        return True

    def _update_pinned_config_order(self):
        from config_loader import config_data
        pinned_apps = config_data.get("pinned_apps", [])
        if not pinned_apps:
            return
        pinned_classes_ordered = [cls for cls in self.task_order if cls in {p.get("class") for p in pinned_apps}]
        new_pinned_list = []
        for cls in pinned_classes_ordered:
            for entry in pinned_apps:
                if entry.get("class") == cls:
                    new_pinned_list.append(entry)
                    break
        config_data["pinned_apps"] = new_pinned_list

    def _update_overflow(self):
        total_count = len(self.task_order)
        max_visible = 10

        if total_count > max_visible:
            visible_classes = self.task_order[:max_visible]
        else:
            visible_classes = self.task_order[:]

        for child in list(self.tasks_box):
            if child == self.overflow_button:
                continue
            if isinstance(child, AppButton) and child.app_class not in visible_classes:
                self.tasks_box.remove(child)

        for cls in visible_classes:
            btn = self.buttons_map.get(cls)
            if not btn:
                continue
            if btn.get_parent() is None:
                idx = visible_classes.index(cls)
                if idx == 0:
                    self.tasks_box.prepend(btn)
                else:
                    prev_class = visible_classes[idx - 1]
                    prev_btn = self.buttons_map.get(prev_class)
                    if prev_btn and prev_btn.get_parent() is self.tasks_box:
                        self.tasks_box.insert_child_after(btn, prev_btn)
                    else:
                        self.tasks_box.append(btn)

        if total_count > max_visible:
            if self.overflow_button is None:
                self._create_overflow_button()
            if self.overflow_button.get_parent() is None:
                self.tasks_box.append(self.overflow_button)
        else:
            if self.overflow_button and self.overflow_button.get_parent():
                self.tasks_box.remove(self.overflow_button)

    def _create_overflow_button(self):
        self.overflow_button = Gtk.Button(label="⋮")
        self.overflow_button.add_css_class("overflow-button")
        btn_width = self.config.get("button_width", 36)
        btn_height = self.config.get("button_height", 36)
        self.overflow_button.set_size_request(btn_width, btn_height)
        self.overflow_popover = Gtk.Popover.new()
        self.overflow_popover.set_parent(self.overflow_button)
        self.overflow_popover.set_autohide(True)
        self.overflow_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.overflow_popover.set_child(self.overflow_list)
        self.overflow_button.connect("clicked", self._on_overflow_clicked)

    def _on_overflow_clicked(self, button):
        if not self.overflow_popover:
            return
        for child in list(self.overflow_list):
            self.overflow_list.remove(child)
        hidden_classes = self.task_order[10:]
        for cls in hidden_classes:
            btn = self.buttons_map.get(cls)
            if not btn:
                continue
            icon_widget = None
            if btn.icon_widget:
                icon_image = Gtk.Image.new_from_icon_name(cls)
                icon_image.set_pixel_size(self.config.get("icon_size", 32))
                icon_widget = icon_image
            app_label = Gtk.Label(label=cls)
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            if icon_widget:
                item_box.append(icon_widget)
            item_box.append(app_label)
            item_button = Gtk.Button()
            item_button.set_child(item_box)
            item_button.add_css_class("overflow-app-item")
            item_button.connect("clicked", self._on_overflow_item_activated, cls)
            self.overflow_list.append(item_button)
        self.overflow_popover.popup()

    def _on_overflow_item_activated(self, button, app_class):
        btn = self.buttons_map.get(app_class)
        if btn:
            btn.on_left_click(None)
        if self.overflow_popover:
            self.overflow_popover.popdown()

    def remove_app(self, class_name):
        btn = self.buttons_map.get(class_name)
        if not btn:
            return
        if btn.get_parent():
            self.tasks_box.remove(btn)
        if class_name in self.buttons_map:
            del self.buttons_map[class_name]
        if class_name in self.task_order:
            self.task_order.remove(class_name)
        self._update_overflow()
