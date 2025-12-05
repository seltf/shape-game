import tkinter as tk
import random
import math
import threading
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from separate modules
from constants import *
from audio import play_sound_async, play_beep_async, play_beep_unthrottled, start_background_music, stop_background_music
from entities import BlackHole, Player, Enemy, TriangleEnemy, PentagonEnemy, Particle, Shard, Projectile, Minion, MinionProjectile
from menus import MenuManager
from collision import CollisionDetector, PlayerCollisionHandler


class Game:
    """
    Main game class. Handles game state, input, rendering, and logic.
    """
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the game window, player, enemies, and event bindings."""
        self.root: tk.Tk = root
        
        self.canvas: tk.Canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
        self.canvas.pack()
        
        # Get the actual canvas dimensions (after packing)
        root.update()
        self.window_width: int = self.canvas.winfo_width()
        self.window_height: int = self.canvas.winfo_height()
        
        # If canvas dimensions are not set yet, use root window dimensions
        if self.window_width <= 1:
            self.window_width = root.winfo_width()
        if self.window_height <= 1:
            self.window_height = root.winfo_height()
        
        # Draw starfield background
        self._draw_starfield()
        
        self.score = 0
        self.score_text = self.canvas.create_text(self.window_width//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.player = Player(self.canvas, self.window_width//2, self.window_height//2, PLAYER_SIZE)
        self.player.game = self  # Give player reference to game instance for shield pushback
        
        self.enemies = []
        self.particles = []
        self.shards = []  # Track shrapnel shards
        self.projectiles = []
        self.minions = []  # Track friendly minions
        self.minion_projectiles = []  # Track minion projectiles
        self.game_time_ms = 0  # Track time played in milliseconds
        self.last_dash_dx = 1  # Default dash direction (right)
        self.last_dash_dy = 0
        self.active_upgrades = []  # List of active upgrade keys
        self.computed_weapon_stats = self.compute_weapon_stats()  # Cache computed stats
        
        # Activate initial shield if shield upgrade is owned
        self._update_player_shield()
        
        self.dash_cooldown_counter = 0
        self.last_move_dx = 1  # Track last movement direction
        self.last_move_dy = 0
        self.xp = 0  # Current XP
        self.level = 0  # Current level
        self.xp_for_next_level = 10  # XP needed for next level
        self.level_text = self.canvas.create_text(self.window_width//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(self.window_width//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")

        # Ability system

        self.black_holes = []  # List of active black holes from weapon upgrades
        
        # Initialize menu manager
        self.menu_manager = MenuManager(self)
        
        self.spawn_enemies()
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.root.bind('<FocusOut>', self.on_window_focus_out)
        self.root.bind('<FocusIn>', self.on_window_focus_in)
        self.pressed_keys = set()
        self.paused = False
        self.ammo_orbs = []  # Track ammo orb canvas items
        self.ammo_rotation = 0  # Angle for orbiting ammo orbs
        self.sound_enabled = True  # Sound effects enabled by default
        self.music_enabled = False  # Background music disabled by default
        self.keyboard_layout = 'dvorak'  # 'dvorak' or 'qwerty'
        self.game_over_active = False  # Whether game over screen is showing
        self.game_over_restart_btn = None  # Reference to restart button
        self.auto_fire_enabled = False  # Auto-fire toggle
        self.attack_cooldown = 0  # Milliseconds until next attack available
        
        # Start background music
        start_background_music(self)
        
        self.root.after(50, self.update)
        # Schedule first respawn
        self.root.after(RESPAWN_INTERVAL, self.on_respawn_timer)

    def _draw_starfield(self):
        """Draw a starfield background with randomly positioned stars."""
        # Create a tag for starfield so we can keep it in background
        num_stars = 150
        for _ in range(num_stars):
            x = random.randint(0, self.window_width)
            y = random.randint(0, self.window_height)
            size = random.randint(1, 3)  # Small stars
            brightness = random.randint(100, 255)
            color = f'#{brightness:02x}{brightness:02x}{brightness:02x}'  # White-ish
            
            # Create small circles for stars
            star = self.canvas.create_oval(
                x - size//2, y - size//2,
                x + size//2, y + size//2,
                fill=color, outline=color
            )
            # Send to back so it doesn't interfere with game elements
            self.canvas.tag_lower(star)

    def compute_weapon_stats(self):
        """Compute effective weapon stats based on base stats and active upgrades."""
        stats = WEAPON_STATS.copy()
        
        for upgrade_key in self.active_upgrades:
            upgrade = None
            
            # Check regular upgrades first
            if upgrade_key in WEAPON_UPGRADES:
                upgrade = WEAPON_UPGRADES[upgrade_key]
            # Then check linked upgrades
            elif upgrade_key in LINKED_UPGRADES:
                upgrade = LINKED_UPGRADES[upgrade_key].get('modifiers', {})
            else:
                continue
            
            # Handle different upgrade types
            for key, value in upgrade.items():
                if key == 'name' or key == 'requires':
                    continue  # Skip name and requires fields
                
                if key == 'splits':
                    # Override splits directly
                    stats['splits'] = value
                elif key in ['projectile_speed', 'homing', 'bounces', 'shrapnel', 'explosive_shrapnel', 'chain_lightning', 'black_hole', 'shield', 'attack_range']:
                    # Add to base values
                    if key not in stats:
                        stats[key] = 0
                    stats[key] += value
        
        return stats
    
    def add_xp(self, amount):
        """Add XP and check for level up."""
        self.xp += amount
        self.canvas.itemconfig(self.xp_text, text=f"XP: {self.xp}/{self.xp_for_next_level}")
        
        if self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            self.xp_for_next_level = int(self.xp_for_next_level * 1.2)  # Scale XP requirement
            self.canvas.itemconfig(self.level_text, text=f"Level: {self.level}")
            self.canvas.itemconfig(self.xp_text, text=f"XP: {self.xp}/{self.xp_for_next_level}")
            # Show upgrade menu on level up
            if not self.menu_manager.upgrade_menu_active and not self.paused:
                self.show_upgrade_menu()

    def add_upgrade(self, upgrade_key):
        """Add an upgrade to active upgrades and recompute stats."""
        try:
            if upgrade_key not in WEAPON_UPGRADES and upgrade_key not in LINKED_UPGRADES:
                return False
            self.active_upgrades.append(upgrade_key)
            self.computed_weapon_stats = self.compute_weapon_stats()
            # Only update player shield if a shield-related upgrade was picked
            if upgrade_key == 'shield':
                self._update_player_shield()
            # Spawn a minion when summon_minion upgrade is picked
            elif upgrade_key == 'summon_minion':
                self._spawn_minion()
            return True
        except Exception as e:
            return False
    
    def remove_upgrade(self, upgrade_key):
        """Remove an upgrade from active upgrades and recompute stats."""
        if upgrade_key in self.active_upgrades:
            self.active_upgrades.remove(upgrade_key)
            self.computed_weapon_stats = self.compute_weapon_stats()
            return True
        return False

    def spawn_enemies(self):
        """Create a new set of enemies at random positions outside the screen, scaled by level."""
        self.enemies.clear()
        initial_count = TESTING_MODE_ENEMY_COUNT if TESTING_MODE else INITIAL_ENEMY_COUNT
        # Scale initial enemy count with level
        level_scaled_count = int(initial_count * (1 + 0.15 * self.level))  # 15% increase per level
        
        for _ in range(level_scaled_count):
            # Spawn enemies outside the screen bounds
            margin = 200  # Spawn distance from edge
            
            # Choose a side (top, bottom, left, right) and spawn on that edge only
            side = random.choice(['top', 'bottom', 'left', 'right'])
            
            if side == 'top':
                # Top edge: x spans full width, y is above screen
                x = random.randint(-ENEMY_SIZE, self.window_width)
                y = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
            elif side == 'bottom':
                # Bottom edge: x spans full width, y is below screen
                x = random.randint(-ENEMY_SIZE, self.window_width)
                y = random.randint(self.window_height, self.window_height + margin)
            elif side == 'left':
                # Left edge: x is left of screen, y spans full height
                x = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
                y = random.randint(-ENEMY_SIZE, self.window_height)
            else:  # right
                # Right edge: x is right of screen, y spans full height
                x = random.randint(self.window_width, self.window_width + margin)
                y = random.randint(-ENEMY_SIZE, self.window_height)
            
            self._spawn_enemy_by_level(x, y)
    
    def _spawn_enemy_by_level(self, x, y):
        """Spawn an enemy with type based on current level."""
        # Pentagon chance increases with level: 0% at level 0, 15% at level 10, 30% at level 20
        pentagon_chance = min(0.3, 0.015 * self.level)
        
        # Triangle chance: starts at 30% at level 5, increases to 60% at level 20
        # Before level 5, triangles don't spawn
        if self.level >= 5:
            triangle_chance = min(0.6, 0.3 + (0.015 * (self.level - 5)))
        else:
            triangle_chance = 0
        
        rand = random.random()
        
        # Determine enemy type based on weighted probabilities
        if rand < pentagon_chance:
            enemy = PentagonEnemy(self.canvas, x, y, ENEMY_SIZE)
        elif rand < pentagon_chance + triangle_chance:
            enemy = TriangleEnemy(self.canvas, x, y, ENEMY_SIZE)
        else:
            enemy = Enemy(self.canvas, x, y, ENEMY_SIZE)
        
        self.enemies.append(enemy)
    
    def get_current_respawn_interval(self):
        """Calculate respawn interval based on time played."""
        minutes_played = self.game_time_ms / 60000
        interval = RESPAWN_INTERVAL - (minutes_played * 1000 * RESPAWN_BATCH_SCALE)
        return max(interval, RESPAWN_INTERVAL_MIN)
    
    def respawn_enemies(self, count):
        """Spawn 'count' new enemies at random positions with level-based scaling."""
        # Increase max enemies based on level (not just time played)
        base_max = MAX_ENEMY_COUNT
        level_scaling = 1 + (0.05 * self.level)  # 5% increase per level (reduced from 10%)
        max_enemies = int(base_max * level_scaling)
        
        # Also increase respawn count with level
        scaled_count = int(count * (1 + 0.025 * self.level))  # 2.5% increase per level (reduced from 5%)
        
        if len(self.enemies) >= max_enemies:
            return
        
        for _ in range(scaled_count):
            if len(self.enemies) >= max_enemies:
                break
            
            # Spawn enemies outside the screen bounds (same as initial spawn)
            margin = 200
            side = random.choice(['top', 'bottom', 'left', 'right'])
            
            if side == 'top':
                x = random.randint(-ENEMY_SIZE, WIDTH)
                y = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
            elif side == 'bottom':
                x = random.randint(-ENEMY_SIZE, WIDTH)
                y = random.randint(HEIGHT, HEIGHT + margin)
            elif side == 'left':
                x = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
                y = random.randint(-ENEMY_SIZE, HEIGHT)
            else:  # right
                x = random.randint(WIDTH, WIDTH + margin)
                y = random.randint(-ENEMY_SIZE, HEIGHT)
            
            self._spawn_enemy_by_level(x, y)

    def on_respawn_timer(self):
        """Called when it's time to spawn a new batch of enemies."""
        if not self.paused:
            self.respawn_enemies(RESPAWN_BATCH_SIZE)
        # Schedule next respawn with dynamic interval
        interval = int(self.get_current_respawn_interval())
        self.root.after(interval, self.on_respawn_timer)

    def get_attack_direction(self):
        """Calculate the angle from the player to the mouse cursor."""
        px, py = self.player.get_center()
        mouse_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        mouse_y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        dx = mouse_x - px
        dy = mouse_y - py
        angle = math.atan2(dy, dx)
        return angle

    def on_canvas_click(self, event):
        """Handle canvas clicks - routes to appropriate menu or attack."""
        try:
            # If game over screen is showing, handle restart button click
            if self.game_over_active:
                if self.game_over_restart_btn is not None:
                    coords = self.canvas.coords(self.game_over_restart_btn)
                    if coords and len(coords) >= 4:
                        x1, y1, x2, y2 = coords
                        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                            self.restart_game()
                            return
                return  # Click outside button does nothing
            
            # If upgrade menu is open, only handle upgrade menu clicks
            if self.menu_manager.upgrade_menu_active:
                self.menu_manager.handle_upgrade_menu_click(event)
                return
            
            # If dev menu is open, only handle dev menu clicks
            if self.menu_manager.dev_menu_active:
                self.menu_manager.handle_dev_menu_click(event)
                return
            
            # If pause menu is open, only handle pause menu clicks
            if self.paused:
                self.menu_manager.handle_pause_menu_click(event)
                return
            
            # Otherwise, attack
            self.attack()
        except Exception as e:
            import sys
            sys.stdout.write(f"[ERROR] FATAL ERROR IN CLICK HANDLER: {e}\n")
            sys.stdout.flush()
            import traceback
            traceback.print_exc()
            sys.stdout.flush()

    def show_upgrade_menu(self):
        """Display upgrade selection menu with three random choices."""
        self.menu_manager.show_upgrade_menu()

    def on_upgrade_selection(self, upgrade_key):
        """Handle upgrade selection."""
        self.menu_manager.on_upgrade_selection(upgrade_key)

    def close_upgrade_menu(self):
        """Close the upgrade menu."""
        self.menu_manager.close_upgrade_menu()

    def show_pause_menu(self):
        """Display pause menu overlay on the game canvas."""
        self.menu_manager.show_pause_menu()

    def hide_pause_menu(self):
        """Hide the pause menu and resume the game."""
        self.menu_manager.hide_pause_menu()

    def quit_game(self):
        """Close the game window and exit."""
        self.menu_manager.quit_game()

    def toggle_sound(self):
        """Toggle sound on/off and refresh pause menu to show new state."""
        self.menu_manager.toggle_sound()

    def toggle_music(self):
        """Toggle music on/off and refresh pause menu to show new state."""
        self.menu_manager.toggle_music()

    def toggle_keyboard_layout(self):
        """Toggle between Dvorak and QWERTY keyboard layouts and refresh pause menu."""
        self.menu_manager.toggle_keyboard_layout()

    def show_dev_menu(self):
        """Display the developer testing menu."""
        self.menu_manager.show_dev_menu()

    def _handle_dev_menu_action(self, action):
        """Handle dev menu button actions."""
        self.menu_manager._handle_dev_menu_action(action)

    def close_dev_menu(self):
        """Close the dev menu and return to pause menu."""
        self.menu_manager.close_dev_menu()

    def on_pause_menu_click(self, event):
        """Handle pause menu button clicks."""
        self.menu_manager.handle_pause_menu_click(event)

    def restart_game(self):
        """Restart the game, resetting player, enemies, and score."""
        # First, ensure pause/game over states are reset before stopping music
        self.paused = False
        self.game_over_active = False
        
        # Reset menu manager state
        self.menu_manager = MenuManager(self)
        
        # Now stop background music safely
        stop_background_music()
        
        # Clear the canvas
        self.canvas.delete('all')
        
        # Redraw starfield background
        self._draw_starfield()
        
        self.score = 0
        self.game_time_ms = 0
        self.dash_cooldown_counter = 0
        self.particles.clear()
        self.shards.clear()
        self.projectiles.clear()
        self.black_holes.clear()  # Also clear black holes
        self.minions.clear()  # Clear minions
        self.minion_projectiles.clear()  # Clear minion projectiles
        self.active_upgrades = []
        self.computed_weapon_stats = self.compute_weapon_stats()
        self.xp = 0
        self.level = 0
        self.xp_for_next_level = 10
        self.player = Player(self.canvas, WIDTH//2, HEIGHT//2, PLAYER_SIZE)
        self.player.game = self  # Give player reference to game instance for shield pushback
        self.enemies = []
        self.spawn_enemies()
        self.score_text = self.canvas.create_text(WIDTH//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.level_text = self.canvas.create_text(WIDTH//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(WIDTH//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")
        
        # Restart background music
        start_background_music(self)

    def on_key_press(self, event):
        """Handle key press events for movement and actions."""
        # Check for special keys FIRST (before movement keys)
        if event.keysym == 'space':  # Spacebar (toggle auto-fire)
            self.auto_fire_enabled = not self.auto_fire_enabled
            print(f"[ACTION] Auto-fire {'ENABLED' if self.auto_fire_enabled else 'DISABLED'}")
            return
        elif event.keysym == 'Escape':
            # If dev menu is open, close it
            if self.menu_manager.dev_menu_active:
                self.close_dev_menu()
            # If pause menu is open, close it (resume game)
            elif self.paused:
                self.hide_pause_menu()
            # Otherwise, open pause menu
            else:
                self.show_pause_menu()
            return
        
        # Use keysyms for layout-independent controls
        # Map keysyms to directions - supports arrow keys, WASD, and Dvorak
        keysym_map = {
            # Arrow keys (universal)
            'Up': 'up',
            'Down': 'down',
            'Left': 'left',
            'Right': 'right',
            # QWERTY
            'w': 'up',
            's': 'down',
            'a': 'left',
            'd': 'right',
            # Dvorak (physical key positions map to WASD positions)
            'comma': 'up',      # Dvorak ',' key is where WASD 'w' is
            'a': 'left',        # Dvorak 'a' is same position as QWERTY
            'o': 'down',        # Dvorak 'o' key is where WASD 's' is
            'e': 'right',       # Dvorak 'e' key is where WASD 'd' is
        }
        
        if event.keysym in keysym_map:
            self.pressed_keys.add(keysym_map[event.keysym])

    def on_key_release(self, event):
        """Handle key release events for movement."""
        # Use keysyms for layout-independent controls
        keysym_map = {
            # Arrow keys (universal)
            'Up': 'up',
            'Down': 'down',
            'Left': 'left',
            'Right': 'right',
            # QWERTY
            'w': 'up',
            's': 'down',
            'a': 'left',
            'd': 'right',
            # Dvorak (physical key positions map to WASD positions)
            'comma': 'up',      # Dvorak ',' key is where WASD 'w' is
            'a': 'left',        # Dvorak 'a' is same position as QWERTY
            'o': 'down',        # Dvorak 'o' key is where WASD 's' is
            'e': 'right',       # Dvorak 'e' key is where WASD 'd' is
        }
        
        if event.keysym in keysym_map:
            self.pressed_keys.discard(keysym_map[event.keysym])
    


    def on_window_focus_out(self, event):
        """Pause game when window loses focus."""
        if not self.paused and not self.game_over_active:
            self.show_pause_menu()

    def on_window_focus_in(self, event):
        """Optional: could resume game when window regains focus, but keeping paused is safer."""
        pass

    def update(self):
        """Main game loop: update movement, enemies, and schedule next frame."""
        if self.paused:
            self.root.after(50, self.update)
            return
        
        try:
            # Track time played
            self.game_time_ms += 50
            
            # Update attack cooldown
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 50
            
            # Auto-fire if enabled and cooldown is ready
            if self.auto_fire_enabled and self.attack_cooldown <= 0:
                self.attack()
            
            self.handle_player_movement()
            self.move_enemies()
            self.check_player_collision()  # Check if enemies hit player
            self.update_particles()
            self.update_shards()
            self.update_projectiles()
            self.update_black_holes()
            self.update_minions()  # Update friendly minions
            self.update_minion_projectiles()  # Update minion projectiles
            self.update_ammo_orbs()
            self.update_dash_cooldown()
            self.update_shield_cooldown()
        except Exception as e:
            sys.stdout.write(f"[UPDATE ERROR] Uncaught exception in update loop: {e}\n")
            import traceback
            sys.stdout.write(traceback.format_exc())
            sys.stdout.flush()
        
        self.root.after(50, self.update)

    def handle_player_movement(self):
        """Check pressed keys and apply acceleration accordingly."""
        accel_x, accel_y = 0, 0
        
        # Check direction keys (now layout-independent)
        if 'up' in self.pressed_keys:
            accel_y -= 1
        if 'down' in self.pressed_keys:
            accel_y += 1
        if 'left' in self.pressed_keys:
            accel_x -= 1
        if 'right' in self.pressed_keys:
            accel_x += 1
        
        # Always apply movement (even if accel is 0, friction will slow player)
        self.move_player(accel_x, accel_y)
        
        if accel_x != 0 or accel_y != 0:
            # Track movement direction for dash
            dist = math.hypot(accel_x, accel_y)
            self.last_move_dx = accel_x / dist
            self.last_move_dy = accel_y / dist

    def move_player(self, dx, dy):
        """Move the player by (dx, dy)."""
        self.player.move(dx, dy, 0, self.window_width, self.window_height)

    def create_death_poof(self, x, y):
        """Create a poof particle effect at (x, y)."""
        for i in range(PARTICLE_COUNT):
            angle = (2 * math.pi * i) / PARTICLE_COUNT
            speed = 3
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            particle = Particle(self.canvas, x, y, vx, vy, PARTICLE_LIFE)
            self.particles.append(particle)

    def create_shrapnel(self, x, y, proj_vx, proj_vy, shrapnel_level):
        """Create shrapnel shards at (x, y) in a cone from projectile direction."""
        shard_count = 1 + shrapnel_level  # 2 shards for level 1, 3 for level 2, etc
        
        # Get the projectile's direction
        proj_angle = math.atan2(proj_vy, proj_vx)
        
        # Spread shards in a cone (60 degree spread)
        spread_angle = math.radians(60)
        start_angle = proj_angle - spread_angle / 2
        
        # Play shrapnel sound
        play_beep_async(800, 25, self)
        
        # Check if explosive shrapnel upgrade is active
        explosive = self.computed_weapon_stats.get('explosive_shrapnel', 0) > 0
        
        for i in range(shard_count):
            # Distribute angles across the cone
            angle = start_angle + (spread_angle * i / (shard_count - 1)) if shard_count > 1 else proj_angle
            
            # Shard speed
            shard_speed = 8
            vx = math.cos(angle) * shard_speed
            vy = math.sin(angle) * shard_speed
            
            shard = Shard(self.canvas, x, y, vx, vy, self, lifetime=1000, explosive=explosive)  # 1000ms = 1 second
            self.shards.append(shard)
    
    def create_explosive_shrapnel(self, x, y):
        """Create an explosion of shrapnel shards in all directions."""
        # Scale explosion size based on upgrade level
        explosive_level = self.computed_weapon_stats.get('explosive_shrapnel', 0)
        shard_count = 3 + (2 * explosive_level)  # 5 at level 1, 7 at level 2, 9 at level 3, etc (small poof to bigger)
        shard_speed = 4 + (1.5 * explosive_level)  # 5.5 at level 1, 7 at level 2, 8.5 at level 3, etc
        
        # Play deep boom sound
        play_beep_async(120, 200, self)  # Low frequency (120Hz), long duration (200ms)
        
        for i in range(shard_count):
            # Distribute angles evenly in all directions
            angle = (2 * math.pi * i) / shard_count
            
            vx = math.cos(angle) * shard_speed
            vy = math.sin(angle) * shard_speed
            
            shard = Shard(self.canvas, x, y, vx, vy, self, lifetime=1000, explosive=False)
            self.shards.append(shard)

    def _spawn_minion(self) -> None:
        """Spawn a new minion near the player."""
        px, py = self.player.get_center()
        
        # Spawn minion at a random position around the player
        spawn_distance = 50
        angle = random.random() * 2 * math.pi
        minion_x = px + math.cos(angle) * spawn_distance
        minion_y = py + math.sin(angle) * spawn_distance
        
        # Clamp to screen bounds
        minion_x = max(15, min(self.window_width - 15, minion_x))
        minion_y = max(15, min(self.window_height - 15, minion_y))
        
        # Create and add minion
        minion = Minion(self.canvas, minion_x, minion_y, self)
        self.minions.append(minion)
        
        print(f"[ACTION] Minion summoned (total: {len(self.minions)})")

    def update_particles(self):
        """Update all particles and remove dead ones."""
        alive = []
        for p in self.particles:
            if p.update():
                alive.append(p)
            else:
                p.cleanup()
        self.particles = alive

    def update_shards(self):
        """Update all shards and remove expired ones."""
        alive = []
        for s in self.shards:
            if s.update():
                alive.append(s)
            else:
                s.cleanup()
        self.shards = alive

    def update_projectiles(self):
        """Update all projectiles and remove dead ones."""
        alive_projectiles = []
        for p in self.projectiles:
            if p.update():
                alive_projectiles.append(p)
            else:
                p.cleanup()
        self.projectiles = alive_projectiles

    def update_black_holes(self):
        """Update all active black holes from weapon upgrades and remove expired ones."""
        alive_black_holes = []
        for black_hole in self.black_holes:
            if black_hole.update():
                alive_black_holes.append(black_hole)
            else:
                black_hole.cleanup()
        self.black_holes = alive_black_holes

    def update_minions(self) -> None:
        """Update all minions and remove dead ones."""
        alive_minions = []
        for minion in self.minions:
            if minion.update():
                alive_minions.append(minion)
            else:
                minion.cleanup()
        self.minions = alive_minions

    def update_minion_projectiles(self) -> None:
        """Update all minion projectiles and remove dead ones."""
        alive_projectiles = []
        for projectile in self.minion_projectiles:
            if projectile.update():
                alive_projectiles.append(projectile)
            else:
                projectile.cleanup()
        self.minion_projectiles = alive_projectiles

    def update_dash_cooldown(self):
        """Update dash cooldown timer."""
        if self.dash_cooldown_counter > 0:
            self.dash_cooldown_counter -= 50
    
    def _update_player_shield(self):
        """Update player shield based on shield upgrade."""
        shield_level = self.computed_weapon_stats.get('shield', 0)
        shield_level = min(shield_level, 3)  # Cap at level 3
        
        if shield_level > 0:
            # Update player's shield level
            old_level = self.player.shield_level
            self.player.shield_level = shield_level
            
            # If shield level changed and shield is active, recreate the rings
            if self.player.shield_active and old_level != shield_level:
                # Delete old rings
                for ring in self.player.shield_rings:
                    if ring is not None:
                        self.canvas.delete(ring)
                # Create new rings with updated level
                self.player.shield_rings = []
                for i in range(self.player.shield_level):
                    shield_radius = self.player.size // 2 + 15 + (i * 12)
                    ring = self.canvas.create_oval(
                        self.player.x - shield_radius, self.player.y - shield_radius,
                        self.player.x + shield_radius, self.player.y + shield_radius,
                        outline='cyan', width=2
                    )
                    self.player.shield_rings.append(ring)
            elif not self.player.shield_active:
                # Activate shield if not already active
                self.player.activate_shield()

    def update_shield_cooldown(self):
        """Update shield cooldown timer."""
        if self.player is not None:
            shield_level = self.computed_weapon_stats.get('shield', 0)
            if shield_level > 0:
                # Update shield cooldown
                self.player.update_shield(50)  # 50ms per frame

    def update_ammo_orbs(self):
        """Update ammo orbs to orbit around the player."""
        # Fixed ammo value - always 1 orb
        max_ammo = 1
        
        # Calculate available ammo - only show orb when there are no main projectiles actively in combat
        # Mini-forks don't count as active ammo usage
        has_active_main_projectile = any(p for p in self.projectiles if not p.is_mini_fork and not p.returning)
        available_ammo = 0 if has_active_main_projectile else 1
        
        # Remove old orbs
        for orb_id in self.ammo_orbs:
            try:
                self.canvas.delete(orb_id)
            except tk.TclError:
                pass  # Already deleted
        self.ammo_orbs = []
        
        # Update rotation angle
        self.ammo_rotation = (self.ammo_rotation + 6) % 360  # Rotate 6 degrees per frame
        rotation_rad = math.radians(self.ammo_rotation)
        
        # Draw ammo orbs - show all slots, but only fill available ones
        px, py = self.player.get_center()
        orbit_radius = 35
        
        for i in range(max_ammo):
            angle = rotation_rad + (2 * math.pi * i / max_ammo)
            orb_x = px + orbit_radius * math.cos(angle)
            orb_y = py + orbit_radius * math.sin(angle)
            
            # Strong collision avoidance - push away from all nearby enemies
            for enemy in self.enemies:
                ex, ey = enemy.get_position()
                ex_center = ex + ENEMY_SIZE // 2
                ey_center = ey + ENEMY_SIZE // 2
                
                # Distance from orb to enemy center
                dx = orb_x - ex_center
                dy = orb_y - ey_center
                dist = math.hypot(dx, dy)
                
                # Larger avoidance radius - push if within 40 pixels of enemy center
                min_distance = 40
                if dist < min_distance and dist > 0:
                    # Strongly push the orb away from the enemy
                    push_distance = min_distance - dist + 10  # +10 to give significant buffer
                    norm_dx = dx / dist
                    norm_dy = dy / dist
                    orb_x += norm_dx * push_distance
                    orb_y += norm_dy * push_distance
            
            # Only draw orb if it's available (not fired)
            if i < available_ammo:
                # Draw filled orb as a yellow circle matching the projectile (8x8 pixels)
                orb_id = self.canvas.create_oval(
                    orb_x - 4, orb_y - 4,
                    orb_x + 4, orb_y + 4,
                    fill='yellow'
                )
                self.ammo_orbs.append(orb_id)

    def move_enemies(self):
        """Move all enemies towards the player."""
        px, py = self.player.get_center()
        for enemy in self.enemies:
            # Different speeds for different enemy types
            if isinstance(enemy, PentagonEnemy):
                enemy.move_towards(px, py, speed=3)  # Pentagons move slower
            elif isinstance(enemy, TriangleEnemy):
                enemy.move_towards(px, py, speed=4)  # Triangles medium speed
            else:  # CircleEnemy
                enemy.move_towards(px, py, speed=5)  # Circles normal speed

    def check_player_collision(self) -> None:
        """Check if any enemy collides with player and deal damage."""
        px, py = self.player.get_center()
        for enemy in self.enemies:
            ex, ey = enemy.get_position()
            
            # Check distance between player and enemy
            if not CollisionDetector.check_player_enemy_collision(px, py, ex, ey):
                # No collision, update immunity timer and continue
                if enemy.shield_immunity > 0:
                    enemy.shield_immunity -= 1
                continue
            
            # Decrease immunity timer
            if enemy.shield_immunity > 0:
                enemy.shield_immunity -= 1
            
            # Skip if enemy is currently immune
            if enemy.shield_immunity > 0:
                continue
            
            # Collision detected - handle it
            if self.player.shield_active and self.player.shield_rings:
                # Shield blocks the damage (only if there are rings)
                print(f"[ACTION] Shield blocked enemy hit! Rings remaining: {len(self.player.shield_rings)}")
                play_beep_async(1200, 50, self)  # Blip sound on shield hit
                self.player.deactivate_shield(enemy=enemy)
                enemy.shield_immunity = 10  # Prevent re-collision for 10 frames
            else:
                # No shield - deal damage to player
                print(f"[ACTION] Enemy hit player! Health: {self.player.health} -> {self.player.health - 1}")
                self.player.health -= 1
                if self.player.health <= 0:
                    print(f"[ACTION] Player died!")
                    self.game_over()
            return  # Only take damage once per frame

    def game_over(self):
        """Handle game over - show game over screen."""
        self.paused = True
        self.game_over_active = True  # Flag to indicate game over screen is active
        
        # Calculate overlay size based on actual content
        # Title + Score + Button with padding: 60 + 40 + 50 + 60 = 210 pixels high
        overlay_width = 400
        overlay_height = 210
        overlay_x = (self.window_width - overlay_width) // 2
        overlay_y = (self.window_height - overlay_height) // 2
        
        # Background
        self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a1a', outline='red', width=3
        )
        
        # Game Over text
        self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 30,
            text='GAME OVER',
            fill='red',
            font=('Arial', 48, 'bold')
        )
        
        # Score text
        self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 80,
            text=f'Final Score: {self.score}',
            fill='yellow',
            font=('Arial', 24)
        )
        
        # Restart button
        btn_width = 200
        btn_height = 50
        btn_x = overlay_x + (overlay_width - btn_width) // 2
        btn_y = overlay_y + 140
        
        self.game_over_restart_btn = self.canvas.create_rectangle(
            btn_x, btn_y,
            btn_x + btn_width, btn_y + btn_height,
            fill='green', outline='white', width=2
        )
        self.canvas.create_text(
            overlay_x + overlay_width // 2, btn_y + 25,
            text='Restart',
            fill='white',
            font=('Arial', 20, 'bold')
        )

    def attack(self):
        """Launch a projectile if none are active."""
        # Make sure we're not in a menu
        if self.paused or self.menu_manager.upgrade_menu_active:
            return
        
        # Check if there's a main projectile active (mini-forks don't block firing)
        has_main_projectile = any(p for p in self.projectiles if not p.is_mini_fork)
        if has_main_projectile:  # Can't fire if a main projectile is already active
            return
        
        # Play attack sound asynchronously
        print(f"[ACTION] Player attacking - firing projectile")
        # Use unthrottled beep so rapid fire sounds clean, not crunchy
        play_beep_unthrottled(400, 50, self)
        
        center_x, center_y = self.player.get_center()
        angle = self.get_attack_direction()
        
        # Get weapon stats
        projectile_speed = self.computed_weapon_stats['projectile_speed']
        
        vx = math.cos(angle) * projectile_speed
        vy = math.sin(angle) * projectile_speed
        projectile = Projectile(self.canvas, center_x, center_y, vx, vy, self)
        # Set homing from weapon stats (0 by default, 0.15 if Homing upgrade owned)
        projectile.homing_strength = self.computed_weapon_stats['homing']
        self.projectiles.append(projectile)
        
        # Set attack cooldown (500ms from PROJECTILE_RETURN_TIME_MS)
        self.attack_cooldown = PROJECTILE_RETURN_TIME_MS

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Top Down Game Prototype')
    # Maximize window
    root.state('zoomed')
    # Get screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    # Update global WIDTH and HEIGHT
    WIDTH = screen_width
    HEIGHT = screen_height
    game = Game(root)
    root.mainloop()
