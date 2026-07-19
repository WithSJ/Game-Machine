# Game Machine UI Design Philosophy

This document is the **single source of truth** for how Game Machine looks, feels, and reads. Every new screen, popup, button, list, or animation added to the project MUST follow these rules. The canonical reference implementation is the **Launch Game popup** (`ui/draw_popup.py::_draw_launch_menu_body`) — when in doubt, copy its style.

---

## 1. Visual Language — "Premium Console Dashboard"

Game Machine emulates the visual feel of a modern gaming console dashboard (PS5 / Xbox Series X) running on a TV in a dark room. The aesthetic is:

- **Dark, almost-black background** so cover art and accent colors pop.
- **One accent color per console** that threads through every element tied to that console (tabs, hero, cards, chips, buttons, popup glow line).
- **Slight, deliberate geometry** — parallelogram-cut corners on primary buttons echo the "angular" feel of console UIs (vs. the soft rounded iOS look).
- **Soft glow + pulse** on key edges (hero top edge, popup top accent line) for life without distraction.
- **Heavy type, wide tracking** for titles; **dim monospace** for control hints so they recede until needed.

---

## 2. Color Palette (from `ui/theme.py`)

All colors are RGB tuples. Never introduce new colors outside this palette without adding them to `ui/theme.py` first.

### 2.1 Neutral scale (use these 90% of the time)

| Token | RGB | Use |
|---|---|---|
| `COL_BG`        | `(7, 8, 12)`     | App background — the "void" behind everything |
| `COL_BG_GLOW`   | `(16, 19, 28)`   | Subtle radial glow centers (splash, hero background) |
| `COL_PANEL`     | `(17, 20, 27)`   | Popups, modals, hero banner, cards |
| `COL_PANEL2`    | `(26, 30, 39)`   | Unselected button fill, secondary panels |
| `COL_CARD_BORDER` | `(28, 32, 42)` | 1px border on unselected cards / buttons / rows |
| `COL_FOOT_LINE` | `(23, 26, 34)`   | Footer separator line |
| `COL_TEXT`      | `(238, 240, 244)` | Primary text (titles, selected labels) |
| `COL_DIM`       | `(138, 141, 148)` | Secondary text (unselected labels, values) |
| `COL_DIMMER`    | `(86, 91, 102)`   | Tertiary text (hints, sub-labels, "NEW" timestamp) |

### 2.2 Accent colors (one per console — never mix)

| Token | RGB | Console / Context |
|---|---|---|
| `REC_COLOR` | `(95, 212, 232)`  | RECENTS tab + Setup/Settings accent (cyan) |
| `CONSOLE_COLORS["PSP"]` | `(240, 112, 60)` | PSP — orange |
| `CONSOLE_COLORS["PS2"]` | `(79, 214, 166)`  | PS2 — green |
| `CONSOLE_COLORS["PS3"]` | `(157, 147, 245)` | PS3 — purple |

Auto-detected consoles draw from `EXTRA_COLORS` (pink, gold, cyan, coral, lime) in declaration order.

### 2.3 Functional colors (semantic, never decorative)

| Token | RGB | Meaning |
|---|---|---|
| `COL_PAD_OK` | `(93, 202, 165)` | "Good" — pad connected, NEW badge, A button hint, success |
| `COL_BTN_Y`  | `(250, 199, 117)` | "Caution" — Y button hint, custom console tags, warnings |
| `COL_BTN_B`  | `(240, 149, 149)` | "Destructive" — B button, close [X], error text, cancel |
| Destructive fill | `(200, 70, 80)` | Used for CANCEL/NO button fills (deeper than `COL_BTN_B`) |
| Selected text on accent | `(11, 13, 19)` | Dark text placed on a colored fill for contrast |
| Light text on destructive | `(255, 240, 240)` | Text on red CANCEL buttons |

### 2.4 Color rules

- **MUST** use `mix(c1, c2, t)` from `ui/theme.py` to derive tints/shades. Never hand-pick a "close enough" RGB.
- **MUST NOT** introduce raw RGB tuples in draw code. Always go through a theme token or a `mix()` expression.
- **MUST** keep accent colors per-console consistent across every surface (tab, hero, card border, chip, popup glow, button fill).
- **MUST NOT** use accent colors for body text — they're reserved for highlights, borders, fills, and key labels.

---

## 3. Typography

