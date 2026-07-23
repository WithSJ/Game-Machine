"""
GAME MACHINE - Emulator version detection and update checking.
"""
import os
import re
import json
import urllib.request
import subprocess
from core.config import EMULATOR_DOWNLOADS, get_emulators_dir


def get_installed_emulator_version(emulator_name, emulators_dir=None):
    """
    Get the installed version of an emulator by checking its executable.
    Returns version string or None if not installed/undetectable.
    """
    info = EMULATOR_DOWNLOADS.get(emulator_name)
    if not info:
        return None
    
    if emulators_dir is None:
        emulators_dir = get_emulators_dir()
    exe_path = os.path.join(emulators_dir, info["folder"], info["exe"])
    
    if not os.path.isfile(exe_path):
        return None
    
    # Try different methods to get version
    version = _get_version_from_file_properties(exe_path)
    if version:
        return version
    
    # Fallback: try running with --version or -version
    version = _get_version_from_cli(exe_path)
    if version:
        return version
    
    return None


def _get_version_from_file_properties(exe_path):
    """Extract version from Windows file properties (EXE metadata)."""
    try:
        # Use PowerShell to get file version info
        ps_cmd = f'(Get-Item "{exe_path}").VersionInfo.FileVersion'
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _get_version_from_cli(exe_path):
    """Try to get version by running executable with version flags."""
    for flag in ["--version", "-version", "/version", "-v", "/v"]:
        try:
            result = subprocess.run(
                [exe_path, flag],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout or result.stderr
            if output:
                # Extract version number from output
                match = re.search(r'(\d+\.\d+\.\d+(?:-\d+)?)', output)
                if match:
                    return match.group(1)
        except Exception:
            pass
    return None


def check_github_latest_version(repo, current_version):
    """
    Check GitHub API for latest release version.
    Returns (latest_version, download_url, release_notes_url) or (None, None, None) on failure.
    """
    try:
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'GameMachine/1.0', 'Accept': 'application/vnd.github.v3+json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.load(response)
        
        latest_tag = data.get("tag_name", "")
        latest_version = latest_tag.lstrip('v')
        
        # Find matching asset URL
        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "").lower()
            # Match based on emulator type
            if "ppsspp" in repo.lower() and name.endswith(".zip") and "windows" in name and "x64" in name:
                download_url = asset.get("browser_download_url")
                break
            elif "pcsx2" in repo.lower() and name.endswith(".7z") and "windows" in name and "qt" in name:
                download_url = asset.get("browser_download_url")
                break
            elif "rpcs3" in repo.lower() and name.endswith(".7z") and "win64" in name:
                download_url = asset.get("browser_download_url")
                break
        
        # If no specific asset found, use first matching asset
        if not download_url and data.get("assets"):
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if name.endswith((".zip", ".7z")) and "win" in name:
                    download_url = asset.get("browser_download_url")
                    break
        
        release_url = data.get("html_url", "")
        
        return latest_version, download_url, release_url
        
    except Exception:
        return None, None, None


def compare_versions(current, latest):
    """
    Compare two version strings.
    Returns: -1 if current < latest, 0 if equal, 1 if current > latest
    """
    if not current or not latest:
        return 0
    
    def parse_ver(v):
        # Split into numeric and non-numeric parts
        parts = []
        for part in re.split(r'([0-9]+)', v):
            if part.isdigit():
                parts.append(int(part))
            elif part:
                parts.append(part)
        return parts
    
    current_parts = parse_ver(current)
    latest_parts = parse_ver(latest)
    
    for c, l in zip(current_parts, latest_parts):
        if isinstance(c, int) and isinstance(l, int):
            if c < l:
                return -1
            elif c > l:
                return 1
        else:
            if c < l:
                return -1
            elif c > l:
                return 1
    
    if len(current_parts) < len(latest_parts):
        return -1
    elif len(current_parts) > len(latest_parts):
        return 1
    return 0


def scan_existing_emulators(emulators_dir=None):
    """
    Scan the emulators directory and return dict of installed emulators with versions.
    Returns: {emulator_name: {"installed": bool, "version": str, "exe_path": str}}
    """
    result = {}
    if emulators_dir is None:
        emulators_dir = get_emulators_dir()
    
    if not os.path.isdir(emulators_dir):
        return result
    
    for emu_name, info in EMULATOR_DOWNLOADS.items():
        exe_path = os.path.join(emulators_dir, info["folder"], info["exe"])
        installed = os.path.isfile(exe_path)
        version = get_installed_emulator_version(emu_name, emulators_dir) if installed else None
        
        result[emu_name] = {
            "installed": installed,
            "version": version,
            "exe_path": exe_path if installed else None,
            "folder": info["folder"],
            "latest_version": info["version"],
        }
    
    return result


def check_emulator_updates(emulators_dir=None):
    """
    Check all installed emulators for updates.
    Returns dict: {emulator_name: {"update_available": bool, "current": str, "latest": str, "release_url": str, "download_url": str}}
    """
    installed = scan_existing_emulators(emulators_dir)
    updates = {}
    
    for emu_name, info in installed.items():
        if not info["installed"] or not info["version"]:
            updates[emu_name] = {
                "update_available": False,
                "current": "Not installed",
                "latest": EMULATOR_DOWNLOADS[emu_name]["version"],
                "release_url": "",
                "download_url": EMULATOR_DOWNLOADS[emu_name]["url"],
            }
            continue
        
        repo = EMULATOR_DOWNLOADS[emu_name].get("github_repo")
        if repo:
            latest_ver, download_url, release_url = check_github_latest_version(repo, info["version"])
            
            if latest_ver:
                cmp = compare_versions(info["version"], latest_ver)
                updates[emu_name] = {
                    "update_available": cmp < 0,
                    "current": info["version"],
                    "latest": latest_ver,
                    "release_url": release_url,
                    "download_url": download_url or EMULATOR_DOWNLOADS[emu_name]["url"],
                }
            else:
                # Fallback to configured version
                configured = EMULATOR_DOWNLOADS[emu_name]["version"]
                cmp = compare_versions(info["version"], configured)
                updates[emu_name] = {
                    "update_available": cmp < 0,
                    "current": info["version"],
                    "latest": configured,
                    "release_url": "",
                    "download_url": EMULATOR_DOWNLOADS[emu_name]["url"],
                }
        else:
            updates[emu_name] = {
                "update_available": False,
                "current": info["version"],
                "latest": info["version"],
                "release_url": "",
                "download_url": "",
            }
    
    return updates