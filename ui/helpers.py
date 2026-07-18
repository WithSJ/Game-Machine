"""
GAME MACHINE - UI drawing helper functions.
"""
import pygame
import pygame.gfxdraw

from ui.theme import COL_DIM


def spaced_text(screen, font, text, color, pos, spacing):
    """Letter-spaced text (the design uses wide tracking for headings)."""
    x, y = pos
    for ch in text:
        glyph = font.render(ch, True, color)
        screen.blit(glyph, (x, y))
        x += glyph.get_width() + spacing
    return x


def parallelogram(screen, rect, color, cut=9, width=0):
    pts = [(int(rect.x + cut), int(rect.y)), (int(rect.right), int(rect.y)),
           (int(rect.right - cut), int(rect.bottom)), (int(rect.x), int(rect.bottom))]
    if width == 0:
        pygame.gfxdraw.filled_polygon(screen, pts, color)
        pygame.gfxdraw.aapolygon(screen, pts, color)
    else:
        pygame.gfxdraw.aapolygon(screen, pts, color)


def key_hint(screen, f_mono, f_hint, x, y, letter, color, text):
    pygame.gfxdraw.aacircle(screen, int(x + 9), int(y + 9), 9, color)
    glyph = f_mono.render(letter, True, color)
    screen.blit(glyph, glyph.get_rect(center=(int(x + 9), int(y + 9))))
    label = f_hint.render(text, True, COL_DIM)
    screen.blit(label, (int(x + 24), int(y + 1)))
    return x + 24 + label.get_width() + 24


def wrap_lines(text, font, maxw, max_lines=3):
    """Wrap a title onto at most max_lines lines, ellipsizing the rest."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.size(trial)[0] <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
        cur = ""
    if cur and len(lines) == max_lines:  # text still left over -> ellipsis
        last = lines[-1]
        while last and font.size(last + "…")[0] > maxw:
            last = last[:-1]
        lines[-1] = last + "…"
    return lines[:max_lines]
