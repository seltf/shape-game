# Phase 2 Refactoring Plan: Entity Extraction

## Overview
Phase 2 focuses on extracting entity classes from the monolithic `top_down_game.py` into dedicated modules. This will further improve code organization, testability, and maintainability.

## Current State (After Phase 1)
- **Files**: 3 (constants.py, audio.py, top_down_game.py)
- **Main file size**: 2,612 lines
- **Classes in top_down_game.py**: 8 entity classes + 1 game class
- **Global state**: Eliminated from audio system ✅

## Phase 2 Goals
1. Extract all entity classes into separate module (`entities.py`)
2. Extract all menu logic into menu manager (`menus.py`)
3. Reduce main file from 2,612 to ~1,200 lines
4. Improve testability of entity behaviors
5. Separate concerns: entities vs game logic vs UI

## Phase 2 Tasks

### Task 2.1: Create `entities.py` Module
**Scope**: Extract all 6 entity/effect classes

**Classes to Extract**:
1. `BlackHole` (lines 14-245)
   - Current features: Detonation, enemy pulling, ring animation
   - Dependencies: canvas, game instance, constants
   
2. `Player` (lines 247-371)
   - Current features: Movement, shield system, position tracking
   - Dependencies: canvas, game instance, constants
   
3. `Enemy` (lines 373-424)
   - Base class for all enemies
   - Current features: Basic movement toward target
   - Dependencies: canvas, constants
   
4. `TriangleEnemy` (lines 426-489)
   - Current features: Triangle shape rendering, damage tracking
   - Inherits from: Enemy
   - Dependencies: canvas, constants, Enemy
   
5. `PentagonEnemy` (lines 491-556)
   - Current features: Pentagon shape rendering, damage tracking
   - Inherits from: Enemy
   - Dependencies: canvas, constants, Enemy
   
6. `Particle` (lines 558-587)
   - Current features: Movement, decay, cleanup
   - Dependencies: canvas, constants
   
7. `Shard` (lines 591-679)
   - Current features: Movement, collision detection, explosion
   - Dependencies: canvas, game instance, constants
   
8. `Projectile` (lines 681-1195)
   - Current features: Complex movement, targeting, splitting, black hole spawning
   - Dependencies: canvas, game instance, constants, math
   - **Note**: Largest entity class (~500 lines), consider for Phase 3 further modularization

**File Structure** (entities.py):
```python
# Imports
from constants import *
import math
import random

# Entity classes in order:
# - BlackHole
# - Player
# - Enemy (base class)
# - TriangleEnemy
# - PentagonEnemy
# - Particle
# - Shard
# - Projectile

# Total expected lines: 900-1000
```

**Update top_down_game.py**:
- Add import: `from entities import BlackHole, Player, Enemy, TriangleEnemy, PentagonEnemy, Particle, Shard, Projectile`
- Remove entity class definitions (lines 14-1195)

**Expected Result**:
- entities.py: ~950 lines
- top_down_game.py: ~1,650 lines (2,612 - 950 + imports)

### Task 2.2: Create `menus.py` Module (MenuManager)
**Scope**: Consolidate all menu-related functionality

**Menu Methods to Extract**:
1. `show_upgrade_menu()` (lines 1591-1703)
2. `on_upgrade_selection()` (lines 1704-1714)
3. `close_upgrade_menu()` (lines 1715-1731)
4. `show_pause_menu()` (lines 1733-1913)
5. `show_dev_menu()` (lines 1944-2058)
6. `_handle_dev_menu_action()` (lines 2016-2058)
7. `close_dev_menu()` (lines 2059-2073)
8. `hide_pause_menu()` (lines 2075-2092)
9. `on_pause_menu_click()` (lines 2094-2108)

**Menu Data Storage**:
- `self.pause_menu_id`
- `self.pause_menu_elements` (list)
- `self.pause_buttons` (dict)
- `self.dev_buttons` (dict)
- `self.dev_menu_active`
- `self.upgrade_menu_active`
- `self.upgrade_menu_clickable`
- `self.upgrade_buttons` (dict)
- `self.upgrade_choices`

**MenuManager Class Design**:
```python
class MenuManager:
    def __init__(self, game_instance):
        self.game = game_instance
        # State
        self.pause_menu_id = None
        self.pause_menu_elements = []
        self.pause_buttons = {}
        self.dev_buttons = {}
        self.dev_menu_active = False
        self.upgrade_menu_active = False
        self.upgrade_menu_clickable = False
        self.upgrade_buttons = {}
        self.upgrade_choices = []
    
    # Menu methods
    def show_upgrade_menu(self): ...
    def on_upgrade_selection(self, upgrade_key): ...
    def close_upgrade_menu(self): ...
    def show_pause_menu(self): ...
    def show_dev_menu(self): ...
    def _handle_dev_menu_action(self, action): ...
    def close_dev_menu(self): ...
    def hide_pause_menu(self): ...
    def on_pause_menu_click(self, event): ...
```

