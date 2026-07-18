# Game Machine Roadmap

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

The roadmap details the levels of development for Game Machine, tracking the completed and planned improvements to the console experience.

## ✅ Level 1 — Core Functionality (Completed)
- [x] Multi-console scanning (PSP, PS2, PS3).
- [x] Keyboard & gamepad UI navigation.
- [x] Regex-based game name cleaning.
- [x] Dynamic scrolling list with index counters.
- [x] Console-specific color tagging.
- [x] Auto-relaunch bug fix.
- [x] Portable mode execution with proper `cwd`.

## ✅ Level 2 — Box Art & Cover Grid (Completed)
- [x] Render a cover image grid layout (PS5 dashboard style).
- [x] Read from a `covers/` directory resolved dynamically under the library base folder.
- [x] Implement a fallback placeholder box with title text when no cover exists.
- [x] Add horizontal (Left/Right) D-Pad/keyboard navigation for grid items.

## ✅ Level 3 — Console Feel & Settings (Completed)
- [x] Filter games by console tabs (using L1/R1 or Q/E to cycle).
- [x] Unified Settings Panel modal with 5 tabs (Folders, Consoles, Display, System, About).
- [x] Interactive first-run Setup Wizard to configure paths and custom consoles.
- [x] Playtime tracking & database key merging across directories.

## ✅ Level 4 — System-Level Console Mode (Completed)
- [x] Borderless fullscreen window mode toggling.
- [x] Configure startup launching via Windows Auto-Start Registry.
- [x] Add lock, shutdown, restart, and exit options in the UI Settings/System menu.

## 🔜 Future Concepts & WIP
- [ ] UI sounds (select, confirm) and background music (BGM).
- [ ] Text search filter for quick ROM indexing.
- [ ] Cross-platform compatibility for Linux (using Flatpaks) to deploy on Steam Deck/other laptops.
- [ ] Multiple controller binding profiles.
- [ ] Custom UI themes.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
