"""
GAME MACHINE - Launch confirmation popup drawing.

Three popup types share this surface:
  - "launch"       : 2-option YES/NO prompt (used when no save state exists)
  - "decrypt"      : 2-option YES/NO prompt with PS3-encryption warning
  - "launch_menu" : 3-option vertical menu (LOAD LAST SAVE STATE / JUST PLAY / CANCEL)
                    shown when a save state was found for the game.
"""
import math
import pygame
import pygame.gfxdraw

from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT, COL_DIM,
    COL_DIMMER, COL_CARD_BORDER, COL_BTN_B, COL_BTN_Y, mix, ease_out
)
from ui.helpers import parallelogram


# Action identifiers stored in gm.popup_option_rects so the input handlers
# can look up which button was hit without hard-coding indices.
ACT_LOAD_STATE = "load_state"
ACT_JUST_PLAY = "just_play"
ACT_CANCEL = "cancel"


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

    p_type = getattr(gm, "popup_type", "launch")
    # Popup dimensions vary per type
    if p_type == "launch_menu":
        pw, ph = 520, 380
    elif p_type == "decrypt":
        pw, ph = 460, 240
    else:
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
        if p_type == "decrypt":
            title_text = "DECRYPT GAME?"
        elif p_type == "launch_menu":
            title_text = "LAUNCH GAME?"
        else:
            title_text = "LAUNCH GAME?"
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
            _draw_decrypt_body(gm, scr, popup_r, pw, accent)
        elif p_type == "launch_menu":
            _draw_launch_menu_body(gm, scr, popup_r, pw, ph, accent)
        else:
            _draw_launch_body(gm, scr, popup_r, pw, accent)
    else:
        # During animation, draw a simple scaled panel
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=int(14 * scale))
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, popup_r.w, max(2, int(3 * scale))),
                         border_radius=int(14 * scale))


def _draw_launch_body(gm, scr, popup_r, pw, accent):
    """2-option YES/NO popup body (used when no save state exists)."""
    # Separator line
    sep_y = popup_r.y + 132
    pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 24, sep_y), (popup_r.right - 24, sep_y))

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
    hint = gm.f_mono.render("A = Confirm    B / Esc = Cancel    \u25c4 \u25ba = Switch", True, COL_DIMMER)
    scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 22))


def _draw_decrypt_body(gm, scr, popup_r, pw, accent):
    """2-option YES/NO popup body with a PS3-encryption warning."""
    warn_s = gm.f_small.render("This PS3 game is encrypted. Decrypt it now?", True, COL_BTN_Y)
    scr.blit(warn_s, (popup_r.x + (pw - warn_s.get_width()) // 2, popup_r.y + 124))

    sep_y = popup_r.y + 152
    pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 24, sep_y), (popup_r.right - 24, sep_y))

    btn_w, btn_h = 140, 42
    btn_gap = 24
    total_w = btn_w * 2 + btn_gap
    bx = popup_r.x + (pw - total_w) // 2
    by = popup_r.y + 168

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

    hint = gm.f_mono.render("A = Confirm    B / Esc = Cancel    \u25c4 \u25ba = Switch", True, COL_DIMMER)
    scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 22))


