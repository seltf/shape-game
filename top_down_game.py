import tkinter as tk
import random
import math
import winsound
import threading
import os
import sys
from pathlib import Path

# Determine the base directory for resources (handles both dev and bundled exe)
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as a script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Audio is available on Windows with winsound
AUDIO_AVAILABLE = True

# Sound effects dictionary - maps sound names to file paths
SOUND_EFFECTS = {
    'black_hole_detonate': os.path.join(BASE_DIR, 'sounds/black_hole_detonate.wav'),
    'projectile_hit': os.path.join(BASE_DIR, 'sounds/projectile_hit.wav'),
    'enemy_death': os.path.join(BASE_DIR, 'sounds/enemy_death.wav'),
    'powerup': os.path.join(BASE_DIR, 'sounds/powerup.wav'),
}

# Background music file
BACKGROUND_MUSIC = os.path.join(BASE_DIR, 'sounds/bit track space.wav')
_music_thread = None
_music_stop_event = None

# Sound effect throttling to prevent overlapping/crunchy audio
_last_sound_time = {}  # Track when each sound was last played
_sound_cooldown_ms = 50  # Minimum milliseconds between same sound effects

def play_sound_async(sound_name, frequency=None, duration=None, game_instance=None):
    """
    Play a sound asynchronously. Can use custom sound file or fallback to beep.
    
    Args:
        sound_name: Name of the sound effect from SOUND_EFFECTS
        frequency: Frequency for beep fallback (Hz)
        duration: Duration for beep fallback (ms)
        game_instance: Game instance to check if sound is enabled
    """
    import time
    
    # Check if sound is enabled (default to True if no game instance)
    if game_instance is not None and not game_instance.sound_enabled:
        return
    
    # Throttle sound effects to prevent overlapping/crunchy audio
    current_time = time.time() * 1000  # Convert to milliseconds
    if sound_name in _last_sound_time:
        time_since_last = current_time - _last_sound_time[sound_name]
        if time_since_last < _sound_cooldown_ms:
            print(f"[SOUND] SKIPPED sound effect: {sound_name} (too soon, {time_since_last:.0f}ms since last)")
            return  # Skip this sound, too soon after last one
    
    _last_sound_time[sound_name] = current_time
    print(f"[SOUND] Playing sound effect: {sound_name} (freq={frequency}, dur={duration}ms)")
    
    def play():
        # Try to load custom sound file using winsound
        if sound_name in SOUND_EFFECTS and AUDIO_AVAILABLE:
            sound_path = SOUND_EFFECTS[sound_name]
            if os.path.exists(sound_path):
                try:
                    print(f"  -> Playing file: {sound_path}")
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return  # Successfully played file, don't play fallback
                except Exception as e:
                    print(f"  -> Failed to play file {sound_path}: {e}")
                    # Fall through to beep fallback
        
        # Fallback to beep if custom sound unavailable or couldn't be loaded
        if frequency is not None and duration is not None:
            try:
                print(f"  -> Playing beep fallback: {frequency}Hz for {duration}ms")
                winsound.Beep(frequency, duration)
            except Exception as e:
                print(f"  -> Failed to play beep: {e}")
    
    thread = threading.Thread(target=play, daemon=True)
    thread.start()

def play_beep_async(frequency, duration, game_instance=None):
    """Play a beep asynchronously in a background thread."""
    import time
    
    # Check if sound is enabled (default to True if no game instance)
    if game_instance is not None and not game_instance.sound_enabled:
        return
    
    # Throttle beeps by frequency to prevent overlapping
    beep_key = f"beep_{frequency}"
    current_time = time.time() * 1000
    if beep_key in _last_sound_time:
        time_since_last = current_time - _last_sound_time[beep_key]
        if time_since_last < _sound_cooldown_ms:
            print(f"[SOUND] SKIPPED beep: {frequency}Hz (too soon, {time_since_last:.0f}ms since last)")
            return  # Skip this beep, too soon after last one
    
    _last_sound_time[beep_key] = current_time
    print(f"[SOUND] Playing beep: {frequency}Hz for {duration}ms")
    
    def beep():
        try:
            winsound.Beep(frequency, duration)
        except Exception as e:
            print(f"[SOUND] Failed to play beep: {e}")
    thread = threading.Thread(target=beep, daemon=True)
    thread.start()

