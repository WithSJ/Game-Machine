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

## Related Resources
- [Wiki Maintainer Skill](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md)
- [Wiki Index](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md)
- [Wiki Log](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md)
