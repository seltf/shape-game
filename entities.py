"""
Entities module for shape-game.
Contains all entity classes: BlackHole, Player, Enemy types, Particles, Shards, and Projectiles.
"""

import tkinter as tk
import math
import random
from typing import Optional, List, Set, Tuple, Any, Dict
from constants import *
from audio import play_sound_async, play_beep_async


def enemy_center(enemy: Any) -> Tuple[float, float]:
    """Return the center (x,y) of an enemy using its size if available."""
    ex, ey = enemy.get_position()
    half = getattr(enemy, 'size', ENEMY_SIZE) // 2
    return ex + half, ey + half


class BaseEntity:
    """
    Base interface for all entities to standardize lifecycle and interaction.
    """
    def __init__(self) -> None:
        self.alive: bool = True

    def update(self, dt_ms: int) -> None:
        """Advance entity state by dt_ms (milliseconds)."""
        pass

    def render(self) -> None:
        """Update entity visual representation if needed."""
        pass

    def get_position(self) -> Tuple[float, float]:
        """Return top-left position for rectangle-like entities."""
        return 0.0, 0.0

    def take_damage(self) -> bool:
        """Apply 1 damage and return True if still alive."""
        return self.alive

    def cleanup(self) -> None:
        """Remove visual artifacts and mark entity as dead."""
        self.alive = False


class BlackHole:
    """
    Represents a black hole effect spawned by weapon hits.
    Pulls and kills enemies in its radius when it detonates.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, radius: int, game: Any, level: int = 1) -> None:
        """Initialize black hole at (x, y) with given radius."""
        self.canvas: tk.Canvas = canvas
        self.game: Any = game
        self.x: float = x
        self.y: float = y
        self.radius: int = radius
        self.level: int = level  # Store upgrade level for damage calculation
        self.time_alive: int = 0  # Track lifetime in milliseconds
        self.detonation_phase: bool = False
        # Visual representation - only outline, apply display transform for scaling
        scale = self.game.display_scale if getattr(self.game, 'display_scale', 1.0) > 0 else 1.0
        off_x = getattr(self.game, 'offset_x', 0.0)
        off_y = getattr(self.game, 'offset_y', 0.0)
        self.rect: int = self.canvas.create_oval(
            off_x + (x - radius) * scale, off_y + (y - radius) * scale,
            off_x + (x + radius) * scale, off_y + (y + radius) * scale,
            fill='', outline='#6600ff', width=2
        )
        # Animated rings during pull phase
        self.active_rings: List[List[Any]] = []  # Track canvas IDs of active animated rings
        self.ring_spawn_counter: int = 0  # Counter to spawn rings at intervals
    
    def update(self) -> bool:
        """Update black hole and check for detonation."""
        self.time_alive += 20  # Update is called every 20ms
        
        # Immediately start detonation (no travel phase for weapon version)
        if not self.detonation_phase:
            self.detonation_phase = True
            self._start_detonation()
        
        # Keep pulling enemies if detonating and within duration
        if self.detonation_phase:
            self._pull_enemies()
            self._update_rings()  # Update animated rings
            # Check if detonation duration expired
            if self.time_alive >= BLACK_HOLE_PULL_DURATION:
                self._cleanup_rings()  # Clean up any remaining rings
                self._kill_enemies_at_center()  # Kill all enemies in center at end
                return False  # Remove after pull duration ends
            return True
        
        return True
    
    def _start_detonation(self) -> None:
        """Start the detonation sequence with visual effects."""
        # Create explosion animation expanding from black hole
        for ring in range(3):
            ring_size = 20 + (ring * 30)
            scale = self.game.display_scale if getattr(self.game, 'display_scale', 1.0) > 0 else 1.0
            off_x = getattr(self.game, 'offset_x', 0.0)
            off_y = getattr(self.game, 'offset_y', 0.0)
            ring_id = self.canvas.create_oval(
                off_x + (self.x - ring_size) * scale, off_y + (self.y - ring_size) * scale,
                off_x + (self.x + ring_size) * scale, off_y + (self.y + ring_size) * scale,
                outline='#6600ff', width=2
            )
            
            def delete_ring(rid=ring_id):
                try:
                    self.canvas.delete(rid)
                except tk.TclError:
                    pass
            
            self.canvas.after(150 + (ring * 50), delete_ring)
    
    def _pull_enemies(self) -> None:
        """Pull all nearby enemies toward the black hole center."""
        for enemy in self.game.enemies[:]:
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            
            dx = self.x - ex_center
            dy = self.y - ey_center
            dist_sq = dx * dx + dy * dy
            radius_sq = self.radius * self.radius
            
            # Only pull enemies within pull radius
            if dist_sq < radius_sq and dist_sq > 0:
                dist = math.sqrt(dist_sq)
                # Pull force decreases with distance but has a minimum to prevent getting stuck
                pull_factor = 1.0 - (dist / self.radius)  # 0 to 1
                pull_factor = max(0.33, pull_factor)  # Minimum of 33% strength even at edge
                pull_speed = BLACK_HOLE_PULL_STRENGTH * pull_factor
                
                # Direction toward black hole
                dir_x = dx / dist
                dir_y = dy / dist
                
                # Apply pull continuously during detonation
                enemy.pull_velocity_x = dir_x * pull_speed
                enemy.pull_velocity_y = dir_y * pull_speed
                enemy.being_pulled = True
                enemy.pull_timer = 1  # Reset pull timer to 1 frame
    
    def _update_rings(self) -> None:
        """Update animated rings, spawning new ones and shrinking existing ones."""
        # Spawn a new ring every 500ms (25 updates at 20ms per update)
        self.ring_spawn_counter += 1
        if self.ring_spawn_counter >= 25:
            self.ring_spawn_counter = 0
            self._spawn_new_ring()
        
        # Update all existing rings - shrink them toward center
        rings_to_remove = []
        for ring_data in self.active_rings:
            ring_id, current_size, max_size = ring_data
            
            # Shrink ring by 1 pixel per update (slower animation for 20ms ticks)
            new_size = current_size - 1
            
            if new_size <= 0:
                # Ring has shrunk to center, remove it
                try:
                    self.canvas.delete(ring_id)
                except tk.TclError:
                    pass
                rings_to_remove.append(ring_data)
            else:
                # Update ring size on canvas
                try:
                    scale = self.game.display_scale if getattr(self.game, 'display_scale', 1.0) > 0 else 1.0
                    off_x = getattr(self.game, 'offset_x', 0.0)
                    off_y = getattr(self.game, 'offset_y', 0.0)
                    self.canvas.coords(
                        ring_id,
                        off_x + (self.x - new_size) * scale, off_y + (self.y - new_size) * scale,
                        off_x + (self.x + new_size) * scale, off_y + (self.y + new_size) * scale
                    )
                    # Update the size tracking
                    ring_data[1] = new_size
                except tk.TclError:
                    rings_to_remove.append(ring_data)
        
        # Remove rings that disappeared
        for ring_data in rings_to_remove:
            if ring_data in self.active_rings:
                self.active_rings.remove(ring_data)
    
    def _spawn_new_ring(self) -> None:
        """Spawn a new animated ring at the edge of the pull radius."""
        ring_size = self.radius
        scale = self.game.display_scale if getattr(self.game, 'display_scale', 1.0) > 0 else 1.0
        off_x = getattr(self.game, 'offset_x', 0.0)
        off_y = getattr(self.game, 'offset_y', 0.0)
        ring_id = self.canvas.create_oval(
            off_x + (self.x - ring_size) * scale, off_y + (self.y - ring_size) * scale,
            off_x + (self.x + ring_size) * scale, off_y + (self.y + ring_size) * scale,
            outline='#6600ff', width=1.5
        )
        # Store ring data as [id, current_size, max_size]
        self.active_rings.append([ring_id, ring_size, ring_size])
    
    def _cleanup_rings(self) -> None:
        """Remove all animated rings from canvas."""
        for ring_data in self.active_rings:
            ring_id = ring_data[0]
            try:
                self.canvas.delete(ring_id)
            except tk.TclError:
                pass
        self.active_rings.clear()
    
    def _kill_enemies_at_center(self) -> None:
        """Deal damage to enemies in radius and fling them outward."""
        # Play custom black hole detonation sound or fallback to THWOMP effect
        print(f"[ACTION] Black hole detonating at center ({self.x}, {self.y})")
        play_sound_async('black_hole_detonate', 80, 200, self.game)
        
        # Apply effects to all enemies in the radius
        fling_speed = 1.92  # Speed to fling enemies outward (scaled for 20ms tick rate)
        
        for enemy in self.game.enemies[:]:
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            radius_sq = self.radius * self.radius
            
            # Apply effect if in radius
            if dist_sq < radius_sq and dist_sq > 0:
                dist = math.sqrt(dist_sq)
                
                # Deal damage based on level: 1 damage at levels 1-4, 2 damage at level 5+
                damage = 2 if self.level >= 5 else 1
                if hasattr(enemy, 'take_damage'):
                    # All enemies now have take_damage method
                    for _ in range(damage):
                        if not enemy.take_damage():
                            break  # Enemy died
                else:
                    # Fallback for any entities without take_damage (shouldn't happen)
                    if hasattr(enemy, 'health'):
                        enemy.health -= damage
                
                # Fling enemy outward from black hole
                # Direction away from black hole
                fling_dir_x = dx / dist
                fling_dir_y = dy / dist
                
                # Apply fling using pull_velocity (which is already integrated into move_towards)
                enemy.pull_velocity_x = fling_dir_x * fling_speed
                enemy.pull_velocity_y = fling_dir_y * fling_speed
                enemy.being_pulled = True
                enemy.pull_timer = 20  # Fling for 20 frames (~1 second)
        
        # Clean up dead enemies robustly (avoid mutating the main list while iterating)
        dead_enemies = [e for e in list(self.game.enemies) if hasattr(e, 'health') and e.health <= 0]
        for enemy in dead_enemies:
            try:
                ex, ey = enemy.get_position()
                half = getattr(enemy, 'size', ENEMY_SIZE) // 2
                self.game.create_death_poof(ex + half, ey + half)
            except Exception:
                pass
            try:
                # Use game's kill_enemy method to handle removal and XP
                self.game.kill_enemy(enemy)
            except Exception:
                # As a fallback, attempt to remove and delete visuals
                try:
                    if enemy in self.game.enemies:
                        self.game.enemies.remove(enemy)
                except Exception:
                    pass
                try:
                    self.canvas.delete(enemy.rect)
                except Exception:
                    pass

        # Ensure no dead enemies remain in the game's enemy list
        try:
            self.game.enemies = [e for e in self.game.enemies if not (hasattr(e, 'health') and e.health <= 0)]
        except Exception:
            # If something goes wrong, keep existing list (avoid crash)
            pass
    
    def cleanup(self) -> None:
        """Remove black hole from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass


