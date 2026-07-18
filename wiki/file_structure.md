# Game Machine Folder Structure

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

The Game Machine workspace layout is structured to be completely **portable**. All settings, configurations, emulators, and game ROMs are stored within the root folder, meaning the entire directory can be copied to another drive or machine and run immediately.

## Directory Layout

```
D:\Game Machine\
│
├── console.py                   ← Launcher entry point
├── app.py                       ← Main execution controller
├── core\                        ← Core business logic (scanner, launcher, decrypter)
├── ui\                          ← Pygame-based UI rendering files
├── covers\                      ← Cover art cache
│
├── PPSSPP_win\                  ← PSP Emulator binaries & settings
│   └── memstick\                ← PPSSPP save states, savedata, system settings
├── PPSSPP_ios\                  ← PSP Game ROMs (.iso, .cso)
│
├── PCSX2_win\                   ← PS2 Emulator binaries & settings
│   ├── portable\                ← Empty file/directory to enable PCSX2 portable mode
│   └── bios\                    ← PS2 BIOS files (required)
├── PCSX2_ios\                   ← PS2 Game ROMs (.iso, .chd)
│
├── RPCS3_win\                   ← PS3 Emulator binaries & settings
│   ├── dev_flash\               ← PS3 system firmware files
│   └── dev_hdd0\                ← PS3 virtual HDD (saves, game data)
├── RPCS3_ios\                   ← PS3 Game ROMs (.iso, folder-based, decrypted ISOs)
│
└── PS_Firmwares\                ← Backups of system firmwares / BIOS files
```

## Adding a New Console

To add support for a new console, you have two options:
1. **Recommended Portable Layout**: Place two folders side-by-side in any of your configured Game Machine directories:
   - `<EMULATOR>_win\`: Emulator executable and its associated configuration (configured for portable mode).
   - `<EMULATOR>_ios\`: Folder containing the ROMs for that console (supporting extensions like `.iso`, `.cso`, `.chd`, `.bin`).
   *These pairs are automatically detected by the scanner.*
2. **Custom Mapping**: Run the Setup Wizard and add a custom console, where you can pair any custom emulator `.exe` file with any directory containing game files on your system.

## Cover Art Cache
To preserve portability, the `covers\` folder is stored directly in the launcher's root directory (`PROJECT_DIR`) next to `console.py`, rather than inside the emulation directories. This ensures that cover arts persist inside the launcher folder, allowing you to move the launcher across different machines or drives while keeping your cache intact.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md)
