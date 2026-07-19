# 🎮 GAME MACHINE — Complete Documentation

> **Custom Gamepad-Driven Emulator Frontend**
> A portable, console-style launcher for PSP / PS2 / PS3 (and any custom emulator)
> built with Python + Pygame.

- **Platform:** Windows 10 / 11
- **Language / Runtime:** Python 3.8+ · Pygame 2.0+
- **Current version:** v4 (Dashboard UI)
- **Last updated:** 20 July 2026
- **Project root:** the `Game Machine` folder (fully portable)

---

## Table of Contents

1. [Overview & Vision](#1-overview--vision)
2. [What Is an Emulation Frontend?](#2-what-is-an-emulation-frontend)
3. [Core Principles](#3-core-principles)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Module Reference](#5-module-reference)
6. [Execution Flow (Boot → Launch → Resume)](#6-execution-flow-boot--launch--resume)
7. [Directory Layout](#7-directory-layout)
8. [Smart Features](#8-smart-features)
9. [Input & Controls](#9-input--controls)
10. [Game / Console Data Model](#10-game--console-data-model)
11. [Getting Started & Setup](#11-getting-started--setup)
12. [Adding a New Console](#12-adding-a-new-console)
13. [Settings Panel Reference](#13-settings-panel-reference)
14. [Troubleshooting & FAQs](#14-troubleshooting--faqs)
15. [Build / Run Checklist](#15-build--run-checklist)
16. [Roadmap](#16-roadmap)

---

## 1. Overview & Vision

Game Machine turns any Windows PC into a dedicated **retro-game console**.
When you launch it, a full-screen, console-style dashboard opens where:

- Every game from every connected console appears in **one place**.
- The entire UI is **navigable by gamepad** (D-pad / stick to move, A to play).
- Selecting a game **launches the correct emulator automatically**, and when you
  quit the game you return straight to the dashboard — you never see the
  emulators' own menus.
- The look-and-feel mimics a PlayStation / Steam Deck console shell.

Rather than use a ready-made frontend (ES-DE, RetroBat, LaunchBox), Game Machine
is **built from scratch** for full control, learning, and a perfectly tailored
portable workflow.

---

## 2. What Is an Emulation Frontend?

An *emulation frontend* is a shell that sits in front of one or more emulators.
It does **not** emulate anything itself — it is a beautiful remote-control that:

1. **SCAN** — reads game folders and builds a list of games.
2. **SHOW** — renders that list in a navigable, branded UI.
3. **LAUNCH** — runs the right emulator with the right game, waits for it to
   close, then hands control back to the UI.

Game Machine follows exactly this three-responsibility model, but adds a layer
of "console OS" features on top: a setup wizard, a settings panel, cover-art
generation, playtime tracking, save-state resuming, Windows auto-start, and
power controls.

---

## 3. Core Principles

| Principle | What it means in Game Machine |
|-----------|-------------------------------|
| **Frontend ≠ emulator** | The app never runs a game; it only builds a command line and `subprocess`-launches the emulator. |
| **Data / logic separation** | Console definitions live in `playtime.json` (the database), not hardcoded in the source. Adding a console = adding data, not editing code. |
| **Portable by design** | The emulator is launched with `cwd` set to its own folder, so each emulator stays in *portable mode* (settings, BIOS, saves live next to the `.exe`). Copy the whole folder to any PC and it works. |
| **UI on the main thread only** | Pygame surfaces are created on the main thread. All heavy work (ISO parsing, cover downloads, decryption) runs in background worker threads and hands results back via thread-safe queues. |
| **Stale-input safety** | After an emulator exits, the input queue is flushed before the UI resumes — this prevents the "game re-launches itself" bug. |

---

## 4. High-Level Architecture

Game Machine is a **decoupled, event-driven Pygame application** split into four
concern areas:

```
┌─────────────────────────────────────────────────────────────┐
│                         console.py                            │
│                    (entry point → app.main)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                           app.py                              │
│                   GameMachine orchestrator                    │
│  • Boot / splash / font loading                               │
│  • State: tabs, selection, settings, popups, panels           │
│  • Main loop: handle events → update → draw → flip            │
│  • Launch orchestration & playtime accounting                 │
└──────┬───────────────┬───────────────┬───────────────┬───────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│  core/      │ │   ui/       │ │  input/     │ │   covers/    │
│ execution   │ │ rendering   │ │ controllers │ │ box-art +    │
│ & data      │ │ engine      │ │             │ │ ISO parsing  │
└─────────────┘ └─────────────┘ └─────────────┘ └──────────────┘
```

### Subsystem responsibilities

| Subsystem | Responsibility |
|-----------|----------------|
| `core/` | Path resolution, console discovery, game scanning, launching, decryption, playtime DB, save-state discovery, Windows auto-start. |
| `ui/` | Every drawable surface (header, tabs, hero, grid, footer, popup, settings, setup, exit menu, toast, splash) plus a render cache. |
| `input/` | Translates keyboard, gamepad, mouse, and touch events into `GameMachine` actions. |
| `covers/` | Background worker that extracts PSP/PS3 cover art from ISOs and downloads PS2 covers by serial. |

### Decoupling mechanism

`app.py` only knows about **abstract actions** (`move_sel`, `set_tab`,
`launch_selected`, `_show_settings`, …). The `input/` modules map physical
buttons to those actions; the `ui/` modules render state; `core/` performs side
effects. Nothing in `input/` draws, nothing in `ui/` launches processes.

---

## 5. Module Reference

### Entry point — `console.py`
Thin wrapper. Imports `app.main` and calls it. All real logic lives in `app.py`.

### Orchestrator — `app.py`
The `GameMachine` class owns all runtime state and the main loop (`run()`):

- **Boot sequence:** `pygame.init()` → detect native resolution → override
  `theme` layout constants → load fonts → load `playtime.json` → decide if
  setup is needed → scan consoles/games (or show Setup Wizard) → build render
  caches → start cover generator.
- **Event loop:** `handle_event(e)` dispatches to input handlers or to focused
  overlays (popup, exit menu, settings, setup). Input is ignored while
  `ignore_input_until` is in the future (post-launch freeze).
- **Render:** `draw(now)` composites background, grid lines, ambient particles,
  then each UI component.
- **Launch:** `launch_selected()` → confirmation popup → `_confirm_launch()` →
  `core.launcher.launch_game()` → record playtime → flush input.

### `core/config.py`
Resolves paths from the database.
- `PROJECT_DIR` — folder containing `console.py`.
- `PLAYDATA_FILE` — `playtime.json` next to `console.py`.
- `BASE` — first configured library folder (default `D:\Game Machine`).
- `get_covers_dir()` / `refresh_paths()` — re-resolve `BASE` after the Setup
  Wizard writes new folders, so covers and scans pick up the change live.

### `core/scanner.py`
- `clean_name(filename)` — regex name cleaner (see §8.1).
- `find_emulator_exe(folder)` — picks the largest `.exe` in an emulator folder
  (skips `unins*`, `setup*`, `updater*`, etc.).
- `discover_consoles(folders, custom_consoles)` — resolves the 3 default
  consoles, merges custom consoles, then **auto-detects** any
  `<NAME>_win` + `<NAME>_ios` folder pair.
- `scan_games(consoles)` — walks each ROM folder, keeps matching extensions,
  builds the `games` list.

### `core/launcher.py`
- `_build_command(cfg, game, load_state)` — assembles the emulator argv,
  including per-emulator save-state flags (`--state=`, `-statefile`,
  `--savestate`).
- `launch_game(game, consoles, load_state)` — `subprocess.Popen` with
  `cwd = emulator folder` and `DETACHED_PROCESS`; optional PPSSPP menu monitor
  thread; `proc.wait()`; then the **stale-input flush** (`pygame.time.wait(500)`
  → `event.pump()` → `event.clear()`); returns elapsed seconds.

### `core/decrypter.py`
Headless **PS3 ISO decryption** via `PS3Dec.exe`.
- `_resolve_tool_dir()` — finds the `PS3QDD*` folder (portable-aware).
- `find_dkey_path()` — matches the game's `.dkey` file (exact, case-insensitive,
  then fuzzy by cleaned name).
- `run_decryption_thread(gm, game)` — runs PS3Dec, then **safely replaces** the
  encrypted ISO (rename-to-`.enc.bak`, move decrypted in, delete backup only on
  success). On success sets `gm.decryption_done` so the app auto-launches.

### `core/playdata.py`
The persistent database layer.
- `load_playdata()` — merges `playtime.json` from `PROJECT_DIR` **and** each
  configured `BASE`, keeping the record with the most playtime per game.
- `save_playdata(data)` — writes to both locations.
- `fmt_dur()` / `fmt_last()` — human-readable duration and "last played" labels.

### `core/savestates.py`
`find_latest_save_state(game, consoles)` — locates the newest save-state file
for a game by parsing the disc serial from the ISO (PSP `DISC_ID`, PS2 `BOOT2`
serial, PS3 `TITLE_ID`) and scanning each emulator's state directory.

### `core/autostart.py`
- `is_auto_start_enabled()` / `set_auto_start(enabled)` — add/remove Game
  Machine from the Windows `HKCU\...\Run` registry key, using `pythonw.exe` so
  no console window appears on boot.

### `covers/iso_parser.py`
A from-scratch **ISO9660 reader**: walks the Primary Volume Descriptor, reads
directory records, and extracts `ICON0.PNG` / `PIC1.PNG`. Also parses
`PARAM.SFO` (PSP/PS3) and `SYSTEM.CNF` (PS2) to recover disc IDs / serials.

### `covers/ps2_serial.py`
`get_ps2_serial(iso_path)` — reads `SYSTEM.CNF`'s `BOOT2` line and normalizes
the serial to the hyphenated form (`SLUS-21134`) used by save states and
cover-art repositories.

### `covers/generator.py`
Background cover-art worker.
- `_cover_worker()` — processes `CoverTask` items, extracts ISO images or
  resolves PS2 serials, pushes `CoverResult` to a queue.
- `start_cover_generator_thread()` — idempotent thread starter / task enqueuer.
- `process_cover_results()` — **main-thread** consumer that builds/saves the
  pygame surface (composite cover for PSP/PS3, downloaded JPG for PS2).

### `ui/` (rendering)
| File | Renders |
|------|---------|
| `theme.py` | Colors, layout rects, console color pool, easing. |
| `cache.py` | Cached background, grid lines, hero art, ghost text, covers, placeholders. |
| `draw_splash.py` | Boot splash screen. |
| `draw_header.py` | Logo, clock, SIZE + SETTINGS buttons. |
| `draw_tabs.py` | Console tabs (RECENTS + each console), with accent color. |
| `draw_hero.py` | Selected-game hero banner + cover + playtime stats. |
| `draw_grid.py` | Cover-art grid with selection animation. |
| `draw_footer.py` | Control hints. |
| `draw_toast.py` | Transient status messages. |
| `draw_popup.py` | Launch / decrypt / launch-menu confirmation popups. |
| `draw_settings.py` | 5-tab Settings Panel. |
| `draw_setup.py` | First-run Setup Wizard (Tkinter pickers). |
| `draw_exit_menu.py` | Power / exit menu. |

### `input/`
| File | Handles |
|------|---------|
| `keyboard.py` | Arrow keys, Enter/Space, `Q/E` tab switch, `R` random, `F11` fullscreen, `S` grid size, `Esc` exit menu. |
| `gamepad.py` | A/B/X/Y, L1/R1, D-pad/analog axis navigation with **hold-to-repeat**. |
| `mouse.py` | Hover-to-select, click-to-activate, wheel scroll. |
| `touch.py` | Finger tap = click, drag = scroll. |

---

## 6. Execution Flow (Boot → Launch → Resume)

```
python console.py
        │
        ▼
   app.main()  →  GameMachine().__init__()
        │
        ├─ pygame.init(), detect resolution, override theme layout
        ├─ load fonts, show splash
        ├─ load playtime.json → __settings__ (folders, custom_consoles, size)
        │
        ├─ needs_setup?  (no folders AND no custom consoles)
        │        │
        │       YES → draw_setup wizard (pick folders / consoles)
        │        │            │  finish_setup() → discover_consoles → scan_games
        │        │
        │       NO  → discover_consoles() + scan_games()
        │
        ├─ build tabs [RECENTS, PSP, PS2, PS3, ...]
        ├─ build render caches (bg, gridlines, particles)
        ├─ start_cover_generator_thread(games, consoles)
        │
        ▼
   run()  ── main loop ──
        │  for each event: handle_event()
        │  update_gamepad(now) / update_scroll()
        │  process_cover_results()  (drain queue → save covers)
        │  if decryption_done: _confirm_launch()
        │  draw(now); flip(); clock.tick(30)
        │
        ▼  (user presses A on a game)
   launch_selected() → popup
        │  user confirms → _confirm_launch()
        │        │
        │        ▼
        │   core.launcher.launch_game()
        │        ├─ _build_command()  (with optional save state)
        │        ├─ subprocess.Popen(cwd = emulator folder)
        │        ├─ proc.wait()
        │        ├─ pygame.time.wait(500) + event.pump() + event.clear()
        │        └─ return elapsed seconds
        │
        ▼
   record playtime → save → set ignore_input_until (+1s) → resume loop
```

---

## 7. Directory Layout

```
Game Machine\
├── console.py                 # Entry point (calls app.main)
├── app.py                     # GameMachine orchestrator + main loop
├── playtime.json              # Persistent DB: playtime + __settings__ (folders, custom_consoles)
├── core/                      # Execution & data logic
│   ├── config.py              # Path resolution
│   ├── scanner.py             # Console discovery + game scan + name cleaner
│   ├── launcher.py            # Emulator launch wrapper + input flush
│   ├── decrypter.py           # PS3Dec headless decryption
│   ├── playdata.py            # Playtime DB manager
│   ├── savestates.py          # Save-state discovery
│   └── autostart.py           # Windows registry auto-start
├── ui/                        # Render system (theme, cache, draw_* modules)
├── input/                     # keyboard / gamepad / mouse / touch
├── covers/                    # Cover generator + ISO parser + PS2 serial
├── PPSSPP_win/                # PSP emulator (portable)  + PPSSPP_ios/  (PSP ROMs)
├── PCSX2_win/                 # PS2 emulator (portable)  + PCSX2_ios/  (PS2 ROMs)
├── RPCS3_win/                 # PS3 emulator (portable)  + RPCS3_ios/  (PS3 ROMs)
├── <NAME>_win/ + <NAME>_ios/  # Any custom console (auto-detected)
├── PS3QDD*/                   # PS3Dec tool + Keys/ + Decrypted/
├── PS_Firmwares/              # BIOS / PUP backups
└── covers/                    # Generated box art: covers/<CONSOLE>/<Name>.png|.jpg
```

### The portable `_win` / `_ios` pattern
Every console is expressed as a **pair**:
- `<CONSOLE>_win/` — the emulator `.exe` and its portable settings/BIOS/saves.
- `<CONSOLE>_ios/` — the game files (`.iso`, `.cso`, `.chd`, `.bin`).

Because the emulator launches with `cwd` set to its own folder, it reads
settings from there (not `C:\Users`), so the entire `Game Machine` folder is a
self-contained console you can copy to any PC or external drive.

---

## 8. Smart Features

### 8.1 Regex name cleaning
`0517 - Tekken - Dark Resurrection (USA) (En,Fr,De,Es,It).iso`
→ displays as **`Tekken - Dark Resurrection`**

`clean_name()` (scanner.py):
1. Strips a leading `NNNN - ` number prefix.
2. Peels bracketed / parenthesized tags **iteratively** so nested tags like
   `Game (USA (En,Fr,De))` are fully removed.
3. Converts `_` → space, collapses multiple spaces.

### 8.2 Dual-source cover generator (background thread)
Runs as a daemon worker, never blocking the UI:
- **PSP & PS3:** parses the ISO's `PSP_GAME` / `PS3_GAME` directory, pulls
  `ICON0.PNG` (logo) + `PIC1.PNG` (backdrop), composites a 3:4 (360×480) cover.
- **PS2:** reads the serial from `SYSTEM.CNF`, downloads the matching cover from
  the `xlenore/ps2-covers` repo.
- **Custom consoles:** mapped to PSP/PS2/PS3 routines by name or emulator path.
- Covers are cached under `covers/<CONSOLE>/`; already-present high-res covers
  are skipped.

### 8.3 Save-state resume
Before launching, `find_latest_save_state()` checks for a recent save state.
If found, the launch popup offers **Load Last Save State / Just Play / Cancel**.
Per-emulator flags are applied automatically:
- PSP → `--state=<path>`
- PS2 → `-statefile <path>`
- PS3 → `--savestate <path>` (no ISO; state embeds everything)

### 8.4 Automatic PS3 ISO decryption
First-time encrypted PS3 games prompt for decryption. `decrypter.py` runs
`PS3Dec.exe` headlessly against the matched `.dkey`, then **safely replaces**
the encrypted ISO (backup → move decrypted in → delete backup only on success).
On completion the game auto-launches.

### 8.5 Input-event purging (the "self-relaunch" fix)
While an emulator runs, gamepad button events keep buffering in Pygame's queue
(because joystick events don't need window focus). On return, a stale "A press"
would re-launch the same game. Fix (in `launch_game`): wait 500 ms, pump OS
events into the queue, then `pygame.event.clear()` to drop them all. The app
additionally sets `ignore_input_until` ~1 s after launch as a second guard.

### 8.6 Unified Settings Panel
A 5-tab modal (FOLDERS, CONSOLES, DISPLAY, SYSTEM, ABOUT) lets you manage
libraries, custom consoles, grid size, fullscreen, Windows auto-start, lock /
restart / shutdown / exit, and view stats — all inside the Pygame UI.

### 8.7 Playtime & Recents
Every launch accumulates seconds per game path; `RECENTS` tab shows the last 16
played games; the hero banner shows total playtime and "last played" labels.

---

## 9. Input & Controls

### Gamepad (XInput / DirectInput)
| Button | Action |
|--------|--------|
| **A** (0) | Play selected game / activate focused header button |
| **B** (1) | Back to RECENTS tab |
| **Y** (3) | Random pick |
| **L1 / R1** (4 / 5) | Previous / next console tab |
| **D-pad / Left stick** | Navigate grid (hold = repeat) |
| **Up from top row** | Focus header (SIZE / SETTINGS / EXIT) |

In overlays, A confirms, B cancels/back, L1/R1 switch settings tabs.

### Keyboard
| Key | Action |
|-----|--------|
| Arrows / WASD | Navigate |
| Enter / Space | Play / activate |
| Q / E (or `[` / `]`) | Previous / next tab |
| R / Y | Random pick |
| S | Cycle grid size |
| F11 | Toggle fullscreen |
| Esc | Exit menu |
| Home / End | Jump to first / last game |
| PageUp / PageDown | Jump 2 rows |

### Mouse / Touch
- **Hover** a card to select it; **click** to play (click again on selected).
- **Wheel** scrolls the grid.
- **Tap** = click; **drag** = scroll (touch).

---

## 10. Game / Console Data Model

A **game** dict (built by `scan_games`):
```python
{
    "name": "Tekken - Dark Resurrection",   # cleaned display name
    "path": r"...\PPSSPP_ios\game.iso",      # absolute file path
    "console": "PSP",                         # console key
}
```

A **console** config (resolved by `discover_consoles` / stored in
`__settings__.custom_consoles`):
```python
{
    "rom_folder": r"...\PPSSPP_ios",
    "extensions": [".iso", ".cso"],
    "emulator":   r"...\PPSSPP_win\PPSSPPWindows64.exe",
    "args":       ["--fullscreen"],
}
```

`playtime.json` shape:
```json
{
  "__settings__": {
    "size": "medium",
    "folders": ["D:\\Game Machine"],
    "custom_consoles": { "Dolphin": { ... } },
    "auto_start": false
  },
  "D:\\Game Machine\\PPSSPP_ios\\game.iso": { "seconds": 5400, "last": 1750000000 }
}
```

### Supported / auto-detected consoles
| Console | Emulator | Formats | Launch args |
|---------|----------|---------|-------------|
| PSP | PPSSPP (64-bit) | `.iso`, `.cso` | `--fullscreen` |
| PS2 | PCSX2 v2+ | `.iso`, `.chd` | `-fullscreen -batch` |
| PS3 | RPCS3 | `.iso`, folders | `--no-gui` |
| Custom | any `.exe` | user-defined | user-defined |

Any `<NAME>_win` + `<NAME>_ios` pair in a configured folder is auto-detected
with default extensions and empty args.

---

## 11. Getting Started & Setup

### Prerequisites
- **OS:** Windows 10 / 11.
- **Python:** 3.8+ (tick *"Add Python to PATH"* during install).
- **Controller (optional):** XInput (Xbox / DualSense / Steam Deck) or
  DirectInput gamepad.
- **Emulators:** place each emulator in its `<NAME>_win` folder in portable mode.

### Install & run
```bash
# 1. Clone / copy the whole "Game Machine" folder
# 2. Install the one dependency
pip install pygame

# 3. Launch
python console.py
```

### First-run Setup Wizard
On first launch (no folders configured), the **Setup Wizard** appears:
1. **Add Library Folder** — pick the folder that contains your `_win`/`_ios`
   pairs (native Tkinter folder picker).
2. **Add Custom Console** — optionally map a custom emulator + ROM folder.
3. **Help** — explains the portable pattern.
4. **Finish Setup** — triggers discovery, scan, and cover generation.

After setup, config is saved to `playtime.json` and the dashboard opens.

---

## 12. Adding a New Console

### Option A — Portable auto-detect (recommended)
Place side-by-side in any configured library folder:
```
Dolphin_win/   ← contains Dolphin.exe (+ portable settings)
Dolphin_ios/   ← contains .iso / .wbfs games
```
Game Machine auto-discovers it on the next scan — no configuration needed.

### Option B — Interactive mapping
1. Open **Settings** (SETTINGS button / gear) → **CONSOLES** tab.
2. Select **+ Add Custom Console**.
3. Enter name, pick the emulator `.exe`, pick the ROM directory, set extensions
   and custom launch args.
4. Game Machine updates `playtime.json`, rescans, and adds the console to the
   dashboard.

---

## 13. Settings Panel Reference

| Tab | Options |
|-----|---------|
| **FOLDERS** | Add / remove library folders to scan. |
| **CONSOLES** | View detected consoles; add / remove custom consoles. |
| **DISPLAY** | Grid size (Small 12 / Medium 8 / Large 5 cols); toggle borderless fullscreen. |
| **SYSTEM** | Windows Auto-Start toggle; Lock Screen; Restart PC; Shutdown PC; Exit. |
| **ABOUT** | Game count, console count, directories, version. |

System power actions call Windows APIs directly (`LockWorkStation`,
`shutdown /r` or `/s`). Auto-Start writes the launch command (via `pythonw`) to
the `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` registry key.

---

## 14. Troubleshooting & FAQs

| Problem | Cause / Fix |
|---------|-------------|
| No games appear | Settings → FOLDERS: verify library path. Settings → CONSOLES: verify emulator path & extensions. |
| Game won't launch | Confirm the emulator `.exe` path; test the full command manually in `Win+R`. Ensure `_win` folder is in portable mode. |
| PS2 BIOS error | Put BIOS files in `PCSX2_win\bios\` and select them in PCSX2 settings. |
| PS3 not fullscreen | Enable *Start games in fullscreen* in RPCS3, or use Alt+Enter in-game. |
| Game re-launches after exit | Stale-input bug — already fixed via `event.clear()` + `ignore_input_until`. Restart the launcher if it persists. |
| Gamepad not detected | Connect the pad **before** running `console.py`; if it disconnects, restart to re-init pygame joystick. |
| PS3 encrypted ISO | Use the in-app Decrypt prompt; ensure `PS3QDD*` (with `PS3Dec.exe` + `Keys/`) is present in a library folder. |
| Auto-Start not working | Enable it in Settings → SYSTEM; it registers `pythonw console.py` in the Windows Run key. |
| Covers missing | First launch generates them in the background; PS2 needs internet access to the cover repo. |

---

## 15. Build / Run Checklist

- [ ] Python 3.8+ on PATH.
- [ ] `pip install pygame`.
- [ ] Emulators placed in `<NAME>_win` folders (portable mode).
- [ ] Game files in `<NAME>_ios` folders.
- [ ] (PS3) `PS3QDD*` tool folder with `PS3Dec.exe` + `Keys/`.
- [ ] Run `python console.py`; complete Setup Wizard on first launch.

---

## 16. Roadmap

### ✅ Completed
- [x] **Level 1 — Core:** multi-console scan, regex cleaner, grid list, gamepad +
      keyboard input, custom consoles, self-relaunch fix, portable mode.
- [x] **Level 2 — Box Art:** ISO cover extraction, PS2 serial cover download,
      cover grid + placeholders, background worker.
- [x] **Level 3 — Console Feel:** console tabs (L1/R1, Q/E), settings panel,
      save-state resume, playtime DB + Recents, database merge.
- [x] **Level 4 — System Console Mode:** borderless fullscreen, Windows
      auto-start registry, lock / restart / shutdown, exit menu, touch input,
      Setup Wizard.

### 🔜 Future Concepts
- [ ] UI sound effects (select / confirm) and background music.
- [ ] Text search / filter for quick ROM indexing.
- [ ] Cross-platform Linux build (Flatpak) for Steam Deck / laptops.
- [ ] Multiple gamepad binding profiles.
- [ ] Themes / color customization.
- [ ] Metadata scraping (descriptions, ratings).

---

> *"A tired old laptop can become a Linux console, and a single Python file can
> become a whole PlayStation UI — with the right tools and realistic expectations."*

**Happy Gaming! 🕹️**
