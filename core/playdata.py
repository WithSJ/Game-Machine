"""
GAME MACHINE - Play-time tracking (powers the RECENTS tab + hero banner stats).
"""
import os
import json
from datetime import date

from core.config import PROJECT_DIR


def get_playdata_path():
    """Return the playtime.json path in the user-selected root folder (first folder in folders list)."""
    # Load settings to get the first folder
    try:
        local_fallback = os.path.join(PROJECT_DIR, "playtime.json")
        if os.path.isfile(local_fallback):
            with open(local_fallback, "r", encoding="utf-8") as f:
                data = json.load(f)
                folders = data.get("__settings__", {}).get("folders", [])
                if folders:
                    return os.path.join(folders[0], "playtime.json")
    except (OSError, ValueError):
        pass
    # Fallback to project directory during initial setup
    return os.path.join(PROJECT_DIR, "playtime.json")


def load_playdata():
    data = {}
    
    # 1. Load from local playtime.json first (for initial setup detection)
    local_path = os.path.join(PROJECT_DIR, "playtime.json")
    if os.path.isfile(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
                if isinstance(local_data, dict):
                    data.update(local_data)
        except (OSError, ValueError):
            pass
            
    # 2. Load from user-selected root folder playtime.json and merge
    user_playdata_path = get_playdata_path()
    if os.path.isfile(user_playdata_path) and user_playdata_path != local_path:
        try:
            with open(user_playdata_path, "r", encoding="utf-8") as f:
                base_data = json.load(f)
                if isinstance(base_data, dict):
                    for k, v in base_data.items():
                        if k == "__settings__":
                            if k not in data:
                                data[k] = {}
                            data[k].update(v)
                        else:
                            if k in data:
                                # Compare seconds and keep the one with more playtime progress
                                sec1 = data[k].get("seconds", 0) if isinstance(data[k], dict) else 0
                                sec2 = v.get("seconds", 0) if isinstance(v, dict) else 0
                                if sec2 > sec1:
                                    data[k] = v
                            else:
                                data[k] = v
        except (OSError, ValueError):
            pass
                     
    return data


def save_playdata(data):
    """Save playtime.json ONLY to the user-selected root folder."""
    playdata_path = get_playdata_path()
    try:
        with open(playdata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass  # tracking is a bonus feature - never block launching over it


def fmt_dur(seconds):
    """4h 20m style duration. 0 seconds shows as '0m' rather than '1m'."""
    minutes = seconds // 60
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


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
