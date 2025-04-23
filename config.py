# config.py

# Liste aller gepinnten Apps (nur Namen)
PINNED_APPS = [
    "kitty",
    "firefox",
    "code-oss",
]

# Globale Overrides für **beliebige** Apps (nicht nur gepinnt)
# key = app-Name (window class), value = Dict mit optionalen Icon- und Exec-Overrides
APP_CONFIG = {
    "code-oss": {
        "icon": "/usr/share/pixmaps/com.visualstudio.code.oss.png",
        "exec": "code",
    },
}
