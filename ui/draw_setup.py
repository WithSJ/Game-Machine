"""
GAME MACHINE - Setup Screen drawing and interactions.
Simplified: only 2 buttons - "Setup Game Machine" (fully automatic) and "Exit"
"""
import os
import math
import random
import threading
import tkinter as tk
from tkinter import filedialog
import pygame
import pygame.gfxdraw

from ui.theme import (
    SCREEN_W, SCREEN_H, COL_BG, COL_PANEL, COL_PANEL2, COL_TEXT,
    COL_DIM, COL_DIMMER, COL_CARD_BORDER, COL_BTN_Y, COL_BTN_B, COL_PAD_OK,
    REC_COLOR, COL_BRAND, COL_TEXT_ON_RED, mix, ease_out
)
from ui.helpers import parallelogram
from core.config import get_emulators_dir, EMULATOR_DOWNLOADS


def pick_directory(title="Select Folder"):
    root = tk.Tk()
    try:
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askdirectory(title=title)
    finally:
        root.destroy()
    return path


# ============================================================
# AUTOMATIC SETUP THREAD
# ============================================================
class AutoSetupThread:
    """Handles the complete automatic setup in a background thread."""
    
    def __init__(self, gm, root_folder):
        self.gm = gm
        self.root_folder = root_folder
        self.active = False
        self.step = 0
        self.total_steps = 6
        self.progress = 0.0
        self.status = ""
        self.log_lines = []
        self.error = None
        self.thread = None
        self.finished = False
        self.success = False

    def start(self):
        self.active = True
        self.finished = False
        self.success = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            self._log("Starting Game Machine automatic setup...")
            
            # Step 1: Create folder structure
            self.step = 1
            self.status = "Creating folder structure..."
            self._update_progress()
            self._create_folders()
            
            # Step 2: Set emulators folder
            self.step = 2
            self.status = "Configuring emulators folder..."
            self._update_progress()
            self._setup_emulators_folder()
            
            # Step 3: Download PPSSPP
            self.step = 3
            self.status = "Downloading PPSSPP (PSP)..."
            self._update_progress()
            self._download_emulator("PPSSPP")
            
            # Step 4: Download PCSX2
            self.step = 4
            self.status = "Downloading PCSX2 (PS2)..."
            self._update_progress()
            self._download_emulator("PCSX2")
            
            # Step 5: Download RPCS3
            self.step = 5
            self.status = "Downloading RPCS3 (PS3)..."
            self._update_progress()
            self._download_emulator("RPCS3")
            
            # Step 6: Save settings and finish
            self.step = 6
            self.status = "Finalizing setup..."
            self._update_progress()
            self._finalize()
            
            self.success = True
            self.status = "Setup complete!"
            self._log("All done! Launching Game Machine...")
            
        except Exception as e:
            self.error = str(e)
            self.status = f"Error: {e}"
            self._log(f"ERROR: {e}")
        finally:
            self.finished = True
            self.active = False

    def _log(self, message):
        self.log_lines.append(message)
        if len(self.log_lines) > 20:
            self.log_lines.pop(0)
        # Also print to terminal/console
        print(f"[GameMachine Setup] {message}")

    def _update_progress(self):
        self.progress = self.step / self.total_steps

    def _create_folders(self):
        """Create the complete folder structure."""
        folders = [
            "emulators",
            "PSP_iso",
            "PS2_iso", 
            "PS3_iso",
            "covers",
        ]
        for folder in folders:
            path = os.path.join(self.root_folder, folder)
            os.makedirs(path, exist_ok=True)
            self._log(f"Created: {folder}/")
        
        # Also create emulators subfolders
        emu_folders = ["PPSSPP_win", "PCSX2_win", "RPCS3_win"]
        for emu in emu_folders:
            path = os.path.join(self.root_folder, "emulators", emu)
            os.makedirs(path, exist_ok=True)
            self._log(f"Created: emulators/{emu}/")

    def _setup_emulators_folder(self):
        """Configure emulators folder in settings."""
        emu_dir = os.path.join(self.root_folder, "emulators")
        self.gm.settings["emulators_folder"] = emu_dir
        self._log(f"Emulators folder: {emu_dir}")

    def _download_emulator(self, console_name):
        """Download and extract a single emulator."""
        info = EMULATOR_DOWNLOADS[console_name]
        url = info["url"]
        folder = info["folder"]
        exe_name = info["exe"]
        
        emulators_dir = os.path.join(self.root_folder, "emulators")
        target_dir = os.path.join(emulators_dir, folder)
        
        self._log(f"Downloading {console_name} from {url}")
        
        import urllib.request
        import zipfile
        import py7zr
        import shutil
        import subprocess
        import tempfile
        import time
        
        # Download to a named file (not temp) so we control the handle
        ext = self._get_ext(url)
        temp_file = os.path.join(tempfile.gettempdir(), f"gm_{folder}_download{ext}")
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                p = min(0.9, (block_num * block_size) / total_size)
                self.gm.setup_sub_progress = p
        
        try:
            # Download
            urllib.request.urlretrieve(url, temp_file, reporthook=progress_hook)
            self._log(f"Downloaded {console_name} ({os.path.getsize(temp_file)//1024//1024} MB), extracting...")
            
            # Extract based on file type
            if ext == '.zip':
                self._log(f"Extracting ZIP archive...")
                with zipfile.ZipFile(temp_file, 'r') as zf:
                    zf.extractall(target_dir)
                    
            elif ext == '.7z':
                extracted = self._extract_7z(temp_file, target_dir, console_name)
                if not extracted:
                    # All extraction methods failed - save for manual extraction
                    manual_path = os.path.join(emulators_dir, f"{folder}.7z")
                    # Copy instead of move to avoid file lock issues
                    shutil.copy2(temp_file, manual_path)
                    self._log(f"ERROR: Could not auto-extract {console_name} (needs 7-Zip with BCJ2 support)")
                    self._log(f"Saved 7z file to: {manual_path}")
                    self._log(f"Manual steps:")
                    self._log(f"  1. Install 7-Zip from https://7-zip.org/ if not installed")
                    self._log(f"  2. Right-click {manual_path} -> 7-Zip -> Extract to {folder}/")
                    self._log(f"  3. Or run: \"C:\\Program Files\\7-Zip\\7z.exe\" x \"{manual_path}\" -o\"{target_dir}\"")
                    self._log(f"  4. After extraction, click RETRY to continue setup")
                    raise RuntimeError(
                        f"{console_name} needs manual extraction.\n"
                        f"Saved to: {manual_path}\n"
                        f"Extract to: {target_dir}\n"
                        f"Install 7-Zip from https://7-zip.org/ if needed."
                    )
            
            # Find exe and move to correct location if needed
            exe_path = os.path.join(target_dir, exe_name)
            if not os.path.isfile(exe_path):
                for root, dirs, files in os.walk(target_dir):
                    for f in files:
                        if f.lower() == exe_name.lower():
                            src = os.path.join(root, f)
                            if src != exe_path:
                                shutil.move(src, exe_path)
                                self._log(f"Moved {exe_name} to root of {folder}/")
                            break
            
            if os.path.isfile(exe_path):
                self._log(f"{console_name} installed successfully!")
            else:
                raise FileNotFoundError(f"{exe_name} not found after extraction")
                
        finally:
            # Cleanup temp file - try multiple times to handle file locks
            for attempt in range(5):
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                    break
                except OSError:
                    time.sleep(0.5)

    def _extract_7z(self, archive_path, target_dir, console_name):
        """Try multiple methods to extract a 7z archive. Returns True on success."""
        import subprocess
        import shutil
        import os
        
        # Method 1: Try py7zr first
        try:
            import py7zr
            with py7zr.SevenZipFile(archive_path, 'r') as sz:
                sz.extractall(target_dir)
            self._log(f"Extracted {console_name} using py7zr")
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "bcj2" in err_str or "filter" in err_str or "unsupported" in err_str:
                self._log(f"py7zr cannot extract (BCJ2 filter), trying system 7-Zip...")
            else:
                self._log(f"py7zr failed: {e}, trying system 7-Zip...")
        
        # Method 2: Try system 7-Zip (common install paths)
        sevenzip_paths = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
            r"C:\Program Files\7-Zip\7za.exe",
            r"C:\Program Files\7-Zip\7zr.exe",
        ]
        
        for sz_path in sevenzip_paths:
            if os.path.isfile(sz_path):
                try:
                    self._log(f"Trying system 7-Zip at: {sz_path}")
                    result = subprocess.run(
                        [sz_path, "x", archive_path, f"-o{target_dir}", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        self._log(f"Extracted {console_name} using system 7-Zip")
                        return True
                    else:
                        self._log(f"7-Zip returned error: {result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    self._log(f"7-Zip timed out, trying next method...")
                except Exception as e:
                    self._log(f"7-Zip failed: {e}")
        
        # Method 3: Try 7z from PATH
        try:
            result = subprocess.run(
                ["7z", "x", archive_path, f"-o{target_dir}", "-y"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                self._log(f"Extracted {console_name} using 7z from PATH")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Method 4: Download 7zr.exe (standalone 7-Zip reducer) and use it
        try:
            szr_path = self._download_7zr()
            if szr_path:
                self._log(f"Using downloaded 7zr.exe to extract {console_name}...")
                result = subprocess.run(
                    [szr_path, "x", archive_path, f"-o{target_dir}", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    self._log(f"Extracted {console_name} using 7zr.exe")
                    return True
                else:
                    self._log(f"7zr.exe returned error: {result.stderr[:200]}")
        except Exception as e:
            self._log(f"7zr.exe extraction failed: {e}")
        
        return False

    def _download_7zr(self):
        """Download 7zr.exe (standalone 7-Zip reducer) for extracting BCJ2 archives."""
        import urllib.request
        import os
        
        # Save to emulators folder so it persists
        emulators_dir = os.path.join(self.root_folder, "emulators")
        szr_path = os.path.join(emulators_dir, "7zr.exe")
        
        # If already downloaded, use it
        if os.path.isfile(szr_path) and os.path.getsize(szr_path) > 100000:
            return szr_path
        
        # Create emulators directory if it doesn't exist
        os.makedirs(emulators_dir, exist_ok=True)
        
        url = "https://www.7-zip.org/a/7zr.exe"
        self._log(f"Downloading 7zr.exe (standalone 7-Zip extractor) from {url}")
        
        try:
            urllib.request.urlretrieve(url, szr_path)
            if os.path.isfile(szr_path) and os.path.getsize(szr_path) > 100000:
                self._log(f"7zr.exe downloaded successfully ({os.path.getsize(szr_path)//1024} KB)")
                return szr_path
            else:
                self._log(f"7zr.exe download appears incomplete")
                return None
        except Exception as e:
            self._log(f"Failed to download 7zr.exe: {e}")
            return None

    def _get_ext(self, url):
        if url.endswith('.zip'):
            return '.zip'
        elif url.endswith('.7z'):
            return '.7z'
        return '.tmp'

    def _finalize(self):
        """Save settings and trigger rescan."""
        self.gm.settings["folders"] = [self.root_folder]
        self.gm.folders = [self.root_folder]
        
        from core.playdata import save_playdata
        save_playdata(self.gm.playdata)
        
        # Refresh paths
        from core.config import refresh_paths
        refresh_paths()
        
        self._log("Settings saved. Ready to play!")


# ============================================================
# SETUP SCREEN DRAWING
# ============================================================
def draw_setup(gm, now):
    scr = gm.screen
    accent = REC_COLOR

    # Draw dark background
    scr.fill(COL_BG)

    # Draw floating background particles
    gm._overlay.fill((0, 0, 0, 0))
    for pt in gm.particles:
        pt["y"] -= pt["v"]
        if pt["y"] < -4:
            pt["y"] = SCREEN_H + 4
            pt["x"] = random.uniform(0, SCREEN_W)
        tw = 0.25 + 0.35 * abs(math.sin(now / 1400 + pt["ph"]))
        pygame.draw.circle(gm._overlay, accent + (int(tw * 255),),
                           (int(pt["x"]), int(pt["y"])), pt["s"])
    scr.blit(gm._overlay, (0, 0))

    # Title Banner
    title_s = gm.f_hero.render("GAME MACHINE SETUP", True, COL_TEXT)
    scr.blit(title_s, (60, 40))
    sub_s = gm.f_small.render("First-time setup: configure your game library and install emulators automatically.", True, COL_DIM)
    scr.blit(sub_s, (60, 92))

    # Check if auto-setup is running
    if getattr(gm, "auto_setup", None) and gm.auto_setup.active:
        draw_auto_setup_progress(gm, now)
        return

    # Check if auto-setup finished
    if getattr(gm, "auto_setup", None) and gm.auto_setup.finished:
        if gm.auto_setup.success:
            draw_setup_complete(gm, now)
        else:
            draw_setup_error(gm, now)
        return

    # --- MAIN SETUP UI ---
    # Center panel - increased height to prevent overlap
    panel_w, panel_h = 700, 400
    panel_x = (SCREEN_W - panel_w) // 2
    panel_y = (SCREEN_H - panel_h) // 2

    pygame.draw.rect(scr, COL_PANEL, (panel_x, panel_y, panel_w, panel_h), border_radius=14)
    pygame.draw.rect(scr, accent, (panel_x, panel_y, panel_w, 3), border_radius=14)
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), (panel_x, panel_y, panel_w, panel_h), 1, border_radius=14)

    # Icon/Logo area
    icon_y = panel_y + 40
    # Draw a simple console icon
    pygame.draw.rect(scr, accent, (panel_x + panel_w//2 - 60, icon_y, 120, 120), border_radius=20)
    pygame.draw.rect(scr, COL_BG, (panel_x + panel_w//2 - 40, icon_y + 20, 80, 40), border_radius=8)
    pygame.draw.rect(scr, accent, (panel_x + panel_w//2 - 40, icon_y + 20, 80, 40), 2, border_radius=8)
    # Buttons on console
    pygame.draw.circle(scr, accent, (panel_x + panel_w//2 + 30, icon_y + 40), 8)
    pygame.draw.circle(scr, accent, (panel_x + panel_w//2 - 30, icon_y + 40), 8)

    # Description - compact layout
    desc_y = icon_y + 130
    desc_lines = [
        "Welcome to Game Machine!",
        "This will automatically set up everything:",
        "  • Create folder structure (PSP_iso, PS2_iso, PS3_iso, emulators/, covers/)",
        "  • Download & install PPSSPP, PCSX2, RPCS3 portable emulators",
        "  • Configure all paths for portable use",
        "",
        "Select a root folder to begin (e.g., D:\\Game Machine)"
    ]
    for i, line in enumerate(desc_lines):
        if line == "":
            continue
        if line.startswith("  •"):
            color = COL_DIM
            font = gm.f_small
            x_offset = 40
        elif line.startswith("Welcome") or line.startswith("Select"):
            color = COL_TEXT
            font = gm.f_small
            x_offset = 0
        else:
            color = COL_DIM
            font = gm.f_small
            x_offset = 20
        text_s = font.render(line, True, color)
        scr.blit(text_s, (panel_x + (panel_w - text_s.get_width()) // 2 + x_offset, desc_y + i * 22))

    # --- TWO BUTTONS ---
    btn_w, btn_h = 280, 50
    btn_gap = 20
    total_w = btn_w * 2 + btn_gap
    btn_start_x = panel_x + (panel_w - total_w) // 2
    btn_y = panel_y + panel_h - 80

    # Setup Game Machine button (primary)
    setup_btn_r = pygame.Rect(btn_start_x, btn_y, btn_w, btn_h)
    gm.setup_btn_rect = setup_btn_r
    
    is_setup_hover = setup_btn_r.collidepoint(pygame.mouse.get_pos())
    setup_bg = accent if is_setup_hover else mix(COL_BG, accent, 0.2)
    setup_border = accent if is_setup_hover else COL_CARD_BORDER
    
    parallelogram(scr, setup_btn_r, setup_bg, cut=8)
    parallelogram(scr, setup_btn_r, setup_border, cut=8, width=2)
    
    setup_text = gm.f_btn.render("SETUP GAME MACHINE", True, COL_BG if is_setup_hover else COL_TEXT)
    scr.blit(setup_text, setup_text.get_rect(center=setup_btn_r.center))

    # Exit button (secondary)
    exit_btn_r = pygame.Rect(btn_start_x + btn_w + btn_gap, btn_y, btn_w, btn_h)
    gm.exit_btn_rect = exit_btn_r
    
    is_exit_hover = exit_btn_r.collidepoint(pygame.mouse.get_pos())
    exit_bg = COL_BTN_B if is_exit_hover else COL_PANEL2
    exit_border = COL_BTN_B if is_exit_hover else COL_CARD_BORDER
    
    parallelogram(scr, exit_btn_r, exit_bg, cut=8)
    if not is_exit_hover:
        parallelogram(scr, exit_btn_r, exit_border, cut=8, width=1)
    
    exit_text = gm.f_btn.render("EXIT", True, COL_TEXT_ON_RED if is_exit_hover else COL_DIM)
    scr.blit(exit_text, exit_text.get_rect(center=exit_btn_r.center))

    # Hint
    hint_s = gm.f_mono.render("Enter/Space/A = Select    Mouse = Click    ESC = Exit", True, COL_DIMMER)
    scr.blit(hint_s, (panel_x + (panel_w - hint_s.get_width()) // 2, panel_y + panel_h - 20))


def draw_auto_setup_progress(gm, now):
    """Draw the progress screen during automatic setup."""
    scr = gm.screen
    accent = REC_COLOR
    setup = gm.auto_setup

    # Dark overlay
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    scr.blit(overlay, (0, 0))

    # Progress panel
    pw, ph = 800, 500
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    panel_r = pygame.Rect(px, py, pw, ph)

    pygame.draw.rect(scr, COL_PANEL, panel_r, border_radius=14)
    pygame.draw.rect(scr, accent, (px, py, pw, 3), border_radius=14)
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), panel_r, 1, border_radius=14)

    # Title
    title_s = gm.f_popup_title.render("SETTING UP GAME MACHINE", True, accent)
    scr.blit(title_s, (px + (pw - title_s.get_width()) // 2, py + 20))

    # Current status
    status_s = gm.f_small.render(setup.status, True, COL_TEXT)
    scr.blit(status_s, (px + 30, py + 70))

    # Main progress bar
    bar_x, bar_y = px + 30, py + 110
    bar_w, bar_h = pw - 60, 28
    pygame.draw.rect(scr, COL_PANEL2, (bar_x, bar_y, bar_w, bar_h), border_radius=6)
    pygame.draw.rect(scr, COL_CARD_BORDER, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)
    
    fill_w = int(bar_w * setup.progress)
    if fill_w > 0:
        pygame.draw.rect(scr, accent, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
    
    pct_s = gm.f_small.render(f"{int(setup.progress * 100)}%", True, COL_BG)
    scr.blit(pct_s, (bar_x + bar_w - pct_s.get_width() - 10, bar_y + 4))

    # Sub-progress (for current emulator download)
    if hasattr(gm, 'setup_sub_progress') and gm.setup_sub_progress > 0:
        sub_y = bar_y + bar_h + 10
        sub_w = pw - 60
        pygame.draw.rect(scr, COL_PANEL2, (bar_x, sub_y, sub_w, 12), border_radius=4)
        sub_fill = int(sub_w * gm.setup_sub_progress)
        if sub_fill > 0:
            pygame.draw.rect(scr, COL_BRAND, (bar_x, sub_y, sub_fill, 12), border_radius=4)

    # Step indicators
    step_y = bar_y + 50
    steps = [
        ("1", "Create Folders"),
        ("2", "Configure Emulators"),
        ("3", "Download PPSSPP"),
        ("4", "Download PCSX2"),
        ("5", "Download RPCS3"),
        ("6", "Finalize"),
    ]
    for i, (num, label) in enumerate(steps):
        x = px + 30 + i * 125
        y = step_y
        completed = i < setup.step - 1
        current = i == setup.step - 1
        
        circle_r = 18
        circle_x = x
        circle_y = y + 12
        
        if completed:
            pygame.draw.circle(scr, COL_PAD_OK, (circle_x, circle_y), circle_r)
            pygame.draw.circle(scr, COL_PAD_OK, (circle_x, circle_y), circle_r - 2)
            check_s = gm.f_small.render("✓", True, COL_BG)
            scr.blit(check_s, check_s.get_rect(center=(circle_x, circle_y)))
        elif current:
            pygame.draw.circle(scr, accent, (circle_x, circle_y), circle_r, 3)
            pygame.draw.circle(scr, accent, (circle_x, circle_y), circle_r - 2)
        else:
            pygame.draw.circle(scr, COL_DIMMER, (circle_x, circle_y), circle_r, 2)
            num_s = gm.f_small.render(num, True, COL_DIMMER)
            scr.blit(num_s, num_s.get_rect(center=(circle_x, circle_y)))
        
        label_s = gm.f_small.render(label, True, COL_TEXT if current else COL_DIM)
        scr.blit(label_s, (x - label_s.get_width() // 2, y + 40))

    # Log area
    log_y = step_y + 70
    log_h = ph - (log_y - py) - 30
    log_r = pygame.Rect(px + 20, log_y, pw - 40, log_h)
    pygame.draw.rect(scr, COL_BG, log_r, border_radius=6)
    pygame.draw.rect(scr, COL_CARD_BORDER, log_r, 1, border_radius=6)

    # Draw log lines (most recent at bottom)
    log_font = gm.f_mono
    line_h = 18
    visible_lines = log_h // line_h
    start_idx = max(0, len(setup.log_lines) - visible_lines)
    
    for i, line in enumerate(setup.log_lines[start_idx:]):
        line_y = log_r.y + 8 + i * line_h
        if line_y + line_h > log_r.bottom - 8:
            break
        color = COL_DIM if "Created" in line or "Downloading" in line else COL_TEXT
        if "ERROR" in line.upper():
            color = COL_BTN_B
        elif "success" in line.lower() or "installed" in line.lower():
            color = COL_PAD_OK
        line_s = log_font.render(line, True, color)
        scr.blit(line_s, (log_r.x + 10, line_y))

    # Spinner animation
    if setup.active:
        spin_x = bar_x + bar_w + 30
        spin_y = bar_y + bar_h // 2
        angle = (now / 50) % 360
        for i in range(8):
            a = angle + i * 45
            rad = math.radians(a)
            x = spin_x + int(12 * math.cos(rad))
            y = spin_y + int(12 * math.sin(rad))
            alpha = int(255 * (1 - i / 8))
            pygame.draw.circle(scr, accent + (alpha,), (x, y), 4)


def draw_setup_complete(gm, now):
    """Draw success screen after setup completes."""
    scr = gm.screen
    accent = COL_PAD_OK

    # Auto-transition after 3 seconds
    if not hasattr(gm, 'setup_complete_time'):
        gm.setup_complete_time = now
    if now - gm.setup_complete_time > 3000:
        gm.needs_setup = False
        gm.finish_setup()
        return

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    scr.blit(overlay, (0, 0))

    pw, ph = 500, 300
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2

    pygame.draw.rect(scr, COL_PANEL, (px, py, pw, ph), border_radius=14)
    pygame.draw.rect(scr, accent, (px, py, pw, 3), border_radius=14)

    # Checkmark animation
    check_y = py + 60
    prog = min(1.0, (now - gm.setup_complete_time) / 500)
    radius = int(40 * ease_out(prog))
    pygame.draw.circle(scr, accent, (px + pw // 2, check_y), radius, 4)
    if prog > 0.5:
        check_s = gm.f_hero.render("✓", True, accent)
        scr.blit(check_s, check_s.get_rect(center=(px + pw // 2, check_y)))

    title_s = gm.f_popup_title.render("SETUP COMPLETE!", True, accent)
    scr.blit(title_s, (px + (pw - title_s.get_width()) // 2, check_y + 60))

    msg_s = gm.f_small.render("Launching Game Machine...", True, COL_DIM)
    scr.blit(msg_s, (px + (pw - msg_s.get_width()) // 2, check_y + 110))


def draw_setup_error(gm, now):
    """Draw error screen if setup fails - shows full logs for debugging."""
    scr = gm.screen
    accent = COL_BTN_B
    setup = gm.auto_setup

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    scr.blit(overlay, (0, 0))

    pw, ph = 800, 550
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2

    pygame.draw.rect(scr, COL_PANEL, (px, py, pw, ph), border_radius=14)
    pygame.draw.rect(scr, accent, (px, py, pw, 3), border_radius=14)
    pygame.draw.rect(scr, mix(COL_BG, accent, 0.4), (px, py, pw, ph), 1, border_radius=14)

    title_s = gm.f_popup_title.render("SETUP FAILED", True, accent)
    scr.blit(title_s, (px + (pw - title_s.get_width()) // 2, py + 20))

    # Error summary
    err_summary = setup.error if setup.error else "Unknown error"
    err_s = gm.f_small.render(f"Error: {err_summary}", True, COL_BTN_B)
    scr.blit(err_s, (px + 30, py + 60))

    # Full log area
    log_label = gm.f_small.render("Setup Logs (most recent first):", True, COL_DIM)
    scr.blit(log_label, (px + 30, py + 90))

    log_r = pygame.Rect(px + 20, py + 115, pw - 40, ph - 170)
    pygame.draw.rect(scr, COL_BG, log_r, border_radius=6)
    pygame.draw.rect(scr, COL_CARD_BORDER, log_r, 1, border_radius=6)

    # Draw log lines (most recent at bottom)
    log_font = gm.f_mono
    line_h = 18
    visible_lines = log_r.h // line_h
    start_idx = max(0, len(setup.log_lines) - visible_lines)
    
    for i, line in enumerate(setup.log_lines[start_idx:]):
        line_y = log_r.y + 8 + i * line_h
        if line_y + line_h > log_r.bottom - 8:
            break
        color = COL_DIM
        if "ERROR" in line.upper():
            color = COL_BTN_B
        elif "success" in line.lower() or "installed" in line.lower() or "created" in line.lower():
            color = COL_PAD_OK
        elif "Downloading" in line or "Extracting" in line:
            color = COL_BRAND
        line_s = log_font.render(line, True, color)
        scr.blit(line_s, (log_r.x + 10, line_y))

    # Retry / Exit buttons
    btn_w, btn_h = 180, 48
    btn_y = py + ph - 70
    retry_r = pygame.Rect(px + pw//2 - btn_w - 20, btn_y, btn_w, btn_h)
    exit_r = pygame.Rect(px + pw//2 + 20, btn_y, btn_w, btn_h)

    gm.setup_retry_rect = retry_r
    gm.setup_exit_rect = exit_r

    for r, label, color in [(retry_r, "RETRY SETUP", COL_PAD_OK), (exit_r, "EXIT", COL_BTN_B)]:
        hover = r.collidepoint(pygame.mouse.get_pos())
        bg = color if hover else mix(COL_BG, color, 0.2)
        parallelogram(scr, r, bg, cut=8)
        parallelogram(scr, r, color, cut=8, width=2 if not hover else 0)
        text = gm.f_btn.render(label, True, COL_BG if hover else COL_TEXT)
        scr.blit(text, text.get_rect(center=r.center))

    # Hint
    hint_s = gm.f_small.render("Check logs above for details. RETRY will restart from beginning.", True, COL_DIMMER)
    scr.blit(hint_s, (px + (pw - hint_s.get_width()) // 2, btn_y + btn_h + 10))


# Keep the old help modal for reference (can be removed if not needed)
def draw_setup_help_modal(gm, now):
    pass