# Game Machine Smart Features

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

Game Machine includes several helper functions to improve the gaming console experience.

## 1. Game Name Cleaner (Regex)

Raw game ROMs often contain release tags, regional flags, and numbers (e.g. `0517 - Tekken - Dark Resurrection (USA) (En,Fr,De,Es,It).iso`). A regex-based name cleaner filters these details out for the UI representation:

- **Regex used**:
  - `^\d+\s*-\s*`: Removes leading numbers and dashes (e.g. `0517 - `).
  - `[\(\[].*?[\)\]]`: Removes bracketed and parenthesized tags (e.g. `(USA) (En,Fr,De,Es,It)`).
- **Result**: `Tekken - Dark Resurrection` is displayed.

## 2. Dynamic Scrolling List

For directories containing a large list of ROMs (e.g., 100+ files):
- The UI maintains focus on the active selection by scrolling the list view dynamically.
- The UI header displays a counter of total games and current index: `114 games | 37/114`.

## 3. Console Color Tags

To easily distinguish games in mixed lists, each console is assigned a distinct color tag:
- **PSP**: Blue
- **PS2**: Green
- **PS3**: Orange

## 4. Input Queue Purge

When returning from a game session, the event queue is cleared to prevent accidental double-launches caused by buttons pressed while the emulator was running. See [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md) for details.

## 5. Junk File Filtering

Only files matching configuration extensions (e.g. `.iso`, `.cso`, `.chd`) are ingested, filtering out webp, png, and temporary files that may reside in the directories.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Resolved Bugs](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/resolved_bugs.md)
