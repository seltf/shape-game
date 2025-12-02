import tkinter as tk
import random
import math
import winsound
import threading

def play_beep_async(frequency, duration, game_instance=None):
    """Play a beep asynchronously in a background thread."""
    # Check if sound is enabled (default to True if no game instance)
    if game_instance is not None and not game_instance.sound_enabled:
        return
    
    def beep():
        winsound.Beep(frequency, duration)
    thread = threading.Thread(target=beep, daemon=True)
    thread.start()

TESTING_MODE = False  # Set to True to spawn many enemies for testing weapons

WIDTH, HEIGHT = 600, 400
PLAYER_SIZE = 20
ENEMY_SIZE = 20
INITIAL_ENEMY_COUNT = 10  # Enemies to spawn at game start
TESTING_MODE_ENEMY_COUNT = 100  # Enemies in testing mode
MAX_ENEMY_COUNT = 150  # Maximum enemies allowed
RESPAWN_BATCH_SIZE = 20  # Enemies to spawn per batch
RESPAWN_INTERVAL = 10000  # Milliseconds between batches (10 seconds)
RESPAWN_INTERVAL_MIN = 3000  # Minimum interval at high difficulty (3 seconds)
RESPAWN_BATCH_SCALE = 5  # Milliseconds to reduce interval per minute played
MAX_BOUNCES = 100  # Maximum number of enemy bounces per projectile
DASH_DISTANCE = 60  # How far the dash moves the player
DASH_COOLDOWN = 500  # Milliseconds between dashes
PARTICLE_COUNT = 8  # Particles in death poof effect
PARTICLE_LIFE = 15  # Frames until particle dies
HOMING_STRENGTH = 0.15  # How strongly projectile homes in on target
COLLISION_DISTANCE = 30  # Distance for projectile-enemy collision
PROJECTILE_SPLIT_ANGLE = 30  # Degrees to split projectiles on each bounce
PROJECTILE_LIFETIME = 10000  # Milliseconds before projectile explodes
EXPLOSION_RADIUS = 100  # Pixels for explosion damage radius

WEAPON_STATS = {'projectile_speed': 16, 'homing': 0.30, 'bounces': 0, 'splits': True, 'shrapnel': 0}

# Weapon upgrades - modifiers that can be applied to base weapon
WEAPON_UPGRADES = {
    'extra_bounce': {'bounces': 1, 'name': 'Extra Bounce'},
    'shrapnel': {'shrapnel': 1, 'name': 'Shrapnel'},
    'speed_boost': {'projectile_speed': 3, 'name': 'Speed Boost'},
}

# Linked upgrades - only appear if prerequisite(s) are owned
LINKED_UPGRADES = {
    'explosive_shrapnel': {
        'name': 'Explosive Shrapnel',
        'requires': 'shrapnel',  # Single prerequisite
        'modifiers': {'explosive_shrapnel': 1}
    },
    'chain_lightning': {
        'name': 'Chain Lightning',
        'requires': ['speed_boost', 'extra_bounce'],  # Multiple prerequisites
        'modifiers': {'chain_lightning': 1}
    },
    'fork_lightning': {
        'name': 'Fork Lightning',
        'requires': {'upgrade': 'chain_lightning', 'level': 5},  # Chain lightning at level 5+
        'modifiers': {'fork_lightning': 1}
    }
}

PLAYER_ACCELERATION = 3.5  # How quickly player accelerates
PLAYER_MAX_SPEED = 22  # Maximum player speed
PLAYER_FRICTION = 0.80  # Friction multiplier (0-1, lower = more friction)

# Ability constants
ABILITY_COOLDOWN = 5000  # Milliseconds between ability uses (5 seconds)
BLACK_HOLE_SPEED = 3  # How fast the black hole orb travels
BLACK_HOLE_LIFETIME = 3000  # Milliseconds before detonation (3 seconds)
BLACK_HOLE_DETONATION_DURATION = 5000  # Milliseconds that black hole pulls enemies (5 seconds)
BLACK_HOLE_RADIUS = 200  # Pull radius when detonating (increased from 120)
BLACK_HOLE_PULL_STRENGTH = 15  # Speed at which enemies get pulled in
BLACK_HOLE_MIN_PULL_STRENGTH = 5  # Minimum pull strength at radius edge to prevent getting stuck

