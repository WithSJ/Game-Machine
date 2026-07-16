"""
MY CONSOLE - Custom Emulator Frontend (v3 - Sandeep's Game Machine)
====================================================================
Configured for: D:\\Game Machine
  PSP  -> PPSSPP_win + PPSSPP_ios
  PS2  -> PCSX2_win  + PCSX2_ios
  PS3  -> RPCS3_win  + RPCS3_ios
  + koi bhi naya <NAME>_win + <NAME>_ios folder pair AUTO-DETECT ho jata hai!

Kaise chalaye:
  1. pip install pygame   (agar pehle se nahi kiya)
  2. Ye file D:\\Game Machine me rakho (already wahi hai)
  3. python console.py

Controls (v3 - saare input types):
  Keyboard : Up/Down ya W/S = navigate, PgUp/PgDn = page jump,
             Home/End = top/bottom, Enter ya Space = launch,
             F11 = fullscreen toggle, Esc = exit
  Gamepad  : D-pad ya Left Stick = navigate (hold = auto-repeat),
             A button = launch (gamepad baad me lagao to bhi chalega)
  Mouse    : Hover = select, Click = launch, Scroll wheel = list scroll,
             EXIT button (top-right) = band karo
  Touch    : Tap = select, selected pe dobara Tap = launch,
             upar/neeche Drag = list scroll, EXIT button = band karo
"""

import os
import re
import subprocess
import pygame

BASE = r"D:\Game Machine"

# ============================================================
# CONFIG - tumhare asli paths (dir /s output se liye gaye)
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
        # -batch = game band karo to PCSX2 bhi band (seedha launcher pe wapas)
        "args": ["-fullscreen", "-batch"],
    },
    "PS3": {
        "rom_folder": os.path.join(BASE, "RPCS3_ios"),
        "extensions": [".iso"],
        "emulator": os.path.join(BASE, "RPCS3_win", "rpcs3.exe"),
        # --no-gui = RPCS3 ki main window skip, seedha game boot
        "args": ["--no-gui"],
    },
}

# Auto-detect hue naye consoles ke liye default game extensions
DEFAULT_EXTENSIONS = [".iso", ".cso", ".chd", ".bin"]

# ============================================================
# AUTO-DETECT - Documentation ka "Naya console add karne ka formula"
# <NAME>_win (emulator) + <NAME>_ios (games) folder pair mila to
# wo console CONFIG me likhe bina bhi list me aa jayega.
# ============================================================
def find_emulator_exe(folder):
    """Emulator folder me main .exe dhundo (sabse bada exe = emulator)."""
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
    """CONFIG wale consoles + BASE me mile naye _win/_ios pairs."""
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
            continue  # ye CONFIG me pehle se hai (jaise PPSSPP_ios -> PSP)

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
    name = re.sub(r"^\d+\s*-\s*", "", name)          # aage ka "0517 - " hatao
    name = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", name)  # (USA) (v1.01) [b] hatao
    return name.strip()

# ============================================================
# STEP 1: GAME SCANNING
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
# STEP 2: GAME LAUNCHING
# ============================================================
def launch_game(game, consoles):
    cfg = consoles[game["console"]]
    command = [cfg["emulator"]] + cfg["args"] + [game["path"]]
    # cwd = emulator ka apna folder, taaki portable mode sahi kaam kare
    subprocess.run(command, cwd=os.path.dirname(cfg["emulator"]))
    # BUG FIX: game ke dauran dabaye gaye gamepad/keyboard buttons launcher ki
    # queue me jama ho jaate hain - wapas aate hi wahi purana "A press" game ko
    # dobara launch kar deta tha. Isliye queue poori saaf karo:
    pygame.time.wait(500)      # emulator ko poori tarah band hone do
    pygame.event.clear()       # saare purane/stale events hatao

# ============================================================
# STEP 3: UI
# ============================================================
CONSOLE_COLORS = {
    "PSP": (80, 160, 255),   # blue
    "PS2": (100, 220, 120),  # green
    "PS3": (255, 170, 60),   # orange
}
# Auto-detect hue naye consoles ko in colors me se milega
EXTRA_COLORS = [
    (255, 105, 180),  # pink
    (180, 120, 255),  # purple
    (255, 230, 90),   # yellow
    (90, 230, 230),   # cyan
    (255, 120, 90),   # coral
]

# Layout constants (list geometry - input hit-testing me bhi use hote hain)
SCREEN_W, SCREEN_H = 1280, 720
LIST_TOP = 100
ROW_H = 50
VISIBLE = 11  # ek screen pe kitni games dikhengi
EXIT_BTN = pygame.Rect(1140, 18, 110, 44)

# Gamepad analog/d-pad hold karne par auto-repeat timing (ms)
AXIS_DEADZONE = 0.5
NAV_REPEAT_DELAY = 350
NAV_REPEAT_RATE = 120

TAP_SLOP = 12  # itne pixels se kam hila finger = tap, zyada = drag/scroll