Fonts are loaded in `app.py::GameMachine.__init__` and stored on `self.f_*`. Two type families only:

| Family | Stack | Role |
|---|---|---|
| **Heavy / Heading** | `"bahnschrift,verdana,arial"` (`FH`) | Titles, button labels, chips, hero, popup headings |
| **Body** | `"verdana,arial"` (`FB`) | Body text, sub-labels, card names, small text |
| **Mono** | `"consolas,couriernew,monospace"` | Control hints, timestamps, file paths |

### Type scale (in points)

| Token | Size | Bold | Use |
|---|---|---|---|
| `f_logo`         | 24 | yes | Header "GAME MACHINE" |
| `f_sub`          | 11 | no  | Header subtitle, taglines |
| `f_clock`        | 17 | yes | Clock |
| `f_tab`          | 16 | yes | Tab labels, panel section headers |
| `f_channel`      | 13 | yes | Hero channel line ("PSP · RECENTLY PLAYED") |
| `f_hero`         | 38 | yes | Hero game title, empty-state headline |
| `f_meta`         | 14 | no  | Hero meta line ("Last played today · 4h 20m played") |
| `f_btn`          | 15 | yes | Button labels in lists / settings rows |
| `f_card`         | 13 | yes | Game card names |
| `f_chip`         | 10 | yes | Console chips, badges, sub-labels inside buttons |
| `f_small`        | 12 | no  | Body text, status, warnings |
| `f_hint`         | 12 | no  | Footer hint labels |
| `f_mono`         | 11 | no  | Control hint strings, timestamps, file paths |
| `f_popup_title`  | 22 | yes | Modal/popup titles ("LAUNCH GAME?", "SETTINGS") |
| `f_popup_name`   | 18 | yes | Game name inside a popup |
| `f_popup_btn`    | 15 | yes | Button labels inside popups |

### Type rules

- **MUST** use the Bahnschrift stack for any "branded" feel (headings, buttons, chips).
- **MUST** use the mono stack only for control hints, codes, and paths — never for prose.
- **MUST** use `spaced_text()` (from `ui/helpers.py`) for wide-tracked headings (logo, hero channel).
- **MUST NOT** introduce new font sizes — pick from the scale above. If a new size is truly needed, add a token to `app.py::__init__` and document it here.

---

## 4. Button Taxonomy — three archetypes, no others

Every interactive button in Game Machine is one of exactly three archetypes. New buttons MUST pick the archetype that matches their semantic role.

### 4.1 Archetype A — Parallelogram Action Button (primary actions)

Used for: the most important action on a surface — hero PLAY, popup YES/LOAD STATE/JUST PLAY, setup wizard menu items, primary power-menu choices.

**Visual recipe** (from `ui/helpers.py::parallelogram`):

```
       ┌──────────────────────────┐
       │                          │
       │  ▶  LABEL                │   ← parallelogram, cut=8–10
       │                          │
       └──────────────────────────┘
```

| State | Fill | Border | Text color | Icon color |
|---|---|---|---|---|
| **Selected** | accent color (or `(231,233,238)` for neutral actions) | none (filled solid) | `(11, 13, 19)` dark (or `(255, 240, 240)` on red) | same as text |
| **Unselected** | `COL_PANEL2` | 1px `COL_CARD_BORDER` (parallelogram outline) | `COL_DIM` | `COL_DIMMER` |
| **Destructive selected** | `(200, 70, 80)` | none (filled solid) | `(255, 240, 240)` | same as text |

Code pattern (canonical example: `ui/draw_popup.py::_draw_launch_menu_body`):

```python
if on:
    parallelogram(scr, r, col, cut=10)
    text_col = (255, 240, 240) if action == ACT_CANCEL else (11, 13, 19)
    icon_col = text_col
else:
    parallelogram(scr, r, COL_PANEL2, cut=10)
    parallelogram(scr, r, COL_CARD_BORDER, cut=10, width=1)
    text_col = COL_DIM
    icon_col = COL_DIMMER
```

**Rules:**
- `cut` (corner offset) is **8** for small buttons, **10** for popup-sized buttons.
- Button height: **38px** (hero), **42–50px** (popup), **48px** (setup wizard).
- A geometric icon (drawn with `pygame.gfxdraw` primitives) sits **24–28px from the left edge**, vertically centered. The label starts **24px** right of the icon.
- **MUST** draw icons with `pygame.gfxdraw.filled_polygon` + `aapolygon` or `pygame.draw.line` — never rely on unicode glyphs (`▶`, `↻`, `✕`) which may be missing from Bahnschrift.
- **MUST** use `gm.f_popup_btn` (15pt bold) for the label.

