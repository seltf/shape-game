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
        # Visual representation - only outline, no fill so enemies are visible
        self.rect: int = self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                           fill='', outline='#6600ff', width=2)
        # Animated rings during pull phase
        self.active_rings: List[List[Any]] = []  # Track canvas IDs of active animated rings
        self.ring_spawn_counter: int = 0  # Counter to spawn rings at intervals
    
    def update(self) -> bool:
        """Update black hole and check for detonation."""
        self.time_alive += 50  # Update is called every 50ms
        
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
            ring_id = self.canvas.create_oval(
                self.x - ring_size, self.y - ring_size,
                self.x + ring_size, self.y + ring_size,
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
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
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
        # Spawn a new ring every 400ms (8 updates at 50ms per update)
        self.ring_spawn_counter += 1
        if self.ring_spawn_counter >= 8:
            self.ring_spawn_counter = 0
            self._spawn_new_ring()
        
        # Update all existing rings - shrink them toward center
        rings_to_remove = []
        for ring_data in self.active_rings:
            ring_id, current_size, max_size = ring_data
            
            # Shrink ring by 2 pixels per update (slower animation)
            new_size = current_size - 2
            
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
                    self.canvas.coords(
                        ring_id,
                        self.x - new_size, self.y - new_size,
                        self.x + new_size, self.y + new_size
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
        ring_id = self.canvas.create_oval(
            self.x - ring_size, self.y - ring_size,
            self.x + ring_size, self.y + ring_size,
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
        fling_speed = 12  # Speed to fling enemies outward
        
        for enemy in self.game.enemies[:]:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            radius_sq = self.radius * self.radius
            
            # Apply effect if in radius
            if dist_sq < radius_sq and dist_sq > 0:
                dist = math.sqrt(dist_sq)
                
                # Deal damage based on level: 1 damage at levels 1-4, 2 damage at level 5+
                damage = 2 if self.level >= 5 else 1
                if hasattr(enemy, 'health'):
                    enemy.health -= damage
                else:
                    # Basic enemies have 1 health, so damage kills them
                    enemy.health = -1
                
                # Fling enemy outward from black hole
                # Direction away from black hole
                fling_dir_x = dx / dist
                fling_dir_y = dy / dist
                
                # Apply fling using pull_velocity (which is already integrated into move_towards)
                enemy.pull_velocity_x = fling_dir_x * fling_speed
                enemy.pull_velocity_y = fling_dir_y * fling_speed
                enemy.being_pulled = True
                enemy.pull_timer = 20  # Fling for 20 frames (~1 second)
        
        # Clean up dead enemies
        alive_enemies = []
        for enemy in self.game.enemies:
            if not hasattr(enemy, 'health') or enemy.health > 0:
                alive_enemies.append(enemy)
            else:
                # Remove dead enemy from canvas
                ex, ey = enemy.get_position()
                self.game.create_death_poof(ex + ENEMY_SIZE_HALF, ey + ENEMY_SIZE_HALF)
                self.game.canvas.delete(enemy.rect)
                
                # Award XP based on enemy type
                is_pentagon = isinstance(enemy, PentagonEnemy)
                is_triangle = isinstance(enemy, TriangleEnemy)
                
                if is_pentagon:
                    xp_reward = 7
                elif is_triangle:
                    xp_reward = 3
                else:
                    xp_reward = 1
                self.game.add_xp(xp_reward)
                self.game.score += 1
        
        self.game.enemies = alive_enemies
        
        # Update score display
        self.game.canvas.itemconfig(self.game.score_text, text=str(self.game.score))
    
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
        
        # Update position
        self.x = max(self.size//2, min(window_width-self.size//2, self.x+self.vx))
        self.y = max(self.size//2, min(window_height-self.size//2, self.y+self.vy))
        self.canvas.coords(self.rect, self.x-self.size//2, self.y-self.size//2, self.x+self.size//2, self.y+self.size//2)
        
        # Update shield ring position if active
        # Update shield rings if active
        if self.shield_rings:
            for i, ring in enumerate(self.shield_rings):
                if ring is not None:
                    # Each ring is offset further out
                    shield_radius = self.size // 2 + 15 + (i * 12)
                    self.canvas.coords(ring, 
                                      self.x - shield_radius, self.y - shield_radius,
                                      self.x + shield_radius, self.y + shield_radius)

    def get_center(self) -> Tuple[float, float]:
        """Return the center coordinates of the player circle."""
        return self.x, self.y

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
            push_radius = 150  # Radius to affect enemies
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
                            push_force = 2.5  # Pushback speed per frame
                            nearby_enemy.being_pushed = True
                            nearby_enemy.push_velocity_x = (dx / dist) * push_force
                            nearby_enemy.push_velocity_y = (dy / dist) * push_force
                            nearby_enemy.push_timer = 16  # Push for 16 frames (~0.8 seconds)
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


class Enemy:
    """
    Represents an enemy in the game.
    Handles position, movement towards the player, and rendering.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize enemy at (x, y) with given size."""
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
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

    def move_towards(self, target_x: float, target_y: float, speed: int = 5) -> None:
        """Move enemy towards (target_x, target_y) by 'speed' pixels."""
        # Apply push force if being pushed by shield
        if self.being_pushed and self.push_timer > 0:
            self.x += int(self.push_velocity_x)
            self.y += int(self.push_velocity_y)
            self.push_timer -= 1
            if self.push_timer <= 0:
                self.being_pushed = False
        # Apply pull force if being pulled by black hole
        elif self.being_pulled and self.pull_timer > 0:
            self.x += int(self.pull_velocity_x)
            self.y += int(self.pull_velocity_y)
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement toward target
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += int(dx/dist * speed)
                self.y += int(dy/dist * speed)
        
        self.canvas.coords(self.rect, self.x, self.y, self.x+self.size, self.y+self.size)

    def get_position(self) -> Tuple[float, float]:
        """Return the top-left coordinates of the enemy rectangle."""
        return self.x, self.y


class TriangleEnemy:
    """
    Represents a triangle enemy that takes three hits to defeat.
    Tougher than the basic square enemy.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize triangle enemy at (x, y) with given size."""
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.health: int = 5  # Takes 5 hits to kill
        self.being_pulled: bool = False  # Whether currently pulled by black hole
        self.pull_velocity_x: float = 0  # Pull force direction X
        self.pull_velocity_y: float = 0  # Pull force direction Y
        self.pull_timer: int = 0  # Frames remaining to be pulled
        self.being_pushed: bool = False  # Whether currently pushed by shield
        self.push_velocity_x: float = 0  # Push force direction X
        self.push_velocity_y: float = 0  # Push force direction Y
        self.push_timer: int = 0  # Frames remaining to be pushed
        self.shield_immunity: int = 0  # Frames of immunity after shield hit
        # Draw triangle using create_polygon
        # Triangle points: top center, bottom-left, bottom-right
        self.points: List[float] = [
            x + size//2, y,  # top center
            x, y + size,     # bottom-left
            x + size, y + size  # bottom-right
        ]
        self.rect: int = self.canvas.create_polygon(*self.points, fill='orange')

    def move_towards(self, target_x: float, target_y: float, speed: int = 5) -> None:
        """Move enemy towards (target_x, target_y) by 'speed' pixels."""
        # Apply pull force if being pulled by black hole
        if self.being_pulled and self.pull_timer > 0:
            self.x += int(self.pull_velocity_x)
            self.y += int(self.pull_velocity_y)
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement toward target
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += int(dx/dist * speed)
                self.y += int(dy/dist * speed)
        
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
        return self.health > 0


class PentagonEnemy:
    """
    Represents a pentagon tank enemy that's tougher than triangles.
    Takes many hits but gives good XP.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, size: int) -> None:
        """Initialize pentagon enemy at (x, y) with given size."""
        self.canvas: tk.Canvas = canvas
        self.size: int = size
        self.x: float = x
        self.y: float = y
        self.health: int = 8  # Takes 8 hits to kill (tank)
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
        self.rect: int = self.canvas.create_polygon(*self.points, fill='purple')
    
    def _calculate_pentagon_points(self, x: float, y: float, size: int) -> List[float]:
        """Calculate the 5 points of a regular pentagon."""
        points: List[float] = []
        for i in range(5):
            angle = (2 * math.pi * i / 5) - (math.pi / 2)  # Start from top
            px = x + size//2 + int((size//2) * math.cos(angle))
            py = y + size//2 + int((size//2) * math.sin(angle))
            points.extend([px, py])
        return points
    
    def move_towards(self, target_x: float, target_y: float, speed: int = 5) -> None:
        """Move enemy towards (target_x, target_y) by 'speed' pixels."""
        # Apply pull force if being pulled by black hole
        if self.being_pulled and self.pull_timer > 0:
            self.x += int(self.pull_velocity_x)
            self.y += int(self.pull_velocity_y)
            self.pull_timer -= 1
            if self.pull_timer <= 0:
                self.being_pulled = False
        else:
            # Normal movement toward target
            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += int(dx/dist * speed)
                self.y += int(dy/dist * speed)
        
        # Update pentagon points
        self.points = self._calculate_pentagon_points(self.x, self.y, self.size)
        self.canvas.coords(self.rect, *self.points)
    
    def get_position(self) -> Tuple[float, float]:
        """Return the center coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self) -> bool:
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        return self.health > 0


class Particle:
    """
    Represents a particle in a death poof effect.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, life: int) -> None:
        """Initialize particle at (x, y) with velocity (vx, vy) and lifespan."""
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
        self.canvas.coords(self.rect, self.x-2, self.y-2, self.x+2, self.y+2)
        return self.life > 0

    def cleanup(self) -> None:
        """Remove particle from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted


class Shard:
    """
    Represents a shrapnel shard that scatters from a projectile impact.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, game: Any, 
                 lifetime: int = 1000, explosive: bool = False) -> None:
        """Initialize shard at (x, y) with velocity (vx, vy) and lifetime in milliseconds."""
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
        self.time_alive += 50  # Update is called every 50ms
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Apply gravity/slow down
        self.vx *= 0.98
        self.vy *= 0.98
        
        self.canvas.coords(self.rect, self.x-2, self.y-2, self.x+2, self.y+2)
        
        # Check for enemy collision
        for enemy in self.game.enemies[:]:  # Use slice to avoid modification during iteration
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < COLLISION_DISTANCE_SQ:
                # Hit enemy!
                self.game.create_death_poof(ex_center, ey_center)
                
                # Check if it's a tank or triangle enemy (they take damage)
                is_pentagon = isinstance(enemy, PentagonEnemy)
                is_triangle = isinstance(enemy, TriangleEnemy)
                enemy_dies = True
                
                if is_pentagon or is_triangle:
                    # Tank/triangle enemy takes damage but might survive
                    if enemy.take_damage():
                        # Still alive after damage
                        enemy_dies = False
                    else:
                        # Enemy is now dead
                        enemy_dies = True
                
                if enemy_dies:
                    # Remove enemy
                    self.game.enemies.remove(enemy)
                    self.game.canvas.delete(enemy.rect)
                    self.game.score += 1
                    self.game.canvas.itemconfig(self.game.score_text, text=str(self.game.score))
                # Award XP for kill (7 for pentagon, 3 for triangle, 1 for regular)
                if is_pentagon:
                    xp_reward = 7
                elif is_triangle:
                    xp_reward = 3
                else:
                    xp_reward = 1
                self.game.add_xp(xp_reward)
                print(f"[ACTION] Enemy taking damage from black hole")
                play_beep_async(250, 20, self.game)                # If explosive shrapnel, create explosion effect with more shards
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
            pass  # Canvas item may have already been deleted


class Projectile:
    """
    Represents a projectile that ricochets between enemies with homing effect.
    """
    def __init__(self, canvas: tk.Canvas, x: float, y: float, vx: float, vy: float, game: Any) -> None:
        """Initialize projectile at (x, y) with velocity (vx, vy)."""
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
        self.chain_lightning_level: int = stats.get('chain_lightning', 0)  # Chain lightning upgrade level
        self.black_hole_level: int = stats.get('black_hole', 0)  # Black hole upgrade level
        self.current_target: Optional[Any] = self._find_closest_target()  # Initial target for homing
        self.time_alive: int = 0  # Track lifetime in milliseconds
        self.returning: bool = False  # Whether projectile is returning to player
        self.is_mini_fork: bool = False  # Whether this is a mini-fork that can only chain once
        self.max_distance: float = stats.get('attack_range', 500)  # Maximum distance before returning
        self.distance_traveled: float = 0  # Track distance from spawn point
        # Calculate timeout: use extended timeout only if attack_range upgraded beyond base
        # Base timeout: 500ms (0.5 seconds - original behavior)
        # If attack_range > 500, scale timeout based on distance
        if self.max_distance > 500:
            self.timeout_ms: int = int((self.max_distance / self.speed) * 50 * 1.5)  # 1.5x safety multiplier
        else:
            self.timeout_ms: int = 500  # Base timeout unchanged

    def update(self) -> bool:
        """Update projectile position and check for collisions."""
        # Track lifetime
        self.time_alive += 50  # Update is called every 50ms
        
        # Check if projectile has traveled beyond max range first (distance check takes priority)
        if not self.returning and self.distance_traveled > self.max_distance:
            self.returning = True
        # If not already returning, check if time limit exceeded (scaled by distance)
        elif not self.returning and self.time_alive >= self.timeout_ms:
            self.returning = True
        
        # Return animation
        if self.returning:
            px, py = self.game.player.get_center()
            dx = px - self.x
            dy = py - self.y
            dist = math.hypot(dx, dy)
            
            if dist < 15:  # Reached player (increased from 10)
                return False
            
            # Move towards player at fast speed, but don't overshoot
            return_speed = 50
            move_distance = min(return_speed, dist)  # Don't move more than distance to player
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
            tx_center = tx + ENEMY_SIZE_HALF
            ty_center = ty + ENEMY_SIZE_HALF
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
        
        self.x += self.vx
        self.y += self.vy
        # Track total distance traveled from spawn point
        self.distance_traveled += math.hypot(self.vx, self.vy)
        self.canvas.coords(self.rect, self.x-4, self.y-4, self.x+4, self.y+4)
        
        # Check for enemy collision - use squared distances to avoid sqrt
        closest_enemy = None
        closest_dist_sq = COLLISION_DISTANCE_SQ
        
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy  # Squared distance (avoid sqrt)
            
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_enemy = enemy
        
        if closest_enemy:
            # Hit enemy!
            ex, ey = closest_enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            # Create poof effect
            self.game.create_death_poof(ex_center, ey_center)
            
            # Check if it's a tank or triangle enemy (they take damage)
            is_pentagon = isinstance(closest_enemy, PentagonEnemy)
            is_triangle = isinstance(closest_enemy, TriangleEnemy)
            enemy_dies = True
            
            if is_pentagon or is_triangle:
                # Tank/triangle enemy takes damage but might survive
                if closest_enemy.take_damage():
                    # Still alive after damage
                    enemy_dies = False
                    # Don't award XP until it actually dies
                else:
                    # Enemy is now dead
                    enemy_dies = True
            
            if enemy_dies:
                # Create shrapnel if upgrade is active (on every hit, not just final kill)
                if self.shrapnel_level > 0:
                    self.game.create_shrapnel(ex_center, ey_center, self.vx, self.vy, self.shrapnel_level)
                
                # Remove enemy
                self.game.enemies.remove(closest_enemy)
                self.game.canvas.delete(closest_enemy.rect)
                self.game.score += 1
                self.game.canvas.itemconfig(self.game.score_text, text=str(self.game.score))
                
                # Award XP for kill (7 for pentagon, 3 for triangle, 1 for regular)
                if is_pentagon:
                    xp_reward = 7
                elif is_triangle:
                    xp_reward = 3
                else:
                    xp_reward = 1
                self.game.add_xp(xp_reward)
                
                # Play kill sound asynchronously
                print(f"[ACTION] Projectile killed enemy")
                play_beep_async(250, 20, self.game)
            else:
                # Enemy took damage but survived - create shrapnel anyway if upgrade active
                if self.shrapnel_level > 0:
                    self.game.create_shrapnel(ex_center, ey_center, self.vx, self.vy, self.shrapnel_level)
            
            # Mark as hit
            self.hit_enemies.add(id(closest_enemy))
            
            # Black hole: Check if we should spawn a black hole on this hit
            if self.black_hole_level > 0:
                self._try_spawn_black_hole(ex_center, ey_center)
            
            # Chain lightning: On initial hit only, trigger a chain through level number of targets
            if self.chain_lightning_level > 0 and not self.is_mini_fork and self.bounces == 0:
                # Number of targets to chain through: equal to chain_lightning_level (level 1 = 1 chain, etc.)
                num_chain_targets = self.chain_lightning_level
                
                # Starting range: 150 + (60 * level), decreases by only 20% per bounce
                chain_range = 150 + (60 * self.chain_lightning_level)
                range_multiplier = 0.8  # Each chain reduces range to 80% of previous
                current_range = chain_range
                
                # Build chain path from current enemy, finding closest unhit enemies within range
                chain_targets = []
                current_position = (ex_center, ey_center)
                
                for bounce_index in range(num_chain_targets):
                    # Find closest unhit enemy to current position within current range
                    next_target = None
                    next_dist_sq = current_range * current_range
                    
                    for enemy in self.game.enemies:
                        if id(enemy) in self.hit_enemies:
                            continue
                        ex, ey = enemy.get_position()
                        ex_center_i = ex + ENEMY_SIZE_HALF
                        ey_center_i = ey + ENEMY_SIZE_HALF
                        
                        dx = ex_center_i - current_position[0]
                        dy = ey_center_i - current_position[1]
                        dist_sq = dx * dx + dy * dy
                        
                        # Only consider enemies within current range (use squared distance)
                        if dist_sq < next_dist_sq:
                            next_dist_sq = dist_sq
                            next_target = enemy
                    
                    if next_target is None:
                        break  # No more enemies to chain to within range
                    
                    chain_targets.append((next_target, bounce_index))  # Store target with its bounce index
                    self.hit_enemies.add(id(next_target))
                    next_pos = (next_target.get_position()[0] + ENEMY_SIZE_HALF,
                              next_target.get_position()[1] + ENEMY_SIZE_HALF)
                    current_position = next_pos
                    
                    # Reduce range for next chain (range falloff)
                    current_range *= range_multiplier
                
                # Draw lightning chain and strike all targets
                if chain_targets:
                    # Draw lines connecting the chain
                    current_ex, current_ey = closest_enemy.get_position()
                    current_center = (current_ex + ENEMY_SIZE_HALF, current_ey + ENEMY_SIZE_HALF)
                    
                    for chain_target, bounce_index in chain_targets:
                        tx, ty = chain_target.get_position()
                        tx_center = (tx + ENEMY_SIZE_HALF, ty + ENEMY_SIZE_HALF)
                        
                        # Draw lightning line
                        line_id = self.game.canvas.create_line(
                            current_center[0], current_center[1],
                            tx_center[0], tx_center[1],
                            fill='cyan', width=3
                        )
                        
                        # Delete the line after a short delay
                        def delete_line(lid=line_id):
                            try:
                                self.game.canvas.delete(lid)
                            except tk.TclError:
                                pass
                        self.game.root.after(150, delete_line)
                        
                        current_center = tx_center
                    
                    # Strike all chain targets and handle forking on odd bounces
                    for chain_target, bounce_index in chain_targets:
                        # Check if this is an odd bounce (0-indexed, so 0, 2, 4... are odd in visual terms 1, 3, 5...)
                        is_odd_bounce = (bounce_index % 2 == 0)  # First bounce is index 0 (visually "1st" = odd)
                        
                        # Strike the target
                        self._strike_lightning_target(chain_target)
                        
                        # Create fork on odd bounces
                        if is_odd_bounce:
                            self._create_fork_from_target(chain_target)
            
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
                tx_center = tx + ENEMY_SIZE_HALF
                ty_center = ty + ENEMY_SIZE_HALF
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
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest = enemy
        return closest
    
    def _find_next_target(self) -> Optional[Any]:
        """Find the closest unhit enemy for ricochet."""
        closest: Optional[Any] = None
        closest_dist_sq: float = float('inf')
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx = ex_center - self.x
            dy = ey_center - self.y
            dist_sq = dx * dx + dy * dy
            if dist_sq < closest_dist_sq:
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
        
        # Create poof effect at the target
        self.game.create_death_poof(tx_center, ty_center)
        
        # Check if it's a tank or triangle enemy
        is_pentagon = isinstance(target_enemy, PentagonEnemy)
        is_triangle = isinstance(target_enemy, TriangleEnemy)
        enemy_dies = True
        
        if is_pentagon or is_triangle:
            # Tank/triangle enemy takes damage but might survive
            if target_enemy.take_damage():
                # Still alive after damage
                enemy_dies = False
            else:
                # Enemy is now dead
                enemy_dies = True
        
        if enemy_dies:
            # Create shrapnel if upgrade is active (only on final kill)
            if self.shrapnel_level > 0:
                self.game.create_shrapnel(tx_center, ty_center, self.vx, self.vy, self.shrapnel_level)
            
            # Remove enemy
            self.game.enemies.remove(target_enemy)
            self.game.canvas.delete(target_enemy.rect)
            self.game.score += 1
            self.game.canvas.itemconfig(self.game.score_text, text=str(self.game.score))
            
            # Award XP for kill (7 for pentagon, 3 for triangle, 1 for regular)
            if is_pentagon:
                xp_reward = 7
            elif is_triangle:
                xp_reward = 3
            else:
                xp_reward = 1
            self.game.add_xp(xp_reward)
            
            # Play kill sound asynchronously
            print(f"[ACTION] Chain lightning killed enemy")
            play_beep_async(250, 20, self.game)
    
    def _create_mini_fork(self, target_enemy: Any) -> None:
        """Create a mini-fork lightning to a target enemy. Mini-forks only chain once."""
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE // 2
        ty_center = ty + ENEMY_SIZE // 2
        
        # Draw lightning line (magenta for mini-forks)
        line_id = self.game.canvas.create_line(
            self.x, self.y, tx_center, ty_center,
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
            
            # Draw fork lightning line (white/bright color for forks)
            fork_line_id = self.game.canvas.create_line(
                tx_center, ty_center,
                ftx_center, fty_center,
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
        """Try to spawn a black hole at the given position based on black hole level."""
        # Only allow one black hole at a time
        if len(self.game.black_holes) > 0:
            return  # Already have a black hole active
        
        # Calculate chance: 15% base at level 1, increases with level
        trigger_chance = BLACK_HOLE_TRIGGER_CHANCE * self.black_hole_level
        
        # Check if we trigger the black hole
        if random.random() > trigger_chance:
            return  # Didn't trigger
        
        # Calculate radius based on level: 40 base + 20 per level
        radius = BLACK_HOLE_BASE_RADIUS + (20 * self.black_hole_level)
        
        # Create the black hole
        black_hole = BlackHole(self.game.canvas, x, y, radius, self.game, self.black_hole_level)
        self.game.black_holes.append(black_hole)
    
    def _create_split_projectiles(self) -> None:
        """Create two split projectiles branching off at angles."""
        # Calculate current velocity angle
        current_angle = math.atan2(self.vy, self.vx)
        split_angle_rad = math.radians(PROJECTILE_SPLIT_ANGLE)
        
        # Create two projectiles at split angles
        for angle_offset in [-split_angle_rad, split_angle_rad]:
            new_angle = current_angle + angle_offset
            new_vx = math.cos(new_angle) * self.speed
            new_vy = math.sin(new_angle) * self.speed
            
            # Create new projectile at current position
            new_projectile = Projectile(self.game.canvas, self.x, self.y, new_vx, new_vy, self.game)
            new_projectile.bounces = self.bounces  # Start at current bounce count
            new_projectile.hit_enemies = self.hit_enemies.copy()  # Copy hit enemies so they don't re-hit
            new_projectile.homing_strength = self.homing_strength
            new_projectile.allow_splits = self.allow_splits
    
    def cleanup(self) -> None:
        """Remove projectile from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted
