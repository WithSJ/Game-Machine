"""
GAME MACHINE - Tab bar drawing.
"""
import pygame

from ui.theme import SCREEN_W, PAD_X, COL_BG, COL_DIM, COL_DIMMER, mix
from ui.helpers import parallelogram


def draw_tabs(gm, now):
    """Draw the console tab bar."""
    scr = gm.screen
    L = gm.current_list()
    sel = min(gm.sel, len(L) - 1) if L else 0

    ty = 76
    hint_q = gm.f_chip.render("Q ◄", True, COL_DIMMER)
    scr.blit(hint_q, (PAD_X, ty + 10))
    tx = PAD_X + hint_q.get_width() + 12
    for i, (name, col) in enumerate(gm.tabs):
        on = i == gm.tab
        label = gm.f_tab.render(name, True, col if on else COL_DIM)
        r = pygame.Rect(tx, ty, label.get_width() + 46, 34)
        if on:
            parallelogram(scr, r, mix(COL_BG, col, 0.16))
            parallelogram(scr, r, col, width=1)
        else:
            parallelogram(scr, r, (18, 21, 28))
            parallelogram(scr, r, (32, 36, 46), width=1)
        scr.blit(label, label.get_rect(center=r.center))
        gm.tab_rects.append((i, r))
        tx = r.right + 10
    hint_e = gm.f_chip.render("► E", True, COL_DIMMER)
    scr.blit(hint_e, (tx + 4, ty + 10))
    count = gm.f_small.render(
        f"{len(L)} games · {sel + 1 if L else 0}/{len(L)}", True, COL_DIMMER)
    scr.blit(count, (SCREEN_W - PAD_X - count.get_width(), ty + 9))