def start_background_music(game_instance=None):
    """Start looping background music."""
    global _music_thread, _music_stop_event
    
    # Check if sound and music are enabled
    if game_instance is not None and (not game_instance.sound_enabled or not game_instance.music_enabled):
        return
    
    # Stop any existing music
    stop_background_music()
    
    if not AUDIO_AVAILABLE or not os.path.exists(BACKGROUND_MUSIC):
        return
    
    # Create stop event for this music session
    _music_stop_event = threading.Event()
    
    def loop_music():
        try:
            while not _music_stop_event.is_set():
                # Use winsound to play with lower volume
                winsound.PlaySound(BACKGROUND_MUSIC, winsound.SND_FILENAME | winsound.SND_ASYNC)
                
                # Wait for the music to finish, checking stop event frequently
                import time
                # Estimate a reasonable wait time (adjust based on your music file length)
                wait_time = 0
                max_wait = 300  # Max 5 minutes per song to ensure full playback before loop
                while wait_time < max_wait and not _music_stop_event.is_set():
                    time.sleep(0.5)
                    wait_time += 0.5
                
                if _music_stop_event.is_set():
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    break
        except Exception as e:
            print(f"Failed to play background music: {e}")
    
    _music_thread = threading.Thread(target=loop_music, daemon=True)
    _music_thread.start()

def stop_background_music():
    """Stop the looping background music."""
    global _music_thread, _music_stop_event
    
    if _music_stop_event is not None:
        _music_stop_event.set()
    
    # Stop winsound playback
    try:
        winsound.PlaySound(None, winsound.SND_PURGE)
    except:
        pass
    
    # Wait for thread to finish
    if _music_thread is not None and _music_thread.is_alive():
        _music_thread.join(timeout=1.0)
    
    _music_thread = None
    _music_stop_event = None




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
RESPAWN_BATCH_SCALE = 2  # Milliseconds to reduce interval per minute played
MAX_BOUNCES = 100  # Maximum number of enemy bounces per projectile
DASH_DISTANCE = 60  # How far the dash moves the player
DASH_COOLDOWN = 500  # Milliseconds between dashes
PARTICLE_COUNT = 5  # Particles in death poof effect (reduced from 8 for performance)
PARTICLE_LIFE = 15  # Frames until particle dies
HOMING_STRENGTH = 0.15  # How strongly projectile homes in on target
COLLISION_DISTANCE = 30  # Distance for projectile-enemy collision
ENEMY_SIZE_HALF = 10  # Pre-calculated ENEMY_SIZE // 2 for performance
COLLISION_DISTANCE_SQ = COLLISION_DISTANCE ** 2  # Pre-calculated squared distance for sqrt elimination
PROJECTILE_SPLIT_ANGLE = 30  # Degrees to split projectiles on each bounce
PROJECTILE_LIFETIME = 10000  # Milliseconds before projectile explodes
EXPLOSION_RADIUS = 100  # Pixels for explosion damage radius

WEAPON_STATS = {'projectile_speed': 16, 'homing': 0, 'bounces': 0, 'splits': True, 'shrapnel': 0}