class BlackHoleAbility:
    """
    Represents a black hole ability that pulls enemies in when it detonates.
    """
    def __init__(self, canvas, x, y, vx, vy, game):
        """Initialize black hole at (x, y) with velocity (vx, vy)."""
        self.canvas = canvas
        self.game = game
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.time_alive = 0  # Track lifetime in milliseconds
        self.detonated = False
        # Visual representation - dark purple expanding circle
        self.rect = self.canvas.create_oval(x-8, y-8, x+8, y+8, fill='#330033', outline='#6600ff', width=2)
        # Animated rings during pull phase
        self.active_rings = []  # Track canvas IDs of active animated rings
        self.ring_spawn_counter = 0  # Counter to spawn rings at intervals
    
    def update(self):
        """Update black hole position and check for detonation."""
        self.time_alive += 50  # Update is called every 50ms
        
        # Move the black hole (before detonation)
        if not self.detonated:
            self.x += self.vx
            self.y += self.vy
        
        # Update position on canvas
        self.canvas.coords(self.rect, self.x-8, self.y-8, self.x+8, self.y+8)
        
        # Check for detonation time
        if self.time_alive >= BLACK_HOLE_LIFETIME and not self.detonated:
            self.detonate()
        
        # Keep pulling enemies if detonated and within duration
        if self.detonated:
            self._pull_enemies()
            self._update_rings()  # Update animated rings
            # Check if detonation duration expired
            if self.time_alive >= BLACK_HOLE_LIFETIME + BLACK_HOLE_DETONATION_DURATION:
                self._cleanup_rings()  # Clean up any remaining rings
                return False  # Remove after pull duration ends
            return True
        
        # Check for out of bounds (before detonation)
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            return False
        
        return True
    
    def detonate(self):
        """Detonate the black hole, initiating pulling of nearby enemies."""
        self.detonated = True
        
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
        
        # Play detonation sound
        play_beep_async(200, 200, self.game)
    
    def _pull_enemies(self):
        """Pull all nearby enemies toward the black hole."""
        for enemy in self.game.enemies[:]:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            
            # Only pull enemies within pull radius
            if dist < BLACK_HOLE_RADIUS and dist > 0:
                # Pull force decreases with distance but has a minimum to prevent getting stuck
                pull_factor = 1.0 - (dist / BLACK_HOLE_RADIUS)  # 0 to 1
                pull_factor = max(0.33, pull_factor)  # Minimum of 33% strength even at edge
                pull_speed = BLACK_HOLE_PULL_STRENGTH * pull_factor
                
                # Direction toward black hole
                dx = (self.x - ex_center) / dist
                dy = (self.y - ey_center) / dist
                
                # Apply pull continuously during detonation
                enemy.pull_velocity_x = dx * pull_speed
                enemy.pull_velocity_y = dy * pull_speed
                enemy.being_pulled = True
                enemy.pull_timer = 1  # Reset pull timer to 1 frame, we'll refresh it each update
    
    def _update_rings(self):
        """Update animated rings, spawning new ones and shrinking existing ones."""
        # Spawn a new ring every 250ms (5 updates at 50ms per update)
        self.ring_spawn_counter += 1
        if self.ring_spawn_counter >= 5:
            self.ring_spawn_counter = 0
            self._spawn_new_ring()
        
        # Update all existing rings - shrink them toward center
        rings_to_remove = []
        for ring_data in self.active_rings:
            ring_id, current_size, max_size = ring_data
            
            # Shrink ring by 4 pixels per update (slower)
            new_size = current_size - 4
            
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
    
    def _spawn_new_ring(self):
        """Spawn a new animated ring at the edge of the pull radius."""
        ring_size = BLACK_HOLE_RADIUS
        ring_id = self.canvas.create_oval(
            self.x - ring_size, self.y - ring_size,
            self.x + ring_size, self.y + ring_size,
            outline='#6600ff', width=1.5
        )
        # Store ring data as [id, current_size, max_size]
        self.active_rings.append([ring_id, ring_size, ring_size])
    
    def _cleanup_rings(self):
        """Remove all animated rings from canvas."""
        for ring_data in self.active_rings:
            ring_id = ring_data[0]
            try:
                self.canvas.delete(ring_id)
            except tk.TclError:
                pass
        self.active_rings.clear()
    
    def cleanup(self):
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
    def __init__(self, canvas, x, y, size):
        """Initialize player at (x, y) with given size."""
        self.canvas = canvas
        self.size = size
        self.x = x
        self.y = y
        self.vx = 0  # Velocity x
        self.vy = 0  # Velocity y
        self.rect = self.canvas.create_oval(x-size//2, y-size//2, x+size//2, y+size//2, fill='blue')

    def move(self, accel_x, accel_y):
        """Apply acceleration to player velocity and update position."""
        # Apply acceleration
        self.vx += accel_x * PLAYER_ACCELERATION
        self.vy += accel_y * PLAYER_ACCELERATION
        
        # Clamp velocity to max speed
        speed = math.hypot(self.vx, self.vy)
        if speed > PLAYER_MAX_SPEED:
            self.vx = (self.vx / speed) * PLAYER_MAX_SPEED
            self.vy = (self.vy / speed) * PLAYER_MAX_SPEED
        
        # Apply friction
        self.vx *= PLAYER_FRICTION
        self.vy *= PLAYER_FRICTION
        
        # Update position
        self.x = max(self.size//2, min(WIDTH-self.size//2, self.x+self.vx))
        self.y = max(self.size//2, min(HEIGHT-self.size//2, self.y+self.vy))
        self.canvas.coords(self.rect, self.x-self.size//2, self.y-self.size//2, self.x+self.size//2, self.y+self.size//2)

    def get_center(self):
        """Return the center coordinates of the player circle."""
        return self.x, self.y

class Enemy:
    """
    Represents an enemy in the game.
    Handles position, movement towards the player, and rendering.
    """
    def __init__(self, canvas, x, y, size):
        """Initialize enemy at (x, y) with given size."""
        self.canvas = canvas
        self.size = size
        self.x = x
        self.y = y
        self.being_pulled = False  # Whether currently pulled by black hole
        self.pull_velocity_x = 0  # Pull force direction X
        self.pull_velocity_y = 0  # Pull force direction Y
        self.pull_timer = 0  # Frames remaining to be pulled
        self.rect = self.canvas.create_rectangle(x, y, x+size, y+size, fill='red')

    def move_towards(self, target_x, target_y, speed=5):
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
        
        self.canvas.coords(self.rect, self.x, self.y, self.x+self.size, self.y+self.size)

    def get_position(self):
        """Return the top-left coordinates of the enemy rectangle."""
        return self.x, self.y

class TriangleEnemy:
    """
    Represents a triangle enemy that takes three hits to defeat.
    Tougher than the basic square enemy.
    """
    def __init__(self, canvas, x, y, size):
        """Initialize triangle enemy at (x, y) with given size."""
        self.canvas = canvas
        self.size = size
        self.x = x
        self.y = y
        self.health = 5  # Takes 5 hits to kill
        self.being_pulled = False  # Whether currently pulled by black hole
        self.pull_velocity_x = 0  # Pull force direction X
        self.pull_velocity_y = 0  # Pull force direction Y
        self.pull_timer = 0  # Frames remaining to be pulled
        # Draw triangle using create_polygon
        # Triangle points: top center, bottom-left, bottom-right
        self.points = [
            x + size//2, y,  # top center
            x, y + size,     # bottom-left
            x + size, y + size  # bottom-right
        ]
        self.rect = self.canvas.create_polygon(*self.points, fill='orange')

    def move_towards(self, target_x, target_y, speed=5):
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

    def get_position(self):
        """Return the center-ish coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self):
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        return self.health > 0

class PentagonEnemy:
    """
    Represents a pentagon tank enemy that's tougher than triangles.
    Takes many hits but gives good XP.
    """
    def __init__(self, canvas, x, y, size):
        """Initialize pentagon enemy at (x, y) with given size."""
        self.canvas = canvas
        self.size = size
        self.x = x
        self.y = y
        self.health = 10  # Takes 10 hits to kill (tank)
        self.being_pulled = False  # Whether currently pulled by black hole
        self.pull_velocity_x = 0  # Pull force direction X
        self.pull_velocity_y = 0  # Pull force direction Y
        self.pull_timer = 0  # Frames remaining to be pulled
        # Draw pentagon using create_polygon
        self.points = self._calculate_pentagon_points(x, y, size)
        self.rect = self.canvas.create_polygon(*self.points, fill='purple')
    
    def _calculate_pentagon_points(self, x, y, size):
        """Calculate the 5 points of a regular pentagon."""
        import math
        points = []
        for i in range(5):
            angle = (2 * math.pi * i / 5) - (math.pi / 2)  # Start from top
            px = x + size//2 + int((size//2) * math.cos(angle))
            py = y + size//2 + int((size//2) * math.sin(angle))
            points.extend([px, py])
        return points
    
    def move_towards(self, target_x, target_y, speed=5):
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
    
    def get_position(self):
        """Return the center coordinates of the enemy for collision."""
        return self.x, self.y
    
    def take_damage(self):
        """Reduce health by 1. Returns True if enemy is still alive."""
        self.health -= 1
        return self.health > 0

class Particle:
    """
    Represents a particle in a death poof effect.
    """
    def __init__(self, canvas, x, y, vx, vy, life):
        """Initialize particle at (x, y) with velocity (vx, vy) and lifespan."""
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.rect = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='orange')

    def update(self):
        """Update particle position and lifespan."""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        # Fade out effect by changing color
        fade = int(255 * (self.life / self.max_life))
        self.canvas.itemconfig(self.rect, fill=f'#{fade:02x}{min(fade//2, 100):02x}00')
        self.canvas.coords(self.rect, self.x-2, self.y-2, self.x+2, self.y+2)
        return self.life > 0

    def cleanup(self):
        """Remove particle from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted

class Shard:
    """
    Represents a shrapnel shard that scatters from a projectile impact.
    """
    def __init__(self, canvas, x, y, vx, vy, game, lifetime=1000, explosive=False):
        """Initialize shard at (x, y) with velocity (vx, vy) and lifetime in milliseconds."""
        self.canvas = canvas
        self.game = game
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime  # milliseconds
        self.time_alive = 0
        self.explosive = explosive  # Whether this shard explodes on impact
        self.rect = self.canvas.create_oval(x-2, y-2, x+2, y+2, fill='white' if not explosive else 'red')
    
    def update(self):
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
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            
            if dist < COLLISION_DISTANCE:
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
                play_beep_async(400, 30, self.game)                # If explosive shrapnel, create explosion effect with more shards
                if self.explosive:
                    self.game.create_explosive_shrapnel(ex_center, ey_center)
                
                # Despawn shard after hitting one enemy (whether it dies or not)
                return False
        
        # Check if lifetime expired
        return self.time_alive < self.lifetime
    
    def cleanup(self):
        """Remove shard from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted

class Projectile:
    """
    Represents a projectile that ricochets between enemies with homing effect.
    """
    def __init__(self, canvas, x, y, vx, vy, game):
        """Initialize projectile at (x, y) with velocity (vx, vy)."""
        self.canvas = canvas
        self.game = game
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.rect = self.canvas.create_oval(x-4, y-4, x+4, y+4, fill='yellow')
        self.hit_enemies = set()  # Track enemies already hit
        self.bounces = 0
        # Get weapon stats from game's computed stats
        stats = game.computed_weapon_stats
        self.max_bounces = stats.get('bounces', 0)
        self.allow_splits = stats.get('splits', False)
        self.shrapnel_level = stats.get('shrapnel', 0)
        self.homing_strength = stats.get('homing', 0.15)
        self.speed = stats.get('projectile_speed', 16)  # Use weapon stat speed, not calculated speed
        self.chain_lightning_level = stats.get('chain_lightning', 0)  # Chain lightning upgrade level
        self.fork_lightning_level = stats.get('fork_lightning', 0)  # Fork lightning upgrade level
        self.current_target = self._find_closest_target()  # Initial target for homing
        self.time_alive = 0  # Track lifetime in milliseconds
        self.returning = False  # Whether projectile is returning to player
        self.is_mini_fork = False  # Whether this is a mini-fork that can only chain once

    def update(self):
        """Update projectile position and check for collisions."""
        # Track lifetime
        self.time_alive += 50  # Update is called every 50ms
        
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
            tx_center = tx + ENEMY_SIZE // 2
            ty_center = ty + ENEMY_SIZE // 2
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
        self.canvas.coords(self.rect, self.x-4, self.y-4, self.x+4, self.y+4)
        
        # Check for enemy collision
        closest_enemy = None
        closest_dist = float('inf')
        
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            
            if dist < COLLISION_DISTANCE and dist < closest_dist:
                closest_dist = dist
                closest_enemy = enemy
        
        if closest_enemy:
            # Hit enemy!
            ex, ey = closest_enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            
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
                # Create shrapnel if upgrade is active (only on final kill)
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
                play_beep_async(400, 30, self.game)
            else:
                # Enemy took damage but survived - just mark as hit for this bounce
                pass
            
            # Mark as hit
            self.hit_enemies.add(id(closest_enemy))
            
            # Chain lightning: ONE BIG ZAP that instantly strikes all nearby enemies and returns
            if self.chain_lightning_level > 0 and not self.is_mini_fork:
                # Find all nearby unhit enemies within range
                chain_range = 100 + (50 * self.chain_lightning_level)  # 100 at level 1, 150 at level 2, 200 at level 3, etc
                nearby_enemies = self._find_nearby_enemies_for_chain(chain_range)
                
                if nearby_enemies:
                    # Build an aesthetically pleasing lightning path using greedy forward-biased selection
                    lightning_path = [(self.x, self.y)]  # Start from current projectile position
                    lightning_targets = []
                    visited = set()
                    visited.add(id(closest_enemy))  # Already hit the first enemy
                    
                    current_pos = (self.x, self.y)
                    
                    # Greedily select next targets based on forward bias and distance
                    while len(visited) < len(nearby_enemies) + 1:  # +1 because we already hit first enemy
                        remaining_enemies = [e for e in nearby_enemies if id(e) not in visited]
                        if not remaining_enemies:
                            break
                        
                        # Score each remaining enemy based on:
                        # 1. Direction preference (prefer targets ahead in current direction)
                        # 2. Distance (prefer closer targets)
                        best_enemy = None
                        best_score = float('-inf')
                        
                        for enemy in remaining_enemies:
                            ex, ey = enemy.get_position()
                            ex_center = ex + ENEMY_SIZE // 2
                            ey_center = ey + ENEMY_SIZE // 2
                            
                            # Vector from current position to this enemy
                            dx = ex_center - current_pos[0]
                            dy = ey_center - current_pos[1]
                            dist = math.hypot(dx, dy)
                            
                            if dist == 0:
                                continue
                            
                            # Get current direction (from projectile velocity or previous chain direction)
                            if len(lightning_targets) == 0 and (abs(self.vx) > 0 or abs(self.vy) > 0):
                                # Use projectile direction
                                current_dir_x = self.vx
                                current_dir_y = self.vy
                            elif len(lightning_targets) > 0:
                                # Use direction of last chain segment
                                prev_pos = lightning_path[-1]
                                current_dir_x = prev_pos[0] - lightning_path[-2][0]
                                current_dir_y = prev_pos[1] - lightning_path[-2][1]
                            else:
                                # No direction info, use zero
                                current_dir_x, current_dir_y = 0, 0
                            
                            # Normalize direction
                            dir_len = math.hypot(current_dir_x, current_dir_y)
                            if dir_len > 0:
                                current_dir_x /= dir_len
                                current_dir_y /= dir_len
                            
                            # Dot product: how much target is ahead of current direction (-1 to 1)
                            # +1 = directly ahead, 0 = perpendicular, -1 = directly behind
                            dot_product = (dx / dist) * current_dir_x + (dy / dist) * current_dir_y
                            
                            # Score: prefer forward targets (boost by dot product), closer is better
                            # Forward bias factor: 0.5 multiplier on distance to emphasize direction
                            forward_bonus = max(0, dot_product)  # Only reward forward (0 to 1)
                            distance_score = -dist  # Closer is better
                            score = forward_bonus * 100 + distance_score * 0.5
                            
                            if score > best_score:
                                best_score = score
                                best_enemy = enemy
                        
                        if best_enemy is None:
                            break
                        
                        # Add to path
                        ex, ey = best_enemy.get_position()
                        ex_center = ex + ENEMY_SIZE // 2
                        ey_center = ey + ENEMY_SIZE // 2
                        lightning_path.append((ex_center, ey_center))
                        lightning_targets.append(best_enemy)
                        visited.add(id(best_enemy))
                        current_pos = (ex_center, ey_center)
                    
                    # Draw the entire lightning path instantly (thicker for more dramatic ZAP)
                    for i in range(len(lightning_path) - 1):
                        x1, y1 = lightning_path[i]
                        x2, y2 = lightning_path[i + 1]
                        line_id = self.game.canvas.create_line(
                            x1, y1, x2, y2,
                            fill='cyan', width=3
                        )
                        
                        # Delete the line after a short delay
                        def delete_line(lid=line_id):
                            try:
                                self.game.canvas.delete(lid)
                            except tk.TclError:
                                pass
                        self.game.root.after(150, delete_line)
                    
                    # Instantly strike all enemies in the path
                    for target_enemy in lightning_targets:
                        self._strike_lightning_target(target_enemy)
                    
                    # Create mini-forks to some targets if fork lightning is active
                    if self.fork_lightning_level > 0 and len(nearby_enemies) >= 2:
                        # Create mini-forks to 1-2 enemies (not the first one)
                        fork_targets = nearby_enemies[1:3]
                        for fork_target in fork_targets:
                            self._create_mini_fork(fork_target)
                    
                    # After the big ZAP, immediately return to player (no more bouncing)
                    self.returning = True
                    return True
            
            # Mini-fork chains end after one hit
            if self.is_mini_fork:
                self.returning = True
                return True
            
            # Regular bouncing (only if we have bounces left)
            self.bounces += 1
            
            # If bounces exhausted, projectile returns
            if self.bounces > self.max_bounces:
                self.returning = True
                return True
            
            # Find next target for ricochet
            next_target = self._find_next_target()
            if next_target:
                tx, ty = next_target.get_position()
                tx_center = tx + ENEMY_SIZE // 2
                ty_center = ty + ENEMY_SIZE // 2
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
        
        # Out of bounds
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            return False
        
        return True
    
    def _find_closest_target(self):
        """Find the closest unhit enemy for initial homing."""
        closest = None
        closest_dist = float('inf')
        for enemy in self.game.enemies:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            if dist < closest_dist:
                closest_dist = dist
                closest = enemy
        return closest
    
    def _find_next_target(self):
        """Find the closest unhit enemy for ricochet."""
        closest = None
        closest_dist = float('inf')
        for enemy in self.game.enemies:
            if id(enemy) in self.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE // 2
            ey_center = ey + ENEMY_SIZE // 2
            dist = math.hypot(ex_center - self.x, ey_center - self.y)
            if dist < closest_dist:
                closest_dist = dist
                closest = enemy
        return closest
    
    def _find_nearby_enemies_for_chain(self, chain_range=150):
        """Find nearby unhit enemies for chain lightning (within range)."""
        nearby = []
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
    
    def _strike_lightning_target(self, target_enemy):
        """Strike a target enemy with chain lightning, dealing damage and effects."""
        if target_enemy not in self.game.enemies:
            return  # Enemy already dead
        
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE // 2
        ty_center = ty + ENEMY_SIZE // 2
        
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
            play_beep_async(400, 30, self.game)
    
    def _create_mini_fork(self, target_enemy):
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
        mini_fork_proj.fork_lightning_level = 0  # Mini-forks can't fork
        self.game.projectiles.append(mini_fork_proj)
    
    def _create_split_projectiles(self):
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
    
    def cleanup(self):
        """Remove projectile from canvas."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Canvas item may have already been deleted

class Game:
    """
    Main game class. Handles game state, input, rendering, and logic.
    """
    def __init__(self, root):
        """Initialize the game window, player, enemies, and event bindings."""
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
        self.canvas.pack()
        self.score = 0
        self.score_text = self.canvas.create_text(WIDTH//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.player = Player(self.canvas, WIDTH//2, HEIGHT//2, PLAYER_SIZE)
        self.enemies = []
        self.particles = []
        self.shards = []  # Track shrapnel shards
        self.projectiles = []
        self.game_time_ms = 0  # Track time played in milliseconds
        self.last_dash_dx = 1  # Default dash direction (right)
        self.last_dash_dy = 0
        self.active_upgrades = []  # List of active upgrade keys
        self.computed_weapon_stats = self.compute_weapon_stats()  # Cache computed stats
        self.dash_cooldown_counter = 0
        self.last_move_dx = 1  # Track last movement direction
        self.last_move_dy = 0
        self.xp = 0  # Current XP
        self.level = 0  # Current level
        self.xp_for_next_level = 10  # XP needed for next level
        self.level_text = self.canvas.create_text(WIDTH//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(WIDTH//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")

        # Ability system
        self.abilities = []  # List of active abilities being cast
        self.ability_cooldown_counter = 0  # Cooldown counter for abilities
        self.current_ability = 'black_hole'  # Current active ability
        
        self.upgrade_menu_active = False  # Whether upgrade menu is displayed
        self.upgrade_menu_clickable = False  # Whether upgrade buttons can be clicked
        self.upgrade_choices = []  # Three random upgrade choices
        self.upgrade_buttons = {}  # Track upgrade choice buttons
        self.upgrade_menu_elements = []  # Track all upgrade menu elements
        self.spawn_enemies()
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.root.bind('<space>', self.on_ability_activate)
        self.pressed_keys = set()
        self.paused = False
        self.pause_menu_id = None  # Track pause menu rectangle
        self.pause_buttons = {}  # Track pause menu buttons
        self.pause_menu_elements = []  # Track all pause menu elements
        self.dev_menu_active = False  # Whether dev testing menu is open
        self.dev_menu_elements = []  # Track dev menu elements
        self.dev_buttons = {}  # Track dev menu buttons
        self.ammo_orbs = []  # Track ammo orb canvas items
        self.ammo_rotation = 0  # Angle for orbiting ammo orbs
        self.sound_enabled = True  # Sound toggle setting
        self.keyboard_layout = 'dvorak'  # 'dvorak' or 'qwerty'
        self.root.after(50, self.update)
        # Schedule first respawn
        self.root.after(RESPAWN_INTERVAL, self.on_respawn_timer)

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
                elif key in ['projectile_speed', 'homing', 'bounces', 'shrapnel', 'explosive_shrapnel', 'chain_lightning', 'fork_lightning']:
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
            self.xp_for_next_level = int(self.xp_for_next_level * 1.35)  # Scale XP requirement
            self.canvas.itemconfig(self.level_text, text=f"Level: {self.level}")
            self.canvas.itemconfig(self.xp_text, text=f"XP: {self.xp}/{self.xp_for_next_level}")
            # Show upgrade menu on level up
            if not self.upgrade_menu_active and not self.paused:
                self.show_upgrade_menu()

    def add_upgrade(self, upgrade_key):
        """Add an upgrade to active upgrades and recompute stats."""
        if upgrade_key not in WEAPON_UPGRADES and upgrade_key not in LINKED_UPGRADES:
            return False
        self.active_upgrades.append(upgrade_key)
        self.computed_weapon_stats = self.compute_weapon_stats()
        return True
    
    def remove_upgrade(self, upgrade_key):
        """Remove an upgrade from active upgrades and recompute stats."""
        if upgrade_key in self.active_upgrades:
            self.active_upgrades.remove(upgrade_key)
            self.computed_weapon_stats = self.compute_weapon_stats()
            return True
        return False

    def spawn_enemies(self):
        """Create a new set of enemies at random positions, scaled by level."""
        self.enemies.clear()
        initial_count = TESTING_MODE_ENEMY_COUNT if TESTING_MODE else INITIAL_ENEMY_COUNT
        # Scale initial enemy count with level
        level_scaled_count = int(initial_count * (1 + 0.15 * self.level))  # 15% increase per level
        
        for _ in range(level_scaled_count):
            x = random.randint(0, WIDTH-ENEMY_SIZE)
            y = random.randint(0, HEIGHT-ENEMY_SIZE)
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
        level_scaling = 1 + (0.1 * self.level)  # 10% increase per level
        max_enemies = int(base_max * level_scaling)
        
        # Also increase respawn count with level
        scaled_count = int(count * (1 + 0.05 * self.level))  # 5% increase per level
        
        if len(self.enemies) >= max_enemies:
            return
        
        for _ in range(scaled_count):
            if len(self.enemies) >= max_enemies:
                break
            x = random.randint(0, WIDTH-ENEMY_SIZE)
            y = random.randint(0, HEIGHT-ENEMY_SIZE)
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
        """Handle canvas clicks - routes to upgrade menu or pause menu or dev menu or attack."""
        # If dev menu is open, handle dev button clicks
        if self.dev_menu_active:
            for action, btn_id in self.dev_buttons.items():
                coords = self.canvas.coords(btn_id)
                if coords and len(coords) >= 4:
                    x1, y1, x2, y2 = coords
                    if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                        self._handle_dev_menu_action(action)
                        return
            return  # Click outside buttons in dev menu does nothing
        
        # If upgrade menu is open, handle upgrade button clicks
        if self.upgrade_menu_active:
            if not self.upgrade_menu_clickable:
                return  # Upgrade menu not ready for clicks yet
            for upgrade_key, btn_id in self.upgrade_buttons.items():
                coords = self.canvas.coords(btn_id)
                if coords and len(coords) >= 4 and (coords[0] <= event.x <= coords[2] and coords[1] <= event.y <= coords[3]):
                    self.on_upgrade_selection(upgrade_key)
                    return
            return  # Click outside buttons in upgrade menu does nothing
        
        # If pause menu is open, handle pause button clicks
        if self.paused:
            for action, btn_id in self.pause_buttons.items():
                coords = self.canvas.coords(btn_id)
                if coords and len(coords) >= 4:
                    x1, y1, x2, y2 = coords
                    if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                        if action == 'resume':
                            self.hide_pause_menu()
                        elif action == 'restart':
                            self.restart_game()
                        elif action == 'quit':
                            self.quit_game()
                        elif action == 'sound':
                            self.toggle_sound()
                        elif action == 'keyboard':
                            self.toggle_keyboard_layout()
                        elif action == 'dev':
                            self.show_dev_menu()
                        return
            return  # Click outside buttons in pause menu does nothing
        
        # Otherwise, attack
        self.attack()

    def show_upgrade_menu(self):
        """Display upgrade selection menu with three random choices."""
        try:
            self.upgrade_menu_active = True
            self.paused = True
            
            # Pick three random upgrades
            available_upgrades = list(WEAPON_UPGRADES.keys())
            
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
                    upgrade_count = self.active_upgrades.count(upgrade_name)
                    if upgrade_count >= required_level:
                        can_unlock = True
                elif isinstance(requires, list):
                    # All prerequisites must be owned
                    if all(req in self.active_upgrades for req in requires):
                        can_unlock = True
                else:
                    # Single prerequisite string
                    if requires in self.active_upgrades:
                        can_unlock = True
                
                if can_unlock:
                    available_upgrades.append(linked_key)
            
            self.upgrade_choices = random.sample(available_upgrades, min(3, len(available_upgrades)))
            
            # Create overlay
            menu_size = min(WIDTH, HEIGHT) // 2
            overlay_x = (WIDTH - menu_size) // 2
            overlay_y = (HEIGHT - menu_size) // 2
            overlay_width = menu_size
            overlay_height = menu_size
            
            # Background rectangle
            overlay_id = self.canvas.create_rectangle(
                overlay_x, overlay_y,
                overlay_x + overlay_width, overlay_y + overlay_height,
                fill='#1a1a2e', outline='lime', width=3
            )
            self.upgrade_menu_elements.append(overlay_id)
            
            # Title
            title = self.canvas.create_text(
                WIDTH // 2, overlay_y + 30,
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
                    WIDTH // 2, btn_y + button_height // 2,
                    text=upgrade_name,
                    fill='lime',
                    font=('Arial', 16)
                )
                self.upgrade_menu_elements.append(text_id)
            
            # Enable clicks after 300ms delay to prevent accidental selections from rapid clicking
            self.upgrade_menu_clickable = False
            self.root.after(300, lambda: setattr(self, 'upgrade_menu_clickable', True))
        except Exception as e:
            print(f"Error in show_upgrade_menu: {e}")
            self.upgrade_menu_active = False
            self.paused = False
    
    def on_upgrade_selection(self, upgrade_key):
        """Handle upgrade selection."""
        if upgrade_key in self.upgrade_choices:
            self.add_upgrade(upgrade_key)
            self.close_upgrade_menu()
    
    def close_upgrade_menu(self):
        """Close the upgrade menu."""
        for element_id in self.upgrade_menu_elements:
            self.canvas.delete(element_id)
        
        self.upgrade_menu_elements = []
        self.upgrade_buttons = {}
        self.upgrade_choices = []
        self.upgrade_menu_active = False
        self.upgrade_menu_clickable = False
        self.paused = False

    def show_pause_menu(self):
        """Display pause menu overlay on the game canvas."""
        self.paused = True
        
        # Create square overlay
        menu_size = min(WIDTH, HEIGHT) // 2
        overlay_x = (WIDTH - menu_size) // 2
        overlay_y = (HEIGHT - menu_size) // 2
        overlay_width = menu_size
        overlay_height = menu_size
        
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
            WIDTH // 2, overlay_y + 30,
            text='PAUSED',
            fill='yellow',
            font=('Arial', 32, 'bold')
        )
        self.pause_menu_elements.append(title)
        
        # Upgrades panel
        upgrades_label = self.canvas.create_text(
            WIDTH // 2, overlay_y + 70,
            text='Active Upgrades:',
            fill='cyan',
            font=('Arial', 14, 'bold')
        )
        self.pause_menu_elements.append(upgrades_label)
        
        # Display active upgrades
        if self.active_upgrades:
            # Count upgrades by type
            upgrade_counts = {}
            for upgrade_key in self.active_upgrades:
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
            WIDTH // 2, overlay_y + 90,
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
            WIDTH // 2, resume_btn_y + 20,
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
            WIDTH // 2, restart_btn_y + 20,
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
            WIDTH // 2, quit_btn_y + 20,
            text='Quit',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['quit'])
        self.pause_menu_elements.append(quit_text)
        
        # Sound toggle button
        sound_btn_y = quit_btn_y + 60
        sound_status = 'ON' if self.sound_enabled else 'OFF'
        self.pause_buttons['sound'] = self.canvas.create_rectangle(
            overlay_x + 40, sound_btn_y,
            overlay_x + overlay_width - 40, sound_btn_y + 40,
            fill='#4a4a7a', outline='white', width=2
        )
        sound_text = self.canvas.create_text(
            WIDTH // 2, sound_btn_y + 20,
            text=f'Sound: {sound_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['sound'])
        self.pause_menu_elements.append(sound_text)
        
        # Keyboard layout toggle button
        keyboard_btn_y = sound_btn_y + 60
        keyboard_layout_display = self.keyboard_layout.upper()
        self.pause_buttons['keyboard'] = self.canvas.create_rectangle(
            overlay_x + 40, keyboard_btn_y,
            overlay_x + overlay_width - 40, keyboard_btn_y + 40,
            fill='#7a4a7a', outline='white', width=2
        )
        keyboard_text = self.canvas.create_text(
            WIDTH // 2, keyboard_btn_y + 20,
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

    def quit_game(self):
        """Close the game window and exit."""
        self.root.destroy()
    
    def toggle_sound(self):
        """Toggle sound on/off and refresh pause menu to show new state."""
        self.sound_enabled = not self.sound_enabled
        # Close and reopen pause menu to update the sound button text
        self.hide_pause_menu()
        self.show_pause_menu()
    
    def toggle_keyboard_layout(self):
        """Toggle between Dvorak and QWERTY keyboard layouts and refresh pause menu."""
        self.keyboard_layout = 'qwerty' if self.keyboard_layout == 'dvorak' else 'dvorak'
        # Close and reopen pause menu to update the keyboard button text
        self.hide_pause_menu()
        self.show_pause_menu()
    
    def show_dev_menu(self):
        """Display the developer testing menu."""
        self.dev_menu_active = True
        
        # Create overlay
        menu_size = min(WIDTH, HEIGHT) * 0.6
        overlay_x = (WIDTH - menu_size) // 2
        overlay_y = (HEIGHT - menu_size) // 2
        overlay_width = menu_size
        overlay_height = menu_size
        
        # Background rectangle
        overlay_id = self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a3e', outline='magenta', width=3
        )
        self.dev_menu_elements.append(overlay_id)
        
        # Title
        title = self.canvas.create_text(
            WIDTH // 2, overlay_y + 20,
            text='DEV TESTING MENU',
            fill='magenta',
            font=('Arial', 20, 'bold')
        )
        self.dev_menu_elements.append(title)
        
        # Button definitions: (label, action, color)
        buttons = [
            ('Add Extra Bounce', 'upgrade_extra_bounce', '#4a4a8a'),
            ('Add Shrapnel', 'upgrade_shrapnel', '#4a4a8a'),
            ('Add Speed Boost', 'upgrade_speed_boost', '#4a4a8a'),
            ('Add Chain Lightning', 'upgrade_chain_lightning', '#4a4a8a'),
            ('Add Fork Lightning', 'upgrade_fork_lightning', '#4a4a8a'),
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
                WIDTH // 2, btn_y1 + button_height // 2,
                text=label,
                fill='white',
                font=('Arial', 12)
            )
            self.dev_menu_elements.append(text_id)
    
    def _handle_dev_menu_action(self, action):
        """Handle dev menu button actions."""
        try:
            if action == 'upgrade_extra_bounce':
                self.add_upgrade('extra_bounce')
            elif action == 'upgrade_shrapnel':
                self.add_upgrade('shrapnel')
            elif action == 'upgrade_speed_boost':
                self.add_upgrade('speed_boost')
            elif action == 'upgrade_chain_lightning':
                self.add_upgrade('chain_lightning')
            elif action == 'upgrade_fork_lightning':
                self.add_upgrade('fork_lightning')
            elif action == 'level_up':
                self.level += 1
                self.xp_for_next_level = int(self.xp_for_next_level * 1.35)
                self.canvas.itemconfig(self.level_text, text=f"Level: {self.level}")
            elif action == 'add_xp':
                self.add_xp(100)
            elif action == 'spawn_enemies_cmd':
                self.respawn_enemies(30)
            elif action == 'back_to_pause':
                self.close_dev_menu()
                return
            
            # Close dev menu and return to pause menu after action
            self.close_dev_menu()
        except Exception as e:
            print(f"Error in dev action '{action}': {e}")

    def close_dev_menu(self):
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

    def hide_pause_menu(self):
        """Hide the pause menu and resume the game."""
        # Explicitly clear everything
        self.paused = False
        self.pause_menu_id = None
        self.pause_buttons = {}
        
        # Delete all pause menu elements
        if hasattr(self, 'pause_menu_elements'):
            for element in self.pause_menu_elements:
                try:
                    self.canvas.delete(element)
                except:
                    pass  # Element may already be deleted
            self.pause_menu_elements = []
    
    def on_pause_menu_click(self, event):
        """Handle pause menu button clicks."""
        # Check which button was clicked
        for action, btn_id in self.pause_buttons.items():
            coords = self.canvas.coords(btn_id)
            if coords and len(coords) >= 4:
                x1, y1, x2, y2 = coords
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    if action == 'resume':
                        self.hide_pause_menu()
                    elif action == 'restart':
                        self.restart_game()
                    elif action == 'quit':
                        self.quit_game()
                    return

    def restart_game(self):
        """Restart the game, resetting player, enemies, and score."""
        if self.paused:
            self.hide_pause_menu()
        self.canvas.delete('all')
        self.score = 0
        self.game_time_ms = 0
        self.dash_cooldown_counter = 0
        self.ability_cooldown_counter = 0
        self.particles.clear()
        self.shards.clear()
        self.projectiles.clear()
        self.abilities.clear()
        self.active_upgrades = []
        self.computed_weapon_stats = self.compute_weapon_stats()
        self.xp = 0
        self.level = 0
        self.xp_for_next_level = 10
        self.player = Player(self.canvas, WIDTH//2, HEIGHT//2, PLAYER_SIZE)
        self.enemies = []
        self.spawn_enemies()
        self.score_text = self.canvas.create_text(WIDTH//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.level_text = self.canvas.create_text(WIDTH//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(WIDTH//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")

    def on_key_press(self, event):
        """Handle key press events for movement and actions."""
        # Get the movement keys based on current keyboard layout
        if self.keyboard_layout == 'dvorak':
            # Dvorak controls: ',' = up, 'a' = left, 'o' = down, 'e' = right
            movement_keys = [',', 'a', 'o', 'e']
        else:  # QWERTY
            # QWERTY controls: 'w' = up, 'a' = left, 's' = down, 'd' = right
            movement_keys = ['w', 'a', 's', 'd']
        
        if event.char in movement_keys:
            self.pressed_keys.add(event.char)
        elif event.keysym == 'Escape':
            if not hasattr(self, 'paused') or not self.paused:
                self.show_pause_menu()

    def on_key_release(self, event):
        """Handle key release events for movement."""
        # Get the movement keys based on current keyboard layout
        if self.keyboard_layout == 'dvorak':
            movement_keys = [',', 'a', 'o', 'e']
        else:  # QWERTY
            movement_keys = ['w', 'a', 's', 'd']
        
        if event.char in movement_keys:
            self.pressed_keys.discard(event.char)
    
    def on_ability_activate(self, event):
        """Handle active ability activation."""
        if self.ability_cooldown_counter > 0:
            return  # Ability is on cooldown
        
        # Cast the current ability
        if self.current_ability == 'black_hole':
            self.cast_black_hole()
        
        self.ability_cooldown_counter = ABILITY_COOLDOWN
    
    def cast_black_hole(self):
        """Cast black hole ability toward mouse cursor."""
        px, py = self.player.get_center()
        
        # Get direction to mouse
        mouse_x = self.canvas.winfo_pointerx() - self.canvas.winfo_rootx()
        mouse_y = self.canvas.winfo_pointery() - self.canvas.winfo_rooty()
        dx = mouse_x - px
        dy = mouse_y - py
        dist = math.hypot(dx, dy)
        
        if dist == 0:
            # No direction, use forward direction
            dx, dy = self.last_move_dx, self.last_move_dy
            dist = 1
        
        # Normalize and apply speed
        vx = (dx / dist) * BLACK_HOLE_SPEED
        vy = (dy / dist) * BLACK_HOLE_SPEED
        
        # Create black hole
        black_hole = BlackHoleAbility(self.canvas, px, py, vx, vy, self)
        self.abilities.append(black_hole)
        
        # Play ability sound
        play_beep_async(150, 100, self)

    def update(self):
        """Main game loop: update movement, enemies, and schedule next frame."""
        if self.paused:
            self.root.after(50, self.update)
            return
        
        # Track time played
        self.game_time_ms += 50
        
        self.handle_player_movement()
        self.move_enemies()
        self.update_particles()
        self.update_shards()
        self.update_projectiles()
        self.update_abilities()
        self.update_ammo_orbs()
        self.update_dash_cooldown()
        self.update_ability_cooldown()
        self.root.after(50, self.update)

    def handle_player_movement(self):
        """Check pressed keys and apply acceleration accordingly."""
        accel_x, accel_y = 0, 0
        
        # Get movement keys based on current keyboard layout
        if self.keyboard_layout == 'dvorak':
            up_key, left_key, down_key, right_key = ',', 'a', 'o', 'e'
        else:  # QWERTY
            up_key, left_key, down_key, right_key = 'w', 'a', 's', 'd'
        
        if up_key in self.pressed_keys:
            accel_y -= 1
        if down_key in self.pressed_keys:
            accel_y += 1
        if left_key in self.pressed_keys:
            accel_x -= 1
        if right_key in self.pressed_keys:
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
        self.player.move(dx, dy)

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

    def update_abilities(self):
        """Update all active abilities and remove dead ones."""
        alive_abilities = []
        for ability in self.abilities:
            if ability.update():
                alive_abilities.append(ability)
            else:
                ability.cleanup()
        self.abilities = alive_abilities

    def update_dash_cooldown(self):
        """Update dash cooldown timer."""
        if self.dash_cooldown_counter > 0:
            self.dash_cooldown_counter -= 50
    
    def update_ability_cooldown(self):
        """Update ability cooldown timer."""
        if self.ability_cooldown_counter > 0:
            self.ability_cooldown_counter -= 50

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
            enemy.move_towards(px, py)

    def attack(self):
        """Launch a projectile if none are active."""
        # Make sure we're not in a menu
        if self.paused or self.upgrade_menu_active:
            return
        
        # Check if there's a main projectile active (mini-forks don't block firing)
        has_main_projectile = any(p for p in self.projectiles if not p.is_mini_fork)
        if has_main_projectile:  # Can't fire if a main projectile is already active
            return
        
        # Play attack sound asynchronously
        play_beep_async(500, 50, self)
        
        center_x, center_y = self.player.get_center()
        angle = self.get_attack_direction()
        
        # Get weapon stats
        projectile_speed = self.computed_weapon_stats['projectile_speed']
        
        vx = math.cos(angle) * projectile_speed
        vy = math.sin(angle) * projectile_speed
        projectile = Projectile(self.canvas, center_x, center_y, vx, vy, self)
        # Set projectile homing strength
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
