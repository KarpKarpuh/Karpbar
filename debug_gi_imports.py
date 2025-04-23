import sys
import gi
import os

# Bereits geladene gi-Module anzeigen
print(">>> Bereits geladene gi-Module:")
for mod in sys.modules:
    if "gi.repository" in mod:
        print(" -", mod)

# GI_TYPELIB_PATH prüfen
print("\n>>> GI_TYPELIB_PATH:", os.environ.get("GI_TYPELIB_PATH", "<nicht gesetzt>"))

# sys.path prüfen
print("\n>>> sys.path:")
for p in sys.path:
    print("   ", p)
