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

def close_window_by_class(class_name):
    """
    Schließt alle Fenster einer Anwendung anhand des Klassennamens via Hyprland.
    Nutzt hyprctl dispatch closewindow mit Regex für exakten Klassenmatch.
    Hinweis: Schließt ggf. mehrere Fenster der gleichen Klasse nacheinander.
    """
    # Regex ^class_name$ um exakten Match zu erzwingen (Hyprland interpretiert closewindow-Argument als Regex)
    target = f"^{class_name}$"
    try:
        # Möglicherweise muss dieser Befehl mehrfach ausgeführt werden, um mehrere Fenster zu schließen.
        subprocess.run(["hyprctl", "dispatch", "closewindow", target], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Schließen von Fenstern der Klasse {class_name}: {e}")
