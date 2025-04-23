# ~/Karpbar/taskbar_data.py

from config import PINNED_APPS
from window_manager import get_windows

def generate_taskbar_data():
    windows = get_windows()
    tasks = []

    # Alle Klassen extrahieren (klein geschrieben für Robustheit)
    running_classes = {win["class"].lower() for win in windows}

    print("🧠 Generiere Taskbar-Daten:")
    for entry in PINNED_APPS:
        app_class = entry["name"].lower()
        is_running = app_class in running_classes

        # Ist ein Fenster dieser Klasse fokussiert?
        focused = any(
            win for win in windows
            if win["class"].lower() == app_class and win["focused"]
        )

        task = {
            "name": entry["name"],  # original behalten für Anzeige
            "icon": entry["icon"],
            "exec": entry["exec"],
            "running": is_running,
            "focused": focused
        }

        status = "🟢" if is_running else "⚪"
        star = "⭐" if focused else ""
        print(f"{status} {entry['name']:<10} {star}")

        tasks.append(task)

    return tasks


if __name__ == "__main__":
    from pprint import pprint
    data = generate_taskbar_data()
    print("\n🔽 Taskbar Struktur:")
    pprint(data)
