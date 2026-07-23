"""
GAME MACHINE - Emulator downloader and installer.
Downloads portable Windows 64-bit builds for PPSSPP, PCSX2, RPCS3.
"""
import os
import shutil
import threading
import urllib.request
import zipfile
from pathlib import Path

try:
    import py7zr
except ImportError:
    py7zr = None

from core.config import EMULATOR_DOWNLOADS, get_emulators_dir


class EmulatorDownloader:
    def __init__(self, gm):
        self.gm = gm
        self.active = False
        self.current_console = None
        self.progress = 0.0
        self.status = ""
        self.error = None
        self.thread = None
        self.callback = None

    def start_download(self, console_name, callback=None):
        """Start downloading and installing an emulator."""
        if console_name not in EMULATOR_DOWNLOADS:
            self.error = f"Unknown console: {console_name}"
            if callback:
                callback(False, self.error)
            return False
        
        if self.active:
            self.error = "Download already in progress"
            if callback:
                callback(False, self.error)
            return False
        
        self.active = True
        self.current_console = console_name
        self.progress = 0.0
        self.status = f"Preparing {console_name} download..."
        self.error = None
        self.callback = callback
        
        self.thread = threading.Thread(target=self._download_and_install, daemon=True)
        self.thread.start()
        return True

    def _download_and_install(self):
        try:
            info = EMULATOR_DOWNLOADS[self.current_console]
            emulators_dir = get_emulators_dir()
            console_folder = os.path.join(emulators_dir, info["folder"])
            
            self.status = f"Creating folder: {info['folder']}"
            os.makedirs(console_folder, exist_ok=True)
            
            # Download to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_extension(info["url"])) as tmp:
                temp_path = tmp.name
            
            self.status = f"Downloading {self.current_console}..."
            
            def reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    self.progress = min((block_num * block_size) / total_size, 1.0)
                    self.status = f"Downloading {self.current_console}: {self.progress*100:.1f}%"
            
            urllib.request.urlretrieve(info["url"], temp_path, reporthook)
            
            self.status = f"Extracting {self.current_console}..."
            self.progress = 0.0
            
            # Extract based on file type
            if info["url"].endswith(".zip"):
                with zipfile.ZipFile(temp_path, 'r') as zf:
                    zf.extractall(console_folder)
            elif info["url"].endswith(".7z"):
                if py7zr is None:
                    raise RuntimeError("py7zr not installed. Run: pip install py7zr")
                with py7zr.SevenZipFile(temp_path, mode='r') as sz:
                    sz.extractall(console_folder)
            else:
                raise RuntimeError(f"Unsupported archive format for {self.current_console}")
            
            # Verify executable exists
            exe_path = os.path.join(console_folder, info["exe"])
            if not os.path.isfile(exe_path):
                # Try to find it in subdirectories
                for root, dirs, files in os.walk(console_folder):
                    for f in files:
                        if f.lower() == info["exe"].lower():
                            exe_path = os.path.join(root, f)
                            break
            
            if not os.path.isfile(exe_path):
                raise RuntimeError(f"Executable not found after extraction: {info['exe']}")
            
            self.progress = 1.0
            self.status = f"{self.current_console} installed successfully!"
            self.active = False
            
            # Save emulators folder path in settings
            self.gm.settings["emulators_folder"] = get_emulators_dir()
            from core.playdata import save_playdata
            save_playdata(self.gm.playdata)
            
            if self.callback:
                self.callback(True, f"{self.current_console} installed to {console_folder}")
                
        except Exception as e:
            self.error = str(e)
            self.status = f"Error: {e}"
            self.active = False
            if self.callback:
                self.callback(False, str(e))
        finally:
            # Clean up temp file
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    def _get_extension(self, url):
        if url.endswith(".zip"):
            return ".zip"
        elif url.endswith(".7z"):
            return ".7z"
        return ".tmp"

    def cancel(self):
        """Cancel the current download (best effort)."""
        self.active = False
        self.status = "Cancelling..."


def download_all_emulators(gm, callback=None):
    """Download all three standard emulators sequentially."""
    consoles = ["PPSSPP", "PCSX2", "RPCS3"]
    
    def run_sequence(index=0):
        if index >= len(consoles):
            if callback:
                callback(True, "All emulators installed!")
            return
        
        console = consoles[index]
        downloader = EmulatorDownloader(gm)
        
        def on_complete(success, message):
            if not success:
                if callback:
                    callback(False, f"Failed at {console}: {message}")
                return
            # Continue with next
            run_sequence(index + 1)
        
        downloader.start_download(console, on_complete)
    
    run_sequence()