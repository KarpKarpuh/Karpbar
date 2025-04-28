import subprocess
import json

def _run_hyprctl_json(command):
    """
    Führt den hyprctl-Befehl mit JSON-Ausgabe aus und gibt das geparste JSON zurück.
    Bei Fehlern wird eine leere Struktur zurückgegeben.
    """
    try:
        result = subprocess.run(["hyprctl", "-j"] + command.split(), capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    # JSON Ausgabe parsen
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = None
    return data

def get_windows():
    """
    Ruft die Liste aller offenen Fenster (Clients) von Hyprland ab.
    Rückgabe: Liste von Dictionaries mit Fensterinformationen.
    """
    data = _run_hyprctl_json("clients")
    if data is None:
        return []
    return data

def get_active_window():
    """
    Ruft das aktuell fokussierte Fenster (active window) von Hyprland ab.
    Rückgabe: Dictionary mit Informationen zum aktiven Fenster oder None.
    """
    data = _run_hyprctl_json("activewindow")
    return data

def focus_window_by_class(class_name):
    """
    Fokussiert ein Fenster anhand des Klassennamens (Application Class) via Hyprland.
    Nutzt hyprctl dispatch focuswindow.
    """
    try:
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"class:{class_name}"], check=True)
    except subprocess.CalledProcessError as e:
        # Fehler ignorieren oder protokollieren
        print(f"Fehler beim Fokussieren von {class_name}: {e}")

import subprocess
import json

def get_windows():
    try:
        result = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, check=True)
        windows = json.loads(result.stdout)
        return windows
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Abrufen der Fensterliste: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Fehler beim Parsen der Fensterliste: {e}")
        return []

def focus_window_by_class(app_class):
    windows = get_windows()
    for window in windows:
        if window.get('class', '').lower() == app_class.lower():
            window_id = window.get('address')
            if window_id:
                subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{window_id}"])
                print(f"[Debug] Fenster fokussiert: {app_class} (ID: {window_id})")
                return
    print(f"[Debug] Kein passendes Fenster zum Fokussieren gefunden für {app_class}.")

def close_window_by_class(app_class):
    windows = get_windows()
    
    print(f"[Debug] Offene Fenster beim Versuch, {app_class} zu schließen:")
    for window in windows:
        print(f" - CLASS: {window.get('class', '')} | TITLE: {window.get('title', '')}")

    for window in windows:
        window_class = window.get('class', '').lower()
        if window_class == app_class.lower():
            window_id = window.get('address')
            if window_id:
                subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{window_id}"])
                print(f"[Debug] Fenster geschlossen: {window_class} (ID: {window_id})")
                return
    print(f"[Debug] Kein passendes Fenster für {app_class} gefunden.")
