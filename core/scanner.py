"""
GAME MACHINE - Console discovery and game scanning.
"""
import os
import re

from core.config import BASE, CONSOLES, DEFAULT_EXTENSIONS


# ============================================================
# NAME CLEANER - "0517 - Tekken (USA) (v1.01).iso" -> "Tekken"
# ============================================================
def clean_name(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r"^\d+\s*-\s*", "", name)              # strip "0517 - " prefix
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name)  # strip (USA) (v1.01) [b]
    name = name.replace("_", " ")                         # underscores -> spaces
    name = re.sub(r" {2,}", " ", name)                    # collapse multiple spaces
    return name.strip()


# ============================================================
# AUTO-DETECT - the documented "add a new console" formula:
# a <NAME>_win (emulator) + <NAME>_ios (games) folder pair shows
# up in the UI even without adding it to CONFIG.
# ============================================================
def find_emulator_exe(folder):
    """Find the main .exe inside an emulator folder (largest exe wins)."""
    skip_words = ("unins", "setup", "updater", "crash", "install")
    exes = []
    for f in os.listdir(folder):
        low = f.lower()
        if low.endswith(".exe") and not any(w in low for w in skip_words):
            exes.append(os.path.join(folder, f))
    if not exes:
        return None
    return max(exes, key=os.path.getsize)


def discover_consoles():
    """CONFIG consoles + any new _win/_ios pairs found in BASE."""
    consoles = dict(CONSOLES)
    if not os.path.isdir(BASE):
        return consoles

    known_rom_folders = {os.path.normcase(cfg["rom_folder"]) for cfg in consoles.values()}

    for entry in sorted(os.listdir(BASE)):
        if not entry.lower().endswith("_ios"):
            continue
        rom_folder = os.path.join(BASE, entry)
        if not os.path.isdir(rom_folder):
            continue
        if os.path.normcase(rom_folder) in known_rom_folders:
            continue  # already configured (e.g. PPSSPP_ios -> PSP)

        name = entry[: -len("_ios")]
        emu_folder = os.path.join(BASE, name + "_win")
        if not os.path.isdir(emu_folder):
            continue
        exe = find_emulator_exe(emu_folder)
        if not exe:
            continue

        consoles[name.upper()] = {
            "rom_folder": rom_folder,
            "extensions": DEFAULT_EXTENSIONS,
            "emulator": exe,
            "args": [],
        }
    return consoles


# ============================================================
# GAME SCANNING
# ============================================================
def scan_games(consoles):
    games = []
    for console_name, cfg in consoles.items():
        folder = cfg["rom_folder"]
        if not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in cfg["extensions"]:
                games.append({
                    "name": clean_name(filename),
                    "path": os.path.join(folder, filename),
                    "console": console_name,
                })
    return games
