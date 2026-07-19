"""
GAME MACHINE - Background cover art generation and downloading.
Handles PSP/PS3 ISO extraction and PS2 cover downloading.

Thread-safety: The background thread does ALL heavy lifting (ISO parsing, HTTP downloads)
and puts results onto a thread-safe queue. The main thread drains the queue each frame
and performs the pygame Surface creation / image saving. This keeps pygame calls on
the main thread where they belong.
"""
import io
import os
import queue
import urllib.request
from dataclasses import dataclass
from typing import Optional

from covers.iso_parser import extract_iso_images
from covers.ps2_serial import get_ps2_serial


@dataclass
class CoverTask:
    """Work item for background thread to process."""
    game_path: str
    game_name: str
    console_name: str
    covers_dir: str
    is_psp: bool
    is_ps2: bool
    is_ps3: bool


@dataclass
class CoverResult:
    """Result from background thread, ready for main-thread pygame processing."""
    game_path: str
    game_name: str
    console_name: str
    covers_dir: str
    icon0_data: Optional[bytes] = None
    pic1_data: Optional[bytes] = None
    ps2_serial: Optional[str] = None
    error: Optional[str] = None


_COVER_WORK_QUEUE: queue.Queue[CoverTask] = queue.Queue()
_COVER_RESULT_QUEUE: queue.Queue[CoverResult] = queue.Queue()
_COVER_THREAD_STARTED = False


def _has_highres_cover(covers_dir: str, name: str) -> bool:
    """True if a usable (>=360px wide) cover already exists for `name`."""
    for ext in (".jpg", ".jpeg", ".png"):
        cov_path = os.path.join(covers_dir, name + ext)
        if not os.path.isfile(cov_path):
            continue
        try:
            import pygame
            img_info = pygame.image.load(cov_path)
            if img_info.get_width() >= 360:
                return True
        except Exception:
            pass
    return False


def _build_composite_cover(icon0_data: bytes, pic1_data: bytes):
    """Composite a 3:4 (360x480) cover from an ISO's ICON0.PNG and PIC1.PNG.

    MUST be called from main thread only (uses pygame.Surface).
    """
    import pygame
    save_w, save_h = 360, 480
    cover_surf = pygame.Surface((save_w, save_h))
    cover_surf.fill((17, 20, 27))

    if pic1_data:
        pic_img = pygame.image.load(io.BytesIO(pic1_data))
        pic_w, pic_h = pic_img.get_size()
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


def _cover_worker():
    """Background worker: processes CoverTask items, puts CoverResult on result queue."""
    while True:
        task: CoverTask = _COVER_WORK_QUEUE.get()
        if task is None:  # Sentinel for shutdown
            break

        try:
            result = CoverResult(
                game_path=task.game_path,
                game_name=task.game_name,
                console_name=task.console_name,
                covers_dir=task.covers_dir,
            )

            if task.is_psp or task.is_ps3:
                game_dir_name = "PSP_GAME" if task.is_psp else "PS3_GAME"
                icon0_data, pic1_data = extract_iso_images(task.game_path, game_dir_name)
                if not icon0_data and not pic1_data:
                    _COVER_WORK_QUEUE.task_done()
                    continue
                result.icon0_data = icon0_data
                result.pic1_data = pic1_data

            elif task.is_ps2:
                serial = get_ps2_serial(task.game_path)
                if not serial:
                    _COVER_WORK_QUEUE.task_done()
                    continue
                result.ps2_serial = serial

            _COVER_RESULT_QUEUE.put(result)

        except Exception as e:
            _COVER_RESULT_QUEUE.put(CoverResult(
                game_path=task.game_path,
                game_name=task.game_name,
                console_name=task.console_name,
                covers_dir=task.covers_dir,
                error=str(e),
            ))
        finally:
            _COVER_WORK_QUEUE.task_done()


def start_cover_generator_thread(games, consoles=None):
    """Initialize queues and start the background worker thread once."""
    global _COVER_THREAD_STARTED
    if consoles is None:
        consoles = {}

    if _COVER_THREAD_STARTED:
        # Just enqueue new work for the already-running thread
        _enqueue_cover_tasks(games, consoles)
        return

    # Create console directories
    for g in games:
        try:
            covers_dir = os.path.join(_get_covers_dir(), g["console"])
            os.makedirs(covers_dir, exist_ok=True)
        except Exception:
            pass

    _enqueue_cover_tasks(games, consoles)

    import threading
    worker_thread = threading.Thread(target=_cover_worker, daemon=True)
    worker_thread.start()
    _COVER_THREAD_STARTED = True


def _get_covers_dir():
    """Lazy import to avoid circular dependency at module load time."""
    from core.config import get_covers_dir
    return get_covers_dir()


def _enqueue_cover_tasks(games, consoles):
    """Create and enqueue CoverTask for each game that needs a cover."""
    for g in games:
        path = g["path"]
        console_name = g["console"].upper()
        covers_dir = os.path.join(_get_covers_dir(), g["console"])

        # Skip if high-res cover already exists
        if _has_highres_cover(covers_dir, g["name"]):
            continue

        emu_path = ""
        cfg = consoles.get(g["console"])
        if cfg:
            emu_path = cfg.get("emulator", "").upper()

        is_psp = any(x in console_name for x in ("PSP", "PPSSPP", "PPSSP")) or "PPSSPP" in emu_path
        is_ps2 = any(x in console_name for x in ("PS2", "PCSX2")) or "PCSX2" in emu_path
        is_ps3 = any(x in console_name for x in ("PS3", "RPCS3")) or "RPCS3" in emu_path

        if ((is_psp or is_ps3) and path.lower().endswith(".iso")) or (is_ps2 and path.lower().endswith(".iso")):
            _COVER_WORK_QUEUE.put(CoverTask(
                game_path=path,
                game_name=g["name"],
                console_name=g["console"],
                covers_dir=covers_dir,
                is_psp=is_psp,
                is_ps2=is_ps2,
                is_ps3=is_ps3,
            ))


def process_cover_results(cover_cache):
    """Call once per frame from main thread: drain result queue, build/save covers with pygame."""
    import pygame

    while not _COVER_RESULT_QUEUE.empty():
        try:
            result: CoverResult = _COVER_RESULT_QUEUE.get_nowait()
        except queue.Empty:
            break

        if result.error:
            print(f"[Cover Gen] Failed for {result.game_name}: {result.error}")
            continue

        try:
            if result.icon0_data is not None or result.pic1_data is not None:
                # PSP / PS3 composite cover
                label = "PSP" if result.icon0_data is not None or result.pic1_data is not None else "PS3"
                cover_surf = _build_composite_cover(result.icon0_data or b"", result.pic1_data or b"")
                out_path = os.path.join(result.covers_dir, result.game_name + ".png")
                pygame.image.save(cover_surf, out_path)
                cover_cache.pop(result.game_path, None)
                print(f"[Cover Gen] Generated high-res {label} cover for {result.game_name}")

            elif result.ps2_serial:
                # PS2 cover download
                url = f"https://raw.githubusercontent.com/xlenore/ps2-covers/main/covers/default/{result.ps2_serial}.jpg"
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = response.read()
                out_path = os.path.join(result.covers_dir, result.game_name + ".jpg")
                with open(out_path, "wb") as f:
                    f.write(data)
                cover_cache.pop(result.game_path, None)
                print(f"[Cover Gen] Downloaded PS2 cover for {result.game_name} ({result.ps2_serial})")

        except Exception as e:
            print(f"[Cover Gen] Failed to save cover for {result.game_name}: {e}")