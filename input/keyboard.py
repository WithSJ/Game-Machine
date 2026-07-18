"""
GAME MACHINE - Keyboard input handling.
"""
import pygame

from core.playdata import save_playdata


def handle_keyboard(gm, event):
    """Handle keyboard key-down events."""
    k = event.key
    if k == pygame.K_ESCAPE:
        gm._show_exit_menu()
    elif k == pygame.K_LEFT:
        gm.move_sel(-1, 0)
    elif k == pygame.K_RIGHT:
        gm.move_sel(1, 0)
    elif k == pygame.K_UP:
        gm.move_sel(0, -1)
    elif k == pygame.K_DOWN:
        gm.move_sel(0, 1)
    elif k == pygame.K_PAGEUP:
        gm.move_sel(0, -2)
    elif k == pygame.K_PAGEDOWN:
        gm.move_sel(0, 2)
    elif k == pygame.K_HOME:
        gm.sel = 0
        gm.ensure = True
    elif k == pygame.K_END:
        L = gm.current_list()
        if L:
            gm.sel = len(L) - 1
            gm.ensure = True
    elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
        if gm.header_focus == 0:
            gm._activate_header_size()
        elif gm.header_focus == 1:
            gm._show_exit_menu()
        else:
            gm.launch_selected()
    elif k in (pygame.K_q, pygame.K_LEFTBRACKET):
        gm.set_tab(gm.tab - 1)
    elif k in (pygame.K_e, pygame.K_RIGHTBRACKET):
        gm.set_tab(gm.tab + 1)
    elif k in (pygame.K_r, pygame.K_y):
        gm.random_pick()
    elif k == pygame.K_F11:
        gm.toggle_fullscreen()
    elif k == pygame.K_s:
        current = gm.settings.get("size", "medium")
        new_size = "medium" if current == "small" else ("large" if current == "medium" else "small")
        gm.settings["size"] = new_size
        save_playdata(gm.playdata)
        gm.update_sizes()
        gm.pop(f"Grid size: {new_size.upper()}")
