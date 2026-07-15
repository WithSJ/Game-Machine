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
  Keyboard : Up/Down = navigate, Enter = launch, Esc = exit
  Gamepad  : D-pad = navigate, A button = launch
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
    selected = 0
    scroll = 0
    VISIBLE = 11  # ek screen pe kitni games dikhengi

    running = True
    while running:
        # ---------- INPUT ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_DOWN and games:
                    selected = (selected + 1) % len(games)
                elif event.key == pygame.K_UP and games:
                    selected = (selected - 1) % len(games)
                elif event.key == pygame.K_RETURN and games:
                    launch_game(games[selected])

            elif event.type == pygame.JOYHATMOTION and games:
                if event.value[1] == -1:
                    selected = (selected + 1) % len(games)
                elif event.value[1] == 1:
                    selected = (selected - 1) % len(games)

            elif event.type == pygame.JOYBUTTONDOWN and games:
                if event.button == 0:  # A button
                    launch_game(games[selected])

        # Scroll window adjust karo taaki selected hamesha dikhe
        if selected < scroll:
            scroll = selected
        elif selected >= scroll + VISIBLE:
            scroll = selected - VISIBLE + 1

        # ---------- DRAWING ----------
        screen.fill((13, 13, 22))

        title = font_big.render("GAME MACHINE", True, (0, 200, 255))
        screen.blit(title, (40, 18))
        if games:
            count = font_small.render(f"{len(games)} games  |  {selected + 1}/{len(games)}", True, (110, 110, 110))
            screen.blit(count, (44, 68))

        if not games:
            msg = font_item.render("Koi game nahi mili! CONFIG me path check karo.", True, (255, 80, 80))
            screen.blit(msg, (40, 120))
        else:
            y = 100
            for i in range(scroll, min(scroll + VISIBLE, len(games))):
                game = games[i]
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

        hint = font_small.render("Up/Down ya D-pad = navigate  |  Enter ya A = launch  |  Esc = exit", True, (110, 110, 110))
        screen.blit(hint, (40, 685))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
