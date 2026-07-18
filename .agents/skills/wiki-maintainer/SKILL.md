---
name: wiki-maintainer
description: Manages the LLM Wiki in this workspace, providing workflows for Ingestion, Querying, and Linting.
---

# Wiki Maintainer Skill

This skill outlines the precise steps and workflows for managing the LLM Wiki within the `Game-Machine` workspace.

## 🛠️ Operations

### 1. Ingest Workflow
When a new file is added to `sources/` or you are asked to process a source:

1. **Read and Analyze**: Read the raw source document from `sources/`. Identify core components, emulator details, guides, bugs, and roadmap items.
2. **Determine Wiki Updates**:
   - For each distinct concept, emulator, or architecture layer, determine if it needs a dedicated flat wiki page or if an existing page should be updated.
   - Example pages for Game Machine: `emulator_commands.md`, `folder_structure.md`, `pygame_ui_loop.md`, `resolved_bugs.md`, `roadmap.md`.
3. **Write / Update Pages**:
   - Write pages using clear markdown headers.
   - Include a frontmatter block or metadata footer specifying the source files it depends on and the last updated date.
   - Ensure every page is interlinked with other related pages using absolute `file://` links to make them clickable in the agent workspace.
4. **Update Index**:
   - Edit [index.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md).
   - Add new pages under the appropriate categories.
   - Include a concise one-line summary for each page.
5. **Log the Operation**:
   - Append a new section to [log.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/log.md).
   - Format the header exactly as: `## [YYYY-MM-DD] ingest | <Source Filename>` followed by a brief bulleted list of changes made.

### 2. Query Workflow
When asked an informational or architectural question:

1. **Scan Index**: First, read [index.md](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/index.md) to locate relevant pages.
2. **Read Pages**: Read the specific wiki pages instead of raw files (unless code verification is needed).
3. **Synthesize**: Generate a comprehensive answer referencing the pages read.
4. **Filing Back**: If the answer is a complex analysis, comparison, or new architecture design that would be valuable to preserve, propose saving it as a new wiki page (e.g., `wiki/analysis_x.md`) and updating the index/log accordingly.

### 3. Lint Workflow
To ensure the health of the wiki:

1. **Orphans & Dead Links**: Parse all markdown files in `wiki/`.
   - Verify that all local file links point to files that actually exist.
   - List pages that have no inbound links from other pages (except `index.md`).
2. **Contradictions & Stale Claims**: Review content to see if updates in one page contradict another page (e.g., outdated paths or emulator flags).
3. **Document Gaps**: Suggest new concepts or areas that have been added to the code but are not yet described in the wiki.

## 📋 Wiki Standards

- **Flat Directory**: Save all content pages directly under `wiki/` (e.g., `wiki/resolved_bugs.md`). Do not use subfolders, as this keeps Obsidian and path references simple.
- **Clickable Absolute Paths**: Use absolute `file://` URIs for files: `[Link Text](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/filename.md)`.
- **Source Citations**: Every page must state its source, e.g. `*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*`.
