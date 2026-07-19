# Game Machine Wiki Log

This file is a chronological log of operations performed on the Wiki (latest logs on top).

## [2026-07-19] system | Add mandatory testing rule before git commit + push
Added a new top-level section "Mandatory Testing Before Git Commit & Push (Applies to EVERY change)" to `.agents/AGENTS.md` and wove it into the existing "Mandatory Change Workflow" as a new step 2 (between wiki update and `git add`).

### The rule (4 steps)
1. **Test before staging** — run a real verification step that exercises the changed code (not just `py_compile` for Python; offscreen render test for UI; JSON/Markdown parse check for wiki/config). If you don't know what test to run, ASK the user.
2. **Report test results to the user** — show what was run, what passed, what failed. Fix failures before going further.
3. **Ask the user for testing confirmation BEFORE `git add` / `git commit` / `git push`** — use the `question` tool and wait. Options: "Proceed with commit + push" / "Run more tests first" / "Hold off — I want to test myself". Do NOT commit until the user explicitly says to proceed.
4. **Only after the user confirms, run the normal commit + push workflow.**

### Hard rules added
- MUST run at least one real test before asking the user.
- MUST NOT run `git add` / `git commit` / `git push` until the user has explicitly confirmed.
- MUST NOT skip the ask step even for tiny/obvious changes.
- MUST report test results truthfully — never claim a test passed if it failed or wasn't run.
- MUST re-test after any post-test edit; the testing rule restarts from step 1.

### Updated "Mandatory Change Workflow"
The existing 4-step workflow is now 5 steps: (1) update wiki → (2) test and ask user for confirmation → (3) stage → (4) commit → (5) push. The new step 2 references the testing section.

## [2026-07-19] refactor | Tokenize all raw RGB tuples in ui/*.py to enforce the design philosophy
Audited every button and draw call across all 13 files in `ui/` against the UI Design Philosophy §2.4 ("MUST NOT introduce raw RGB tuples in draw code"). Found 30+ violations where colors were hardcoded instead of sourced from `ui/theme.py` tokens. All fixed.

### New tokens added to `ui/theme.py`
- `COL_BRAND = (240, 112, 60)` — Game Machine brand orange (was hardcoded in header logo, splash, exit menu, settings)
- `COL_DESTRUCTIVE = (200, 70, 80)` — destructive red fill for CANCEL/NO/SHUTDOWN buttons (was hardcoded in popup, exit menu, settings)
- `COL_TEXT_DARK = (11, 13, 19)` — dark text on accent fills (was hardcoded in hero PLAY, popup YES, launch menu)
- `COL_TEXT_LIGHT = (231, 233, 238)` — slightly dimmer than COL_TEXT; used for selected list-row labels (was hardcoded in exit menu, settings, grid, toast, popup)
- `COL_TEXT_ON_RED = (255, 240, 240)` — light text on the destructive red fill (was hardcoded in popup NO/CANCEL)
- `COL_KNOB_OFF = (140, 143, 150)` — toggle knob in the OFF position (was hardcoded in exit menu)
- `COL_FALLBACK = (150, 150, 150)` — neutral gray for unknown console / missing color (was hardcoded in grid, settings)

