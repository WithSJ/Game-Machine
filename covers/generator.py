"""
GAME MACHINE - Background cover art generation and downloading.
Handles PSP/PS3 ISO extraction and PS2 cover downloading.
"""
import io
import os
import urllib.request

import pygame

from core.config import COVERS_DIR
from covers.iso_parser import extract_iso_images
from covers.ps2_serial import get_ps2_serial


def background_cover_generator_thread(games, colors, cover_cache):
    """
    Unified background thread that:
    1. Scans PSP/PS3/PPSSPP/RPCS3 games and extracts high-resolution 3:4 composite covers from ISOs.
    2. Scans PS2/PCSX2 games, parses their serial, and downloads cover art from GitHub.
    """
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

        # --- PSP/PPSSPP Cover Art Generation ---
        if any(x in console_name for x in ("PSP", "PPSSPP", "PPSSP")) and path.lower().endswith(".iso"):
            cover_exists = False
            for ext in (".jpg", ".jpeg", ".png"):
                cov_path = os.path.join(covers_dir, g["name"] + ext)
                if os.path.isfile(cov_path):
                    try:
                        img_info = pygame.image.load(cov_path)
                        if img_info.get_width() >= 360:
                            cover_exists = True
                            break
                    except Exception:
                        pass
                        
            if cover_exists:
                continue
                
            try:
                icon0_data, pic1_data = extract_iso_images(path, "PSP_GAME")
                if not icon0_data and not pic1_data:
                    continue
                    
                pygame.init()
                save_w, save_h = 360, 480
                cover_surf = pygame.Surface((save_w, save_h))
                cover_surf.fill((17, 20, 27))
                
                if pic1_data:
                    pic_file = io.BytesIO(pic1_data)
                    pic_img = pygame.image.load(pic_file).convert()
                    pic_w, pic_h = pic_img.get_size()
                    target_aspect = save_w / save_h
                    crop_h = pic_h
                    crop_w = int(crop_h * target_aspect)
                    crop_x = (pic_w - crop_w) // 2
                    crop_y = 0
                    
                    cropped_pic = pygame.Surface((crop_w, crop_h))
                    cropped_pic.blit(pic_img, (0, 0), (crop_x, crop_y, crop_w, crop_h))
                    
                    bg_scaled = pygame.transform.smoothscale(cropped_pic, (save_w, save_h))
                    cover_surf.blit(bg_scaled, (0, 0))
                    
                    overlay = pygame.Surface((save_w, save_h), pygame.SRCALPHA)
                    overlay.fill((10, 12, 18, 120))
                    cover_surf.blit(overlay, (0, 0))
                    
                if icon0_data:
                    icon_file = io.BytesIO(icon0_data)
                    icon_img = pygame.image.load(icon_file).convert_alpha()
                    icon_w, icon_h = icon_img.get_size()
                    new_icon_w = 300
                    new_icon_h = int(icon_h * (new_icon_w / icon_w))
                    
                    icon_scaled = pygame.transform.smoothscale(icon_img, (new_icon_w, new_icon_h))
                    icon_x = (save_w - new_icon_w) // 2
                    icon_y = (save_h - new_icon_h) // 2
                    cover_surf.blit(icon_scaled, (icon_x, icon_y))
                    
                out_path = os.path.join(covers_dir, g["name"] + ".png")
                pygame.image.save(cover_surf, out_path)
                cover_cache.pop(path, None)
                print(f"[Cover Gen] Generated high-res PSP cover for {g['name']}")
            except Exception as e:
                print(f"[Cover Gen] Failed to generate PSP cover for {g['name']}: {e}")
                
        # --- PS3/RPCS3 Cover Art Generation ---
        elif any(x in console_name for x in ("PS3", "RPCS3")) and path.lower().endswith(".iso"):
            cover_exists = False
            for ext in (".jpg", ".jpeg", ".png"):
                cov_path = os.path.join(covers_dir, g["name"] + ext)
                if os.path.isfile(cov_path):
                    try:
                        img_info = pygame.image.load(cov_path)
                        if img_info.get_width() >= 360:
                            cover_exists = True
                            break
                    except Exception:
                        pass
                        
            if cover_exists:
                continue
                
            try:
                icon0_data, pic1_data = extract_iso_images(path, "PS3_GAME")
                if not icon0_data and not pic1_data:
                    continue
                    
                pygame.init()
                save_w, save_h = 360, 480
                cover_surf = pygame.Surface((save_w, save_h))
                cover_surf.fill((17, 20, 27))
                
                if pic1_data:
                    pic_file = io.BytesIO(pic1_data)
                    pic_img = pygame.image.load(pic_file).convert()
                    pic_w, pic_h = pic_img.get_size()
                    target_aspect = save_w / save_h
                    crop_h = pic_h
                    crop_w = int(crop_h * target_aspect)
                    crop_x = (pic_w - crop_w) // 2
                    crop_y = 0
                    
                    cropped_pic = pygame.Surface((crop_w, crop_h))
                    cropped_pic.blit(pic_img, (0, 0), (crop_x, crop_y, crop_w, crop_h))
                    
                    bg_scaled = pygame.transform.smoothscale(cropped_pic, (save_w, save_h))
                    cover_surf.blit(bg_scaled, (0, 0))
                    
                    overlay = pygame.Surface((save_w, save_h), pygame.SRCALPHA)
                    overlay.fill((10, 12, 18, 120))
                    cover_surf.blit(overlay, (0, 0))
                    
                if icon0_data:
                    icon_file = io.BytesIO(icon0_data)
                    icon_img = pygame.image.load(icon_file).convert_alpha()
                    icon_w, icon_h = icon_img.get_size()
                    new_icon_w = 300
                    new_icon_h = int(icon_h * (new_icon_w / icon_w))
                    
                    icon_scaled = pygame.transform.smoothscale(icon_img, (new_icon_w, new_icon_h))
                    icon_x = (save_w - new_icon_w) // 2
                    icon_y = (save_h - new_icon_h) // 2
                    cover_surf.blit(icon_scaled, (icon_x, icon_y))
                    
                out_path = os.path.join(covers_dir, g["name"] + ".png")
                pygame.image.save(cover_surf, out_path)
                cover_cache.pop(path, None)
                print(f"[Cover Gen] Generated high-res PS3 cover for {g['name']}")
            except Exception as e:
                print(f"[Cover Gen] Failed to generate PS3 cover for {g['name']}: {e}")
                
        # --- PS2/PCSX2 Cover Art Downloading ---
        elif any(x in console_name for x in ("PS2", "PCSX2")) and path.lower().endswith(".iso"):
            cover_exists = False
            for ext in (".jpg", ".jpeg", ".png"):
                if os.path.isfile(os.path.join(covers_dir, g["name"] + ext)):
                    cover_exists = True
                    break
                    
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