### 4.2 Archetype B — Rounded Rect Chip Button (secondary / header / tab)

Used for: header buttons (SIZE, SETTINGS, EXIT), tab pills, settings tab pills, console chips, badges.

```
   ╭──────────────╮
   │   SIZE: M    │     ← rounded rect, border_radius=6
   ╰──────────────╯
```

| State | Fill | Border | Text |
|---|---|---|---|
| **Focused / hovered** | `COL_PANEL2` | **2px** in the accent color | accent color or `COL_TEXT` |
| **Unfocused** | `COL_PANEL2` | 1px `COL_CARD_BORDER` | `COL_DIM` |

Code pattern (from `ui/draw_header.py`):

```python
pygame.draw.rect(scr, COL_PANEL2, rect, border_radius=6)
if focused:
    pygame.draw.rect(scr, accent, rect, 2, border_radius=6)
else:
    pygame.draw.rect(scr, COL_CARD_BORDER, rect, 1, border_radius=6)
scr.blit(label, label.get_rect(center=rect.center))
```

**Rules:**
- `border_radius`: **3** for chips, **4** for badges, **6** for header buttons, **8** for tab pills.
- Height: **28px** (header), **34px** (tab pills), **18–20px** (chips).
- Text is **always centered**.
- Focused border is always **2px**; unfocused is always **1px**.

### 4.3 Archetype C — List Option Row (settings / menus)

Used for: settings panel rows, exit/power menu options, any selectable vertical list inside a modal.

```
   ┌────────────────────────────────────────────┐
   │ ▎  LABEL                          VALUE    │   ← rounded rect, border_radius=8
   └────────────────────────────────────────────┘
       ↑ 3px left accent bar (selected only)
```

| State | Fill | Border | Left bar | Label color | Value color |
|---|---|---|---|---|---|
| **Selected** | `mix(COL_BG, accent, 0.25)` | **2px** accent | 3px wide, accent color, 6px padding top/bottom | `(231, 233, 238)` | accent |
| **Unselected** | `COL_PANEL2` | 1px `COL_CARD_BORDER` | none | `COL_DIM` | `COL_DIMMER` |

Code pattern (from `ui/draw_settings.py::_draw_option_row`):

```python
if on:
    pygame.draw.rect(scr, mix(COL_BG, col, 0.25), r, border_radius=8)
    pygame.draw.rect(scr, col, r, 2, border_radius=8)
    pygame.draw.rect(scr, col, (r.x, r.y + 6, 3, r.h - 12))   # left accent bar
else:
    pygame.draw.rect(scr, COL_PANEL2, r, border_radius=8)
    pygame.draw.rect(scr, COL_CARD_BORDER, r, 1, border_radius=8)
```

**Rules:**
- `border_radius=8`.
- Height: **44px** (settings rows), **48px** (system actions), **56px** (display rows with values).
- Label uses `gm.f_btn` (15pt bold), 16px left padding, vertically centered.
- Optional value (right-aligned, 16px right padding) uses `gm.f_small` (12pt) in accent (selected) or `COL_DIMMER` (unselected).
- **MUST** append `(action, rect)` to the appropriate `*_option_rects` list on `gm` so input handlers can hit-test.

---

## 5. Popup / Modal Pattern

Every modal in Game Machine (launch popup, decrypt popup, exit menu, settings panel, setup help) follows the same recipe. New modals MUST follow it too.

### 5.1 Anatomy

