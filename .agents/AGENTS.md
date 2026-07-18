# Game Machine Workspace Rules

This file defines style guidelines and behavioral constraints for agents working on the Game Machine codebase.

## The LLM Wiki System

We maintain a persistent, compounding knowledge base under `wiki/` powered by raw source materials stored under `sources/`.

1. **Consult first**: Before answering architectural questions or starting changes, read `wiki/index.md` and check the relevant wiki pages.
2. **Co-evolution**: Keep the wiki in sync with codebase modifications. When you add features or refactor code, update the corresponding wiki pages.
3. **Operations**:
   - For ingestion, querying, and linting, refer to the custom skill [wiki-maintainer](file:///c:/Users/jadam/Desktop/Game-Machine/.agents/skills/wiki-maintainer/SKILL.md).
   - Log all operations chronologically in [log.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md).
   - Keep the [index.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md) fully up-to-date.

## Git Commit & Push Rule

1. **Automatic Commits**: Every time you modify, add, or delete any file in the repository, you must stage and commit the changes.
2. **Proper Messages**: The commit message must include a concise subject line and a descriptive body summarizing what was changed and why.
3. **Push to Remote**: After making the commit, push the changes to the remote GitHub repository (`origin`).
