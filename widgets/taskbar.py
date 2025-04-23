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
        # Konfiguration speichern
        self.config = config
        # Alle App-Buttons in einem Dictionary nach Klassenname
        self.buttons_map = {}
        # Container für App-Buttons (horizontale Box, zentriert)
        self.tasks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        # Drag-and-Drop DropTarget auf die Task-Liste (für zukünftiges Reordering oder Pinnen per Drag)
        drop_target = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
        self.tasks_box.add_controller(drop_target)
        # Power-Button erstellen (rechts außen)
        power_icon = Gtk.Image.new_from_icon_name("system-shutdown")
        power_icon.set_pixel_size(config.get("icon_size", 32))
        power_button = Gtk.Button()
        power_button.set_child(power_icon)
        power_button.add_css_class("power-button")
        power_button.connect("clicked", self.on_power_clicked)
        # Hauptcontainer als CenterBox, um App-Buttons zentriert und Power-Button rechts zu platzieren
        self.container = Gtk.CenterBox()
        self.container.set_start_widget(None)
        self.container.set_center_widget(self.tasks_box)
        self.container.set_end_widget(power_button)
        self.container.add_css_class("taskbar")
        # Das Widget, das von außen in das Fenster eingefügt wird
        self.widget = self.container
        # Gepinnte Apps aus der Konfig initial hinzufügen
        pinned_apps = config.get("pinned_apps", [])
        for app in pinned_apps:
            app_class = app.get("class")
            exec_cmd = app.get("exec")
            icon_path = app.get("icon")
            # AppButton erzeugen (gepinned)
            btn = AppButton(app_class, icon_path=icon_path, exec_cmd=exec_cmd, pinned=True, icon_size=config.get("icon_size", 32))
            # Größe des Buttons gemäß Konfig setzen
            btn.set_size_request(config.get("button_width", 40), config.get("button_height", 40))
            # Indikator-Höhe setzen
            btn.indicator.set_size_request(-1, config.get("indicator_height", 2))
            # "Beenden" im Kontextmenü initial deaktivieren (App startet evtl. später)
            btn.close_menu_item.set_sensitive(False)
            self.tasks_box.append(btn)
            self.buttons_map[app_class] = btn
        # Status der letzten bekannten offenen Fenster und Fokus (für Change-Detection)
        self.last_open_classes = set()
        self.current_active_class = None
        # Einmal initial aktuellen Stand abrufen und UI anpassen
        self.refresh(initial=True)
        # Periodischen Refresh einrichten
        GLib.timeout_add(500, self.refresh)

    def refresh(self, initial=False):
        """
        Aktualisiert die Taskbar: offene Fenster ermitteln, neue App-Buttons ggf. hinzufügen,
        geschlossene Anwendungen entfernen, Fokus-Hervorhebung aktualisieren.
        """
        # Aktives Fenster und alle Fenster von Hyprland abfragen
        active_info = get_active_window()
        active_class = None
        if active_info and isinstance(active_info, dict):
            active_class = active_info.get("class")
        windows = get_windows()
        # Alle offenen Fenster gruppiert nach Klassenname sammeln
        open_classes = {}
        for win in windows:
            if win.get("class"):
                cls = win["class"]
                open_classes.setdefault(cls, []).append(win)
        # Falls nicht initialer Aufruf: prüfen, ob Änderungen vorliegen
        if not initial:
            current_open_set = set(open_classes.keys())
            if active_class == self.current_active_class and current_open_set == self.last_open_classes:
                # Keine Änderung in geöffneten Apps oder Fokus -> nichts aktualisieren
                return True
        # Update Merker für offene Klassen und aktive Klasse
        current_open_set = set(open_classes.keys())
        self.last_open_classes = current_open_set
        self.current_active_class = active_class
        # App-Buttons für alle offenen Klassen aktualisieren oder erzeugen
        for cls, wins in open_classes.items():
            if cls in self.buttons_map:
                # Button existiert bereits (falls gepinnt)
                btn = self.buttons_map[cls]
                btn.set_running(True)
            else:
                # Neue (nicht gepinnte) App: Button hinzufügen
                btn = AppButton(cls, icon_path=None, exec_cmd=cls, pinned=False, icon_size=self.config.get("icon_size", 32))
                btn.set_size_request(self.config.get("button_width", 40), self.config.get("button_height", 40))
                btn.indicator.set_size_request(-1, self.config.get("indicator_height", 2))
                btn.set_running(True)
                # "Beenden" im Menü aktivieren, da läuft
                btn.close_menu_item.set_sensitive(True)
                self.tasks_box.append(btn)
                self.buttons_map[cls] = btn
        # Nicht mehr offene (geschlossene) Apps entfernen, wenn sie nicht gepinnt sind
        # (Gepinnte bleiben als Icon sichtbar, werden aber als "nicht laufend" markiert)
        for cls in list(self.buttons_map.keys()):
            btn = self.buttons_map[cls]
            if not btn.pinned and cls not in open_classes:
                # Entfernen aus UI und Map
                self.tasks_box.remove(btn)
                del self.buttons_map[cls]
        # Laufstatus für verbleibende Buttons anpassen (Indikator ein/aus)
        for cls, btn in self.buttons_map.items():
            btn.set_running(cls in open_classes)
        # Fokus-Hervorhebung aktualisieren: alle Buttons entsprechend active_class markieren
        for cls, btn in self.buttons_map.items():
            btn.set_focused(cls == active_class and active_class is not None)
        return True

    def on_drop(self, drop_target, value, x, y):
        """Wird aufgerufen, wenn ein AppButton per Drag auf die Taskbar fallen gelassen wird."""
        class_name = value
        if isinstance(value, GObject.Value):
            class_name = value.get_string()
        print(f"Drag-and-Drop: {class_name} wurde auf Taskleiste fallen gelassen (Reihenfolgeänderung nicht implementiert).")
        # Hier könnte man die Reihenfolge der Buttons anpassen oder App pinnen/entpinnen.
        return True

    def on_power_clicked(self, button):
        print("Karpbar wird geschlossen.")
        app = Gtk.Application.get_default()
        if app:
            app.quit()