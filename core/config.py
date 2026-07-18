"""
GAME MACHINE - Configuration constants and paths.
Configured for: D:\\Game Machine
  PSP  -> PPSSPP_win + PPSSPP_ios
  PS2  -> PCSX2_win  + PCSX2_ios
  PS3  -> RPCS3_win  + RPCS3_ios
  + any new <NAME>_win + <NAME>_ios folder pair is AUTO-DETECTED!
"""
import os
import sys
import json

# Project root directory (where console.py lives)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Play-time database lives next to console.py (portable, travels with the folder)
PLAYDATA_FILE = os.path.join(PROJECT_DIR, "playtime.json")

def load_settings():
    try:
        if os.path.isfile(PLAYDATA_FILE):
            with open(PLAYDATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("__settings__", {})
    except (OSError, ValueError):
        pass
    return {}

settings = load_settings()
folders = settings.get("folders", [])
custom_consoles = settings.get("custom_consoles", {})

BASE = folders[0] if folders else r"D:\Game Machine"

# ============================================================
# CONFIG - your real paths (taken from the dir /s output)
# ============================================================
CONSOLES = {
    "PSP": {
        "rom_folder": os.path.join(BASE, "PPSSPP_ios"),
        "extensions": [".iso", ".cso"],
        "emulator": os.path.join(BASE, "PPSSPP_win", "PPSSPPWindows64.exe"),
        "args": ["--fullscreen"],
    },
    "PS2": {
        "rom_folder": os.path.join(BASE, "PCSX2_ios"),
        "extensions": [".iso", ".chd"],
        "emulator": os.path.join(BASE, "PCSX2_win", "pcsx2-qt.exe"),
        # -batch = when the game closes, PCSX2 closes too (straight back here)
        "args": ["-fullscreen", "-batch"],
    },
    "PS3": {
        "rom_folder": os.path.join(BASE, "RPCS3_ios"),
        "extensions": [".iso"],
        "emulator": os.path.join(BASE, "RPCS3_win", "rpcs3.exe"),
        # --no-gui = skip the RPCS3 main window, boot the game directly
        "args": ["--no-gui"],
    },
}

# Default game extensions for auto-detected consoles
DEFAULT_EXTENSIONS = [".iso", ".cso", ".chd", ".bin"]

# Cover art: covers\<CONSOLE>\<Clean Game Name>.jpg / .png
# Set covers directory inside the primary Game Machine folder (BASE)
COVERS_DIR = os.path.join(BASE, "covers")

# Auto-start registry key
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "GameMachine"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "console.py")

