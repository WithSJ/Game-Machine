"""
GAME MACHINE - Main App Orchestrator and GameMachine Class.
"""
import math
import os
import random
import sys
import time
import threading
import pygame
import pygame.gfxdraw

# Initialize pygame and detect native desktop resolution before other UI modules are imported
pygame.init()
pygame.joystick.init()
info = pygame.display.Info()

# Import theme and dynamically override resolution-dependent coordinates
import ui.theme
ui.theme.SCREEN_W = info.current_w
ui.theme.SCREEN_H = info.current_h
ui.theme.HERO_RECT = pygame.Rect(ui.theme.PAD_X, 122, int(ui.theme.SCREEN_W - 2 * ui.theme.PAD_X), 172)
ui.theme.FOOTER_Y = ui.theme.SCREEN_H - 52
grid_height = ui.theme.FOOTER_Y - 310 - 6
ui.theme.GRID_RECT = pygame.Rect(ui.theme.PAD_X, 310, int(ui.theme.SCREEN_W - 2 * ui.theme.PAD_X), int(grid_height))

# Now import modules that depend on theme constants
from core.scanner import discover_consoles, scan_games
from core.playdata import load_playdata, save_playdata, fmt_dur, fmt_last
from core.launcher import launch_game
from core.savestates import find_latest_save_state
from core.autostart import is_auto_start_enabled, set_auto_start

from covers.generator import start_cover_generator_thread, process_cover_results

from ui.theme import (
    COL_BG, COL_TEXT, COL_DIM, COL_DIMMER, COL_PANEL2, COL_CARD_BORDER,
    REC_COLOR, build_console_colors, ease_out, SCREEN_W, SCREEN_H,
    GRID_RECT, HERO_RECT, FOOTER_Y, NAV_REPEAT_DELAY, NAV_REPEAT_RATE,
    TAB_ANIM_MS, TOAST_MS
)
from ui.draw_splash import draw_splash
from ui.draw_header import draw_header
from ui.draw_tabs import draw_tabs
from ui.draw_hero import draw_hero
from ui.draw_grid import draw_grid
from ui.draw_footer import draw_footer
from ui.draw_toast import draw_toast
from ui.draw_popup import draw_popup
from ui.draw_exit_menu import draw_exit_menu
from ui.draw_setup import draw_setup
from ui.draw_settings import draw_settings, TABS as SETTINGS_TABS
from ui.cache import (
    build_bg, build_gridlines, get_hero_bg, get_ghost_text,
    get_cover_for, get_placeholder
)

from input.keyboard import handle_keyboard
from input.gamepad import (
    handle_gamepad_buttons, handle_gamepad_connect,
    handle_gamepad_disconnect, update_gamepad_axes
)
from input.mouse import handle_mouse_motion, handle_mouse_click, handle_mouse_wheel
from input.touch import handle_touch_down, handle_touch_motion, handle_touch_up


