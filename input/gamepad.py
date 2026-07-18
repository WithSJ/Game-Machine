"""
GAME MACHINE - Gamepad input handling.
"""
import pygame

from ui.theme import AXIS_DEADZONE, NAV_REPEAT_DELAY, NAV_REPEAT_RATE


def handle_gamepad_buttons(gm, event):
    """Handle gamepad button-down events."""
    if event.button == 0:      # A = play / activate header
        if gm.header_focus == 0:
            gm._activate_header_size()
        elif gm.header_focus == 1:
            gm._show_exit_menu()
        else:
            gm.launch_selected()
    elif event.button == 1:    # B = back to Recents
        gm.set_tab(0)
    elif event.button == 3:    # Y = random game
        gm.random_pick()
    elif event.button == 4:    # L1 = previous tab
        gm.set_tab(gm.tab - 1)
    elif event.button == 5:    # R1 = next tab
        gm.set_tab(gm.tab + 1)


def handle_gamepad_connect(gm, event):
    """Handle controller plug-in after launch."""
    gm.joystick = pygame.joystick.Joystick(event.device_index)
    gm.joystick.init()


def handle_gamepad_disconnect(gm, event):
    """Handle controller removal."""
    if gm.joystick is not None and gm.joystick.get_instance_id() == event.instance_id:
        gm.joystick = None
        gm.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}


def _pad_axis_repeat(gm, key, cur, now, mover):
    """Hold-to-repeat for one gamepad axis (d-pad or analog stick)."""
    st = gm.pad_state[key]
    if cur != st["dir"]:
        st["dir"] = cur
        if cur:
            mover(cur)
            st["next"] = now + NAV_REPEAT_DELAY
    elif cur and now >= st["next"]:
        mover(cur)
        st["next"] = now + NAV_REPEAT_RATE


def update_gamepad_axes(gm, now):
    """Handle gamepad axis navigation with hold-to-repeat."""
    # Block grid navigation when exit menu is active; handle D-pad up/down for menu
    if gm.exit_menu_active:
        j = gm.joystick
        if j is not None:
            dy = 0
            if j.get_numhats() > 0:
                _, hy = j.get_hat(0)
                dy = -hy
            if dy == 0 and j.get_numaxes() > 1:
                ay = j.get_axis(1)
                dy = 1 if ay > AXIS_DEADZONE else (-1 if ay < -AXIS_DEADZONE else 0)
            def exit_menu_ud(d):
                gm.exit_menu_sel = (gm.exit_menu_sel + d) % 4
            _pad_axis_repeat(gm, "y", dy, now, exit_menu_ud)
        return
    # Block grid navigation when popup is active; handle popup D-pad instead
    if gm.popup_active:
        j = gm.joystick
        if j is not None:
            dx = 0
            if j.get_numhats() > 0:
                hx, _ = j.get_hat(0)
                dx = hx
            if dx == 0 and j.get_numaxes() > 0:
                ax = j.get_axis(0)
                dx = 1 if ax > AXIS_DEADZONE else (-1 if ax < -AXIS_DEADZONE else 0)
            # Use repeat logic for left/right toggle
            def popup_lr(d):
                gm.popup_sel = 1 - gm.popup_sel
            _pad_axis_repeat(gm, "x", dx, now, popup_lr)
        return
    j = gm.joystick
    dx = dy = 0
    if j is not None:
        if j.get_numhats() > 0:
            hx, hy = j.get_hat(0)
            dx, dy = hx, -hy
        if dx == 0 and j.get_numaxes() > 0:
            ax = j.get_axis(0)
            dx = 1 if ax > AXIS_DEADZONE else (-1 if ax < -AXIS_DEADZONE else 0)
        if dy == 0 and j.get_numaxes() > 1:
            ay = j.get_axis(1)
            dy = 1 if ay > AXIS_DEADZONE else (-1 if ay < -AXIS_DEADZONE else 0)
    _pad_axis_repeat(gm, "x", dx, now, lambda d: gm.move_sel(d, 0))
    _pad_axis_repeat(gm, "y", dy, now, lambda d: gm.move_sel(0, d))
