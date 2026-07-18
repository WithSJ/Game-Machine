"""
GAME MACHINE - Play-time tracking (powers the RECENTS tab + hero banner stats).
"""
import os
import json
from datetime import date

from core.config import PLAYDATA_FILE, PROJECT_DIR, BASE


def load_playdata():
    data = {}
    
    # 1. Load from local playtime.json first
    local_path = os.path.join(PROJECT_DIR, "playtime.json")
    if os.path.isfile(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
                if isinstance(local_data, dict):
                    data.update(local_data)
        except (OSError, ValueError):
            pass
            
    # 2. Load from BASE/playtime.json and merge (so if they have playtimes there, they are preserved)
    # Check both the static BASE and any folders configured in data
    folders_to_check = []
    if BASE:
        folders_to_check.append(BASE)
    settings = data.get("__settings__", {})
    for f in settings.get("folders", []):
        if f not in folders_to_check:
            folders_to_check.append(f)

    for base_dir in folders_to_check:
        if base_dir and os.path.isdir(base_dir):
            base_path = os.path.join(base_dir, "playtime.json")
            if os.path.isfile(base_path):
                try:
                    with open(base_path, "r", encoding="utf-8") as f:
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
    # Save locally next to console.py (so settings are remembered at next startup)
    local_path = os.path.join(PROJECT_DIR, "playtime.json")
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass

    # Save in BASE if BASE is configured and exists (preserves portability and existing playtimes)
    # Resolve BASE dynamically from the data to prevent out-of-sync issues during setup
    settings = data.get("__settings__", {})
    folders = settings.get("folders", [])
    base_dir = folders[0] if folders else BASE

    if base_dir and os.path.isdir(base_dir) and os.path.normpath(base_dir) != os.path.normpath(PROJECT_DIR):
        base_path = os.path.join(base_dir, "playtime.json")
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