class Player:
    """
    Represents the player character in the game.
    Handles position, movement, and rendering.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize player at (x, y) with given size."""
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0  # Velocity x
        self.vy: float = 0  # Velocity y
        self.health: int = 1  # Player starts with 1 HP
        self.shield_active: bool = False  # Whether shield is currently up
        self.shield_cooldown: int = 0  # Cooldown counter in milliseconds
        self.shield_rings: List[Optional[int]] = []  # List of canvas objects for shield rings (multiple rings for levels)
        self.shield_level: int = 0  # Current shield level (0-3)
        self.prev_x: float = x  # Previous frame position for interpolation
        self.prev_y: float = y
        self.rect: int = self.canvas.create_oval(x-size//2, y-size//2, x+size//2, y+size//2, fill='blue')

    def move(self, accel_x: float, accel_y: float, speed_boost: float = 0, window_width: Optional[int] = None, window_height: Optional[int] = None) -> None:
        """Apply acceleration to player velocity and update position."""
        # Use provided window dimensions, fall back to constants if not provided
        if window_width is None:
            window_width = WIDTH
        if window_height is None:
            window_height = HEIGHT
        
        # Apply acceleration
        self.vx += accel_x * PLAYER_ACCELERATION
        self.vy += accel_y * PLAYER_ACCELERATION
        
        # Clamp velocity to max speed (including speed boost from upgrades)
        max_speed = PLAYER_MAX_SPEED + speed_boost
        speed = math.hypot(self.vx, self.vy)
        if speed > max_speed:
            self.vx = (self.vx / speed) * max_speed
            self.vy = (self.vy / speed) * max_speed
        
        # Apply friction
        self.vx *= PLAYER_FRICTION
        self.vy *= PLAYER_FRICTION
        
        # Store previous position for interpolation
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Update position
        self.x = max(self.size//2, min(window_width-self.size//2, self.x+self.vx))
        self.y = max(self.size//2, min(window_height-self.size//2, self.y+self.vy))

    def get_center(self) -> Tuple[float, float]:
        """Return the center coordinates of the player circle."""
        return self.x, self.y

    def update_render_position(self, interpolation_factor: float) -> None:
        """Interpolate and update rendered position based on interpolation factor (0.0 to 1.0)."""
        interp_x = self.prev_x + (self.x - self.prev_x) * interpolation_factor
        interp_y = self.prev_y + (self.y - self.prev_y) * interpolation_factor
        # Apply display transform (scale + offsets) for render-time scaling
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        dx1 = off_x + (interp_x - self.size//2) * scale
        dy1 = off_y + (interp_y - self.size//2) * scale
        dx2 = off_x + (interp_x + self.size//2) * scale
        dy2 = off_y + (interp_y + self.size//2) * scale
        self.canvas.coords(self.rect, dx1, dy1, dx2, dy2)
        
        # Update shield rings if active
        if self.shield_rings:
            for i, ring in enumerate(self.shield_rings):
                if ring is not None:
                    shield_radius = self.size // 2 + 15 + (i * 12)
                    rx1 = off_x + (interp_x - shield_radius) * scale
                    ry1 = off_y + (interp_y - shield_radius) * scale
                    rx2 = off_x + (interp_x + shield_radius) * scale
                    ry2 = off_y + (interp_y + shield_radius) * scale
                    self.canvas.coords(ring, rx1, ry1, rx2, ry2)

    def activate_shield(self) -> None:
        """Activate the shield rings around the player based on shield level."""
        if not self.shield_active:
            self.shield_active = True
            self.shield_cooldown = 0
            # Create rings based on shield level
            self.shield_rings = []
            for i in range(self.shield_level):
                shield_radius = self.size // 2 + 15 + (i * 12)
                ring = self.canvas.create_oval(
                    self.x - shield_radius, self.y - shield_radius,
                    self.x + shield_radius, self.y + shield_radius,
                    outline='cyan', width=2
                )
                self.shield_rings.append(ring)

    def deactivate_shield(self, enemy: Optional[Any] = None) -> None:
        """Remove one shield ring and push back nearby enemies. Start cooldown if all rings destroyed."""
        print(f"[SHIELD] deactivate_shield called, has game: {hasattr(self, 'game')}")
        try:
            # Remove one ring from the display
            if self.shield_rings:
                ring = self.shield_rings.pop()
                if ring is not None:
                    self.canvas.delete(ring)
            
            # If no rings left, start cooldown
            if not self.shield_rings:
                self.shield_active = False
                self.shield_cooldown = 5000  # 5 seconds in milliseconds
            
            # Push back all nearby enemies in a radius
            push_radius = 100  # Radius to affect enemies (reduced from 150)
            px, py = self.get_center()
            
            # Find the game instance to access all enemies
            # The game instance is passed when deactivate_shield is called from check_player_collision
            # We'll need to pass the game instance or access enemies differently
            # For now, store reference to game in player during init
            if hasattr(self, 'game'):
                for nearby_enemy in self.game.enemies:
                    try:
                        ex, ey = nearby_enemy.get_position()
                        ex_center = ex + nearby_enemy.size // 2
                        ey_center = ey + nearby_enemy.size // 2
                        
                        # Calculate distance to this enemy
                        dx = ex_center - px
                        dy = ey_center - py
                        dist = math.hypot(dx, dy)
                        
                        # If enemy is within push radius, push it back
                        if dist < push_radius and dist > 0:
                            push_force = 3.0  # Pushback speed per frame (gentle knockback to create space)
                            nearby_enemy.being_pushed = True
                            nearby_enemy.push_velocity_x = (dx / dist) * push_force
                            nearby_enemy.push_velocity_y = (dy / dist) * push_force
                            nearby_enemy.push_timer = 15  # Push for 15 frames (~0.3 seconds at 50 FPS)
                    except Exception as e:
                        print(f"[ERROR] Failed to push enemy: {e}")
        except Exception as e:
            print(f"[ERROR] Shield deactivation failed: {e}")

    def update_shield(self, dt_ms: int) -> None:
        """Update shield cooldown (dt_ms is delta time in milliseconds)."""
        if not self.shield_active and self.shield_cooldown > 0:
            self.shield_cooldown -= dt_ms
            if self.shield_cooldown <= 0:
                self.activate_shield()


class Enemy(BaseEntity):
    """
    Represents a square (4-sided) enemy in the game.
    Takes 4 hits to defeat. Basic difficulty enemy.
    Handles position, movement towards the player, and rendering.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        super().__init__()
        """Initialize square enemy at (x, y) with given size."""
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sides: int = 4  # Square = 4 sides
        self.health: int = 4  # Takes 4 hits to kill (sides = strength)
        self.being_pulled: bool = False  # Whether currently pulled by black hole
        self.pull_velocity_x: float = 0  # Pull force direction X
        self.pull_velocity_y: float = 0  # Pull force direction Y
        self.pull_timer: int = 0  # Frames remaining to be pulled
        self.being_pushed: bool = False  # Whether currently pushed by shield
        self.push_velocity_x: float = 0  # Push force direction X
        self.push_velocity_y: float = 0  # Push force direction Y
        self.push_timer: int = 0  # Frames remaining to be pushed
        self.shield_immunity: int = 0  # Frames of immunity after shield hit
        self.rect: int = self.canvas.create_rectangle(x, y, x+size, y+size, fill='red')

    def move_towards(self, target_x: float, target_y: float, speed: int = 4) -> None:
        """Move enemy towards (target_x, target_y) with capped acceleration, damping, separation, and arrival."""
        # Apply push force if being pushed by shield
        if self.being_pushed and self.push_timer > 0:
            self.x += self.push_velocity_x
            self.y += self.push_velocity_y
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += self.pull_velocity_x
            self.y += self.pull_velocity_y
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement: steer toward player with capped acceleration
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                # Arrival: slow desired speed near target
                desired_speed = speed
                arrive_radius = 120
                if dist < arrive_radius:
                    desired_speed = max(1.0, speed * (dist / arrive_radius))
                target_vx = (dx / dist) * desired_speed
                target_vy = (dy / dist) * desired_speed
                # Compute desired acceleration toward target velocity
                ax = (target_vx - self.vx)
                ay = (target_vy - self.vy)
                # Cap acceleration magnitude (turn rate)
                max_accel = 0.45
                acc_mag = math.hypot(ax, ay)
                if acc_mag > max_accel:
                    ax = (ax / acc_mag) * max_accel
                    ay = (ay / acc_mag) * max_accel
                self.vx += ax
                self.vy += ay
                # Separation from nearby enemies to reduce convergence
                sep_force_x = 0.0
                sep_force_y = 0.0
                sep_radius = 40
                sep_radius_sq = sep_radius * sep_radius
                sep_strength = 0.6
                for other in getattr(self, 'game', None).enemies if hasattr(self, 'game') else []:
                    if other is self:
                        continue
                    ox, oy = other.get_position()
                    ox += other.size // 2
                    oy += other.size // 2
                    sx = (self.x + self.size // 2) - ox
                    sy = (self.y + self.size // 2) - oy
                    dsq = sx * sx + sy * sy
                    if 0 < dsq < sep_radius_sq:
                        d = math.sqrt(dsq)
                        sep_force_x += (sx / d) * (sep_strength * (1 - d / sep_radius))
                        sep_force_y += (sy / d) * (sep_strength * (1 - d / sep_radius))
                self.vx += sep_force_x
                self.vy += sep_force_y
                # Normalize to desired_speed to keep consistent speed
                spd = math.hypot(self.vx, self.vy)
                if spd > 0:
                    self.vx = (self.vx / spd) * desired_speed
                    self.vy = (self.vy / spd) * desired_speed
                self.x += self.vx
                self.y += self.vy
        
        self.canvas.coords(self.rect, self.x, self.y, self.x+self.size, self.y+self.size)

    def get_position(self) -> Tuple[float, float]:
        """Return the top-left coordinates of the enemy rectangle."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        self.alive = self.health > 0
        return self.alive

    def cleanup(self) -> None:
        """Remove enemy from canvas and mark as dead."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass

        self.alive = False

class RangedEnemy(Enemy):
    """Enemy that stays put and fires projectiles toward the player periodically."""
    def __init__(self, canvas: tk.Canvas, x: int, y: int, size: int = ENEMY_SIZE) -> None:
        # Initialize as a normal enemy, then replace the visual with a diamond
        super().__init__(canvas, x, y, size)
        # Ranged enemies are fragile — one hit to kill
        self.health = 1
        try:
            # Remove the default rectangle created by Enemy
            self.canvas.delete(self.rect)
        except Exception:
            pass
        half = size // 2
        # Playing-card diamond: inset top/bottom so the shape is fuller (not a thin gem)
        inset_x = int(size * 0.15)
        inset_y = int(size * 0.15)
        self.points: List[int] = [
            x + half, y + inset_y,                # top (inset)
            x + size - inset_x, y + half,         # right (wider)
            x + half, y + size - inset_y,         # bottom (inset)
            x + inset_x, y + half                  # left (wider)
        ]
        self.rect = canvas.create_polygon(*self.points, fill='#6a00a8', outline='white', width=2)
        # Firing cooldown in ms (logic updates at 20ms)
        self.fire_timer_ms: int = 0
        self.fire_interval_ms: int = 1800  # fires roughly every 1.8s
        # Wandering (small movement around spawn to look natural)
        self.base_x = float(x)
        self.base_y = float(y)
        self.wander_phase = random.random() * (2 * math.pi)
        self.wander_phase_y = random.random() * (2 * math.pi)
        # Small random speed and radius so multiple ranged enemies differ
        self.wander_speed = 0.05 + random.random() * 0.06
        self.wander_radius = 4.0 + random.random() * 6.0

    def get_position(self) -> Tuple[float, float]:
        return self.x, self.y

    def update_shape(self) -> None:
        """Recompute diamond points for current position and update canvas coords."""
        # Apply light wandering around the base position before drawing
        try:
            self.wander_phase += self.wander_speed
            self.wander_phase_y += self.wander_speed * 0.9
            ox = math.cos(self.wander_phase) * self.wander_radius
            oy = math.sin(self.wander_phase_y) * (self.wander_radius * 0.6)
            # Update logical position used by other systems
            self.x = self.base_x + ox
            self.y = self.base_y + oy
        except Exception:
            # Fallback: keep current position
            pass

        half = self.size // 2
        inset_x = int(self.size * 0.15)
        inset_y = int(self.size * 0.15)
        self.points = [
            self.x + half, self.y + inset_y,
            self.x + self.size - inset_x, self.y + half,
            self.x + half, self.y + self.size - inset_y,
            self.x + inset_x, self.y + half
        ]
        try:
            self.canvas.coords(self.rect, *self.points)
        except tk.TclError:
            pass


class TriangleEnemy(BaseEntity):
    """
    Represents a triangle (3-sided) enemy.
    Takes 2 hits to defeat. Weak enemy type.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize triangle enemy at (x, y) with given size."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sides: int = 3  # Triangle = 3 sides
        self.health: int = 2  # Takes 2 hits to kill
        self.being_pulled: bool = False  # Whether currently pulled by black hole
        self.pull_velocity_x: float = 0  # Pull force direction X
        self.pull_velocity_y: float = 0  # Pull force direction Y
        self.pull_timer: int = 0  # Frames remaining to be pulled
        self.being_pushed: bool = False  # Whether currently pushed by shield
        self.push_velocity_x: float = 0  # Push force direction X
        self.push_velocity_y: float = 0  # Push force direction Y
        self.push_timer: int = 0  # Frames remaining to be pushed
        self.shield_immunity: int = 0  # Frames of immunity after shield hit
        # Pop effect when spawned from hexagon split
        self.pop_velocity_x: float = 0  # Outward velocity during pop
        self.pop_velocity_y: float = 0
        self.pop_distance: float = 0  # Distance traveled during pop
        self.pop_distance_max: float = 0  # Max distance to pop (0 = no pop)
        # Draw triangle using create_polygon
        # Triangle points: top center, bottom-left, bottom-right
        self.points: List[float] = [
            x + size//2, y,  # top center
            x, y + size,     # bottom-left
            x + size, y + size  # bottom-right
        ]
        self.rect: int = self.canvas.create_polygon(*self.points, fill='orange')

    def move_towards(self, target_x: float, target_y: float, speed: int = 4) -> None:
        """Move enemy towards (target_x, target_y) with capped acceleration, damping, separation, and arrival."""
        # Apply pop effect if triangle is spawning from hexagon split
        if self.pop_distance_max > 0 and self.pop_distance < self.pop_distance_max:
            self.x += self.pop_velocity_x
            self.y += self.pop_velocity_y
            self.pop_distance += math.hypot(self.pop_velocity_x, self.pop_velocity_y)
        # Apply push force if being pushed by shield
        elif self.being_pushed and self.push_timer > 0:
            self.x += self.push_velocity_x
            self.y += self.push_velocity_y
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += self.pull_velocity_x
            self.y += self.pull_velocity_y
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement: steer toward player with capped acceleration
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                desired_speed = speed
                arrive_radius = 120
                if dist < arrive_radius:
                    desired_speed = max(1.0, speed * (dist / arrive_radius))
                target_vx = (dx / dist) * desired_speed
                target_vy = (dy / dist) * desired_speed
                ax = (target_vx - self.vx)
                ay = (target_vy - self.vy)
                max_accel = 0.5
                acc_mag = math.hypot(ax, ay)
                if acc_mag > max_accel:
                    ax = (ax / acc_mag) * max_accel
                    ay = (ay / acc_mag) * max_accel
                self.vx += ax
                self.vy += ay
                # Separation
                sep_force_x = 0.0
                sep_force_y = 0.0
                sep_radius = 36
                sep_radius_sq = sep_radius * sep_radius
                sep_strength = 0.55
                for other in getattr(self, 'game', None).enemies if hasattr(self, 'game') else []:
                    if other is self:
                        continue
                    ox, oy = other.get_position()
                    ox += other.size // 2
                    oy += other.size // 2
                    sx = (self.x + self.size // 2) - ox
                    sy = (self.y + self.size // 2) - oy
                    dsq = sx * sx + sy * sy
                    if 0 < dsq < sep_radius_sq:
                        d = math.sqrt(dsq)
                        sep_force_x += (sx / d) * (sep_strength * (1 - d / sep_radius))
                        sep_force_y += (sy / d) * (sep_strength * (1 - d / sep_radius))
                self.vx += sep_force_x
                self.vy += sep_force_y
                spd = math.hypot(self.vx, self.vy)
                if spd > 0:
                    self.vx = (self.vx / spd) * desired_speed
                    self.vy = (self.vy / spd) * desired_speed
                self.x += self.vx
                self.y += self.vy
        
        # Update triangle points
        self.points = [
            self.x + self.size//2, self.y,  # top center
            self.x, self.y + self.size,     # bottom-left
            self.x + self.size, self.y + self.size  # bottom-right
        ]
        self.canvas.coords(self.rect, *self.points)

    def get_position(self) -> Tuple[float, float]:
        """Return the center-ish coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        self.alive = self.health > 0
        return self.alive

    def cleanup(self) -> None:
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass
        self.alive = False


class PentagonEnemy(BaseEntity):
    """
    Represents a pentagon (5-sided) tank enemy.
    Takes 5 hits to defeat. Strongest enemy type.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize pentagon enemy at (x, y) with given size."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sides: int = 5  # Pentagon = 5 sides
        self.health: int = 5  # Takes 5 hits to kill (sides = strength)
        self.being_pulled: bool = False  # Whether currently pulled by black hole
        self.pull_velocity_x: float = 0  # Pull force direction X
        self.pull_velocity_y: float = 0  # Pull force direction Y
        self.pull_timer: int = 0  # Frames remaining to be pulled
        self.being_pushed: bool = False  # Whether currently pushed by shield
        self.push_velocity_x: float = 0  # Push force direction X
        self.push_velocity_y: float = 0  # Push force direction Y
        self.push_timer: int = 0  # Frames remaining to be pushed
        self.shield_immunity: int = 0  # Frames of immunity after shield hit
        # Draw pentagon using create_polygon
        self.points: List[float] = self._calculate_pentagon_points(x, y, size)
        self.rect: int = self.canvas.create_polygon(*self.points, fill='purple', outline='#FF00FF', width=2)
    
    def _calculate_pentagon_points(self, x: float, y: float, size: int) -> List[float]:
        """Calculate the 5 points of a regular pentagon."""
        points: List[float] = []
        for i in range(5):
            angle = (2 * math.pi * i / 5) - (math.pi / 2)  # Start from top
            px = x + int((size//2) * math.cos(angle))
            py = y + int((size//2) * math.sin(angle))
            points.extend([px, py])
        return points
    
    def move_towards(self, target_x: float, target_y: float, speed: int = 4) -> None:
        """Move enemy towards (target_x, target_y) with capped acceleration, damping, separation, and arrival."""
        # Apply push force if being pushed by shield
        if self.being_pushed and self.push_timer > 0:
            self.x += self.push_velocity_x
            self.y += self.push_velocity_y
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += self.pull_velocity_x
            self.y += self.pull_velocity_y
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement: steer toward player with capped acceleration
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                desired_speed = speed
                arrive_radius = 140
                if dist < arrive_radius:
                    desired_speed = max(0.8, speed * (dist / arrive_radius))
                target_vx = (dx / dist) * desired_speed
                target_vy = (dy / dist) * desired_speed
                ax = (target_vx - self.vx)
                ay = (target_vy - self.vy)
                max_accel = 0.4
                acc_mag = math.hypot(ax, ay)
                if acc_mag > max_accel:
                    ax = (ax / acc_mag) * max_accel
                    ay = (ay / acc_mag) * max_accel
                self.vx += ax
                self.vy += ay
                # Separation
                sep_force_x = 0.0
                sep_force_y = 0.0
                sep_radius = 44
                sep_radius_sq = sep_radius * sep_radius
                sep_strength = 0.5
                for other in getattr(self, 'game', None).enemies if hasattr(self, 'game') else []:
                    if other is self:
                        continue
                    ox, oy = other.get_position()
                    ox += other.size // 2
                    oy += other.size // 2
                    sx = (self.x + self.size // 2) - ox
                    sy = (self.y + self.size // 2) - oy
                    dsq = sx * sx + sy * sy
                    if 0 < dsq < sep_radius_sq:
                        d = math.sqrt(dsq)
                        sep_force_x += (sx / d) * (sep_strength * (1 - d / sep_radius))
                        sep_force_y += (sy / d) * (sep_strength * (1 - d / sep_radius))
                self.vx += sep_force_x
                self.vy += sep_force_y
                spd = math.hypot(self.vx, self.vy)
                if spd > 0:
                    self.vx = (self.vx / spd) * desired_speed
                    self.vy = (self.vy / spd) * desired_speed
                self.x += self.vx
                self.y += self.vy
        
        # Update pentagon points
        self.points = self._calculate_pentagon_points(self.x, self.y, self.size)
        self.canvas.coords(self.rect, *self.points)
    
    def get_position(self) -> Tuple[float, float]:
        """Return the center coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        self.alive = self.health > 0
        return self.alive

    def cleanup(self) -> None:
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass
        self.alive = False


class HexagonEnemy(BaseEntity):
    """
    Represents a hexagon (6-sided) split enemy.
    Takes 6 hits to defeat. When killed, splits into 2 triangle enemies.
    Special ability: splits on death, creating tactical challenge.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize hexagon enemy at (x, y) with given size."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sides: int = 6  # Hexagon = 6 sides
        self.health: int = 6  # Takes 6 hits to kill (sides = strength)
        self.being_pulled: bool = False  # Whether currently pulled by black hole
        self.pull_velocity_x: float = 0  # Pull force direction X
        self.pull_velocity_y: float = 0  # Pull force direction Y
        self.pull_timer: int = 0  # Frames remaining to be pulled
        self.being_pushed: bool = False  # Whether currently pushed by shield
        self.push_velocity_x: float = 0  # Push force direction X
        self.push_velocity_y: float = 0  # Push force direction Y
        self.push_timer: int = 0  # Frames remaining to be pushed
        self.shield_immunity: int = 0  # Frames of immunity after shield hit
        self.should_split: bool = False  # Flag to trigger split on death
        # Draw hexagon using create_polygon
        self.points: List[float] = self._calculate_hexagon_points(x, y, size)
        self.rect: int = self.canvas.create_polygon(*self.points, fill='#00CCFF')
    
    def _calculate_hexagon_points(self, x: float, y: float, size: int) -> List[float]:
        """Calculate the 6 points of a regular hexagon."""
        points: List[float] = []
        for i in range(6):
            angle = (2 * math.pi * i / 6)  # Start from right, 60 degrees apart
            px = x + int((size//2) * math.cos(angle))
            py = y + int((size//2) * math.sin(angle))
            points.extend([px, py])
        return points
    
    def move_towards(self, target_x: float, target_y: float, speed: int = 4) -> None:
        """Move enemy towards (target_x, target_y) with capped acceleration, damping, separation, and arrival."""
        # Apply push force if being pushed by shield
        if self.being_pushed and self.push_timer > 0:
            self.x += self.push_velocity_x
            self.y += self.push_velocity_y
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += self.pull_velocity_x
            self.y += self.pull_velocity_y
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement: steer toward player with capped acceleration
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                desired_speed = speed
                arrive_radius = 120
                if dist < arrive_radius:
                    desired_speed = max(1.0, speed * (dist / arrive_radius))
                target_vx = (dx / dist) * desired_speed
                target_vy = (dy / dist) * desired_speed
                ax = (target_vx - self.vx)
                ay = (target_vy - self.vy)
                max_accel = 0.45
                acc_mag = math.hypot(ax, ay)
                if acc_mag > max_accel:
                    ax = (ax / acc_mag) * max_accel
                    ay = (ay / acc_mag) * max_accel
                self.vx += ax
                self.vy += ay
                # Separation
                sep_force_x = 0.0
                sep_force_y = 0.0
                sep_radius = 40
                sep_radius_sq = sep_radius * sep_radius
                sep_strength = 0.6
                for other in getattr(self, 'game', None).enemies if hasattr(self, 'game') else []:
                    if other is self:
                        continue
                    ox, oy = other.get_position()
                    ox += other.size // 2
                    oy += other.size // 2
                    sx = (self.x + self.size // 2) - ox
                    sy = (self.y + self.size // 2) - oy
                    dsq = sx * sx + sy * sy
                    if 0 < dsq < sep_radius_sq:
                        d = math.sqrt(dsq)
                        sep_force_x += (sx / d) * (sep_strength * (1 - d / sep_radius))
                        sep_force_y += (sy / d) * (sep_strength * (1 - d / sep_radius))
                self.vx += sep_force_x
                self.vy += sep_force_y
                spd = math.hypot(self.vx, self.vy)
                if spd > 0:
                    self.vx = (self.vx / spd) * desired_speed
                    self.vy = (self.vy / spd) * desired_speed
                self.x += self.vx
                self.y += self.vy
        
        # Update hexagon points
        self.points = self._calculate_hexagon_points(self.x, self.y, self.size)
        self.canvas.coords(self.rect, *self.points)
    
    def get_position(self) -> Tuple[float, float]:
        """Return the center coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        self.alive = self.health > 0
        return self.alive

    def cleanup(self) -> None:
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass
        self.alive = False


class BossEnemy(Enemy):
    """
    Represents the final boss - an octagon (8-sided) enemy.
    Takes 20 hits to defeat. Spawns smaller enemies (hexagons and pentagons) when damaged.
    Boss-exclusive mechanics: phases, special attacks, and minion spawning.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize boss enemy at (x, y) with given size."""
        # Initialize as a normal Enemy so boss integrates with enemy systems
        super().__init__(canvas, x, y, size)
        # Remove the default rectangle created by Enemy and replace with boss polygon
        try:
            self.canvas.delete(self.rect)
        except Exception:
            pass
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.sides: int = 8  # Octagon = 8 sides
        self.health: int = 100  # Boss takes 100 hits to kill
        self.max_health: int = 100  # Track original health for phase detection
        self.being_pulled: bool = False
        self.pull_velocity_x: float = 0
        self.pull_velocity_y: float = 0
        self.pull_timer: int = 0
        self.being_pushed: bool = False
        self.push_velocity_x: float = 0
        self.push_velocity_y: float = 0
        self.push_timer: int = 0
        self.shield_immunity: int = 0
        self.is_boss: bool = True  # Flag to identify this as a boss
        self.spawn_counter: int = 0  # Counter for spawning minions on damage
        self.phase: int = 1  # Boss phase (1-3)
        self.phase_change_timer: int = 0  # Timer for phase transitions
        # Roaming behavior (boss does not chase player)
        self.roam_target_x: float = float(x)
        self.roam_target_y: float = float(y)
        self.roam_change_timer: int = random.randint(60, 200)  # frames until pick new roam target
        # Draw octagon using create_polygon with gold/red color
        self.points: List[float] = self._calculate_octagon_points(x, y, size)
        self.rect: int = self.canvas.create_polygon(*self.points, fill='#FFD700', outline='#FF6600', width=3)
    
    def _calculate_octagon_points(self, x: float, y: float, size: int) -> List[float]:
        """Calculate the 8 points of a regular octagon."""
        # Treat (x, y) as the entity's top-left (consistent with other enemies)
        cx = x + (size / 2.0)
        cy = y + (size / 2.0)
        radius = size / 2.0
        points: List[float] = []
        for i in range(8):
            angle = (2 * math.pi * i / 8) - (math.pi / 8)  # Rotated 22.5 degrees
            px = cx + (radius * math.cos(angle))
            py = cy + (radius * math.sin(angle))
            points.extend([px, py])
        return points
    
    def move_towards(self, target_x: float, target_y: float, speed: int = 3) -> None:
        """Roam the arena slowly instead of chasing the player. Ignores provided target."""
        # Apply push force if being pushed by shield
        if self.being_pushed and self.push_timer > 0:
            self.x += self.push_velocity_x
            self.y += self.push_velocity_y
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += self.pull_velocity_x
            self.y += self.pull_velocity_y
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Roaming: ignore provided target and move toward internal roam target
            # Pick a new roam target occasionally
            self.roam_change_timer -= 1
            if self.roam_change_timer <= 0:
                # Determine arena bounds
                gw = getattr(self, 'game', None)
                if gw is not None and hasattr(gw, 'window_width') and hasattr(gw, 'window_height'):
                    win_w = gw.window_width
                    win_h = gw.window_height
                else:
                    # Fallback to constants if game not attached
                    try:
                        from constants import WIDTH as win_w, HEIGHT as win_h
                    except Exception:
                        win_w, win_h = 800, 600
                margin = int(self.size * 1.5)
                self.roam_target_x = random.randint(margin, max(margin+1, win_w - margin))
                self.roam_target_y = random.randint(margin, max(margin+1, win_h - margin))
                self.roam_change_timer = random.randint(120, 360)

            dx = self.roam_target_x - self.x
            dy = self.roam_target_y - self.y
            dist = math.hypot(dx, dy)
            # Boss moves slowly; lower speed to 0.6 by default
            boss_speed = 0.6
            if dist > 0:
                target_vx = (dx / dist) * boss_speed
                target_vy = (dy / dist) * boss_speed
                steer = 0.12
                self.vx += (target_vx - self.vx) * steer
                self.vy += (target_vy - self.vy) * steer
                wobble = 0.02
                self.vx += (random.random() - 0.5) * wobble
                self.vy += (random.random() - 0.5) * wobble
                spd = math.hypot(self.vx, self.vy)
                if spd > boss_speed:
                    self.vx = (self.vx / spd) * boss_speed
                    self.vy = (self.vy / spd) * boss_speed
                self.x += self.vx
                self.y += self.vy
        
        # Update octagon points
        self.points = self._calculate_octagon_points(self.x, self.y, self.size)
        self.canvas.coords(self.rect, *self.points)
    
    def get_position(self) -> Tuple[float, float]:
        """Return the center coordinates of the boss for collision."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if boss is still alive. Spawns minions on phase changes."""
        self.health -= 1
        self.spawn_counter += 1
        
        # Update color based on health phase
        health_percent = self.health / self.max_health
        if health_percent > 0.66:
            color = '#FFD700'  # Gold
        elif health_percent > 0.33:
            color = '#FF8C00'  # Dark orange
        else:
            color = '#FF4500'  # Red-orange
        
        self.canvas.itemconfig(self.rect, fill=color)
        
        # Spawn minions at phase changes (every ~7 hits)
        if self.spawn_counter >= 7:
            self.spawn_counter = 0
            return True  # Still alive, minions will be spawned by game
        
        self.alive = self.health > 0
        return self.alive
    
    def get_phase(self) -> int:
        """Get current boss phase based on health."""
        health_percent = self.health / self.max_health
        if health_percent > 0.66:
            return 1
        elif health_percent > 0.33:
            return 2
        else:
            return 3

    def cleanup(self) -> None:
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass
        self.alive = False


class Particle(BaseEntity):
    """
    Represents a particle in a death poof effect.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, life: int) -> None:
        """Initialize particle at (x, y) with velocity (vx, vy) and lifespan."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.life: int = life
        self.max_life: int = life
        self.rect: int = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='orange')

    def update(self) -> bool:
        """Update particle position and lifespan."""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        # Fade out effect by changing color
        fade = int(255 * (self.life / self.max_life))
        self.canvas.itemconfig(self.rect, fill=f'#{fade:02x}{min(fade//2, 100):02x}00')
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        self.canvas.coords(self.rect,
                   off_x + (self.x - 2) * scale,
                   off_y + (self.y - 2) * scale,
                   off_x + (self.x + 2) * scale,
                   off_y + (self.y + 2) * scale)
        return self.life > 0

    def reset(self, x: float, y: float, vx: float, vy: float, life: int) -> None:
        """Reset particle for reuse from object pool."""
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        # Show the particle again (it may be hidden)
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        self.canvas.coords(self.rect,
                   off_x + (x - 2) * scale,
                   off_y + (y - 2) * scale,
                   off_x + (x + 2) * scale,
                   off_y + (y + 2) * scale)
        self.canvas.itemconfig(self.rect, fill='orange', state='normal')
    
    def cleanup(self) -> None:
        """Hide particle (don't delete for object pooling)."""
        try:
            # Hide instead of delete for object pooling
            self.canvas.itemconfig(self.rect, state='hidden')
        except tk.TclError:
            pass  # Canvas item may have already been deleted
        self.alive = False


class Shard(BaseEntity):
    """
    Represents a shrapnel shard that scatters from a projectile impact.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, game: Any, 
                 lifetime: int = 1000, explosive: bool = False) -> None:
        """Initialize shard at (x, y) with velocity (vx, vy) and lifetime in milliseconds."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.game: Any = game
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.lifetime: int = lifetime  # milliseconds
        self.time_alive: int = 0
        self.explosive: bool = explosive  # Whether this shard explodes on impact
        self.rect: int = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='white' if not explosive else 'red')
    
    def update(self) -> bool:
        """Update shard position and lifetime, check for enemy collisions."""
        self.time_alive += 20  # Update is called every 20ms
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Apply gravity/slow down
        self.vx *= 0.98
        self.vy *= 0.98
        
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        self.canvas.coords(self.rect,
                   off_x + (self.x - 2) * scale,
                   off_y + (self.y - 2) * scale,
                   off_x + (self.x + 2) * scale,
                   off_y + (self.y + 2) * scale)
        
        # Check for enemy collision
        for enemy in self.game.enemies[:]:  # Use slice to avoid modification during iteration
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < COLLISION_DISTANCE_SQ:
                # Hit enemy!
                enemy_dies = False  # Assume enemy survives by default
                
                # All enemies can now take damage
                if hasattr(enemy, 'take_damage'):
                    if not enemy.take_damage():
                        # Enemy is now dead (take_damage returns False when health <= 0)
                        enemy_dies = True
                
                if enemy_dies:
                    # Create poof effect only when enemy dies
                    self.game.create_death_poof(ex_center, ey_center)
                    # Remove enemy and award XP
                    self.game.kill_enemy(enemy)
                # If explosive shrapnel, create explosion effect with more shards
                if self.explosive:
                    self.game.create_explosive_shrapnel(ex_center, ey_center)
                
                # Despawn shard after hitting one enemy (whether it dies or not)
                return False
        
        # Check if lifetime expired
        return self.time_alive < self.lifetime
    def cleanup(self) -> None:
        """Remove shard from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted
        self.alive = False


class Projectile(BaseEntity):
    """
    Represents a projectile that ricochets between enemies with homing effect.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, game: Any) -> None:
        """Initialize projectile at (x, y) with velocity (vx, vy)."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.game: Any = game
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.rect: int = self.canvas.create_oval(x-4, y-4, x+4, y+4, fill='yellow')
        self.hit_enemies: Set[int] = set()  # Track enemies already hit
        self.bounces: int = 0
        # Get weapon stats from game's computed stats
        stats: Dict[str, Any] = game.computed_weapon_stats
        self.max_bounces: int = stats.get('bounces', 0)
        self.allow_splits: bool = stats.get('splits', False)
        self.shrapnel_level: int = stats.get('shrapnel', 0)
        self.homing_strength: float = stats.get('homing', 0.15)
        self.speed: int = stats.get('projectile_speed', 16)  # Use weapon stat speed, not calculated speed
        self.return_speed: int = stats.get('return_speed', 20)  # Speed at which projectile returns to player
        self.chain_lightning_level: int = stats.get('chain_lightning', 0)  # Chain lightning upgrade level
        self.black_hole_level: int = stats.get('black_hole', 0)  # Black hole upgrade level
        self.current_target: Optional[Any] = self._find_closest_target()  # Initial target for homing
        self.time_alive: int = 0  # Track lifetime in milliseconds
        self.returning: bool = False  # Whether projectile is returning to player
        self.is_mini_fork: bool = False  # Whether this is a mini-fork that can only chain once
        self.max_distance: float = stats.get('attack_range', 500)  # Maximum distance before returning
        self.distance_traveled: float = 0  # Track distance from spawn point
        # Base timeout is 500ms with base speed 6 (for 50 FPS logic)
        # Scale timeout inversely with speed so faster projectiles return sooner, maintaining same range
        base_speed = 6
        self.timeout_ms: int = int(500 * (base_speed / self.speed))  # Faster speed = shorter timeout

    def update(self) -> bool:
        """Update projectile position and check for collisions."""
        # Track lifetime
        self.time_alive += 20  # Update is called every 20ms
        
        # If not already returning, check if time limit exceeded
        if not self.returning and self.time_alive >= self.timeout_ms:
            self.returning = True
        
        # Return animation
        if self.returning:
            px, py = self.game.player.get_center()
            dx = px - self.x
            dy = py - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 15:  # Reached player (increased from 10)
                return False
            
            # Move towards player at return speed (upgradeable via weapon stats)
            move_distance = min(self.return_speed, dist)  # Don't move more than distance to player
            if dist > 0:
                self.x += (dx / dist) * move_distance
                self.y += (dy / dist) * move_distance
            self.canvas.coords(self.rect, self.x-4, self.y-4, self.x+4, self.y+4)
            # Change color to cyan when returning
            self.canvas.itemconfig(self.rect, fill='cyan')
            return True
        
        # Apply homing if we have a target
        if self.current_target and self.current_target in self.game.enemies:
            tx, ty = self.current_target.get_position()
            half = getattr(self.current_target, 'size', ENEMY_SIZE) // 2
            tx_center = tx + half
            ty_center = ty + half
            dx = tx_center - self.x
            dy = ty_center - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                # Blend current velocity with direction to target
                target_vx = (dx / dist) * self.speed
                target_vy = (dy / dist) * self.speed
                self.vx += (target_vx - self.vx) * self.homing_strength
                self.vy += (target_vy - self.vy) * self.homing_strength
        elif self.current_target:
            # Target is dead, find a new one
            self.current_target = self._find_next_target()
        
        # Calculate movement distance
        movement_dist = math.hypot(self.vx, self.vy)
        
        # Normal movement
        self.x += self.vx
        self.y += self.vy
        self.distance_traveled += movement_dist
        
        # Render-time scaling
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        self.canvas.coords(self.rect,
                   off_x + (self.x - 4) * scale,
                   off_y + (self.y - 4) * scale,
                   off_x + (self.x + 4) * scale,
                   off_y + (self.y + 4) * scale)
        
        # Check for enemy collision - account for variable enemy sizes and high-speed tunneling
        closest_enemy = None
        closest_dist_sq = float('inf')
        proj_radius = 4  # projectile drawn as oval with ±4
        # previous position (before this frame's movement) for segment collision checks
        prev_x = self.x - self.vx
        prev_y = self.y - self.vy

        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half

            # collision radius is sum of enemy half-size and projectile radius
            coll_r = half + proj_radius
            coll_r_sq = coll_r * coll_r

            # Check current position first
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy

            hit = False
            if dist_sq <= coll_r_sq:
                hit = True
            else:
                # Also check segment from previous position to current position to avoid tunneling
                # Compute squared distance from circle center to segment
                vx = self.x - prev_x
                vy = self.y - prev_y
                if vx == 0 and vy == 0:
                    seg_dist_sq = dist_sq
                else:
                    t = ((ex_center - prev_x) * vx + (ey_center - prev_y) * vy) / (vx*vx + vy*vy)
                    t = max(0.0, min(1.0, t))
                    proj_x = prev_x + vx * t
                    proj_y = prev_y + vy * t
                    dx2 = ex_center - proj_x
                    dy2 = ey_center - proj_y
                    seg_dist_sq = dx2*dx2 + dy2*dy2
                if seg_dist_sq <= coll_r_sq:
                    hit = True

            if hit and dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_enemy = enemy
        
        if closest_enemy:
            # Hit enemy!
            ex, ey = closest_enemy.get_position()
            half = getattr(closest_enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            
            # All enemies can now take damage (sides = health)
            # Triangle (3 sides) = 3 health, Square (4 sides) = 4 health, Pentagon (5 sides) = 5 health
            enemy_dies = False  # Assume enemy survives by default
            
            # Check if enemy has take_damage method (all do now)
            if hasattr(closest_enemy, 'take_damage'):
                if not closest_enemy.take_damage():
                    # Enemy is now dead (take_damage returns False when health <= 0)
                    enemy_dies = True
            
            if enemy_dies:
                # Create poof effect only when enemy dies
                self.game.create_death_poof(ex_center, ey_center)
                # Create shrapnel if upgrade is active (on every hit, not just final kill)
                if self.shrapnel_level > 0:
                    self.game.create_shrapnel(ex_center, ey_center, self.vx, self.vy, self.shrapnel_level)
                
                # Handle hexagon split mechanic
                if isinstance(closest_enemy, HexagonEnemy):
                    # Spawn 3 triangle enemies that explode outward
                    spawn_offset = 20
                    for angle_offset in [0, 120, 240]:  # Spawn at 120 degree intervals
                        angle_rad = math.radians(angle_offset)
                        spawn_x = ex_center + int(spawn_offset * math.cos(angle_rad)) - ENEMY_SIZE_HALF
                        spawn_y = ey_center + int(spawn_offset * math.sin(angle_rad)) - ENEMY_SIZE_HALF
                        # Create new triangle enemy
                        new_triangle = TriangleEnemy(self.game.canvas, spawn_x, spawn_y, ENEMY_SIZE)
                        # Give triangle an outward velocity for the "pop" effect
                        new_triangle.pop_velocity_x = math.cos(angle_rad) * 4.0  # Outward velocity
                        new_triangle.pop_velocity_y = math.sin(angle_rad) * 4.0
                        new_triangle.pop_distance = 0  # Track distance traveled in pop
                        new_triangle.pop_distance_max = 60  # Pop for 60 pixels
                        self.game.enemies.append(new_triangle)
                        print(f"[ACTION] Hexagon split into triangles")
                
                # Handle boss defeat - boss does not split, just dies
                if isinstance(closest_enemy, BossEnemy):
                    print(f"[BOSS] Boss defeated!")
                
                # Remove enemy and award XP using game's method
                self.game.kill_enemy(closest_enemy)
                
                # Play kill sound asynchronously
                print(f"[ACTION] Projectile killed enemy")
                play_beep_async(250, 20, self.game)
            else:
                # Enemy took damage but survived
                if self.shrapnel_level > 0:
                    self.game.create_shrapnel(ex_center, ey_center, self.vx, self.vy, self.shrapnel_level)
                
                # Award partial XP for hitting boss even if it survives
                if isinstance(closest_enemy, BossEnemy):
                    xp_reward = 1  # Small XP for each hit on boss
                    self.game.add_xp(xp_reward)
            
            # Mark as hit
            self.hit_enemies.add(id(closest_enemy))
            
            # Black hole: Check if we should spawn a black hole on this hit
            if self.black_hole_level > 0:
                # Delegate to WeaponSystem
                self.game.weapon.try_spawn_black_hole(ex_center, ey_center)
            
            # Chain lightning: On initial hit only, trigger centralized handling
            if self.chain_lightning_level > 0 and not self.is_mini_fork and self.bounces == 0:
                self.game.weapon.handle_chain_lightning(closest_enemy, (ex_center, ey_center))
            
            # Regular bouncing (only if we have bounces left) - happens after chain lightning
            # Chain lightning doesn't prevent normal bouncing
            
            # Mini-fork chains end after one hit (don't continue bouncing)
            if self.is_mini_fork:
                self.returning = True
                return True
            
            self.bounces += 1
            # Extend return timer by 500ms for each ricochet
            self.time_alive -= 500
            
            # If bounces exhausted, projectile returns
            if self.bounces > self.max_bounces:
                self.returning = True
                return True
            
            # Find next target for ricochet
            next_target = self._find_next_target()
            if next_target:
                tx, ty = next_target.get_position()
                half = getattr(next_target, 'size', ENEMY_SIZE) // 2
                tx_center = tx + half
                ty_center = ty + half
                dx = tx_center - self.x
                dy = ty_center - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.vx = (dx / dist) * self.speed
                    self.vy = (dy / dist) * self.speed
                self.current_target = next_target
                # Note: Don't create splits on bounces, only on initial shot
            else:
                self.returning = True  # Start returning if no more targets
                return True
        
        # Out of bounds - use canvas dimensions, not global WIDTH/HEIGHT
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if self.x < 0 or self.x > canvas_width or self.y < 0 or self.y > canvas_height:
            return False
        
        return True
    
    def _find_closest_target(self) -> Optional[Any]:
        """Find the closest unhit enemy for initial homing."""
        closest: Optional[Any] = None
        closest_dist_sq: float = float('inf')
        for enemy in self.game.enemies:
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest = enemy
        return closest
    
    def _find_next_target(self) -> Optional[Any]:
        """Find the closest unhit enemy for ricochet within range."""
        closest: Optional[Any] = None
        closest_dist_sq: float = float('inf')
        max_range_sq = RICOCHET_RANGE ** 2
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < closest_dist_sq and dist_sq < max_range_sq:
                closest_dist_sq = dist_sq
                closest = enemy
        return closest
    
    def _find_nearby_enemies_for_chain(self, chain_range: int = 150) -> List[Any]:
        """Find nearby unhit enemies for chain lightning (within range)."""
        nearby: List[Tuple[float, Any]] = []
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            if dist < chain_range:
                nearby.append((dist, enemy))
        # Return sorted by distance (closest first)
        return [enemy for dist, enemy in sorted(nearby, key=lambda x: x[0])]
    
    def _strike_lightning_target(self, target_enemy: Any) -> None:
        """Strike a target enemy with chain lightning, dealing damage and effects."""
        if target_enemy not in self.game.enemies:
            return  # Enemy already dead
        
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE_HALF
        ty_center = ty + ENEMY_SIZE_HALF
        
        # All enemies can now take damage
        enemy_dies = False  # Assume enemy survives by default
        
        if hasattr(target_enemy, 'take_damage'):
            if not target_enemy.take_damage():
                # Enemy is now dead (take_damage returns False when health <= 0)
                enemy_dies = True
        
        if enemy_dies:
            # Create poof effect only when enemy dies
            self.game.create_death_poof(tx_center, ty_center)
            # Create shrapnel if upgrade is active (only on final kill)
            if self.shrapnel_level > 0:
                self.game.create_shrapnel(tx_center, ty_center, self.vx, self.vy, self.shrapnel_level)
            
            # Remove enemy and award XP
            self.game.kill_enemy(target_enemy)
            
            # Play kill sound asynchronously
            print(f"[ACTION] Chain lightning killed enemy")
            play_beep_async(250, 20, self.game)
    
    def _create_mini_fork(self, target_enemy: Any) -> None:
        """Create a mini-fork lightning to a target enemy. Mini-forks only chain once."""
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE // 2
        ty_center = ty + ENEMY_SIZE // 2
        # Draw lightning line (magenta for mini-forks) with transform
        scale = self.game.display_scale if self.game.display_scale > 0 else 1.0
        off_x = self.game.offset_x
        off_y = self.game.offset_y
        line_id = self.game.canvas.create_line(
            off_x + self.x * scale, off_y + self.y * scale,
            off_x + tx_center * scale, off_y + ty_center * scale,
            fill='magenta', width=1.5
        )
        
        # Delete the line after a short delay
        def delete_line():
            try:
                self.game.canvas.delete(line_id)
            except tk.TclError:
                pass
        self.game.root.after(100, delete_line)
        
        # Create a new mini-fork projectile that stops after one chain
        mini_fork_proj = Projectile(self.game.canvas, tx_center, ty_center, 0, 0, self.game)
        mini_fork_proj.current_target = target_enemy
        mini_fork_proj.hit_enemies = self.hit_enemies.copy()
        mini_fork_proj.hit_enemies.add(id(target_enemy))  # Mark the target as already hit
        mini_fork_proj.is_mini_fork = True  # Mark as mini-fork so it returns after one hit
        mini_fork_proj.chain_lightning_level = 0  # Mini-forks don't chain
        self.game.projectiles.append(mini_fork_proj)
    
    def _create_fork_from_target(self, target_enemy: Any) -> None:
        """Create a forking lightning from a target enemy, attempting to chain to one nearby enemy."""
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE_HALF
        ty_center = ty + ENEMY_SIZE_HALF
        
        # Find the closest unhit enemy within fork range for this fork to target
        fork_range = 150 + (60 * self.chain_lightning_level) * 0.8  # Reduced range for forks
        fork_range_sq = fork_range * fork_range
        fork_target = None
        fork_target_dist_sq = fork_range_sq
        
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx = ex_center - tx_center
            dy = ey_center - ty_center
            dist_sq = dx * dx + dy * dy
            
            # Only consider enemies within fork range
            if dist_sq < fork_target_dist_sq:
                fork_target_dist_sq = dist_sq
                fork_target = enemy
        
        # If we found a target, create a fork to it
        if fork_target:
            ftx, fty = fork_target.get_position()
            ftx_center = ftx + ENEMY_SIZE_HALF
            fty_center = fty + ENEMY_SIZE_HALF
            
            # Draw fork lightning line (white/bright color for forks) with transform
            scale = self.game.display_scale if self.game.display_scale > 0 else 1.0
            off_x = self.game.offset_x
            off_y = self.game.offset_y
            fork_line_id = self.game.canvas.create_line(
                off_x + tx_center * scale, off_y + ty_center * scale,
                off_x + ftx_center * scale, off_y + fty_center * scale,
                fill='white', width=2
            )
            
            # Delete the fork line after a short delay
            def delete_fork_line():
                try:
                    self.game.canvas.delete(fork_line_id)
                except tk.TclError:
                    pass
            self.game.root.after(150, delete_fork_line)
            
            # Strike the fork target
            self._strike_lightning_target(fork_target)
    
    def _try_spawn_black_hole(self, x: float, y: float) -> None:
        """Deprecated: use WeaponSystem.try_spawn_black_hole."""
        self.game.weapon.try_spawn_black_hole(x, y)
    
    def _create_split_projectiles(self) -> None:
        """Create two split projectiles branching off at angles (delegated)."""
        self.game.weapon.create_split_projectiles(self.x, self.y, self.vx, self.vy)
    
    def cleanup(self) -> None:
        """Remove projectile from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted
        self.alive = False


class Minion(BaseEntity):
    """
    Represents a friendly minion that follows the player and attacks nearby enemies.
    Summoned by the summon_minion upgrade.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, game: Any, minion_size: int = 12) -> None:
        """Initialize minion at (x, y)."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.game: Any = game
        self.x: float = x
        self.y: float = y
        self.vx: float = 0  # Velocity x
        self.vy: float = 0  # Velocity y
        self.size: int = minion_size
        self.max_speed: int = 2  # Slightly slower than player (scaled for 50 FPS logic)
        self.follow_distance: int = 100  # Max distance from player to maintain follow
        self.aggro_range: int = 200  # Range to detect enemies for engagement
        self.aggro_drop_distance: int = 250  # Distance from player to drop aggro and return
        self.attack_range: int = 120  # Distance to engage enemies
        self.attack_cooldown: int = 0  # Milliseconds until next attack
        self.attack_cooldown_reset: int = 600  # Attack every 600ms
        self.current_target: Optional[Any] = None  # Current enemy being engaged
        
        # Patrol behavior - minions wander around when near player but idle
        self.patrol_timer: int = 0  # Countdown to next patrol waypoint change
        self.patrol_interval: int = random.randint(2000, 4000)  # Time between patrol waypoint changes (2-4 seconds, randomized)
        self.patrol_waypoint_x: float = x  # Current patrol target x
        self.patrol_waypoint_y: float = y  # Current patrol target y
        self.patrol_radius: int = 60  # How far from player's last known position to patrol
        
        # Visual representation - green circle for minion
        self.rect: int = self.canvas.create_oval(
            x - self.size // 2, y - self.size // 2,
            x + self.size // 2, y + self.size // 2,
            fill='lime'
        )

    def update(self) -> bool:
        """Update minion position and attack logic. Returns True if minion should persist."""
        # Update attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 20  # Update is called every 20ms
        
        # Get player position
        px, py = self.game.player.get_center()
        dx_to_player = px - self.x
        dy_to_player = py - self.y
        dist_to_player = math.hypot(dx_to_player, dy_to_player)
        
        # Check if current target is still valid (alive and in range)
        if self.current_target:
            if self.current_target not in self.game.enemies:
                # Target died, drop aggro
                self.current_target = None
            else:
                # Check if target is still within aggro drop distance from player
                ex, ey = self.current_target.get_position()
                ex_center = ex + ENEMY_SIZE_HALF
                ey_center = ey + ENEMY_SIZE_HALF
                target_dist_from_player = math.hypot(ex_center - px, ey_center - py)
                
                if target_dist_from_player > self.aggro_drop_distance:
                    # Target is too far from player, drop aggro and return
                    self.current_target = None
        
        # If no current target, look for enemies in aggro range (around player, not minion)
        if not self.current_target:
            # Find enemies in aggro range and pick one (with some randomness for independence)
            nearby_enemies = []
            aggro_range_sq = self.aggro_range * self.aggro_range
            
            for enemy in self.game.enemies:
                ex, ey = enemy.get_position()
                ex_center = ex + ENEMY_SIZE_HALF
                ey_center = ey + ENEMY_SIZE_HALF
                
                # Check distance from PLAYER, not minion
                dx = ex_center - px
                dy = ey_center - py
                dist_sq = dx * dx + dy * dy
                
                if dist_sq < aggro_range_sq:
                    nearby_enemies.append(enemy)
            
            if nearby_enemies:
                # Pick a random enemy from nearby ones for more independent behavior
                self.current_target = random.choice(nearby_enemies)
        
        # Calculate repulsion from other minions and enemies
        repulsion_x = 0.0
        repulsion_y = 0.0
        min_distance = 25  # Minions try to stay this far apart (reduced for more independence)
        repulsion_strength = 0.08  # Weaker repulsion for more independent movement
        
        # Repulsion from other minions
        for other_minion in self.game.minions:
            if other_minion is self:
                continue
            
            ox, oy = other_minion.get_position()
            dx_other = self.x - ox
            dy_other = self.y - oy
            dist_to_other = math.hypot(dx_other, dy_other)
            
            # If too close, push away
            if dist_to_other < min_distance and dist_to_other > 0:
                # Direction away from other minion
                repulsion_x += (dx_other / dist_to_other) * repulsion_strength
                repulsion_y += (dy_other / dist_to_other) * repulsion_strength
        
        # Repulsion from enemies (push minions away from hostile enemies)
        enemy_min_distance = 50  # Keep distance from enemies
        enemy_repulsion_strength = 0.2  # Reduced for more aggressive behavior
        
        for enemy in self.game.enemies:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx_enemy = self.x - ex_center
            dy_enemy = self.y - ey_center
            dist_to_enemy = math.hypot(dx_enemy, dy_enemy)
            
            # If too close to an enemy, push away
            if dist_to_enemy < enemy_min_distance and dist_to_enemy > 0:
                # Direction away from enemy
                repulsion_x += (dx_enemy / dist_to_enemy) * enemy_repulsion_strength
                repulsion_y += (dy_enemy / dist_to_enemy) * enemy_repulsion_strength
        
        # Apply repulsion to velocity
        self.vx += repulsion_x
        self.vy += repulsion_y
        
        # Movement logic: either chase target or follow player
        if self.current_target:
            # Move towards current target
            ex, ey = self.current_target.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx_to_target = ex_center - self.x
            dy_to_target = ey_center - self.y
            dist_to_target = math.hypot(dx_to_target, dy_to_target)
            
            if dist_to_target > 0:
                # Move towards target
                target_vx = (dx_to_target / dist_to_target) * self.max_speed
                target_vy = (dy_to_target / dist_to_target) * self.max_speed
                
                # Smoothly blend velocity toward target
                self.vx += (target_vx - self.vx) * 0.2
                self.vy += (target_vy - self.vy) * 0.2
        else:
            # No target: follow player if too far
            if dist_to_player > self.follow_distance:
                # Apply acceleration towards player
                target_vx = (dx_to_player / dist_to_player) * self.max_speed
                target_vy = (dy_to_player / dist_to_player) * self.max_speed
                
                # Smoothly blend velocity toward target
                self.vx += (target_vx - self.vx) * 0.2
                self.vy += (target_vy - self.vy) * 0.2
            else:
                # Close enough to player: patrol behavior instead of standing still
                self._update_patrol(px, py)
        
        # Clamp velocity to max speed
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            self.vx = (self.vx / speed) * self.max_speed
            self.vy = (self.vy / speed) * self.max_speed
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Clamp to screen bounds (with some margin)
        margin = 20
        if self.x < margin:
            self.x = margin
        if self.x > self.game.window_width - margin:
            self.x = self.game.window_width - margin
        if self.y < margin:
            self.y = margin
        if self.y > self.game.window_height - margin:
            self.y = self.game.window_height - margin
        
        # Update canvas position
        self.canvas.coords(
            self.rect,
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.x + self.size // 2,
            self.y + self.size // 2
        )
        
        # Check for enemies in attack range
        if self.attack_cooldown <= 0:
            self._try_attack()
        
        return True  # Minions persist until player dies

    def _try_attack(self) -> None:
        """Find and attack closest enemy within range."""
        closest_enemy = None
        closest_dist_sq = self.attack_range * self.attack_range
        
        for enemy in self.game.enemies:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_enemy = enemy
        
        if closest_enemy:
            self._fire_at_enemy(closest_enemy)
            self.attack_cooldown = self.attack_cooldown_reset

    def _fire_at_enemy(self, enemy: Any) -> None:
        """Fire a minion projectile at the given enemy."""
        ex, ey = enemy.get_position()
        ex_center = ex + ENEMY_SIZE_HALF
        ey_center = ey + ENEMY_SIZE_HALF
        
        # Calculate direction to enemy
        dx = ex_center - self.x
        dy = ey_center - self.y
        dist = math.hypot(dx, dy)
        
        if dist > 0:
            # Create minion projectile
            projectile_speed = 6  # Scaled down for 20ms game tick (was 12 for faster ticks)
            vx = (dx / dist) * projectile_speed
            vy = (dy / dist) * projectile_speed
            
            # Create projectile at minion position
            minion_projectile = MinionProjectile(self.game.canvas, self.x, self.y, vx, vy, self.game)
            self.game.minion_projectiles.append(minion_projectile)
            
            # Play attack sound
            play_beep_async(500, 15, self.game)

    def _update_patrol(self, player_x: float, player_y: float) -> None:
        """Update patrol behavior when minion is idle near player."""
        # Decrement patrol timer
        self.patrol_timer -= 20  # Called every 20ms
        
        # If timer expired, pick new patrol waypoint
        if self.patrol_timer <= 0:
            # Randomize next waypoint around player
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(20, self.patrol_radius)
            
            self.patrol_waypoint_x = player_x + math.cos(angle) * distance
            self.patrol_waypoint_y = player_y + math.sin(angle) * distance
            
            # Clamp waypoint to screen bounds
            margin = 30
            self.patrol_waypoint_x = max(margin, min(self.patrol_waypoint_x, self.game.window_width - margin))
            self.patrol_waypoint_y = max(margin, min(self.patrol_waypoint_y, self.game.window_height - margin))
            
            # Reset timer with new random interval for individuality
            self.patrol_interval = random.randint(1500, 3500)  # Vary the patrol speed
            self.patrol_timer = self.patrol_interval
        
        # Move towards current patrol waypoint
        dx_to_waypoint = self.patrol_waypoint_x - self.x
        dy_to_waypoint = self.patrol_waypoint_y - self.y
        dist_to_waypoint = math.hypot(dx_to_waypoint, dy_to_waypoint)
        
        if dist_to_waypoint > 0:
            # Move slowly towards waypoint (slower than following player)
            patrol_speed = self.max_speed * 0.6  # 60% of normal speed
            patrol_vx = (dx_to_waypoint / dist_to_waypoint) * patrol_speed
            patrol_vy = (dy_to_waypoint / dist_to_waypoint) * patrol_speed
            
            # Blend velocity smoothly
            self.vx += (patrol_vx - self.vx) * 0.15
            self.vy += (patrol_vy - self.vy) * 0.15
        else:
            # At waypoint, apply slight friction
            self.vx *= 0.9
            self.vy *= 0.9

    def cleanup(self) -> None:
        """Remove minion from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted

    def get_position(self) -> Tuple[float, float]:
        """Return the center coordinates of the minion."""
        return self.x, self.y


class MinionProjectile(BaseEntity):
    """
    Represents a projectile fired by a minion.
    Simple projectile that damages enemies on contact.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, game: Any) -> None:
        """Initialize minion projectile at (x, y) with velocity (vx, vy)."""
        super().__init__()
        self.canvas: tk.Canvas = canvas
        self.game: Any = game
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.time_alive: int = 0
        self.max_lifetime: int = 3000  # 3 seconds before despawn
        self.collision_radius: int = 8
        
        # Visual representation - small yellow projectile
        self.rect: int = self.canvas.create_oval(
            x - 3, y - 3,
            x + 3, y + 3,
            fill='yellow'
        )

    def update(self) -> bool:
        """Update projectile position and check for collisions. Returns False if projectile should despawn."""
        # Track lifetime
        self.time_alive += 20  # Update is called every 20ms
        
        # Despawn if lifetime exceeded
        if self.time_alive >= self.max_lifetime:
            return False
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        # Render-time scaling
        scale = getattr(self, 'game', None).display_scale if hasattr(self, 'game') else 1.0
        off_x = getattr(self, 'game', None).offset_x if hasattr(self, 'game') else 0.0
        off_y = getattr(self, 'game', None).offset_y if hasattr(self, 'game') else 0.0
        self.canvas.coords(self.rect,
                   off_x + (self.x - 3) * scale,
                   off_y + (self.y - 3) * scale,
                   off_x + (self.x + 3) * scale,
                   off_y + (self.y + 3) * scale)
        
        # Check bounds - despawn if off screen
        if (self.x < -50 or self.x > self.game.window_width + 50 or
            self.y < -50 or self.y > self.game.window_height + 50):
            return False
        
        # Check for enemy collision
        for enemy in self.game.enemies[:]:
            ex, ey = enemy.get_position()
            half = getattr(enemy, 'size', ENEMY_SIZE) // 2
            ex_center = ex + half
            ey_center = ey + half
            
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < (self.collision_radius + ENEMY_SIZE_HALF) ** 2:
                # Collision! Deal damage to enemy
                enemy_dies = False  # Assume enemy survives by default
                
                # All enemies can now take damage
                if hasattr(enemy, 'take_damage'):
                    if not enemy.take_damage():
                        # Enemy is now dead (take_damage returns False when health <= 0)
                        enemy_dies = True
                
                if enemy_dies:
                    # Create poof effect only when enemy dies
                    self.game.create_death_poof(ex_center, ey_center)
                    # Remove enemy and award XP
                    self.game.kill_enemy(enemy)
                
                # Projectile despawns after hit
                return False
        
        return True

    def cleanup(self) -> None:
        """Remove minion projectile from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted
        self.alive = False

    def get_position(self) -> Tuple[float, float]:
        """Return the position of the projectile."""
        return self.x, self.y
