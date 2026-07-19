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

## Mandatory Testing Before Git Commit & Push (Applies to EVERY change)

**Testing is mandatory and comes BEFORE any `git add`, `git commit`, or `git push`. No exceptions. A change is not "done" until it has been tested and the user has confirmed the test result.**

### The rule

1. **Test before staging.** After you finish writing/editing code, you MUST run a verification step BEFORE running `git add`. The verification must actually exercise the code you changed — not just `py_compile`. Examples by change type:
   - **Python source change** (`*.py`): at minimum `python -m py_compile <changed_files>`. For UI/draw code, also run an offscreen render test that calls the modified `draw_*` function. For launcher/core logic, run a smoke test that imports the module and calls the changed function with synthetic input.
   - **UI / visual change** (anything under `ui/`): run the offscreen boot test that exercises every `draw_*` path (main screen, launch popup, exit menu, settings panel, setup screen, setup help modal). Verify no `NameError`, no crash, and that the expected pixels render with the correct theme tokens.
   - **Wiki / docs / config change** (`wiki/*.md`, `.agents/*`, `*.json`): verify the file parses (for Markdown, check headers and links; for JSON, run `python -c "import json; json.load(open(...))"`; for YAML frontmatter in skill files, sanity-check the `name:` and `description:` fields).
   - If you don't know what test to run, ASK the user before proceeding.

2. **Report the test result to the user.** Show what you ran, what passed, and what (if anything) failed. If anything failed, fix it and re-test before going further. Do NOT move to step 3 until every test passes.

3. **Ask the user for testing confirmation BEFORE `git add` / `git commit` / `git push`.** Use the `question` tool (or an explicit inline question) and wait for their answer. Suggested phrasing:
   > I've completed the changes and ran these tests: <list>. All passed. Would you like me to test anything else before I commit and push, or proceed with `git commit` + `git push`?
   
   Options to offer: "Proceed with commit + push" / "Run more tests first" / "Hold off — I want to test myself".
   
   - If the user asks for more tests, run them and re-ask.
   - If the user wants to test themselves, STOP and wait. Do not commit until they explicitly say to proceed.
   - If the user says proceed, go to step 4.

4. **Only after the user confirms, run the normal commit + push workflow** (see "Mandatory Change Workflow" below — start at step 2 "Stage the changes").

### Hard rules

- **MUST** run at least one real test before asking the user. Asking the user without having tested first is a violation.
- **MUST NOT** run `git add`, `git commit`, or `git push` until the user has explicitly confirmed.
- **MUST NOT** skip the ask step even for "tiny" or "obvious" changes — the ask is the user's safety net.
- **MUST** report test results truthfully. Never claim a test passed if it failed or wasn't run.
- **MUST** re-test after any post-test edit. If the user asks for a follow-up change, the testing rule restarts from step 1.
- If a test fails, fix the root cause and re-test. Never paper over a failure to get to the commit step.

## Mandatory Change Workflow (Applies to EVERY modification)

**Every time you modify, add, or delete ANY file in the repository - whether code, config, wiki, or docs - you MUST complete ALL of the following steps in order, without exception and without being asked twice:**

1. **Update the wiki**
   - Add a new entry at the TOP of [`wiki/log.md`](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md) describing what changed and why.
   - Use the existing entry format: `## [YYYY-MM-DD] <type> | <short title>` followed by bullet points. `<type>` is one of `feature`, `bugfix`, `refactor`, `config`, `doc`, `ingest`, `system`.
   - If the change affects architecture, file structure, smart features, resolved bugs, emulator setup, or the roadmap, also update the corresponding page under `wiki/` and `wiki/index.md`.
   - Consult the [wiki-maintainer](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md) skill for ingestion/linting workflows when unsure.

2. **Test the change** — follow the "Mandatory Testing Before Git Commit & Push" section above. **Do not proceed to step 3 until the user has confirmed the test result.**

3. **Stage the changes**
   - `git add <files>` - stage every file you touched, including the wiki updates. Never stage files you did not intend to change. Never stage `playtime.json` or anything under `covers/` (both are gitignored for portability/privacy).

4. **Commit with a proper message**
   - Subject line: concise, lowercase prefix matching the log `<type>` (`bugfix:`, `feature:`, `refactor:`, `config:`, `doc:`, `ingest:`, `system:`) followed by a short summary. Keep the subject under ~72 characters.
   - Body: a descriptive paragraph or bullet list explaining what changed, why, and any notable side effects. Reference specific files and line regions when helpful.

5. **Push to remote**
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
