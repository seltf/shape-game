import tkinter as tk
import random
import math
import threading
import os
import sys
from typing import List, Dict, Any, Optional, Tuple

# Import from separate modules
from constants import *
from constants import GameState
from audio import play_beep_async, play_beep_unthrottled, start_background_music, stop_background_music
from entities import BlackHole, Player, Enemy, TriangleEnemy, PentagonEnemy, HexagonEnemy, BossEnemy, Particle, Shard, Projectile, Minion, MinionProjectile
from menus import MenuManager
from collision import CollisionDetector, PlayerCollisionHandler


class Game:
    """
    Main game class. Handles game state, input, rendering, and logic.
    """
    # Keyboard layout map - layout-independent controls
    # Maps both keysym names and characters to support cross-platform
    KEYSYM_MAP = {
        # Arrow keys
        'Up': 'up', 'Down': 'down', 'Left': 'left', 'Right': 'right',
        # QWERTY WASD
        'w': 'up', 'W': 'up',
        's': 'down', 'S': 'down', 
        'a': 'left', 'A': 'left',
        'd': 'right', 'D': 'right',
        # Dvorak ,AOE (physical WASD positions on Dvorak layout)
        ',': 'up',  # macOS sends character (physical W position)
        'comma': 'up',  # Windows sends keysym name (physical W position)
        'o': 'down', 'O': 'down',  # Physical S position on Dvorak
        # 'a' already mapped for left (same on both layouts)
        'e': 'right', 'E': 'right',  # Physical D position on Dvorak
    }
    
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
        self.version_text = self.canvas.create_text(10, self.window_height - 10, anchor='sw', fill='gray', font=('Arial', 10), text=f"v{VERSION}")
        self.player = Player(self.canvas, self.window_width//2, self.window_height//2, PLAYER_SIZE)
        self.player.game = self  # Give player reference to game instance for shield pushback
        
        self.enemies = []
        self.particles = []
        self.shards = []  # Track shrapnel shards
        self.projectiles = []
        self.minions = []  # Track friendly minions
        self.minion_projectiles = []  # Track minion projectiles
        self.game_time_ms = 0  # Track time played in milliseconds
        self.active_upgrades = []  # List of active upgrade keys
        self.computed_weapon_stats = self.compute_weapon_stats()  # Cache computed stats
        
        # Activate initial shield if shield upgrade is owned
        self._update_player_shield()
        
        self.last_move_dx = 1  # Track last movement direction
        self.last_move_dy = 0
        self.xp = 0  # Current XP
        self.level = 0  # Current player level (for upgrades)
        self.xp_for_next_level = 10  # XP needed for next level
        self.level_text = self.canvas.create_text(self.window_width//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(self.window_width//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")

        # Game level progression (separate from player level - for enemy difficulty)
        self.game_level = 1  # Current game level (wave progression)
        self.game_level_text = self.canvas.create_text(self.window_width//2, 130, anchor='n', fill='orange', font=('Arial', 16), text=f"Game Level: {self.game_level}")
        self.current_wave = 0  # Current wave within the game level
        self.wave_timer = 0  # Time until next wave spawns (milliseconds)
        self.level_rest_timer = 0  # Time remaining in rest period between levels (0 = not resting)
        self.is_resting = False  # Whether we're in a rest period between levels
        
        # Boss fight tracking
        self.boss_fight_active = False  # Whether boss fight is happening
        self.current_boss = None  # Reference to current boss enemy
        self.boss_announcement_timer = 0  # Display boss announcement
        self.boss_announcement_text = None  # Canvas text ID for boss announcement
        self.boss_minion_spawn_timer = 0  # Timer for boss minion spawns

        # Timer display
        self.timer_text = self.canvas.create_text(self.window_width - 80, 30, anchor='n', fill='white', font=('Arial', 16), text="Time: 0:00")

        # Ability system

        self.black_holes = []  # List of active black holes from weapon upgrades
        
        # Performance optimization: spatial partitioning grid
        self.spatial_grid = {}  # Dict of (grid_x, grid_y) -> list of enemies
        self.grid_needs_rebuild = True  # Flag to rebuild grid when enemies move
        
        # Performance optimization: object pooling for particles
        self.particle_pool = []  # Reusable particle objects
        
        # Performance monitoring
        self.frame_count = 0
        self.fps_timer = 0
        self.current_fps = 0
        self.perf_text = None
        if PERFORMANCE_MONITORING:
            self.perf_text = self.canvas.create_text(
                10, 30, anchor='nw', fill='lime', 
                font=('Courier', 10), text="FPS: 0"
            )
        
        # Initialize menu manager
        self.menu_manager = MenuManager(self)
        
        # Game state machine (replaces scattered boolean flags)
        self._game_state = GameState.MAIN_MENU
        self.game_started = False  # Track if game has been started
        
        # Show main menu instead of starting game directly
        self.show_main_menu()
        
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.root.bind('<FocusOut>', self.on_window_focus_out)
        self.root.bind('<FocusIn>', self.on_window_focus_in)
        self.pressed_keys = set()
        self.ammo_orbs = []  # Track ammo orb canvas items
        self.ammo_rotation = 0  # Angle for orbiting ammo orbs
        self.sound_enabled = True  # Sound effects enabled by default
        self.music_enabled = False  # Background music disabled by default
        self.keyboard_layout = 'dvorak'  # 'dvorak' or 'qwerty'
        self.game_over_restart_btn = None  # Reference to restart button
        self.auto_fire_enabled = False  # Auto-fire toggle
        self.attack_cooldown = 0  # Milliseconds until next attack available (after firing)
        
        # Start background music
        start_background_music(self)
        
        # Schedule render loop at 120 FPS (~8ms) and logic loop at 50 FPS (20ms)
        self.root.after(8, self.update)
        self.root.after(20, self.schedule_logic_updates)
        self.interpolation_factor = 0.0  # Track time within logic frame for smooth animation

    # ========================================================================
    # PERFORMANCE OPTIMIZATION METHODS
    # ========================================================================
    
    def _get_grid_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Get grid cell coordinates for a position."""
        from constants import SPATIAL_GRID_CELL_SIZE
        return (int(x // SPATIAL_GRID_CELL_SIZE), int(y // SPATIAL_GRID_CELL_SIZE))
    
    def _rebuild_spatial_grid(self) -> None:
        """Rebuild spatial partitioning grid for collision detection."""
        self.spatial_grid.clear()
        for enemy in self.enemies:
            ex, ey = enemy.get_position()
            cell = self._get_grid_cell(ex + ENEMY_SIZE_HALF, ey + ENEMY_SIZE_HALF)
            if cell not in self.spatial_grid:
                self.spatial_grid[cell] = []
            self.spatial_grid[cell].append(enemy)
        self.grid_needs_rebuild = False
    
    def _get_nearby_enemies(self, x: float, y: float, radius: float) -> List[Any]:
        """Get enemies near a position using spatial grid (much faster than checking all)."""
        from constants import SPATIAL_GRID_CELL_SIZE
        if self.grid_needs_rebuild:
            self._rebuild_spatial_grid()
        
        nearby = []
        cell = self._get_grid_cell(x, y)
        
        # Check this cell and adjacent cells
        check_range = int(radius // SPATIAL_GRID_CELL_SIZE) + 1
        for dx in range(-check_range, check_range + 1):
            for dy in range(-check_range, check_range + 1):
                check_cell = (cell[0] + dx, cell[1] + dy)
                if check_cell in self.spatial_grid:
                    nearby.extend(self.spatial_grid[check_cell])
        
        return nearby
    
    def _get_particle_from_pool(self) -> Optional[Any]:
        """Get a particle from the object pool, or None if pool is empty."""
        if self.particle_pool:
            return self.particle_pool.pop()
        return None
    
    def _return_particle_to_pool(self, particle: Any) -> None:
        """Return a particle to the object pool for reuse."""
        from constants import MAX_POOLED_PARTICLES
        if len(self.particle_pool) < MAX_POOLED_PARTICLES:
            # Reset particle state for reuse
            particle.life = 0
            self.particle_pool.append(particle)

    # ========================================================================
    # STATE MACHINE PROPERTIES AND METHODS
    # ========================================================================
    
    @property
    def game_state(self) -> GameState:
        """Get current game state."""
        return self._game_state
    
    @property
    def paused(self) -> bool:
        """Check if game is paused (for backward compatibility)."""
        return self._game_state == GameState.PAUSED
    
    @property
    def main_menu_active(self) -> bool:
        """Check if main menu is active (for backward compatibility)."""
        return self._game_state == GameState.MAIN_MENU
    
    @property
    def game_over_active(self) -> bool:
        """Check if game over screen is active (for backward compatibility)."""
        return self._game_state == GameState.GAME_OVER
    
    def set_state(self, new_state: GameState) -> None:
        """Set game state with validation and side effects.
        
        Args:
            new_state: The new state to transition to
        """
        old_state = self._game_state
        
        # Validate state transition (you can add more validation here)
        if old_state == new_state:
            return  # No change needed
        
        print(f"[STATE] Transitioning from {old_state.name} to {new_state.name}")
        
        # Apply state change
        self._game_state = new_state
        
        # Handle state-specific side effects
        if new_state == GameState.PLAYING:
            # Clear any menu elements
            if old_state in [GameState.PAUSED, GameState.UPGRADE_MENU, GameState.DEV_MENU]:
                self.pressed_keys.clear()  # Clear stuck keys
        elif new_state == GameState.PAUSED:
            # Ensure game loop is not updating
            pass
        elif new_state == GameState.GAME_OVER:
            # Stop background music on game over
            stop_background_music()

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
                elif key in ['projectile_speed', 'return_speed', 'homing', 'bounces', 'shrapnel', 'explosive_shrapnel', 'chain_lightning', 'black_hole', 'shield']:
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

    def kill_enemy(self, enemy) -> None:
        """Remove an enemy from the game and award XP based on enemy type."""
        if enemy not in self.enemies:
            return
        
        # Award XP based on enemy type
        if isinstance(enemy, TriangleEnemy):
            xp_reward = 1
        elif isinstance(enemy, PentagonEnemy):
            xp_reward = 3
        elif isinstance(enemy, HexagonEnemy):
            xp_reward = 4
        else:  # Square/Circle enemies and others
            xp_reward = 2
        
        # Remove from game
        self.enemies.remove(enemy)
        self.canvas.delete(enemy.rect)
        
        # Award XP
        self.add_xp(xp_reward)
        
        # Update score
        self.score += 1
        self.canvas.itemconfig(self.score_text, text=str(self.score))

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

    def start_game_level(self) -> None:
        """Initialize a new game level with wave progression."""
        # Check if this is the boss fight at level 21
        if self.game_level == 21:
            self._start_boss_fight()
            return
        
        # Don't clear enemies - let previous level's enemies stay alive
        # They'll be killed by player or move off screen naturally
        self.current_wave = 0
        self.wave_timer = 0
        self.is_resting = False
        self.level_rest_timer = 0
        self._spawn_next_wave()
    
    def _spawn_next_wave(self) -> None:
        """Spawn the next wave of enemies for the current game level."""
        # Check if level is defined in GAME_LEVEL_WAVES
        if self.game_level not in GAME_LEVEL_WAVES:
            # Auto-generate level for levels beyond 20
            self._spawn_next_wave_autogenerated()
            return
        
        waves = GAME_LEVEL_WAVES[self.game_level]
        
        if self.current_wave >= len(waves):
            # All waves completed, move to rest period then next level
            print(f"[LEVEL COMPLETE] Level {self.game_level} - all {len(waves)} waves completed, entering rest period")
            self.is_resting = True
            self.level_rest_timer = LEVEL_REST_DURATION
            return
        
        wave_info = waves[self.current_wave]
        enemy_type, count, spawn_delay = wave_info
        
        print(f"[WAVE SPAWN] Level {self.game_level}, Wave {self.current_wave + 1}: Spawning {count} {enemy_type} enemies (total enemies: {len(self.enemies)})")
        
        # Enforce MAX_ENEMY_COUNT cap
        available_slots = MAX_ENEMY_COUNT - len(self.enemies)
        actual_count = min(count, available_slots)
        
        if actual_count < count:
            print(f"[WAVE SPAWN] Capped spawn at {actual_count}/{count} enemies due to MAX_ENEMY_COUNT ({MAX_ENEMY_COUNT})")
        
        # Spawn enemies based on type
        for _ in range(actual_count):
            x, y = self._get_spawn_position()
            self._spawn_enemy_by_type(x, y, enemy_type)
        
        self.current_wave += 1
        
        # Set timer to WAVE_SPAWN_INTERVAL for next wave (waves spawn continuously regardless of alive enemies)
        self.wave_timer = WAVE_SPAWN_INTERVAL
        print(f"[WAVE SPAWN] Wave spawned. Total enemies now: {len(self.enemies)}, next wave in 5s")
    
    def _spawn_next_wave_autogenerated(self) -> None:
        """Generate and spawn a wave for levels beyond 20."""
        # Auto-generate difficulty based on game level
        # More enemies, harder types as level increases
        num_waves = min(6 + (self.game_level // 10), 10)  # 6-10 waves per level
        num_waves_per_level = max(6, num_waves - self.current_wave)
        
        if self.current_wave >= num_waves_per_level:
            # Level complete
            self.is_resting = True
            self.level_rest_timer = LEVEL_REST_DURATION
            return
        
        # Determine enemy types and count based on level - scaling for crazy hoard feel
        total_enemies = 15 + (self.game_level - 20) * 2  # More enemies as level increases
        pentagon_ratio = min(0.5, 0.02 * (self.game_level - 20) + 0.1)
        triangle_ratio = min(0.7, 0.3 + (0.02 * (self.game_level - 20)))
        
        pentagons = int(total_enemies * pentagon_ratio)
        triangles = int(total_enemies * triangle_ratio * (1 - pentagon_ratio))
        basics = total_enemies - pentagons - triangles
        
        # Enforce MAX_ENEMY_COUNT cap
        available_slots = MAX_ENEMY_COUNT - len(self.enemies)
        actual_total = min(total_enemies, available_slots)
        
        if actual_total < total_enemies:
            # Scale down proportionally
            scale = actual_total / total_enemies
            basics = int(basics * scale)
            triangles = int(triangles * scale)
            pentagons = int(pentagons * scale)
            print(f"[WAVE SPAWN] Scaled autogen spawn to {actual_total}/{total_enemies} enemies due to MAX_ENEMY_COUNT")
        
        # Spawn enemies
        for _ in range(basics):
            x, y = self._get_spawn_position()
            self._spawn_enemy_by_type(x, y, 'square')
        for _ in range(triangles):
            x, y = self._get_spawn_position()
            self._spawn_enemy_by_type(x, y, 'triangle')
        for _ in range(pentagons):
            x, y = self._get_spawn_position()
            self._spawn_enemy_by_type(x, y, 'pentagon')
        
        self.current_wave += 1
        self.wave_timer = WAVE_SPAWN_INTERVAL  # Use constant for wave spawn timing
    
    def _start_boss_fight(self) -> None:
        """Initialize the boss fight at level 21."""
        print("[BOSS] ===== BOSS FIGHT INITIATED =====")
        self.boss_fight_active = True
        self.boss_announcement_timer = 3000  # Display announcement for 3 seconds
        self.boss_minion_spawn_timer = 5000  # First minion wave after 5 seconds
        
        # Spawn boss in center of screen
        boss_x = self.window_width // 2 - ENEMY_SIZE // 2
        boss_y = self.window_height // 2 - ENEMY_SIZE // 2
        self.current_boss = BossEnemy(self.canvas, boss_x, boss_y, ENEMY_SIZE)
        self.enemies.append(self.current_boss)
        
        # Clear existing waves/enemies for clean boss fight
        for enemy in self.enemies[:-1]:  # Keep only the boss
            self.canvas.delete(enemy.rect)
        self.enemies = [self.current_boss]
        
        print(f"[BOSS] Boss spawned with {self.current_boss.health} HP")
    
    def _update_boss_fight(self) -> None:
        """Update boss fight mechanics during combat."""
        if not self.boss_fight_active or not self.current_boss:
            return
        
        # Update boss announcement timer and display
        if self.boss_announcement_timer > 0:
            self.boss_announcement_timer -= 20
            
            # Create announcement text if it doesn't exist
            if self.boss_announcement_text is None:
                self.boss_announcement_text = self.canvas.create_text(
                    self.window_width // 2, self.window_height // 2 - 100,
                    text="⚠️ BOSS FIGHT ⚠️",
                    font=('Arial', 64, 'bold'), fill='red', anchor='center'
                )
            
            # Remove announcement when timer expires
            if self.boss_announcement_timer <= 0 and self.boss_announcement_text is not None:
                try:
                    self.canvas.delete(self.boss_announcement_text)
                except tk.TclError:
                    pass
                self.boss_announcement_text = None
        
        # Update minion spawn timer
        if self.boss_minion_spawn_timer > 0:
            self.boss_minion_spawn_timer -= 20
            if self.boss_minion_spawn_timer <= 0:
                self._spawn_boss_minions()
                # Schedule next minion wave in 8 seconds
                self.boss_minion_spawn_timer = 8000
        
        # Check if boss is defeated
        if self.current_boss not in self.enemies:
            self._boss_defeated()
    
    def _spawn_boss_minions(self) -> None:
        """Spawn minion waves for the boss fight."""
        if not self.current_boss:
            return
        
        phase = self.current_boss.get_phase()
        
        # Phase 1: Spawn 3 hexagons
        if phase == 1:
            minion_count = 3
            enemy_type = 'hexagon'
        # Phase 2: Spawn 4 hexagons and 2 pentagons
        elif phase == 2:
            minion_count = 4
            enemy_type = 'hexagon'
            # Spawn pentagons too
            for _ in range(2):
                x, y = self._get_spawn_position()
                self._spawn_enemy_by_type(x, y, 'pentagon')
        # Phase 3: Spawn 5 hexagons and 3 pentagons
        else:
            minion_count = 5
            enemy_type = 'hexagon'
            # Spawn pentagons too
            for _ in range(3):
                x, y = self._get_spawn_position()
                self._spawn_enemy_by_type(x, y, 'pentagon')
        
        # Spawn main minion wave
        for _ in range(minion_count):
            x, y = self._get_spawn_position()
            self._spawn_enemy_by_type(x, y, enemy_type)
        
        print(f"[BOSS] Minion wave spawned (Phase {phase}): {minion_count}x {enemy_type}")
    
    def _boss_defeated(self) -> None:
        """Handle boss defeat and victory."""
        print("[BOSS] ===== BOSS DEFEATED =====")
        self.boss_fight_active = False
        self.current_boss = None
        
        # Award major XP bonus
        xp_reward = 50
        self.add_xp(xp_reward)
        print(f"[BOSS] Victory! Awarded {xp_reward} XP")
        
        # Display victory message briefly
        victory_text = self.canvas.create_text(
            self.window_width // 2, self.window_height // 2,
            text="BOSS DEFEATED!\nGAME COMPLETE!",
            font=('Arial', 48, 'bold'), fill='gold', anchor='center'
        )
        
        # End game after 3 seconds
        self.canvas.after(3000, self.game_over)
    
    def _get_spawn_position(self) -> Tuple[int, int]:
        """Get a random spawn position outside screen bounds."""
        margin = 200
        side = random.choice(['top', 'bottom', 'left', 'right'])
        
        if side == 'top':
            x = random.randint(-ENEMY_SIZE, self.window_width)
            y = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
        elif side == 'bottom':
            x = random.randint(-ENEMY_SIZE, self.window_width)
            y = random.randint(self.window_height, self.window_height + margin)
        elif side == 'left':
            x = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
            y = random.randint(-ENEMY_SIZE, self.window_height)
        else:  # right
            x = random.randint(self.window_width, self.window_width + margin)
            y = random.randint(-ENEMY_SIZE, self.window_height)
        
        return x, y
    
    def _spawn_enemy_by_type(self, x: int, y: int, enemy_type: str) -> None:
        """Spawn a specific enemy type."""
        if enemy_type == 'triangle':
            enemy = TriangleEnemy(self.canvas, x, y, ENEMY_SIZE)
        elif enemy_type == 'pentagon':
            enemy = PentagonEnemy(self.canvas, x, y, ENEMY_SIZE)
        elif enemy_type == 'hexagon':
            enemy = HexagonEnemy(self.canvas, x, y, ENEMY_SIZE)
        elif enemy_type == 'boss':
            enemy = BossEnemy(self.canvas, x, y, ENEMY_SIZE)
        else:  # 'square' (4-sided, basic difficulty)
            enemy = Enemy(self.canvas, x, y, ENEMY_SIZE)
        
        self.enemies.append(enemy)
    
    def spawn_enemy(self, enemy_type: str) -> None:
        """Spawn a single enemy of the specified type at a random location around the player."""
        px, py = self.player.get_center()
        
        # Spawn at a random angle and distance around player
        angle = random.random() * 2 * math.pi
        distance = 100 + random.random() * 50  # 100-150 pixels away
        spawn_x = px + int(math.cos(angle) * distance)
        spawn_y = py + int(math.sin(angle) * distance)
        
        # Clamp to screen bounds
        spawn_x = max(ENEMY_SIZE_HALF, min(self.window_width - ENEMY_SIZE_HALF, spawn_x))
        spawn_y = max(ENEMY_SIZE_HALF, min(self.window_height - ENEMY_SIZE_HALF, spawn_y))
        
        self._spawn_enemy_by_type(spawn_x, spawn_y, enemy_type)


    
    def respawn_enemies(self, count: int) -> None:
        """Spawn a batch of enemies for dev/testing purposes."""
        # Respect MAX_ENEMY_COUNT cap
        available_slots = MAX_ENEMY_COUNT - len(self.enemies)
        actual_count = min(count, available_slots)
        
        if actual_count <= 0:
            print(f"[SPAWN] Cannot spawn enemies - at MAX_ENEMY_COUNT ({MAX_ENEMY_COUNT})")
            return
        
        print(f"[SPAWN] Spawning {actual_count} enemies (requested {count}, {len(self.enemies)} already exist)")
        
        for _ in range(actual_count):
            x, y = self._get_spawn_position()
            # Spawn mostly squares with some triangles for testing
            enemy_type = 'square' if random.random() > 0.3 else 'triangle'
            self._spawn_enemy_by_type(x, y, enemy_type)



    def update_game_level_progression(self) -> None:
        """Update wave timers and level progression."""
        # Handle rest period between levels
        if self.is_resting:
            # Only count down rest timer if all enemies are dead
            if len(self.enemies) == 0:
                self.level_rest_timer -= 20  # Decrement by logic tick (20ms)
                if self.level_rest_timer <= 0:
                    # Rest period complete, advance to next level
                    self.is_resting = False
                    self.game_level += 1
                    self.start_game_level()
            return
        
        # Decrement wave timer
        self.wave_timer -= 20  # Decrement by logic tick (20ms)
        
        # Wave timer expired - spawn next wave regardless of alive enemies
        if self.wave_timer <= 0:
            self._spawn_next_wave()
            # wave_timer is set in _spawn_next_wave() for next wave
        
        # Update game level display
        self.canvas.itemconfig(self.game_level_text, text=f"Game Level: {self.game_level}")

    def get_attack_direction(self):
        """Calculate the angle from the player to the mouse cursor."""
        px, py = self.player.get_center()
        mouse_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        mouse_y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        dx = mouse_x - px
        dy = mouse_y - py
        angle = math.atan2(dy, dx)
        return angle

    def format_time(self, milliseconds: int) -> str:
        """Convert milliseconds to MM:SS format."""
        total_seconds = milliseconds // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"

    def on_canvas_click(self, event):
        """Handle canvas clicks - routes to appropriate menu or attack."""
        try:
            # If main menu is active, any click starts the game
            if self.main_menu_active:
                self.start_game_from_menu()
                return
            
            # If main menu is active, any click starts the game
            if self.main_menu_active:
                self.start_game_from_menu()
                return
            
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
        except tk.TclError as e:
            print(f"[ERROR] Tkinter error in click handler: {e}")
            import traceback
            traceback.print_exc()
        except AttributeError as e:
            print(f"[ERROR] Attribute error in click handler (possibly deleted object): {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error in click handler: {e}")
            import traceback
            traceback.print_exc()

    def show_upgrade_menu(self):
        """Display upgrade selection menu with three random choices."""
        self.menu_manager.show_upgrade_menu()

    def on_upgrade_selection(self, upgrade_key):
        """Handle upgrade selection."""
        self.menu_manager.on_upgrade_selection(upgrade_key)

    def close_upgrade_menu(self):
        """Close the upgrade menu."""
        self.menu_manager.close_upgrade_menu()

    def show_main_menu(self):
        """Display the main menu at game start."""
        self.set_state(GameState.MAIN_MENU)
        self.canvas.delete('all')
        self._draw_starfield()
        
        # Title
        self.canvas.create_text(
            self.window_width // 2, self.window_height // 2 - 100,
            text='SHAPE GAME',
            fill='cyan',
            font=('Arial', 64, 'bold')
        )
        
        # Subtitle
        self.canvas.create_text(
            self.window_width // 2, self.window_height // 2 - 20,
            text='Click to Start or Press SPACE',
            fill='lime',
            font=('Arial', 24)
        )
        
        # Store references for click detection
        self.main_menu_start_rect = None

    def start_game_from_menu(self):
        """Start the game after main menu."""
        if not self.game_started:
            self.game_started = True
            self.set_state(GameState.PLAYING)
            self.canvas.delete('all')
            self._draw_starfield()
            
            # Recreate player's canvas item (it was deleted by canvas.delete('all'))
            self.player.rect = self.canvas.create_oval(
                self.player.x - self.player.size//2, self.player.y - self.player.size//2,
                self.player.x + self.player.size//2, self.player.y + self.player.size//2,
                fill='blue'
            )
            
            # Reinitialize game UI
            self.score_text = self.canvas.create_text(self.window_width//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
            self.version_text = self.canvas.create_text(10, self.window_height - 10, anchor='sw', fill='gray', font=('Arial', 10), text=f"v{VERSION}")
            self.level_text = self.canvas.create_text(self.window_width//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
            self.xp_text = self.canvas.create_text(self.window_width//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")
            self.game_level_text = self.canvas.create_text(self.window_width//2, 130, anchor='n', fill='orange', font=('Arial', 16), text=f"Game Level: {self.game_level}")
            self.timer_text = self.canvas.create_text(self.window_width - 80, 30, anchor='n', fill='white', font=('Arial', 16), text="Time: 0:00")
            self.start_game_level()

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
        # First, ensure game is in playing state
        self.set_state(GameState.PLAYING)
        
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
        self.start_game_level()
        self.score_text = self.canvas.create_text(WIDTH//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.version_text = self.canvas.create_text(10, HEIGHT - 10, anchor='sw', fill='gray', font=('Arial', 10), text=f"v{VERSION}")
        self.level_text = self.canvas.create_text(WIDTH//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(WIDTH//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")
        self.timer_text = self.canvas.create_text(WIDTH - 80, 30, anchor='n', fill='white', font=('Arial', 16), text="Time: 0:00")
        
        # Restart background music
        start_background_music(self)

    def on_key_press(self, event):
        """Handle key press events for movement and actions."""
        # Check for special keys FIRST (before movement keys)
        if event.keysym == 'space':  # Spacebar
            # If main menu is active, start the game
            if self.main_menu_active:
                self.start_game_from_menu()
                return
            # Otherwise toggle auto-fire
            self.auto_fire_enabled = not self.auto_fire_enabled
            print(f"[ACTION] Auto-fire {'ENABLED' if self.auto_fire_enabled else 'DISABLED'}")
            return
        elif event.keysym in ['1', '2', '3']:  # Number keys for upgrade selection
            if self.menu_manager.upgrade_menu_active and self.menu_manager.upgrade_menu_clickable:
                # Convert key to upgrade index (1=first, 2=second, 3=third)
                upgrade_index = int(event.keysym) - 1
                # Get the upgrade choices in order
                upgrade_choices_list = list(self.menu_manager.upgrade_choices)
                if upgrade_index < len(upgrade_choices_list):
                    upgrade_key = upgrade_choices_list[upgrade_index]
                    self.menu_manager.on_upgrade_selection(upgrade_key)
                    print(f"[ACTION] Upgrade selected via key {event.keysym}: {upgrade_key}")
            return
        elif event.keysym == 'Escape':
            # If dev menu is open, close it
            if self.menu_manager.dev_menu_active:
                self.close_dev_menu()
            # If upgrade menu is open, close it without resuming, then open pause menu
            elif self.menu_manager.upgrade_menu_active:
                self.menu_manager.close_upgrade_menu(resume_game=False)
                self.show_pause_menu()
            # If pause menu is open, close it (resume game)
            elif self.paused:
                self.hide_pause_menu()
            # Otherwise, open pause menu
            else:
                self.show_pause_menu()
            return
        
        # Use layout-independent keysym map for movement controls
        if event.keysym in self.KEYSYM_MAP:
            self.pressed_keys.add(self.KEYSYM_MAP[event.keysym])

    def on_key_release(self, event):
        """Handle key release events for movement."""
        if event.keysym in self.KEYSYM_MAP:
            self.pressed_keys.discard(self.KEYSYM_MAP[event.keysym])
    


    def on_window_focus_out(self, event):
        """Pause game when window loses focus."""
        if self._game_state == GameState.PLAYING:
            self.show_pause_menu()

    def on_window_focus_in(self, event):
        """Optional: could resume game when window regains focus, but keeping paused is safer."""
        pass

    def schedule_logic_updates(self):
        """Schedule the next logic update at 50 FPS (20ms)."""
        self.update_logic()
        self.interpolation_factor = 0.0  # Reset for next logic tick
        self.root.after(20, self.schedule_logic_updates)

    def update(self):
        """Main render loop: updates visuals at 120 FPS (~8ms)."""
        if self._game_state == GameState.PLAYING:
            # Increment interpolation factor (0.0 to 1.0 over 20ms logic tick)
            self.interpolation_factor = min(1.0, self.interpolation_factor + (8.0 / 20.0))
            # Update player render position with interpolation
            self.player.update_render_position(self.interpolation_factor)
            # Update timer display during gameplay
            time_str = self.format_time(self.game_time_ms)
            self.canvas.itemconfig(self.timer_text, text=f"Time: {time_str}")
            
            # Performance monitoring
            if PERFORMANCE_MONITORING and self.perf_text:
                self.frame_count += 1
                self.fps_timer += 8
                if self.fps_timer >= 1000:  # Update FPS display every second
                    self.current_fps = self.frame_count
                    self.frame_count = 0
                    self.fps_timer = 0
                    entity_count = (len(self.enemies) + len(self.particles) + 
                                  len(self.projectiles) + len(self.shards) + 
                                  len(self.minions) + len(self.black_holes))
                    self.canvas.itemconfig(
                        self.perf_text, 
                        text=f"FPS: {self.current_fps}\nEntities: {entity_count}\nGrid Cells: {len(self.spatial_grid)}"
                    )
            
            # Force canvas redraw
            self.canvas.update_idletasks()
        self.root.after(8, self.update)

    def update_logic(self):
        """Main game logic loop: updates game state at 50 FPS (20ms)."""
        # Only run game logic when actively playing
        if self._game_state != GameState.PLAYING:
            return
        
        try:
            # Track time played
            self.game_time_ms += 20
            
            # Auto-fire if enabled (return time limits firing)
            if self.auto_fire_enabled:
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
            self.update_shield_cooldown()
            self.update_game_level_progression()  # Update wave and level progression
            self._update_boss_fight()  # Update boss fight mechanics if active
        except tk.TclError as e:
            print(f"[UPDATE ERROR] Tkinter error in update loop: {e}")
            # Don't print full traceback for common Tkinter errors
        except ZeroDivisionError as e:
            print(f"[UPDATE ERROR] Math error in update loop: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"[UPDATE ERROR] Unexpected exception in update loop: {e}")
            import traceback
            traceback.print_exc()

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
        """Create a poof particle effect at (x, y) using object pooling."""
        for i in range(PARTICLE_COUNT):
            angle = (2 * math.pi * i) / PARTICLE_COUNT
            speed = 1.2  # Scaled for 50 FPS logic
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Try to reuse a particle from pool
            particle = self._get_particle_from_pool()
            if particle:
                # Reuse existing particle
                particle.reset(x, y, vx, vy, PARTICLE_LIFE)
            else:
                # Create new particle
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
            shard_speed = 3.2  # Scaled for 50 FPS logic
            vx = math.cos(angle) * shard_speed
            vy = math.sin(angle) * shard_speed
            
            shard = Shard(self.canvas, x, y, vx, vy, self, lifetime=1000, explosive=explosive)  # 1000ms = 1 second
            self.shards.append(shard)
    
    def create_explosive_shrapnel(self, x, y):
        """Create an explosion of shrapnel shards in all directions."""
        # Scale explosion size based on upgrade level
        explosive_level = self.computed_weapon_stats.get('explosive_shrapnel', 0)
        shard_count = 3 + (2 * explosive_level)  # 5 at level 1, 7 at level 2, 9 at level 3, etc (small poof to bigger)
        shard_speed = 1.6 + (0.6 * explosive_level)  # Scaled for 50 FPS logic
        
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
        """Update all particles and remove dead ones (with object pooling)."""
        alive = []
        for p in self.particles:
            if p.update():
                alive.append(p)
            else:
                # Return to pool instead of destroying
                self._return_particle_to_pool(p)
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
        
        # Calculate available ammo - only show orb when there are no main projectiles at all
        # (including ones that are returning)
        has_active_main_projectile = any(p for p in self.projectiles if not p.is_mini_fork)
        available_ammo = 0 if has_active_main_projectile else 1
        
        # Remove old orbs
        for orb_id in self.ammo_orbs:
            try:
                self.canvas.delete(orb_id)
            except tk.TclError:
                pass  # Already deleted
        self.ammo_orbs = []
        
        # Update rotation angle
        self.ammo_rotation = (self.ammo_rotation + 2.4) % 360  # Rotate 2.4 degrees per frame (scaled for 50 FPS logic)
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
        """Move all enemies towards the player with optimized collision avoidance."""
        px, py = self.player.get_center()
        
        # Mark grid for rebuild after all movements
        self.grid_needs_rebuild = True
        
        # Batch canvas updates for better performance
        canvas_updates = []
        
        # Apply collision avoidance and movement
        for enemy in self.enemies:
            # Different speeds for different enemy types
            if isinstance(enemy, PentagonEnemy):
                speed = 1.5  # Pentagons move slower
            elif isinstance(enemy, TriangleEnemy):
                speed = 2.2  # Triangles medium speed
            else:  # CircleEnemy, SquareEnemy, HexagonEnemy
                speed = 2.4  # Others normal speed
            
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            # Calculate direction to player
            dx = px - ex_center
            dy = py - ey_center
            dist_sq = dx * dx + dy * dy  # Use squared distance to avoid sqrt
            
            if dist_sq > 1:  # Avoid division by zero
                dist = math.sqrt(dist_sq)
                # Base movement toward player
                move_x = (dx / dist) * speed
                move_y = (dy / dist) * speed
                
                # OPTIMIZED: Only check nearby enemies using spatial grid
                # This reduces O(n²) to approximately O(n*k) where k is much smaller
                nearby_enemies = self._get_nearby_enemies(ex_center, ey_center, 60)
                
                # Collision avoidance: steer away from nearby enemies
                for other in nearby_enemies:
                    if other is enemy:
                        continue
                    
                    ox, oy = other.get_position()
                    ox_center = ox + ENEMY_SIZE_HALF
                    oy_center = oy + ENEMY_SIZE_HALF
                    
                    # Vector from other enemy to this enemy
                    diff_x = ex_center - ox_center
                    diff_y = ey_center - oy_center
                    enemy_dist_sq = diff_x * diff_x + diff_y * diff_y
                    
                    # Avoidance radius: push enemies apart if too close
                    min_distance_sq = 1600  # 40^2 - avoid sqrt
                    if enemy_dist_sq < min_distance_sq and enemy_dist_sq > 1:
                        enemy_dist = math.sqrt(enemy_dist_sq)
                        # Steer away proportionally to closeness
                        steer_strength = 0.6 * (40 - enemy_dist) / 40
                        avoidance_x = (diff_x / enemy_dist) * steer_strength
                        avoidance_y = (diff_y / enemy_dist) * steer_strength
                        move_x += avoidance_x
                        move_y += avoidance_y
                
                # Apply movement directly
                enemy.x += int(move_x)
                enemy.y += int(move_y)
                
                # Prepare canvas update (batch for performance)
                if isinstance(enemy, TriangleEnemy):
                    enemy.points = [
                        enemy.x + enemy.size//2, enemy.y,
                        enemy.x, enemy.y + enemy.size,
                        enemy.x + enemy.size, enemy.y + enemy.size
                    ]
                    canvas_updates.append((enemy.rect, 'polygon', enemy.points))
                else:
                    canvas_updates.append((enemy.rect, 'rect', (enemy.x, enemy.y, enemy.x + enemy.size, enemy.y + enemy.size)))
        
        # Batch apply all canvas updates
        for rect_id, shape_type, coords in canvas_updates:
            if shape_type == 'polygon':
                self.canvas.coords(rect_id, *coords)
            else:
                self.canvas.coords(rect_id, *coords)

    def check_player_collision(self) -> None:
        """Check if any enemy collides with player and deal damage."""
        px, py = self.player.get_center()
        
        # OPTIMIZED: Only check enemies near player using spatial grid
        nearby_enemies = self._get_nearby_enemies(px, py, 80)
        
        for enemy in nearby_enemies:
            ex, ey = enemy.get_position()
            
            # Decrease immunity timer if enemy has it
            if enemy.shield_immunity > 0:
                enemy.shield_immunity -= 1
            
            # Check distance between player and enemy
            if not CollisionDetector.check_player_enemy_collision(px, py, ex, ey):
                # No collision, continue
                continue
            
            # Skip if enemy is currently immune (after decrementing above)
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
        self.set_state(GameState.GAME_OVER)
        
        # Calculate overlay size based on actual content
        # Title + Score + Time + Button with padding: 60 + 40 + 40 + 50 + 60 = 250 pixels high
        overlay_width = 400
        overlay_height = 250
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
        
        # Time text
        time_str = self.format_time(self.game_time_ms)
        self.canvas.create_text(
            overlay_x + overlay_width // 2, overlay_y + 120,
            text=f'{time_str}',
            fill='cyan',
            font=('Arial', 20)
        )
        
        # Restart button
        btn_width = 200
        btn_height = 50
        btn_x = overlay_x + (overlay_width - btn_width) // 2
        btn_y = overlay_y + 170
        
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
