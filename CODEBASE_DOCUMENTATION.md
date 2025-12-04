# Shape-Game Codebase Documentation

## Project Overview

**Shape-Game** is a top-down shooter game built in Python using Tkinter for GUI rendering. Players control a player character, defend against enemy shapes, and progress through an upgrade system by collecting XP and selecting weapon enhancements.

**Technology Stack:**
- Python 3.14
- Tkinter (GUI/Canvas rendering)
- pytest (28 unit tests covering collision detection, entity interactions, and edge cases)
- Git version control

---

## Architecture & File Structure

### Core Modules

#### 1. **top_down_game.py** (909 lines)
**Purpose:** Main game loop, state management, and event handling

**Key Responsibilities:**
- Game initialization and window management
- Main update loop (50ms tick rate)
- Player input handling (keyboard movement, mouse clicks)
- Game state tracking (score, XP, level, active upgrades)
- Menu integration (pause, upgrades, dev menu, game over)

**Critical Instance Variables:**
```python
self.window_width, self.window_height  # Actual canvas dimensions (not global WIDTH/HEIGHT)
self.canvas                             # Tkinter Canvas for rendering
self.player                             # Player entity
self.enemies[]                          # List of active enemies
self.projectiles[]                      # List of active projectiles
self.particles[]                        # Visual effects (poof, death animations)
self.shards[]                           # Shrapnel/debris particles
self.black_holes[]                      # Active black hole upgrades
self.computed_weapon_stats{}            # Current weapon stats (damage, speed, etc.)
self.active_upgrades[]                  # List of collected upgrades
```

**Key Methods:**
- `__init__()`: Initialize game, capture actual canvas dimensions
- `update()`: Main game loop - calls all update methods in sequence
- `attack()`: Fire projectile from player toward mouse
- `get_attack_direction()`: Calculate angle from player to mouse cursor
- `move_player(accel_x, accel_y)`: Apply acceleration and friction physics
- `move_enemies()`: Update enemy positions and spawning
- `check_player_collision()`: Detect enemy-player collisions
- `spawn_enemies()`: Spawn new enemies based on wave system
- `add_xp(amount)`: Add XP and handle leveling
- `handle_upgrade_selection(upgrade_key)`: Apply selected upgrade
- `update_projectiles/particles/shards/black_holes()`: Entity lifecycle management

**Important Pattern:**
> All spatial operations use `self.window_width` and `self.window_height` instead of global constants. This ensures correct behavior on any screen size.

---

#### 2. **entities.py** (1,207 lines)
**Purpose:** All game entity classes and their behaviors

**Entity Classes:**

**Player**
- Handles movement with acceleration/friction physics
- Position clamping within screen bounds
- Center calculation for weapon firing
- Health/shield management

**Projectile**
- Fires from player toward enemies
- 0.5-second lifetime before returning to player
- Homing behavior (seeks closest enemy)
- Chain lightning capability (bounces between enemies)
- Splits into mini-forks on certain hits
- Tracks hit enemies to avoid double-damage
- **Critical Fix:** Uses `self.canvas.winfo_width/height()` for bounds checking (not global WIDTH/HEIGHT)

**Enemy Types**
- `Enemy`: Basic circular enemy (1 health, 1 XP)
- `TriangleEnemy`: Purple triangle (3 health, 3 XP, slower)
- `PentagonEnemy`: Green pentagon (5 health, 7 XP, slowest)

**Particle**
- Visual effects (death poof, explosions)
- Fades out over lifetime
- No collision logic

**Shard**
- Shrapnel from projectile impacts
- Can be explosive (triggers secondary explosions)
- Lifetime-based despawn (1 second default)

**BlackHole**
- Spawned from black hole upgrade
- Pulls nearby enemies toward center
- Deals damage on contact
- Self-destructs after 5 seconds

**Key Methods in All Entities:**
- `update() -> bool`: Returns True if entity should persist, False to despawn
- `cleanup()`: Remove visual representation from canvas
- `get_position()`: Return (x, y) tuple

---

#### 3. **collision.py** (366 lines)
**Purpose:** All collision detection and response logic

