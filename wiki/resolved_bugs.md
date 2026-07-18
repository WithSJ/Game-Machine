# Game Machine Resolved Bugs

*Source: [Game-Machine-Documentation.md](file:///c:/Users/jadam/Desktop/Game-Machine/sources/Game-Machine-Documentation.md)*

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
