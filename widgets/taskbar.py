import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk, GObject
from widgets.app_button import AppButton
from window_manager import get_windows, get_active_window

class Taskbar:
    """
    Die Taskbar enthält alle App-Buttons (gepinnte und laufende Anwendungen) sowie den Power-Button.
    Sie aktualisiert regelmäßig die Liste der Fenster und den Fokus-Status.
    """
    def __init__(self, config):
        self.config = config
        self.buttons_map = {}

        # Container für App-Buttons
        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # DropTarget für zukünftiges Drag-and-Drop-Reordering
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        self.tasks_box.add_controller(drop_target)

        # Power-Button
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown")
        power_icon.set_pixel_size(config.get("icon_size", 32))
        power_button = Gtk.Button()
        power_button.set_child(power_icon)
        power_button.add_css_class("power-button")
        power_button.connect("clicked", self.on_power_clicked)

        # Layout mit zentrierter App-Liste und Power-Button rechts
        self.container = Gtk.CenterBox()
        self.container.set_start_widget(None)
        self.container.set_center_widget(self.tasks_box)
        self.container.set_end_widget(power_button)
        self.container.add_css_class("taskbar")

        self.widget = self.container

        # Gepinnte Apps initial erzeugen
        for app in config.get("pinned_apps", []):
            app_class = app.get("class")
            exec_cmd = app.get("exec")
            icon_path = app.get("icon")

            btn = AppButton(app_class, icon_path=icon_path, exec_cmd=exec_cmd, pinned=True, config=config)
            btn.close_menu_item.set_sensitive(False)
            self.tasks_box.append(btn)
            self.buttons_map[app_class] = btn

        self.last_open_classes = set()
        self.current_active_class = None

        self.refresh(initial=True)
        GLib.timeout_add(500, self.refresh)

    def refresh(self, initial=False):
        active_info = get_active_window()
        active_class = active_info.get("class") if isinstance(active_info, dict) else None

        windows = get_windows()
        open_classes = {}
        for win in windows:
            cls = win.get("class")
            if cls:
                open_classes.setdefault(cls, []).append(win)

        if not initial:
            current_open_set = set(open_classes.keys())
            if active_class == self.current_active_class and current_open_set == self.last_open_classes:
                return True  # Keine Änderung

        self.last_open_classes = set(open_classes.keys())
        self.current_active_class = active_class

        for cls, wins in open_classes.items():
            if cls in self.buttons_map:
                btn = self.buttons_map[cls]
                btn.set_running(True)
            else:
                btn = AppButton(cls, icon_path=None, exec_cmd=cls, pinned=False, config=self.config)
                btn.set_running(True)
                btn.close_menu_item.set_sensitive(True)
                self.tasks_box.append(btn)
                self.buttons_map[cls] = btn

        for cls in list(self.buttons_map.keys()):
            btn = self.buttons_map[cls]
            if not btn.pinned and cls not in open_classes:
                self.tasks_box.remove(btn)
                del self.buttons_map[cls]

        for cls, btn in self.buttons_map.items():
            btn.set_running(cls in open_classes)

        for cls, btn in self.buttons_map.items():
            btn.set_focused(cls == active_class and active_class is not None)

        return True

    def on_drop(self, drop_target, value, x, y):
        """Drag-and-Drop-Erkennung (Reihenfolgeänderung oder Pinnen möglich)"""
        class_name = value
        if isinstance(value, GObject.Value):
            class_name = value.get_string()
        print(f"Drag-and-Drop: {class_name} wurde auf Taskleiste fallen gelassen (noch nicht umgesetzt).")
        return True

    def on_power_clicked(self, button):
        print("Karpbar wird geschlossen.")
        app = Gtk.Application.get_default()
        if app:
            app.quit()
