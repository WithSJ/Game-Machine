# Game Machine Wiki Log

This file is a chronological log of operations performed on the Wiki (latest logs on top).

## [2026-07-18] bugfix | Power Menu: fix icon/label overlap and add mouse close button
Two issues in the Power Menu (`ui/draw_exit_menu.py`):

1. **Icon overlapping label**: Each option row hardcoded the label start to `r.x + 42`, which was sized for the old single-glyph Unicode icons (~15px wide). The recent ASCII replacements (`[X]`, `[LOCK]`, `[RST]`, `[OFF]`) at `f_popup_btn` (15pt bold) render up to ~60px wide, so the icon crashed into the label. Fix: render the icon first, measure its width, then place the label at `icon_x + icon_w + 14` so the gap is always 14px regardless of icon width.

2. **No mouse/touch way to dismiss**: The Power Menu could only be closed with `Esc` or the gamepad B button. Added a close `[X]` button at the top-right of the popup (stored on `gm.exit_menu_close_rect`, initialized in `__init__` for safety). Mouse clicks and finger taps on this rect call `_close_exit_menu()`. Updated the hint footer to mention `[X]=Close`.

Wired up the new rect in `app.py`:
- Added `self.exit_menu_close_rect = pygame.Rect(0, 0, 0, 0)` to `__init__`.
- Inserted close-rect checks at the top of both the `MOUSEBUTTONDOWN` and `FINGERUP` branches of the exit-menu input handler so the close button is tested before the option rects.

Verified: `python -m py_compile` clean; hint width (366px) fits inside the 420px panel.

## [2026-07-18] config | Enforce mandatory wiki-update + commit + push workflow
Rewrote `.agents/AGENTS.md` to make the change workflow explicit and mandatory for every modification - no matter how small. Previously the rules for wiki updates and git commit/push were stated separately and were easy to skip on tiny edits. The new "Mandatory Change Workflow" section consolidates them into a single ordered checklist that applies to every file touched:

1. Update `wiki/log.md` (top entry) and any affected wiki pages.
2. `git add` only the intended files (never `playtime.json` or `covers/`).
3. Commit with a `<type>:` subject and a descriptive body.
4. `git push origin main` (or current branch) - confirm it succeeds.

Also added rules of thumb: one logical change per commit, never commit secrets/BIOS/ISOs, never `--amend` pushed commits or force-push, fix root cause on hook failures rather than amending, and the workflow is mandatory even for one-line fixes.

## [2026-07-18] bugfix | Empty RECENTS tab trapped gamepad users out of EXIT button
`app.py::move_sel` had an early `if not L: return` that ran *before* the header-focus logic. When the RECENTS tab was empty (nothing played yet - the default state on a fresh install), pressing UP on the gamepad hit that return and never reached the code that moves focus to the SIZE/EXIT buttons. The user was stuck with no way to reach Power Menu via controller.

Fix: restructured `move_sel` so the header-focus block runs first regardless of list size; when the list is empty, only UP does something (jumps focus to the SIZE button, from which LEFT reaches EXIT and A activates it).

## [2026-07-18] bugfix | Comprehensive bug sweep across 8 modules
Audited the full codebase and fixed 15 bugs of varying severity:

**Critical**
- `core/decrypter.py`: Replaced destructive `os.remove()` + `shutil.move()` pattern with a rename-to-`.enc.bak` + move + delete-backup sequence so a failed move can no longer delete the user's original encrypted ISO.
- `core/decrypter.py`: Removed hardcoded `D:\Game Machine\PS3QDD.v1.3.2.with.keys` path; added `_resolve_tool_dir()` which searches configured `BASE`/`folders`/`PROJECT_DIR` (and any `PS3QDD*` child) so decryption works on any drive letter.
- `app.py`: Exit menu keyboard shortcut for Auto-Start was bound to `K_a` instead of `K_y`, contradicting the on-screen hint and the gamepad Y-button mapping. Switched to `K_y`.
- `covers/generator.py`: Refactored the PSP/PS3 cover-generation branches (previously near-duplicated) into a shared `_build_composite_cover()` helper and dropped `pygame.init()` / `Surface.convert()` / `Surface.convert_alpha()` calls - SDL is not thread-safe and these ran from the background daemon thread, risking crashes. `pygame.image.save()` works fine on unconverted surfaces.

