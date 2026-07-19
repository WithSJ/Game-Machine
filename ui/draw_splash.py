"""
GAME MACHINE - Splash/loading screen drawing.
"""
import pygame
import pygame.gfxdraw

from ui.theme import COL_BG, COL_BG_GLOW, COL_DIM, COL_DIMMER, COL_PANEL2, COL_TEXT, COL_BRAND, SCREEN_W, SCREEN_H, mix


def draw_splash(screen, status_text="Loading..."):
    """Draw a splash/loading screen. Uses basic font since custom fonts may not be loaded yet."""
    screen.fill(COL_BG)

    # Subtle radial glow in center
    cx, cy = SCREEN_W // 2, SCREEN_H // 2 - 40
    for i in range(60, 0, -1):
        t = i / 60
        col = mix(COL_BG_GLOW, COL_BG, t)
        pygame.draw.circle(screen, col, (cx, cy), int(320 * t))

    # GAME MACHINE title - use a basic font (always available)
    try:
        title_font = pygame.font.SysFont("bahnschrift,verdana,arial", 48, bold=True)
        sub_font = pygame.font.SysFont("verdana,arial", 14)
        status_font = pygame.font.SysFont("consolas,couriernew,monospace", 13)
    except Exception:
        title_font = pygame.font.Font(None, 48)
        sub_font = pygame.font.Font(None, 18)
        status_font = pygame.font.Font(None, 16)

    # Logo diamond
    diamond_pts = [(cx, cy - 65), (cx + 10, cy - 55), (cx, cy - 45), (cx - 10, cy - 55)]
    pygame.gfxdraw.filled_polygon(screen, diamond_pts, COL_BRAND)
    pygame.gfxdraw.aapolygon(screen, diamond_pts, COL_BRAND)

    # Title text
    title_s = title_font.render("GAME MACHINE", True, COL_TEXT)
    screen.blit(title_s, (cx - title_s.get_width() // 2, cy - 30))

    # Subtitle
    sub_s = sub_font.render("EMULATOR FRONTEND", True, COL_DIMMER)
    screen.blit(sub_s, (cx - sub_s.get_width() // 2, cy + 28))

    # Loading bar background
    bar_w, bar_h = 300, 4
    bar_x = cx - bar_w // 2
    bar_y = cy + 70
    pygame.draw.rect(screen, COL_PANEL2, (bar_x, bar_y, bar_w, bar_h), border_radius=2)

    # Animated loading bar (pulsing sweep)
    t = (pygame.time.get_ticks() % 1200) / 1200
    glow_x = bar_x + int(t * bar_w)
    glow_w = min(80, bar_w - int(t * bar_w))
    pygame.draw.rect(screen, COL_BRAND, (glow_x, bar_y, glow_w, bar_h), border_radius=2)

    # Status text
    stat_s = status_font.render(status_text, True, COL_DIM)
    screen.blit(stat_s, (cx - stat_s.get_width() // 2, bar_y + 18))