**File Structure** (menus.py):
```python
# Imports
from constants import *
import random

class MenuManager:
    # Full menu implementation
    # Total expected lines: 400-500
```

**Update top_down_game.py**:
- Add import: `from menus import MenuManager`
- In Game.__init__: `self.menu_manager = MenuManager(self)`
- Replace menu methods with calls to `self.menu_manager.method_name()`
- Update on_canvas_click to delegate to menu manager
- Remove menu methods from Game class

**Expected Result**:
- menus.py: ~450 lines
- top_down_game.py: ~1,200 lines (1,650 - 450 + delegation code)

### Task 2.3: Update `top_down_game.py`
**Scope**: Clean up imports and adapt to new module structure

**Changes**:
1. Update imports at top of file:
   ```python
   from constants import *
   from audio import play_sound_async, play_beep_async, start_background_music, stop_background_music
   from entities import BlackHole, Player, Enemy, TriangleEnemy, PentagonEnemy, Particle, Shard, Projectile
   from menus import MenuManager
   ```

2. Remove menu-related state variables from Game.__init__

3. Update references in Game class:
   - `self.show_upgrade_menu()` → `self.menu_manager.show_upgrade_menu()`
   - `self.upgrade_menu_active` → `self.menu_manager.upgrade_menu_active`
   - `self.dev_menu_active` → `self.menu_manager.dev_menu_active`
   - `self.paused` stays in Game (used by many methods)

4. Update on_canvas_click to handle menu manager integration

5. Remove entity class definitions

6. Keep all game loop logic and state management

**Expected Result**:
- Clean imports at top
- Game class focused on game logic, not UI
- All state references properly delegated

## Phase 2 Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| File Count | 3 | 5 | ✓ |
| Main file (lines) | 2,612 | 1,200 | ✓ |
| Entity file (lines) | 0 | 950 | ✓ |
| Menu file (lines) | 0 | 450 | ✓ |
| Classes per file | 9 in main | 1 main + 2 mgmt | ✓ |
| Testability | Low | Medium | ✓ |
| Code reuse | None | Entities reusable | ✓ |

## Phase 2 Estimated Timeline

- **Task 2.1** (entities.py): 2-3 hours
  - Extract 8 classes
  - Test imports
  - Verify entity functionality
  
- **Task 2.2** (menus.py): 1.5-2 hours
  - Create MenuManager class
  - Extract menu methods
  - Test menu interactions
  
- **Task 2.3** (top_down_game.py): 1-1.5 hours
  - Update imports and references
  - Verify game logic still works
  - Integration testing
  
**Total Phase 2**: 4.5-6.5 hours

## Phase 2 Benefits

✅ **Improved Code Organization**
- Entity classes separate from game logic
- Menu logic centralized in MenuManager
- Clear module responsibilities

✅ **Enhanced Testability**
- Entities can be tested independently
- Menu logic can be tested in isolation
- Easier to mock dependencies

✅ **Better Maintainability**
- Smaller, focused files (easier to understand)
- Related code grouped together
- Reduced coupling

✅ **Reusability**
- Entities module can be reused in other projects
- MenuManager pattern can be adapted

✅ **Performance** (eventual)
- Smaller files = faster loading
- Better opportunity for optimization

## Phase 2 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Breaking entity references | High | Comprehensive testing after extraction |
| Menu state sync issues | High | Careful delegation pattern implementation |
| Circular imports | Medium | Careful module dependency design |
| Performance regression | Low | Monitor game loop performance |

## Next Steps After Phase 2

**Phase 3: Quality & Polish**
- Add comprehensive type hints throughout
- Extract collision detection system
- Refactor ProjectileManager from Projectile class
- Add docstrings to all classes and methods
- Create unit tests for core systems
- Estimated: 4-6 hours

## Success Criteria

- ✅ All tests pass with new module structure
- ✅ Game runs without errors
- ✅ No performance regression
- ✅ Menu systems responsive
- ✅ Entity behaviors unchanged
- ✅ Code is more readable and maintainable
- ✅ Each module has single clear responsibility

---

**Phase 1 Status**: ✅ COMPLETE (Commit 995fd3e)
**Phase 2 Status**: 📋 PLANNED
**Phase 2 Start**: Ready to begin