class GameMachine:
    def __init__(self):
        pygame.key.set_repeat(NAV_REPEAT_DELAY, NAV_REPEAT_RATE)

        self.fullscreen = True
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
        pygame.display.set_caption("GAME MACHINE")
        self.clock = pygame.time.Clock()

        # ---- Show splash screen IMMEDIATELY so boot feels instant ----
        self._draw_splash("Starting...")
        pygame.display.flip()

        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        # Fonts
        self._draw_splash("Loading fonts...")
        pygame.display.flip()

        def FH(size, bold=False):
            return pygame.font.SysFont("bahnschrift,verdana,arial", size, bold=bold)

        def FB(size, bold=False):
            return pygame.font.SysFont("verdana,arial", size, bold=bold)

        self.f_logo = FH(24, True)
        self.f_sub = FB(11)
        self.f_clock = FH(17, True)
        self.f_tab = FH(16, True)
        self.f_channel = FH(13, True)
        self.f_hero = FH(38, True)
        self.f_meta = FB(14)
        self.f_btn = FH(15, True)
        self.f_card = FB(13, True)
        self.f_chip = FB(10, True)
        self.f_small = FB(12)
        self.f_hint = FB(12)
        self.f_ghost = FH(120, True)
        self.f_mono = pygame.font.SysFont("consolas,couriernew,monospace", 11)
        self.f_popup_title = FH(22, True)
        self.f_popup_name = FH(18, True)
        self.f_popup_btn = FH(15, True)

        # Data - scan games and load playtime
        self.playdata = load_playdata()
        self.settings = self.playdata.setdefault("__settings__", {"size": "medium"})
        self.folders = self.settings.setdefault("folders", [])
        self.custom_consoles = self.settings.setdefault("custom_consoles", {})
        self.update_sizes()

        # Check if setup is needed
        self.needs_setup = not self.folders and not self.custom_consoles

        if self.needs_setup:
            self._draw_splash("Starting Setup...")
            pygame.display.flip()
            self.consoles = {}
            self.colors = build_console_colors(self.consoles)
            self.games = []
            self.tabs = [("RECENTS", REC_COLOR)]
            
            # Setup screen navigation states
            self.setup_sel = 0
            self.setup_help_active = False
            self.setup_delete_rects = []
            self.setup_menu_rects = []
        else:
            self._draw_splash("Scanning games...")
            pygame.display.flip()
            self.consoles = discover_consoles(self.folders, self.custom_consoles)
            self.colors = build_console_colors(self.consoles)
            self.games = scan_games(self.consoles)
            
            present = [c for c in self.consoles if any(g["console"] == c for g in self.games)]
            self.tabs = [("RECENTS", REC_COLOR)] + [(c, self.colors[c]) for c in present]

        # UI state
        self.tab = 0 if self._recents() else (1 if len(self.tabs) > 1 else 0)
        self.sel = 0
        self.scroll = 0.0
        self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()
        self.toast = None
        self.toast_until = 0
        self.running = True

        # Header focus: -1 = not focused, 0 = SIZE button, 1 = EXIT button
        self.header_focus = -1

        # Confirmation popup state
        self.popup_active = False
        self.popup_game = None
        self.popup_sel = 0          # 0 = YES (or LOAD STATE), 1 = NO (or JUST PLAY), 2 = CANCEL
        self.popup_anim_start = 0
        self.popup_yes_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_no_rect = pygame.Rect(0, 0, 0, 0)
        self.popup_option_rects = []   # 3-option menu: list of (idx, action, rect)
        self.popup_save_state = None   # path to the latest save state (when popup_type == "launch_menu")
        self.popup_type = "launch"     # "launch", "decrypt", or "launch_menu"
        self.decrypting_active = False
        self.decryption_status = ""
        self.decryption_error = None
        self.decryption_done = threading.Event()
        self.decryption_close_rect = pygame.Rect(0, 0, 0, 0)

        # Exit / Power menu state
        self.exit_menu_active = False
        self.exit_menu_sel = 0
        self.exit_menu_anim_start = 0
        self.exit_menu_option_rects = []
        self.exit_menu_autostart_rect = pygame.Rect(0, 0, 0, 0)
        self.exit_menu_close_rect = pygame.Rect(0, 0, 0, 0)
        self.auto_start = is_auto_start_enabled()

        # Settings panel state
        self.settings_active = False
        self.settings_tab = 0
        self.settings_sel = 0
        self.settings_anim_start = 0
        self.settings_tab_rects = []
        self.settings_option_rects = []
        self.settings_close_rect = pygame.Rect(0, 0, 0, 0)

        # Handle restart flag cleanup on boot
        restart_flag = self.playdata.pop("__restart_pending__", False)
        if restart_flag:
            save_playdata(self.playdata)
            # If auto-start is off, remove the registry entry that was added for restart
            if not self.settings.get("auto_start", False):
                set_auto_start(False)
                self.auto_start = False

        # Gamepad hold-to-repeat state (x and y tracked separately)
        self.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}

        # Touch state
        self.touch_id = None
        self.touch_start = None
        self.touch_last_y = 0.0
        self.touch_moved = False

        # Hit-test rects
        self.tab_rects = []
        self.card_rects = []
        self.play_rect = None
        self.details_rect = None
        self.exit_rect = pygame.Rect(0, 0, 0, 0)

        # Build render caches
        self._draw_splash("Building UI...")
        pygame.display.flip()

        self._bg = build_bg()
        self._gridlines = build_gridlines()
        self._hero_cache = {}
        self._ghost_cache = {}
        self._cover_cache = {}
        self._placeholder_cache = {}

        # Ambient particles
        self.particles = [{
            "x": random.uniform(0, SCREEN_W), "y": random.uniform(0, SCREEN_H),
            "s": random.uniform(0.6, 2.6), "v": random.uniform(0.1, 0.45),
            "ph": random.uniform(0, math.tau),
        } for _ in range(90)]
        self._overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)

        # Start background thread to extract PSP & PS2 cover arts only if setup is not needed
        if not self.needs_setup:
            start_cover_generator_thread(self.games, self.consoles)

    def _draw_splash(self, status_text="Loading..."):
        draw_splash(self.screen, status_text)

    def update_sizes(self):
        size = self.settings.get("size", "medium")
        if size == "small":
            self.cols = 12
        elif size == "large":
            self.cols = 5
        else: # medium
            self.cols = 8
            
        self.gap = 14
        self.card_w = ((GRID_RECT.w + self.gap) // self.cols) - self.gap
        self.cover_h = int(self.card_w * 4 // 3)
        self.card_h = self.cover_h + 90
        
        ui.theme.COLS = self.cols
        
        # Clear cover cache so everything gets reloaded at the new resolution
        if hasattr(self, "_cover_cache"):
            self._cover_cache.clear()
        if hasattr(self, "_placeholder_cache"):
            self._placeholder_cache.clear()
            
        self.ensure = True

    # ---------------- data helpers ----------------
    def _recents(self):
        def _last(g):
            rec = self.playdata.get(g["path"])
            if isinstance(rec, dict):
                val = rec.get("last")
                return val if isinstance(val, (int, float)) else 0
            return 0
        played = [g for g in self.games if _last(g)]
        played.sort(key=lambda g: -_last(g))
        return played[:16]

    def current_list(self):
        name = self.tabs[self.tab][0]
        if name == "RECENTS":
            return self._recents()
        return [g for g in self.games if g["console"] == name]

    def accent(self):
        return self.tabs[self.tab][1]

    def game_stats(self, game):
        rec = self.playdata.get(game["path"])
        if rec and rec.get("last"):
            return rec
        return None

    # ---------------- actions ----------------
    def pop(self, msg):
        self.toast = msg
        self.toast_until = pygame.time.get_ticks() + TOAST_MS

    def set_tab(self, i):
        n = i % len(self.tabs)
        if n == self.tab:
            return
        self.tab = n
        self.sel = 0
        self.scroll = self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()

    def move_sel(self, dx, dy):
        L = self.current_list()

        # If header is focused, handle navigation within header (3 buttons)
        if self.header_focus >= 0:
            if dx != 0:
                self.header_focus = max(0, min(2, self.header_focus + dx))
            if dy > 0:
                self.header_focus = -1
            return

        # Empty list: only UP does something (jumps to header).
        # Without this, an empty RECENTS tab traps the user - they can't
        # reach the SIZE/EXIT buttons via gamepad.
        if not L:
            if dy < 0:
                self.header_focus = 0  # focus SIZE button first
            return

        # Check if pressing UP from the top row -> go to header
        if dy < 0 and self.sel < self.cols:
            self.header_focus = 0  # focus SIZE button first
            return

        new = self.sel + dx + dy * self.cols
        self.sel = max(0, min(new, len(L) - 1))
        self.ensure = True

    def random_pick(self):
        L = self.current_list()
        if not L:
            return
        self.sel = random.randrange(len(L))
        self.ensure = True
        self.pop("Random pick: " + L[self.sel]["name"])

    def show_details(self):
        L = self.current_list()
        if not L:
            return
        g = L[min(self.sel, len(L) - 1)]
        rec = self.game_stats(g)
        if rec:
            self.pop(f"{g['name']} · {g['console']} · {fmt_dur(rec['seconds'])} played")
        else:
            self.pop(f"{g['name']} · {g['console']} · not played yet")

    def launch_selected(self):
        L = self.current_list()
        if not L:
            return
        game = L[min(self.sel, len(L) - 1)]
        self.popup_active = True
        self.popup_game = game
        self.popup_sel = 0  # default to the first (primary) action
        self.popup_anim_start = pygame.time.get_ticks()
        self.popup_option_rects = []
        self.popup_save_state = None

        # First-time encrypted PS3 games still get the decrypt prompt.
        if game["console"] == "PS3" and self.game_stats(game) is None:
            self.popup_type = "decrypt"
            return

        # Otherwise look for an existing save state. If found, show the 3-option
        # launch menu; if not, fall back to the 2-option YES/NO popup.
        state_path = find_latest_save_state(game, self.consoles)
        if state_path and os.path.isfile(state_path):
            self.popup_type = "launch_menu"
            self.popup_save_state = state_path
        else:
            self.popup_type = "launch"

    def _start_decryption(self):
        game = self.popup_game
        self.popup_active = False  # Close the prompt popup
        self.decrypting_active = True
        self.decryption_status = "Initializing..."
        self.decryption_error = None
        self.decryption_done.clear()
        
        import threading
        from core.decrypter import run_decryption_thread
        self.decryption_thread = threading.Thread(
            target=run_decryption_thread,
            args=(self, game),
            daemon=True
        )
        self.decryption_thread.start()

    def _popup_activate(self):
        """Take the currently-selected option in the launch popup and act on it."""
        if self.popup_type == "launch_menu":
            # 0 = LOAD LAST SAVE STATE, 1 = JUST PLAY, 2 = CANCEL
            if self.popup_sel == 0:
                self._confirm_launch(load_state=self.popup_save_state)
            elif self.popup_sel == 1:
                self._confirm_launch(load_state=None)
            else:
                self._cancel_popup()
        else:
            # 2-option popup (launch / decrypt): YES -> start, NO -> cancel
            if self.popup_sel == 0:
                if self.popup_type == "decrypt":
                    self._start_decryption()
                else:
                    self._confirm_launch()
            else:
                self._cancel_popup()

    def _confirm_launch(self, load_state=None):
        game = self.popup_game
        self.popup_active = False
        self.popup_game = None
        self.popup_save_state = None
        self.popup_option_rects = []
        if game is None:
            return
        try:
            elapsed = launch_game(game, self.consoles, load_state=load_state)
        except Exception as e:
            self.pop(f"Launch failed: {e}")
            return
        rec = self.playdata.setdefault(game["path"], {"seconds": 0, "last": 0})
        rec["seconds"] += elapsed
        rec["last"] = int(time.time())
        save_playdata(self.playdata)
        self._reinit_joystick()
        if load_state:
            self.pop(f"Welcome back \u00b7 {fmt_dur(elapsed)} session (loaded save state)")
        else:
            self.pop(f"Welcome back \u00b7 {fmt_dur(elapsed)} session")
        self.ignore_input_until = pygame.time.get_ticks() + 1000

    def _reinit_joystick(self):
        """Re-acquire the gamepad after an emulator exits.

        Emulators grab exclusive HID ownership of the controller during
        fullscreen. When they release it on exit, Pygame's cached joystick
        object goes stale and stops reporting input, so we rebuild it here.
        """
        pygame.joystick.quit()
        pygame.joystick.init()
        try:
            if pygame.joystick.get_count() > 0:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
            else:
                self.joystick = None
        except KeyError:
            # pygame bug: internal joystick mapping corrupted
            self.joystick = None
        self.pad_state = {"x": {"dir": 0, "next": 0}, "y": {"dir": 0, "next": 0}}

    def _cancel_popup(self):
        self.popup_active = False
        self.popup_game = None
        self.popup_save_state = None
        self.popup_option_rects = []

    def _show_exit_menu(self):
        if self.exit_menu_active:
            return
        self.settings_active = False  # Close settings if open
        self.exit_menu_active = True
        self.exit_menu_sel = 0
        self.exit_menu_anim_start = pygame.time.get_ticks()

    def _close_exit_menu(self):
        self.exit_menu_active = False

    # ---------------- settings panel ----------------
    def _show_settings(self):
        if self.settings_active:
            return
        self.exit_menu_active = False  # Close exit menu if open
        self.settings_active = True
        self.settings_tab = 0
        self.settings_sel = 0
        self.settings_anim_start = pygame.time.get_ticks()
        self.header_focus = -1

    def _close_settings(self):
        self.settings_active = False

    def _settings_switch_tab(self, delta):
        n = len(SETTINGS_TABS)
        self.settings_tab = (self.settings_tab + delta) % n
        self.settings_sel = 0

    def _settings_activate(self):
        if not self.settings_option_rects:
            return
        if self.settings_sel >= len(self.settings_option_rects):
            return
        action, _ = self.settings_option_rects[self.settings_sel]
        self._settings_execute(action)

    def _settings_execute(self, action):
        if action == "add_folder":
            self._settings_add_folder()
        elif action == "add_console":
            self._settings_add_console()
        elif action == "change_emulators_folder":
            self._settings_change_emulators_folder()
        elif action.startswith("delete_folder:"):
            idx = int(action.split(":")[1])
            if 0 <= idx < len(self.folders):
                removed = self.folders.pop(idx)
                self._settings_rescan()
                self.pop(f"Removed: {os.path.basename(removed)}")
        elif action.startswith("delete_console:"):
            name = action.split(":", 1)[1]
            if name in self.custom_consoles:
                del self.custom_consoles[name]
                self._settings_rescan()
                self.pop(f"Removed: {name}")
        elif action == "cycle_grid_size":
            self._activate_header_size()
        elif action == "toggle_fullscreen":
            self.toggle_fullscreen()
        elif action == "toggle_auto_start":
            self._toggle_auto_start()
        elif action == "lock_screen":
            self._close_settings()
            try:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            except Exception as e:
                self.pop(f"Lock failed: {e}")
        elif action == "restart":
            self.playdata["__restart_pending__"] = True
            save_playdata(self.playdata)
            set_auto_start(True)
            pygame.quit()
            os.system("shutdown /r /t 3 /c \"Game Machine: Restarting...\"")
            sys.exit(0)
        elif action == "shutdown":
            pygame.quit()
            os.system("shutdown /s /t 3 /c \"Game Machine: Shutting down...\"")
            sys.exit(0)
        elif action == "exit_gm":
            self.running = False

    def _settings_change_emulators_folder(self):
        from ui.draw_setup import add_emulators_folder_dialog
        add_emulators_folder_dialog(self)
        self._settings_rescan()
        self.settings_sel = 0

    def _settings_rescan(self):
        """Re-save settings, refresh config paths, and re-scan games."""
        self.settings["folders"] = self.folders
        self.settings["custom_consoles"] = self.custom_consoles
        save_playdata(self.playdata)

        from core.config import refresh_paths
        refresh_paths()

        self.consoles = discover_consoles(self.folders, self.custom_consoles)
        self.colors = build_console_colors(self.consoles)
        self.games = scan_games(self.consoles)

        present = [c for c in self.consoles if any(g["console"] == c for g in self.games)]
        self.tabs = [("RECENTS", REC_COLOR)] + [(c, self.colors[c]) for c in present]

        if self.tab >= len(self.tabs):
            self.tab = max(0, len(self.tabs) - 1)
        self.sel = 0
        self.scroll = 0.0
        self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()

        if self.games:
            start_cover_generator_thread(self.games, self.consoles)

    def _settings_add_folder(self):
        from ui.draw_setup import add_gm_folder_dialog
        add_gm_folder_dialog(self)
        self._settings_rescan()
        self.settings_sel = 0

    def _settings_add_console(self):
        from ui.draw_setup import add_custom_console_dialog
        add_custom_console_dialog(self)
        self._settings_rescan()
        self.settings_sel = 0

    def _exit_menu_confirm(self):
        sel = self.exit_menu_sel
        if sel == 0:    # Exit Game Machine
            self.running = False
        elif sel == 1:  # Lock Screen
            self._close_exit_menu()
            try:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            except Exception as e:
                self.pop(f"Lock failed: {e}")
        elif sel == 2:  # Restart
            self.playdata["__restart_pending__"] = True
            save_playdata(self.playdata)
            set_auto_start(True)
            pygame.quit()
            os.system("shutdown /r /t 3 /c \"Game Machine: Restarting...\"")
            sys.exit(0)
        elif sel == 3:  # Shutdown
            pygame.quit()
            os.system("shutdown /s /t 3 /c \"Game Machine: Shutting down...\"")
            sys.exit(0)

    def _toggle_auto_start(self):
        self.auto_start = not self.auto_start
        set_auto_start(self.auto_start)
        self.settings["auto_start"] = self.auto_start
        save_playdata(self.playdata)
        self.pop(f"Auto-Start: {'ON' if self.auto_start else 'OFF'}")

    def _activate_header_size(self):
        current = self.settings.get("size", "medium")
        if current == "small":
            new_size = "medium"
        elif current == "medium":
            new_size = "large"
        else:
            new_size = "small"
        self.settings["size"] = new_size
        save_playdata(self.playdata)
        self.update_sizes()
        self.pop(f"Grid size: {new_size.upper()}")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)

    def click(self, pos):
        """Shared mouse-click / touch-tap handler."""
        if self.exit_rect.collidepoint(pos):
            self._show_exit_menu()
            return
        if hasattr(self, "size_rect") and self.size_rect.collidepoint(pos):
            self._activate_header_size()
            return
        if hasattr(self, "settings_rect") and self.settings_rect.collidepoint(pos):
            self._show_settings()
            return
        for i, r in self.tab_rects:
            if r.collidepoint(pos):
                self.set_tab(i)
                return
        if self.play_rect and self.play_rect.collidepoint(pos):
            self.launch_selected()
            return
        if self.details_rect and self.details_rect.collidepoint(pos):
            self.show_details()
            return
        for i, r in self.card_rects:
            if r.collidepoint(pos):
                if i == self.sel:
                    self.launch_selected()
                else:
                    self.sel = i
                return

    # ---------------- UI helpers ----------------
    def _hero_bg(self, accent):
        return get_hero_bg(self, accent)

    def _ghost_text(self, text, accent):
        return get_ghost_text(self, text, accent)

    def _cover_for(self, game):
        return get_cover_for(self, game)

    def _placeholder(self, accent, active):
        return get_placeholder(self, accent, active)

    # ---------------- input ----------------
    def handle_event(self, e):
        # Always honor QUIT (Alt-F4 / window close), even during the
        # post-launch input freeze - otherwise the user can't exit.
        if e.type == pygame.QUIT:
            if getattr(self, "needs_setup", False):
                pygame.quit()
                sys.exit()
            self._show_exit_menu()
            return

        if pygame.time.get_ticks() < getattr(self, "ignore_input_until", 0):
            return

        if getattr(self, "needs_setup", False):
            self.handle_setup_event(e)
            return

        # ---- Decryption progress input handling ----
        if getattr(self, "decrypting_active", False):
            if self.decryption_error:
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                        self.decrypting_active = False
                        self.decryption_error = None
                        self.popup_game = None
                elif e.type == pygame.JOYBUTTONDOWN:
                    if e.button in (0, 1): # A or B
                        self.decrypting_active = False
                        self.decryption_error = None
                        self.popup_game = None
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if not getattr(e, "touch", False):
                        if getattr(self, "decryption_close_rect", pygame.Rect(0,0,0,0)).collidepoint(e.pos):
                            self.decrypting_active = False
                            self.decryption_error = None
                            self.popup_game = None
                elif e.type == pygame.FINGERUP:
                    if self.touch_start is not None and not getattr(self, 'touch_moved', False):
                        w, h = self.screen.get_size()
                        pos = (e.x * w, e.y * h)
                        if getattr(self, "decryption_close_rect", pygame.Rect(0,0,0,0)).collidepoint(pos):
                            self.decrypting_active = False
                            self.decryption_error = None
                            self.popup_game = None
            return

        # ---- Popup input handling ----
        if self.popup_active:
            n_opts = 3 if getattr(self, "popup_type", "launch") == "launch_menu" else 2
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._popup_activate()
                elif e.key == pygame.K_ESCAPE:
                    self._cancel_popup()
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.popup_sel = (self.popup_sel - 1) % n_opts
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.popup_sel = (self.popup_sel + 1) % n_opts
                elif e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    # For 2-option popups keep horizontal toggle; for 3-option
                    # treat left/right as up/down so a d-pad in any direction works.
                    if n_opts == 2:
                        self.popup_sel = 1 - self.popup_sel
                    else:
                        self.popup_sel = (self.popup_sel + (1 if e.key == pygame.K_RIGHT else -1)) % n_opts
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:
                    self._popup_activate()
                elif e.button == 1:
                    self._cancel_popup()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if not getattr(e, "touch", False):
                    if n_opts == 3 and self.popup_option_rects:
                        for idx, action, r in self.popup_option_rects:
                            if r.collidepoint(e.pos):
                                self.popup_sel = idx
                                self._popup_activate()
                                break
                    else:
                        if self.popup_yes_rect.collidepoint(e.pos):
                            self.popup_sel = 0
                            self._popup_activate()
                        elif self.popup_no_rect.collidepoint(e.pos):
                            self.popup_sel = 1
                            self._popup_activate()
            elif e.type == pygame.FINGERUP:
                if self.touch_start is not None and not getattr(self, 'touch_moved', False):
                    w, h = self.screen.get_size()
                    pos = (e.x * w, e.y * h)
                    if n_opts == 3 and self.popup_option_rects:
                        for idx, action, r in self.popup_option_rects:
                            if r.collidepoint(pos):
                                self.popup_sel = idx
                                self._popup_activate()
                                break
                    else:
                        if self.popup_yes_rect.collidepoint(pos):
                            self.popup_sel = 0
                            self._popup_activate()
                        elif self.popup_no_rect.collidepoint(pos):
                            self.popup_sel = 1
                            self._popup_activate()
            return

        # ---- Exit menu input handling ----
        if self.exit_menu_active:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self._close_exit_menu()
                elif e.key in (pygame.K_UP,):
                    self.exit_menu_sel = (self.exit_menu_sel - 1) % 4
                elif e.key in (pygame.K_DOWN,):
                    self.exit_menu_sel = (self.exit_menu_sel + 1) % 4
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._exit_menu_confirm()
                elif e.key == pygame.K_y:
                    self._toggle_auto_start()
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:
                    self._exit_menu_confirm()
                elif e.button == 1:
                    self._close_exit_menu()
                elif e.button == 3:
                    self._toggle_auto_start()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if not getattr(e, "touch", False):
                    # [X] close button dismisses the power menu
                    if self.exit_menu_close_rect.collidepoint(e.pos):
                        self._close_exit_menu()
                        return
                    for idx, rect in self.exit_menu_option_rects:
                        if rect.collidepoint(e.pos):
                            self.exit_menu_sel = idx
                            self._exit_menu_confirm()
                            return
                    if self.exit_menu_autostart_rect.collidepoint(e.pos):
                        self._toggle_auto_start()
            elif e.type == pygame.FINGERUP:
                if self.touch_start is not None and not getattr(self, 'touch_moved', False):
                    w, h = self.screen.get_size()
                    pos = (e.x * w, e.y * h)
                    # [X] close button dismisses the power menu
                    if self.exit_menu_close_rect.collidepoint(pos):
                        self._close_exit_menu()
                        return
                    for idx, rect in self.exit_menu_option_rects:
                        if rect.collidepoint(pos):
                            self.exit_menu_sel = idx
                            self._exit_menu_confirm()
                            return
                    if self.exit_menu_autostart_rect.collidepoint(pos):
                        self._toggle_auto_start()
            return

        # ---- Settings panel input handling ----
        if getattr(self, "settings_active", False):
            n_tabs = len(SETTINGS_TABS)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self._close_settings()
                elif e.key in (pygame.K_UP, pygame.K_w):
                    if self.settings_option_rects:
                        self.settings_sel = (self.settings_sel - 1) % len(self.settings_option_rects)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    if self.settings_option_rects:
                        self.settings_sel = (self.settings_sel + 1) % len(self.settings_option_rects)
                elif e.key in (pygame.K_LEFT, pygame.K_q):
                    self._settings_switch_tab(-1)
                elif e.key in (pygame.K_RIGHT, pygame.K_e):
                    self._settings_switch_tab(1)
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._settings_activate()
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:    # A = confirm
                    self._settings_activate()
                elif e.button == 1:  # B = close
                    self._close_settings()
                elif e.button == 4:  # L1 = prev tab
                    self._settings_switch_tab(-1)
                elif e.button == 5:  # R1 = next tab
                    self._settings_switch_tab(1)
            elif e.type == pygame.MOUSEMOTION:
                if not getattr(e, "touch", False):
                    for idx, (action, rect) in enumerate(self.settings_option_rects):
                        if rect.collidepoint(e.pos):
                            self.settings_sel = idx
                            break
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if not getattr(e, "touch", False):
                    if self.settings_close_rect.collidepoint(e.pos):
                        self._close_settings()
                        return
                    for idx, rect in self.settings_tab_rects:
                        if rect.collidepoint(e.pos):
                            self.settings_tab = idx
                            self.settings_sel = 0
                            return
                    for idx, (action, rect) in enumerate(self.settings_option_rects):
                        if rect.collidepoint(e.pos):
                            self.settings_sel = idx
                            self._settings_execute(action)
                            return
            elif e.type == pygame.FINGERUP:
                if self.touch_start is not None and not getattr(self, 'touch_moved', False):
                    w, h = self.screen.get_size()
                    pos = (e.x * w, e.y * h)
                    if self.settings_close_rect.collidepoint(pos):
                        self._close_settings()
                        return
                    for idx, rect in self.settings_tab_rects:
                        if rect.collidepoint(pos):
                            self.settings_tab = idx
                            self.settings_sel = 0
                            return
                    for idx, (action, rect) in enumerate(self.settings_option_rects):
                        if rect.collidepoint(pos):
                            self.settings_sel = idx
                            self._settings_execute(action)
                            return
            return

        # ----- Normal input handling -----
        if e.type == pygame.KEYDOWN:
            handle_keyboard(self, e)
        elif e.type == pygame.JOYBUTTONDOWN:
            handle_gamepad_buttons(self, e)
        elif e.type == pygame.JOYDEVICEADDED:
            handle_gamepad_connect(self, e)
        elif e.type == pygame.JOYDEVICEREMOVED:
            handle_gamepad_disconnect(self, e)
        elif e.type == pygame.MOUSEMOTION:
            handle_mouse_motion(self, e)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            handle_mouse_click(self, e)
        elif e.type == pygame.MOUSEWHEEL:
            handle_mouse_wheel(self, e)
        elif e.type == pygame.FINGERDOWN:
            handle_touch_down(self, e)
        elif e.type == pygame.FINGERMOTION:
            handle_touch_motion(self, e)
        elif e.type == pygame.FINGERUP:
            handle_touch_up(self, e)

    def update_gamepad(self, now):
        update_gamepad_axes(self, now)

    def update_scroll(self):
        L = self.current_list()
        if L:
            self.sel = min(self.sel, len(L) - 1)
        rows = (len(L) + self.cols - 1) // self.cols
        max_scroll = max(0, rows * (self.card_h + self.gap) - self.gap - GRID_RECT.h)

        if self.ensure and L:
            row_top = (self.sel // self.cols) * (self.card_h + self.gap)
            row_bot = row_top + self.card_h
            if row_top < self.scroll_t:
                self.scroll_t = row_top
            elif row_bot > self.scroll_t + GRID_RECT.h:
                self.scroll_t = row_bot - GRID_RECT.h
        self.ensure = False

        self.scroll_t = max(0.0, min(self.scroll_t, float(max_scroll)))
        self.scroll += (self.scroll_t - self.scroll) * 0.35
        if abs(self.scroll - self.scroll_t) < 0.5:
            self.scroll = self.scroll_t

    # ---------------- drawing ----------------
    def draw(self, now):
        if getattr(self, "needs_setup", False):
            # Check if auto-setup is waiting for user input (update prompt).
            # This takes priority over the progress screen because the thread
            # is still "active" while it waits for a YES/NO answer.
            if getattr(self, "auto_setup", None) and self.auto_setup.awaiting_user_input:
                from ui.draw_setup import draw_update_prompt
                draw_update_prompt(self, now)
            # Check if auto-setup is running
            elif getattr(self, "auto_setup", None) and self.auto_setup.active:
                from ui.draw_setup import draw_auto_setup_progress
                draw_auto_setup_progress(self, now)
            elif getattr(self, "auto_setup", None) and self.auto_setup.finished:
                if self.auto_setup.success:
                    from ui.draw_setup import draw_setup_complete
                    draw_setup_complete(self, now)
                else:
                    from ui.draw_setup import draw_setup_error
                    draw_setup_error(self, now)
            else:
                from ui.draw_setup import draw_setup
                draw_setup(self, now)
            draw_toast(self, now)
            return

        gm_list = self.current_list()
        sel = min(self.sel, len(gm_list) - 1) if gm_list else 0
        cur = gm_list[sel] if gm_list else None
        accent = self.colors.get(cur["console"], self.accent()) if cur else self.accent()

        p = max(0.0, min(1.0, (now - self.switch_ms) / TAB_ANIM_MS))
        anim_off = int(26 * (1 - ease_out(p)))

        self.tab_rects = []
        self.card_rects = []
        self.play_rect = None
        self.details_rect = None

        self.screen.blit(self._bg, (0, 0))
        self.screen.blit(self._gridlines, (0, 0))

        # Particles
        self._overlay.fill((0, 0, 0, 0))
        tab_col = self.accent()
        for pt in self.particles:
            pt["y"] -= pt["v"]
            if pt["y"] < -4:
                pt["y"] = SCREEN_H + 4
                pt["x"] = random.uniform(0, SCREEN_W)
            tw = 0.25 + 0.35 * abs(math.sin(now / 1400 + pt["ph"]))
            pygame.draw.circle(self._overlay, tab_col + (int(tw * 255),),
                               (int(pt["x"]), int(pt["y"])), pt["s"])
        self.screen.blit(self._overlay, (0, 0))

        # Draw components
        draw_header(self, now)
        draw_tabs(self, now)
        draw_hero(self, now, anim_off)
        draw_grid(self, now, anim_off)
        draw_footer(self, now)
        draw_toast(self, now)
        draw_popup(self, now)
        draw_exit_menu(self, now)
        draw_settings(self, now)

    def handle_setup_event(self, e):
        # If auto-setup is waiting for user input (update prompt), handle it
        # FIRST. The thread is still "active" while waiting, so this must be
        # checked before the "active -> ESC only" block below.
        if getattr(self, "auto_setup", None) and self.auto_setup.awaiting_user_input:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_y):
                    self.auto_setup.user_response = True
                    self.auto_setup.awaiting_user_input = False
                elif e.key in (pygame.K_ESCAPE, pygame.K_n):
                    self.auto_setup.user_response = False
                    self.auto_setup.awaiting_user_input = False
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:  # A = Yes
                    self.auto_setup.user_response = True
                    self.auto_setup.awaiting_user_input = False
                elif e.button == 1:  # B = No
                    self.auto_setup.user_response = False
                    self.auto_setup.awaiting_user_input = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hasattr(self, 'update_yes_rect') and self.update_yes_rect.collidepoint(e.pos):
                    self.auto_setup.user_response = True
                    self.auto_setup.awaiting_user_input = False
                elif hasattr(self, 'update_no_rect') and self.update_no_rect.collidepoint(e.pos):
                    self.auto_setup.user_response = False
                    self.auto_setup.awaiting_user_input = False
            return

        # If auto-setup is running (and not awaiting input), only allow ESC to cancel
        if getattr(self, "auto_setup", None) and self.auto_setup.active:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.auto_setup = None  # Cancel setup
            return

        # If auto-setup finished with error, handle retry/exit
        if getattr(self, "auto_setup", None) and self.auto_setup.finished and not self.auto_setup.success:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_r):
                    self._start_auto_setup()  # Retry
                elif e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            elif e.type == pygame.JOYBUTTONDOWN:
                if e.button == 0:  # A = Retry
                    self._start_auto_setup()
                elif e.button == 1:  # B = Exit
                    pygame.quit()
                    sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hasattr(self, 'setup_retry_rect') and self.setup_retry_rect.collidepoint(e.pos):
                    self._start_auto_setup()
                elif hasattr(self, 'setup_exit_rect') and self.setup_exit_rect.collidepoint(e.pos):
                    pygame.quit()
                    sys.exit()
            return

        # If auto-setup finished successfully, any key continues
        if getattr(self, "auto_setup", None) and self.auto_setup.finished and self.auto_setup.success:
            if e.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERUP):
                self.needs_setup = False
                self.auto_setup = None
            return

