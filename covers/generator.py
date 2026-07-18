"""
GAME MACHINE - Background cover art generation and downloading.
Handles PSP/PS3 ISO extraction and PS2 cover downloading.

NOTE: This module runs entirely in a background daemon thread. SDL/pygame
are NOT thread-safe; in particular, calling pygame.init() or Surface.convert()
from a non-main thread touches the display surface and can crash the app.
We therefore avoid those calls here - surfaces are loaded and saved directly
without converting to the display pixel format.
"""
import io
import os
import urllib.request

import pygame

from core.config import COVERS_DIR
from covers.iso_parser import extract_iso_images
from covers.ps2_serial import get_ps2_serial


def _has_highres_cover(covers_dir, name):
    """True if a usable (>=360px wide) cover already exists for `name`."""
    for ext in (".jpg", ".jpeg", ".png"):
        cov_path = os.path.join(covers_dir, name + ext)
        if not os.path.isfile(cov_path):
            continue
        try:
            img_info = pygame.image.load(cov_path)
            if img_info.get_width() >= 360:
                return True
        except Exception:
            pass
    return False


def _build_composite_cover(icon0_data, pic1_data):
    """Composite a 3:4 (360x480) cover from an ISO's ICON0.PNG and PIC1.PNG.

    Returns a pygame.Surface suitable for pygame.image.save(). No convert()
    /convert_alpha() calls are made on purpose - they would touch the display
    surface and are unnecessary for saving to disk.
    """
    save_w, save_h = 360, 480
    cover_surf = pygame.Surface((save_w, save_h))
    cover_surf.fill((17, 20, 27))

    if pic1_data:
        pic_img = pygame.image.load(io.BytesIO(pic1_data))
        pic_w, pic_h = pic_img.get_size()
        # Center-crop PIC1 to the 3:4 target aspect ratio
        target_aspect = save_w / save_h
        crop_w = int(pic_h * target_aspect)
        crop_x = max(0, (pic_w - crop_w) // 2)

        cropped_pic = pygame.Surface((crop_w, pic_h))
        cropped_pic.blit(pic_img, (0, 0), (crop_x, 0, crop_w, pic_h))
        bg_scaled = pygame.transform.smoothscale(cropped_pic, (save_w, save_h))
        cover_surf.blit(bg_scaled, (0, 0))

        overlay = pygame.Surface((save_w, save_h), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 120))
        cover_surf.blit(overlay, (0, 0))

    if icon0_data:
        icon_img = pygame.image.load(io.BytesIO(icon0_data))
        icon_w, icon_h = icon_img.get_size()
        new_icon_w = 300
        new_icon_h = int(icon_h * (new_icon_w / icon_w))
        icon_scaled = pygame.transform.smoothscale(icon_img, (new_icon_w, new_icon_h))
        icon_x = (save_w - new_icon_w) // 2
        icon_y = (save_h - new_icon_h) // 2
        cover_surf.blit(icon_scaled, (icon_x, icon_y))

    return cover_surf


def background_cover_generator_thread(games, colors, cover_cache, consoles=None):
    """
    Unified background thread that:
    1. Scans PSP/PS3/PPSSPP/RPCS3 games and extracts high-resolution 3:4 composite covers from ISOs.
    2. Scans PS2/PCSX2 games, parses their serial, and downloads cover art from GitHub.
    """
    if consoles is None:
        consoles = {}

    # Dynamically create folders for all active consoles
    for g in games:
        try:
            os.makedirs(os.path.join(COVERS_DIR, g["console"]), exist_ok=True)
        except Exception:
            pass

    for g in games:
        path = g["path"]
        console_name = g["console"].upper()
        covers_dir = os.path.join(COVERS_DIR, g["console"])

        # Try to find the emulator executable associated with this console
        emu_path = ""
        cfg = consoles.get(g["console"])
        if cfg:
            emu_path = cfg.get("emulator", "").upper()

        is_psp = any(x in console_name for x in ("PSP", "PPSSPP", "PPSSP")) or "PPSSPP" in emu_path
        is_ps2 = any(x in console_name for x in ("PS2", "PCSX2")) or "PCSX2" in emu_path
        is_ps3 = any(x in console_name for x in ("PS3", "RPCS3")) or "RPCS3" in emu_path

        # --- PSP / PS3 composite cover generation from ISO ---
        if (is_psp or is_ps3) and path.lower().endswith(".iso"):
            if _has_highres_cover(covers_dir, g["name"]):
                continue

            game_dir_name = "PSP_GAME" if is_psp else "PS3_GAME"
            label = "PSP" if is_psp else "PS3"
            try:
                icon0_data, pic1_data = extract_iso_images(path, game_dir_name)
                if not icon0_data and not pic1_data:
                    continue

                cover_surf = _build_composite_cover(icon0_data, pic1_data)
                out_path = os.path.join(covers_dir, g["name"] + ".png")
                pygame.image.save(cover_surf, out_path)
                cover_cache.pop(path, None)
                print(f"[Cover Gen] Generated high-res {label} cover for {g['name']}")
            except Exception as e:
                print(f"[Cover Gen] Failed to generate {label} cover for {g['name']}: {e}")

        # --- PS2/PCSX2 Cover Art Downloading ---
        elif is_ps2 and path.lower().endswith(".iso"):
            cover_exists = any(
                os.path.isfile(os.path.join(covers_dir, g["name"] + ext))
                for ext in (".jpg", ".jpeg", ".png")
            )
            if cover_exists:
                continue

            try:
                serial = get_ps2_serial(path)
                if not serial:
                    continue

                url = f"https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/default/{serial}.jpg"
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = response.read()
                    out_path = os.path.join(covers_dir, g["name"] + ".jpg")
                    with open(out_path, "wb") as f:
                        f.write(data)

                cover_cache.pop(path, None)
                print(f"[Cover Gen] Downloaded PS2 cover for {g['name']} ({serial})")
            except Exception as e:
                print(f"[Cover Gen] Failed to download PS2 cover for {g['name']}: {e}")
