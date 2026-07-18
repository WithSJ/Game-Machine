"""
GAME MACHINE - Hero banner drawing.
"""
import math

import pygame
import pygame.gfxdraw

from core.playdata import fmt_dur, fmt_last
from ui.theme import HERO_RECT, COL_BG, mix
from ui.helpers import spaced_text, parallelogram


def draw_hero(gm, now, anim_off):
    """Draw the hero banner with selected game info."""
    scr = gm.screen
    L = gm.current_list()
    sel = min(gm.sel, len(L) - 1) if L else 0
    cur = L[sel] if L else None
    accent = gm.colors.get(cur["console"], gm.accent()) if cur else gm.accent()
    tab_name = gm.tabs[gm.tab][0]

    hero = HERO_RECT.move(0, anim_off)
    scr.blit(gm._hero_bg(accent), hero.topleft)
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.30), hero, 1, border_radius=16)

    scr.set_clip(hero)
    if cur:
        ghost = gm._ghost_text(cur["console"], accent)
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
        rec = gm.game_stats(cur)
        channel = (f"{cur['console']} · RECENTLY PLAYED" if tab_name == "RECENTS"
                   else f"{cur['console']} CHANNEL")
        spaced_text(scr, gm.f_channel, channel, accent, (hero.x + 32, hero.y + 18), 3)
        scr.set_clip(hero)
        title = gm.f_hero.render(cur["name"], True, (253, 253, 253))
        scr.blit(title, (hero.x + 30, hero.y + 40))
        scr.set_clip(None)
        if rec:
            meta_txt = f"Last played {fmt_last(rec['last'])} · {fmt_dur(rec['seconds'])} played"
        else:
            meta_txt = "Not played yet · Press A to start"
        meta = gm.f_meta.render(meta_txt, True, (155, 160, 170))
        scr.blit(meta, (hero.x + 31, hero.y + 88))

        by = hero.bottom - 52
        play_label = gm.f_btn.render("RESUME" if rec else "PLAY", True, (11, 13, 19))
        gm.play_rect = pygame.Rect(hero.x + 30, by, play_label.get_width() + 70, 38)
        parallelogram(scr, gm.play_rect, accent, cut=8)
        cy = gm.play_rect.centery
        tri_x = gm.play_rect.x + 24
        tri_pts = [(tri_x, cy - 6), (tri_x, cy + 6), (tri_x + 10, cy)]
        pygame.gfxdraw.filled_polygon(scr, tri_pts, (11, 13, 19))
        pygame.gfxdraw.aapolygon(scr, tri_pts, (11, 13, 19))
        scr.blit(play_label, (tri_x + 18, cy - play_label.get_height() // 2))

        det_label = gm.f_btn.render("DETAILS", True, (185, 188, 194))
        gm.details_rect = pygame.Rect(gm.play_rect.right + 12, by,
                                        det_label.get_width() + 44, 38)
        parallelogram(scr, gm.details_rect, (58, 62, 72), cut=8, width=1)
        scr.blit(det_label, det_label.get_rect(center=gm.details_rect.center))
    else:
        spaced_text(scr, gm.f_channel, "GAME MACHINE", accent, (hero.x + 32, hero.y + 22), 3)
        if tab_name == "RECENTS":
            t1, t2 = "Nothing played yet", "Pick a console tab and start a game - it will show up here."
        else:
            t1, t2 = "No games found", "Check the CONFIG paths at the top of console.py."
        scr.blit(gm.f_hero.render(t1, True, (253, 253, 253)), (hero.x + 30, hero.y + 48))
        scr.blit(gm.f_meta.render(t2, True, (155, 160, 170)), (hero.x + 31, hero.y + 100))
