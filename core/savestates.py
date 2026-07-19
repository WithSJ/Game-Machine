"""
GAME MACHINE - Save-state discovery for emulators.

Finds the most recently-modified save state file for a given game across
PPSSPP (PSP), PCSX2 (PS2), and RPCS3 (PS3) by scanning each emulator's
save-state directory.

Per-emulator rules (verified against each emulator's source on GitHub):

  PPSSPP  -> CLI flag: --state=<path>     files: <DISC_ID>_<DISC_VER>_<slot>.ppst
  PCSX2   -> CLI flag: -statefile <path>  files: <serial> (<CRC>).<NN>.p2s
                                                <serial> (<CRC>).resume.p2s
  RPCS3   -> CLI flag: --savestate <path> files: <config_dir>/savestates/<TitleID>/*.SAVESTAT
"""
import glob
import os

from covers.iso_parser import get_psp_disc_id, get_ps3_title_id
from covers.ps2_serial import get_ps2_serial


# ------------------------------------------------------------
# Per-emulator save-state directory candidates.
# We always try the portable location (next to the emulator's exe)
# first because Game Machine ships emulators in portable folders;
# then fall back to the user's home Documents/AppData path.
# ------------------------------------------------------------
def _ppsspp_state_dirs(console_cfg):
    emu_dir = os.path.dirname(console_cfg["emulator"])
    candidates = [
        os.path.join(emu_dir, "memstick", "PSP", "PPSSPP_STATE"),
        os.path.join(emu_dir, "PSP", "PPSSPP_STATE"),
    ]
    home = os.path.expanduser("~")
    if home:
        candidates.append(os.path.join(home, "Documents", "PPSSPP", "PSP", "PPSSPP_STATE"))
    return candidates


def _pcsx2_state_dirs(console_cfg):
    emu_dir = os.path.dirname(console_cfg["emulator"])
    candidates = [
        os.path.join(emu_dir, "sstates"),
        os.path.join(emu_dir, "inis", "sstates"),
    ]
    home = os.path.expanduser("~")
    if home:
        candidates.append(os.path.join(home, "Documents", "PCSX2", "sstates"))
    return candidates


def _rpcs3_state_dirs(console_cfg, title_id):
    if not title_id:
        return []
    emu_dir = os.path.dirname(console_cfg["emulator"])
    candidates = [
        os.path.join(emu_dir, "portable", "savestates", title_id),
        os.path.join(emu_dir, "savestates", title_id),
    ]
    env = os.environ.get("RPCS3_CONFIG_DIR")
    if env:
        candidates.append(os.path.join(env, "savestates", title_id))
    home = os.path.expanduser("~")
    if home:
        candidates.append(os.path.join(home, "AppData", "Local", "rpcs3", "savestates", title_id))
    return candidates


def _newest(paths):
    """Return the path with the newest mtime from a list, or None if empty."""
    best = None
    best_mtime = -1.0
    for p in paths:
        try:
            m = os.path.getmtime(p)
            if m > best_mtime:
                best_mtime = m
                best = p
        except OSError:
            continue
    return best


def find_latest_save_state(game, consoles):
    """Find the newest save state file for the given game.

    Returns an absolute path string, or None if no save state exists
    (or the game's console is unsupported / its serial can't be parsed).
    """
    console_name = game.get("console")
    if console_name not in consoles:
        return None
    cfg = consoles[console_name]

    if console_name == "PSP":
        disc_id, disc_ver = get_psp_disc_id(game["path"])
        if not disc_id:
            return None
        prefix = f"{disc_id}_{disc_ver}_" if disc_ver else f"{disc_id}_"
        results = []
        for d in _ppsspp_state_dirs(cfg):
            if os.path.isdir(d):
                results.extend(glob.glob(os.path.join(d, prefix + "*.ppst")))
        return _newest(results)

    if console_name == "PS2":
        serial = get_ps2_serial(game["path"])
        if not serial:
            return None
        results = []
        for d in _pcsx2_state_dirs(cfg):
            if os.path.isdir(d):
                # PCSX2 filename pattern: "<serial> (<CRC>).<NN>.p2s"
                # and "<serial> (<CRC>).resume.p2s". The serial is the
                # hyphenated form (e.g. "SLUS-21134"); the "(" right after
                # the serial space is unique enough to scope this game's
                # state files.
                results.extend(glob.glob(os.path.join(d, f"{serial} (*.p2s")))
                results.extend(glob.glob(os.path.join(d, f"{serial} (*.p2s.backup")))
        return _newest(results)

    if console_name == "PS3":
        title_id = get_ps3_title_id(game["path"])
        if not title_id:
            return None
        results = []
        for d in _rpcs3_state_dirs(cfg, title_id):
            if os.path.isdir(d):
                for ext in ("*.SAVESTAT", "*.SAVESTAT.zst", "*.SAVESTAT.gz"):
                    results.extend(glob.glob(os.path.join(d, ext)))
        return _newest(results)

    return None
