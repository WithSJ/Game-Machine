"""
GAME MACHINE - Cover art grid drawing.
"""
import pygame

from core.playdata import fmt_last
from ui.theme import GRID_RECT, COL_BG, COL_PANEL, COL_CARD_BORDER, COL_DIMMER, COL_PAD_OK, mix
from ui.helpers import wrap_lines


def draw_grid(gm, now, anim_off):
    """Draw the scrollable game cover grid."""
    scr = gm.screen
    L = gm.current_list()
    sel = min(gm.sel, len(L) - 1) if L else 0

    scr.set_clip(GRID_RECT)
    for i, g in enumerate(L):
        row, col = divmod(i, gm.cols)
        gx = GRID_RECT.x + col * (gm.card_w + gm.gap)
        gy = GRID_RECT.y + row * (gm.card_h + gm.gap) - int(gm.scroll) + anim_off
        if gy + gm.card_h < GRID_RECT.y or gy > GRID_RECT.bottom:
            continue
        on = i == sel
        c = gm.colors.get(g["console"], (150, 150, 150))
        lift = -6 if on else 0
        card = pygame.Rect(gx, gy + lift, gm.card_w, gm.card_h)
        rec = gm.game_stats(g)

        pygame.draw.rect(scr, COL_PANEL, card, border_radius=10)
        cover = gm._cover_for(g)
        cov_area = pygame.Rect(card.x, card.y, gm.card_w, gm.cover_h)
        prev_clip = scr.get_clip()
        scr.set_clip(prev_clip.clip(cov_area) if prev_clip else cov_area)
        scr.blit(cover if cover else gm._placeholder(c, on), cov_area.topleft)
        scr.set_clip(prev_clip)

        # Draw a beautiful "NEW" badge on the top right of the card if not played
        if not rec:
            badge_s = gm.f_chip.render("NEW", True, COL_BG)
            badge_w = badge_s.get_width() + 12
            badge_h = 18
            badge_r = pygame.Rect(card.right - badge_w - 8, card.y + 8, badge_w, badge_h)
            pygame.draw.rect(scr, COL_PAD_OK, badge_r, border_radius=4)
            scr.blit(badge_s, badge_s.get_rect(center=badge_r.center))

        # Clip all card text content within the card boundary
        card_text_area = pygame.Rect(card.x, card.y + gm.cover_h, gm.card_w, gm.card_h - gm.cover_h)
        card_clip = GRID_RECT.clip(card_text_area)
        scr.set_clip(card_clip)

        # Game name - full name with multi-line wrapping (up to 3 lines)
        ty2 = card.y + gm.cover_h + 8
        name_lines = wrap_lines(g["name"], gm.f_card, gm.card_w - 20, max_lines=3)
        for line in name_lines:
            scr.blit(gm.f_card.render(line, True, (231, 233, 238) if on else (185, 188, 195)),
                     (card.x + 10, ty2))
            ty2 += 18

        # Console chip + status at the bottom of the card
        chip = gm.f_chip.render(g["console"], True, c)
        chip_r = pygame.Rect(card.x + 10, card.bottom - 26, chip.get_width() + 14, 18)
        pygame.draw.rect(scr, mix(COL_BG, c, 0.35), chip_r, 1, border_radius=3)
        scr.blit(chip, chip.get_rect(center=chip_r.center))
        sub_txt = fmt_last(rec["last"]) if rec else "NEW"
        sub_s = gm.f_mono.render(sub_txt, True, COL_DIMMER)
        scr.blit(sub_s, (card.right - 10 - sub_s.get_width(), card.bottom - 23))

        # Restore grid clip for card border drawing
        scr.set_clip(GRID_RECT)

        border_c = mix(COL_BG, c, 0.8) if on else COL_CARD_BORDER
        pygame.draw.rect(scr, border_c, card, 1, border_radius=10)
        if on:
            pygame.draw.rect(scr, c, (card.x, card.y, gm.card_w, 2))
        # clip the hit-test rect to the grid so half-hidden cards
        # can't be clicked through the hero banner or footer
        gm.card_rects.append((i, card.clip(GRID_RECT)))
    scr.set_clip(None)
