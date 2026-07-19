"""
GAME MACHINE - Header drawing (logo, clock, pad status, size chip, exit button).
"""
import time

import pygame
import pygame.gfxdraw

from ui.theme import (
    SCREEN_W, PAD_X, COL_BG, COL_TEXT, COL_DIMMER, COL_PANEL2, COL_CARD_BORDER,
    COL_PAD_OK, COL_BTN_B, COL_BRAND, REC_COLOR, mix,
)
from ui.helpers import spaced_text


def draw_header(gm, now):
    """Draw the header bar: logo, clock, pad status, size chip, exit button."""
    scr = gm.screen
    accent = gm.accent()

    # Logo diamond + title
    logo_pts = [(PAD_X + 7, 26), (PAD_X + 14, 33), (PAD_X + 7, 40), (PAD_X, 33)]
    pygame.gfxdraw.filled_polygon(scr, logo_pts, COL_BRAND)
    pygame.gfxdraw.aapolygon(scr, logo_pts, COL_BRAND)
    x_end = spaced_text(scr, gm.f_logo, "GAME MACHINE", COL_TEXT, (PAD_X + 26, 20), 5)
    sub = gm.f_sub.render("v1.1.0 · EMULATOR FRONTEND", True, COL_DIMMER)
    scr.blit(sub, (x_end + 12, 30))

    # EXIT button (rightmost) — archetype B: rounded chip, destructive semantic
    gm.exit_rect = pygame.Rect(int(SCREEN_W - PAD_X - 58), 20, 58, 28)
    exit_focused = gm.header_focus == 2
    pygame.draw.rect(scr, mix(COL_BG, COL_BTN_B, 0.15), gm.exit_rect, border_radius=6)
    if exit_focused:
        pygame.draw.rect(scr, COL_BTN_B, gm.exit_rect, 2, border_radius=6)
    else:
        pygame.draw.rect(scr, COL_BTN_B, gm.exit_rect, 1, border_radius=6)
    ex = gm.f_sub.render("EXIT", True, COL_BTN_B)
    scr.blit(ex, ex.get_rect(center=gm.exit_rect.center))

    # SETTINGS button (left of EXIT) — archetype B
    settings_focused = gm.header_focus == 1
    settings_label = gm.f_sub.render("SETTINGS", True, REC_COLOR)
    sw = settings_label.get_width() + 24
    gm.settings_rect = pygame.Rect(gm.exit_rect.x - 10 - sw, 20, sw, 28)
    pygame.draw.rect(scr, COL_PANEL2, gm.settings_rect, border_radius=6)
    if settings_focused:
        pygame.draw.rect(scr, REC_COLOR, gm.settings_rect, 2, border_radius=6)
    else:
        pygame.draw.rect(scr, COL_CARD_BORDER, gm.settings_rect, 1, border_radius=6)
    scr.blit(settings_label, settings_label.get_rect(center=gm.settings_rect.center))

    # Clock (left of SETTINGS)
    clock_s = gm.f_clock.render(time.strftime("%I:%M %p").lstrip("0"), True, COL_TEXT)
    cx = gm.settings_rect.x - 18 - clock_s.get_width()
    scr.blit(clock_s, (cx, 24))

    # Pad status
    pad_txt = "● PAD 1" if gm.joystick else "○ NO PAD"
    pad_col = COL_PAD_OK if gm.joystick else COL_DIMMER
    pad_s = gm.f_small.render(pad_txt, True, pad_col)
    scr.blit(pad_s, (cx - 18 - pad_s.get_width(), 27))

    # Size settings chip
    size_focused = gm.header_focus == 0
    size_txt = f"SIZE: {gm.settings['size'].upper()}"
    size_s = gm.f_small.render(size_txt, True, COL_TEXT)
    gm.size_rect = pygame.Rect(cx - 36 - pad_s.get_width() - (size_s.get_width() + 24), 20, size_s.get_width() + 24, 28)
    pygame.draw.rect(scr, COL_PANEL2, gm.size_rect, border_radius=6)
    if size_focused:
        pygame.draw.rect(scr, accent, gm.size_rect, 2, border_radius=6)
    else:
        pygame.draw.rect(scr, COL_CARD_BORDER, gm.size_rect, 1, border_radius=6)
    scr.blit(size_s, size_s.get_rect(center=gm.size_rect.center))
