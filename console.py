"""
MY CONSOLE - Custom Emulator Frontend (v2 - Sandeep's Game Machine)
====================================================================
Configured for: D:\\Game Machine
  PSP  -> PPSSPP_win + PPSSPP_ios
  PS2  -> PCSX2_win  + PCSX2_ios
  PS3  -> RPCS3_win  + RPCS3_ios

Kaise chalaye:
  1. pip install pygame   (agar pehle se nahi kiya)
  2. Ye file D:\\Game Machine me rakho (already wahi hai)
  3. python my_console.py

Controls:
  Keyboard : Up/Down = navigate, Left/Right = tab change, Enter = launch, Esc = exit
  Gamepad  : D-pad Up/Down = navigate, D-pad Left/Right = tab change, A button = launch

Tabs:
  RECENT = jo bhi game last me khela (kisi bhi console ka), sabse naya sabse upar
  PSP / PS2 / PS3 = sirf us console ki games
"""

import os
import re
import json
import time
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
def scan_games():
    games = []
    for console_name, cfg in CONSOLES.items():
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
# RECENT GAMES - last played list (JSON file me save hoti hai)
# ============================================================
RECENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recent_games.json")
RECENT_LIMIT = 20  # recent tab me max itni games

def load_recent():
    try:
        with open(RECENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        pass
    return []

def save_recent(recent):
    try:
        with open(RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(recent, f, indent=2)
    except OSError:
        pass  # save fail ho jaye to bhi launcher chalta rahe

def add_to_recent(recent, game):
    # pehle se list me hai to purani entry hatao, phir sabse upar daalo
    recent[:] = [r for r in recent if r.get("path") != game["path"]]
    recent.insert(0, {"path": game["path"], "time": time.time()})
    del recent[RECENT_LIMIT:]
    save_recent(recent)

def recent_games_list(recent, games):
    # recent file ki entries ko scan hui games se match karo (same order me)
    by_path = {g["path"]: g for g in games}
    return [by_path[r["path"]] for r in recent if r.get("path") in by_path]

# ============================================================
# STEP 2: GAME LAUNCHING
# ============================================================
def launch_game(game):
    cfg = CONSOLES[game["console"]]
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

TABS = ["RECENT"] + list(CONSOLES.keys())  # RECENT, PSP, PS2, PS3
TAB_COLORS = {"RECENT": (255, 90, 200)}    # pink; baaki tabs console color use karenge
TAB_COLORS.update(CONSOLE_COLORS)

def games_for_tab(tab, games, recent):
    if tab == "RECENT":
        return recent_games_list(recent, games)
    return [g for g in games if g["console"] == tab]

def main():
    pygame.init()
    pygame.joystick.init()

    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("MY CONSOLE - Game Machine")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("arial", 44, bold=True)
    font_item = pygame.font.SysFont("arial", 26)
    font_small = pygame.font.SysFont("arial", 18)

    games = scan_games()
    recent = load_recent()
    tab_index = 0  # RECENT tab se shuru
    tab_games = games_for_tab(TABS[tab_index], games, recent)
    selected = 0
    scroll = 0
    VISIBLE = 10  # ek screen pe kitni games dikhengi (tab bar ke neeche fit hoti hain)

    def switch_tab(direction):
        nonlocal tab_index, tab_games, selected, scroll
        tab_index = (tab_index + direction) % len(TABS)
        tab_games = games_for_tab(TABS[tab_index], games, recent)
        selected = 0
        scroll = 0

    def play(game):
        launch_game(game)
        add_to_recent(recent, game)
        # RECENT tab khuli ho to list turant refresh karo
        nonlocal tab_games, selected, scroll
        if TABS[tab_index] == "RECENT":
            tab_games = games_for_tab("RECENT", games, recent)
            selected = 0
            scroll = 0

    running = True
    while running:
        # ---------- INPUT ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT:
                    switch_tab(+1)
                elif event.key == pygame.K_LEFT:
                    switch_tab(-1)
                elif event.key == pygame.K_DOWN and tab_games:
                    selected = (selected + 1) % len(tab_games)
                elif event.key == pygame.K_UP and tab_games:
                    selected = (selected - 1) % len(tab_games)
                elif event.key == pygame.K_RETURN and tab_games:
                    play(tab_games[selected])

            elif event.type == pygame.JOYHATMOTION:
                if event.value[0] == 1:
                    switch_tab(+1)
                elif event.value[0] == -1:
                    switch_tab(-1)
                elif event.value[1] == -1 and tab_games:
                    selected = (selected + 1) % len(tab_games)
                elif event.value[1] == 1 and tab_games:
                    selected = (selected - 1) % len(tab_games)

            elif event.type == pygame.JOYBUTTONDOWN and tab_games:
                if event.button == 0:  # A button
                    play(tab_games[selected])

        # Scroll window adjust karo taaki selected hamesha dikhe
        if selected < scroll:
            scroll = selected
        elif selected >= scroll + VISIBLE:
            scroll = selected - VISIBLE + 1

        # ---------- DRAWING ----------
        screen.fill((13, 13, 22))

        title = font_big.render("GAME MACHINE", True, (0, 200, 255))
        screen.blit(title, (40, 18))

        # ---- TAB BAR ----
        tab_x = 40
        tab_y = 78
        for i, tab in enumerate(TABS):
            tab_color = TAB_COLORS.get(tab, (150, 150, 150))
            label = font_item.render(tab, True, (255, 255, 255) if i == tab_index else (130, 130, 130))
            w = label.get_width() + 36
            if i == tab_index:
                pygame.draw.rect(screen, (0, 80, 145), (tab_x, tab_y, w, 40), border_radius=8)
                pygame.draw.rect(screen, tab_color, (tab_x, tab_y + 36, w, 4), border_radius=2)
            screen.blit(label, (tab_x + 18, tab_y + 5))
            tab_x += w + 12

        if tab_games:
            count = font_small.render(f"{len(tab_games)} games  |  {selected + 1}/{len(tab_games)}", True, (110, 110, 110))
            screen.blit(count, (tab_x + 20, tab_y + 12))

        if not tab_games:
            if TABS[tab_index] == "RECENT":
                msg = font_item.render("Abhi tak koi game nahi kheli - koi bhi game launch karo, yahan dikhegi!", True, (255, 170, 60))
            else:
                msg = font_item.render("Koi game nahi mili! CONFIG me path check karo.", True, (255, 80, 80))
            screen.blit(msg, (40, 160))
        else:
            y = 140
            for i in range(scroll, min(scroll + VISIBLE, len(tab_games))):
                game = tab_games[i]
                tag_color = CONSOLE_COLORS.get(game["console"], (150, 150, 150))
                if i == selected:
                    pygame.draw.rect(screen, (0, 80, 145), (30, y - 4, 1180, 46), border_radius=6)
                    color = (255, 255, 255)
                else:
                    color = (165, 165, 165)
                tag = font_item.render(f"[{game['console']}]", True, tag_color)
                item = font_item.render(game["name"], True, color)
                screen.blit(tag, (44, y))
                screen.blit(item, (140, y))
                y += 50

        hint = font_small.render("Left/Right = tab  |  Up/Down = navigate  |  Enter ya A = launch  |  Esc = exit", True, (110, 110, 110))
        screen.blit(hint, (40, 685))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