**Key Functions:**
- `check_collision_circle(x1, y1, r1, x2, y2, r2) -> bool`: Precise circle-circle collision
- `check_collision_distance_sq(x1, y1, x2, y2) -> float`: Squared distance (avoids sqrt)
- `check_collision_line_circle()`: For future melee weapons
- `check_collision_rect()`: For future UI clickboxes

**Constants Used:**
```python
COLLISION_DISTANCE_SQ = 1024  # Projectile-enemy collision threshold squared
ENEMY_SIZE_HALF = 20           # Half-width of enemy collision circle
```

**Design Pattern:**
> Uses squared distances throughout to avoid expensive square root calculations. Only takes sqrt when necessary for physics calculations.

---

#### 4. **menus.py** (606 lines)
**Purpose:** All menu UI management (pause, upgrades, dev, game over)

**MenuManager Class - Key Methods:**

**`show_upgrade_menu()`**
- Displays 3 random upgrade choices when player levels up
- **Dynamic Height Calculation:** Menu height = title_height + (buttons × button_height) + spacing + padding
- Prevents accidental selection with 300ms delay
- Supports one-time upgrades and linked upgrades (prerequisites)

**`show_pause_menu()`**
- Pause/Resume buttons
- Dev menu access
- Quit option

**`show_dev_menu()`**
- Debug tools (spawn enemies, give XP, add upgrades, God mode)
- Useful for testing and development

**`show_game_over_menu()`**
- Final score display
- Restart button

**Important Fix:** Menu height now calculated dynamically based on number of buttons:
```python
menu_height = title_height + (num_buttons * button_height) + ((num_buttons - 1) * button_spacing) + padding
```

---

#### 5. **constants.py** (92 lines)
**Purpose:** Game configuration constants and upgrade definitions

**Game Parameters:**
```python
WIDTH = 600, HEIGHT = 400           # Default canvas size (overridden by actual screen)
PLAYER_SIZE = 16                    # Player collision radius
ENEMY_SIZE = 40                     # Enemy visual size
ENEMY_SIZE_HALF = 20                # Enemy collision radius
PARTICLE_COUNT = 12                 # Particles in death effect
PARTICLE_LIFE = 500                 # Particle lifetime (milliseconds)
COLLISION_DISTANCE_SQ = 1024        # Projectile collision distance squared
```

**Upgrade System:**
- `WEAPON_UPGRADES{}`: Main upgrades (damage, projectile speed, homing, etc.)
- `LINKED_UPGRADES{}`: Upgrades with prerequisites (chain lightning forks, etc.)

**Upgrade Structure:**
```python
{
    'name': str,                    # Display name
    'description': str,             # Upgrade details
    'one_time': bool,              # Can only be picked once
    'requires': str/list/dict,     # Prerequisites for linked upgrades
}
```

---

#### 6. **audio.py** (202 lines)
**Purpose:** Sound effect generation and async playback

**Key Function:**
- `play_beep_async(frequency, duration, game)`: Play beep in background thread
  - Frequency: Hz (250 for hit, 500 for attack, 120 for explosion)
  - Duration: milliseconds
  - Uses threading to prevent blocking game loop

---

#### 7. **utils.py** (19 lines)
**Purpose:** Utility functions

**Current Functions:**
- `cleanup_duplicates()`: Removed 1,180 lines of duplicate code during refactoring

---

## Game Loop Architecture

### Update Sequence (Every 50ms)
```
update() called
├─ handle_player_movement()          # Check pressed keys, apply acceleration
├─ move_enemies()                    # Update enemy positions & spawn new ones
├─ check_player_collision()          # Detect enemy-player hits
├─ update_particles()                # Update & remove dead particles
├─ update_shards()                   # Update shrapnel, check for hits
├─ update_projectiles()              # Update projectiles, check collisions
├─ update_black_holes()              # Update black holes, pull enemies
├─ update_ammo_orbs()                # Update ammo drops (future feature)
├─ update_dash_cooldown()            # Cooldown tick for dash ability
└─ update_shield_cooldown()          # Cooldown tick for shield
```

### Event Handlers
- `on_key_press()`: Store pressed key in `self.pressed_keys` set
- `on_key_release()`: Remove released key from set
- `on_canvas_click()`: Route to menu or call `attack()`
- `on_mouse_move()`: Track mouse position for attack direction

