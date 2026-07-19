# Emulator Setup & Command Reference

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

Each console emulator is launched programmatically via Pygame using `subprocess.run()`. Crucial flags are passed to make the transitions seamless and headless.

## Commands Configuration

| Console | Launch Command | Flag Explanations |
|---------|---------------|-------------------|
| **PSP** (PPSSPP) | `PPSSPPWindows64.exe --fullscreen "game.iso"` | `--fullscreen` runs the emulator in fullscreen immediately. |
| **PS2** (PCSX2) | `pcsx2-qt.exe -fullscreen -batch "game.iso"` | `-fullscreen` starts the UI in fullscreen mode.<br>`-batch` automatically exits the PCSX2 backend process when the game window is closed, returning focus to Game Machine. |
| **PS3** (RPCS3) | `rpcs3.exe --no-gui "game.iso"` | `--no-gui` boots the game immediately and bypasses RPCS3's main game manager interface. |

## Save-State Launch Commands

When the user picks "Load Last Save State" from the launch popup, Game Machine injects an extra CLI flag so the emulator resumes the latest save state for that game. The exact flag and game-path convention differ per emulator (verified against each emulator's source on GitHub):

| Console | Save-State Flag | Game ISO Still Passed? | Example |
|---------|----------------|------------------------|---------|
| **PSP** (PPSSPP) | `--state=<path>` (double-dash, `=`, no space) | Yes | `PPSSPPWindows64.exe --fullscreen --state="…\PPSSPP_STATE\ULUS12345_1.00_1.ppst" "game.iso"` |
| **PS2** (PCSX2) | `-statefile <path>` (single-dash, space) | Yes | `pcsx2-qt.exe -fullscreen -batch -statefile "…\sstates\SLUS-21134 (ABCD1234).01.p2s" "game.iso"` |
| **PS3** (RPCS3) | `--savestate <path>` (double-dash, space) | **No** — savestate only | `rpcs3.exe --no-gui --fullscreen --savestate "…\savestates\BLUS30450\BLUS30450_0_1.SAVESTAT"` |

### Save-State File Locations

Discovery (`core/savestates.py`) globs each emulator's save-state directory and picks the newest match by mtime. The portable folder (next to the emulator's `.exe`) is checked first, with a fallback to the user's `Documents` / `AppData` default.

| Console | Default Folder (portable) | Filename Pattern | Keyed By |
|---------|--------------------------|------------------|----------|
| **PSP**  | `<PPSSPP_win>/memstick/PSP/PPSSPP_STATE/` | `<DISC_ID>_<DISC_VER>_<slot>.ppst` | PSP `DISC_ID` + `DISC_VERSION` (from `PSP_GAME/PARAM.SFO`) |
| **PS2**  | `<PCSX2_win>/sstates/` | `<serial> (<CRC>).<NN>.p2s` (also `.resume.p2s`) | PS2 serial (from `SYSTEM.CNF`) + ELF CRC |
| **PS3**  | `<RPCS3_win>/savestates/<TitleID>/` | `<title>_<prefix>_<id>.SAVESTAT` (+ `.zst` / `.gz`) | PS3 `TITLE_ID` (from `PS3_GAME/PARAM.SFO`) |

### Notes & Gotchas

- **RPCS3 `--fullscreen` requires `--no-gui`** — Game Machine already passes `--no-gui` by default, so this is satisfied. RPCS3 will fatally error if `--fullscreen` is used without `--no-gui`.
- **RPCS3 savestates are self-contained** — the savestate file embeds the disc path and title ID, so the game ISO must NOT be passed alongside `--savestate`. Game Machine's `_build_command` handles this per-emulator.
- **PPSSPP `--state=` is undocumented** on the official command-line page but is parsed in `UI/NativeApp.cpp:641` and `headless/Headless.cpp:442`. Treat it as a stable internal flag.
- **Save-state version drift** — across emulator updates, older save states may fail to load (RPCS3 is the strictest). Game Machine verifies `os.path.isfile()` before launching and silently falls back to "Just Play" if the file has been removed since the popup was shown.
- For games with **no save state yet**, the launch popup auto-collapses to the 2-option YES/NO form (Just Play / Cancel) — see [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md).

## Portability & Working Directories (`cwd`)

To preserve portable configurations, emulators must be launched with their respective working directories set to their installation folder (e.g., using `cwd` argument in `subprocess.Popen` or `subprocess.run`). This ensures they find local BIOS files, memory cards, and shader caches in their own subdirectories rather than searching in default locations inside `C:\Users\<username>\AppData`.

## Troubleshooting

- **No games detected**: Check `rom_folder` paths in `core/config.py`.
- **Game fails to start**: Test the launch command manually in `Win+R` using absolute paths.
- **PS2 BIOS Error**: Verify that the BIOS bin files exist under `PCSX2_win\bios\` and that they are selected in the PCSX2 settings.
- **PS3 Fullscreen**: Verify "Start games in fullscreen mode" is enabled inside RPCS3 settings.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [File Structure](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/file_structure.md)