### Files fixed (13 files, 30+ raw RGB tuples eliminated)
- `ui/draw_header.py` — EXIT button: replaced `(60, 20, 25)` dark red fill with `mix(COL_BG, COL_BTN_B, 0.15)`; replaced `(255, 120, 130)` and `(200, 70, 80)` with `COL_BTN_B`. SETTINGS button: replaced `(95, 212, 232)` with `REC_COLOR`. Logo diamond: replaced `(240, 112, 60)` with `COL_BRAND`. Clock text: replaced `(213, 215, 220)` with `COL_TEXT`.
- `ui/draw_exit_menu.py` — 4 option colors replaced with `COL_BRAND` / `REC_COLOR` / `COL_PAD_OK` / `COL_DESTRUCTIVE`. Selected label: replaced `(231, 233, 238)` with `COL_TEXT_LIGHT`. Toggle switch: replaced `(79, 214, 166)` with `COL_PAD_OK`, `(231, 233, 238)` with `COL_TEXT_LIGHT`, `(140, 143, 150)` with `COL_KNOB_OFF`.
- `ui/draw_hero.py` — PLAY triangle + text: replaced `(11, 13, 19)` with `COL_TEXT_DARK`. DETAILS outline: replaced `(58, 62, 72)` with `COL_CARD_BORDER`. DETAILS text: replaced `(185, 188, 194)` with `COL_DIM`. Hero title: replaced `(253, 253, 253)` with `COL_TEXT`. Meta text: replaced `(155, 160, 170)` with `COL_DIM`.
- `ui/draw_tabs.py` — Unselected tab fill: replaced `(18, 21, 28)` with `COL_PANEL`. Unselected tab border: replaced `(32, 36, 46)` with `COL_CARD_BORDER`.
- `ui/draw_settings.py` — Accent: replaced all 5 occurrences of `(95, 212, 232)` with `REC_COLOR`. Option row text: replaced `(231, 233, 238)` with `COL_TEXT_LIGHT`. System tab actions: replaced `(79, 214, 166)` with `COL_PAD_OK`, `(200, 70, 80)` with `COL_DESTRUCTIVE`, `(240, 112, 60)` with `COL_BRAND`. Fallback console color: replaced `(150, 150, 150)` with `COL_FALLBACK`.
- `ui/draw_setup.py` — Accent: replaced 2 occurrences of `(95, 212, 232)` with `REC_COLOR`. Selected text: replaced `(7, 8, 12)` with `COL_BG`.
- `ui/draw_splash.py` — Logo diamond + loading bar: replaced `(240, 112, 60)` with `COL_BRAND`. Title: replaced `(238, 240, 244)` with `COL_TEXT`. Radial glow: replaced `(20, 24, 35)` with `COL_BG_GLOW`.
- `ui/draw_toast.py` — Border: replaced `(44, 47, 56)` with `COL_CARD_BORDER`. Toast text: replaced `(231, 233, 238)` with `COL_TEXT_LIGHT`.
- `ui/draw_grid.py` — Card name: replaced `(231, 233, 238)` / `(185, 188, 195)` with `COL_TEXT_LIGHT` / `COL_DIM`. Fallback console color: replaced `(150, 150, 150)` with `COL_FALLBACK`.
- `ui/draw_footer.py` — L1 R1 pill text: replaced `(185, 188, 194)` with `COL_DIM`.
- `ui/draw_popup.py` — 2-option YES button: replaced `(11, 13, 19)` with `COL_TEXT_DARK`. 2-option NO button: replaced `(200, 70, 80)` with `COL_DESTRUCTIVE` and `(255, 240, 240)` with `COL_TEXT_ON_RED`. 3-option launch_menu: replaced `(231, 233, 238)` with `COL_TEXT_LIGHT`, `(200, 70, 80)` with `COL_DESTRUCTIVE`, `(255, 240, 240)` with `COL_TEXT_ON_RED`, `(11, 13, 19)` with `COL_TEXT_DARK`.
- `ui/cache.py` — Hero background gradient: replaced `(16, 19, 25)` with `COL_BG_GLOW`, `(11, 13, 19)` with `COL_TEXT_DARK`. Placeholder label: replaced `(58, 62, 72)` with `COL_CARD_BORDER`.

### Verification
- Automated scan confirms **zero raw RGB tuples** remaining in `ui/*.py` (excluding `theme.py` which defines them).
- All 13 modified files compile cleanly.
- Offscreen render test confirms all 3 launch_menu selections, the 2-option launch popup, and the exit menu all render with the correct token-sourced colors.

## [2026-07-19] doc | Establish UI Design Philosophy as a mandatory skill
Created a single source of truth for Game Machine's visual design and made it a loadable opencode skill + a wiki page + a mandatory workflow rule in `AGENTS.md`. The launch-game 3-option popup (`ui/draw_popup.py::_draw_launch_menu_body`) is the canonical reference implementation.

### New skill: `.agents/skills/ui-design-philosophy/SKILL.md`
- Auto-discoverable opencode skill (`name: ui-design-philosophy`) that enforces the design workflow before any UI file is touched.
- Lists when to load it (any UI/draw change), the 10-step workflow, hard rules, and a copy-from table of canonical reference implementations.
- Loaded via the same mechanism as the existing `wiki-maintainer` skill.