---

## Critical Coordinate Systems

### Screen Coordinates
- Origin at top-left of physical screen
- Retrieved via `winfo_pointerx()`, `winfo_pointery()`
- Used for mouse input

### Canvas Coordinates
- Origin at top-left of canvas within window
- `canvas.coords(item_id)` returns canvas coordinates
- Canvas offset from screen: `winfo_rootx()`, `winfo_rooty()`

### Canvas Dimensions (CRITICAL)
```python
# In Game.__init__():
self.window_width = self.canvas.winfo_width()      # After packing
self.window_height = self.canvas.winfo_height()

# Use these for ALL spatial calculations
# DO NOT use global WIDTH/HEIGHT constants for runtime logic
```

**Why This Matters:**
- Global WIDTH/HEIGHT are hardcoded defaults (600x400)
- Actual canvas might be maximized (2560x1369 on 4K)
- Using global constants causes:
  - Player spawning at wrong position
  - Projectiles disappearing instantly (out of bounds)
  - Movement clamping to wrong area

---

## Physics & Formulas

### Velocity to Angle Conversion
```python
angle = math.atan2(dy, dx)          # Result: -π to π radians
vx = math.cos(angle) * speed        # Speed in pixels/frame
vy = math.sin(angle) * speed
```

### Acceleration with Friction
```python
velocity += acceleration
velocity *= friction_factor         # Usually 0.85-0.95
position += velocity
```

### Distance Calculation (Optimized)
```python
# Use squared distance to avoid sqrt() when possible
dist_sq = (x2 - x1)**2 + (y2 - y1)**2

# Only use sqrt when necessary:
dist = math.hypot(dx, dy)          # More accurate than sqrt(dx^2 + dy^2)
```

### Homing Blend
```python
# Smoothly blend velocity toward target over time
target_vx = (dx / dist) * speed
target_vy = (dy / dist) * speed
self.vx += (target_vx - self.vx) * homing_strength  # 0.15 default
self.vy += (target_vy - self.vy) * homing_strength
```

---

## Upgrade System

### How Upgrades Work

1. **Selection Flow:**
   - Player reaches new level → triggers XP level-up
   - `show_upgrade_menu()` called with 3 random choices
   - Player clicks upgrade → `handle_upgrade_selection()`
   - Upgrade added to `self.active_upgrades[]`

2. **Stats Computation:**
   - `compute_weapon_stats()` calculates combined effects
   - Checks `self.active_upgrades[]` for owned upgrades
   - Sums bonuses: `damage = base + (upgrades_owned * bonus_per_level)`
   - Stores in `self.computed_weapon_stats{}`

3. **Upgrade Types:**

   **Multiplicative** (stack linearly):
   - Damage, Projectile Speed, Attack Speed

   **Boolean** (one-time effects):
   - Homing, Splits, Shrapnel, Dash, Shield

   **Linked** (require prerequisites):
   - Chain Lightning (requires base damage level 5)
   - Mini-Forks (requires chain lightning)
   - Explosive Shrapnel (requires shrapnel)

### Adding New Upgrades

1. Add to `WEAPON_UPGRADES` or `LINKED_UPGRADES` in `constants.py`:
```python
'my_upgrade': {
    'name': 'My Upgrade',
    'description': 'Does something cool',
    'one_time': False,  # Can pick multiple times
    'damage': 2,        # Bonus per level (optional)
}
```

2. In `compute_weapon_stats()` in `top_down_game.py`, add logic:
```python
level = self.active_upgrades.count('my_upgrade')
if level > 0:
    stats['my_stat'] = base_value + (level * bonus_per_level)
```

3. Use stat in entity update or attack logic:
```python
my_value = self.game.computed_weapon_stats['my_stat']
```

---

## Testing

### Test Suite (28 tests)
Located in `test_game.py`

**Coverage Areas:**
- Collision detection (circle-circle, distance calculations)
- Entity spawning and despawning
- Upgrade system logic
- Player movement bounds clamping
- Enemy wave spawning
- Edge cases (screen boundaries, missing targets, etc.)

