# config_loader.py

import json
import os

config_data = {}  # Globale Konfigurationsdaten

def load_config(path=None):
    """
    Lädt die Konfigurationsdatei (JSON) und stellt die Daten in config_data bereit.
    Falls kein Pfad angegeben, wird 'config.json' im gleichen Verzeichnis verwendet.
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
    Gibt die geladene Konfiguration zurück. Stellt sicher, dass zuvor load_config() aufgerufen wurde.
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
