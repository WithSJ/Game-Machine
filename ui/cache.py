"""
GAME MACHINE - UI asset caches and background/cover builders.
"""
import os
import pygame

from core.config import COVERS_DIR
from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_BG_GLOW, HERO_RECT, COL_PANEL2, COL_CARD_BORDER, mix
)


def build_bg():
    """Radial glow at the top-right, like the design's backdrop."""
    s = pygame.Surface((SCREEN_W, SCREEN_H))
    s.fill(COL_BG)
    cx, cy = int(SCREEN_W * 0.7), int(-SCREEN_H * 0.1)
    steps = 90
    for i in range(steps, 0, -1):
        t = i / steps
        pygame.draw.circle(s, mix(COL_BG_GLOW, COL_BG, t), (cx, cy), int(900 * t))
    return s


def build_gridlines():
    s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    col = (120, 140, 180, 11)
    for x in range(0, SCREEN_W, 56):
        pygame.draw.line(s, col, (x, 0), (x, SCREEN_H))
    for y in range(0, SCREEN_H, 56):
        pygame.draw.line(s, col, (0, y), (SCREEN_W, y))
    return s


def get_hero_bg(gm, accent):
    if accent not in gm._hero_cache:
        w, h = HERO_RECT.size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        c_a = mix((16, 19, 25), accent, 0.16)
        c_b = (16, 19, 25)
        c_c = (11, 13, 19)
        for x in range(w):
            t = x / w
            col = mix(c_a, c_b, t / 0.55) if t < 0.55 else mix(c_b, c_c, (t - 0.55) / 0.45)
            pygame.draw.line(surf, col, (x, 0), (x, h))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=16)
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        gm._hero_cache[accent] = surf
    return gm._hero_cache[accent]


def get_ghost_text(gm, text, accent):
    key = (text, accent)
    if key not in gm._ghost_cache:
        surf = gm.f_ghost.render(text, True, accent)
        surf.set_alpha(38)
        gm._ghost_cache[key] = surf
    return gm._ghost_cache[key]


def get_cover_for(gm, game):
    """Load covers\\<CONSOLE>\\<Clean Name>.jpg/.png if it exists (cached)."""
    path = game["path"]
    if path not in gm._cover_cache:
        surf = None
        for ext in (".jpg", ".jpeg", ".png"):
            p = os.path.join(COVERS_DIR, game["console"], game["name"] + ext)
            if os.path.isfile(p):
                try:
                    img = pygame.image.load(p).convert()
                    surf = pygame.transform.smoothscale(img, (gm.card_w, gm.cover_h))
                except pygame.error:
                    surf = None
                break
        gm._cover_cache[path] = surf
    return gm._cover_cache[path]


def get_placeholder(gm, accent, active):
    key = (accent, active, gm.card_w, gm.cover_h)
    if key not in gm._placeholder_cache:
        s = pygame.Surface((gm.card_w, gm.cover_h), pygame.SRCALPHA)
        stripe = accent + ((36,) if active else (16,))
        for i in range(-gm.cover_h, gm.card_w + gm.cover_h, 24):
            pygame.draw.line(s, stripe, (i, gm.cover_h), (i + gm.cover_h, 0), 12)
        label = gm.f_mono.render("COVER ART", True,
                                   accent if active else (58, 62, 72))
        if not active:
            label.set_alpha(255)
        s.blit(label, label.get_rect(center=(gm.card_w // 2, gm.cover_h // 2)))
        gm._placeholder_cache[key] = s
    return gm._placeholder_cache[key]
