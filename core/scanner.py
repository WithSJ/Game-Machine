"""
GAME MACHINE - Console discovery and game scanning.
"""
import os
import re

from core.config import BASE, DEFAULT_EXTENSIONS


# ============================================================
# NAME CLEANER - "0517 - Tekken (USA) (v1.01).iso" -> "Tekken"
# ============================================================
def clean_name(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r"^\d+\s*-\s*", "", name)              # strip "0517 - " prefix
    # Strip bracketed/parenthesized tags, including nested ones. A single
    # non-nested pattern can't handle "Game (USA (En,Fr,De))" because the
    # innermost ")" closes before the outer group is seen, leaving a dangling
    # "(USA " behind. We therefore strip the innermost pair each pass and
    # repeat until the name stops changing. The pattern allows nested
    # brackets inside the content so a whole "(USA (En,Fr,De))" group is
    # consumed in one go once its inner pairs are gone.
    bracket_re = re.compile(r"\s*[\(\[][^\(\)\[\]]*[\)\]]")
    prev = None
    while prev != name:
        prev = name
        # First peel any fully-inner pairs, then the outer wrapper.
        name = re.sub(r"\(([^\(\)]*)\)", "", name)
        name = re.sub(r"\[([^\[\]]*)\]", "", name)
        name = bracket_re.sub("", name)
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


def discover_consoles(folders=None, custom_consoles=None):
    """Scan all folders for standard consoles and custom consoles, plus _win/_ios pairs."""
    if folders is None:
        from core.config import folders as config_folders
        folders = list(config_folders)
    if not folders:
        from core.config import BASE
        folders = [BASE]
    if custom_consoles is None:
        from core.config import custom_consoles as config_customs
        custom_consoles = config_customs

    # Standard/default consoles setup definition
    default_consoles = {
        "PSP": {
            "rom_sub": "PPSSPP_ios",
            "extensions": [".iso", ".cso"],
            "emu_sub": os.path.join("PPSSPP_win", "PPSSPPWindows64.exe"),
            "args": ["--fullscreen"],
        },
        "PS2": {
            "rom_sub": "PCSX2_ios",
            "extensions": [".iso", ".chd"],
            "emu_sub": os.path.join("PCSX2_win", "pcsx2-qt.exe"),
            "args": ["-fullscreen", "-batch"],
        },
        "PS3": {
            "rom_sub": "RPCS3_ios",
            "extensions": [".iso"],
            "emu_sub": os.path.join("RPCS3_win", "rpcs3.exe"),
            "args": ["--no-gui"],
        },
    }

    consoles = {}
    
    # 1. Resolve standard/default consoles across configured folders
    for name, info in default_consoles.items():
        for folder in folders:
            rom_folder = os.path.join(folder, info["rom_sub"])
            emulator = os.path.join(folder, info["emu_sub"])
            if os.path.isdir(rom_folder) and os.path.isfile(emulator):
                consoles[name] = {
                    "rom_folder": rom_folder,
                    "extensions": info["extensions"],
                    "emulator": emulator,
                    "args": info["args"],
                }
                break # First match wins

    # 2. Add custom consoles configured via Setup Wizard
    if custom_consoles:
        for name, info in custom_consoles.items():
            consoles[name] = info

    # 3. Auto-detect any other `<NAME>_win` + `<NAME>_ios` folder pairs
    known_rom_folders = {os.path.normcase(cfg["rom_folder"]) for cfg in consoles.values()}
    for base in folders:
        if not os.path.isdir(base):
            continue
        try:
            for entry in sorted(os.listdir(base)):
                if not entry.lower().endswith("_ios"):
                    continue
                rom_folder = os.path.join(base, entry)
                if not os.path.isdir(rom_folder):
                    continue
                if os.path.normcase(rom_folder) in known_rom_folders:
                    continue

                name = entry[: -len("_ios")]
                emu_folder = os.path.join(base, name + "_win")
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
        except OSError:
            pass

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