def _draw_launch_menu_body(gm, scr, popup_r, pw, ph, accent):
    """3-option vertical menu: LOAD LAST SAVE STATE / JUST PLAY / CANCEL.

    Shown when find_latest_save_state() returned a path. The path itself is
    stored on gm.popup_save_state and passed to launch_game() when chosen.

    Uses parallelogram buttons (matching the YES/NO popup design language)
    with geometric icons drawn via pygame primitives so we don't depend on
    unicode glyphs being present in the system font.
    """
    state_path = getattr(gm, "popup_save_state", None)

    # Subtitle hinting a save state was found (soft, centered)
    sub_s = gm.f_small.render("A save state was found for this game", True, COL_DIM)
    scr.blit(sub_s, (popup_r.x + (pw - sub_s.get_width()) // 2, popup_r.y + 126))

    # (action, label, button color, icon kind)
    # The LOAD STATE row is taller so it can fit a second line showing the
    # save-state filename without overlapping the main label.
    options = [
        (ACT_LOAD_STATE, "LOAD LAST SAVE STATE", accent,         "resume", True),
        (ACT_JUST_PLAY,  "JUST PLAY",            (231, 233, 238), "play",   False),
        (ACT_CANCEL,     "CANCEL",               (200, 70, 80),   "cancel", False),
    ]

    # Three stacked parallelogram buttons, centered horizontally.
    # The LOAD STATE row is taller (60px) to fit the filename sub-line;
    # the other two are 50px each.
    btn_w = 340
    btn_h_main = 50
    btn_h_load = 60
    btn_gap = 14
    total_h = btn_h_load + btn_h_main * 2 + btn_gap * 2
    bx = popup_r.x + (pw - btn_w) // 2
    by = popup_r.y + 160
    # Vertically centre the stack in the space between subtitle and hint
    available = ph - (by - popup_r.y) - 30
    by += max(0, (available - total_h) // 2)

    gm.popup_option_rects = []
    for idx, (action, label, col, icon_kind, is_load_row) in enumerate(options):
        on = idx == gm.popup_sel
        btn_h = btn_h_load if is_load_row else btn_h_main
        r = pygame.Rect(bx, by, btn_w, btn_h)
        gm.popup_option_rects.append((idx, action, r))

        if on:
            parallelogram(scr, r, col, cut=10)
            # Dark text on the colored button for contrast (white on red for cancel)
            text_col = (255, 240, 240) if action == ACT_CANCEL else (11, 13, 19)
            icon_col = text_col
            sub_col = mix(text_col, col, 0.35)
        else:
            parallelogram(scr, r, COL_PANEL2, cut=10)
            parallelogram(scr, r, COL_CARD_BORDER, cut=10, width=1)
            text_col = COL_DIM
            icon_col = COL_DIMMER
            sub_col = COL_DIMMER

        # Icon on the left, vertically centered in the button
        icon_cx = r.x + 28
        icon_cy = r.centery
        _draw_popup_icon(scr, icon_kind, icon_cx, icon_cy, icon_col)

        # Label - for the tall LOAD STATE row, nudge the label up so the
        # filename can sit on a second line below it without overlapping.
        lbl_s = gm.f_popup_btn.render(label, True, text_col)
        lbl_x = icon_cx + 24
        if is_load_row and state_path:
            lbl_y = r.y + 10
        else:
            lbl_y = r.centery - lbl_s.get_height() // 2
        scr.blit(lbl_s, (lbl_x, lbl_y))

        # Save-state filename on a second line below the label (LOAD STATE row only)
        if is_load_row and state_path:
            short_name = _short_state_name(state_path)
            sub_s = gm.f_chip.render(short_name, True, sub_col)
            scr.blit(sub_s, (lbl_x, lbl_y + lbl_s.get_height() + 2))

        by += btn_h + btn_gap

    hint = gm.f_mono.render("\u25b2\u25bc Navigate   A = Confirm   B / Esc = Cancel", True, COL_DIMMER)
    scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 22))


def _draw_popup_icon(scr, kind, cx, cy, col):
    """Draw a small geometric icon centered at (cx, cy) using primitives.

    Avoids relying on unicode glyphs (\u25b6, \u21bb, ...) that may be missing
    from the system Bahnschrift / Verdana font fallback chain.
    """
    if kind == "play":
        # Solid play triangle pointing right
        pts = [(cx - 6, cy - 7), (cx - 6, cy + 7), (cx + 7, cy)]
        pygame.gfxdraw.filled_polygon(scr, pts, col)
        pygame.gfxdraw.aapolygon(scr, pts, col)
    elif kind == "resume":
        # Play triangle with a vertical bar to its left - the standard
        # "skip to start / resume from saved point" icon
        pygame.draw.rect(scr, col, (cx - 8, cy - 7, 3, 14))
        pts = [(cx - 3, cy - 7), (cx - 3, cy + 7), (cx + 7, cy)]
        pygame.gfxdraw.filled_polygon(scr, pts, col)
        pygame.gfxdraw.aapolygon(scr, pts, col)
    elif kind == "cancel":
        # X mark - two crossed lines, drawn twice for a clean AA look
        d = 7
        pygame.draw.line(scr, col, (cx - d, cy - d), (cx + d, cy + d), 2)
        pygame.draw.line(scr, col, (cx + d, cy - d), (cx - d, cy + d), 2)


def _short_state_name(path):
    """Shorten a save-state file path for display in the popup."""
    name = path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
    if len(name) > 28:
        name = name[:25] + "..."
    return name


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
        pulse_x = bar_r.x + int((bar_r.w - pulse_w) * (0.5 + 0.5 * math.sin(now / 180.0)))
        pulse_r = pygame.Rect(pulse_x, bar_r.y, pulse_w, bar_r.h)
        pygame.draw.rect(scr, accent, pulse_r, border_radius=3)

        # Keep warning in mind
        warn_s = gm.f_mono.render("Please do not close Game Machine or turn off PC.", True, COL_DIMMER)
        scr.blit(warn_s, (popup_r.x + (pw - warn_s.get_width()) // 2, popup_r.bottom - 22))
