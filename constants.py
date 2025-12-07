"""
Game constants - centralized configuration for Top Down Game
"""
from typing import Dict, Any
from enum import Enum, auto

# ============================================================================
# GAME STATE MACHINE
# ============================================================================
class GameState(Enum):
    """Enumeration of all possible game states."""
    MAIN_MENU = auto()      # Showing main menu
    PLAYING = auto()        # Active gameplay
    PAUSED = auto()         # Game paused
    UPGRADE_MENU = auto()   # Showing upgrade selection
    DEV_MENU = auto()       # Developer menu open
    GAME_OVER = auto()      # Game over screen

# ============================================================================
# VERSION
# ============================================================================
VERSION: str = "0.0.1"  # Game version number

# ============================================================================
# DISPLAY & WINDOW
# ============================================================================
TESTING_MODE: bool = False  # Set to True to spawn many enemies for testing weapons

WIDTH: int = 600
HEIGHT: int = 400

# ============================================================================
# PLAYER CONFIGURATION
# ============================================================================
PLAYER_SIZE: int = 20
PLAYER_ACCELERATION: float = 2.0  # How quickly player accelerates (scaled for 50 FPS logic)
PLAYER_MAX_SPEED: int = 3  # Maximum player speed (scaled for 50 FPS logic)
PLAYER_FRICTION: float = 0.70  # Friction multiplier (0-1, lower = more friction)

# ============================================================================
# ENEMY CONFIGURATION
# ============================================================================
ENEMY_SIZE: int = 20
ENEMY_SIZE_HALF: int = 10  # Pre-calculated ENEMY_SIZE // 2 for performance

INITIAL_ENEMY_COUNT: int = 10  # Enemies to spawn at game start
TESTING_MODE_ENEMY_COUNT: int = 100  # Enemies in testing mode
MAX_ENEMY_COUNT: int = 150  # Maximum enemies allowed
RESPAWN_BATCH_SIZE: int = 20  # Enemies to spawn per batch
RESPAWN_INTERVAL: int = 10000  # Milliseconds between batches (10 seconds)
RESPAWN_INTERVAL_MIN: int = 3000  # Minimum interval at high difficulty (3 seconds)
RESPAWN_BATCH_SCALE: float = 0.8  # Milliseconds to reduce interval per minute played (scaled for 50 FPS logic: was 2, now 0.8)

# ============================================================================
# GAME LEVEL PROGRESSION & WAVES
# ============================================================================
LEVEL_REST_DURATION: int = 2000  # Milliseconds of rest between levels (2 seconds)
WAVE_SPAWN_INTERVAL: int = 5000  # Default milliseconds between wave spawns (5 seconds)

# Wave-based level progression. Each level has waves of enemies.
# Wave format: (enemy_type, count, spawn_delay_ms)
# enemy_type: 'square' (4-sided, basic), 'triangle' (3-sided, weak), 'pentagon' (5-sided, strong), 'hexagon' (6-sided, splits into 2 triangles)
# Difficulty scales with: triangle(1hp) < circle(1hp) < square(4hp) < pentagon(5hp) < hexagon(6hp, splits)
GAME_LEVEL_WAVES: Dict[int, list] = {
    # Level 1-2: Intro - all triangles to learn mechanics
    1: [('triangle', 20, 0)],
    2: [('triangle', 30, 0)],
    
    # Level 3-4: Introduce squares
    3: [('triangle', 30, 0), ('square', 15, 0)],
    4: [('triangle', 25, 0), ('square', 25, 0)],
    
    # Level 5-6: More squares, mixed waves
    5: [('square', 35, 0), ('triangle', 20, 0)],
    6: [('square', 30, 0), ('triangle', 25, 0), ('square', 25, 0)],
    
    # Level 7-9: Squares dominate, introduce pentagons
    7: [('square', 45, 0), ('triangle', 15, 0)],
    8: [('square', 35, 0), ('square', 25, 0), ('pentagon', 8, 0)],
    9: [('square', 40, 0), ('pentagon', 12, 0), ('triangle', 20, 0)],
    
    # Level 10-12: Pentagon presence increases, introduce hexagons
    10: [('square', 35, 0), ('pentagon', 15, 0), ('square', 30, 0)],
    11: [('pentagon', 20, 0), ('square', 35, 0), ('hexagon', 8, 0), ('triangle', 20, 0)],
    12: [('square', 40, 0), ('pentagon', 25, 0), ('hexagon', 12, 0)],
    
    # Level 13-15: Hexagons ramp up, pentagons provide support
    13: [('hexagon', 15, 0), ('pentagon', 30, 0), ('square', 40, 0)],
    14: [('hexagon', 20, 0), ('pentagon', 30, 0), ('square', 45, 0), ('hexagon', 8, 0)],
    15: [('hexagon', 25, 0), ('pentagon', 40, 0), ('square', 50, 0)],
    
    # Level 16-20: Endgame - CHAOS! Heavy on hexagons creating split chains
    16: [('hexagon', 30, 0), ('pentagon', 40, 0), ('hexagon', 15, 0), ('square', 50, 0)],
    17: [('hexagon', 40, 0), ('pentagon', 50, 0), ('hexagon', 20, 0), ('square', 60, 0)],
    18: [('hexagon', 50, 0), ('pentagon', 60, 0), ('hexagon', 30, 0), ('square', 70, 0)],
    19: [('hexagon', 60, 0), ('pentagon', 70, 0), ('hexagon', 40, 0), ('square', 80, 0)],
    20: [('hexagon', 70, 0), ('pentagon', 80, 0), ('hexagon', 50, 0), ('square', 100, 0)],
    # Level 21: Boss fight - no other enemies
    21: [],  # Boss spawned separately in _start_boss_fight()
}

