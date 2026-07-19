---
name: ui-design-philosophy
description: The single source of truth for Game Machine's visual design, button taxonomy, color palette, typography, and animation rules. MUST be consulted before any UI change, new screen, popup, button, or animation is added.
---

# UI Design Philosophy Skill

This skill enforces visual consistency across Game Machine. Before writing or modifying any file under `ui/`, drawing code in `core/`/`input/`, or anything that renders pixels to the screen, you MUST follow this workflow.

## 📐 When to load this skill

Load this skill any time you are asked to:
- Build, redesign, or extend any UI screen, popup, modal, button, list, or animation
- Add a new console, theme color, or font size
- Change spacing, layout, or animation timing
- Refactor any file under `ui/` (including `draw_*.py`, `theme.py`, `helpers.py`)
- Add an icon, badge, chip, or hint
- Review or critique UI work done by another agent

## 🧭 Workflow

1. **Read the philosophy** — open [`wiki/ui_design_philosophy.md`](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/ui_design_philosophy.md) and read it end-to-end. It is short (~600 lines) and prescriptive.

2. **Identify the archetype** — for any new button, pick exactly one of:
   - **A — Parallelogram Action Button** (primary action on a surface): hero PLAY, popup choices, setup menu items. See §4.1.
   - **B — Rounded Rect Chip Button** (secondary / header / tab): header buttons, tab pills, console chips. See §4.2.
   - **C — List Option Row** (selectable vertical list rows): settings, exit menu. See §4.3.

3. **Pick colors from the palette** — never invent new RGB tuples. Use tokens from `ui/theme.py` or `mix(c1, c2, t)`. See §2.

4. **Pick a font from the scale** — never introduce a new font size without adding a token in `app.py::__init__` and updating the philosophy doc. See §3.

5. **Draw icons geometrically** — use `pygame.gfxdraw.filled_polygon` + `aapolygon` or `pygame.draw.line`. Never use unicode glyphs (`▶`, `✕`, `↻`) as icons. See §8.

6. **Follow the popup anatomy** — any new modal MUST follow §5: dark overlay → COL_PANEL + 14px radius → 3px accent top line → 1px `mix(COL_BG, accent, 0.4)` border → centered title → body → hint at bottom.

7. **Wire all four input modalities** — keyboard, gamepad, mouse, touch. Register hit-rects during draw. See §11.

8. **Animate with `ease_out`** — 200–220ms for popups, 420ms for tab switches. Never linear for organic motion. See §10.

9. **Run the checklist in §14** before committing.

10. **Update the wiki** — every UI change gets a new entry at the top of `wiki/log.md`, and if the philosophy itself changed, update `wiki/ui_design_philosophy.md` and `wiki/index.md`.

## 🚫 Hard rules (never violate)

- No raw RGB tuples in draw code.
- No unicode glyphs as icons.
- No new font sizes without a token.
- No modal without the close [X] button (top-right, 26×26, `COL_BTN_B` border on hover).
- No linear motion for organic animations.
- No mixed accent colors across consoles on the same surface.
- No hardcoded screen coordinates — use `SCREEN_W`, `SCREEN_H`, `PAD_X`, `HERO_RECT`, `GRID_RECT`, `FOOTER_Y`.
- No commit of `playtime.json` or anything under `covers/` (both gitignored).

## 📚 Canonical reference implementations

When extending the UI, copy from these files (also listed in §13 of the philosophy):

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

## 🔗 Related resources

- The full philosophy: [`wiki/ui_design_philosophy.md`](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/ui_design_philosophy.md)
- Workspace rules: [`.agents/AGENTS.md`](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/AGENTS.md)
- Wiki maintainer skill: [`wiki-maintainer`](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md)
