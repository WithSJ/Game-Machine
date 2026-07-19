"""
GAME MACHINE - Game launching and process management.
"""
import ctypes
import ctypes.wintypes
import os
import subprocess
import threading
import time

import pygame


def _ppsspp_menu_monitor(proc):
    """Background watcher: auto-close PPSSPP when the game exits to menu.

    While a game is running the window title looks like:
        "PPSSPP v1.x.x - Game Title"       (contains " - ")
    When the user picks 'Exit to Menu' from the pause menu:
        "PPSSPP v1.x.x"                    (no " - ")
    We detect that transition and terminate the process so control
    returns straight to Game Machine.
    """
    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
    )

    time.sleep(3)  # give PPSSPP time to boot the game

    game_seen = False

    while proc.poll() is None:
        titles = []

        def _cb(hwnd, _lp):
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value != proc.pid:
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                titles.append(buf.value)
            return True

        try:
            user32.EnumWindows(WNDENUMPROC(_cb), 0)
        except OSError:
            pass

        game_running = any(" - " in t for t in titles)

        if game_running:
            game_seen = True
        elif game_seen and titles:
            # Game was running, now at menu -> close PPSSPP
            proc.terminate()
            break

        time.sleep(0.5)


def _build_command(cfg, game, load_state=None):
    """Build the emulator launch command for a game.

    When load_state is None, the emulator boots the game normally.
    When load_state is an absolute path to a save-state file, the
    emulator loads that state right after booting.

    Per-emulator save-state flags (verified against each emulator's source):

      PPSSPP  ->  --state=<path>    (game ISO still passed; state loads after boot)
      PCSX2   ->  -statefile <path> (game ISO still passed; state loads after boot)
      RPCS3   ->  --savestate <path> (NO game ISO; savestate embeds everything)

    Returns the argv list to Popen, or None if a save state was requested
    but the file no longer exists (caller should fall back to Just Play).
    """
    base_args = list(cfg["args"])

    if load_state is not None:
        if not os.path.isfile(load_state):
            return None
        console = game["console"]
        if console == "PSP":
            # PPSSPP: --state=<path> (double-dash with =), then the game ISO
            base_args.append(f"--state={load_state}")
            base_args.append(game["path"])
        elif console == "PS2":
            # PCSX2: -statefile <path> (single-dash with space), then the game ISO
            base_args.append("-statefile")
            base_args.append(load_state)
            base_args.append(game["path"])
        elif console == "PS3":
            # RPCS3: --savestate <path> ONLY (no game ISO). --fullscreen
            # requires --no-gui, which we already pass by default.
            base_args = ["--no-gui", "--fullscreen", "--savestate", load_state]
        else:
            # Unknown console - can't apply a save state; boot normally.
            base_args.append(game["path"])
    else:
        base_args.append(game["path"])

    return [cfg["emulator"]] + base_args


def launch_game(game, consoles, load_state=None):
    cfg = consoles[game["console"]]
    command = _build_command(cfg, game, load_state)
    if command is None:
        # Requested save state vanished between popup and launch - fall back
        # to a normal boot so the user still gets to play.
        command = [cfg["emulator"]] + list(cfg["args"]) + [game["path"]]
    start = time.time()
    # cwd = the emulator's own folder so portable mode works correctly
    proc = subprocess.Popen(
        command,
        cwd=os.path.dirname(cfg["emulator"]),
        creationflags=subprocess.DETACHED_PROCESS,
    )

    # Auto-close PPSSPP when game exits to its menu (pause menu still works)
    if game["console"] == "PSP":
        threading.Thread(
            target=_ppsspp_menu_monitor, args=(proc,), daemon=True
        ).start()

    proc.wait()
    elapsed = int(time.time() - start)
    # BUG FIX: buttons pressed while the game was running pile up in our
    # event queue - the stale "A press" used to relaunch the same game
    # the moment we came back. Flush everything:
    pygame.time.wait(500)      # let the emulator shut down completely
    pygame.event.pump()        # process OS events into Pygame's queue so they can be cleared
    pygame.event.clear()       # drop all stale input events
    return elapsed