### New wiki page: `wiki/ui_design_philosophy.md`
A prescriptive, 14-section design system covering:
- §1 Visual language — "premium console dashboard" feel, dark + per-console accent.
- §2 Color palette — every token in `ui/theme.py` (neutrals, accent colors per console, functional colors) with rules: no raw RGB tuples, use `mix()`, one accent per console.
- §3 Typography — three families (Bahnschrift heavy / Verdana body / Consolas mono) and the full 15-token type scale from `app.py::__init__`. No new sizes without a token.
- §4 Button taxonomy — exactly three archetypes, no others:
  - **A — Parallelogram Action Button**: primary actions (hero PLAY, popup choices, setup menu). Filled accent when selected, `COL_PANEL2` + `COL_CARD_BORDER` outline when not. `cut=8–10`. Dark text on accent fill.
  - **B — Rounded Rect Chip Button**: secondary / header / tab. `border_radius=3–8`. Focused = 2px accent border, unfocused = 1px `COL_CARD_BORDER`.
  - **C — List Option Row**: settings & exit menu rows. `border_radius=8`. Selected = `mix(COL_BG, accent, 0.25)` fill + 2px accent border + 3px left accent bar.
- §5 Popup anatomy — overlay alpha 160, `COL_PANEL` + `border_radius=14`, 3px accent top glow, 1px `mix(COL_BG, accent, 0.4)` border, `ease_out` scale-in over 200–220ms, centered `f_popup_title` 24px from top, `f_mono` hint 22px from bottom. Includes an ASCII diagram of the launch popup.
- §6 Console chip pattern, §7 Hint/footer pattern, §8 Iconography (geometric primitives only, no unicode glyphs), §9 Spacing & layout, §10 Animation principles (`ease_out`, never linear for organic motion), §11 Input binding conventions (all four modalities wired), §12 MUST / MUST NOT quick reference, §13 Reference implementations table, §14 New-screen checklist.

### Updated: `.agents/AGENTS.md`
- Added a new top-level section "Mandatory UI Design Workflow (Applies to ANY UI / visual change)" with 10 enforceable steps that must run before any `ui/` change is committed.
- Updated "Related Resources" to link the new skill and wiki page alongside the existing wiki-maintainer skill.

### Updated: `wiki/index.md`
- Added the new "UI Design Philosophy" entry under "Guides & Instructions" so future agents discover it when consulting the wiki.
- Bumped "Last updated" date to 2026-07-19.

## [2026-07-19] feature | Save-State Launcher popup (3-option) + per-emulator CLI save-state loading
Added a "Load Last Save State" option to the launch-game popup. When the user activates a game card, Game Machine now scans the emulator's save-state directory for the newest save state matching that game and, if found, shows a 3-option vertical popup (LOAD LAST SAVE STATE / JUST PLAY / CANCEL); otherwise it falls back to the 2-option YES/NO popup. Encrypted PS3 games still get the existing DECRYPT GAME? prompt first.

### New file: `core/savestates.py`
- `find_latest_save_state(game, consoles)` globs each emulator's save-state directory and returns the newest match by mtime, or `None`.
- PSP: scans `<PPSSPP_win>/memstick/PSP/PPSSPP_STATE/` for `<DISC_ID>_<DISC_VER>_<slot>.ppst` (falls back to `~/Documents/PPSSPP/...`).
- PS2: scans `<PCSX2_win>/sstates/` for `<serial> (*.p2s` (falls back to `~/Documents/PCSX2/...`).
- PS3: scans `<RPCS3_win>/savestates/<TitleID>/*.SAVESTAT` (+ `.zst` / `.gz` variants) (also tries `portable/` and `%RPCS3_CONFIG_DIR%`).

### Extended: `covers/iso_parser.py`
- New `_read_iso_file(iso_path, dir_name, file_name)` walks an ISO9660 directory chain to read any file (PARAM.SFO, SYSTEM.CNF, etc.) — used by the save-state identifier and reuses `parse_dir_record` / `read_directory`.
- New `parse_param_sfo(data)` decodes the PSP/PS3 PARAM.SFO binary format (header + index table + key table + data table) into a `{key: value}` dict, handling string (`0x0404`/`0x0204`) and integer (`0x0402`) data formats.
- New `get_psp_disc_id(iso_path)` returns `(DISC_ID, DISC_VERSION)` from `PSP_GAME/PARAM.SFO`.
- New `get_ps3_title_id(iso_path)` returns `TITLE_ID` from `PS3_GAME/PARAM.SFO`.

