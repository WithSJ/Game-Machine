# Game Machine Architecture

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

The Game Machine software is an **emulation frontend** written in Python using PyGame. Its main purpose is to coordinate the scanning of game ROMs, display them in a gamepad-navigable fullscreen UI, and launch the correct emulator smoothly.

## Main Execution Flow

The entry point of the application is [console.py](file:///c:/Users/jadam/Desktop/Game-Machine/console.py), which runs the main loop defined in [app.py](file:///c:/Users/jadam/Desktop/Game-Machine/app.py).

```
python console.py
        │
        ▼
┌───────────────────┐
│  1. SCAN GAMES    │  Scans each console's game folders,
│  scan_games()     │  filters by extension, cleans names using regex.
└────────┬──────────┘
         ▼
┌───────────────────┐
│  2. UI LOOP       │  Draws 1280x720 window, handles dark theme,
│  main()           │  manages scrolling lists, gamepad/keyboard input.
└────────┬──────────┘
         ▼ (Enter / A button)
┌───────────────────┐
│  3. LAUNCH        │  Runs subprocess.run() to launch the emulator,
│  launch_game()    │  freezes frontend, waits for emulator exit,
│                   │  clears stale input events, resumes UI.
└────────┬──────────┘
         └──────────→ (loop continues)
```

## Console Configurations (`CONSOLES`)

The system configuration is defined in `core/config.py` as a dictionary of console configurations:

```python
CONSOLES = {
    "PSP": {
        "rom_folder": r"D:\Game Machine\PPSSPP_ios",
        "extensions": [".iso", ".cso"],
        "emulator":   r"D:\Game Machine\PPSSPP_win\PPSSPPWindows64.exe",
        "args":       ["--fullscreen"],
    },
    "PS2": {
        "rom_folder": r"D:\Game Machine\PCSX2_ios",
        "extensions": [".iso", ".chd"],
        "emulator":   r"D:\Game Machine\PCSX2_win\pcsx2-qt.exe",
        "args":       ["-fullscreen", "-batch"],
    },
    "PS3": {
        "rom_folder": r"D:\Game Machine\RPCS3_ios",
        "extensions": [".iso"],
        "emulator":   r"D:\Game Machine\RPCS3_win\rpcs3.exe",
        "args":       ["--no-gui"],
    },
}
```

Adding a new console is as simple as defining a new key-value block in this dictionary. This isolates data/configuration from logical execution code.

## Related Pages
- [File Structure](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/file_structure.md)
- [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
- [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md)
- [Roadmap](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/roadmap.md)
