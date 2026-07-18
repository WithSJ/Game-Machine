"""
GAME MACHINE - Launch confirmation popup drawing.
"""
import pygame
import pygame.gfxdraw

from ui.theme import SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT, COL_DIM, COL_DIMMER, COL_CARD_BORDER, mix, ease_out
from ui.helpers import parallelogram


def draw_popup(gm, now):
    """Draw the launch confirmation popup if active."""
    if not gm.popup_active or not gm.popup_game:
        return

    scr = gm.screen
    g = gm.popup_game
    accent = gm.colors.get(g["console"], gm.accent())

    # Animate popup scale-in
    anim_p = max(0.0, min(1.0, (now - gm.popup_anim_start) / 200))
    scale = ease_out(anim_p)

    # Dark overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(160 * scale)))
    scr.blit(overlay, (0, 0))

    # Popup dimensions
    pw, ph = 460, 220
    px = (SCREEN_W - int(pw * scale)) // 2
    py = (SCREEN_H - int(ph * scale)) // 2
    popup_r = pygame.Rect(px, py, int(pw * scale), int(ph * scale))

    if scale >= 0.95:  # Draw full popup once animation is nearly done
        popup_r = pygame.Rect((SCREEN_W - pw) // 2, (SCREEN_H - ph) // 2, pw, ph)

        # Panel background with rounded corners
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=14)
        # Accent glow line at top
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, pw, 3), border_radius=14)
        # Border
        pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), popup_r, 1, border_radius=14)

        # Title
        title_s = gm.f_popup_title.render("LAUNCH GAME?", True, accent)
        scr.blit(title_s, (popup_r.x + (pw - title_s.get_width()) // 2, popup_r.y + 24))

        # Game name (centered, clipped)
        name_s = gm.f_popup_name.render(g["name"], True, COL_TEXT)
        name_x = popup_r.x + (pw - min(name_s.get_width(), pw - 40)) // 2
        scr.set_clip(pygame.Rect(popup_r.x + 20, popup_r.y + 60, pw - 40, 30))
        scr.blit(name_s, (name_x, popup_r.y + 64))
        scr.set_clip(None)

        # Console chip below name
        chip_s = gm.f_chip.render(g["console"], True, accent)
        chip_r = pygame.Rect(popup_r.x + (pw - chip_s.get_width() - 14) // 2,
                             popup_r.y + 98, chip_s.get_width() + 14, 20)
        pygame.draw.rect(scr, mix(COL_BG, accent, 0.25), chip_r, 1, border_radius=4)
        scr.blit(chip_s, chip_s.get_rect(center=chip_r.center))

        # Separator line
        sep_y = popup_r.y + 132
        pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 24, sep_y), (popup_r.right - 24, sep_y))

        # YES / NO buttons
        btn_w, btn_h = 140, 42
        btn_gap = 24
        total_w = btn_w * 2 + btn_gap
        bx = popup_r.x + (pw - total_w) // 2
        by = popup_r.y + 148

        # YES button
        yes_r = pygame.Rect(bx, by, btn_w, btn_h)
        gm.popup_yes_rect = yes_r
        if gm.popup_sel == 0:
            parallelogram(scr, yes_r, accent, cut=8)
            yes_col = (11, 13, 19)
        else:
            parallelogram(scr, yes_r, COL_PANEL2, cut=8)
            parallelogram(scr, yes_r, COL_CARD_BORDER, cut=8, width=1)
            yes_col = COL_DIM
        yes_s = gm.f_popup_btn.render("YES", True, yes_col)
        # Play triangle icon
        tri_cx = yes_r.x + 28
        tri_cy = yes_r.centery
        tri_pts = [(tri_cx, tri_cy - 5), (tri_cx, tri_cy + 5), (tri_cx + 8, tri_cy)]
        pygame.gfxdraw.filled_polygon(scr, tri_pts, yes_col)
        pygame.gfxdraw.aapolygon(scr, tri_pts, yes_col)
        scr.blit(yes_s, (tri_cx + 16, yes_r.centery - yes_s.get_height() // 2))

        # NO button
        no_r = pygame.Rect(bx + btn_w + btn_gap, by, btn_w, btn_h)
        gm.popup_no_rect = no_r
        if gm.popup_sel == 1:
            parallelogram(scr, no_r, (200, 70, 80), cut=8)
            no_col = (255, 240, 240)
        else:
            parallelogram(scr, no_r, COL_PANEL2, cut=8)
            parallelogram(scr, no_r, COL_CARD_BORDER, cut=8, width=1)
            no_col = COL_DIM
        no_s = gm.f_popup_btn.render("NO", True, no_col)
        scr.blit(no_s, no_s.get_rect(center=no_r.center))

        # Hint text at bottom
        hint = gm.f_mono.render("A = Confirm    B / Esc = Cancel    ◄ ► = Switch", True, COL_DIMMER)
        scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 22))
    else:
        # During animation, draw a simple scaled panel
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=int(14 * scale))
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, popup_r.w, max(2, int(3 * scale))),
                         border_radius=int(14 * scale))
