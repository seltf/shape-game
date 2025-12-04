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
- `on_key_press()`: Store pressed key in `self.pressed_keys` set; handle special keys (E for auto-fire toggle, Escape for menu)
- `on_key_release()`: Remove released key from set
- `on_canvas_click()`: Route to menu or call `attack()`
- `on_mouse_move()`: Track mouse position for attack direction

### Player Controls

**Movement Controls (Layout-Independent)**
- **W / Comma (Dvorak) / Up Arrow**: Move up
- **A**: Move left
- **S / O (Dvorak) / Down Arrow**: Move down
- **D / E (Dvorak) / Right Arrow**: Move right

**Combat Controls**
- **Mouse Click / Left Button**: Fire projectile toward mouse cursor
- **E Key (QWERTY) / Physical position-based**: Toggle auto-fire on/off

**System Controls**
- **Escape**: Open/close pause menu

**Auto-Fire Feature**
- Pressing E toggles auto-fire mode on/off
- When enabled, projectiles fire automatically every 500ms
- Auto-fire respects normal firing rules:
  - Cannot fire while paused or upgrade menu is open
  - Cannot fire while a main projectile is already active
  - Respects the 500ms attack cooldown between shots
- Console displays "Auto-fire ENABLED" or "Auto-fire DISABLED" when toggled

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

### Core Gameplay Features