### Extended: `core/launcher.py`
- New `_build_command(cfg, game, load_state=None)` builds the emulator launch argv. When `load_state` is given, it injects the per-emulator flag and verifies `os.path.isfile()` first — returns `None` if the file vanished (caller falls back to Just Play):
  - PSP: `--fullscreen --state=<path> <game.iso>` (PPSSPP `--state=` is undocumented but parsed in `UI/NativeApp.cpp:641`).
  - PS2: `-fullscreen -batch -statefile <path> <game.iso>` (PCSX2's documented flag).
  - PS3: `--no-gui --fullscreen --savestate <path>` (NO game ISO — the savestate embeds everything; `--fullscreen` requires `--no-gui` per RPCS3 source).
- `launch_game()` now takes `load_state=None` and uses `_build_command`; falls back to a normal boot if the state file disappeared between popup and launch.

### Rewritten: `ui/draw_popup.py`
- New `popup_type = "launch_menu"` draws a vertical 3-option menu with parallelogram buttons (archetype A) — LOAD LAST SAVE STATE (accent), JUST PLAY (near-white), CANCEL (red `(200, 70, 80)`).
- LOAD STATE row is taller (60px vs 50px) to fit a second line showing the truncated save-state filename (`_short_state_name` truncates to 28 chars) without overlapping the label.
- New `_draw_popup_icon()` helper draws three geometric icons via `pygame.gfxdraw` primitives (no unicode glyphs): `play` (filled triangle), `resume` (vertical bar + triangle), `cancel` (X mark from two crossed 2px lines).
- Existing 2-option `launch` and `decrypt` popup bodies preserved (extracted into `_draw_launch_body` and `_draw_decrypt_body` for clarity).
- Popup dimensions: `launch_menu` = 520×380, `decrypt` = 460×240, `launch` = 460×220.

### Extended: `app.py`
- Imported `find_latest_save_state` from `core/savestates`.
- New state on `GameMachine`: `popup_save_state` (path), `popup_option_rects` (list of `(idx, action, rect)`).
- `launch_selected()` now calls `find_latest_save_state()` and selects `popup_type`: `"decrypt"` for first-time encrypted PS3 games, `"launch_menu"` if a save state exists, else `"launch"`.
- New `_popup_activate()` dispatcher: in `launch_menu` it picks LOAD STATE / JUST PLAY / CANCEL; in 2-option popups it preserves the old YES/NO behavior.
- `_confirm_launch(load_state=None)` now accepts an optional save-state path and toasts "loaded save state" when used.
- Rewrote popup input handlers (keyboard / gamepad / mouse / touch) to cycle through 3 options when `popup_type == "launch_menu"` and to hit-test the 3 rects stored on `gm.popup_option_rects`. Fixed a bug where `K_RIGHT` was being checked as `K_DOWN` inside the `K_LEFT/K_RIGHT` branch.

### Extended: `input/gamepad.py`
- Popup axis-repeat now uses up/down navigation for the 3-option `launch_menu` and keeps the old left/right toggle for the 2-option popups.

### Updated wiki pages
- `wiki/emulator_setup.md`: new "Save-State Launch Commands" section with the per-emulator flag table, file location table, and gotchas (RPCS3 `--fullscreen` requires `--no-gui`, PPSSPP `--state=` is undocumented, save-state version drift handling).
- `wiki/smart_features.md`: new §6 "Save-State Launcher Popup" documenting the user-visible behavior and the call flow.
- `wiki/roadmap.md`: new "Level 5 — Save-State Launcher" milestone marked completed.

## [2026-07-18] config | Bump version to v1.1.0 for release
- Updated the version string from `v4` to `v1.1.0` in `ui/draw_header.py` and `ui/draw_settings.py` to match the release version.
- Created and pushed Git tag `v1.1.0` to the remote repository.

## [2026-07-18] doc | Update complete README to reflect modern configuration features
- Updated `README.md` to reflect the latest codebase additions, including the interactive Setup Wizard and the 5-tab Settings Panel.
- Updated the system architecture flow diagram (Mermaid) to include configuration checks, first-run wizard, and Settings Panel pathways.
- Documented the FOLDERS, CONSOLES, DISPLAY, SYSTEM, and ABOUT tabs of the Settings Panel.
- Documented the portable settings and database storage behavior in `playtime.json`.
- Updated the "Adding a New Console" guide to show how to register custom platforms through the GUI.
- Updated the "Roadmap" section in both `README.md` and `wiki/roadmap.md` to mark Level 2, 3, and 4 milestones as completed (box art grid, filter tabs, settings panel, auto-start, lock/shutdown options).

## [2026-07-18] feature | Settings panel with 5 tabs (Folders/Consoles/Display/System/About)
Added a comprehensive Settings button to the header and a tabbed settings modal that consolidates all configuration and system actions in one place. Previously, folder management and custom console setup were only available on the first-run Setup Wizard, grid size was a header button, auto-start was buried in the Exit menu, and power options were only in the Exit menu.

### New file: `ui/draw_settings.py`
- `TABS = ["FOLDERS", "CONSOLES", "DISPLAY", "SYSTEM", "ABOUT"]`
- `draw_settings(gm, now)` draws a 760x560 modal popup with a tab bar, content area, close [X] button, and footer hint.
- `_draw_option_row()` — generic highlighted row with label (left) and optional value (right). Each row registers its hit-rect on `gm.settings_option_rects` so mouse/touch/keyboard/gamepad can all interact with it.
- `_draw_add_button()` — centered "+ ADD ..." button.
- **FOLDERS tab**: lists all configured library folders with delete buttons + an "Add Folder" button (reuses `add_gm_folder_dialog` from `ui/draw_setup.py`).
- **CONSOLES tab**: read-only list of auto-detected standard consoles (PSP/PS2/PS3 + any `_win/_ios` pairs) showing emulator name and game count, followed by editable custom consoles with delete buttons + "Add Custom Console" button.
- **DISPLAY tab**: Grid Size (cycles Small/Medium/Large) and Fullscreen toggle.
- **SYSTEM tab**: Auto-Start toggle, Lock Screen, Restart, Shutdown, Exit Game Machine — consolidates the old Exit menu power actions.
- **ABOUT tab**: Version, library folder, games count, console counts, grid size, fullscreen, auto-start status.

### Modified: `ui/draw_header.py`
- Added a SETTINGS button between CLOCK and EXIT (cyan-themed, matching the settings panel accent).
- Header now has 3 focusable buttons: `header_focus 0=SIZE, 1=SETTINGS, 2=EXIT`.

### Modified: `app.py`
- Added settings state to `__init__`: `settings_active`, `settings_tab`, `settings_sel`, `settings_anim_start`, `settings_tab_rects`, `settings_option_rects`, `settings_close_rect`.
- Added methods: `_show_settings()`, `_close_settings()`, `_settings_switch_tab()`, `_settings_activate()`, `_settings_execute(action)` (dispatches add/delete/toggle/power actions), `_settings_rescan()` (saves settings, refreshes config paths, re-scans consoles/games, rebuilds tabs, starts cover generator thread), `_settings_add_folder()`, `_settings_add_console()`.
- `_show_exit_menu()` now closes settings if open, and `_show_settings()` closes exit menu if open (mutual exclusion).
- `move_sel()` header navigation updated from 2-button toggle to 3-button clamp (`max(0, min(2, ...))`).
- `click()` now checks `settings_rect` after `size_rect`.
- Event handler: added a full settings panel input block (keyboard, gamepad, mouse motion, mouse click, touch) between the exit-menu block and normal input.
- `draw()` now calls `draw_settings(self, now)` after `draw_exit_menu()`.

### Modified: `input/keyboard.py`
- Enter/Space now dispatches: `header_focus 0` → size, `1` → settings, `2` → exit menu.

### Modified: `input/gamepad.py`
- A button now dispatches: `header_focus 0` → size, `1` → settings, `2` → exit menu.
- `update_gamepad_axes()` now checks `settings_active` before the popup check and routes D-pad/analog UP/DOWN to settings option navigation.

Navigation summary: L1/R1 or Q/E or LEFT/RIGHT switches tabs; UP/DOWN navigates options; A/Enter activates; B/Esc/[X] closes.

Verified: `py_compile` clean; all tab labels fit in the tab bar (max 87px < 138px per tab); hint footer (402px) fits in the 760px panel.

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

