"""
Game constants - centralized configuration for Top Down Game
"""

# ============================================================================
# DISPLAY & WINDOW
# ============================================================================
TESTING_MODE = False  # Set to True to spawn many enemies for testing weapons

WIDTH = 600
HEIGHT = 400

# ============================================================================
# PLAYER CONFIGURATION
# ============================================================================
PLAYER_SIZE = 20
PLAYER_ACCELERATION = 3.5  # How quickly player accelerates
PLAYER_MAX_SPEED = 6  # Maximum player speed (barely faster than circles at 5)
PLAYER_FRICTION = 0.70  # Friction multiplier (0-1, lower = more friction)
DASH_DISTANCE = 60  # How far the dash moves the player
DASH_COOLDOWN = 500  # Milliseconds between dashes

# ============================================================================
# ENEMY CONFIGURATION
# ============================================================================
ENEMY_SIZE = 20
ENEMY_SIZE_HALF = 10  # Pre-calculated ENEMY_SIZE // 2 for performance

INITIAL_ENEMY_COUNT = 10  # Enemies to spawn at game start
TESTING_MODE_ENEMY_COUNT = 100  # Enemies in testing mode
MAX_ENEMY_COUNT = 150  # Maximum enemies allowed
RESPAWN_BATCH_SIZE = 20  # Enemies to spawn per batch
RESPAWN_INTERVAL = 10000  # Milliseconds between batches (10 seconds)
RESPAWN_INTERVAL_MIN = 3000  # Minimum interval at high difficulty (3 seconds)
RESPAWN_BATCH_SCALE = 2  # Milliseconds to reduce interval per minute played

# ============================================================================
# PROJECTILE & WEAPON CONFIGURATION
# ============================================================================
MAX_BOUNCES = 100  # Maximum number of enemy bounces per projectile
HOMING_STRENGTH = 0.15  # How strongly projectile homes in on target
COLLISION_DISTANCE = 30  # Distance for projectile-enemy collision
COLLISION_DISTANCE_SQ = COLLISION_DISTANCE ** 2  # Pre-calculated squared distance for sqrt elimination
PROJECTILE_SPLIT_ANGLE = 30  # Degrees to split projectiles on each bounce
PROJECTILE_LIFETIME = 10000  # Milliseconds before projectile explodes
PROJECTILE_RETURN_TIME_MS = 500  # Time before projectile returns to player
EXPLOSION_RADIUS = 100  # Pixels for explosion damage radius

# ============================================================================
# WEAPON STATS & UPGRADES
# ============================================================================
WEAPON_STATS = {
    'projectile_speed': 16,
    'homing': 0,
    'bounces': 0,
    'splits': True,
    'shrapnel': 0,
    'shield': 0
}

# Weapon upgrades - modifiers that can be applied to base weapon
WEAPON_UPGRADES = {
    'extra_bounce': {'bounces': 1, 'name': 'Ricochet'},
    'shrapnel': {'shrapnel': 1, 'name': 'Shrapnel'},
    'speed_boost': {'projectile_speed': 3, 'name': 'Speed Boost'},
    'black_hole': {'black_hole': 1, 'name': 'Black Hole'},
    'homing': {'homing': 0.35, 'name': 'Homing', 'one_time': True},
    'shield': {'shield': 1, 'name': 'Shield'},
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

# ============================================================================
# BLACK HOLE UPGRADE CONFIGURATION
# ============================================================================
BLACK_HOLE_TRIGGER_CHANCE = 0.15  # 15% chance per hit at level 1
BLACK_HOLE_BASE_RADIUS = 40  # Base radius of black hole effect
BLACK_HOLE_PULL_STRENGTH = 15  # Speed at which enemies get pulled in
BLACK_HOLE_PULL_DURATION = 3000  # Milliseconds that black hole pulls enemies (3 seconds)
BLACK_HOLE_PULL_STRENGTH_MIN = 5  # Minimum pull strength at radius edge to prevent getting stuck

# ============================================================================
# PARTICLE & EFFECT CONFIGURATION
# ============================================================================
PARTICLE_COUNT = 5  # Particles in death poof effect (reduced from 8 for performance)
PARTICLE_LIFE = 15  # Frames until particle dies

# ============================================================================
# SOUND CONFIGURATION
# ============================================================================
SOUND_COOLDOWN_MS = 50  # Minimum milliseconds between same sound effects