```
   ┌──────────────────────────────────────────────┐  ← 3px accent glow line at top
   │                                              │
   │                LAUNCH GAME?                   │  ← f_popup_title, accent color, centered
   │                                              │
   │                 Wipeout Pulse                 │  ← f_popup_name, COL_TEXT, centered
   │                                              │
   │                  ╭ PSP ╮                     │  ← console chip, accent border, centered
   │                                              │
   │   A save state was found for this game       │  ← f_small, COL_DIM, centered subtitle
   │                                              │
   │   ┌──────────────────────────────────────┐   │
   │   │ ▎▎  ▶  LOAD LAST SAVE STATE          │   │  ← archetype A buttons (parallelogram)
   │   │       ULUS12345_1.00_3.ppst          │   │     ↑ first option is the default selection
   │   └──────────────────────────────────────┘   │
   │   ┌──────────────────────────────────────┐   │
   │   │      ▶  JUST PLAY                    │   │
   │   └──────────────────────────────────────┘   │
   │   ┌──────────────────────────────────────┐   │
   │   │      ✕  CANCEL                        │   │
   │   └──────────────────────────────────────┘   │
   │                                              │
   │     ▲▼ Navigate   A=Confirm   B/Esc=Cancel   │  ← f_mono, COL_DIMMER, centered hint
   └──────────────────────────────────────────────┘
        ↑ 1px border: mix(COL_BG, accent, 0.4)
        ↑ fill: COL_PANEL, border_radius=14
```

### 5.2 Construction rules

1. **Dark overlay** — `pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)`, fill `(0, 0, 0, int(160 * scale))`.
2. **Panel** — `pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=14)`.
3. **Accent glow line** — 3px tall accent-colored rect at the top, same `border_radius=14`.
4. **Border** — 1px in `mix(COL_BG, accent, 0.4)`.
5. **Scale-in animation** — `ease_out(anim_p)` over **200–220ms**. While `scale < 0.95`, draw a simplified scaled panel; only draw full content once `scale >= 0.95`.
6. **Title** — `f_popup_title` (22pt bold), accent color, horizontally centered, 24px from top.
7. **Body** — game name, console chip, subtitle, then action buttons.
8. **Hint** — `f_mono` (11pt), `COL_DIMMER`, centered, 22px from bottom. Always documents every input binding for the modal.

### 5.3 Popup dimensions (per current type)

| Type | Width × Height | Use |
|---|---|---|
| `launch` (2-option) | 460 × 220 | No save state exists |
| `decrypt` (2-option) | 460 × 240 | PS3 first-time decrypt prompt |
| `launch_menu` (3-option) | 520 × 380 | Save state exists — has the taller LOAD STATE row |
| `decryption_progress` | 500 × 240 | During decryption (pulsing bar) |
| `exit_menu` | 420 × 370 | Power menu (4 options + autostart toggle) |
| `settings` | 760 × 560 | 5-tab settings panel |
| `setup_help` | 780 × 520 | File structure help modal |

---

## 6. Console Chip Pattern

Used in hero, popup, grid card, settings to tag a game's console.

```
   ╭ PSP ╮     ← 1px border, border_radius=4
   ╰─────╯
```

| Element | Value |
|---|---|
| Fill | `mix(COL_BG, accent, 0.25)` |
| Border | 1px, same mixed color (slightly darker than fill) |
| `border_radius` | 4 |
| Height | 18–20px |
| Width | `text_width + 14` |
| Text | `f_chip` (10pt bold), accent color, centered |
| Padding | small chip text inside the rounded rect |

Code (from `ui/draw_popup.py`):

```python
chip_s = gm.f_chip.render(g["console"], True, accent)
chip_r = pygame.Rect(popup_r.x + (pw - chip_s.get_width() - 14) // 2,
                     popup_r.y + 98, chip_s.get_width() + 14, 20)
pygame.draw.rect(scr, mix(COL_BG, accent, 0.25), chip_r, 1, border_radius=4)
scr.blit(chip_s, chip_s.get_rect(center=chip_r.center))
```

---

## 7. Hint / Footer Pattern

Every modal and the main footer MUST end with a hint line documenting all valid inputs.

- **Font**: `f_mono` (11pt).
- **Color**: `COL_DIMMER` — recedes until the user looks for it.
- **Alignment**: horizontally centered, 22–24px from the bottom edge.
- **Format**: glyph + action pairs separated by 3 spaces. Example: `▲▼ Navigate   A = Confirm   B / Esc = Cancel   ◄ ► = Switch`.
- **Footer key hints** (main screen, `draw_footer.py`) use the `key_hint()` helper: a 9px-radius circle with the letter inside, color-coded by function:
  - **A** → `COL_PAD_OK` (green) — Play / confirm
  - **B** → `COL_BTN_B` (red) — Back / cancel
  - **Y** → `COL_BTN_Y` (yellow) — Random / special
  - **S** → `COL_TEXT` (white) — Size
  - **L1 R1** → `COL_DIM` pill — Tab switch

---

## 8. Iconography

