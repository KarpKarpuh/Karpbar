import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import subprocess
from window_manager import focus_window_by_class, close_window_by_class

class AppButton(Gtk.Button):
    def __init__(self, app_class, icon_path=None, exec_cmd=None, pinned=False, icon_size=32):
        super().__init__()
        self.app_class = app_class
        self.exec_cmd = exec_cmd
        self.pinned = pinned
        self.is_running = False
        self.is_focused = False
        self.icon_size = icon_size

        self.add_css_class("app-button")

        # === ICON AUSWÄHLEN UND WRAPPEN ===
        if icon_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    filename=icon_path,
                    width=icon_size,
                    height=icon_size,
                    preserve_aspect_ratio=True
                )
                image = Gtk.Image.new()
                image.set_from_pixbuf(pixbuf)
                image.set_pixel_size(icon_size)
                icon_widget = self._wrap_icon_widget(image)
            except Exception as e:
                print(f"Warnung: Konnte Icon nicht laden: {e}")
                icon_widget = self._build_fallback_icon()
        else:
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            if icon_theme and icon_theme.has_icon(self.app_class):
                image = Gtk.Image.new_from_icon_name(self.app_class)
                image.set_pixel_size(icon_size)
                icon_widget = self._wrap_icon_widget(image)
            else:
                icon_widget = self._build_fallback_icon()

        # === BUTTON-GRÖSSE FESTLEGEN ===
        self.set_size_request(icon_size + 4, icon_size + 10)
        self.set_valign(Gtk.Align.FILL)
        self.set_halign(Gtk.Align.CENTER)

        # === INDIKATOR ===
        self.indicator = Gtk.Box()
        self.indicator.add_css_class("indicator")
        self.indicator.set_visible(False)
        self.indicator.set_halign(Gtk.Align.FILL)
        self.indicator.set_valign(Gtk.Align.END)

        # === LAYOUT ===
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_size_request(icon_size + 4, icon_size + 10)
        vbox.append(icon_widget)
        vbox.append(self.indicator)
        self.set_child(vbox)

        # === EVENTS ===
        self.connect("clicked", self.on_left_click)

        self.right_click = Gtk.GestureClick()
        self.right_click.set_button(3)
        self.right_click.connect("released", self.on_right_click)
        self.add_controller(self.right_click)

        drag_source = Gtk.DragSource()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        self.add_controller(drag_source)

        self.icon_widget = icon_widget
        self._build_context_menu()

    def _wrap_icon_widget(self, widget):
        box = Gtk.Box()
        box.set_size_request(self.icon_size, self.icon_size)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)

        widget.set_valign(Gtk.Align.CENTER)
        widget.set_halign(Gtk.Align.CENTER)

        if isinstance(widget, Gtk.Image):
            widget.set_pixel_size(self.icon_size)

        box.append(widget)
        return box

    def _build_fallback_icon(self):
        label_text = self.app_class[:2]
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.CENTER)
        label.set_valign(Gtk.Align.CENTER)
        label.set_xalign(0.5)
        label.set_yalign(0.5)
        label.set_justify(Gtk.Justification.CENTER)
        label.add_css_class("fallback-label")

        box = Gtk.Box()
        box.set_size_request(self.icon_size, self.icon_size)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.append(label)
        return box

    def _build_context_menu(self):
        self.popover = Gtk.Popover.new()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        pin_label = "Entpinnen" if self.pinned else "Pinnen"
        self.pin_menu_item = Gtk.Button(label=pin_label)
        self.pin_menu_item.connect("clicked", self.on_menu_pin_toggled)

        self.close_menu_item = Gtk.Button(label="Beenden")
        self.close_menu_item.connect("clicked", self.on_menu_close)

        menu_box.append(self.pin_menu_item)
        menu_box.append(self.close_menu_item)

        self.popover.set_child(menu_box)
        self.popover.set_parent(self)
        self.popover.set_autohide(True)

    def on_left_click(self, button):
        if self.is_running:
            focus_window_by_class(self.app_class)
        else:
            if self.exec_cmd:
                try:
                    subprocess.Popen(self.exec_cmd.split(),
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                except Exception as e:
                    print(f"Fehler beim Starten von {self.app_class}: {e}")

    def on_right_click(self, gesture, n_press, x, y):
        if self.popover:
            self.popover.set_pointing_to(None)
            self.popover.set_relative_to(self)
            self.popover.popup()

    def on_menu_pin_toggled(self, button):
        from config_loader import config_data
        if self.pinned:
            self.pinned = False
            self.pin_menu_item.set_label("Pinnen")
            config_data["pinned_apps"] = [
                app for app in config_data.get("pinned_apps", [])
                if app.get("class") != self.app_class
            ]
        else:
            self.pinned = True
            self.pin_menu_item.set_label("Entpinnen")
            new_entry = {
                "class": self.app_class,
                "exec": self.exec_cmd or self.app_class,
                "icon": None
            }
            config_data.setdefault("pinned_apps", []).append(new_entry)

    def on_menu_close(self, button):
        close_window_by_class(self.app_class)
        if self.popover:
            self.popover.popdown()

    def set_running(self, running):
        self.is_running = running
        self.indicator.set_visible(running)
        if hasattr(self, "close_menu_item"):
            self.close_menu_item.set_sensitive(running)

    def set_focused(self, focused):
        self.is_focused = focused
        css = self.get_style_context()
        if focused:
            css.add_class("focused")
        else:
            css.remove_class("focused")

    def on_drag_prepare(self, drag_source, x, y):
        val = GObject.Value()
        val.init(GObject.TYPE_STRING)
        val.set_string(self.app_class)
        provider = Gdk.ContentProvider.new_for_value(val)
        return provider
