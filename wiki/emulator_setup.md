# Emulator Setup & Command Reference

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

Each console emulator is launched programmatically via Pygame using `subprocess.run()`. Crucial flags are passed to make the transitions seamless and headless.

## Commands Configuration

| Console | Launch Command | Flag Explanations |
|---------|---------------|-------------------|
| **PSP** (PPSSPP) | `PPSSPPWindows64.exe --fullscreen "game.iso"` | `--fullscreen` runs the emulator in fullscreen immediately. |
| **PS2** (PCSX2) | `pcsx2-qt.exe -fullscreen -batch "game.iso"` | `-fullscreen` starts the UI in fullscreen mode.<br>`-batch` automatically exits the PCSX2 backend process when the game window is closed, returning focus to Game Machine. |
| **PS3** (RPCS3) | `rpcs3.exe --no-gui "game.iso"` | `--no-gui` boots the game immediately and bypasses RPCS3's main game manager interface. |

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
