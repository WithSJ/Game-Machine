"""
GAME MACHINE - Play-time tracking (powers the RECENTS tab + hero banner stats).
"""
import os
import json
from datetime import date

from core.config import PLAYDATA_FILE, PROJECT_DIR, BASE


def load_playdata():
    # 1. Try to load from BASE first (since it contains their actual playtimes if it was run there)
    if BASE and os.path.isdir(BASE):
        base_path = os.path.join(BASE, "playtime.json")
        if os.path.isfile(base_path):
            try:
                with open(base_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge local settings if they are present
                    local_path = os.path.join(PROJECT_DIR, "playtime.json")
                    if os.path.isfile(local_path):
                        with open(local_path, "r", encoding="utf-8") as lf:
                            local_data = json.load(lf)
                            if "__settings__" in local_data:
                                data["__settings__"] = local_data["__settings__"]
                    return data
            except (OSError, ValueError):
                pass

    # 2. Fallback to local playtime.json
    local_path = os.path.join(PROJECT_DIR, "playtime.json")
    try:
        if os.path.isfile(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    return {}


def save_playdata(data):
    # Save locally next to console.py (so settings are remembered at next startup)
    local_path = os.path.join(PROJECT_DIR, "playtime.json")
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass

    # Save in BASE if BASE is configured and exists (preserves portability and existing playtimes)
    if BASE and os.path.isdir(BASE) and os.path.normpath(BASE) != os.path.normpath(PROJECT_DIR):
        base_path = os.path.join(BASE, "playtime.json")
        try:
            with open(base_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # tracking is a bonus feature - never block launching over it


def fmt_dur(seconds):
    """4h 20m style duration."""
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{max(1, minutes)}m"


def fmt_last(timestamp):
    """Relative 'last played' label in plain English."""
    days = (date.today() - date.fromtimestamp(timestamp)).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "last week"
    return date.fromtimestamp(timestamp).strftime("%d %b %Y")
