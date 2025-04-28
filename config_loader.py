import json
import os
import sys

# Globale Konfigurationsdaten
config_data = {}

def load_config(path=None):
    """
    Lädt die Konfigurationsdatei (JSON) und stellt die Daten in config_data bereit.
    Falls kein Pfad angegeben, wird 'config.json' im Modul-Verzeichnis verwendet.
    """
    global config_data
    if path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "config.json")
    try:
        with open(path, 'r') as f:
            config_data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Konfigurationsdatei konnte nicht geladen werden: {e}")
    return config_data

def get_config():
    """
    Gibt die geladene Konfiguration zurück. Lädt sie bei Bedarf nach.
    """
    if not config_data:
        load_config()
    return config_data

def save_config(path=None):
    """
    Speichert die aktuelle config_data zurück in die JSON-Datei.
    """
    global config_data
    if path is None:
        base_dir = os.path.dirname(__file__)
        path = os.path.join(base_dir, "config.json")
    try:
        with open(path, 'w') as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Fehler beim Speichern der Konfigurationsdatei: {e}", file=sys.stderr)

def get_pinned_apps():
    """
    Liefert die Liste der gepinnten App-Klassen (Strings).
    """
    cfg = get_config()
    return cfg.get("pinned_apps", [])

def get_app_overrides():
    """
    Liefert das Dict aller app_overrides, 
    Keys sind App-Klassen, Values sind dicts mit optionalen 'exec' und 'icon'.
    """
    cfg = get_config()
    return cfg.get("app_overrides", {})
