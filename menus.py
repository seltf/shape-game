"""
MenuManager - Handles all menu UI and state management for the shape-game.
Extracts menu logic from the Game class for better organization and reusability.
"""

import tkinter as tk
import random
from typing import Dict, List, Optional, Any
from constants import (
    WIDTH, HEIGHT,
    WEAPON_UPGRADES, LINKED_UPGRADES, GameState
)
from audio import stop_background_music, start_background_music, play_beep_async


class MenuManager:
    """Manages all menu display and interaction (upgrade, pause, dev menus)."""
    
    def __init__(self, game: Any) -> None:
        """Initialize MenuManager with reference to the Game instance."""
        self.game: Any = game
        self.canvas: tk.Canvas = game.canvas
        
        # Upgrade menu state
        self.upgrade_menu_active: bool = False
        self.upgrade_menu_clickable: bool = False
        self.upgrade_menu_elements: List[int] = []
        self.upgrade_buttons: Dict[str, int] = {}
        self.upgrade_choices: List[str] = []
        
        # Pause menu state
        self.pause_menu_id: Optional[int] = None
        self.pause_menu_elements: List[int] = []
        self.pause_buttons: Dict[str, int] = {}
        
        # Dev menu state
        self.dev_menu_active: bool = False
        self.dev_menu_elements: List[int] = []
        self.dev_buttons: Dict[str, int] = {}
        self.dev_submenu_active: bool = False  # Track if a submenu is showing

        # Main menu state
        self.main_menu_active: bool = False
        self.main_menu_elements: List[int] = []
        self.main_buttons: Dict[str, int] = {}

    def show_main_menu(self) -> None:
        """Display the main menu with Play, Settings, Credits, Quit."""
        self.main_menu_active = True
        self.game.set_state(GameState.MAIN_MENU)
        self.canvas.delete('all')
        self.game._draw_starfield()
        # Galaxy background for title screen
        try:
            self.game._init_galaxy()
        except Exception:
            pass

        # Use game-tracked window dimensions; fall back to canvas if valid
        canvas_width = int(getattr(self.game, 'window_width', self.canvas.winfo_width()))
        canvas_height = int(getattr(self.game, 'window_height', self.canvas.winfo_height()))
        if canvas_width <= 1:
            canvas_width = int(self.canvas.winfo_width())
        if canvas_height <= 1:
            canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.25)
        menu_height = 360
        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2

        # Background panel
        panel_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + menu_width, overlay_y + menu_height,
            fill='', outline='', width=0
        )
        self.main_menu_elements.append(panel_id)

        # Title
        title_id = self.canvas.create_text(
            overlay_x + menu_width // 2, overlay_y + 60,
            text='SHAPE GAME', fill='cyan', font=('Arial', 42, 'bold')
        )
        self.main_menu_elements.append(title_id)

        # Buttons config
        buttons = [
            ('Play', 'play', 'green'),
            ('Settings', 'settings', '#4a4a7a'),
            ('Credits', 'credits', '#7a4a4a'),
            ('Quit', 'quit', 'red'),
        ]
        button_width = menu_width - 60
        button_height = 48
        spacing = 12
        start_y = overlay_y + 120

        for i, (label, action, color) in enumerate(buttons):
            y = start_y + i * (button_height + spacing)
            btn_id = self.canvas.create_rectangle(
                overlay_x + 30, y,
                overlay_x + 30 + button_width, y + button_height,
                fill=color, outline='white', width=2
            )
            self.main_buttons[action] = btn_id
            self.main_menu_elements.append(btn_id)
            txt_id = self.canvas.create_text(
                overlay_x + menu_width // 2, y + button_height // 2,
                text=label, fill='white', font=('Arial', 18)
            )
            self.main_menu_elements.append(txt_id)

    def handle_main_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the main menu."""
        if not self.main_menu_active:
            return
        play_beep_async(300, 80, self.game)
        for action, btn_id in self.main_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    if action == 'play':
                        self.close_main_menu()
                        self.game.start_game_from_menu()
                    elif action == 'settings':
                        self.show_settings_menu()
                    elif action == 'credits':
                        self.show_credits()
                    elif action == 'quit':
                        # On title screen, Quit should close the application
                        self.quit_app()
                    return

    def close_main_menu(self) -> None:
        """Close the main menu and clear elements."""
        for element_id in self.main_menu_elements:
            try:
                self.canvas.delete(element_id)
            except tk.TclError:
                pass
        self.main_menu_elements = []
        self.main_buttons = {}
        self.main_menu_active = False

    def show_settings_menu(self) -> None:
        """Show a simple settings panel (sound/music toggles)."""
        # Clear existing main menu elements but keep active state
        for element_id in self.main_menu_elements:
            try:
                self.canvas.delete(element_id)
            except tk.TclError:
                pass
        self.main_menu_elements = []
        self.main_buttons = {}

        canvas_width = int(getattr(self.game, 'window_width', self.canvas.winfo_width()))
        canvas_height = int(getattr(self.game, 'window_height', self.canvas.winfo_height()))
        if canvas_width <= 1:
            canvas_width = int(self.canvas.winfo_width())
        if canvas_height <= 1:
            canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.25)
        menu_height = 300
        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2

        panel_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + menu_width, overlay_y + menu_height,
            fill='#102010', outline='lime', width=3
        )
        self.main_menu_elements.append(panel_id)

        title_id = self.canvas.create_text(
            overlay_x + menu_width // 2, overlay_y + 40,
            text='SETTINGS', fill='lime', font=('Arial', 28, 'bold')
        )
        self.main_menu_elements.append(title_id)

        # Buttons: Sound toggle, Music toggle, Back
        buttons = [
            (f"Sound: {'ON' if self.game.sound_enabled else 'OFF'}", 'toggle_sound', '#4a4a7a'),
            (f"Music: {'ON' if self.game.music_enabled else 'OFF'}", 'toggle_music', '#7a4a4a'),
            ('Back', 'back', 'orange')
        ]
        button_width = menu_width - 60
        button_height = 44
        spacing = 10
        start_y = overlay_y + 90
        for i, (label, action, color) in enumerate(buttons):
            y = start_y + i * (button_height + spacing)
            btn_id = self.canvas.create_rectangle(
                overlay_x + 30, y,
                overlay_x + 30 + button_width, y + button_height,
                fill=color, outline='white', width=2
            )
            self.main_buttons[action] = btn_id
            self.main_menu_elements.append(btn_id)
            txt_id = self.canvas.create_text(
                overlay_x + menu_width // 2, y + button_height // 2,
                text=label, fill='white', font=('Arial', 16)
            )
            self.main_menu_elements.append(txt_id)

    def show_credits(self) -> None:
        """Show a simple credits screen with Back."""
        for element_id in self.main_menu_elements:
            try:
                self.canvas.delete(element_id)
            except tk.TclError:
                pass
        self.main_menu_elements = []
        self.main_buttons = {}

        canvas_width = int(getattr(self.game, 'window_width', self.canvas.winfo_width()))
        canvas_height = int(getattr(self.game, 'window_height', self.canvas.winfo_height()))
        if canvas_width <= 1:
            canvas_width = int(self.canvas.winfo_width())
        if canvas_height <= 1:
            canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.35)
        menu_height = 280
        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2

        panel_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + menu_width, overlay_y + menu_height,
            fill='#201010', outline='white', width=3
        )
        self.main_menu_elements.append(panel_id)

        title_id = self.canvas.create_text(
            overlay_x + menu_width // 2, overlay_y + 30,
            text='CREDITS', fill='white', font=('Arial', 28, 'bold')
        )
        self.main_menu_elements.append(title_id)

        body_id = self.canvas.create_text(
            overlay_x + menu_width // 2, overlay_y + 120,
            text='Shape Game\nDesign & Code: You\nAudio: System beeps\nEngine: Tkinter',
            fill='white', font=('Arial', 14)
        )
        self.main_menu_elements.append(body_id)

        # Back button
        btn_id = self.canvas.create_rectangle(
            overlay_x + 30, overlay_y + menu_height - 70,
            overlay_x + menu_width - 30, overlay_y + menu_height - 26,
            fill='orange', outline='white', width=2
        )
        self.main_buttons['back'] = btn_id
        self.main_menu_elements.append(btn_id)
        txt_id = self.canvas.create_text(
            overlay_x + menu_width // 2, overlay_y + menu_height - 48,
            text='Back', fill='white', font=('Arial', 16)
        )
        self.main_menu_elements.append(txt_id)

    def handle_settings_or_credits_click(self, event: tk.Event) -> None:
        """Handle clicks on settings/credits screens."""
        if not self.main_menu_active:
            return
        play_beep_async(300, 80, self.game)
        for action, btn_id in self.main_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    if action == 'back':
                        self.show_main_menu()
                    elif action == 'toggle_sound':
                        self.toggle_sound()
                        self.show_settings_menu()
                    elif action == 'toggle_music':
                        self.toggle_music()
                        self.show_settings_menu()
                    return

    def show_upgrade_menu(self) -> None:
        """Display upgrade selection menu with three random choices."""
        try:
            self.upgrade_menu_active = True
            self.game.set_state(GameState.UPGRADE_MENU)
            
            # Pick three random upgrades
            available_upgrades = list(WEAPON_UPGRADES.keys())
            
            # Remove one-time upgrades that have already been picked
            available_upgrades = [
                u for u in available_upgrades 
                if not (WEAPON_UPGRADES[u].get('one_time', False) and u in self.game.active_upgrades)
            ]
            
            # Remove shield upgrade if it's already maxed at level 3
            shield_level = self.game.computed_weapon_stats.get('shield', 0)
            if shield_level >= 3:
                available_upgrades = [u for u in available_upgrades if u != 'shield']
            
            # Add linked upgrades if prerequisites are met
            for linked_key, linked_data in LINKED_UPGRADES.items():
                requires = linked_data['requires']
                can_unlock = False
                
                # Handle different requirement types
                if isinstance(requires, dict):
                    # Level-based requirement: {'upgrade': 'chain_lightning', 'level': 5}
                    upgrade_name = requires.get('upgrade')
                    required_level = requires.get('level', 1)
                    
                    # Count how many times this upgrade is owned (level)
                    upgrade_count = self.game.active_upgrades.count(upgrade_name)
                    if upgrade_count >= required_level:
                        can_unlock = True
                elif isinstance(requires, list):
                    # All prerequisites must be owned
                    if all(req in self.game.active_upgrades for req in requires):
                        can_unlock = True
                else:
                    # Single prerequisite string
                    if requires in self.game.active_upgrades:
                        can_unlock = True
                
                if can_unlock:
                    available_upgrades.append(linked_key)
            
            self.upgrade_choices = random.sample(available_upgrades, min(3, len(available_upgrades)))
            
            # Create overlay - use actual canvas dimensions
            canvas_width = int(self.canvas.winfo_width())
            canvas_height = int(self.canvas.winfo_height())
            menu_width = int(canvas_width * 0.15)  # 15% of canvas width
            
            # Calculate menu height dynamically based on number of buttons
            title_height = 50  # Title text height with padding
            button_height = 50
            button_spacing = 15
            num_buttons = len(self.upgrade_choices)
            padding = 20
            
            menu_height = title_height + (num_buttons * button_height) + ((num_buttons - 1) * button_spacing) + padding
            
            overlay_x = (canvas_width - menu_width) // 2
            overlay_y = (canvas_height - menu_height) // 2
            overlay_width = menu_width
            overlay_height = menu_height
            
            # Background rectangle
            overlay_id = self.canvas.create_rectangle(
                overlay_x, overlay_y,
                overlay_x + overlay_width, overlay_y + overlay_height,
                fill='#1a1a2e', outline='lime', width=3
            )
            self.upgrade_menu_elements.append(overlay_id)
            
            # Title
            title = self.canvas.create_text(
                overlay_x + overlay_width // 2, overlay_y + title_height // 2,
                text='CHOOSE AN UPGRADE',
                fill='lime',
                font=('Arial', 24, 'bold')
            )
            self.upgrade_menu_elements.append(title)
            
            # Display three upgrade choices as buttons
            button_y_start = overlay_y + title_height
            button_height = 50
            button_spacing = 15
            
            for i, upgrade_key in enumerate(self.upgrade_choices):
                btn_y = button_y_start + i * (button_height + button_spacing)
                
                # Get upgrade name from either regular or linked upgrades
                if upgrade_key in WEAPON_UPGRADES:
                    upgrade_name = WEAPON_UPGRADES[upgrade_key]['name']
                else:
                    upgrade_name = LINKED_UPGRADES[upgrade_key]['name']
                
                # Button rectangle
                btn_id = self.canvas.create_rectangle(
                    overlay_x + 20, btn_y,
                    overlay_x + overlay_width - 20, btn_y + button_height,
                    fill='#2a2a4e', outline='lime', width=2
                )
                self.upgrade_buttons[upgrade_key] = btn_id
                self.upgrade_menu_elements.append(btn_id)
                
                # Button text
                text_id = self.canvas.create_text(
                    overlay_x + overlay_width // 2, btn_y + button_height // 2,
                    text=upgrade_name,
                    fill='lime',
                    font=('Arial', 16)
                )
                self.upgrade_menu_elements.append(text_id)
            
            # Enable clicks after 300ms delay to prevent accidental selections
            self.upgrade_menu_clickable = False
            self.game.root.after(300, lambda: setattr(self, 'upgrade_menu_clickable', True))
        except Exception as e:
            print(f"Error in show_upgrade_menu: {e}")
            self.upgrade_menu_active = False
            # Resume gameplay if the upgrade menu failed to show
            self.game.set_state(GameState.PLAYING)

    def on_upgrade_selection(self, upgrade_key: str) -> None:
        """Handle upgrade selection."""
        try:
            if upgrade_key in self.upgrade_choices:
                self.game.add_upgrade(upgrade_key)
                self.close_upgrade_menu()
        except Exception as e:
            # Ensure menu is closed even on error
            self.upgrade_menu_active = False
            # Resume gameplay on error
            self.game.set_state(GameState.PLAYING)

    def close_upgrade_menu(self, resume_game: bool = True) -> None:
        """Close the upgrade menu.
        
        Args:
            resume_game: If True, resume the game. If False, keep paused state.
        """
        self.upgrade_menu_active = False
        self.upgrade_menu_clickable = False
        if resume_game:
            self.game.set_state(GameState.PLAYING)
        
        # Delete canvas elements
        for element_id in self.upgrade_menu_elements:
            try:
                self.canvas.delete(element_id)
            except tk.TclError:
                pass  # Element already deleted or invalid
        
        # Clear all references
        self.upgrade_menu_elements = []
        self.upgrade_buttons = {}
        self.upgrade_choices = []

    def show_pause_menu(self) -> None:
        """Display pause menu overlay on the game canvas."""
        self.game.set_state(GameState.PAUSED)
        
        # Create overlay - use actual canvas dimensions
        canvas_width = int(self.canvas.winfo_width())
        canvas_height = int(self.canvas.winfo_height())
        menu_width = 320  # Fixed width in pixels
        
        # Calculate menu height dynamically based on content
        title_height = 50  # Title with padding
        upgrades_section_height = 50  # Label + text display
        button_height = 40
        button_spacing = 10
        num_buttons = 6  # Resume, Restart, Quit, Sound, Music, Dev (hidden)
        padding = 20
        
        menu_height = (title_height + upgrades_section_height + 
                      (num_buttons * button_height) + ((num_buttons - 1) * button_spacing) + 
                      padding)
        
        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2
        overlay_width = menu_width
        overlay_height = menu_height
        
        # Background rectangle
        self.pause_menu_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a1a', outline='cyan', width=3
        )
        
        # Store all pause menu elements for cleanup
        self.pause_menu_elements = [self.pause_menu_id]
        
        # Title
        title = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 30,
            text='PAUSED',
            fill='yellow',
            font=('Arial', 32, 'bold')
        )
        self.pause_menu_elements.append(title)
        
        # Upgrades panel
        upgrades_label = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 70,
            text='Active Upgrades:',
            fill='cyan',
            font=('Arial', 14, 'bold')
        )
        self.pause_menu_elements.append(upgrades_label)
        
        # Display active upgrades
        if self.game.active_upgrades:
            # Count upgrades by type
            upgrade_counts = {}
            for upgrade_key in self.game.active_upgrades:
                # Check regular upgrades first
                if upgrade_key in WEAPON_UPGRADES:
                    upgrade_name = WEAPON_UPGRADES[upgrade_key]['name']
                # Then check linked upgrades
                elif upgrade_key in LINKED_UPGRADES:
                    upgrade_name = LINKED_UPGRADES[upgrade_key]['name']
                else:
                    continue  # Skip unknown upgrades
                upgrade_counts[upgrade_name] = upgrade_counts.get(upgrade_name, 0) + 1
            
            # Format as "Upgrade x1, Upgrade x2" etc
            upgrades_text = ', '.join([f"{name} x{count}" for name, count in upgrade_counts.items()]) if upgrade_counts else 'None'
        else:
            upgrades_text = 'None'
        
        upgrades_display = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 90,
            text=upgrades_text,
            fill='lime',
            font=('Arial', 12)
        )
        self.pause_menu_elements.append(upgrades_display)
        
        # Calculate button positions based on dynamic height
        button_y = overlay_y + title_height + upgrades_section_height + 10  # 10 for top padding of buttons
        button_width = overlay_width - 80  # 40px margin on each side
        
        # Resume button
        self.pause_buttons['resume'] = self.canvas.create_rectangle(
            overlay_x + 40, button_y,
            overlay_x + overlay_width - 40, button_y + button_height,
            fill='green', outline='white', width=2
        )
        resume_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, button_y + button_height // 2,
            text='Resume',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['resume'])
        self.pause_menu_elements.append(resume_text)
        button_y += button_height + button_spacing
        
        # Restart button
        self.pause_buttons['restart'] = self.canvas.create_rectangle(
            overlay_x + 40, button_y,
            overlay_x + overlay_width - 40, button_y + button_height,
            fill='orange', outline='white', width=2
        )
        restart_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, button_y + button_height // 2,
            text='Restart',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['restart'])
        self.pause_menu_elements.append(restart_text)
        button_y += button_height + button_spacing
        
        # Quit button
        self.pause_buttons['quit'] = self.canvas.create_rectangle(
            overlay_x + 40, button_y,
            overlay_x + overlay_width - 40, button_y + button_height,
            fill='red', outline='white', width=2
        )
        quit_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, button_y + button_height // 2,
            text='Quit',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['quit'])
        self.pause_menu_elements.append(quit_text)
        button_y += button_height + button_spacing
        
        # Sound toggle button
        sound_status = 'ON' if self.game.sound_enabled else 'OFF'
        self.pause_buttons['sound'] = self.canvas.create_rectangle(
            overlay_x + 40, button_y,
            overlay_x + overlay_width - 40, button_y + button_height,
            fill='#4a4a7a', outline='white', width=2
        )
        sound_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, button_y + button_height // 2,
            text=f'Sound: {sound_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['sound'])
        self.pause_menu_elements.append(sound_text)
        button_y += button_height + button_spacing
        
        # Music toggle button
        music_status = 'ON' if self.game.music_enabled else 'OFF'
        self.pause_buttons['music'] = self.canvas.create_rectangle(
            overlay_x + 40, button_y,
            overlay_x + overlay_width - 40, button_y + button_height,
            fill='#7a4a4a', outline='white', width=2
        )
        music_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, button_y + button_height // 2,
            text=f'Music: {music_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['music'])
        self.pause_menu_elements.append(music_text)
        button_y += button_height + button_spacing
        
        # Hidden dev button (tiny, in corner)
        self.pause_buttons['dev'] = self.canvas.create_rectangle(
            overlay_x + overlay_width - 25, overlay_y,
            overlay_x + overlay_width, overlay_y + 20,
            fill='#333333', outline='gray', width=1
        )
        dev_text = self.canvas.create_text(
            overlay_x + overlay_width - 12, overlay_y + 10,
            text='DEV',
            fill='gray',
            font=('Arial', 8)
        )
        self.pause_menu_elements.append(self.pause_buttons['dev'])
        self.pause_menu_elements.append(dev_text)

    def hide_pause_menu(self) -> None:
        """Hide the pause menu and resume the game."""
        # Explicitly clear everything
        self.game.set_state(GameState.PLAYING)
        self.pause_menu_id = None
        self.pause_buttons = {}
        
        # Clear any stuck keys from being pressed while pause menu was open
        self.game.pressed_keys.clear()
        
        # Delete all pause menu elements
        if self.pause_menu_elements:
            for element in self.pause_menu_elements:
                try:
                    self.canvas.delete(element)
                except tk.TclError:
                    pass  # Element may already be deleted
                except Exception as e:
                    print(f"[ERROR] Unexpected error deleting pause menu element: {e}")
            self.pause_menu_elements = []

    def quit_game(self) -> None:
        """Reset game and return to the main menu instead of exiting."""
        stop_background_music()
        try:
            self.game.return_to_main_menu()
        except Exception as e:
            print(f"[MENU] Failed to return to main menu: {e}")

    def quit_app(self) -> None:
        """Close the application window immediately (used by Title Screen Quit)."""
        try:
            stop_background_music()
        except Exception:
            pass
        try:
            # Destroy the Tk root window to exit cleanly
            self.game.root.destroy()
        except Exception as e:
            print(f"[MENU] Failed to close app: {e}")

    def toggle_sound(self) -> None:
        """Toggle sound on/off and refresh pause menu to show new state."""
        self.game.sound_enabled = not self.game.sound_enabled
        # Close and reopen pause menu to update the sound button text
        self.hide_pause_menu()
        self.show_pause_menu()

    def toggle_music(self) -> None:
        """Toggle music on/off and refresh pause menu to show new state."""
        self.game.music_enabled = not self.game.music_enabled
        if not self.game.music_enabled:
            stop_background_music()
        else:
            start_background_music(self.game)
        # Close and reopen pause menu to update the music button text
        self.hide_pause_menu()
        self.show_pause_menu()

    def toggle_keyboard_layout(self) -> None:
        """Toggle between Dvorak and QWERTY keyboard layouts and refresh pause menu."""
        self.game.keyboard_layout = 'qwerty' if self.game.keyboard_layout == 'dvorak' else 'dvorak'
        # Close and reopen pause menu to update the keyboard button text
        self.hide_pause_menu()
        self.show_pause_menu()

    def show_dev_menu(self) -> None:
        """Display the developer testing menu."""
        self.dev_menu_active = True
        
        # Create overlay - use actual canvas dimensions
        canvas_width = int(self.canvas.winfo_width())
        canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.2)  # 20% of canvas width

        # Actual button definitions shown in the dev menu - used to size the overlay
        buttons = [
            ('Upgrades', 'upgrade_submenu', '#4a4a8a'),
            ('Level Up', 'level_up', '#8a4a4a'),
            ('Add 100 XP', 'add_xp', '#8a4a4a'),
            ('Spawn 30 Enemies', 'spawn_enemies_cmd', '#4a8a4a'),
            ('Spawn Enemy', 'spawn_enemy_submenu', '#4a8a4a'),
            ('Back', 'back_to_pause', '#4a4a4a'),
        ]

        num_buttons = len(buttons)
        title_height = 40
        button_height = 35
        button_spacing = 5
        padding = 40
        menu_height = title_height + (num_buttons * button_height) + ((num_buttons - 1) * button_spacing) + padding

        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2
        overlay_width = menu_width
        overlay_height = menu_height
        
        # Background rectangle
        overlay_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a3e', outline='magenta', width=3
        )
        self.dev_menu_elements.append(overlay_id)
        
        # Title
        title = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 20,
            text='DEV TESTING MENU',
            fill='magenta',
            font=('Arial', 20, 'bold')
        )
        self.dev_menu_elements.append(title)
        
        button_width = overlay_width - 40
        button_height = 35
        button_spacing = 5
        start_y = overlay_y + 55
        
        for i, (label, action, color) in enumerate(buttons):
            btn_y = start_y + i * (button_height + button_spacing)
            
            btn_x1 = int(overlay_x + 20)
            btn_y1 = int(btn_y)
            btn_x2 = int(overlay_x + 20 + button_width)
            btn_y2 = int(btn_y + button_height)
            
            btn_id = self.canvas.create_rectangle(
                btn_x1, btn_y1,
                btn_x2, btn_y2,
                fill=color, outline='white', width=1
            )
            self.dev_buttons[action] = btn_id
            self.dev_menu_elements.append(btn_id)
            
            text_id = self.canvas.create_text(
                overlay_x + overlay_width // 2, btn_y1 + button_height // 2,
                text=label,
                fill='white',
                font=('Arial', 12)
            )
            self.dev_menu_elements.append(text_id)

    def show_enemy_spawn_submenu(self) -> None:
        """Display the enemy spawn submenu."""
        self.dev_submenu_active = True
        
        # Create overlay
        canvas_width = int(self.canvas.winfo_width())
        canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.2)
        # Height: title (20) + 6 buttons (35 each) + spacing (5*6) + padding (40) = 275
        menu_height = 275
        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2
        overlay_width = menu_width
        overlay_height = menu_height
        
        # Background rectangle
        overlay_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a3e', outline='cyan', width=3
        )
        self.dev_menu_elements.append(overlay_id)
        
        # Title
        title = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 20,
            text='SPAWN ENEMY',
            fill='cyan',
            font=('Arial', 18, 'bold')
        )
        self.dev_menu_elements.append(title)
        
        # Button definitions: (label, action, color)
        buttons = [
            ('Triangle', 'spawn_triangle', '#4a8a4a'),
            ('Square', 'spawn_square', '#4a8a4a'),
            ('Pentagon', 'spawn_pentagon', '#4a8a4a'),
            ('Hexagon', 'spawn_hexagon', '#4a8a4a'),
            ('Ranged', 'spawn_ranged', '#4a8a4a'),
            ('Boss', 'spawn_boss', '#8a4a4a'),
            ('Back', 'back_to_dev_menu', '#4a4a4a'),
        ]
        
        button_width = overlay_width - 40
        button_height = 35
        button_spacing = 5
        start_y = overlay_y + 55
        
        for i, (label, action, color) in enumerate(buttons):
            btn_y = start_y + i * (button_height + button_spacing)
            
            btn_x1 = int(overlay_x + 20)
            btn_y1 = int(btn_y)
            btn_x2 = int(overlay_x + 20 + button_width)
            btn_y2 = int(btn_y + button_height)
            
            btn_id = self.canvas.create_rectangle(
                btn_x1, btn_y1,
                btn_x2, btn_y2,
                fill=color, outline='white', width=1
            )
            self.dev_buttons[action] = btn_id
            self.dev_menu_elements.append(btn_id)
            
            text_id = self.canvas.create_text(
                overlay_x + overlay_width // 2, btn_y1 + button_height // 2,
                text=label,
                fill='white',
                font=('Arial', 12)
            )
            self.dev_menu_elements.append(text_id)

    def show_upgrade_submenu(self) -> None:
        """Display the dev upgrades submenu."""
        self.dev_submenu_active = True

        # Create overlay - size the height based on number of buttons
        canvas_width = int(self.canvas.winfo_width())
        canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.2)

        # Button definitions: upgrade buttons and back
        buttons = [
              ('Ricochet', 'upgrade_extra_bounce', '#4a8a4a'),
              ('Shrapnel', 'upgrade_shrapnel', '#4a8a4a'),
              ('Rapid Fire', 'upgrade_rapid_fire', '#4a8a4a'),
              ('Chain Lightning', 'upgrade_chain_lightning', '#4a8a4a'),
              ('Black Hole', 'upgrade_black_hole', '#4a8a4a'),
              ('Homing', 'upgrade_homing', '#4a8a4a'),
              ('Shield', 'upgrade_shield', '#4a8a4a'),
              ('Summon Minion', 'upgrade_summon_minion', '#4a8a4a'),
              ('Back', 'back_to_dev_menu', '#4a8a4a'),
        ]

        num_buttons = len(buttons)
        title_height = 40
        button_height = 35
        button_spacing = 6
        padding = 20
        menu_height = title_height + (num_buttons * button_height) + ((num_buttons - 1) * button_spacing) + padding

        overlay_x = (canvas_width - menu_width) // 2
        overlay_y = (canvas_height - menu_height) // 2
        overlay_width = menu_width
        overlay_height = menu_height

        # Background rectangle
        overlay_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a3e', outline='cyan', width=3
        )
        self.dev_menu_elements.append(overlay_id)

        # Title
        title = self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 20,
            text='DEV UPGRADES',
            fill='cyan',
            font=('Arial', 18, 'bold')
        )
        self.dev_menu_elements.append(title)

        button_width = overlay_width - 40
        # Reuse computed button_height and spacing
        start_y = overlay_y + title_height + 8

        for i, (label, action, color) in enumerate(buttons):
            btn_y = start_y + i * (button_height + button_spacing)

            btn_x1 = int(overlay_x + 20)
            btn_y1 = int(btn_y)
            btn_x2 = int(overlay_x + 20 + button_width)
            btn_y2 = int(btn_y + button_height)

            btn_id = self.canvas.create_rectangle(
                btn_x1, btn_y1,
                btn_x2, btn_y2,
                fill=color, outline='white', width=1
            )
            self.dev_buttons[action] = btn_id
            self.dev_menu_elements.append(btn_id)

            text_id = self.canvas.create_text(
                overlay_x + overlay_width // 2, btn_y1 + button_height // 2,
                text=label,
                fill='white',
                font=('Arial', 12)
            )
            self.dev_menu_elements.append(text_id)

    def _handle_dev_menu_action(self, action: str) -> None:
        """Handle dev menu button actions."""
        try:
            # Open upgrades submenu
            if action == 'upgrade_submenu':
                for element_id in self.dev_menu_elements:
                    try:
                        self.canvas.delete(element_id)
                    except tk.TclError:
                        pass
                self.dev_menu_elements = []
                self.dev_buttons = {}
                self.show_upgrade_submenu()
                return
            if action == 'upgrade_extra_bounce':
                self.game.add_upgrade('extra_bounce')
            elif action == 'upgrade_shrapnel':
                self.game.add_upgrade('shrapnel')
            elif action == 'upgrade_rapid_fire':
                self.game.add_upgrade('rapid_fire')
            elif action == 'upgrade_chain_lightning':
                self.game.add_upgrade('chain_lightning')
            elif action == 'upgrade_black_hole':
                self.game.add_upgrade('black_hole')
            elif action == 'upgrade_homing':
                self.game.add_upgrade('homing')
            elif action == 'upgrade_shield':
                self.game.add_upgrade('shield')
            elif action == 'upgrade_summon_minion':
                self.game.add_upgrade('summon_minion')
            elif action == 'level_up':
                self.game.level += 1
                self.game.xp_for_next_level = int(self.game.xp_for_next_level * 1.35)
                self.canvas.itemconfig(self.game.level_text, text=f"Level: {self.game.level}")
            elif action == 'add_xp':
                self.game.add_xp(100)
            elif action == 'spawn_enemies_cmd':
                self.game.respawn_enemies(30)
            elif action == 'spawn_enemy_submenu':
                # Show the enemy spawn submenu
                for element_id in self.dev_menu_elements:
                    try:
                        self.canvas.delete(element_id)
                    except tk.TclError:
                        pass
                self.dev_menu_elements = []
                self.dev_buttons = {}
                self.show_enemy_spawn_submenu()
                return
            elif action == 'spawn_triangle':
                self.game.spawn_enemy('triangle')
                print(f"[DEV] Triangle spawned")
            elif action == 'spawn_square':
                self.game.spawn_enemy('square')
                print(f"[DEV] Square spawned")
            elif action == 'spawn_pentagon':
                self.game.spawn_enemy('pentagon')
                print(f"[DEV] Pentagon spawned")
            elif action == 'spawn_hexagon':
                self.game.spawn_enemy('hexagon')
                print(f"[DEV] Hexagon spawned")
            elif action == 'spawn_ranged':
                self.game.spawn_enemy('ranged')
                print(f"[DEV] Ranged enemy spawned")
            elif action == 'spawn_boss':
                self.game.spawn_enemy('boss')
                print(f"[DEV] Boss spawned")
            elif action == 'back_to_dev_menu':
                # Return to main dev menu from submenu
                for element_id in self.dev_menu_elements:
                    try:
                        self.canvas.delete(element_id)
                    except tk.TclError:
                        pass
                self.dev_menu_elements = []
                self.dev_buttons = {}
                self.dev_submenu_active = False
                self.show_dev_menu()
                return
            elif action == 'back_to_pause':
                self.close_dev_menu()
                return
            
            # Keep dev menu open for multiple selections
            # Delete only dev menu elements and redraw the menu
            for element_id in self.dev_menu_elements:
                try:
                    self.canvas.delete(element_id)
                except tk.TclError:
                    pass
            
            self.dev_menu_elements = []
            self.dev_buttons = {}
            if self.dev_submenu_active:
                self.dev_submenu_active = False
                self.show_dev_menu()
            else:
                self.show_dev_menu()
        except Exception as e:
            print(f"Error in dev action '{action}': {e}")

    def close_dev_menu(self) -> None:
        """Close the dev menu and return to pause menu."""
        for element_id in self.dev_menu_elements:
            try:
                self.canvas.delete(element_id)
            except tk.TclError:
                pass
        
        self.dev_menu_elements = []
        self.dev_buttons = {}
        self.dev_menu_active = False
        
        # Close and reopen pause menu to refresh upgrade display
        self.hide_pause_menu()
        self.show_pause_menu()

    def handle_upgrade_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the upgrade menu."""
        if not self.upgrade_menu_active or not self.upgrade_menu_clickable:
            return
        
        # Play button click sound
        play_beep_async(300, 80, self.game)
        
        # Check which upgrade button was clicked
        upgrade_buttons_copy = list(self.upgrade_buttons.items())
        for upgrade_key, btn_id in upgrade_buttons_copy:
            try:
                coords = self.canvas.coords(btn_id)
                if coords and len(coords) >= 4 and (coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]):
                    self.on_upgrade_selection(upgrade_key)
                    return
            except Exception as e:
                pass

    def handle_pause_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the pause menu."""
        if not self.game.paused or self.dev_menu_active:
            return
        
        # Play button click sound
        play_beep_async(300, 80, self.game)
        
        # Check which button was clicked
        for action, btn_id in self.pause_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    if action == 'resume':
                        self.hide_pause_menu()
                    elif action == 'restart':
                        self.game.restart_game()
                    elif action == 'quit':
                        self.quit_game()
                    elif action == 'sound':
                        self.toggle_sound()
                    elif action == 'music':
                        self.toggle_music()
                    elif action == 'dev':
                        self.show_dev_menu()
                    return

    def handle_dev_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the dev menu."""
        if not self.dev_menu_active:
            return
        
        # Play button click sound
        play_beep_async(300, 80, self.game)
        
        # Check which button was clicked
        for action, btn_id in self.dev_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self._handle_dev_menu_action(action)
                    return
