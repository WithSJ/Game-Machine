# Game Machine Wiki Log

This file is a chronological log of operations performed on the Wiki (latest logs on top).

## [2026-07-18] feature | Portable Setup Screen and Custom Configurations
- Modified `core/config.py` to dynamically load settings from `playtime.json` and resolved `COVERS_DIR` relative to the primary configured directory (`BASE/covers`) for compatibility with existing cover caches.
- Updated `discover_consoles` in `core/scanner.py` to support multiple configured directories and user-mapped custom consoles.
- Implemented a complete Pygame-based Setup Wizard in `ui/draw_setup.py` that utilizes native Tkinter file and directory pickers to allow first-time configuration of folders and custom emulators. It automatically detects and sanitizes the console name based on the chosen emulator executable (e.g. `dolphin.exe` -> `DOLPHIN`), streamlining custom configuration.
- Intercepted events, rendering, and background worker threads in `app.py` to handle the setup lifecycle and initiate dynamic game discovery on completion.
- Updated `wiki/architecture.md` and `wiki/file_structure.md` to reflect dynamic configuration and setup flows.
- Updated `.gitignore` to ignore all contents of `covers/` except `.py` script files to automatically keep all existing and future cover caches local-only.
- Added gamepad axis and D-pad support in `input/gamepad.py` for navigating the Setup Wizard menu, enabling full controller capability alongside keyboard and mouse inputs.
- Refactored `get_cover_for` in `ui/cache.py` to search for cover images next to the ROM file first, then check the central cache directory (matching either the cleaned name or the exact ROM filename). Modified `covers/generator.py` to dynamically create directories for all active consoles and automatically map custom console names (like `KKK`) to PSP/PS2/PS3 extraction/downloading routines by checking the emulator executable path (e.g. PPSSPP, PCSX2, RPCS3).

## [2026-07-18] config | Reverse Wiki Log Order
- Updated the chronological order of [log.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md) to put the latest entries on top.
- Modified custom workspace rules ([AGENTS.md](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/AGENTS.md)) and the [wiki-maintainer](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md) skill to ensure future operations insert logs at the top.

## [2026-07-18] doc | Professional README Update
- Created a comprehensive and professional README.md outlining Game Machine features, portable directory layouts, internal components, custom decrypter, covers generator, keyboard/gamepad setup, and future development guidelines.

## [2026-07-18] config | Untrack playtime.json
- Updated `.gitignore` to exclude `playtime.json` from git tracking.
- Untracked `playtime.json` from the repository using `git rm --cached` to keep it local-only.

## [2026-07-18] ingest | Game-Machine-Documentation.md
- Extracted and structured the monolithic Game-Machine-Documentation.md into 6 focused wiki pages:
  - [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
  - [File Structure](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/file_structure.md)
  - [Emulator Setup](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/emulator_setup.md)
  - [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
  - [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md)
  - [Roadmap](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/roadmap.md)
- Populated [index.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md) with references to all new pages.

## [2026-07-18] system | Wiki Initialized
- Initialized directory structure for the LLM Wiki (`sources/` and `wiki/`).
- Created custom workspace rules (`.agents/AGENTS.md`) and wiki-maintainer skill (`.agents/skills/wiki-maintainer/SKILL.md`).

