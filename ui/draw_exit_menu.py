"""
GAME MACHINE - Exit/Power menu drawing.
"""
import pygame

from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT, COL_DIM,
    COL_DIMMER, COL_CARD_BORDER, COL_BTN_B, mix, ease_out
)


def draw_exit_menu(gm, now):
    """Draw the exit/power menu if active."""
    if not gm.exit_menu_active:
        return

    scr = gm.screen
    accent = gm.accent()
    anim_p = max(0.0, min(1.0, (now - gm.exit_menu_anim_start) / 220))
    scale = ease_out(anim_p)

    # Dark overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, int(180 * scale)))
    scr.blit(overlay, (0, 0))

    pw, ph = 420, 370
    px = (SCREEN_W - int(pw * scale)) // 2
    py = (SCREEN_H - int(ph * scale)) // 2
    popup_r = pygame.Rect(px, py, int(pw * scale), int(ph * scale))

    if scale >= 0.95:
        popup_r = pygame.Rect((SCREEN_W - pw) // 2, (SCREEN_H - ph) // 2, pw, ph)

        # Panel
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=14)
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, pw, 3), border_radius=14)
        pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), popup_r, 1, border_radius=14)

        # Close [X] button (top-right) - lets mouse/touch users dismiss the menu
        close_size = 26
        close_r = pygame.Rect(popup_r.right - close_size - 14, popup_r.y + 14, close_size, close_size)
        gm.exit_menu_close_rect = close_r
        m_pos = pygame.mouse.get_pos()
        close_hover = close_r.collidepoint(m_pos)
        close_bg = mix(COL_BG, COL_BTN_B, 0.15) if close_hover else COL_PANEL2
        pygame.draw.rect(scr, close_bg, close_r, border_radius=6)
        pygame.draw.rect(scr, COL_BTN_B if close_hover else COL_CARD_BORDER, close_r, 1, border_radius=6)
        x_s = gm.f_popup_btn.render("X", True, COL_BTN_B if close_hover else COL_DIM)
        scr.blit(x_s, x_s.get_rect(center=close_r.center))

        # Title (centered, leaves room for the close button on the right)
        title_s = gm.f_popup_title.render("POWER MENU", True, accent)
        scr.blit(title_s, (popup_r.x + (pw - title_s.get_width()) // 2, popup_r.y + 20))

        # Menu options
        options = [
            ("EXIT GAME MACHINE", (240, 112, 60),  "[X]"),
            ("LOCK SCREEN",       (95, 212, 232),  "[LOCK]"),
            ("RESTART",           (79, 214, 166),  "[RST]"),
            ("SHUTDOWN",          (200, 70, 80),   "[OFF]"),
        ]
        gm.exit_menu_option_rects = []
        opt_w, opt_h = pw - 60, 44
        oy = popup_r.y + 58

        for idx, (label, col, icon_ch) in enumerate(options):
            on = idx == gm.exit_menu_sel
            r = pygame.Rect(popup_r.x + 30, oy, opt_w, opt_h)
            gm.exit_menu_option_rects.append((idx, r))

            if on:
                # Filled accent background
                pygame.draw.rect(scr, mix(COL_BG, col, 0.25), r, border_radius=8)
                pygame.draw.rect(scr, col, r, 2, border_radius=8)
                # Left accent bar
                pygame.draw.rect(scr, col, (r.x, r.y + 6, 3, r.h - 12))
            else:
                pygame.draw.rect(scr, COL_PANEL2, r, border_radius=8)
                pygame.draw.rect(scr, COL_CARD_BORDER, r, 1, border_radius=8)

            text_col = col if on else COL_DIM
            # Icon - render first and measure its width so the label can be
            # placed after it with consistent padding. (Previously the label
            # was hardcoded to r.x+42, which overlapped wider ASCII tags
            # like "[LOCK]".)
            icon_s = gm.f_popup_btn.render(icon_ch, True, text_col)
            icon_x = r.x + 16
            scr.blit(icon_s, (icon_x, r.centery - icon_s.get_height() // 2))
            # Label - offset by actual icon width + 14px padding
            lbl_s = gm.f_popup_btn.render(label, True, (231, 233, 238) if on else COL_DIM)
            lbl_x = icon_x + icon_s.get_width() + 14
            scr.blit(lbl_s, (lbl_x, r.centery - lbl_s.get_height() // 2))

            oy += opt_h + 8

        # Separator
        sep_y = oy + 2
        pygame.draw.line(scr, COL_CARD_BORDER, (popup_r.x + 30, sep_y), (popup_r.right - 30, sep_y))

        # Auto-start toggle
        tog_y = sep_y + 12
        tog_label = gm.f_popup_btn.render("AUTO-START", True, COL_TEXT)
        scr.blit(tog_label, (popup_r.x + 42, tog_y + 2))

        # Toggle switch
        sw_w, sw_h = 48, 24
        sw_x = popup_r.right - 42 - sw_w
        sw_y = tog_y
        sw_r = pygame.Rect(sw_x, sw_y, sw_w, sw_h)
        gm.exit_menu_autostart_rect = sw_r

        if gm.auto_start:
            pygame.draw.rect(scr, (79, 214, 166), sw_r, border_radius=12)
            # Knob on right
            pygame.draw.circle(scr, (231, 233, 238), (sw_x + sw_w - 12, sw_y + 12), 9)
        else:
            pygame.draw.rect(scr, COL_DIMMER, sw_r, border_radius=12)
            # Knob on left
            pygame.draw.circle(scr, (140, 143, 150), (sw_x + 12, sw_y + 12), 9)

        on_off = gm.f_chip.render("ON" if gm.auto_start else "OFF", True,
                                    (79, 214, 166) if gm.auto_start else COL_DIMMER)
        scr.blit(on_off, (sw_x - on_off.get_width() - 8, tog_y + 5))

        # Hint text
        hint = gm.f_mono.render("▲▼ Navigate  A=Confirm  B/Esc=Cancel  Y=Auto-Start  [X]=Close", True, COL_DIMMER)
        scr.blit(hint, (popup_r.x + (pw - hint.get_width()) // 2, popup_r.bottom - 22))
    else:
        pygame.draw.rect(scr, COL_PANEL, popup_r, border_radius=int(14 * scale))
        pygame.draw.rect(scr, accent, (popup_r.x, popup_r.y, popup_r.w, max(2, int(3 * scale))),
                         border_radius=int(14 * scale))
