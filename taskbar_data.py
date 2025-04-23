#!/usr/bin/env python3
from config import PINNED_APPS, APP_CONFIG
from window_manager import get_windows


def generate_taskbar_data():
    """
    Erstellt eine Liste von Tasks für die gepinnten Apps:
    - name: App-Name
    - icon: Pfad (oder leer)
    - exec: Befehl zum Starten
    - running: bool
    - focused: bool
    """
    windows = get_windows()
    running_classes = {w["class"].lower() for w in windows}

    tasks = []
    for name in PINNED_APPS:
        lower = name.lower()
        cfg = APP_CONFIG.get(lower, {})
        icon = cfg.get("icon", "")
        exec_cmd = cfg.get("exec", lower)

        is_running = lower in running_classes
        focused = any(
            w for w in windows
            if w["class"].lower() == lower and w["focused"]
        )

        tasks.append({
            "name": name,
            "icon": icon,
            "exec": exec_cmd,
            "running": is_running,
            "focused": focused
        })

    return tasks


if __name__ == '__main__':
    from pprint import pprint
    data = generate_taskbar_data()
    print("🔽 Taskbar Struktur:")
    pprint(data)
