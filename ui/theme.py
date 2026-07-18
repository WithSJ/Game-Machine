"""
GAME MACHINE - Theme colors, layout constants, and utility functions.
"""
import pygame

# ============================================================
# THEME (colors from the dashboard design)
# ============================================================
SCREEN_W, SCREEN_H = 1280, 720
COL_BG = (7, 8, 12)
COL_BG_GLOW = (16, 19, 28)
COL_TEXT = (238, 240, 244)
COL_DIM = (138, 141, 148)
COL_DIMMER = (86, 91, 102)
COL_PANEL = (17, 20, 27)
COL_PANEL2 = (26, 30, 39)
COL_CARD_BORDER = (28, 32, 42)
COL_FOOT_LINE = (23, 26, 34)
COL_PAD_OK = (93, 202, 165)
COL_TOAST_BG = (23, 27, 36)
COL_TOAST_EDGE = (240, 112, 60)
COL_BTN_B = (240, 149, 149)
COL_BTN_Y = (250, 199, 117)

REC_COLOR = (95, 212, 232)  # RECENTS tab accent
CONSOLE_COLORS = {
    "PSP": (240, 112, 60),   # orange
    "PS2": (79, 214, 166),   # green
    "PS3": (157, 147, 245),  # purple
}
# Auto-detected consoles get colors from this pool
EXTRA_COLORS = [
    (255, 105, 180),  # pink
    (250, 199, 117),  # gold
    (90, 230, 230),   # cyan
    (255, 120, 90),   # coral
    (170, 220, 120),  # lime
]

# Layout
PAD_X = 44
HERO_RECT = pygame.Rect(PAD_X, 122, SCREEN_W - 2 * PAD_X, 172)
GRID_RECT = pygame.Rect(PAD_X, 310, SCREEN_W - 2 * PAD_X, 352)
FOOTER_Y = 668
CARD_W, COVER_H, CARD_H, GAP = 132, 176, 246, 14
COLS = (GRID_RECT.w + GAP) // (CARD_W + GAP)

# Input tuning
AXIS_DEADZONE = 0.5
NAV_REPEAT_DELAY = 350
NAV_REPEAT_RATE = 130
TAP_SLOP = 12          # finger moved less than this = tap, more = drag
WHEEL_STEP = 80        # pixels per mouse wheel notch
TOAST_MS = 2200
TAB_ANIM_MS = 420


def mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def build_console_colors(consoles):
    """Give every console a color - auto-detected ones draw from EXTRA_COLORS."""
    colors = dict(CONSOLE_COLORS)
    i = 0
    for name in consoles:
        if name not in colors:
            colors[name] = EXTRA_COLORS[i % len(EXTRA_COLORS)]
            i += 1
    return colors


def ease_out(p):
    return 1 - (1 - p) ** 3
