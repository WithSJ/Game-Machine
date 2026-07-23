"""
GAME MACHINE - Configuration constants and paths.
Configured for: D:\\Game Machine
  PSP  -> PPSSPP_win + PPSSPP_ios
  PS2  -> PCSX2_win  + PCSX2_ios
  PS3  -> RPCS3_win  + RPCS3_ios
  + any new <NAME>_win + <NAME>_ios folder pair is AUTO-DETECTED!
  Emulators now managed in: emulators/<CONSOLE>_win/
"""
import os
import sys
import json

# Project root directory (where console.py lives)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_playdata_file():
    """Return the playtime.json path in the user-selected root folder (first folder in folders list)."""
    # Load settings to get the first folder
    try:
        if os.path.isfile(os.path.join(PROJECT_DIR, "playtime.json")):
            with open(os.path.join(PROJECT_DIR, "playtime.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                folders = data.get("__settings__", {}).get("folders", [])
                if folders:
                    return os.path.join(folders[0], "playtime.json")
    except (OSError, ValueError):
        pass
    # Fallback to project directory during initial setup
    return os.path.join(PROJECT_DIR, "playtime.json")

def load_settings():
    """Load settings from playtime.json in the user-selected root folder."""
    playdata_file = get_playdata_file()
    try:
        if os.path.isfile(playdata_file):
            with open(playdata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("__settings__", {})
    except (OSError, ValueError):
        pass
    # Fallback: try project directory
    try:
        fallback = os.path.join(PROJECT_DIR, "playtime.json")
        if os.path.isfile(fallback):
            with open(fallback, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("__settings__", {})
    except (OSError, ValueError):
        pass
    return {}

settings = load_settings()
folders = settings.get("folders", [])
custom_consoles = settings.get("custom_consoles", {})
emulators_folder = settings.get("emulators_folder", "")

BASE = folders[0] if folders else r"D:\Game Machine"

# Emulators folder: emulators/<CONSOLE>_win/
def get_emulators_dir():
    """Return the emulators directory under the primary BASE folder."""
    if emulators_folder:
        return emulators_folder
    return os.path.join(BASE, "emulators")

# Cover art: covers\<CONSOLE>\<Clean Game Name>.jpg / .png
def get_covers_dir():
    """Return the covers directory under the currently-configured BASE."""
    return os.path.join(BASE, "covers")

def refresh_paths():
    """Re-resolve BASE/COVERS_DIR/EMULATORS_DIR from the on-disk settings file."""
    global settings, folders, custom_consoles, emulators_folder, BASE
    settings = load_settings()
    folders = settings.get("folders", [])
    custom_consoles = settings.get("custom_consoles", {})
    emulators_folder = settings.get("emulators_folder", "")
    if folders:
        BASE = folders[0]

# Default game extensions for auto-detected consoles
DEFAULT_EXTENSIONS = [".iso", ".cso", ".chd", ".bin"]

# Emulator download URLs (portable Windows 64-bit builds) - Updated 2024
EMULATOR_DOWNLOADS = {
    "PPSSPP": {
        "url": "https://github.com/hrydgard/ppsspp/releases/download/v1.20.4/PPSSPP-v1.20.4-Windows-x64.zip",
        "folder": "PPSSPP_win",
        "exe": "PPSSPPWindows64.exe",
        "version": "1.20.4",
        "github_repo": "hrydgard/ppsspp",
    },
    "PCSX2": {
        "url": "https://github.com/PCSX2/pcsx2/releases/download/v2.6.3/pcsx2-v2.6.3-windows-x64-Qt.7z",
        "folder": "PCSX2_win",
        "exe": "pcsx2-qt.exe",
        "version": "2.6.3",
        "github_repo": "PCSX2/pcsx2",
    },
    "RPCS3": {
        "url": "https://github.com/RPCS3/rpcs3-binaries-win/releases/download/build-7a90d09cfe3c31bf95c3cb63c6301c5c0824c531/rpcs3-v0.0.41-19607-7a90d09c_win64_msvc.7z",
        "folder": "RPCS3_win",
        "exe": "rpcs3.exe",
        "version": "0.0.41-19607",
        "github_repo": "RPCS3/rpcs3-binaries-win",
    },
}

# Auto-start registry key
AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "GameMachine"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "console.py")

