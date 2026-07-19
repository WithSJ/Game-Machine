"""
GAME MACHINE - Settings panel with tabbed interface.

Tabs: FOLDERS | CONSOLES | DISPLAY | SYSTEM | ABOUT

Reuses the tkinter folder/file pickers from ui/draw_setup.py.
All option rows register their hit-rects on gm.settings_option_rects
so the app.py input handler can detect clicks/taps and keyboard/gamepad
navigation can move through them with UP/DOWN.
"""
import os

import pygame
import pygame.gfxdraw

from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT,
    COL_DIM, COL_DIMMER, COL_CARD_BORDER, COL_PAD_OK, COL_BTN_B,
    COL_BTN_Y, COL_BRAND, COL_DESTRUCTIVE, COL_FALLBACK, COL_TEXT_LIGHT, REC_COLOR, mix, ease_out
)
from ui.helpers import parallelogram

TABS = ["FOLDERS", "CONSOLES", "DISPLAY", "SYSTEM", "ABOUT"]


def draw_settings(gm, now):
    """Draw the settings panel if active."""
    if not gm.settings_active:
        return

    scr = gm.screen
    accent = REC_COLOR  # Cyan accent for settings
    anim_p = max(0.0, min(1.0, (now - gm.settings_anim_start) / 220))
    scale = ease_out(anim_p)

    # Dark overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(180 * scale)))
    scr.blit(overlay, (0, 0))

    pw, ph = 760, 560
    px = (SCREEN_W - int(pw * scale)) // 2
    py = (SCREEN_H - int(ph * scale)) // 2
    popup_r = pygame.Rect(px, py, int(pw * scale), int(ph * scale))

    if scale >= 0.95:
        popup_r = pygame.Rect((SCREEN_W - pw) // 2, (SCREEN_H - ph) // 2, pw, ph)

        # Panel
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=14)
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, pw, 3), border_radius=14)
        pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), popup_r, 1, border_radius=14)

        # Close [X] button
        close_size = 26
        close_r = pygame.Rect(popup_r.right - close_size - 14, popup_r.y + 14, close_size, close_size)
        gm.settings_close_rect = close_r
        m_pos = pygame.mouse.get_pos()
        close_hover = close_r.collidepoint(m_pos)
        close_bg = mix(COL_BG, COL_BTN_B, 0.15) if close_hover else COL_PANEL2
        pygame.draw.rect(scr, close_bg, close_r, border_radius=6)
        pygame.draw.rect(scr, COL_BTN_B if close_hover else COL_CARD_BORDER, close_r, 1, border_radius=6)
        x_s = gm.f_popup_btn.render("X", True, COL_BTN_B if close_hover else COL_DIM)
        scr.blit(x_s, x_s.get_rect(center=close_r.center))

        # Title
        title_s = gm.f_popup_title.render("SETTINGS", True, accent)
        scr.blit(title_s, (popup_r.x + (pw - title_s.get_width()) // 2, popup_r.y + 18))

        # Tab bar
        tab_y = popup_r.y + 54
        tab_h = 36
        tab_w = (pw - 40) // len(TABS)
        gm.settings_tab_rects = []
        for i, tab_name in enumerate(TABS):
            tab_x = popup_r.x + 20 + i * tab_w
            tab_r = pygame.Rect(tab_x, tab_y, tab_w - 6, tab_h)
            gm.settings_tab_rects.append((i, tab_r))
            on = i == gm.settings_tab
            if on:
                pygame.draw.rect(scr, mix(COL_BG, accent, 0.2), tab_r, border_radius=6)
                pygame.draw.rect(scr, accent, tab_r, 2, border_radius=6)
            else:
                pygame.draw.rect(scr, COL_PANEL2, tab_r, border_radius=6)
                pygame.draw.rect(scr, COL_CARD_BORDER, tab_r, 1, border_radius=6)
            tab_s = gm.f_tab.render(tab_name, True, accent if on else COL_DIM)
            scr.blit(tab_s, tab_s.get_rect(center=tab_r.center))

        # Separator below tabs
        sep_y = tab_y + tab_h + 4
        pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 20, sep_y), (popup_r.right - 20, sep_y))

        # Content area
        content_r = pygame.Rect(popup_r.x + 20, sep_y + 8, pw - 40, ph - (sep_y - popup_r.y) - 52)

        # Reset option rects for this tab
        gm.settings_option_rects = []

        # Draw current tab content
        if gm.settings_tab == 0:
            _draw_folders_tab(gm, scr, content_r)
        elif gm.settings_tab == 1:
            _draw_consoles_tab(gm, scr, content_r)
        elif gm.settings_tab == 2:
            _draw_display_tab(gm, scr, content_r)
        elif gm.settings_tab == 3:
            _draw_system_tab(gm, scr, content_r)
        elif gm.settings_tab == 4:
            _draw_about_tab(gm, scr, content_r)

        # Clamp selection to valid range
        if gm.settings_option_rects:
            gm.settings_sel = min(gm.settings_sel, len(gm.settings_option_rects) - 1)
        else:
            gm.settings_sel = 0

        # Hint text at bottom
        hint = gm.f_mono.render("▲▼ Navigate  ◄►/L1 R1 Switch Tab  A=Confirm  B/Esc=Close  [X]=Close", True, COL_DIMMER)
        scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 24))
    else:
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=int(14 * scale))
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, popup_r.w, max(2, int(3 * scale))),
                         border_radius=int(14 * scale))