### Running Tests
```bash
python -m pytest test_game.py -q          # Quick output
python -m pytest test_game.py -v          # Verbose
python -m pytest test_game.py::test_name  # Specific test
```

**All tests should pass (28/28)** after any code changes.

---

## Common Patterns & Best Practices

### Entity Lifecycle
```python
# Create
entity = SomeEntity(canvas, x, y, ...)
entities_list.append(entity)

# Update each frame
alive_entities = []
for entity in entities_list:
    if entity.update():  # Returns True if alive
        alive_entities.append(entity)
    else:
        entity.cleanup()  # Remove from canvas
entities_list = alive_entities
```

### Collision Detection Pattern
```python
# Find closest target, check distance
closest = None
closest_dist_sq = COLLISION_DISTANCE_SQ

for enemy in self.game.enemies:
    ex, ey = enemy.get_position()
    dx = ex - self.x
    dy = ey - self.y
    dist_sq = dx * dx + dy * dy
    
    if dist_sq < closest_dist_sq:
        closest_dist_sq = dist_sq
        closest = enemy

if closest:
    # Collision detected
```

### Canvas Coordinate Conversion
```python
# Screen → Canvas coordinates
mouse_canvas_x = canvas.winfo_pointerx() - canvas.winfo_rootx()
mouse_canvas_y = canvas.winfo_pointery() - canvas.winfo_rooty()

# Use canvas coordinates for collision checking
```

### Safe Canvas Item Cleanup
```python
def cleanup(self):
    try:
        self.canvas.delete(self.rect_id)
    except tk.TclError:
        pass  # Item already deleted or canvas destroyed
```

---

## Known Limitations & Future Improvements

### Current Limitations
- Single projectile at a time (main, non-fork projectiles)
- No melee weapons
- No inventory system
- No persistent progression (resets each game)
- Audio uses basic beep generation (no audio files)

### Potential Enhancements
1. **Multi-projectile system**: Allow more than one main projectile
2. **Weapon variety**: Melee, beams, homing missiles
3. **Enemy AI**: Patrol patterns, formation attacks
4. **Procedural generation**: Randomly generated levels
5. **Leaderboard**: Score persistence
6. **Mobile support**: Touch controls

---

## Recent Refactoring Summary

### Phase 1: Module Extraction
- Extracted constants from main file
- Extracted audio functionality to separate module
- Result: Removed 296 lines of duplicated code

### Phase 2: Entity & Menu Extraction
- Extracted all entity classes to `entities.py`
- Extracted menu system to `menus.py`
- Result: Removed 610 lines of duplicated code

### Phase 3: Type Hints & Cleanup
- Added 100% type hint coverage
- Removed 1,180 lines of duplicate code
- Result: Reduced 2,876 lines → 909 lines (main file)

### Bug Fixes
- **Projectile Firing:** Fixed by using canvas dimensions instead of global constants
- **Player Spawn:** Fixed by capturing actual canvas size in `__init__()`
- **Menu Height:** Fixed by calculating height dynamically based on button count

---

## Development Workflow

### Making Changes Safely

1. **Make Code Change**
   ```python
   # Edit the relevant file
   ```

2. **Run Tests**
   ```bash
   python -m pytest test_game.py -q
   ```

3. **Test in Game** (if applicable)
   ```bash
   python top_down_game.py
   # Play and verify changes
   ```

4. **Commit**
   ```bash
   git add -A
   git commit -m "Brief description of change"
   ```

### Debugging Tips

- Add `print()` statements to trace execution
- Use dev menu (Alt+D) to test upgrades quickly
- Check canvas dimensions with `self.window_width` and `self.window_height`
- Verify entity lists aren't growing unbounded (memory leak)
- Check for inconsistent coordinate systems (screen vs canvas)

---

## Contact & Questions

For questions about specific systems or features, refer to the relevant module's docstrings and inline comments. Each function includes type hints and documentation.

**Key Files to Review:**
- `top_down_game.py`: Game loop and main logic
- `entities.py`: Entity behavior and physics
- `constants.py`: Configuration and upgrade definitions
- `collision.py`: Collision math and detection
- `menus.py`: UI and menu systems