Icons are **always drawn geometrically** with `pygame.gfxdraw` or `pygame.draw` primitives. Never use unicode glyphs (`▶`, `✕`, `↻`, `★`) in button/chip labels — Bahnschrift's fallback chain is unreliable across Windows installs and you'll get tofu boxes.

### Canonical icons (defined in `ui/draw_popup.py::_draw_popup_icon`)

| Name | Use | Construction |
|---|---|---|
| `play`   | JUST PLAY button, hero PLAY | Filled triangle pointing right, ~14px tall |
| `resume` | LOAD LAST SAVE STATE | Vertical bar on the left + play triangle (the standard "resume from bookmark" glyph) |
| `cancel` | CANCEL button | X mark — two crossed 2px lines, 7px from center |
| diamond  | GAME MACHINE logo | 4-point diamond, 10px wide, orange `(240, 112, 60)` |

### Rules

- **MUST** use `pygame.gfxdraw.filled_polygon` + `aapolygon` for filled shapes (gives anti-aliased edges).
- **MUST** use `pygame.draw.line(..., 2)` for stroke-only icons (X mark) and draw twice for a clean look.
- **MUST NOT** use text glyphs as icons. If you need a new icon, add a `kind` branch to `_draw_popup_icon` or a new helper in `ui/helpers.py`.

---

## 9. Spacing & Layout

| Token | Value | Use |
|---|---|---|
| `PAD_X` | 44 | Left/right margin of every full-width section (header, tabs, hero, grid, footer) |
| `GAP` | 14 | Grid card gap (also used as panel section padding) |
| `HERO_RECT` | `(PAD_X, 122, SCREEN_W - 2*PAD_X, 172)` | Hero banner area |
| `GRID_RECT` | `(PAD_X, 310, SCREEN_W - 2*PAD_X, <computed>)` | Game grid area |
| `FOOTER_Y` | `SCREEN_H - 52` | Footer separator Y |

### Internal popup spacing

- Title to game name: **40px**
- Game name to console chip: **4px**
- Console chip to subtitle: **8px**
- Subtitle to first button: **10–20px**
- Button to button: **14px** (vertical stack) or **24px** (horizontal pair)
- Last button to hint: **~22px**

### Grid card spacing

- Cover art to text area: **8px**
- Text area to bottom chip: padded from bottom by **26px**
- Card border: **10px radius**, **1px** unselected / **accent + 2px top stripe** selected

---

## 10. Animation Principles

Game Machine animations are **subtle, slow, and ease-out**. The UI never feels twitchy.

1. **Popup scale-in**: 200–220ms, `ease_out(p) = 1 - (1 - p)**3`. While `scale < 0.95`, draw only a simplified panel; switch to full content at `scale >= 0.95`.
2. **Tab switch slide**: 420ms (`TAB_ANIM_MS`), 26px horizontal offset that fades to 0 with `ease_out`.
3. **Hero pulse**: 950ms sine wave, 0.55–1.0 amplitude, drawn as a 24-segment gradient along the top edge.
4. **Toast slide-up**: 250ms, `ease_out`, 12px upward slide.
5. **Loading bar**: 1200ms linear sweep (splash), 180ms sine pulse (decrypt progress).
6. **Ambient particles**: 90 dots, 0.1–0.45 px/frame upward drift, sine-modulated alpha (0.25–0.6).

**Rules:**
- **MUST** use `ease_out` from `ui/theme.py` for any enter animation.
- **MUST NOT** use linear motion for organic UI (linear is OK for progress bars only).
- **MUST NOT** animate colors or text content — only position, scale, and alpha.

---

## 11. Input Binding Conventions

Every interactive surface in Game Machine supports four input modalities. New modals MUST wire all four:

| Modality | Confirm | Cancel | Navigate | Tab switch |
|---|---|---|---|---|
| Keyboard | `Enter` / `Space` / `K_RETURN` / `K_KP_ENTER` | `Esc` | `↑ ↓ ← →` (and `W A S D`) | `Q E` / `[ ]` / `L1 R1` (settings) |
| Gamepad | Button `0` (A) | Button `1` (B) | D-pad / left stick axis | Buttons `4 / 5` (L1 / R1) |
| Mouse | Left click inside a hit-rect | (varies) | Hover to focus | Click on tab pill |
| Touch | `FINGERUP` inside a hit-rect (no drag) | (varies) | n/a | Tap on tab pill |

