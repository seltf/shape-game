import tkinter as tk
import random
import math
import winsound
import threading

def play_beep_async(frequency, duration):
    """Play a beep asynchronously in a background thread."""
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
    }
}

PLAYER_ACCELERATION = 3.5  # How quickly player accelerates
PLAYER_MAX_SPEED = 22  # Maximum player speed
PLAYER_FRICTION = 0.80  # Friction multiplier (0-1, lower = more friction)

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
        self.rect = self.canvas.create_rectangle(x, y, x+size, y+size, fill='red')

    def move_towards(self, target_x, target_y, speed=5):
        """Move enemy towards (target_x, target_y) by 'speed' pixels."""
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
        self.canvas.delete(self.rect)

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
                    # Award XP for kill (7 for pentagon, 5 for triangle, 1 for regular)
                    if is_pentagon:
                        xp_reward = 7
                    elif is_triangle:
                        xp_reward = 5
                    else:
                        xp_reward = 1
                    self.game.add_xp(xp_reward)
                    play_beep_async(400, 30)
                
                # If explosive shrapnel, create explosion effect with more shards
                if self.explosive:
                    self.game.create_explosive_shrapnel(ex_center, ey_center)
                
                # Despawn shard after hitting one enemy (whether it dies or not)
                return False
        
        # Check if lifetime expired
        return self.time_alive < self.lifetime
    
    def cleanup(self):
        """Remove shard from canvas."""
        self.canvas.delete(self.rect)

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
        self.current_target = self._find_closest_target()  # Initial target for homing
        self.time_alive = 0  # Track lifetime in milliseconds
        self.returning = False  # Whether projectile is returning to player

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
                
                # Award XP for kill (7 for pentagon, 5 for triangle, 1 for regular)
                if is_pentagon:
                    xp_reward = 7
                elif is_triangle:
                    xp_reward = 5
                else:
                    xp_reward = 1
                self.game.add_xp(xp_reward)
                
                # Play kill sound asynchronously
                play_beep_async(400, 30)
            else:
                # Enemy took damage but survived - just mark as hit for this bounce
                pass
            
            # Mark as hit
            self.hit_enemies.add(id(closest_enemy))
            
            # Chain lightning: automatically bounce to nearby enemies (doesn't consume bounces)
            if self.chain_lightning_level > 0:
                # Find all nearby unhit enemies within range
                chain_range = 100 + (50 * self.chain_lightning_level)  # 100 at level 1, 150 at level 2, 200 at level 3, etc
                nearby_enemies = self._find_nearby_enemies_for_chain(chain_range)
                
                if nearby_enemies:
                    # Pick the closest nearby enemy
                    next_target = nearby_enemies[0]
                    
                    # Draw lightning line from current position to target
                    tx, ty = next_target.get_position()
                    tx_center = tx + ENEMY_SIZE // 2
                    ty_center = ty + ENEMY_SIZE // 2
                    line_id = self.game.canvas.create_line(
                        self.x, self.y, tx_center, ty_center,
                        fill='cyan', width=2
                    )
                    
                    # Delete the line after a short delay (100ms)
                    self.game.root.after(100, lambda: self.game.canvas.delete(line_id) if line_id else None)
                    
                    # Move projectile directly to the target and treat it like a new frame
                    self.x = tx_center
                    self.y = ty_center
                    self.current_target = next_target
                    self.canvas.coords(self.rect, self.x-4, self.y-4, self.x+4, self.y+4)
                    return True  # Continue updating next frame
            
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
        self.canvas.delete(self.rect)

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

        self.upgrade_menu_active = False  # Whether upgrade menu is displayed
        self.upgrade_choices = []  # Three random upgrade choices
        self.upgrade_buttons = {}  # Track upgrade choice buttons
        self.upgrade_menu_elements = []  # Track all upgrade menu elements
        self.spawn_enemies()
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.root.bind('<space>', self.on_dash)
        self.pressed_keys = set()
        self.paused = False
        self.pause_menu_id = None  # Track pause menu rectangle
        self.pause_buttons = {}  # Track pause menu buttons
        self.pause_menu_elements = []  # Track all pause menu elements
        self.ammo_orbs = []  # Track ammo orb canvas items
        self.ammo_rotation = 0  # Angle for orbiting ammo orbs
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
                elif key in ['projectile_speed', 'homing', 'bounces', 'shrapnel', 'explosive_shrapnel', 'chain_lightning']:
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
        """Create a new set of enemies at random positions."""
        self.enemies.clear()
        initial_count = TESTING_MODE_ENEMY_COUNT if TESTING_MODE else INITIAL_ENEMY_COUNT
        for _ in range(initial_count):
            x = random.randint(0, WIDTH-ENEMY_SIZE)
            y = random.randint(0, HEIGHT-ENEMY_SIZE)
            enemy = Enemy(self.canvas, x, y, ENEMY_SIZE)
            self.enemies.append(enemy)
    
    def get_current_respawn_interval(self):
        """Calculate respawn interval based on time played."""
        minutes_played = self.game_time_ms / 60000
        interval = RESPAWN_INTERVAL - (minutes_played * 1000 * RESPAWN_BATCH_SCALE)
        return max(interval, RESPAWN_INTERVAL_MIN)
    
    def respawn_enemies(self, count):
        """Spawn 'count' new enemies at random positions."""
        # Increase max enemies based on time played
        minutes_played = self.game_time_ms / 60000
        scaling_factor = 1 + (minutes_played * 0.1)  # 10% increase per minute
        max_enemies = int(MAX_ENEMY_COUNT * scaling_factor)
        
        if len(self.enemies) >= max_enemies:
            return
        
        for _ in range(count):
            if len(self.enemies) >= max_enemies:
                break
            x = random.randint(0, WIDTH-ENEMY_SIZE)
            y = random.randint(0, HEIGHT-ENEMY_SIZE)
            
            # Spawn pentagon tank enemies starting at level 10 (5% chance)
            if self.level >= 10 and random.random() < 0.05:
                enemy = PentagonEnemy(self.canvas, x, y, ENEMY_SIZE)
            # Spawn triangle enemies starting at level 5 (30% chance)
            elif self.level >= 5 and random.random() < 0.3:
                enemy = TriangleEnemy(self.canvas, x, y, ENEMY_SIZE)
            else:
                enemy = Enemy(self.canvas, x, y, ENEMY_SIZE)
            self.enemies.append(enemy)

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
        """Handle canvas clicks - routes to upgrade menu or pause menu or attack."""
        # If upgrade menu is open, handle upgrade button clicks
        if self.upgrade_menu_active:
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
                # Handle both single and multiple prerequisites
                if isinstance(requires, list):
                    # All prerequisites must be owned
                    if all(req in self.active_upgrades for req in requires):
                        available_upgrades.append(linked_key)
                else:
                    # Single prerequisite
                    if requires in self.active_upgrades:
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
                if upgrade_key in WEAPON_UPGRADES:
                    upgrade_name = WEAPON_UPGRADES[upgrade_key]['name']
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

    def quit_game(self):
        """Close the game window and exit."""
        self.root.destroy()

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
        self.particles.clear()
        self.shards.clear()
        self.projectiles.clear()
        self.active_upgrades = []
        self.computed_weapon_stats = self.compute_weapon_stats()
        self.xp = 0
        self.level = 0
        self.xp_for_next_level = 30
        self.player = Player(self.canvas, WIDTH//2, HEIGHT//2, PLAYER_SIZE)
        self.enemies = []
        self.spawn_enemies()
        self.score_text = self.canvas.create_text(WIDTH//2, 30, anchor='n', fill='yellow', font=('Arial', 24), text=str(self.score))
        self.level_text = self.canvas.create_text(WIDTH//2, 70, anchor='n', fill='cyan', font=('Arial', 20), text=f"Level: {self.level}")
        self.xp_text = self.canvas.create_text(WIDTH//2, 100, anchor='n', fill='green', font=('Arial', 16), text=f"XP: {self.xp}/{self.xp_for_next_level}")

    def on_key_press(self, event):
        """Handle key press events for movement and actions."""
        # Dvorak controls: ',' = up, 'a' = left, 'o' = down, 'e' = right
        if event.char in [',', 'a', 'o', 'e']:
            self.pressed_keys.add(event.char)
        elif event.keysym == 'Escape':
            if not hasattr(self, 'paused') or not self.paused:
                self.show_pause_menu()

    def on_key_release(self, event):
        """Handle key release events for movement."""
        if event.char in [',', 'a', 'o', 'e']:
            self.pressed_keys.discard(event.char)
    
    def on_dash(self, event):
        """Handle dash skill activation."""
        if self.dash_cooldown_counter > 0:
            return  # Dash is on cooldown
        
        self.dash_cooldown_counter = DASH_COOLDOWN
        
        # Dash in the direction of last movement (or default if no movement)
        dash_x = self.last_move_dx * DASH_DISTANCE
        dash_y = self.last_move_dy * DASH_DISTANCE
        self.player.vx += dash_x
        self.player.vy += dash_y
        
        # Clamp velocity to max speed
        speed = math.hypot(self.player.vx, self.player.vy)
        if speed > PLAYER_MAX_SPEED:
            self.player.vx = (self.player.vx / speed) * PLAYER_MAX_SPEED
            self.player.vy = (self.player.vy / speed) * PLAYER_MAX_SPEED

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
        self.update_ammo_orbs()
        self.update_dash_cooldown()
        self.root.after(50, self.update)

    def handle_player_movement(self):
        """Check pressed keys and apply acceleration accordingly."""
        accel_x, accel_y = 0, 0
        if ',' in self.pressed_keys:
            accel_y -= 1
        if 'o' in self.pressed_keys:
            accel_y += 1
        if 'a' in self.pressed_keys:
            accel_x -= 1
        if 'e' in self.pressed_keys:
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
        play_beep_async(800, 25)
        
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
        play_beep_async(120, 200)  # Low frequency (120Hz), long duration (200ms)
        
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

    def update_dash_cooldown(self):
        """Update dash cooldown timer."""
        if self.dash_cooldown_counter > 0:
            self.dash_cooldown_counter -= 50

    def update_ammo_orbs(self):
        """Update ammo orbs to orbit around the player."""
        # Fixed ammo value - always 1 orb
        max_ammo = 1
        
        # Calculate available ammo (max - active projectiles)
        available_ammo = max_ammo - len(self.projectiles)
        
        # Remove old orbs
        for orb_id in self.ammo_orbs:
            self.canvas.delete(orb_id)
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
        
        if self.projectiles:  # Can't fire if a projectile is already active
            return
        
        # Play attack sound asynchronously
        play_beep_async(500, 50)
        
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
