# 🎮 GAME MACHINE — Custom Emulator Frontend (Complete Documentation)

**Project:** Khud ka gaming console UI (custom frontend)
**Platform:** Windows (D:\Game Machine)
**Language:** Python + PyGame
**Status:** v2 working — PSP + PS2 + PS3 games ek hi UI se launch ho rahi hain
**Last updated:** 15 July 2026

---

## Part 1: Idea Kya Hai (The Vision)

Ek hi software jise kholte hi **console jaisa fullscreen UI** khule, jisme:

- Saari games ek jagah dikhein — chahe wo PSP ki ho, PS2 ki ya PS3 ki
- Poora UI **gamepad se control** ho (D-pad se navigate, A se launch)
- Game select karo → sahi emulator apne aap khule → game band karo → wapas UI pe
- User ko kabhi pata hi na chale ki peeche alag-alag emulators chal rahe hain
- Feel bilkul PlayStation/Steam Deck jaisi ho

**Ye concept industry me "Emulation Frontend" kehlata hai** (jaise ES-DE, RetroBat,
LaunchBox). Humne ready-made use karne ki jagah **khud ka banaya** — learning +
full control ke liye.

### Frontend ka Core Principle

> Frontend khud koi game nahi chalata. Wo sirf ek sundar remote control hai
> jo sahi time pe sahi emulator ko sahi game ke saath launch karta hai.

Iske sirf 3 kaam hain:

1. **SCAN** — game folders padho, files ki list banao
2. **SHOW** — list ko sundar UI me dikhao, gamepad se navigation do
3. **LAUNCH** — select hone par ek command chalao, game band hone tak wait karo

Bas. Yahi poora magic hai.

---

## Part 2: Current File System Structure

```
D:\Game Machine\
│
├── my_console.py                ← ⭐ HAMARA FRONTEND (main software)
│
├── PPSSPP_win\                  ← PSP Emulator (portable)
│   ├── PPSSPPWindows64.exe      ← launch hone wala exe
│   ├── PPSSPPWindows.exe        (32-bit version, use nahi karte)
│   ├── assets\                  (emulator ke internal resources)
│   └── memstick\                ← PSP ki "memory card"
│       └── PSP\
│           ├── SAVEDATA\        ← game saves yahan bante hain
│           ├── PPSSPP_STATE\    ← save states yahan
│           └── SYSTEM\          ← ppsspp.ini (settings) + shader cache
│
├── PPSSPP_ios\                  ← PSP GAMES (~100 games)
│   └── *.iso / *.cso            (GTA VCS, Tekken 6, God of War, etc.)
│
├── PCSX2_win\                   ← PS2 Emulator (portable)
│   ├── pcsx2-qt.exe             ← launch hone wala exe
│   ├── portable\                ← ye folder = portable mode ON
│   ├── bios\                    ← PS2 BIOS files (zaruri!)
│   │   ├── SCPH-70004_BIOS_V12_PAL_200.BIN
│   │   ├── scph39001.bin, scph10000.bin, etc.
│   └── resources\, docs\, translations\ (internal)
│
├── PCSX2_ios\                   ← PS2 GAMES (10 games)
│   └── *.iso                    (GTA SA, God of War I/II, RE4, NFS UG2...)
│
├── RPCS3_win\                   ← PS3 Emulator (portable)
│   ├── rpcs3.exe                ← launch hone wala exe
│   ├── dev_flash\               ← PS3 firmware yahan installed hai
│   ├── dev_hdd0\                ← PS3 ki virtual hard disk (saves, trophies)
│   ├── config\                  ← settings + gamepad configs
│   ├── cache\                   ← compiled shaders/PPU modules (auto-banta hai)
│   └── savestates\              ← RPCS3 ke save states
│
├── RPCS3_ios\                   ← PS3 GAMES (1 game)
│   └── Dante's Inferno.iso
│
├── PS_Firmwares\                ← BIOS/Firmware backups
│   ├── ps2-bios-all-bios.zip
│   └── PS3\PS3UPDAT.PUP         ← PS3 firmware installer
│
├── ppsspp_win.zip               (original downloads - delete kar sakte ho)
├── pcsx2-v2.6.3-windows-x64-Qt.7z
└── rpcs3-v0.0.41-...-win64.7z
```

### Structure ka Pattern (Naya console add karne ka formula)

Har console ke liye bas 2 cheezein chahiye:

