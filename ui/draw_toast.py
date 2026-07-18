"""
GAME MACHINE - Toast notification drawing.
"""
import pygame

from ui.theme import SCREEN_W, SCREEN_H, COL_TOAST_BG, COL_TOAST_EDGE, TOAST_MS, ease_out


def draw_toast(gm, now):
    """Draw toast notification if active."""
    if not gm.toast or now >= gm.toast_until:
        return
    scr = gm.screen
    tp = max(0.0, min(1.0, (now - (gm.toast_until - TOAST_MS)) / 250))
    surf = gm.f_small.render(gm.toast, True, (231, 233, 238))
    tw, th = surf.get_width() + 44, 38
    tr = pygame.Rect(int((SCREEN_W - tw) // 2),
                     int(SCREEN_H - 88 + int(12 * (1 - ease_out(tp)))), int(tw), int(th))
    pygame.draw.rect(scr, COL_TOAST_BG, tr, border_radius=6)
    pygame.draw.rect(scr, (44, 47, 56), tr, 1, border_radius=6)
    pygame.draw.rect(scr, COL_TOAST_EDGE, (tr.x, tr.y, 2, th))
    scr.blit(surf, (tr.x + 24, tr.y + 10))
