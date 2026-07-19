# Game Machine Smart Features

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

Game Machine includes several helper functions to improve the gaming console experience.

## 1. Game Name Cleaner (Regex)

Raw game ROMs often contain release tags, regional flags, and numbers (e.g. `0517 - Tekken - Dark Resurrection (USA) (En,Fr,De,Es,It).iso`). A regex-based name cleaner filters these details out for the UI representation:

- **Regex used**:
  - `^\d+\s*-\s*`: Removes leading numbers and dashes (e.g. `0517 - `).
  - `[\(\[].*?[\)\]]`: Removes bracketed and parenthesized tags (e.g. `(USA) (En,Fr,De,Es,It)`).
- **Result**: `Tekken - Dark Resurrection` is displayed.

## 2. Dynamic Scrolling List

For directories containing a large list of ROMs (e.g., 100+ files):
- The UI maintains focus on the active selection by scrolling the list view dynamically.
- The UI header displays a counter of total games and current index: `114 games | 37/114`.

## 3. Console Color Tags

To easily distinguish games in mixed lists, each console is assigned a distinct color tag:
- **PSP**: Blue
- **PS2**: Green
- **PS3**: Orange

## 4. Input Queue Purge

When returning from a game session, the event queue is cleared to prevent accidental double-launches caused by buttons pressed while the emulator was running. See [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md) for details.

## 5. Junk File Filtering

Only files matching configuration extensions (e.g. `.iso`, `.cso`, `.chd`) are ingested, filtering out webp, png, and temporary files that may reside in the directories.

## 6. Save-State Launcher Popup

When the user activates a game card, Game Machine looks for an existing save state for that game in the emulator's save-state folder. If one is found, the launch popup expands into a 3-option vertical menu:

- **LOAD LAST SAVE STATE** (accent color, default selection) — boots the game and resumes the newest save state
- **JUST PLAY** — boots the game from cold boot
- **CANCEL** — dismisses the popup

If no save state exists, the popup auto-collapses to the 2-option Just Play / Cancel form (no dead button). Encrypted PS3 games still get the existing DECRYPT GAME? prompt on first launch.

### How It Works
- `core/savestates.py::find_latest_save_state(game, consoles)` parses the game's `PARAM.SFO` (PSP/PS3) or `SYSTEM.CNF` (PS2) to identify the game's serial, then globs the emulator's save-state directory for matching files and returns the newest by mtime.
- `core/launcher.py::_build_command(cfg, game, load_state)` injects the per-emulator CLI flag (`--state=` for PPSSPP, `-statefile` for PCSX2, `--savestate` for RPCS3) when a save state is requested. See [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md) for the full flag reference.
- The popup UI is rendered in `ui/draw_popup.py` and supports keyboard (arrows / Enter / Esc), gamepad (d-pad / A / B), mouse, and touch input.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md)
- [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md)
