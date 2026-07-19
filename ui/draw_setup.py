"""
GAME MACHINE - Setup Screen drawing and interactions.
"""
import os
import math
import random
import tkinter as tk
from tkinter import filedialog, simpledialog
import pygame
import pygame.gfxdraw

from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT,
    COL_DIM, COL_DIMMER, COL_CARD_BORDER, COL_BTN_Y, COL_BTN_B, COL_PAD_OK,
    REC_COLOR, mix, ease_out
)
from ui.helpers import parallelogram


def pick_directory(title="Select Folder"):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askdirectory(title=title)
    root.destroy()
    return path


def pick_file(title="Select File", filetypes=None):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()
    return path


def ask_string(title, prompt, initialvalue=""):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    val = simpledialog.askstring(title, prompt, initialvalue=initialvalue)
    root.destroy()
    return val


def add_gm_folder_dialog(gm):
    # Temporarily minimize/toggle fullscreen to let dialog show cleanly
    if gm.fullscreen:
        pygame.display.set_mode((SCREEN_W, SCREEN_H))

    path = pick_directory(title="Select Game Machine Folder (containing _win and _ios subfolders)")

    if gm.fullscreen:
        gm.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)

    if path:
        norm_path = os.path.normpath(path)
        if norm_path not in gm.folders:
            gm.folders.append(norm_path)
            gm.toast = f"Added Folder: {os.path.basename(norm_path)}"
            gm.toast_until = pygame.time.get_ticks() + 2000
        else:
            gm.toast = "Folder already added!"
            gm.toast_until = pygame.time.get_ticks() + 2000


def add_custom_console_dialog(gm):
    if gm.fullscreen:
        pygame.display.set_mode((SCREEN_W, SCREEN_H))

    # Step 1: Select Emulator executable directly
    exe = pick_file(title="Select Emulator Executable (.exe)", filetypes=[("Executable Files", "*.exe")])
    if exe:
        exe = os.path.normpath(exe)
        
        # Automatically determine console name from the emulator executable base name
        exe_base = os.path.splitext(os.path.basename(exe))[0].lower()
        if "ppsspp" in exe_base:
            name = "PSP"
        elif "pcsx2" in exe_base:
            name = "PS2"
        elif "rpcs3" in exe_base:
            name = "PS3"
        elif "dolphin" in exe_base:
            name = "DOLPHIN"
        elif "retroarch" in exe_base:
            name = "RETROARCH"
        elif "citra" in exe_base:
            name = "CITRA"
        elif "yuzu" in exe_base:
            name = "YUZU"
        elif "ryujinx" in exe_base:
            name = "RYUJINX"
        elif "xemu" in exe_base:
            name = "XBOX"
        elif "cemu" in exe_base:
            name = "WIIU"
        else:
            name = exe_base.upper()

        # Check standard resolved consoles for the folders added so far
        from core.scanner import discover_consoles
        active_standard_consoles = discover_consoles(gm.folders)

        # Ensure name uniqueness
        orig_name = name
        counter = 2
        while name in gm.custom_consoles or name in active_standard_consoles:
            name = f"{orig_name} {counter}"
            counter += 1

        # Step 2: Select ROMs folder
        roms = pick_directory(title=f"Select {name} Game ROMs Folder")
        if roms:
            roms = os.path.normpath(roms)
            
            # Step 3: Select Extensions
            exts_str = ask_string("File Extensions", f"Enter comma-separated extensions for {name}:", initialvalue=".iso,.cso,.chd")
            if not exts_str:
                exts_str = ".iso,.cso,.chd"
            exts = [e.strip().lower() for e in exts_str.split(",") if e.strip()]

            # Save custom console
            gm.custom_consoles[name] = {
                "rom_folder": roms,
                "extensions": exts,
                "emulator": exe,
                "args": []
            }
            gm.toast = f"Added Custom Console: {name}"
            gm.toast_until = pygame.time.get_ticks() + 2000

    if gm.fullscreen:
        gm.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)


