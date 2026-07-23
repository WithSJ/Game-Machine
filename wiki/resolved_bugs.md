# Game Machine Resolved Bugs

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

## Bug: pygame KeyError: 2 (JOYDEVICEADDED invalid device_index)

### Symptoms
On Windows, when a gamepad is connected/disconnected or when an emulator (PPSSPP/PCSX2/RPCS3) releases exclusive HID ownership on exit, Pygame can emit a `JOYDEVICEADDED` event with an invalid `device_index` (e.g., `2` when only indices 0,1 exist). This triggers `KeyError: 2` inside `pygame.joystick.Joystick()`, crashing the frontend with:
```
KeyError: 2
SystemError: <built-in function get> returned a result with an exception set
```

### Root Cause
Two code paths create `pygame.joystick.Joystick(event.device_index)`:
1. `input/gamepad.py::handle_gamepad_connect()` — called from `JOYDEVICEADDED` event handler.
2. `app.py::_reinit_joystick()` — called after emulator exits to re-acquire the gamepad.

Both assumed `event.device_index` was valid. When an emulator releases exclusive HID ownership, Windows can re-enumerate the device with a new index that Pygame hasn't registered yet, or emit a stale index. Additionally, `pygame.joystick.quit()` + `init()` inside `_reinit_joystick()` can leave the joystick subsystem in a transient state where indices shift.

### Solution
Wrapped both `Joystick(event.device_index)` calls in `try/except KeyError`:
- **`input/gamepad.py:30-35`**: On `KeyError`, call `pygame.joystick.quit()`, `pygame.joystick.init()`, then re-query `pygame.joystick.get_count()` and initialize the first available joystick, or set `gm.joystick = None`.
- **`app.py:454-463`**: On `KeyError` in `_reinit_joystick()`, fall back to `pygame.joystick.quit()/init()`, re-query count, initialize first available, or set `self.joystick = None`. Also reset `self.pad_state` to clear stale axis repeat state.

This gracefully recovers from the pygame joystick subsystem desync instead of crashing.

### Files Modified
- `input/gamepad.py` — `handle_gamepad_connect()`: wrap in try/except, recover subsystem
- `app.py` — `_reinit_joystick()`: wrap in try/except, recover subsystem, reset `pad_state`

### Verification
- `python -m py_compile app.py input/gamepad.py` — clean compile
- Simulated `KeyError: 2` by mocking `JOYDEVICEADDED` with invalid index — handler recovers, `gm.joystick` becomes valid `Joystick(0)` or `None`, no crash

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)

## Bug: Game Exit Auto-Relaunch

### Symptoms
When exiting an emulator (e.g. PPSSPP, PCSX2), the game would immediately boot up again, locking the user in a launch loop.

### Root Cause
While the emulator is running, the Game Machine Python frontend is frozen in a blocked process execution state (`subprocess.run`). However, gamepad controller inputs (joystick button presses) do not require focus to be processed by SDL / Pygame. Therefore, any button press (including the exit or confirmation buttons pressed during gameplay) accumulates in the background OS input event queue.
When the emulator exits and focus returns to the frontend script, the next loop iteration immediately reads the stale event queue, registers the "Confirm (A/Enter)" button press, and starts the game again.

### Solution
In `launch_game()`, right after the `subprocess.run` command terminates, we wait briefly for the emulator to completely release processes, and then purge the Pygame event queue before returning control to the main UI loop:

```python
import pygame

# 1. Wait briefly for emulator to close fully
pygame.time.wait(500)

# 2. Clear all stale/cached joystick and key events
pygame.event.clear()
```

This ensures that the event queue is clean when control is handed back to the UI navigation logic.

## Related Pages
- [Architecture](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/architecture.md)
- [Smart Features](file:///c:/Users/jadam/Desktop/Game-Machine/wiki/smart_features.md)