# ============================================================
# Helper: draw a generic option row
# ============================================================
def _draw_option_row(gm, scr, x, y, w, h, label, value, col, action):
    """Draw a row with label (left) and optional value (right).

    Appends (action, rect) to gm.settings_option_rects. The selection
    highlight is determined by comparing the row's index (current length
    of settings_option_rects) against gm.settings_sel.
    """
    idx = len(gm.settings_option_rects)
    on = idx == gm.settings_sel
    r = pygame.Rect(x, y, w, h)
    gm.settings_option_rects.append((action, r))

    if on:
        pygame.draw.rect(scr, mix(COL_BG, col, 0.25), r, border_radius=8)
        pygame.draw.rect(scr, col, r, 2, border_radius=8)
        pygame.draw.rect(scr, col, (r.x, r.y + 6, 3, r.h - 12))
    else:
        pygame.draw.rect(scr, COL_PANEL2, r, border_radius=8)
        pygame.draw.rect(scr, COL_CARD_BORDER, r, 1, border_radius=8)

    text_col = COL_TEXT_LIGHT if on else COL_DIM
    lbl_s = gm.f_btn.render(label, True, text_col)
    scr.blit(lbl_s, (r.x + 16, r.centery - lbl_s.get_height() // 2))

    if value:
        val_s = gm.f_small.render(value, True, col if on else COL_DIMMER)
        scr.blit(val_s, (r.right - val_s.get_width() - 16, r.centery - val_s.get_height() // 2))


def _draw_add_button(gm, scr, x, y, w, h, label, action):
    """Draw a centered '+ ADD ...' button and register it."""
    idx = len(gm.settings_option_rects)
    on = idx == gm.settings_sel
    r = pygame.Rect(x, y, w, h)
    gm.settings_option_rects.append((action, r))
    add_col = COL_PAD_OK
    if on:
        pygame.draw.rect(scr, mix(COL_BG, add_col, 0.25), r, border_radius=8)
        pygame.draw.rect(scr, add_col, r, 2, border_radius=8)
    else:
        pygame.draw.rect(scr, COL_PANEL2, r, border_radius=8)
        pygame.draw.rect(scr, COL_CARD_BORDER, r, 1, border_radius=8)
    add_s = gm.f_btn.render(label, True, add_col if on else COL_DIM)
    scr.blit(add_s, add_s.get_rect(center=r.center))


# ============================================================
# Tab: FOLDERS
# ============================================================
def _draw_folders_tab(gm, scr, content_r):
    y = content_r.y
    row_h = 44
    row_w = content_r.w
    col = REC_COLOR

    hdr_s = gm.f_tab.render("CONFIGURED FOLDERS", True, col)
    scr.blit(hdr_s, (content_r.x, y))
    y += 32

    if not gm.folders:
        empty_s = gm.f_small.render("No folders configured. Add one below.", True, COL_DIMMER)
        scr.blit(empty_s, (content_r.x + 8, y + 8))
        y += row_h + 8
    else:
        for i, folder in enumerate(gm.folders):
            _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                             os.path.basename(folder), folder, col,
                             f"delete_folder:{i}")
            y += row_h + 8

    y += 8
    _draw_add_button(gm, scr, content_r.x, y, row_w, row_h, "+ ADD FOLDER", "add_folder")


# ============================================================
# Tab: CONSOLES
# ============================================================
def _draw_consoles_tab(gm, scr, content_r):
    y = content_r.y
    row_h = 44
    row_w = content_r.w

    # --- Auto-detected consoles (read-only) ---
    hdr_s = gm.f_tab.render("AUTO-DETECTED CONSOLES", True, COL_DIM)
    scr.blit(hdr_s, (content_r.x, y))
    y += 32

    auto_consoles = {name: cfg for name, cfg in gm.consoles.items()
                     if name not in gm.custom_consoles}
    for name, cfg in auto_consoles.items():
        r = pygame.Rect(content_r.x, y, row_w, row_h)
        pygame.draw.rect(scr, COL_PANEL2, r, border_radius=8)
        pygame.draw.rect(scr, COL_CARD_BORDER, r, 1, border_radius=8)
        col = gm.colors.get(name, COL_FALLBACK)
        chip_s = gm.f_chip.render(name, True, col)
        chip_r = pygame.Rect(r.x + 12, r.centery - 10, chip_s.get_width() + 10, 20)
        pygame.draw.rect(scr, mix(COL_BG, col, 0.2), chip_r, border_radius=4)
        scr.blit(chip_s, chip_s.get_rect(center=chip_r.center))
        emu_name = os.path.basename(cfg["emulator"])
        path_s = gm.f_small.render(emu_name, True, COL_DIM)
        scr.blit(path_s, (chip_r.right + 12, r.centery - path_s.get_height() // 2))
        count = sum(1 for g in gm.games if g["console"] == name)
        count_s = gm.f_small.render(f"{count} games", True, COL_DIMMER)
        scr.blit(count_s, (r.right - count_s.get_width() - 16, r.centery - count_s.get_height() // 2))
        y += row_h + 4
        if y > content_r.bottom - row_h - 60:
            break

    # --- Custom consoles (editable) ---
    y += 8
    hdr2_s = gm.f_tab.render("CUSTOM CONSOLES", True, COL_BTN_Y)
    scr.blit(hdr2_s, (content_r.x, y))
    y += 32

    if not gm.custom_consoles:
        empty_s = gm.f_small.render("No custom consoles. Add one below.", True, COL_DIMMER)
        scr.blit(empty_s, (content_r.x + 8, y + 8))
        y += row_h + 8
    else:
        for name, cfg in gm.custom_consoles.items():
            label = name
            value = f"{os.path.basename(cfg['emulator'])} -> {os.path.basename(cfg['rom_folder'])}"
            _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                             label, value, COL_BTN_Y,
                             f"delete_console:{name}")
            y += row_h + 8

    y += 8
    _draw_add_button(gm, scr, content_r.x, y, row_w, row_h, "+ ADD CUSTOM CONSOLE", "add_console")


# ============================================================
# Tab: DISPLAY
# ============================================================
def _draw_display_tab(gm, scr, content_r):
    y = content_r.y
    row_h = 56
    row_w = content_r.w
    col = REC_COLOR

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Grid Size", gm.settings.get("size", "medium").upper(),
                     col, "cycle_grid_size")
    y += row_h + 8

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Fullscreen", "ON" if gm.fullscreen else "OFF",
                     col, "toggle_fullscreen")


# ============================================================
# Tab: SYSTEM
# ============================================================
def _draw_system_tab(gm, scr, content_r):
    y = content_r.y
    row_h = 48
    row_w = content_r.w

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Auto-Start", "ON" if gm.auto_start else "OFF",
                     COL_PAD_OK, "toggle_auto_start")
    y += row_h + 8

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Lock Screen", "", REC_COLOR, "lock_screen")
    y += row_h + 8

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Restart PC", "", COL_PAD_OK, "restart")
    y += row_h + 8

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Shutdown PC", "", COL_DESTRUCTIVE, "shutdown")
    y += row_h + 8

    _draw_option_row(gm, scr, content_r.x, y, row_w, row_h,
                     "Exit Game Machine", "", COL_BRAND, "exit_gm")


# ============================================================
# Tab: ABOUT
# ============================================================
def _draw_about_tab(gm, scr, content_r):
    y = content_r.y + 20
    col = REC_COLOR

    title = gm.f_hero.render("GAME MACHINE", True, COL_TEXT)
    scr.blit(title, (content_r.x + 20, y))
    y += title.get_height() + 4

    sub = gm.f_sub.render("v1.1.0 - EMULATOR FRONTEND", True, COL_DIMMER)
    scr.blit(sub, (content_r.x + 20, y))
    y += sub.get_height() + 24

    info_lines = [
        f"Library Folder:  {gm.folders[0] if gm.folders else 'Not configured'}",
        f"Games Scanned:   {len(gm.games)}",
        f"Consoles Active: {len(gm.consoles)}",
        f"Custom Consoles: {len(gm.custom_consoles)}",
        f"Grid Size:       {gm.settings.get('size', 'medium').upper()}",
        f"Fullscreen:      {'ON' if gm.fullscreen else 'OFF'}",
        f"Auto-Start:      {'ON' if gm.auto_start else 'OFF'}",
    ]
    for line in info_lines:
        s = gm.f_small.render(line, True, COL_DIM)
        scr.blit(s, (content_r.x + 20, y))
        y += s.get_height() + 8

    y += 16
    tip = gm.f_small.render("Press A on any option to change it. Use L1/R1 to switch tabs.", True, col)
    scr.blit(tip, (content_r.x + 20, y))