# Normal setup screen (2 buttons: Setup Game Machine, Exit)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.setup_sel = (self.setup_sel - 1) % 2
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.setup_sel = (self.setup_sel + 1) % 2
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._setup_confirm_action()
            elif e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif e.type == pygame.JOYBUTTONDOWN:
            if e.button in (11, 12):  # D-pad up/down
                pass  # handled by axis
            elif e.button == 0:  # A = Confirm
                self._setup_confirm_action()
            elif e.button == 1:  # B = Exit
                pygame.quit()
                sys.exit()

        elif e.type == pygame.MOUSEMOTION:
            # Check hover for both buttons
            if hasattr(self, 'setup_btn_rect') and self.setup_btn_rect.collidepoint(e.pos):
                self.setup_sel = 0
            elif hasattr(self, 'exit_btn_rect') and self.exit_btn_rect.collidepoint(e.pos):
                self.setup_sel = 1

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if hasattr(self, 'setup_btn_rect') and self.setup_btn_rect.collidepoint(e.pos):
                self.setup_sel = 0
                self._setup_confirm_action()
                return
            elif hasattr(self, 'exit_btn_rect') and self.exit_btn_rect.collidepoint(e.pos):
                self.setup_sel = 1
                self._setup_confirm_action()
                return

    def _start_auto_setup(self):
        """Start the automatic setup process."""
        from ui.draw_setup import pick_directory, AutoSetupThread
        
        # Temporarily exit fullscreen for folder dialog
        if self.fullscreen:
            pygame.display.set_mode((SCREEN_W, SCREEN_H))
        
        root_folder = pick_directory(title="Select Game Machine Root Folder (will create all subfolders)")
        
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
        
        if root_folder:
            norm_path = os.path.normpath(root_folder)
            self.auto_setup = AutoSetupThread(self, norm_path)
            self.auto_setup.start()
        else:
            self.toast = "Setup cancelled - no folder selected"
            self.toast_until = pygame.time.get_ticks() + 2000

    def _setup_confirm_action(self):
        if self.setup_sel == 0:  # Setup Game Machine
            self._start_auto_setup()
        elif self.setup_sel == 1:  # Exit
            pygame.quit()
            sys.exit()

    def _start_auto_setup(self):
        """Start the fully automatic setup process."""
        # Ask for root folder
        from ui.draw_setup import pick_directory
        if self.fullscreen:
            pygame.display.set_mode((SCREEN_W, SCREEN_H))
        path = pick_directory(title="Select Game Machine Root Folder (will create emulators/, PSP_iso/, PS2_iso/, PS3_iso/)")
        if self.fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
        
        if not path:
            self.toast = "Setup cancelled - no folder selected"
            self.toast_until = pygame.time.get_ticks() + 2000
            return
        
        norm_path = os.path.normpath(path)
        self.folders = [norm_path]
        self.settings["folders"] = [norm_path]
        
        # Start auto-setup thread
        from ui.draw_setup import AutoSetupThread
        self.auto_setup = AutoSetupThread(self, norm_path)
        self.auto_setup.start()

    def _check_auto_setup_complete(self):
        """Check if auto-setup finished and transition to dashboard."""
        if getattr(self, "auto_setup", None) and self.auto_setup.finished:
            # Don't finish if waiting for user input (update prompts)
            if self.auto_setup.awaiting_user_input:
                return
            if self.auto_setup.success:
                self.finish_setup()
            else:
                error_msg = self.auto_setup.error if self.auto_setup.error else "Setup failed"
                self.auto_setup = None  # Will show error screen on next draw
                self.toast = f"Setup failed: {error_msg}"
                self.toast_until = pygame.time.get_ticks() + 5000

    def finish_setup(self):
        self.settings["folders"] = self.folders
        self.settings["custom_consoles"] = self.custom_consoles
        save_playdata(self.playdata)

        # Refresh module-level BASE/COVERS_DIR so cover generation and other
        # consumers pick up the newly-configured library folder.
        from core.config import refresh_paths
        refresh_paths()

        # Trigger dynamic scan and rebuild configs
        self.consoles = discover_consoles(self.folders, self.custom_consoles)
        self.colors = build_console_colors(self.consoles)
        self.games = scan_games(self.consoles)

        # Rebuild tabs and display elements
        present = [c for c in self.consoles if any(g["console"] == c for g in self.games)]
        self.tabs = [("RECENTS", REC_COLOR)] + [(c, self.colors[c]) for c in present]

        self.tab = 0 if self._recents() else (1 if len(self.tabs) > 1 else 0)
        self.sel = 0
        self.scroll = 0.0
        self.scroll_t = 0.0
        self.ensure = True
        self.switch_ms = pygame.time.get_ticks()

        # Start background thread to extract PSP & PS2 cover arts now that games are loaded
        start_cover_generator_thread(self.games, self.consoles)

        self.needs_setup = False
        self.toast = "Setup Complete!"
        self.toast_until = pygame.time.get_ticks() + 2000

    def run(self):
        while self.running:
            now = pygame.time.get_ticks()
            for e in pygame.event.get():
                self.handle_event(e)
            self.update_gamepad(now)
            self.update_scroll()

            # Check if auto-setup completed
            if getattr(self, "needs_setup", False):
                self._check_auto_setup_complete()

            # Process cover generation queue (main thread only - pygame safe)
            process_cover_results(self._cover_cache)

            # Check if decryption has finished successfully and launch
            if self.decryption_done.is_set():
                self.decryption_done.clear()
                self.decrypting_active = False
                self._confirm_launch()

            self.draw(now)
            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()


def main():
    GameMachine().run()


if __name__ == "__main__":
    main()
