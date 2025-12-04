"""
MenuManager - Handles all menu UI and state management for the shape-game.
Extracts menu logic from the Game class for better organization and reusability.
"""

import tkinter as tk
import random
from typing import Dict, List, Optional, Any, Tuple
from constants import (
    WIDTH, HEIGHT,
    WEAPON_UPGRADES, LINKED_UPGRADES
)
from audio import stop_background_music, start_background_music


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

    def show_upgrade_menu(self) -> None:
        """Display upgrade selection menu with three random choices."""
        try:
            self.upgrade_menu_active = True
            self.game.paused = True
            
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
            # Height: title (30) + 3 buttons (50 each) + spacing (15*2) + padding (40) = 230
            menu_height = 230
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
                overlay_x + overlay_width // 2, overlay_y + 30,
                text='CHOOSE AN UPGRADE',
                fill='lime',
                font=('Arial', 24, 'bold')
            )
            self.upgrade_menu_elements.append(title)
            
            # Display three upgrade choices as buttons
            button_y_start = overlay_y + 80
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
            self.game.paused = False

    def on_upgrade_selection(self, upgrade_key: str) -> None:
        """Handle upgrade selection."""
        try:
            if upgrade_key in self.upgrade_choices:
                self.game.add_upgrade(upgrade_key)
                self.close_upgrade_menu()
        except Exception as e:
            # Ensure menu is closed even on error
            self.upgrade_menu_active = False
            self.game.paused = False

    def close_upgrade_menu(self) -> None:
        """Close the upgrade menu."""
        self.upgrade_menu_active = False
        self.upgrade_menu_clickable = False
        self.game.paused = False
        
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
        self.game.paused = True
        
        # Create overlay - use actual canvas dimensions
        canvas_width = int(self.canvas.winfo_width())
        canvas_height = int(self.canvas.winfo_height())
        menu_width = int(canvas_width * 0.15)  # 15% of canvas width
        # Height: title (30) + upgrades label (20) + upgrades text (20) + 6 buttons (40 each) + spacing (60*5) + padding (40) = 510
        menu_height = 510
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
        
        # Resume button
        resume_btn_y = overlay_y + 130
        self.pause_buttons['resume'] = self.canvas.create_rectangle(
            overlay_x + 40, resume_btn_y,
            overlay_x + overlay_width - 40, resume_btn_y + 40,
            fill='green', outline='white', width=2
        )
        resume_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, resume_btn_y + 20,
            text='Resume',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['resume'])
        self.pause_menu_elements.append(resume_text)
        
        # Restart button
        restart_btn_y = resume_btn_y + 60
        self.pause_buttons['restart'] = self.canvas.create_rectangle(
            overlay_x + 40, restart_btn_y,
            overlay_x + overlay_width - 40, restart_btn_y + 40,
            fill='orange', outline='white', width=2
        )
        restart_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, restart_btn_y + 20,
            text='Restart',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['restart'])
        self.pause_menu_elements.append(restart_text)
        
        # Quit button
        quit_btn_y = restart_btn_y + 60
        self.pause_buttons['quit'] = self.canvas.create_rectangle(
            overlay_x + 40, quit_btn_y,
            overlay_x + overlay_width - 40, quit_btn_y + 40,
            fill='red', outline='white', width=2
        )
        quit_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, quit_btn_y + 20,
            text='Quit',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['quit'])
        self.pause_menu_elements.append(quit_text)
        
        # Sound toggle button
        sound_btn_y = quit_btn_y + 60
        sound_status = 'ON' if self.game.sound_enabled else 'OFF'
        self.pause_buttons['sound'] = self.canvas.create_rectangle(
            overlay_x + 40, sound_btn_y,
            overlay_x + overlay_width - 40, sound_btn_y + 40,
            fill='#4a4a7a', outline='white', width=2
        )
        sound_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, sound_btn_y + 20,
            text=f'Sound: {sound_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['sound'])
        self.pause_menu_elements.append(sound_text)
        
        # Music toggle button
        music_btn_y = sound_btn_y + 60
        music_status = 'ON' if self.game.music_enabled else 'OFF'
        self.pause_buttons['music'] = self.canvas.create_rectangle(
            overlay_x + 40, music_btn_y,
            overlay_x + overlay_width - 40, music_btn_y + 40,
            fill='#7a4a4a', outline='white', width=2
        )
        music_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, music_btn_y + 20,
            text=f'Music: {music_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['music'])
        self.pause_menu_elements.append(music_text)
        
        # Keyboard layout toggle button
        keyboard_btn_y = music_btn_y + 60
        keyboard_layout_display = self.game.keyboard_layout.upper()
        self.pause_buttons['keyboard'] = self.canvas.create_rectangle(
            overlay_x + 40, keyboard_btn_y,
            overlay_x + overlay_width - 40, keyboard_btn_y + 40,
            fill='#7a4a7a', outline='white', width=2
        )
        keyboard_text = self.canvas.create_text(
            overlay_x + overlay_width // 2, keyboard_btn_y + 20,
            text=f'Layout: {keyboard_layout_display}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['keyboard'])
        self.pause_menu_elements.append(keyboard_text)
        
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
        self.game.paused = False
        self.pause_menu_id = None
        self.pause_buttons = {}
        
        # Clear any stuck keys from being pressed while pause menu was open
        self.game.pressed_keys.clear()
        
        # Delete all pause menu elements
        if self.pause_menu_elements:
            for element in self.pause_menu_elements:
                try:
                    self.canvas.delete(element)
                except:
                    pass  # Element may already be deleted
            self.pause_menu_elements = []

    def quit_game(self) -> None:
        """Close the game window and exit."""
        stop_background_music()
        self.game.root.destroy()

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
        # Height: title (20) + 11 buttons (35 each) + spacing (5*11) + padding (40) = 505
        menu_height = 505
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
        
        # Button definitions: (label, action, color)
        buttons = [
            ('Add Ricochet', 'upgrade_extra_bounce', '#4a4a8a'),
            ('Add Shrapnel', 'upgrade_shrapnel', '#4a4a8a'),
            ('Add Speed Boost', 'upgrade_speed_boost', '#4a4a8a'),
            ('Add Chain Lightning', 'upgrade_chain_lightning', '#4a4a8a'),
            ('Add Black Hole', 'upgrade_black_hole', '#4a4a8a'),
            ('Add Homing', 'upgrade_homing', '#4a4a8a'),
            ('Add Shield', 'upgrade_shield', '#4a4a8a'),
            ('Level Up', 'level_up', '#8a4a4a'),
            ('Add 100 XP', 'add_xp', '#8a4a4a'),
            ('Spawn 30 Enemies', 'spawn_enemies_cmd', '#4a8a4a'),
            ('Back', 'back_to_pause', '#4a4a4a'),
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

    def _handle_dev_menu_action(self, action: str) -> None:
        """Handle dev menu button actions."""
        try:
            if action == 'upgrade_extra_bounce':
                self.game.add_upgrade('extra_bounce')
            elif action == 'upgrade_shrapnel':
                self.game.add_upgrade('shrapnel')
            elif action == 'upgrade_speed_boost':
                self.game.add_upgrade('speed_boost')
            elif action == 'upgrade_chain_lightning':
                self.game.add_upgrade('chain_lightning')
            elif action == 'upgrade_black_hole':
                self.game.add_upgrade('black_hole')
            elif action == 'upgrade_homing':
                self.game.add_upgrade('homing')
            elif action == 'upgrade_shield':
                self.game.add_upgrade('shield')
            elif action == 'level_up':
                self.game.level += 1
                self.game.xp_for_next_level = int(self.game.xp_for_next_level * 1.35)
                self.canvas.itemconfig(self.game.level_text, text=f"Level: {self.game.level}")
            elif action == 'add_xp':
                self.game.add_xp(100)
            elif action == 'spawn_enemies_cmd':
                self.game.respawn_enemies(30)
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
        
        # Check which upgrade button was clicked
        import sys
        upgrade_buttons_copy = list(self.upgrade_buttons.items())
        for upgrade_key, btn_id in upgrade_buttons_copy:
            sys.stdout.write(f"[DEBUG] Checking upgrade button: {upgrade_key}\n")
            sys.stdout.flush()
            try:
                coords = self.canvas.coords(btn_id)
                sys.stdout.write(f"[DEBUG] Got coords for {upgrade_key}: {coords}\n")
                sys.stdout.flush()
                if coords and len(coords) >= 4 and (coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]):
                    sys.stdout.write(f"[DEBUG] Click is on button {upgrade_key}, calling on_upgrade_selection\n")
                    sys.stdout.flush()
                    self.on_upgrade_selection(upgrade_key)
                    return
            except Exception as e:
                sys.stdout.write(f"[ERROR] Error checking button {upgrade_key}: {e}\n")
                sys.stdout.flush()
                import traceback
                traceback.print_exc()
        
        sys.stdout.write(f"[DEBUG] No upgrade button matched click, returning\n")
        sys.stdout.flush()

    def handle_pause_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the pause menu."""
        if not self.game.paused or self.dev_menu_active:
            return
        
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
                    elif action == 'keyboard':
                        self.toggle_keyboard_layout()
                    elif action == 'dev':
                        self.show_dev_menu()
                    return

    def handle_dev_menu_click(self, event: tk.Event) -> None:
        """Handle clicks in the dev menu."""
        if not self.dev_menu_active:
            return
        
        # Check which button was clicked
        for action, btn_id in self.dev_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    self._handle_dev_menu_action(action)
                    return
