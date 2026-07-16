"""
GAME MACHINE - Custom Emulator Frontend (v4 - Dashboard UI)
============================================================
Configured for: D:\\Game Machine
  PSP  -> PPSSPP_win + PPSSPP_ios
  PS2  -> PCSX2_win  + PCSX2_ios
  PS3  -> RPCS3_win  + RPCS3_ios
  + any new <NAME>_win + <NAME>_ios folder pair is AUTO-DETECTED!

How to run:
  1. pip install pygame   (if not installed yet)
  2. Keep this file in D:\\Game Machine (it is already there)
  3. python console.py

What's new in v4 (dashboard design):
  - Header with GAME MACHINE logo, gamepad status and live clock
  - Console tabs: RECENTS / PSP / PS2 / PS3 / auto-detected consoles
  - Hero banner for the selected game (title, last played, hours played)
  - Cover-art grid - drop images in covers\\<CONSOLE>\\<Game Name>.jpg
  - Real play-time tracking (stored in playtime.json next to this file)
  - Toast notifications, particles, animated tab switching

Controls:
  Keyboard : Arrows = navigate, Enter/Space = play, Q/E or [ ] = switch tab,
             R = random game, F11 = fullscreen, Esc = exit
  Gamepad  : D-pad / Left Stick = navigate (hold = auto-repeat),
             A = play, B = Recents tab, Y = random game,
             L1/R1 = switch tab (plugging in after launch also works)
  Mouse    : Hover = select, Click = play, Wheel = scroll,
             EXIT chip (top-right) = quit
  Touch    : Tap = select, tap the selected game again = play,
             Drag = scroll, EXIT chip = quit
"""

import json
import math
import os
import random
import re
import subprocess
import time
from datetime import date

import pygame

BASE = r"D:\Game Machine"

# ============================================================
# CONFIG - your real paths (taken from the dir /s output)
# ============================================================
CONSOLES = {
    "PSP": {
        "rom_folder": os.path.join(BASE, "PPSSPP_ios"),
        "extensions": [".iso", ".cso"],
        "emulator": os.path.join(BASE, "PPSSPP_win", "PPSSPPWindows64.exe"),
        "args": ["--fullscreen"],
    },
    "PS2": {
        "rom_folder": os.path.join(BASE, "PCSX2_ios"),
        "extensions": [".iso", ".chd"],
        "emulator": os.path.join(BASE, "PCSX2_win", "pcsx2-qt.exe"),
        # -batch = when the game closes, PCSX2 closes too (straight back here)
        "args": ["-fullscreen", "-batch"],
    },
    "PS3": {
        "rom_folder": os.path.join(BASE, "RPCS3_ios"),
        "extensions": [".iso"],
        "emulator": os.path.join(BASE, "RPCS3_win", "rpcs3.exe"),
        # --no-gui = skip the RPCS3 main window, boot the game directly
        "args": ["--no-gui"],
    },
}

# Default game extensions for auto-detected consoles
DEFAULT_EXTENSIONS = [".iso", ".cso", ".chd", ".bin"]

# Play-time database lives next to this script (portable, travels with the folder)
PLAYDATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playtime.json")

# Cover art: covers\<CONSOLE>\<Clean Game Name>.jpg / .png
COVERS_DIR = os.path.join(BASE, "covers")

# ============================================================
# AUTO-DETECT - the documented "add a new console" formula:
# a <NAME>_win (emulator) + <NAME>_ios (games) folder pair shows
# up in the UI even without adding it to CONFIG.
# ============================================================
def find_emulator_exe(folder):
    """Find the main .exe inside an emulator folder (largest exe wins)."""
    skip_words = ("unins", "setup", "updater", "crash", "install")
    exes = []
    for f in os.listdir(folder):
        low = f.lower()
        if low.endswith(".exe") and not any(w in low for w in skip_words):
            exes.append(os.path.join(folder, f))
    if not exes:
        return None
    return max(exes, key=os.path.getsize)


def discover_consoles():
    """CONFIG consoles + any new _win/_ios pairs found in BASE."""
    consoles = dict(CONSOLES)
    if not os.path.isdir(BASE):
        return consoles

    known_rom_folders = {os.path.normcase(cfg["rom_folder"]) for cfg in consoles.values()}

    for entry in sorted(os.listdir(BASE)):
        if not entry.lower().endswith("_ios"):
            continue
        rom_folder = os.path.join(BASE, entry)
        if not os.path.isdir(rom_folder):
            continue
        if os.path.normcase(rom_folder) in known_rom_folders:
            continue  # already configured (e.g. PPSSPP_ios -> PSP)

        name = entry[: -len("_ios")]
        emu_folder = os.path.join(BASE, name + "_win")
        if not os.path.isdir(emu_folder):
            continue
        exe = find_emulator_exe(emu_folder)
        if not exe:
            continue

        consoles[name.upper()] = {
            "rom_folder": rom_folder,
            "extensions": DEFAULT_EXTENSIONS,
            "emulator": exe,
            "args": [],
        }
    return consoles