# ============================================================================
# PROJECTILE & WEAPON CONFIGURATION
# ============================================================================
MAX_BOUNCES: int = 100  # Maximum number of enemy bounces per projectile
HOMING_STRENGTH: float = 0.15  # How strongly projectile homes in on target
COLLISION_DISTANCE: int = 30  # Distance for projectile-enemy collision
COLLISION_DISTANCE_SQ: int = COLLISION_DISTANCE ** 2  # Pre-calculated squared distance for sqrt elimination
PROJECTILE_SPLIT_ANGLE: int = 30  # Degrees to split projectiles on each bounce
RICOCHET_RANGE: int = 150  # Maximum range for projectile to find ricochet targets (scaled for 50 FPS logic)
PROJECTILE_LIFETIME: int = 10000  # Milliseconds before projectile explodes
PROJECTILE_RETURN_TIME_MS: int = 800  # Time before projectile returns to player (increased for smoother animation)
EXPLOSION_RADIUS: int = 100  # Pixels for explosion damage radius

# ============================================================================
# WEAPON STATS & UPGRADES
# ============================================================================
WEAPON_STATS: Dict[str, Any] = {
    'projectile_speed': 6,  # Scaled for 50 FPS logic (was 16)
    'return_speed': 8,  # Speed at which projectiles return to player (scaled for 50 FPS logic)
    'homing': 0,
    'bounces': 0,
    'splits': True,
    'shrapnel': 0,
    'shield': 0,
    'attack_range': 500  # Base projectile return distance in pixels
}

# Weapon upgrades - modifiers that can be applied to base weapon
WEAPON_UPGRADES: Dict[str, Dict[str, Any]] = {
    'extra_bounce': {'bounces': 1, 'name': 'Ricochet'},
    'shrapnel': {'shrapnel': 1, 'name': 'Shrapnel'},
    'black_hole': {'black_hole': 1, 'name': 'Black Hole'},
    'homing': {'homing': 0.35, 'name': 'Homing', 'one_time': True},
    'shield': {'shield': 1, 'name': 'Shield'},
    'rapid_fire': {'projectile_speed': 1.6, 'return_speed': 2, 'name': 'Rapid Fire'},  # Faster projectiles and returns (scaled for 50 FPS)
    'summon_minion': {'name': 'Summon Minion', 'description': 'Spawn a friendly minion that attacks enemies'},
}

# Linked upgrades - only appear if prerequisite(s) are owned
LINKED_UPGRADES: Dict[str, Dict[str, Any]] = {
    'explosive_shrapnel': {
        'name': 'Explosive Shrapnel',
        'requires': 'shrapnel',  # Single prerequisite
        'modifiers': {'explosive_shrapnel': 1}
    },
    'chain_lightning': {
        'name': 'Chain Lightning',
        'requires': ['extra_bounce'],  # Changed from speed_boost to extra_bounce
        'modifiers': {'chain_lightning': 1}
    }
}

# ============================================================================
# BLACK HOLE UPGRADE CONFIGURATION
# ============================================================================
BLACK_HOLE_TRIGGER_CHANCE: float = 0.15  # 15% chance per hit at level 1
BLACK_HOLE_BASE_RADIUS: int = 40  # Base radius of black hole effect
BLACK_HOLE_PULL_STRENGTH: int = 2.4  # Speed at which enemies get pulled in (scaled for 20ms tick rate)
BLACK_HOLE_PULL_DURATION: int = 3000  # Milliseconds that black hole pulls enemies (3 seconds)
BLACK_HOLE_PULL_STRENGTH_MIN: int = 2  # Minimum pull strength at radius edge to prevent getting stuck

# ============================================================================
# PARTICLE & EFFECT CONFIGURATION
# ============================================================================
PARTICLE_COUNT: int = 5  # Particles in death poof effect (reduced from 8 for performance)
PARTICLE_LIFE: int = 15  # Frames until particle dies

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================
SPATIAL_GRID_CELL_SIZE: int = 100  # Size of each grid cell for spatial partitioning
MAX_POOLED_PARTICLES: int = 200  # Maximum particles to keep in object pool
CANVAS_UPDATE_BATCH_SIZE: int = 50  # Number of entities to update before canvas refresh
PERFORMANCE_MONITORING: bool = False  # Enable FPS and entity count display
COLLISION_CHECK_RADIUS: int = 80  # Radius to check for collisions around player
ENEMY_AVOIDANCE_RADIUS: int = 60  # Radius to check for nearby enemies during movement

# ============================================================================
# WEAPON & ATTACK CONFIGURATION
# ============================================================================
WEAPON_COOLDOWN_MS: int = 200  # Milliseconds between main weapon attacks (5 per second)
WEAPON_RETURN_COOLDOWN_MS: int = 1000  # Cooldown after projectile returns (scales with rapid fire)

# ============================================================================
# SOUND CONFIGURATION
# ============================================================================
SOUND_COOLDOWN_MS: int = 50  # Minimum milliseconds between same sound effects