| Folder | Kaam |
|--------|------|
| `<EMULATOR>_win\` | Emulator ka exe + uski settings (portable mode) |
| `<EMULATOR>_ios\` | Us console ki game files (.iso/.cso/.chd) |

**Portable mode kyun important hai:** Har emulator apni settings apne hi folder
me rakhta hai (C:\Users me nahi). Matlab poora `D:\Game Machine` folder kisi bhi
PC pe copy karo — sab kuch waise ka waisa chalega. Ye ek **portable console** hai!

---

## Part 3: Software Architecture (my_console.py)

### Code ka Flow

```
python my_console.py
        │
        ▼
┌───────────────────┐
│  1. SCAN GAMES    │  Har console ke _ios folder ko padho,
│  scan_games()     │  sahi extensions (.iso/.cso/.chd) filter karo,
└────────┬──────────┘  naam clean karo → games list ready
         ▼
┌───────────────────┐
│  2. UI LOOP       │  1280x720 window, dark theme,
│  main()           │  scrolling list + color tags,
│                   │  keyboard + gamepad input
└────────┬──────────┘
         ▼ (Enter / A button)
┌───────────────────┐
│  3. LAUNCH        │  subprocess.run() se emulator start,
│  launch_game()    │  game band hone tak WAIT,
│                   │  event queue saaf karo,
└────────┬──────────┘  wapas UI loop me
         └──────────→ (loop continue)
