"""
GAME MACHINE - Windows auto-start registry management.
"""
import os
import sys
import winreg

from core.config import AUTOSTART_KEY, AUTOSTART_NAME, SCRIPT_PATH


def is_auto_start_enabled():
    """Check if Game Machine is in the Windows startup registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, AUTOSTART_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


def set_auto_start(enabled):
    """Add or remove Game Machine from Windows startup registry."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            # Use pythonw to avoid console window on startup
            python_exe = sys.executable
            if python_exe.lower().endswith("python.exe"):
                pythonw = python_exe[:-10] + "pythonw.exe"
                if os.path.isfile(pythonw):
                    python_exe = pythonw
            cmd = f'"{ python_exe}" "{SCRIPT_PATH}"'
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError as e:
        print(f"[Auto-Start] Registry error: {e}")