def build_console_colors(consoles):
    """Har console ko ek color do - naye (auto-detect) walon ko EXTRA_COLORS se."""
    colors = dict(CONSOLE_COLORS)
    i = 0
    for name in consoles:
        if name not in colors:
            colors[name] = EXTRA_COLORS[i % len(EXTRA_COLORS)]
            i += 1
    return colors


def row_at(pos, scroll, game_count):
    """Screen position -> games list ka index (ya None agar list ke bahar)."""
    x, y = pos
    if not (30 <= x <= 1210):
        return None
    idx = int(y - (LIST_TOP - 4)) // ROW_H
    if idx < 0 or idx >= VISIBLE:
        return None
    i = scroll + idx
    if i >= game_count:
        return None
    return i


def gamepad_nav_dir(joystick):
    """Gamepad ka current navigation direction: -1 = up, +1 = down, 0 = kuch nahi.
    D-pad (hat) aur left analog stick dono poll karte hain."""
    if joystick is None:
        return 0
    if joystick.get_numhats() > 0:
        hat = joystick.get_hat(0)
        if hat[1] == -1:
            return 1
        if hat[1] == 1:
            return -1
    if joystick.get_numaxes() > 1:
        axis = joystick.get_axis(1)  # left stick vertical
        if axis > AXIS_DEADZONE:
            return 1
        if axis < -AXIS_DEADZONE:
            return -1
    return 0