**Medium**
- `ui/draw_setup.py`: Setup-screen particles fell in fixed vertical columns because `pt["x"]` was preserved on respawn. Now re-randomized with `random.uniform(0, SCREEN_W)` to match the main dashboard.
- `app.py::handle_setup_event`: Touch users could not dismiss the Setup Help modal because only `KEYDOWN`/`JOYBUTTONDOWN`/`MOUSEBUTTONDOWN` were handled. Added `FINGERUP` handling.
- `core/scanner.py::clean_name`: Single-pass bracket regex left a trailing `)` on nested tags like `Game (USA (En,Fr,De))`. Now applies the bracket regex in a loop until stable.
- `ui/draw_hero.py`: Removed a dead `pulse = 0.55 + 0.45 * math.sin(...)` line that was immediately overwritten by the `abs(...)` variant.
- `app.py::handle_event`: The 1-second post-launch input freeze also swallowed `QUIT` events, blocking Alt-F4 / window-close during that window. `QUIT` is now handled before the freeze check.

**Minor**
- `core/playdata.py::fmt_dur`: `fmt_dur(0)` returned `"1m"` due to `max(1, minutes)`. Now returns `"0m"`.
- `core/config.py`: Module-level `COVERS_DIR`/`BASE` were computed once at import, so folders changed in the Setup Wizard never propagated to the cover generator. Added `get_covers_dir()` + `refresh_paths()` and called `refresh_paths()` from `app.py::finish_setup()`.
- `app.py`: Removed dead imports (`BASE`, `CONSOLES`, `PLAYDATA_FILE`, `COVERS_DIR` from `core.config`).
- `app.py::draw`: Removed dead local variable `L` (only `gm_list` was used).
- `ui/draw_exit_menu.py`: Replaced Unicode power/lock/restart/shutdown glyphs (`⏻ ⚿ ⟳ ◼`) with ASCII tags (`[X] [LOCK] [RST] [OFF]`) because Bahnschrift does not reliably render them and they appeared as tofu boxes.
- `app.py::handle_setup_event`: The `setup_help_close_rect` was stored but never click-tested - any click anywhere dismissed the modal. Now only the `[X]` button (or a tap on it) dismisses via mouse/touch; keyboard/gamepad still dismiss from anywhere as before.

Verification: `python -m py_compile` clean across all 27 modules; `clean_name()` unit-checked against 5 representative filenames including nested brackets.

## [2026-07-18] feature | Portable Setup Screen and Custom Configurations
- Modified `core/config.py` and `core/playdata.py` to dynamically load settings from `playtime.json` and sync the playtime database between `PROJECT_DIR` and the primary library folder `BASE` (`BASE/playtime.json`). It performs a key-by-key merge comparing game playtime (keeping maximum progress) and resolves directories dynamically on save to preserve existing playtimes. Relocated `COVERS_DIR` relative to the primary configured directory (`BASE/covers`) for compatibility with existing cover caches.
- Updated `discover_consoles` in `core/scanner.py` to support multiple configured directories and user-mapped custom consoles.
- Implemented a complete Pygame-based Setup Wizard in `ui/draw_setup.py` that utilizes native Tkinter file and directory pickers to allow first-time configuration of folders and custom emulators. It automatically detects and sanitizes the console name based on the chosen emulator executable (e.g. `dolphin.exe` -> `DOLPHIN`), and dynamically checks for naming collisions against only actively resolved standard consoles from the user's folders, preventing premature renaming to numbered aliases (like `PSP 2`).
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