def draw_setup(gm, now):
    scr = gm.screen
    accent = REC_COLOR  # Cyan theme accent for setup screen

    # Draw dark background
    scr.fill(COL_BG)

    # Draw floating background particles
    gm._overlay.fill((0, 0, 0, 0))
    for pt in gm.particles:
        pt["y"] -= pt["v"]
        if pt["y"] < -4:
            pt["y"] = SCREEN_H + 4
            pt["x"] = random.uniform(0, SCREEN_W)
        tw = 0.25 + 0.35 * abs(math.sin(now / 1400 + pt["ph"]))
        pygame.draw.circle(gm._overlay, accent + (int(tw * 255),),
                           (int(pt["x"]), int(pt["y"])), pt["s"])
    scr.blit(gm._overlay, (0, 0))

    # Title Banner
    title_s = gm.f_hero.render("GAME MACHINE SETUP", True, COL_TEXT)
    scr.blit(title_s, (60, 40))
    sub_s = gm.f_small.render("Configure your Game Machine directory or add custom console executables below.", True, COL_DIM)
    scr.blit(sub_s, (60, 92))

    # --- LEFT COLUMN: Configured Folders & Consoles ---
    left_x, left_y, left_w, left_h = 60, 130, 600, 480
    pygame.draw.rect(scr, COL_PANEL, (left_x, left_y, left_w, left_h), border_radius=12)
    pygame.draw.rect(scr, COL_CARD_BORDER, (left_x, left_y, left_w, left_h), 1, border_radius=12)

    # Panel Title
    p_title_s = gm.f_tab.render("CONFIGURED FOLDERS & CONSOLES", True, accent)
    scr.blit(p_title_s, (left_x + 20, left_y + 20))

    # Draw List of Items
    items = []
    for f in gm.folders:
        items.append(("folder", f))
    for name, cfg in gm.custom_consoles.items():
        items.append(("console", f"{name}: {os.path.basename(cfg['emulator'])} -> {os.path.basename(cfg['rom_folder'])}"))

    gm.setup_delete_rects = []

    if not items:
        # Draw placeholder
        empty_s = gm.f_popup_name.render("No folders or custom consoles added.", True, COL_DIMMER)
        scr.blit(empty_s, (left_x + 20, left_y + 80))
        help_s = gm.f_small.render("Use the buttons on the right to add a Game Machine folder", True, COL_DIMMER)
        scr.blit(help_s, (left_x + 20, left_y + 115))
        help_s2 = gm.f_small.render("or map a custom emulator and ROM directory pair.", True, COL_DIMMER)
        scr.blit(help_s2, (left_x + 20, left_y + 135))
    else:
        item_y = left_y + 60
        for idx, (kind, text) in enumerate(items):
            if item_y + 45 > left_y + left_h:
                break  # Overrun
            
            # Row container
            row_r = pygame.Rect(left_x + 15, item_y, left_w - 30, 40)
            pygame.draw.rect(scr, COL_PANEL2, row_r, border_radius=6)
            pygame.draw.rect(scr, COL_CARD_BORDER, row_r, 1, border_radius=6)

            # Icon tag
            tag_text = "FOLDER" if kind == "folder" else "CUSTOM"
            tag_col = COL_PAD_OK if kind == "folder" else COL_BTN_Y
            tag_s = gm.f_chip.render(tag_text, True, tag_col)
            tag_r = pygame.Rect(row_r.x + 10, row_r.y + 10, tag_s.get_width() + 10, 20)
            pygame.draw.rect(scr, mix(COL_BG, tag_col, 0.2), tag_r, border_radius=4)
            scr.blit(tag_s, tag_s.get_rect(center=tag_r.center))

            # Path Text (clipped)
            path_s = gm.f_small.render(text, True, COL_TEXT)
            text_limit_w = row_r.w - tag_r.w - 70
            scr.set_clip(pygame.Rect(tag_r.right + 10, row_r.y, text_limit_w, row_r.h))
            scr.blit(path_s, (tag_r.right + 10, row_r.y + 11))
            scr.set_clip(None)

            # Delete [x] button
            del_r = pygame.Rect(row_r.right - 35, row_r.y + 8, 24, 24)
            gm.setup_delete_rects.append((idx, kind, text, del_r))
            
            # Highlight delete if hovered
            m_pos = pygame.mouse.get_pos()
            is_del_hover = del_r.collidepoint(m_pos)
            del_col = COL_BTN_B if is_del_hover else COL_DIMMER
            
            pygame.draw.rect(scr, mix(COL_BG, del_col, 0.15) if is_del_hover else COL_PANEL, del_r, border_radius=4)
            del_s = gm.f_popup_btn.render("X", True, del_col)
            scr.blit(del_s, del_s.get_rect(center=del_r.center))

            item_y += 48

    # --- RIGHT COLUMN: Menu Actions ---
    right_x, right_y, right_w = 690, 130, 530
    pygame.draw.rect(scr, COL_PANEL, (right_x, right_y, right_w, left_h), border_radius=12)
    pygame.draw.rect(scr, COL_CARD_BORDER, (right_x, right_y, right_w, left_h), 1, border_radius=12)

    # Panel Title
    r_title_s = gm.f_tab.render("ACTIONS", True, accent)
    scr.blit(r_title_s, (right_x + 20, right_y + 20))

    # Menu items configuration
    menu_items = [
        ("Add Game Machine Folder (Recommended)", True),
        ("Add Custom Emulator & ROMs", True),
        ("Show Setup Help & File Structure", True),
        ("Start Game Machine", len(items) > 0),
        ("Exit", True)
    ]

    gm.setup_menu_rects = []
    btn_y = right_y + 70
    btn_w, btn_h = right_w - 40, 48

    for idx, (label, enabled) in enumerate(menu_items):
        btn_r = pygame.Rect(right_x + 20, btn_y, btn_w, btn_h)
        gm.setup_menu_rects.append((idx, label, enabled, btn_r))

        is_selected = (gm.setup_sel == idx)
        
        # Decide colors based on state
        if not enabled:
            bg_col = COL_PANEL2
            border_col = COL_CARD_BORDER
            text_col = COL_DIMMER
        elif is_selected:
            bg_col = accent
            border_col = accent
            text_col = COL_BG
        else:
            bg_col = COL_PANEL2
            border_col = COL_CARD_BORDER
            text_col = COL_TEXT

        # Draw button using parallelogram styling
        parallelogram(scr, btn_r, bg_col, cut=8)
        if not is_selected and enabled:
            parallelogram(scr, btn_r, border_col, cut=8, width=1)

        # Label Text
        text_s = gm.f_btn.render(label, True, text_col)
        scr.blit(text_s, text_s.get_rect(center=btn_r.center))

        btn_y += 68

    # Navigation Hint at Bottom
    hint_y = left_y + left_h - 32
    hint_s = gm.f_mono.render("▲▼ = Navigate    Enter / Space = Confirm    Mouse Clicks Supported", True, COL_DIMMER)
    scr.blit(hint_s, (right_x + (right_w - hint_s.get_width()) // 2, hint_y))

    # --- HELP OVERLAY MODAL ---
    if getattr(gm, "setup_help_active", False):
        draw_setup_help_modal(gm, now)


def draw_setup_help_modal(gm, now):
    scr = gm.screen
    accent = REC_COLOR

    # Dark screen overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    scr.blit(overlay, (0, 0))

    # Help Panel
    pw, ph = 780, 520
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    panel_r = pygame.Rect(px, py, pw, ph)

    pygame.draw.rect(scr, COL_PANEL, panel_r, border_radius=14)
    pygame.draw.rect(scr, accent, (panel_r.x, panel_r.y, pw, 3), border_radius=14)
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), panel_r, 1, border_radius=14)

    # Title
    title_s = gm.f_popup_title.render("RECOMMENDED FILE & FOLDER STRUCTURE", True, accent)
    scr.blit(title_s, (panel_r.x + 30, panel_r.y + 24))

    # Close button [X]
    close_r = pygame.Rect(panel_r.right - 50, panel_r.y + 20, 30, 30)
    gm.setup_help_close_rect = close_r
    
    m_pos = pygame.mouse.get_pos()
    is_close_hover = close_r.collidepoint(m_pos)
    close_col = COL_BTN_B if is_close_hover else COL_DIM
    
    pygame.draw.rect(scr, COL_PANEL2 if not is_close_hover else mix(COL_BG, COL_BTN_B, 0.15), close_r, border_radius=6)
    close_s = gm.f_popup_btn.render("X", True, close_col)
    scr.blit(close_s, close_s.get_rect(center=close_r.center))

    # Structure text lines
    lines = [
        "A Game Machine folder houses all emulators and ROMs in a portable setup.",
        "Organize your folders as shown below under a single root directory:",
        "",
        "  [Game Machine Root Folder] (e.g. D:\\Game Machine\\)",
        "  ├── PPSSPP_win\\             ← PSP Emulator folder (contains PPSSPPWindows64.exe)",
        "  ├── PPSSPP_ios\\             ← PSP Game ROM files (.iso, .cso)",
        "  ├── PCSX2_win\\              ← PS2 Emulator folder (contains pcsx2-qt.exe)",
        "  ├── PCSX2_ios\\              ← PS2 Game ROM files (.iso, .chd)",
        "  ├── RPCS3_win\\              ← PS3 Emulator folder (contains rpcs3.exe)",
        "  └── RPCS3_ios\\              ← PS3 Game ROM files (.iso)",
        "",
        "Why follow this structure?",
        "1. Automatic Discovery: Any matching _win and _ios folder pairs are auto-detected.",
        "2. Complete Portability: Copy the whole root folder to another drive or machine,",
        "   launch console.py, and all emulator settings & savedata remain fully working.",
        "",
        "Press any key, ESC, or click [X] to return."
    ]

    ty = panel_r.y + 76
    for line in lines:
        if "├──" in line or "└──" in line or "  [" in line:
            font = gm.f_mono
            col = COL_TEXT
        elif "Why" in line or "1." in line or "2." in line:
            font = gm.f_small
            col = COL_DIM
        elif "Press any key" in line:
            font = gm.f_small
            col = accent
        else:
            font = gm.f_small
            col = COL_TEXT
            
        text_s = font.render(line, True, col)
        scr.blit(text_s, (panel_r.x + 36, ty))
        ty += 24