# ============================================================
# NAME CLEANER - "0517 - Tekken (USA) (v1.01).iso" -> "Tekken"
# ============================================================
def clean_name(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r"^\d+\s*-\s*", "", name)              # strip "0517 - " prefix
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name)  # strip (USA) (v1.01) [b]
    return name.strip()

# ============================================================
# GAME SCANNING
# ============================================================
def scan_games(consoles):
    games = []
    for console_name, cfg in consoles.items():
        folder = cfg["rom_folder"]
        if not os.path.isdir(folder):
            continue
        for filename in sorted(os.listdir(folder)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in cfg["extensions"]:
                games.append({
                    "name": clean_name(filename),
                    "path": os.path.join(folder, filename),
                    "console": console_name,
                })
    return games

# ============================================================
# PLAY-TIME TRACKING (powers the RECENTS tab + hero banner stats)
# ============================================================
def load_playdata():
    try:
        with open(PLAYDATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_playdata(data):
    try:
        with open(PLAYDATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # tracking is a bonus feature - never block launching over it


def fmt_dur(seconds):
    """4h 20m style duration."""
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{max(1, minutes)}m"


def fmt_last(timestamp):
    """Relative 'last played' label in plain English."""
    days = (date.today() - date.fromtimestamp(timestamp)).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "last week"
    return date.fromtimestamp(timestamp).strftime("%d %b %Y")

# ============================================================
# GAME LAUNCHING
# ============================================================
def launch_game(game, consoles):
    cfg = consoles[game["console"]]
    command = [cfg["emulator"]] + cfg["args"] + [game["path"]]
    start = time.time()
    # cwd = the emulator's own folder so portable mode works correctly
    subprocess.run(command, cwd=os.path.dirname(cfg["emulator"]))
    elapsed = int(time.time() - start)
    # BUG FIX: buttons pressed while the game was running pile up in our
    # event queue - the stale "A press" used to relaunch the same game
    # the moment we came back. Flush everything:
    pygame.time.wait(500)      # let the emulator shut down completely
    pygame.event.clear()       # drop all stale input events
    return elapsed

# ============================================================
# THEME (colors from the dashboard design)
# ============================================================
SCREEN_W, SCREEN_H = 1280, 720
COL_BG = (7, 8, 12)
COL_BG_GLOW = (16, 19, 28)
COL_TEXT = (238, 240, 244)
COL_DIM = (138, 141, 148)
COL_DIMMER = (86, 91, 102)
COL_PANEL = (17, 20, 27)
COL_PANEL2 = (26, 30, 39)
COL_CARD_BORDER = (28, 32, 42)
COL_FOOT_LINE = (23, 26, 34)
COL_PAD_OK = (93, 202, 165)
COL_TOAST_BG = (23, 27, 36)
COL_TOAST_EDGE = (240, 112, 60)
COL_BTN_B = (240, 149, 149)
COL_BTN_Y = (250, 199, 117)

REC_COLOR = (95, 212, 232)  # RECENTS tab accent
CONSOLE_COLORS = {
    "PSP": (240, 112, 60),   # orange
    "PS2": (79, 214, 166),   # green
    "PS3": (157, 147, 245),  # purple
}
# Auto-detected consoles get colors from this pool
EXTRA_COLORS = [
    (255, 105, 180),  # pink
    (250, 199, 117),  # gold
    (90, 230, 230),   # cyan
    (255, 120, 90),   # coral
    (170, 220, 120),  # lime
]

# Layout
PAD_X = 44
HERO_RECT = pygame.Rect(PAD_X, 122, SCREEN_W - 2 * PAD_X, 172)
GRID_RECT = pygame.Rect(PAD_X, 310, SCREEN_W - 2 * PAD_X, 352)
FOOTER_Y = 668
CARD_W, COVER_H, CARD_H, GAP = 132, 176, 246, 14
COLS = (GRID_RECT.w + GAP) // (CARD_W + GAP)

# Input tuning
AXIS_DEADZONE = 0.5
NAV_REPEAT_DELAY = 350
NAV_REPEAT_RATE = 130
TAP_SLOP = 12          # finger moved less than this = tap, more = drag
WHEEL_STEP = 80        # pixels per mouse wheel notch
TOAST_MS = 2200
TAB_ANIM_MS = 420


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def build_console_colors(consoles):
    """Give every console a color - auto-detected ones draw from EXTRA_COLORS."""
    colors = dict(CONSOLE_COLORS)
    i = 0
    for name in consoles:
        if name not in colors:
            colors[name] = EXTRA_COLORS[i % len(EXTRA_COLORS)]
            i += 1
    return colors


def ease_out(p):
    return 1 - (1 - p) ** 3

# ============================================================
# THE DASHBOARD UI
# ============================================================
class GameMachine:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        pygame.key.set_repeat(NAV_REPEAT_DELAY, NAV_REPEAT_RATE)

        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("GAME MACHINE")
        self.clock = pygame.time.Clock()
        self.fullscreen = False

        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Fonts (Rajdhani/Space Grotesk in the design -> closest system fonts).
        # Headings use the DIN-style Bahnschrift; small text that contains
        # symbol glyphs (● ○ ◄ ►) uses Verdana/Arial which reliably have them.
        def FH(size, bold=False):
            return pygame.font.SysFont("bahnschrift,verdana,arial", size, bold=bold)

        def FB(size, bold=False):
            return pygame.font.SysFont("verdana,arial", size, bold=bold)
        self.f_logo = FH(24, True)
        self.f_sub = FB(11)
        self.f_clock = FH(17, True)
        self.f_tab = FH(16, True)
        self.f_channel = FH(13, True)
        self.f_hero = FH(38, True)
        self.f_meta = FB(14)
        self.f_btn = FH(15, True)
        self.f_card = FB(13)
        self.f_chip = FB(10, True)
        self.f_small = FB(12)
        self.f_hint = FB(12)
        self.f_ghost = FH(120, True)
        self.f_mono = pygame.font.SysFont("consolas,couriernew,monospace", 11)

        # Data
        self.consoles = discover_consoles()
        self.colors = build_console_colors(self.consoles)
        self.games = scan_games(self.consoles)
        self.playdata = load_playdata()

        present = [c for c in self.consoles if any(g["console"] == c for g in self.games)]
        self.tabs = [("RECENTS", REC_COLOR)] + [(c, self.colors[c]) for c in present]

        # UI state
        self.tab = 0 if self._recents() else (1 if len(self.tabs) > 1 else 0)
        self.sel = 0
        self.scroll = 0.0
        self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()
        self.toast = None
        self.toast_until = 0
        self.running = True

        # Gamepad hold-to-repeat state (x and y tracked separately)
        self.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}

        # Touch state (to tell taps and drags apart)
        self.touch_id = None
        self.touch_start = None
        self.touch_last_y = 0.0
        self.touch_moved = False

        # Hit-test rects, refreshed every frame by draw()
        self.tab_rects = []
        self.card_rects = []
        self.play_rect = None
        self.details_rect = None
        self.exit_rect = pygame.Rect(0, 0, 0, 0)

        # Render caches
        self._bg = self._build_bg()
        self._gridlines = self._build_gridlines()
        self._hero_cache = {}
        self._ghost_cache = {}
        self._cover_cache = {}
        self._placeholder_cache = {}

        # Ambient particles (drift upward, tinted by the active tab color)
        self.particles = [{
            "x": random.uniform(0, SCREEN_W), "y": random.uniform(0, SCREEN_H),
            "s": random.uniform(0.6, 2.6), "v": random.uniform(0.1, 0.45),
            "ph": random.uniform(0, math.tau),
        } for _ in range(90)]
        self._overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

    # ---------------- data helpers ----------------
    def _recents(self):
        played = [g for g in self.games if self.playdata.get(g["path"], {}).get("last")]
        played.sort(key=lambda g: -self.playdata[g["path"]]["last"])
        return played[:16]

    def current_list(self):
        name = self.tabs[self.tab][0]
        if name == "RECENTS":
            return self._recents()
        return [g for g in self.games if g["console"] == name]

    def accent(self):
        return self.tabs[self.tab][1]

    def game_stats(self, game):
        rec = self.playdata.get(game["path"])
        if rec and rec.get("last"):
            return rec
        return None

    # ---------------- actions ----------------
    def pop(self, msg):
        self.toast = msg
        self.toast_until = pygame.time.get_ticks() + TOAST_MS

    def set_tab(self, i):
        n = i % len(self.tabs)
        if n == self.tab:
            return
        self.tab = n
        self.sel = 0
        self.scroll = self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()

    def move_sel(self, dx, dy):
        L = self.current_list()
        if not L:
            return
        new = self.sel + dx + dy * COLS
        self.sel = max(0, min(new, len(L) - 1))
        self.ensure = True

    def random_pick(self):
        L = self.current_list()
        if not L:
            return
        self.sel = random.randrange(len(L))
        self.ensure = True
        self.pop("Random pick: " + L[self.sel]["name"])

    def show_details(self):
        L = self.current_list()
        if not L:
            return
        g = L[min(self.sel, len(L) - 1)]
        rec = self.game_stats(g)
        if rec:
            self.pop(f"{g['name']} · {g['console']} · {fmt_dur(rec['seconds'])} played")
        else:
            self.pop(f"{g['name']} · {g['console']} · not played yet")

    def launch_selected(self):
        L = self.current_list()
        if not L:
            return
        game = L[min(self.sel, len(L) - 1)]
        elapsed = launch_game(game, self.consoles)
        rec = self.playdata.setdefault(game["path"], {"seconds": 0, "last": 0})
        rec["seconds"] += elapsed
        rec["last"] = int(time.time())
        save_playdata(self.playdata)
        self.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}
        self.pop(f"Welcome back · {fmt_dur(elapsed)} session")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN | pygame.SCALED if self.fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

    def click(self, pos):
        """Shared mouse-click / touch-tap handler."""
        if self.exit_rect.collidepoint(pos):
            self.running = False
            return
        for i, r in self.tab_rects:
            if r.collidepoint(pos):
                self.set_tab(i)
                return
        if self.play_rect and self.play_rect.collidepoint(pos):
            self.launch_selected()
            return
        if self.details_rect and self.details_rect.collidepoint(pos):
            self.show_details()
            return
        for i, r in self.card_rects:
            if r.collidepoint(pos):
                if i == self.sel:
                    self.launch_selected()  # second tap/click = play
                else:
                    self.sel = i            # first tap = just select
                return

    # ---------------- input ----------------
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False

        # ----- Keyboard -----
        elif e.type == pygame.KEYDOWN:
            k = e.key
            if k == pygame.K_ESCAPE:
                self.running = False
            elif k == pygame.K_LEFT:
                self.move_sel(-1, 0)
            elif k == pygame.K_RIGHT:
                self.move_sel(1, 0)
            elif k == pygame.K_UP:
                self.move_sel(0, -1)
            elif k == pygame.K_DOWN:
                self.move_sel(0, 1)
            elif k == pygame.K_PAGEUP:
                self.move_sel(0, -2)
            elif k == pygame.K_PAGEDOWN:
                self.move_sel(0, 2)
            elif k == pygame.K_HOME:
                self.sel = 0
                self.ensure = True
            elif k == pygame.K_END:
                L = self.current_list()
                if L:
                    self.sel = len(L) - 1
                    self.ensure = True
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.launch_selected()
            elif k in (pygame.K_q, pygame.K_LEFTBRACKET):
                self.set_tab(self.tab - 1)
            elif k in (pygame.K_e, pygame.K_RIGHTBRACKET):
                self.set_tab(self.tab + 1)
            elif k in (pygame.K_r, pygame.K_y):
                self.random_pick()
            elif k == pygame.K_F11:
                self.toggle_fullscreen()

        # ----- Gamepad buttons -----
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button == 0:      # A = play
                self.launch_selected()
            elif e.button == 1:    # B = back to Recents
                self.set_tab(0)
            elif e.button == 3:    # Y = random game
                self.random_pick()
            elif e.button == 4:    # L1 = previous tab
                self.set_tab(self.tab - 1)
            elif e.button == 5:    # R1 = next tab
                self.set_tab(self.tab + 1)

        # Controller plugged in AFTER launch still works
        elif e.type == pygame.JOYDEVICEADDED:
            self.joystick = pygame.joystick.Joystick(e.device_index)
            self.joystick.init()
        elif e.type == pygame.JOYDEVICEREMOVED:
            if self.joystick is not None and self.joystick.get_instance_id() == e.instance_id:
                self.joystick = None
                self.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}

        # ----- Mouse -----
        # NOTE: touching the screen makes SDL emit synthetic mouse events
        # too - skip those so touch input is not handled twice.
        elif e.type == pygame.MOUSEMOTION:
            if not getattr(e, "touch", False):
                for i, r in self.card_rects:
                    if r.collidepoint(e.pos):
                        self.sel = i  # hover = select (leave scroll alone)
                        break

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if not getattr(e, "touch", False):
                self.click(e.pos)

        elif e.type == pygame.MOUSEWHEEL:
            self.scroll_t -= e.y * WHEEL_STEP

        # ----- Touch -----
        elif e.type == pygame.FINGERDOWN:
            if self.touch_id is None:  # track the first finger only
                w, h = self.screen.get_size()
                self.touch_id = e.finger_id
                self.touch_start = (e.x * w, e.y * h)
                self.touch_last_y = e.y * h
                self.touch_moved = False

        elif e.type == pygame.FINGERMOTION:
            if e.finger_id == self.touch_id and self.touch_start is not None:
                w, h = self.screen.get_size()
                y = e.y * h
                if abs(y - self.touch_start[1]) > TAP_SLOP:
                    self.touch_moved = True
                if self.touch_moved:
                    # finger up = list scrolls down (natural scrolling)
                    self.scroll_t += self.touch_last_y - y
                self.touch_last_y = y

        elif e.type == pygame.FINGERUP:
            if e.finger_id == self.touch_id:
                if self.touch_start is not None and not self.touch_moved:
                    w, h = self.screen.get_size()
                    self.click((e.x * w, e.y * h))
                self.touch_id = None
                self.touch_start = None

    def _pad_axis_repeat(self, key, cur, now, mover):
        """Hold-to-repeat for one gamepad axis (d-pad or analog stick)."""
        st = self.pad_state[key]
        if cur != st["dir"]:
            st["dir"] = cur
            if cur:
                mover(cur)
                st["next"] = now + NAV_REPEAT_DELAY
        elif cur and now >= st["next"]:
            mover(cur)
            st["next"] = now + NAV_REPEAT_RATE

    def update_gamepad(self, now):
        j = self.joystick
        dx = dy = 0
        if j is not None:
            if j.get_numhats() > 0:
                hx, hy = j.get_hat(0)
                dx, dy = hx, -hy
            if dx == 0 and j.get_numaxes() > 0:
                ax = j.get_axis(0)
                dx = 1 if ax > AXIS_DEADZONE else (-1 if ax < -AXIS_DEADZONE else 0)
            if dy == 0 and j.get_numaxes() > 1:
                ay = j.get_axis(1)
                dy = 1 if ay > AXIS_DEADZONE else (-1 if ay < -AXIS_DEADZONE else 0)
        self._pad_axis_repeat("x", dx, now, lambda d: self.move_sel(d, 0))
        self._pad_axis_repeat("y", dy, now, lambda d: self.move_sel(0, d))

    def update_scroll(self):
        L = self.current_list()
        if L:
            self.sel = min(self.sel, len(L) - 1)
        rows = (len(L) + COLS - 1) // COLS
        max_scroll = max(0, rows * (CARD_H + GAP) - GAP - GRID_RECT.h)

        if self.ensure and L:
            row_top = (self.sel // COLS) * (CARD_H + GAP)
            row_bot = row_top + CARD_H
            if row_top < self.scroll_t:
                self.scroll_t = row_top
            elif row_bot > self.scroll_t + GRID_RECT.h:
                self.scroll_t = row_bot - GRID_RECT.h
        self.ensure = False

        self.scroll_t = max(0.0, min(self.scroll_t, float(max_scroll)))
        self.scroll += (self.scroll_t - self.scroll) * 0.35
        if abs(self.scroll - self.scroll_t) < 0.5:
            self.scroll = self.scroll_t

    # ---------------- cached background art ----------------
    def _build_bg(self):
        """Radial glow at the top-right, like the design's backdrop."""
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        s.fill(COL_BG)
        cx, cy = int(SCREEN_W * 0.7), int(-SCREEN_H * 0.1)
        steps = 90
        for i in range(steps, 0, -1):
            t = i / steps
            pygame.draw.circle(s, mix(COL_BG_GLOW, COL_BG, t), (cx, cy), int(900 * t))
        return s

    def _build_gridlines(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        col = (120, 140, 180, 11)
        for x in range(0, SCREEN_W, 56):
            pygame.draw.line(s, col, (x, 0), (x, SCREEN_H))
        for y in range(0, SCREEN_H, 56):
            pygame.draw.line(s, col, (0, y), (SCREEN_W, y))
        return s

    def _hero_bg(self, accent):
        if accent not in self._hero_cache:
            w, h = HERO_RECT.size
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            c_a = mix((16, 19, 25), accent, 0.16)
            c_b = (16, 19, 25)
            c_c = (11, 13, 19)
            for x in range(w):
                t = x / w
                col = mix(c_a, c_b, t / 0.55) if t < 0.55 else mix(c_b, c_c, (t - 0.55) / 0.45)
                pygame.draw.line(surf, col, (x, 0), (x, h))
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=16)
            surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self._hero_cache[accent] = surf
        return self._hero_cache[accent]

    def _ghost_text(self, text, accent):
        key = (text, accent)
        if key not in self._ghost_cache:
            surf = self.f_ghost.render(text, True, accent)
            surf.set_alpha(38)
            self._ghost_cache[key] = surf
        return self._ghost_cache[key]

    def _cover_for(self, game):
        """Load covers\\<CONSOLE>\\<Clean Name>.jpg/.png if it exists (cached)."""
        path = game["path"]
        if path not in self._cover_cache:
            surf = None
            for ext in (".jpg", ".jpeg", ".png"):
                p = os.path.join(COVERS_DIR, game["console"], game["name"] + ext)
                if os.path.isfile(p):
                    try:
                        img = pygame.image.load(p).convert()
                        surf = pygame.transform.smoothscale(img, (CARD_W, COVER_H))
                    except pygame.error:
                        surf = None
                    break
            self._cover_cache[path] = surf
        return self._cover_cache[path]

    def _placeholder(self, accent, active):
        key = (accent, active)
        if key not in self._placeholder_cache:
            s = pygame.Surface((CARD_W, COVER_H), pygame.SRCALPHA)
            stripe = accent + ((36,) if active else (16,))
            for i in range(-COVER_H, CARD_W + COVER_H, 24):
                pygame.draw.line(s, stripe, (i, COVER_H), (i + COVER_H, 0), 12)
            label = self.f_mono.render("COVER ART", True,
                                       accent if active else (58, 62, 72))
            if not active:
                label.set_alpha(255)
            s.blit(label, label.get_rect(center=(CARD_W // 2, COVER_H // 2)))
            self._placeholder_cache[key] = s
        return self._placeholder_cache[key]

    # ---------------- drawing helpers ----------------
    def _spaced_text(self, font, text, color, pos, spacing):
        """Letter-spaced text (the design uses wide tracking for headings)."""
        x, y = pos
        for ch in text:
            glyph = font.render(ch, True, color)
            self.screen.blit(glyph, (x, y))
            x += glyph.get_width() + spacing
        return x

    def _parallelogram(self, rect, color, cut=9, width=0):
        pts = [(rect.x + cut, rect.y), (rect.right, rect.y),
               (rect.right - cut, rect.bottom), (rect.x, rect.bottom)]
        pygame.draw.polygon(self.screen, color, pts, width)

    def _key_hint(self, x, y, letter, color, text):
        pygame.draw.circle(self.screen, color, (x + 9, y + 9), 9, 1)
        glyph = self.f_mono.render(letter, True, color)
        self.screen.blit(glyph, glyph.get_rect(center=(x + 9, y + 9)))
        label = self.f_hint.render(text, True, COL_DIM)
        self.screen.blit(label, (x + 24, y + 1))
        return x + 24 + label.get_width() + 24

    def _wrap2(self, text, font, maxw):
        """Wrap a title onto at most 2 lines, ellipsizing the rest."""
        words = text.split()
        lines, cur = [], ""
        for i, w in enumerate(words):
            trial = (cur + " " + w).strip()
            if font.size(trial)[0] <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
                if len(lines) == 2:
                    break
        if len(lines) < 2 and cur:
            lines.append(cur)
            cur = ""
        if cur and len(lines) == 2:  # text still left over -> ellipsis
            last = lines[1]
            while last and font.size(last + "…")[0] > maxw:
                last = last[:-1]
            lines[1] = last + "…"
        return lines[:2]

    # ---------------- main draw ----------------
    def draw(self, now):
        scr = self.screen
        L = self.current_list()
        sel = min(self.sel, len(L) - 1) if L else 0
        cur = L[sel] if L else None
        accent = self.colors.get(cur["console"], self.accent()) if cur else self.accent()
        tab_name = self.tabs[self.tab][0]

        # Tab-switch slide-in animation
        p = min(1.0, (now - self.switch_ms) / TAB_ANIM_MS)
        anim_off = int(26 * (1 - ease_out(p)))

        self.tab_rects = []
        self.card_rects = []
        self.play_rect = None
        self.details_rect = None

        scr.blit(self._bg, (0, 0))
        scr.blit(self._gridlines, (0, 0))

        # Particles (tinted with the active tab color)
        self._overlay.fill((0, 0, 0, 0))
        tab_col = self.accent()
        for pt in self.particles:
            pt["y"] -= pt["v"]
            if pt["y"] < -4:
                pt["y"] = SCREEN_H + 4
                pt["x"] = random.uniform(0, SCREEN_W)
            tw = 0.25 + 0.35 * abs(math.sin(now / 1400 + pt["ph"]))
            pygame.draw.circle(self._overlay, tab_col + (int(tw * 255),),
                               (int(pt["x"]), int(pt["y"])), pt["s"])
        scr.blit(self._overlay, (0, 0))

        # ----- Header -----
        pygame.draw.polygon(scr, (240, 112, 60),
                            [(PAD_X + 7, 26), (PAD_X + 14, 33), (PAD_X + 7, 40), (PAD_X, 33)])
        x_end = self._spaced_text(self.f_logo, "GAME MACHINE", COL_TEXT, (PAD_X + 26, 20), 5)
        sub = self.f_sub.render("v4 · EMULATOR FRONTEND", True, COL_DIMMER)
        scr.blit(sub, (x_end + 12, 30))

        self.exit_rect = pygame.Rect(SCREEN_W - PAD_X - 58, 20, 58, 28)
        pygame.draw.rect(scr, (60, 20, 25), self.exit_rect, border_radius=6)
        pygame.draw.rect(scr, (200, 70, 80), self.exit_rect, 1, border_radius=6)
        ex = self.f_sub.render("EXIT", True, (255, 120, 130))
        scr.blit(ex, ex.get_rect(center=self.exit_rect.center))

        clock_s = self.f_clock.render(time.strftime("%I:%M %p").lstrip("0"), True, (213, 215, 220))
        cx = self.exit_rect.x - 18 - clock_s.get_width()
        scr.blit(clock_s, (cx, 24))
        pad_txt = "● PAD 1" if self.joystick else "○ NO PAD"
        pad_col = COL_PAD_OK if self.joystick else COL_DIMMER
        pad_s = self.f_small.render(pad_txt, True, pad_col)
        scr.blit(pad_s, (cx - 18 - pad_s.get_width(), 27))

        # ----- Tabs -----
        ty = 76
        hint_q = self.f_chip.render("Q ◄", True, COL_DIMMER)
        scr.blit(hint_q, (PAD_X, ty + 10))
        tx = PAD_X + hint_q.get_width() + 12
        for i, (name, col) in enumerate(self.tabs):
            on = i == self.tab
            label = self.f_tab.render(name, True, col if on else COL_DIM)
            r = pygame.Rect(tx, ty, label.get_width() + 46, 34)
            if on:
                self._parallelogram(r, mix(COL_BG, col, 0.16))
                self._parallelogram(r, col, width=1)
            else:
                self._parallelogram(r, (18, 21, 28))
                self._parallelogram(r, (32, 36, 46), width=1)
            scr.blit(label, label.get_rect(center=r.center))
            self.tab_rects.append((i, r))
            tx = r.right + 10
        hint_e = self.f_chip.render("► E", True, COL_DIMMER)
        scr.blit(hint_e, (tx + 4, ty + 10))
        count = self.f_small.render(
            f"{len(L)} games · {sel + 1 if L else 0}/{len(L)}", True, COL_DIMMER)
        scr.blit(count, (SCREEN_W - PAD_X - count.get_width(), ty + 9))

        # ----- Hero banner -----
        hero = HERO_RECT.move(0, anim_off)
        scr.blit(self._hero_bg(accent), hero.topleft)
        pygame.draw.rect(scr, mix(COL_BG, accent, 0.30), hero, 1, border_radius=16)

        scr.set_clip(hero)
        if cur:
            ghost = self._ghost_text(cur["console"], accent)
            scr.blit(ghost, (hero.right - ghost.get_width() - 16, hero.y - 34))
        # pulsing glow line along the top edge (fades out to the right)
        pulse = 0.55 + 0.45 * abs(math.sin(now / 950))
        glow_w = int(hero.w * 0.6)
        glow = pygame.Surface((glow_w, 2), pygame.SRCALPHA)
        seg_w = glow_w / 24
        for seg in range(24):
            a = int(200 * pulse * (1 - seg / 24))
            pygame.draw.rect(glow, accent + (a,), (seg * seg_w, 0, seg_w + 1, 2))
        scr.blit(glow, hero.topleft)
        scr.set_clip(None)

        if cur:
            rec = self.game_stats(cur)
            channel = (f"{cur['console']} · RECENTLY PLAYED" if tab_name == "RECENTS"
                       else f"{cur['console']} CHANNEL")
            self._spaced_text(self.f_channel, channel, accent, (hero.x + 32, hero.y + 18), 3)
            title = self.f_hero.render(cur["name"], True, (253, 253, 253))
            scr.blit(title, (hero.x + 30, hero.y + 40))
            if rec:
                meta_txt = f"Last played {fmt_last(rec['last'])} · {fmt_dur(rec['seconds'])} played"
            else:
                meta_txt = "Not played yet · Press A to start"
            meta = self.f_meta.render(meta_txt, True, (155, 160, 170))
            scr.blit(meta, (hero.x + 31, hero.y + 88))

            by = hero.bottom - 52
            play_label = self.f_btn.render("RESUME" if rec else "PLAY", True, (11, 13, 19))
            self.play_rect = pygame.Rect(hero.x + 30, by, play_label.get_width() + 70, 38)
            self._parallelogram(self.play_rect, accent, cut=8)
            cy = self.play_rect.centery
            tri_x = self.play_rect.x + 24
            pygame.draw.polygon(scr, (11, 13, 19),
                                [(tri_x, cy - 6), (tri_x, cy + 6), (tri_x + 10, cy)])
            scr.blit(play_label, (tri_x + 18, cy - play_label.get_height() // 2))

            det_label = self.f_btn.render("DETAILS", True, (185, 188, 194))
            self.details_rect = pygame.Rect(self.play_rect.right + 12, by,
                                            det_label.get_width() + 44, 38)
            self._parallelogram(self.details_rect, (58, 62, 72), cut=8, width=1)
            scr.blit(det_label, det_label.get_rect(center=self.details_rect.center))
        else:
            self._spaced_text(self.f_channel, "GAME MACHINE", accent, (hero.x + 32, hero.y + 22), 3)
            if tab_name == "RECENTS":
                t1, t2 = "Nothing played yet", "Pick a console tab and start a game - it will show up here."
            else:
                t1, t2 = "No games found", "Check the CONFIG paths at the top of console.py."
            scr.blit(self.f_hero.render(t1, True, (253, 253, 253)), (hero.x + 30, hero.y + 48))
            scr.blit(self.f_meta.render(t2, True, (155, 160, 170)), (hero.x + 31, hero.y + 100))

        # ----- Cover grid -----
        scr.set_clip(GRID_RECT)
        for i, g in enumerate(L):
            row, col = divmod(i, COLS)
            gx = GRID_RECT.x + col * (CARD_W + GAP)
            gy = GRID_RECT.y + row * (CARD_H + GAP) - int(self.scroll) + anim_off
            if gy + CARD_H < GRID_RECT.y or gy > GRID_RECT.bottom:
                continue
            on = i == sel
            c = self.colors.get(g["console"], (150, 150, 150))
            lift = -6 if on else 0
            card = pygame.Rect(gx, gy + lift, CARD_W, CARD_H)

            pygame.draw.rect(scr, COL_PANEL, card, border_radius=10)
            cover = self._cover_for(g)
            cov_area = pygame.Rect(card.x, card.y, CARD_W, COVER_H)
            prev_clip = scr.get_clip()
            scr.set_clip(prev_clip.clip(cov_area) if prev_clip else cov_area)
            scr.blit(cover if cover else self._placeholder(c, on), cov_area.topleft)
            scr.set_clip(prev_clip)

            ty2 = card.y + COVER_H + 9
            for line in self._wrap2(g["name"], self.f_card, CARD_W - 20):
                scr.blit(self.f_card.render(line, True, (231, 233, 238) if on else (185, 188, 195)),
                         (card.x + 10, ty2))
                ty2 += 17
            chip = self.f_chip.render(g["console"], True, c)
            chip_r = pygame.Rect(card.x + 10, card.bottom - 26, chip.get_width() + 14, 18)
            pygame.draw.rect(scr, mix(COL_BG, c, 0.35), chip_r, 1, border_radius=3)
            scr.blit(chip, chip.get_rect(center=chip_r.center))
            rec = self.game_stats(g)
            sub_txt = fmt_last(rec["last"]) if rec else "NEW"
            sub_s = self.f_mono.render(sub_txt, True, COL_DIMMER)
            scr.blit(sub_s, (card.right - 10 - sub_s.get_width(), card.bottom - 23))

            border_c = mix(COL_BG, c, 0.8) if on else COL_CARD_BORDER
            pygame.draw.rect(scr, border_c, card, 1, border_radius=10)
            if on:
                pygame.draw.rect(scr, c, (card.x, card.y, CARD_W, 2))
            # clip the hit-test rect to the grid so half-hidden cards
            # can't be clicked through the hero banner or footer
            self.card_rects.append((i, card.clip(GRID_RECT)))
        scr.set_clip(None)

        # ----- Footer -----
        pygame.draw.line(scr, COL_FOOT_LINE, (0, FOOTER_Y), (SCREEN_W, FOOTER_Y))
        ncons = max(0, len(self.tabs) - 1)
        status = self.f_small.render(
            f"{BASE.upper()}  ·  {len(self.games)} GAMES SCANNED  ·  {ncons} CONSOLES",
            True, COL_DIMMER)
        scr.blit(status, (PAD_X, FOOTER_Y + 18))

        hx = SCREEN_W - PAD_X - 560
        hx = self._key_hint(hx, FOOTER_Y + 14, "A", COL_PAD_OK, "Play")
        hx = self._key_hint(hx, FOOTER_Y + 14, "B", COL_BTN_B, "Recents")
        hx = self._key_hint(hx, FOOTER_Y + 14, "Y", COL_BTN_Y, "Random")
        pill = pygame.Rect(hx, FOOTER_Y + 14, 44, 18)
        pygame.draw.rect(scr, COL_DIM, pill, 1, border_radius=9)
        pl = self.f_mono.render("L1 R1", True, (185, 188, 194))
        scr.blit(pl, pl.get_rect(center=pill.center))
        scr.blit(self.f_hint.render("Switch console", True, COL_DIM),
                 (pill.right + 8, FOOTER_Y + 15))

        # ----- Toast -----
        if self.toast and now < self.toast_until:
            tp = min(1.0, (now - (self.toast_until - TOAST_MS)) / 250)
            surf = self.f_small.render(self.toast, True, (231, 233, 238))
            tw, th = surf.get_width() + 44, 38
            tr = pygame.Rect((SCREEN_W - tw) // 2,
                             SCREEN_H - 88 + int(12 * (1 - ease_out(tp))), tw, th)
            pygame.draw.rect(scr, COL_TOAST_BG, tr, border_radius=6)
            pygame.draw.rect(scr, (44, 47, 56), tr, 1, border_radius=6)
            pygame.draw.rect(scr, COL_TOAST_EDGE, (tr.x, tr.y, 2, th))
            scr.blit(surf, (tr.x + 24, tr.y + 10))

    # ---------------- main loop ----------------
    def run(self):
        while self.running:
            now = pygame.time.get_ticks()
            for e in pygame.event.get():
                self.handle_event(e)
            self.update_gamepad(now)
            self.update_scroll()
            self.draw(now)
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()


def main():
    GameMachine().run()


if __name__ == "__main__":
    main()
