"""
GAME MACHINE - Touch input handling.
"""
import pygame

from ui.theme import TAP_SLOP


def handle_touch_down(gm, event):
    """Handle finger-down event."""
    if gm.touch_id is None:  # track the first finger only
        w, h = gm.screen.get_size()
        gm.touch_id = event.finger_id
        gm.touch_start = (event.x * w, event.y * h)
        gm.touch_last_y = event.y * h
        gm.touch_moved = False


def handle_touch_motion(gm, event):
    """Handle finger-motion event."""
    if event.finger_id == gm.touch_id and gm.touch_start is not None:
        w, h = gm.screen.get_size()
        y = event.y * h
        if abs(y - gm.touch_start[1]) > TAP_SLOP:
            gm.touch_moved = True
        if gm.touch_moved:
            # finger up = list scrolls down (natural scrolling)
            gm.scroll_t += gm.touch_last_y - y
        gm.touch_last_y = y


def handle_touch_up(gm, event):
    """Handle finger-up event."""
    if event.finger_id == gm.touch_id:
        if gm.touch_start is not None and not gm.touch_moved:
            w, h = gm.screen.get_size()
            gm.click((event.x * w, event.y * h))
        gm.touch_id = None
        gm.touch_start = None