def main():
    pygame.init()
    pygame.joystick.init()
    # Keyboard key hold karne par auto-repeat (navigate karna fast ho jata hai)
    pygame.key.set_repeat(NAV_REPEAT_DELAY, NAV_REPEAT_RATE)

    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("MY CONSOLE - Game Machine")
    clock = pygame.time.Clock()
    fullscreen = False

    font_big = pygame.font.SysFont("arial", 44, bold=True)
    font_item = pygame.font.SysFont("arial", 26)
    font_small = pygame.font.SysFont("arial", 18)

    consoles = discover_consoles()
    console_colors = build_console_colors(consoles)
    games = scan_games(consoles)
    selected = 0
    scroll = 0
    ensure_visible = True  # selection change hui to scroll adjust karo

    # Gamepad hold-to-repeat state
    pad_dir = 0
    pad_next_repeat = 0

    # Touch state (tap vs drag alag pehchanne ke liye)
    touch_id = None
    touch_start = None
    touch_last_y = 0.0
    touch_moved = False
    touch_scroll_accum = 0.0

    def move_selection(delta):
        nonlocal selected, ensure_visible
        if games:
            selected = (selected + delta) % len(games)
            ensure_visible = True

    def set_selection(index):
        nonlocal selected, ensure_visible
        selected = index
        ensure_visible = True

    def do_launch():
        nonlocal pad_dir
        if games:
            launch_game(games[selected], consoles)
            pad_dir = 0  # game ke baad stale hold-state mat rakho

    running = True
    while running:
        w, h = screen.get_size()
        max_scroll = max(0, len(games) - VISIBLE)

        # ---------- INPUT (events) ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ----- Keyboard -----
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    move_selection(1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    move_selection(-1)
                elif event.key == pygame.K_PAGEDOWN and games:
                    set_selection(min(selected + VISIBLE, len(games) - 1))
                elif event.key == pygame.K_PAGEUP and games:
                    set_selection(max(selected - VISIBLE, 0))
                elif event.key == pygame.K_HOME and games:
                    set_selection(0)
                elif event.key == pygame.K_END and games:
                    set_selection(len(games) - 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    do_launch()
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else 0
                    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

            # ----- Gamepad -----
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button
                    do_launch()

            # Gamepad launcher start hone ke BAAD lagao to bhi kaam kare
            elif event.type == pygame.JOYDEVICEADDED:
                joystick = pygame.joystick.Joystick(event.device_index)
                joystick.init()
            elif event.type == pygame.JOYDEVICEREMOVED:
                if joystick is not None and joystick.get_instance_id() == event.instance_id:
                    joystick = None
                    pad_dir = 0

            # ----- Mouse -----
            # NOTE: touch karne par SDL nakli (synthetic) mouse events bhi bhejta
            # hai - unhe skip karo, warna touch handling double ho jayegi.
            elif event.type == pygame.MOUSEMOTION:
                if not getattr(event, "touch", False):
                    r = row_at(event.pos, scroll, len(games))
                    if r is not None:
                        selected = r  # hover = select (scroll ko mat chhedo)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not getattr(event, "touch", False):
                    if EXIT_BTN.collidepoint(event.pos):
                        running = False
                    else:
                        r = row_at(event.pos, scroll, len(games))
                        if r is not None:
                            selected = r
                            do_launch()

            elif event.type == pygame.MOUSEWHEEL:
                # Wheel se sirf list scroll hoti hai, selection wahi rehti hai
                scroll = max(0, min(scroll - event.y * 3, max_scroll))

            # ----- Touch -----
            elif event.type == pygame.FINGERDOWN:
                if touch_id is None:  # sirf pehli ungli track karo
                    touch_id = event.finger_id
                    touch_start = (event.x * w, event.y * h)
                    touch_last_y = event.y * h
                    touch_moved = False
                    touch_scroll_accum = 0.0

            elif event.type == pygame.FINGERMOTION:
                if event.finger_id == touch_id and touch_start is not None:
                    y = event.y * h
                    if abs(y - touch_start[1]) > TAP_SLOP:
                        touch_moved = True
                    if touch_moved:
                        # Finger upar = list neeche scroll (natural scrolling)
                        touch_scroll_accum += touch_last_y - y
                        while touch_scroll_accum >= ROW_H:
                            scroll = min(scroll + 1, max_scroll)
                            touch_scroll_accum -= ROW_H
                        while touch_scroll_accum <= -ROW_H:
                            scroll = max(scroll - 1, 0)
                            touch_scroll_accum += ROW_H
                    touch_last_y = y

            elif event.type == pygame.FINGERUP:
                if event.finger_id == touch_id:
                    if touch_start is not None and not touch_moved:
                        pos = (event.x * w, event.y * h)
                        if EXIT_BTN.collidepoint(pos):
                            running = False
                        else:
                            r = row_at(pos, scroll, len(games))
                            if r is not None:
                                if r == selected:
                                    do_launch()  # selected pe dobara tap = launch
                                else:
                                    selected = r  # pehla tap = sirf select
                    touch_id = None
                    touch_start = None

        # ---------- INPUT (gamepad hold-to-repeat polling) ----------
        now = pygame.time.get_ticks()
        cur_dir = gamepad_nav_dir(joystick)
        if cur_dir != pad_dir:
            pad_dir = cur_dir
            if pad_dir != 0:
                move_selection(pad_dir)
                pad_next_repeat = now + NAV_REPEAT_DELAY
        elif pad_dir != 0 and now >= pad_next_repeat:
            move_selection(pad_dir)
            pad_next_repeat = now + NAV_REPEAT_RATE

        # Keyboard/gamepad navigation ke baad selected hamesha screen pe rahe
        if ensure_visible:
            if selected < scroll:
                scroll = selected
            elif selected >= scroll + VISIBLE:
                scroll = selected - VISIBLE + 1
            ensure_visible = False
        scroll = max(0, min(scroll, max_scroll))

        # ---------- DRAWING ----------
        screen.fill((13, 13, 22))

        title = font_big.render("GAME MACHINE", True, (0, 200, 255))
        screen.blit(title, (40, 18))
        if games:
            count = font_small.render(f"{len(games)} games  |  {selected + 1}/{len(games)}", True, (110, 110, 110))
            screen.blit(count, (44, 68))

        # EXIT button (mouse/touch ke liye - fullscreen me Esc nahi dhundhna padega)
        pygame.draw.rect(screen, (60, 20, 25), EXIT_BTN, border_radius=8)
        pygame.draw.rect(screen, (200, 70, 80), EXIT_BTN, width=2, border_radius=8)
        exit_label = font_item.render("EXIT", True, (255, 120, 130))
        screen.blit(exit_label, exit_label.get_rect(center=EXIT_BTN.center))

        if not games:
            msg = font_item.render("Koi game nahi mili! CONFIG me path check karo.", True, (255, 80, 80))
            screen.blit(msg, (40, 120))
        else:
            y = LIST_TOP
            for i in range(scroll, min(scroll + VISIBLE, len(games))):
                game = games[i]
                tag_color = console_colors.get(game["console"], (150, 150, 150))
                if i == selected:
                    pygame.draw.rect(screen, (0, 80, 145), (30, y - 4, 1180, 46), border_radius=6)
                    color = (255, 255, 255)
                else:
                    color = (165, 165, 165)
                tag = font_item.render(f"[{game['console']}]", True, tag_color)
                item = font_item.render(game["name"], True, color)
                screen.blit(tag, (44, y))
                screen.blit(item, (140, y))
                y += ROW_H

            # Scrollbar (mouse wheel / touch drag karte waqt position dikhe)
            if len(games) > VISIBLE:
                track_top = LIST_TOP - 4
                track_h = VISIBLE * ROW_H
                bar_h = max(30, int(track_h * VISIBLE / len(games)))
                bar_y = track_top + int((track_h - bar_h) * scroll / max_scroll)
                pygame.draw.rect(screen, (35, 35, 50), (1222, track_top, 8, track_h), border_radius=4)
                pygame.draw.rect(screen, (0, 140, 220), (1222, bar_y, 8, bar_h), border_radius=4)

        hint1 = font_small.render(
            "Keyboard: Up/Down + Enter  |  Gamepad: D-pad/Stick + A  |  F11 = fullscreen  |  Esc = exit",
            True, (110, 110, 110))
        hint2 = font_small.render(
            "Mouse: hover + click = launch, wheel = scroll  |  Touch: tap = select, dobara tap = launch, drag = scroll",
            True, (110, 110, 110))
        screen.blit(hint1, (40, 662))
        screen.blit(hint2, (40, 688))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
