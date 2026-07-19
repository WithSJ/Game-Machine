# Game Machine Workspace Rules

This file defines style guidelines and behavioral constraints for agents working on the Game Machine codebase.

## The LLM Wiki System

We maintain a persistent, compounding knowledge base under `wiki/` powered by raw source materials stored under `sources/`.

1. **Consult first**: Before answering architectural questions or starting changes, read `wiki/index.md` and check the relevant wiki pages.
2. **Co-evolution**: Keep the wiki in sync with codebase modifications. When you add features or refactor code, update the corresponding wiki pages.
3. **Operations**:
   - For ingestion, querying, and linting, refer to the custom skill [wiki-maintainer](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md).
   - Log all operations chronologically in [log.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md) (latest entries on top).
   - Keep the [index.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md) fully up-to-date.

## Mandatory Change Workflow (Applies to EVERY modification)

**Every time you modify, add, or delete ANY file in the repository - whether code, config, wiki, or docs - you MUST complete ALL of the following steps in order, without exception and without being asked twice:**

1. **Update the wiki**
   - Add a new entry at the TOP of [`wiki/log.md`](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md) describing what changed and why.
   - Use the existing entry format: `## [YYYY-MM-DD] <type> | <short title>` followed by bullet points. `<type>` is one of `feature`, `bugfix`, `refactor`, `config`, `doc`, `ingest`, `system`.
   - If the change affects architecture, file structure, smart features, resolved bugs, emulator setup, or the roadmap, also update the corresponding page under `wiki/` and `wiki/index.md`.
   - Consult the [wiki-maintainer](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md) skill for ingestion/linting workflows when unsure.

2. **Stage the changes**
   - `git add <files>` - stage every file you touched, including the wiki updates. Never stage files you did not intend to change. Never stage `playtime.json` or anything under `covers/` (both are gitignored for portability/privacy).

3. **Commit with a proper message**
   - Subject line: concise, lowercase prefix matching the log `<type>` (`bugfix:`, `feature:`, `refactor:`, `config:`, `doc:`, `ingest:`, `system:`) followed by a short summary. Keep the subject under ~72 characters.
   - Body: a descriptive paragraph or bullet list explaining what changed, why, and any notable side effects. Reference specific files and line regions when helpful.

4. **Push to remote**
   - `git push origin main` (or the current branch). Confirm the push succeeds before reporting the task as done.

**Rules of thumb**
- One logical change = one commit. If a request spans multiple unrelated fixes, split into multiple commits.
- Never commit secrets, keys, BIOS files, ISOs, or `playtime.json`.
- Never use `--no-verify`, `--amend` on an already-pushed commit, force-push, or squash-pushed-history unless the user explicitly asks.
- If a commit fails (e.g. a hook rejects it), fix the root cause and create a new commit - do not amend the failed one.
- The workflow is mandatory even for tiny edits: a one-line fix still gets a log entry, a commit, and a push.

## Mandatory UI Design Workflow (Applies to ANY UI / visual change)

**Every time you add, modify, or refactor any file under `ui/`, any `draw_*` function, anything that renders pixels to the screen, or anything that adds a button / popup / icon / animation / color / font size — you MUST follow this workflow without exception:**

1. **Load the UI Design Philosophy skill first** — `.agents/skills/ui-design-philosophy/SKILL.md` (or `wiki/ui_design_philosophy.md` directly). Read it end-to-end before writing any draw code.
2. **Pick the correct button archetype** (A parallelogram / B rounded chip / C list row) per §4 of the philosophy. Never invent a fourth archetype.
3. **Source colors from `ui/theme.py` tokens or `mix()`** — no raw RGB tuples in draw code.
4. **Pick fonts from the existing type scale** in `app.py::__init__` — no new sizes without a token and a philosophy update.
5. **Draw icons geometrically** with `pygame.gfxdraw` primitives — never use unicode glyphs (`▶`, `✕`, `↻`) as icons.
6. **Follow the popup anatomy** in §5 for any new modal: dark overlay → `COL_PANEL` + 14px radius → 3px accent top line → 1px `mix(COL_BG, accent, 0.4)` border → centered title → body → `f_mono` hint at bottom.
7. **Wire all four input modalities** (keyboard / gamepad / mouse / touch) and register hit-rects during draw.
8. **Animate with `ease_out`** — 200–220ms for popups, 420ms for tab switches. Never linear for organic motion.
9. **Run the §14 checklist** in the philosophy doc before committing.
10. **Update `wiki/log.md`** with a `## [YYYY-MM-DD] feature | ...` entry at the top, and if the philosophy itself changed, update `wiki/ui_design_philosophy.md` and `wiki/index.md`.

If you are unsure whether a change counts as a "UI change", it does. When in doubt, load the skill.

## Related Resources
- [UI Design Philosophy Skill](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/ui-design-philosophy/SKILL.md)
- [UI Design Philosophy (wiki)](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/ui_design_philosophy.md)
- [Wiki Maintainer Skill](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md)
- [Wiki Index](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md)
- [Wiki Log](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md)
