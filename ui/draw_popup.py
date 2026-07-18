"""
GAME MACHINE - Launch confirmation popup drawing.
"""
import math
import pygame
import pygame.gfxdraw

from ui.theme import SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT, COL_DIM, COL_DIMMER, COL_CARD_BORDER, COL_BTN_Y, COL_BTN_B, mix, ease_out
from ui.helpers import parallelogram


def draw_popup(gm, now):
    """Draw the launch confirmation popup or decryption progress popup if active."""
    scr = gm.screen
    
    # Handle active decryption rendering first
    if getattr(gm, "decrypting_active", False) and gm.popup_game:
        draw_decryption_popup(gm, now)
        return

    if not gm.popup_active or not gm.popup_game:
        return

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
    p_type = getattr(gm, "popup_type", "launch")
    pw, ph = 460, (240 if p_type == "decrypt" else 220)
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
        title_text = "DECRYPT GAME?" if p_type == "decrypt" else "LAUNCH GAME?"
        title_s = gm.f_popup_title.render(title_text, True, accent)
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

        if p_type == "decrypt":
            warn_s = gm.f_small.render("This PS3 game is encrypted. Decrypt it now?", True, COL_BTN_Y)
            scr.blit(warn_s, (popup_r.x + (pw - warn_s.get_width()) // 2, popup_r.y + 124))

        # Separator line
        sep_y = popup_r.y + (152 if p_type == "decrypt" else 132)
        pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 24, sep_y), (popup_r.right - 24, sep_y))

        # YES / NO buttons
        btn_w, btn_h = 140, 42
        btn_gap = 24
        total_w = btn_w * 2 + btn_gap
        bx = popup_r.x + (pw - total_w) // 2
        by = popup_r.y + (168 if p_type == "decrypt" else 148)

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


def draw_decryption_popup(gm, now):
    """Draw the decryption progress/error popup."""
    scr = gm.screen
    g = gm.popup_game
    accent = gm.colors.get(g["console"], gm.accent())

    # Dark overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    scr.blit(overlay, (0, 0))

    # Dimensions
    pw, ph = 500, 240
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    popup_r = pygame.Rect(px, py, pw, ph)

    # Panel background
    pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=14)
    # Accent glow line at top
    pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, pw, 3), border_radius=14)
    # Border
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), popup_r, 1, border_radius=14)

    if gm.decryption_error:
        # Title: DECRYPTION FAILED
        title_s = gm.f_popup_title.render("DECRYPTION FAILED", True, COL_BTN_B)
        scr.blit(title_s, (popup_r.x + (pw - title_s.get_width()) // 2, popup_r.y + 24))

        # Game name
        name_s = gm.f_popup_name.render(g["name"], True, COL_TEXT)
        scr.blit(name_s, (popup_r.x + (pw - name_s.get_width()) // 2, popup_r.y + 64))

        # Error text wrapped
        from ui.helpers import wrap_lines
        err_lines = wrap_lines(gm.decryption_error, gm.f_small, pw - 60, max_lines=3)
        ty = popup_r.y + 104
        for line in err_lines:
            err_s = gm.f_small.render(line, True, COL_BTN_B)
            scr.blit(err_s, (popup_r.x + (pw - err_s.get_width()) // 2, ty))
            ty += 16

        # CLOSE button
        btn_w, btn_h = 140, 36
        btn_r = pygame.Rect(popup_r.x + (pw - btn_w) // 2, popup_r.bottom - 54, btn_w, btn_h)
        gm.decryption_close_rect = btn_r
        parallelogram(scr, btn_r, COL_BTN_B, cut=6)
        btn_s = gm.f_popup_btn.render("CLOSE", True, COL_BG)
        scr.blit(btn_s, btn_s.get_rect(center=btn_r.center))

    else:
        # Title: DECRYPTING...
        title_s = gm.f_popup_title.render("DECRYPTING GAME...", True, accent)
        scr.blit(title_s, (popup_r.x + (pw - title_s.get_width()) // 2, popup_r.y + 24))

        # Game name
        name_s = gm.f_popup_name.render(g["name"], True, COL_TEXT)
        scr.blit(name_s, (popup_r.x + (pw - name_s.get_width()) // 2, popup_r.y + 64))

        # Status text
        status_s = gm.f_small.render(gm.decryption_status, True, COL_DIM)
        scr.blit(status_s, (popup_r.x + (pw - status_s.get_width()) // 2, popup_r.y + 110))

        # Premium loading bar
        bar_r = pygame.Rect(popup_r.x + 50, popup_r.y + 148, pw - 100, 6)
        pygame.draw.rect(scr, COL_CARD_BORDER, bar_r, border_radius=3)

        # Pulsing active bar
        pulse_w = 100
        # Simple back-and-forth sin-based motion
        pulse_x = bar_r.x + int((bar_r.w - pulse_w) * (0.5 + 0.5 * math.sin(now / 180.0)))
        pulse_r = pygame.Rect(pulse_x, bar_r.y, pulse_w, bar_r.h)
        pygame.draw.rect(scr, accent, pulse_r, border_radius=3)

        # Keep warning in mind
        warn_s = gm.f_mono.render("Please do not close Game Machine or turn off PC.", True, COL_DIMMER)
        scr.blit(warn_s, (popup_r.x + (pw - warn_s.get_width()) // 2, popup_r.bottom - 22))