# Weapon upgrades - modifiers that can be applied to base weapon
WEAPON_UPGRADES = {
    'extra_bounce': {'bounces': 1, 'name': 'Ricochet'},
    'shrapnel': {'shrapnel': 1, 'name': 'Shrapnel'},
    'speed_boost': {'projectile_speed': 3, 'name': 'Speed Boost'},
    'black_hole': {'black_hole': 1, 'name': 'Black Hole'},
    'homing': {'homing': 0.35, 'name': 'Homing', 'one_time': True},
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

# Black hole upgrade constants (now a weapon upgrade, not ability)
BLACK_HOLE_TRIGGER_CHANCE = 0.15  # 15% chance per hit at level 1
BLACK_HOLE_BASE_RADIUS = 40  # Base radius of black hole effect
BLACK_HOLE_PULL_STRENGTH = 15  # Speed at which enemies get pulled in
BLACK_HOLE_PULL_DURATION = 3000  # Milliseconds that black hole pulls enemies (3 seconds)
BLACK_HOLE_PULL_STRENGTH_MIN = 5  # Minimum pull strength at radius edge to prevent getting stuck

# Ability constants (no longer used for black hole, keeping for future abilities)
ABILITY_COOLDOWN = 5000  # Milliseconds between ability uses (5 seconds)

class BlackHole:
    """
    Represents a black hole effect spawned by weapon hits.
    Pulls and kills enemies in its radius when it detonates.
    """
    def __init__(self, canvas, x, y, radius, game, level=1):
        """Initialize black hole at (x, y) with given radius."""
        self.canvas = canvas
        self.game = game
        self.x = x
        self.y = y
        self.radius = radius
        self.level = level  # Store upgrade level for damage calculation
        self.time_alive = 0  # Track lifetime in milliseconds
        self.detonation_phase = False
        # Visual representation - only outline, no fill so enemies are visible
        self.rect = self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, 
                                           fill='', outline='#6600ff', width=2)
        # Animated rings during pull phase
        self.active_rings = []  # Track canvas IDs of active animated rings
        self.ring_spawn_counter = 0  # Counter to spawn rings at intervals
    
    def update(self):
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
    
    def _start_detonation(self):
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
    
    def _pull_enemies(self):
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
    
    def _update_rings(self):
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
    
    def _spawn_new_ring(self):
        """Spawn a new animated ring at the edge of the pull radius."""
        ring_size = self.radius
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
    
    def _kill_enemies_at_center(self):
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
        self.health = 1  # Player starts with 1 HP
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
        self.health = 8  # Takes 8 hits to kill (tank)
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
        self.black_hole_level = stats.get('black_hole', 0)  # Black hole upgrade level
        self.current_target = self._find_closest_target()  # Initial target for homing
        self.time_alive = 0  # Track lifetime in milliseconds
        self.returning = False  # Whether projectile is returning to player
        self.is_mini_fork = False  # Whether this is a mini-fork that can only chain once

    def update(self):
        """Update projectile position and check for collisions."""
        # Track lifetime
        self.time_alive += 50  # Update is called every 50ms
        
        # Check if 0.5 seconds have passed - trigger return
        if not self.returning and self.time_alive >= 500:  # 500ms = 0.5 seconds
            print(f"[ACTION] Projectile returning to player after 2 seconds")
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
            
            # Chain lightning: On initial hit, trigger a chain through level number of targets
            if self.chain_lightning_level > 0 and not self.is_mini_fork:
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
                
                # After chain completes, return to player
                self.returning = True
                return True
            
            # Mini-fork chains end after one hit
            if self.is_mini_fork:
                self.returning = True
                return True
            
            # Regular bouncing (only if we have bounces left)
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
        
        # Out of bounds
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            return False
        
        return True
    
    def _find_closest_target(self):
        """Find the closest unhit enemy for initial homing."""
        closest = None
        closest_dist_sq = float('inf')
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
    
    def _find_next_target(self):
        """Find the closest unhit enemy for ricochet."""
        closest = None
        closest_dist_sq = float('inf')
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
        self.game.projectiles.append(mini_fork_proj)
    
    def _create_fork_from_target(self, target_enemy):
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
    
    def _try_spawn_black_hole(self, x, y):
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
        
        # Draw starfield background
        self._draw_starfield()
        
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
        self.black_holes = []  # List of active black holes from weapon upgrades
        
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
        self.music_enabled = True  # Music toggle setting
        self.keyboard_layout = 'dvorak'  # 'dvorak' or 'qwerty'
        self.game_over_active = False  # Whether game over screen is showing
        self.game_over_restart_btn = None  # Reference to restart button
        
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
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
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
                elif key in ['projectile_speed', 'homing', 'bounces', 'shrapnel', 'explosive_shrapnel', 'chain_lightning', 'black_hole']:
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
                x = random.randint(-ENEMY_SIZE, WIDTH)
                y = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
            elif side == 'bottom':
                # Bottom edge: x spans full width, y is below screen
                x = random.randint(-ENEMY_SIZE, WIDTH)
                y = random.randint(HEIGHT, HEIGHT + margin)
            elif side == 'left':
                # Left edge: x is left of screen, y spans full height
                x = random.randint(-margin - ENEMY_SIZE, -ENEMY_SIZE)
                y = random.randint(-ENEMY_SIZE, HEIGHT)
            else:  # right
                # Right edge: x is right of screen, y spans full height
                x = random.randint(WIDTH, WIDTH + margin)
                y = random.randint(-ENEMY_SIZE, HEIGHT)
            
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
        """Handle canvas clicks - routes to upgrade menu or pause menu or dev menu or attack."""
        print(f"[INPUT] Canvas clicked at ({event.x}, {event.y})")
        
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
                        elif action == 'music':
                            self.toggle_music()
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
            
            # Remove one-time upgrades that have already been picked
            available_upgrades = [
                u for u in available_upgrades 
                if not (WEAPON_UPGRADES[u].get('one_time', False) and u in self.active_upgrades)
            ]
            
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
        
        # Music toggle button
        music_btn_y = sound_btn_y + 60
        music_status = 'ON' if self.music_enabled else 'OFF'
        self.pause_buttons['music'] = self.canvas.create_rectangle(
            overlay_x + 40, music_btn_y,
            overlay_x + overlay_width - 40, music_btn_y + 40,
            fill='#7a4a4a', outline='white', width=2
        )
        music_text = self.canvas.create_text(
            WIDTH // 2, music_btn_y + 20,
            text=f'Music: {music_status}',
            fill='white',
            font=('Arial', 16)
        )
        self.pause_menu_elements.append(self.pause_buttons['music'])
        self.pause_menu_elements.append(music_text)
        
        # Keyboard layout toggle button
        keyboard_btn_y = music_btn_y + 60
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
        stop_background_music()
        self.root.destroy()
    
    def toggle_sound(self):
        """Toggle sound on/off and refresh pause menu to show new state."""
        self.sound_enabled = not self.sound_enabled
        # Close and reopen pause menu to update the sound button text
        self.hide_pause_menu()
        self.show_pause_menu()
    
    def toggle_music(self):
        """Toggle music on/off and refresh pause menu to show new state."""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            stop_background_music()
        else:
            start_background_music(self)
        # Close and reopen pause menu to update the music button text
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
            ('Add Ricochet', 'upgrade_extra_bounce', '#4a4a8a'),
            ('Add Shrapnel', 'upgrade_shrapnel', '#4a4a8a'),
            ('Add Speed Boost', 'upgrade_speed_boost', '#4a4a8a'),
            ('Add Chain Lightning', 'upgrade_chain_lightning', '#4a4a8a'),
            ('Add Black Hole', 'upgrade_black_hole', '#4a4a8a'),
            ('Add Homing', 'upgrade_homing', '#4a4a8a'),
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
            elif action == 'upgrade_black_hole':
                self.add_upgrade('black_hole')
            elif action == 'upgrade_homing':
                self.add_upgrade('homing')
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
            
            # Keep dev menu open for multiple selections
            # Delete only dev menu elements and redraw the menu (don't delete game elements)
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
        
        # Clear any stuck keys from being pressed while pause menu was open
        self.pressed_keys.clear()
        
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
        stop_background_music()
        if self.paused:
            self.hide_pause_menu()
        self.game_over_active = False  # Clear game over flag
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
            # If dev menu is open, close it
            if self.dev_menu_active:
                self.close_dev_menu()
            # If pause menu is open, close it (resume game)
            elif self.paused:
                self.hide_pause_menu()
            # Otherwise, open pause menu
            else:
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
        """Black hole is now a weapon upgrade, not an ability. This method is deprecated."""
        # Black hole effects are now spawned through weapon hits with the black hole upgrade
        # This ability method is kept for future alternative ability implementations
        pass

    def update(self):
        """Main game loop: update movement, enemies, and schedule next frame."""
        if self.paused:
            self.root.after(50, self.update)
            return
        
        # Track time played
        self.game_time_ms += 50
        
        self.handle_player_movement()
        self.move_enemies()
        self.check_player_collision()  # Check if enemies hit player
        self.update_particles()
        self.update_shards()
        self.update_projectiles()
        self.update_abilities()
        self.update_black_holes()
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

    def update_black_holes(self):
        """Update all active black holes from weapon upgrades and remove expired ones."""
        alive_black_holes = []
        for black_hole in self.black_holes:
            if black_hole.update():
                alive_black_holes.append(black_hole)
            else:
                black_hole.cleanup()
        self.black_holes = alive_black_holes

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
            # Different speeds for different enemy types
            if isinstance(enemy, PentagonEnemy):
                enemy.move_towards(px, py, speed=3)  # Pentagons move slower
            elif isinstance(enemy, TriangleEnemy):
                enemy.move_towards(px, py, speed=4)  # Triangles medium speed
            else:  # CircleEnemy
                enemy.move_towards(px, py, speed=5)  # Circles normal speed

    def check_player_collision(self):
        """Check if any enemy collides with player and deal damage."""
        px, py = self.player.get_center()
        for enemy in self.enemies:
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            # Check distance between player and enemy
            dx = ex_center - px
            dy = ey_center - py
            dist_sq = dx * dx + dy * dy
            collision_dist_sq = (PLAYER_SIZE // 2 + ENEMY_SIZE // 2) ** 2
            
            if dist_sq < collision_dist_sq:
                # Collision detected - deal damage to player
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
        # Create game over overlay
        overlay_width = WIDTH // 2
        overlay_height = HEIGHT // 4
        overlay_x = (WIDTH - overlay_width) // 2
        overlay_y = (HEIGHT - overlay_height) // 2
        
        # Background
        self.canvas.create_rectangle(
            overlay_x, overlay_y,
            overlay_x + overlay_width, overlay_y + overlay_height,
            fill='#1a1a1a', outline='red', width=3
        )
        
        # Game Over text
        self.canvas.create_text(
            WIDTH // 2, overlay_y + 30,
            text='GAME OVER',
            fill='red',
            font=('Arial', 48, 'bold')
        )
        
        # Score text
        self.canvas.create_text(
            WIDTH // 2, overlay_y + 90,
            text=f'Final Score: {self.score}',
            fill='yellow',
            font=('Arial', 24)
        )
        
        # Restart button
        btn_width = 200
        btn_height = 50
        btn_x = (WIDTH - btn_width) // 2
        btn_y = overlay_y + 140
        
        self.game_over_restart_btn = self.canvas.create_rectangle(
            btn_x, btn_y,
            btn_x + btn_width, btn_y + btn_height,
            fill='green', outline='white', width=2
        )
        self.canvas.create_text(
            WIDTH // 2, btn_y + 25,
            text='Restart',
            fill='white',
            font=('Arial', 20, 'bold')
        )

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
        print(f"[ACTION] Player attacking - firing projectile")
        play_beep_async(500, 50, self)
        
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
