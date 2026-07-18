"""
GAME MACHINE - Mouse input handling.
"""
import pygame

from ui.theme import WHEEL_STEP


def handle_mouse_motion(gm, event):
    """Handle mouse motion - hover to select card."""
    if not getattr(event, "touch", False):
        for i, r in gm.card_rects:
            if r.collidepoint(event.pos):
                gm.sel = i  # hover = select (leave scroll alone)
                break


def handle_mouse_click(gm, event):
    """Handle mouse button click."""
    if not getattr(event, "touch", False):
        gm.click(event.pos)


def handle_mouse_wheel(gm, event):
    """Handle mouse wheel scrolling."""
    gm.scroll_t -= event.y * WHEEL_STEP
