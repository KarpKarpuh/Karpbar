#!/bin/bash
# Startet Karpbar korrekt mit GTK4 Layer Shell Unterstützung

export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
exec python /home/Karpuh/Karpbar/main.py
