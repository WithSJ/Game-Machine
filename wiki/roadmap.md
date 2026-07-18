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

## 🔜 Level 2 — Box Art & Cover Grid (In-Progress)
- [ ] Render a cover image grid layout (PS5 dashboard style).
- [ ] Read from a `covers/` directory with pattern `covers\<CONSOLE>\<GAME_NAME>.jpg`.
- [ ] Implement a fallback placeholder box with title text when no cover exists.
- [ ] Add horizontal (Left/Right) D-Pad navigation for grid items.

## 🔜 Level 3 — Console Feel & Assets
- [ ] Filter games by console tabs (using L1/R1 to cycle).
- [ ] Bind "B button" to go back, and "Start button" to options.
- [ ] Add background background music (BGM).
- [ ] Add UI sounds (select, confirm).
- [ ] Build a "Recently Played" section displaying history at the top.

## 🔜 Level 4 — System-Level Console Mode
- [ ] Borderless fullscreen window mode.
- [ ] Configure startup launching (`shell:startup` on Windows).
- [ ] Add a shutdown option in the UI exit menu.
- [ ] Cross-platform compatibility for Linux (using Flatpaks) to deploy on other laptops.

## 💡 Future Concepts
- Automatic internet metadata scraping for cover art and descriptions.
- Text search filter for quick ROM indexing.
- Game playtime tracking (log session durations).
- Multiple controller binding profiles.
- Custom UI themes.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
