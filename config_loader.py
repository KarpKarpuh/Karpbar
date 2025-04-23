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
        # Standardpfad relative zum Modul
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
        # Falls noch nicht geladen, automatisch laden (Standardpfad)
        load_config()
    return config_data
