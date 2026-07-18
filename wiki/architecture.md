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
│  1. CHECK CONFIG  │  Reads playtime.json settings.
│  needs_setup?     │  If empty, starts Setup Wizard.
└────────┬──────────┘
         │
         ├─── (Yes) ───►  [ SETUP WIZARD ]
         │                Configure Game Machine folders / Custom Consoles.
         │                Saves settings and transitions to scan.
         │                       │
         └─── (No) ◄─────────────┘
         ▼
┌───────────────────┐
│  2. SCAN GAMES    │  Scans each console's game folders,
│  scan_games()     │  filters by extension, cleans names using regex.
└───────────────────┘
         ▼
┌───────────────────┐
│  3. UI LOOP       │  Draws 1280x720 window, handles dark theme,
│  main()           │  manages scrolling lists, gamepad/keyboard input.
└────────┬──────────┘
         ▼ (Enter / A button)
┌───────────────────┐
│  4. LAUNCH        │  Runs subprocess.run() to launch the emulator,
│  launch_game()    │  freezes frontend, waits for emulator exit,
│                   │  clears stale input events, resumes UI.
└────────┬──────────┘
         └──────────→ (loop continues)
```

## Dynamic Console Configurations (`CONSOLES`)

Rather than being hardcoded to a single `BASE` path (like `D:\Game Machine`), console configurations are now dynamically computed by `discover_consoles(folders, custom_consoles)`:

1. **Configured Folders**: A list of base directories is loaded from settings in `playtime.json` under `"__settings__": {"folders": [...]}`.
2. **Path Resolution**: The standard configurations (`PSP`, `PS2`, `PS3`) search across the list of folders. The first folder containing both the corresponding ROM folder and the emulator executable is selected.
3. **Custom Consoles**: Custom console mappings can be added using the Setup Wizard (which saves them to `"custom_consoles"` in settings).
4. **Auto-Discovery**: Any directory pair ending in `_win` and `_ios` under the configured folders is auto-detected.

This isolates logical execution from data while ensuring complete portability across folders and drives.

## Related Pages
- [File Structure](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/file_structure.md)
- [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
- [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md)
- [Roadmap](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/roadmap.md)
