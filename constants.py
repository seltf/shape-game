"""
Game constants - centralized configuration for Top Down Game
"""
from typing import Dict, Any

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
LEVEL_REST_DURATION: int = 3000  # Milliseconds of rest between levels (3 seconds)

# Wave-based level progression. Each level has waves of enemies.
# Wave format: (enemy_type, count, spawn_delay_ms)
# enemy_type: 'basic' (0), 'triangle' (1), 'pentagon' (2)
GAME_LEVEL_WAVES: Dict[int, list] = {
    # Level 1: Simple intro - one batch of basic enemies
    1: [('basic', 5, 0)],
    
    # Level 2-3: Slightly more enemies
    2: [('basic', 8, 0)],
    3: [('basic', 10, 0), ('basic', 5, 2000)],
    
    # Level 4-6: Introduction to harder enemies
    4: [('basic', 12, 0), ('basic', 8, 2000)],
    5: [('basic', 10, 0), ('triangle', 3, 2000)],
    6: [('basic', 8, 0), ('triangle', 5, 2000), ('basic', 5, 4000)],
    
    # Level 7-10: More mixed waves
    7: [('basic', 10, 0), ('triangle', 4, 2000), ('basic', 8, 3500)],
    8: [('triangle', 6, 0), ('basic', 12, 2000), ('triangle', 3, 4000)],
    9: [('basic', 10, 0), ('triangle', 5, 1500), ('pentagon', 2, 3500)],
    10: [('triangle', 8, 0), ('pentagon', 3, 2000), ('triangle', 5, 4000)],
    
    # Level 11-15: Harder difficulty with more enemy types
    11: [('basic', 12, 0), ('triangle', 6, 1500), ('pentagon', 2, 3500), ('basic', 8, 5000)],
    12: [('triangle', 8, 0), ('pentagon', 4, 2000), ('triangle', 6, 4000), ('basic', 10, 5500)],
    13: [('pentagon', 3, 0), ('triangle', 8, 1500), ('pentagon', 3, 3000), ('triangle', 6, 4500)],
    14: [('basic', 15, 0), ('pentagon', 5, 2000), ('triangle', 8, 3500), ('pentagon', 2, 5000)],
    15: [('triangle', 10, 0), ('pentagon', 4, 2000), ('triangle', 8, 4000), ('pentagon', 3, 5500)],
    
    # Level 16-20: High difficulty with many waves
    16: [('pentagon', 4, 0), ('triangle', 10, 1500), ('pentagon', 5, 3000), ('triangle', 8, 4500), ('basic', 12, 6000)],
    17: [('triangle', 12, 0), ('pentagon', 6, 2000), ('triangle', 10, 3500), ('pentagon', 4, 5000), ('triangle', 8, 6500)],
    18: [('pentagon', 5, 0), ('triangle', 12, 1500), ('pentagon', 6, 3000), ('triangle', 10, 4500), ('pentagon', 4, 6000)],
    19: [('triangle', 14, 0), ('pentagon', 7, 2000), ('triangle', 12, 3500), ('pentagon', 5, 5000), ('triangle', 10, 6500)],
    20: [('pentagon', 8, 0), ('triangle', 15, 1500), ('pentagon', 8, 3000), ('triangle', 12, 4500), ('pentagon', 6, 6000), ('triangle', 12, 7500)],
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
BLACK_HOLE_PULL_STRENGTH: int = 6  # Speed at which enemies get pulled in (scaled for 50 FPS logic)
BLACK_HOLE_PULL_DURATION: int = 3000  # Milliseconds that black hole pulls enemies (3 seconds)
BLACK_HOLE_PULL_STRENGTH_MIN: int = 5  # Minimum pull strength at radius edge to prevent getting stuck

# ============================================================================
# PARTICLE & EFFECT CONFIGURATION
# ============================================================================
PARTICLE_COUNT: int = 5  # Particles in death poof effect (reduced from 8 for performance)
PARTICLE_LIFE: int = 15  # Frames until particle dies

# ============================================================================
# SOUND CONFIGURATION
# ============================================================================
SOUND_COOLDOWN_MS: int = 50  # Minimum milliseconds between same sound effects
