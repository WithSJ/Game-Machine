import os
import shutil
import subprocess
import threading
from core.config import BASE, PROJECT_DIR
from core.scanner import clean_name

def _resolve_tool_dir():
    """Locate the PS3Dec tool directory.

    Searches the configured BASE folder(s) first, then PROJECT_DIR, so the
    path travels with the portable Game Machine folder instead of being
    hardcoded to a single drive letter.
    """
    candidates = []
    settings_folders = []
    try:
        from core.config import load_settings
        settings_folders = load_settings().get("folders", [])
    except Exception:
        pass
    if BASE:
        candidates.append(BASE)
    for f in settings_folders:
        if f and f not in candidates:
            candidates.append(f)
    if PROJECT_DIR and PROJECT_DIR not in candidates:
        candidates.append(PROJECT_DIR)

    tool_subdirs = [
        "PS3QDD.v1.3.2.with.keys",
        "PS3QDD",
    ]
    for base_dir in candidates:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        for sub in tool_subdirs:
            p = os.path.join(base_dir, sub)
            if os.path.isfile(os.path.join(p, "PS3Dec.exe")):
                return p
        # Also scan immediate children of base_dir for any PS3QDD* folder
        try:
            for entry in os.listdir(base_dir):
                if entry.lower().startswith("ps3qdd") and os.path.isdir(os.path.join(base_dir, entry)):
                    p = os.path.join(base_dir, entry)
                    if os.path.isfile(os.path.join(p, "PS3Dec.exe")):
                        return p
        except OSError:
            pass
    # Final fallback: legacy hardcoded path
    return r"D:\Game Machine\PS3QDD.v1.3.2.with.keys"

def find_dkey_path(iso_path, keys_dir):
    """
    Robustly locate the .dkey file matching the game's ISO filename.
    """
    iso_filename = os.path.basename(iso_path)
    base_name = os.path.splitext(iso_filename)[0]
    
    # 1. Try exact filename match first (with .dkey extension)
    exact_path = os.path.join(keys_dir, base_name + ".dkey")
    if os.path.isfile(exact_path):
        return exact_path
        
    try:
        keys_files = os.listdir(keys_dir)
    except Exception:
        return None
        
    # 2. Case-insensitive exact name check
    base_name_lower = base_name.lower()
    for f in keys_files:
        if f.lower() == base_name_lower + ".dkey":
            return os.path.join(keys_dir, f)
            
    # 3. Fuzzy matching based on cleaned name
    cleaned_iso = clean_name(iso_filename).lower()
    best_match = None
    best_score = 0
    
    for f in keys_files:
        if not f.lower().endswith(".dkey"):
            continue
        cleaned_key = clean_name(f).lower()
        if cleaned_key == cleaned_iso:
            # If the clean names match, prioritize based on token overlap
            common = set(base_name_lower.split()) & set(f.lower().replace(".dkey", "").split())
            score = len(common)
            if score > best_score:
                best_score = score
                best_match = f
                
    if best_match:
        return os.path.join(keys_dir, best_match)
        
    return None

def run_decryption_thread(gm, game):
    """
    Background thread target for decrypting a PS3 ISO file.
    """
    try:
        # Configuration paths
        tool_dir = _resolve_tool_dir()
        ps3dec_exe = os.path.join(tool_dir, "PS3Dec.exe")
        keys_dir = os.path.join(tool_dir, "Keys")
        decrypted_dir = os.path.join(tool_dir, "Decrypted")
        
        if not os.path.exists(ps3dec_exe):
            gm.decryption_error = f"PS3Dec.exe not found at:\n{ps3dec_exe}"
            return
            
        gm.decryption_status = "Locating decryption key..."
        dkey_path = find_dkey_path(game["path"], keys_dir)
        if not dkey_path or not os.path.exists(dkey_path):
            gm.decryption_error = "No matching key (.dkey) found in Keys folder."
            return
            
        gm.decryption_status = "Reading decryption key..."
        with open(dkey_path, "r", encoding="utf-8") as f:
            key_hex = f.read().strip()
            
        if len(key_hex) != 32:
            gm.decryption_error = f"Invalid key length ({len(key_hex)} chars). Must be 32."
            return
            
        gm.decryption_status = "Decrypting ISO (using PS3Dec)..."
        
        os.makedirs(decrypted_dir, exist_ok=True)
        iso_name = os.path.basename(game["path"])
        temp_decrypted_path = os.path.join(decrypted_dir, iso_name)
        
        # If temporary file already exists, try to delete it
        if os.path.exists(temp_decrypted_path):
            try:
                os.remove(temp_decrypted_path)
            except Exception:
                pass
                
        # Run PS3Dec: PS3Dec.exe d key <key> <in_iso> <out_iso>
        cmd = [ps3dec_exe, "d", "key", key_hex, game["path"], temp_decrypted_path]
        
        proc = subprocess.Popen(
            cmd,
            cwd=tool_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        stdout, stderr = proc.communicate()
        
        if proc.returncode != 0:
            err_msg = stderr.decode(errors='ignore').strip() or "PS3Dec error code: " + str(proc.returncode)
            gm.decryption_error = f"Decryption failed:\n{err_msg}"
            return
            
        if not os.path.exists(temp_decrypted_path) or os.path.getsize(temp_decrypted_path) < 1000000:
            gm.decryption_error = "Decrypted file was not created or is invalid."
            return
            
        gm.decryption_status = "Replacing original ISO..."

        # Replace the original encrypted ISO safely.
        # The original file is renamed to a .enc.bak first; the freshly
        # decrypted ISO is then moved into its place. Only after the move
        # succeeds is the backup deleted. If anything goes wrong mid-way
        # we restore the backup so the user never loses their game file.
        original_path = game["path"]
        backup_path = original_path + ".enc.bak"
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(original_path):
                os.rename(original_path, backup_path)
            try:
                shutil.move(temp_decrypted_path, original_path)
            except Exception as move_err:
                # Restore the encrypted ISO if the decrypted one couldn't land
                if os.path.exists(backup_path) and not os.path.exists(original_path):
                    os.rename(backup_path, original_path)
                raise move_err
            # Decrypted ISO is in place - drop the encrypted backup
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except OSError:
                    pass
        except Exception as e:
            gm.decryption_error = f"Failed to replace original ISO:\n{e}"
            return
            
        gm.decryption_status = "Decryption complete!"
        gm.decryption_done.set()
        
    except Exception as e:
        gm.decryption_error = f"Unexpected system error:\n{e}"