**Auto-Fire Mode**
- Press E key to toggle on/off (position-based, works on QWERTY/Dvorak)
- When enabled, automatically fires projectiles every 500ms
- Respects all normal firing rules (can't fire during pause, with active projectile, or in menus)
- State is tracked in `self.auto_fire_enabled` boolean
- Attack cooldown managed by `self.attack_cooldown` counter in milliseconds
- Useful for extended play sessions or handling many enemies

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

## AI Agent Instructions for Code Modifications

**⚠️ CRITICAL: DOCUMENTATION MAINTENANCE**

**ANY AI agent working on this codebase MUST update CODEBASE_DOCUMENTATION.md whenever:**
- New features are added (upgrades, entities, mechanics)
- Game architecture changes
- New modules or significant refactoring occurs
- Coordinate system behavior changes
- New common patterns or best practices emerge

**The documentation is the contract between developers. Stale documentation leads to duplicated bugs and wasted time. ALWAYS keep docs current with code changes.**

When an AI agent is tasked with modifying, debugging, or expanding this codebase, the following guidelines ensure quality, consistency, and maintainability:

### Pre-Modification Checklist

1. **Understand Coordinate Systems First**
   - Never assume global WIDTH/HEIGHT are correct at runtime
   - Always use `self.window_width` and `self.window_height` for spatial logic
   - Screen coordinates: `winfo_pointerx/y()`
   - Canvas coordinates: subtract `winfo_rootx/y()` from screen coords
   - This is the #1 source of bugs in this codebase

2. **Review Related Tests Before Changing**
   - Run `python -m pytest test_game.py -q` before making changes
   - After changes, run again to ensure no regressions
   - All 28 tests must pass after any modification
   - If a test fails, the change likely introduced a bug

3. **Check Physics Constants**
   - Verify collision distance squared: `COLLISION_DISTANCE_SQ = 1024`
   - Verify enemy sizes: `ENEMY_SIZE_HALF = 20`
   - Never hardcode these values in entity code
   - Import from `constants.py` instead

### Type Hints & Code Quality

1. **100% Type Coverage Required**
   - Every function parameter must have a type hint
   - Every function return value must have a type hint
   - Use `Optional[T]` for nullable values
   - Use `List[T]`, `Dict[K, V]`, `Tuple[T, ...]` for collections
   - Use `Any` only when necessary (document why)

   Example:
   ```python
   def attack(self) -> None:
       """Launch a projectile if none are active."""
       
   def get_attack_direction(self) -> float:
       """Calculate the angle from player to mouse. Returns radians (-π to π)."""
   ```

2. **Docstrings on All Functions**
   - One-line summary describing what the function does
   - Multi-line summary including parameters and return value behavior
   - Document important side effects (modifies game state, spawns entities, etc.)
   - Document assumptions (e.g., "Assumes canvas is fully rendered")

3. **Variable Naming Conventions**
   - Use descriptive names: `projectile_speed` not `ps`
   - Use snake_case for variables/functions: `move_player()` not `movePlayer()`
   - Use UPPER_CASE for constants: `PLAYER_SIZE`, `COLLISION_DISTANCE_SQ`
   - Prefix private/internal with underscore: `_find_closest_target()`
   - Use `_id` suffix for Tkinter canvas item IDs: `self.rect_id`, `self.text_id`

### Entity Lifecycle Pattern (MANDATORY)

All entities must follow this pattern:

```python
class NewEntity:
    def __init__(self, canvas: tk.Canvas, x: float, y: float, game: Any) -> None:
        self.canvas = canvas
        self.game = game
        self.x = x
        self.y = y
        self.rect = canvas.create_oval(...)
    
    def update(self) -> bool:
        """Update entity state. Return True to keep alive, False to despawn."""
        # ... update logic ...
        self.canvas.coords(self.rect, self.x-r, self.y-r, self.x+r, self.y+r)
        return True  # Keep alive
    
    def cleanup(self) -> None:
        """Remove from canvas. Called when entity is despawned."""
        try:
            self.canvas.delete(self.rect)
        except tk.TclError:
            pass  # Already deleted

# In Game class:
def update_new_entities(self) -> None:
    """Update all new entities and remove dead ones."""
    alive = []
    for entity in self.new_entities:
        if entity.update():
            alive.append(entity)
        else:
            entity.cleanup()
    self.new_entities = alive
```

### Collision Detection Pattern (MANDATORY)

Use squared distances to avoid expensive `sqrt()` calls:

```python
# CORRECT: Use squared distance
closest_dist_sq = COLLISION_DISTANCE_SQ
for enemy in self.game.enemies:
    ex, ey = enemy.get_position()
    dx = ex - self.x
    dy = ey - self.y
    dist_sq = dx * dx + dy * dy  # No sqrt!
    
    if dist_sq < closest_dist_sq:
        closest_dist_sq = dist_sq
        closest_enemy = enemy

# ONLY use sqrt when necessary for physics:
dist = math.hypot(dx, dy)  # More accurate than sqrt(dx²+dy²)
```

### Canvas Operations Safety

1. **Always wrap canvas.delete() in try-except**
   ```python
   try:
       self.canvas.delete(self.rect_id)
   except tk.TclError:
       pass  # Item may have already been deleted
   ```

2. **Don't call winfo methods on destroyed canvas**
   - Check that canvas exists before calling `winfo_width()`, etc.
   - Store dimensions in instance variables when known

3. **Update canvas coordinates each frame**
   - Must call `self.canvas.coords()` after position changes
   - Without this, visual position won't match actual position

### Game State Management

1. **Never Directly Modify Global Constants at Runtime**
   - ❌ WRONG: `global WIDTH; WIDTH = new_width`
   - ✅ RIGHT: Use `self.window_width` instance variable
   - Global constants are for defaults only

2. **Use computed_weapon_stats for All Weapon Values**
   - Never hardcode damage, speed, or other stats in entity code
   - Always read from `self.game.computed_weapon_stats[stat_name]`
   - This ensures upgrades work consistently everywhere

3. **Track Active Upgrades Correctly**
   - Upgrades stored in `self.active_upgrades[]` (can have duplicates for leveling)
   - Count duplicates to determine upgrade level: `self.active_upgrades.count('upgrade_name')`
   - Use `'upgrade_name' in self.active_upgrades` to check if owned

### Adding New Features

#### Adding a New Upgrade

1. Define in `constants.py`:
   ```python
   'my_upgrade': {
       'name': 'My Upgrade Name',
       'description': 'What it does',
       'one_time': False,  # Or True if can only pick once
       'damage': 2,        # Bonus per level (optional)
   }
   ```

2. Add stat computation in `top_down_game.py`:
   ```python
   def compute_weapon_stats(self) -> None:
       # ... existing code ...
       level = self.active_upgrades.count('my_upgrade')
       if level > 0:
           stats['my_stat'] = base_value + (level * bonus_per_level)
   ```

3. Use in entity or attack logic:
   ```python
   my_value = self.game.computed_weapon_stats.get('my_stat', default_value)
   ```

4. Test with dev menu (Alt+D) before committing

#### Adding a New Entity Type

1. Create class in `entities.py` following entity lifecycle pattern
2. Add `update_<new_entities>()` method to `Game` class
3. Call from main `update()` loop
4. Initialize empty list in `Game.__init__()`
5. Add to docstring in `update()` showing call sequence
6. Add tests to `test_game.py` to verify:
   - Entity spawns correctly
   - Update is called properly
   - Cleanup removes from canvas
   - Collision detection works if applicable

#### Adding a New Menu

1. Create methods in `menus.py` (show_X_menu, close_X_menu)
2. Store element IDs in lists for easy cleanup
3. Use actual canvas dimensions: `self.canvas.winfo_width()`
4. Calculate positions dynamically (not hardcoded)
5. Add 300ms delay for buttons to prevent accidental clicks
6. Handle clicks in menu's click handler

#### Adding New Control Features

1. Add state variable in `Game.__init__()`:
   ```python
   self.feature_enabled = False  # Toggle state
   ```

2. Add key handling in `on_key_press()`:
   ```python
   elif event.keysym == 'keysym_name':  # Check keysym, not event.char
       self.feature_enabled = not self.feature_enabled
       print(f"Feature {'ENABLED' if self.feature_enabled else 'DISABLED'}")
   ```

3. Implement feature logic in `update()` loop:
   ```python
   if self.feature_enabled and <precondition>:
       self.do_feature()
   ```

4. Example: Auto-fire feature uses:
   - `self.auto_fire_enabled`: Toggle state (bool)
   - `self.attack_cooldown`: Fire rate limiter (int, milliseconds)
   - `if self.attack_cooldown <= 0`: Check if ready to fire
   - `self.attack_cooldown = PROJECTILE_RETURN_TIME_MS`: Reset cooldown
   - `self.attack()`: Execute action

### Performance Considerations

1. **Avoid sqrt() in Collision Loops**
   - Use squared distance comparison instead
   - Only calculate `math.hypot()` when necessary for physics

2. **Cache Frequently Accessed Values**
   - Store `canvas_width = self.canvas.winfo_width()` in local var in tight loops
   - Don't call `winfo_` methods hundreds of times per frame

3. **Use Slice to Avoid Modification During Iteration**
   ```python
   # WRONG: Modifying list being iterated
   for enemy in self.enemies:
       if should_remove:
           self.enemies.remove(enemy)
   
   # CORRECT: Iterate copy, modify original
   for enemy in self.enemies[:]:
       if should_remove:
           self.enemies.remove(enemy)
   ```

4. **Check Entity Existence Before Accessing**
   - Enemies might be removed between frames
   - Always verify entity still in list before using: `if enemy in self.game.enemies`

### Testing Requirements

1. **Run Tests After ANY Change**
   ```bash
   python -m pytest test_game.py -q
   ```

2. **All 28 Tests Must Pass**
   - If a test fails, the change broke something
   - Fix the code, not the test
   - Only add new tests when adding new features

3. **Test in Game if GUI-Related**
   - Visual changes should be manually verified
   - Run `python top_down_game.py` and test with player
   - Check on various screen sizes if coordinate-related

4. **Check for Memory Leaks**
   - Play for 5+ minutes
   - Watch for entities accumulating without despawning
   - Check task manager for memory growth

### Git Commit Guidelines

1. **Atomic Commits**
   - One logical change per commit
   - ❌ Wrong: "Fix collision, add upgrade, improve menu"
   - ✅ Right: "Fix projectile collision detection with enemies"

2. **Descriptive Commit Messages**
   - Format: `Fix: Issue description` or `Add: Feature description`
   - Include what was changed and why
   - Reference any related bugs or features

3. **Verify Before Committing**
   - Run all tests
   - Manual gameplay test if touching visuals/physics
   - Review changes: `git diff`

### Debugging Strategy

1. **Add Debug Output**
   ```python
   print(f"[DEBUG] Player position: ({self.x:.1f}, {self.y:.1f})")
   print(f"[ACTION] Enemy spawned at ({ex:.1f}, {ey:.1f})")
   print(f"[ERROR] Collision detection failed: {e}")
   ```

2. **Check Coordinate Systems First**
   - Is the entity using screen or canvas coordinates?
   - Are you comparing screen coords with canvas coords?
   - Is the bounds check using correct canvas dimensions?

3. **Verify Entity Lists Aren't Growing**
   - Print list lengths periodically: `len(self.enemies)`, `len(self.projectiles)`
   - Accumulating entities = memory leak

4. **Use Dev Menu for Testing**
   - Press Alt+D to open dev menu
   - Spawn enemies, give XP, add upgrades quickly
   - Faster than playing through the game

### Documentation Standards

1. **Update CODEBASE_DOCUMENTATION.md When:**
   - Adding new entity types
   - Adding new upgrade system features
   - Changing coordinate system logic
   - Adding new game mechanics
   - Modifying game loop sequence

2. **Keep Docstrings Current**
   - If function behavior changes, update docstring
   - If new parameters added, document them
   - If side effects change, document new behavior

### Code Review Checklist for AI Agents

Before completing any task, verify:

- [ ] **Documentation updated** (CRITICAL - update CODEBASE_DOCUMENTATION.md if features/architecture changed)
- [ ] All tests pass (28/28)
- [ ] Type hints on all functions
- [ ] Docstrings on all functions
- [ ] Used `self.window_width/height` not global WIDTH/HEIGHT
- [ ] Used `self.canvas.winfo_width/height()` for actual dimensions
- [ ] Collision logic uses squared distances
- [ ] Entity cleanup is wrapped in try-except
- [ ] Canvas coordinates updated after position changes
- [ ] Weapon stats read from `computed_weapon_stats`
- [ ] No hardcoded values that should be constants
- [ ] Descriptive variable names (no single letters except i, j, k for loops)
- [ ] Memory leak check (entities despawn properly)
- [ ] Manual gameplay test if touching visuals/physics
- [ ] Git commit made with descriptive message
- [ ] Documentation updated if adding features

---

## Contact & Questions

For questions about specific systems or features, refer to the relevant module's docstrings and inline comments. Each function includes type hints and documentation.

**Key Files to Review:**
- `top_down_game.py`: Game loop and main logic
- `entities.py`: Entity behavior and physics
- `constants.py`: Configuration and upgrade definitions
- `collision.py`: Collision math and detection
- `menus.py`: UI and menu systems