```

### CONFIG — Project ka Dil

```python
CONSOLES = {
    "PSP": {
        "rom_folder": r"D:\Game Machine\PPSSPP_ios",
        "extensions": [".iso", ".cso"],
        "emulator":   r"D:\Game Machine\PPSSPP_win\PPSSPPWindows64.exe",
        "args":       ["--fullscreen"],
    },
    "PS2": {
        "rom_folder": r"D:\Game Machine\PCSX2_ios",
        "extensions": [".iso", ".chd"],
        "emulator":   r"D:\Game Machine\PCSX2_win\pcsx2-qt.exe",
        "args":       ["-fullscreen", "-batch"],
    },
    "PS3": {
        "rom_folder": r"D:\Game Machine\RPCS3_ios",
        "extensions": [".iso"],
        "emulator":   r"D:\Game Machine\RPCS3_win\rpcs3.exe",
        "args":       ["--no-gui"],
    },
}
```

Naya console add karna = bas isi pattern me ek aur block. Code me kahin aur
kuch change nahi karna padta. **Ye hi achhe software design ki nishani hai —
data (config) aur logic (code) alag-alag.**

### Emulator Command Reference

| Console | Launch Command | Special Flags ka Matlab |
|---------|---------------|------------------------|
| PSP | `PPSSPPWindows64.exe --fullscreen "game.iso"` | fullscreen me seedha game |
| PS2 | `pcsx2-qt.exe -fullscreen -batch "game.iso"` | `-batch` = game band → PCSX2 bhi band → launcher wapas |
| PS3 | `rpcs3.exe --no-gui "game.iso"` | RPCS3 ki main window skip, seedha boot |

### Smart Features (jo humne add kiye)

1. **Name Cleaner (regex):**
   `0517 - Tekken - Dark Resurrection (USA) (En,Fr,De,Es,It).iso`
   → list me sirf: **Tekken - Dark Resurrection**
   - `^\d+\s*-\s*` → aage ka number prefix hatata hai
   - `[\(\[].*?[\)\]]` → (USA), (v1.01), [b] jaise tags hatata hai

2. **Scrolling List:** 100+ games ke liye — selected item hamesha screen pe
   rahta hai, upar counter dikhta hai (`114 games | 37/114`)

3. **Color Tags:** [PSP] blue, [PS2] green, [PS3] orange — ek nazar me console pehchano

4. **`cwd` Launch:** Emulator apne hi folder se launch hota hai, isliye
   portable mode (memstick, bios, config) bilkul sahi kaam karta hai

5. **Junk Filter:** Extension filter ki wajah se _ios folders me padi
   .jpg/.png/.webp images list me nahi aati

---

## Part 4: Bugs Jo Mile Aur Unke Fix (Real Learning)

### Bug #1: Game exit karte hi khud dobara start ho jati thi ⭐

**Symptom:** PPSSPP se exit karo → wahi game turant phir launch ho jati thi.

**Root Cause (interesting hai!):** Jab game chal rahi hoti hai, launcher
background me "frozen" hota hai — par gamepad ke button presses phir bhi uski
event queue me jama hote rehte hain, kyunki **joystick events ko window focus
ki zarurat nahi hoti** (SDL/pygame ka behaviour). Game band hote hi launcher
jaagta hai, queue me pada purana "A button press" padhta hai, aur usi game ko
dobara launch kar deta hai.

**Fix:** `launch_game()` me `subprocess.run()` ke baad:

```python
pygame.time.wait(500)      # emulator ko poori tarah band hone do
pygame.event.clear()       # saare purane/stale events fenko
```

**Sabak:** Har frontend developer ko ye bug milta hai. Jab bhi koi blocking
operation (game chalana) ke baad UI wapas aaye — pehle input queue saaf karo.

---

## Part 5: Roadmap (Aage Kya Banayenge)

### ✅ Level 1 — DONE (current version)
- [x] Multi-console scanning (PSP + PS2 + PS3)
- [x] Gamepad + keyboard navigation
- [x] Clean game names (regex)
- [x] Scrolling list + color tags
- [x] Auto-relaunch bug fix
- [x] Portable mode support (cwd launch)

### 🔜 Level 2 — Box Art / Cover Grid
- [ ] Har game ke saath uska cover image (grid layout, PS5-style)
- [ ] Covers ke liye `covers\` folder: `covers\PSP\Tekken 6.jpg` pattern
- [ ] Cover na mile to placeholder box + game ka naam
- [ ] Left/Right navigation grid me

### 🔜 Level 3 — Console Feel
- [ ] Console-wise categories/tabs (L1/R1 se switch)
- [ ] B button = back, Start = options
- [ ] Background music + select/confirm sounds
- [ ] "Recently Played" section (last played games top pe)

### 🔜 Level 4 — Full Console Mode
- [ ] Fullscreen borderless mode
- [ ] Windows startup me add (`shell:startup`) → PC on = seedha Game Machine
- [ ] Exit menu me "Shutdown PC" option
- [ ] Ek hi config se Linux support (flatpak commands) — Gateway laptop pe bhi
      yahi launcher chal sake

### 💡 Future Ideas (kabhi mann kare to)
- Metadata scraping (internet se covers + descriptions auto-download)
- Search/filter (100+ games me jaldi dhundo)
- Play time tracking (kaunsi game kitni kheli)
- Multiple gamepad profiles
- Themes (colors change karne ka option)

---

## Part 6: Setup Instructions (Naye PC pe / Recovery ke liye)

1. Poora `D:\Game Machine` folder copy karo (sab kuch portable hai)
2. Python install karo — python.org se, **"Add Python to PATH" TICK karna**
3. Command Prompt: `pip install pygame`
4. `cd "D:\Game Machine"` → `python my_console.py`
5. Gamepad USB se lagao — auto-detect ho jayega

### Troubleshooting

| Problem | Fix |
|---------|-----|
| "Koi game nahi mili" | CONFIG me rom_folder paths check karo |
| Game launch nahi hui | Emulator ka exe path check karo; pehle manually test karo: `Win+R` me poori command paste karke |
| PS2 game me BIOS error | `PCSX2_win\bios\` me BIOS files hain, PCSX2 Settings > BIOS me select karo |
| PS3 game fullscreen nahi | RPCS3 Settings > "Start games in fullscreen mode" ON karo, ya game me Alt+Enter |
| Exit ke baad game dobara chali | Purani my_console.py hai — v2 me `pygame.event.clear()` fix hai |
| Gamepad kaam nahi kar raha | Dusra USB port; launcher restart (gamepad start hone se pehle lagao) |

---

## Part 7: Ye Project Kyun Special Hai

- **RetroBat/ES-DE ready-made the, par humne khud banaya** — ab hume pata hai
  frontend andar se kaise kaam karta hai
- **~200 lines ka Python** = 3 consoles, 110+ games, full gamepad control
- **Portable design** — poora folder hi console hai, kahin bhi le jao
- Ye same architecture bade frontends (LaunchBox, ES-DE) bhi use karte hain —
  bas unke paas zyada polish hai, concept yahi hai

> *"Ek 'bekaar' purana laptop Linux console ban sakta hai, aur ek Python file
> poora PlayStation UI — sahi tools aur realistic expectations ke saath."*

**Happy Gaming! 🕹️**
