# ~/Karpbar/window_manager.py

import subprocess
import json

def get_windows():
    try:
        result = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True)
        clients = json.loads(result.stdout)
    except Exception as e:
        print(f"[window_manager] Fehler beim Abrufen: {e}")
        return []

    windows = []
    for c in clients:
        windows.append({
            "class": c.get("class", "").lower(),
            "title": c.get("title", ""),
            "workspace": c.get("workspace", {}).get("id", -1),
            "address": c.get("address", ""),
            "focused": c.get("focused", False)
        })

    return windows