**Rules:**
- **MUST** flush the Pygame event queue after returning from a game (`pygame.event.clear()` in `core/launcher.py`) so stale button presses don't double-trigger.
- **MUST** set `gm.ignore_input_until = pygame.time.get_ticks() + 1000` after launching a game to absorb the OS focus-return events.
- **MUST** always honor `pygame.QUIT` even during the post-launch freeze.
- **MUST** respect `gm.touch_moved` — a finger that dragged more than `TAP_SLOP` (12px) is a scroll, not a tap.
- **MUST** register every hit-rect on the appropriate `gm.*_rects` list during draw so input handlers can hit-test next frame.

---

## 12. MUST / MUST NOT — Quick Reference

### MUST

- Source colors from `ui/theme.py` tokens or `mix()` expressions.
- Use exactly one of the three button archetypes (A parallelogram, B rounded chip, C list row).
- Draw icons geometrically with `pygame.gfxdraw` — no unicode glyphs as icons.
- End every modal with a `f_mono` / `COL_DIMMER` hint line documenting inputs.
- Use `ease_out` for enter animations; total duration 200–420ms.
- Register hit-rects during draw so input handlers can hit-test.
- Wire all four input modalities (keyboard / gamepad / mouse / touch).
- Set `gm.ignore_input_until` after launching a game.
- Thread the active console's accent color through every element tied to that console.
- Use `parallelogram()` from `ui/helpers.py` for archetype A buttons.
- Update `wiki/log.md` and the relevant wiki page after any UI change.

### MUST NOT

- Introduce raw RGB tuples in draw code.
- Add new font sizes without a token in `app.py::__init__`.
- Use unicode glyphs (`▶`, `✕`, `↻`, `★`) as icons.
- Mix accent colors across consoles on the same surface.
- Use linear motion for organic UI animations.
- Animate colors or text content (only position / scale / alpha).
- Hard-code screen coordinates — use `SCREEN_W`, `SCREEN_H`, `PAD_X`, `HERO_RECT`, `GRID_RECT`, `FOOTER_Y`.
- Add a new modal that doesn't follow the popup anatomy in §5.
- Forget the close [X] button on modals (top-right, 26×26, `COL_BTN_B` border on hover).
- Commit `playtime.json` or anything under `covers/` (both gitignored).

---

## 13. Reference Implementations

When extending the UI, copy from these canonical files:

| Want to build... | Copy from |
|---|---|
| A popup with multiple choices | `ui/draw_popup.py::_draw_launch_menu_body` |
| A 2-option YES/NO popup | `ui/draw_popup.py::_draw_launch_body` |
| A tabbed settings panel | `ui/draw_settings.py` |
| A vertical power menu | `ui/draw_exit_menu.py` |
| A header chip button | `ui/draw_header.py` (SIZE / SETTINGS / EXIT) |
| A console chip tag | `ui/draw_popup.py` (console chip under game name) |
| A geometric icon | `ui/draw_popup.py::_draw_popup_icon` |
| A footer key hint | `ui/draw_footer.py` + `ui/helpers.py::key_hint` |
| A splash / loading screen | `ui/draw_splash.py` |
| A toast notification | `ui/draw_toast.py` |
| A setup wizard with two columns | `ui/draw_setup.py` |

---

## 14. Adding a New Screen — Checklist

Before opening a PR / committing a new screen, verify every box:

- [ ] Colors sourced from `ui/theme.py` tokens or `mix()` expressions
- [ ] Fonts picked from the type scale in §3
- [ ] Buttons match one of the three archetypes (A / B / C)
- [ ] Icons drawn with `pygame.gfxdraw` primitives — no unicode glyphs
- [ ] Modal (if any) follows the popup anatomy in §5
- [ ] Scale-in animation uses `ease_out`, 200–220ms
- [ ] Hint line at the bottom documents all inputs in `f_mono` / `COL_DIMMER`
- [ ] All four input modalities wired (keyboard / gamepad / mouse / touch)
- [ ] Hit-rects registered on `gm.*_rects` lists during draw
- [ ] No raw RGB tuples, no hardcoded screen coordinates
- [ ] `wiki/log.md` updated with a `## [YYYY-MM-DD] feature | ...` entry
- [ ] Relevant wiki page (smart_features, roadmap, this one) updated
- [ ] `wiki/index.md` link added if a new wiki page was created

---

*Last updated: 2026-07-19*
