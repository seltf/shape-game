"""
Game constants - centralized configuration for Top Down Game
"""
from typing import Dict, Any

# ============================================================================
# VERSION
# ============================================================================
VERSION: str = "1.0.0"  # Game version number

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
RESPAWN_BATCH_SCALE: int = 2  # Milliseconds to reduce interval per minute played

# ============================================================================
# PROJECTILE & WEAPON CONFIGURATION
# ============================================================================
MAX_BOUNCES: int = 100  # Maximum number of enemy bounces per projectile
HOMING_STRENGTH: float = 0.15  # How strongly projectile homes in on target
COLLISION_DISTANCE: int = 30  # Distance for projectile-enemy collision
COLLISION_DISTANCE_SQ: int = COLLISION_DISTANCE ** 2  # Pre-calculated squared distance for sqrt elimination
PROJECTILE_SPLIT_ANGLE: int = 30  # Degrees to split projectiles on each bounce
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
