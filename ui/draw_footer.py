"""
GAME MACHINE - Footer bar drawing.
"""
import pygame

from core.config import BASE
from ui.theme import SCREEN_W, PAD_X, FOOTER_Y, COL_FOOT_LINE, COL_DIM, COL_DIMMER, COL_TEXT, COL_PAD_OK, COL_BTN_B, COL_BTN_Y
from ui.helpers import key_hint


def draw_footer(gm, now):
    """Draw the footer bar with status and control hints."""
    scr = gm.screen

    pygame.draw.line(scr, COL_FOOT_LINE, (0, FOOTER_Y), (SCREEN_W, FOOTER_Y))
    ncons = max(0, len(gm.tabs) - 1)
    folder_str = gm.folders[0] if getattr(gm, "folders", None) else BASE
    status = gm.f_small.render(
        f"{folder_str.upper()}  ·  {len(gm.games)} GAMES SCANNED  ·  {ncons} CONSOLES",
        True, COL_DIMMER)
    scr.blit(status, (PAD_X, FOOTER_Y + 18))

    hx = SCREEN_W - PAD_X - 660
    hx = key_hint(scr, gm.f_mono, gm.f_hint, hx, FOOTER_Y + 14, "A", COL_PAD_OK, "Play")
    hx = key_hint(scr, gm.f_mono, gm.f_hint, hx, FOOTER_Y + 14, "B", COL_BTN_B, "Recents")
    hx = key_hint(scr, gm.f_mono, gm.f_hint, hx, FOOTER_Y + 14, "Y", COL_BTN_Y, "Random")
    hx = key_hint(scr, gm.f_mono, gm.f_hint, hx, FOOTER_Y + 14, "S", COL_TEXT, "Size")
    pill = pygame.Rect(hx, FOOTER_Y + 14, 44, 18)
    pygame.draw.rect(scr, COL_DIM, pill, 1, border_radius=9)
    pl = gm.f_mono.render("L1 R1", True, (185, 188, 194))
    scr.blit(pl, pl.get_rect(center=pill.center))
    scr.blit(gm.f_hint.render("Switch console", True, COL_DIM),
             (pill.right + 8, FOOTER_Y + 15))
