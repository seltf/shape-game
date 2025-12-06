# Shape-Game Documentation Index

Welcome! This guide helps you find the right documentation for your needs.

---

## 🎮 For Players

**Start here:** [`README.md`](README.md)

Contains:
- How to play
- Controls and mechanics
- Game progression overview
- Installation instructions

---

## 👨‍💻 For Developers

### Quick Start

1. **First time understanding the code?**
   - Read: [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md)
   - Time: 20-30 minutes
   - Learn: Overall architecture, key files, physics formulas

2. **Need to modify wave difficulty?**
   - Read: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) → "Modifying Wave Configurations"
   - Time: 5 minutes
   - Learn: How to edit level progression without breaking anything

3. **Want to extend the system?**
   - Read: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) → "System Architecture" + "Method Reference"
   - Time: 15 minutes
   - Learn: How wave system works, what methods do what

### By Topic

#### Game Loop & Update Cycle
- **Main:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Game Loop Architecture"
- **Details:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Update Sequence"
- **Implementation:** See `top_down_game.py` → `update_logic()`

#### Enemy Spawning & Waves
- **Quick Guide:** [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) (entire document)
- **Deep Dive:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Game Level Progression System"
- **Configuration:** [`constants.py`](constants.py) → `GAME_LEVEL_WAVES`

#### Game Levels (Player Progression & Upgrades)
- **Upgrades System:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Upgrade System"
- **XP Mechanics:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "How Upgrades Work"

#### Physics & Collision Detection
- **Reference:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Physics & Formulas"
- **Collision Details:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Critical Coordinate Systems"
- **Code:** [`collision.py`](collision.py)

#### Player Controls & Input
- **Controls:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Player Controls"
- **Auto-Fire:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Auto-Fire Feature"
- **Implementation:** [`top_down_game.py`](top_down_game.py) → `on_key_press()`, `on_canvas_click()`

#### Menus & UI
- **System Overview:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → Module 4 (menus.py)
- **Implementation:** [`menus.py`](menus.py)

#### Audio System
- **Setup Guide:** [`AUDIO_SETUP.md`](AUDIO_SETUP.md)
- **Implementation:** [`audio.py`](audio.py)

#### Entities (Player, Enemies, Projectiles, etc.)
- **Overview:** [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → Module 2 (entities.py)
- **Implementation:** [`entities.py`](entities.py)

---

## 🧪 Testing & Validation

### Running Tests

```bash
# Run all unit tests (collision detection, edge cases, etc.)
python -m pytest test_game.py -v

# Should see: 28 passed ✅
```

### Analyzing Game Progression

```bash
# Visualize all 20 levels and their wave structures
python test_level_progression.py

# Useful for:
# - Verifying difficulty curve
# - Checking enemy composition
# - Understanding timing between waves
```

---

## 📁 File Structure

```
shape-game/
├── 📘 Documentation
│   ├── README.md                    ← START HERE (players)
│   ├── CODEBASE_DOCUMENTATION.md    ← Comprehensive technical reference
│   ├── DEVELOPER_GUIDE.md           ← Wave system guide
│   ├── AUDIO_SETUP.md               ← Sound effects setup
│   └── (THIS FILE)                  ← You are here
│
├── 🎮 Game Code
│   ├── top_down_game.py             ← Main game loop, ~1050 lines
│   ├── entities.py                  ← All game entities, ~1470 lines
│   ├── menus.py                     ← UI menus, ~610 lines
│   ├── audio.py                     ← Sound system, ~200 lines
│   ├── collision.py                 ← Collision detection, ~370 lines
│   ├── utils.py                     ← Utilities
│   └── constants.py                 ← Game configuration & wave definitions
│
├── 🧪 Testing
│   ├── test_game.py                 ← 28 unit tests
│   └── test_level_progression.py    ← Wave analysis tool
│
└── 🛠️ Build Tools
    ├── build_game.bat               ← Build executable
    └── shape-game.spec              ← PyInstaller config
```

---

## 🚀 Common Tasks

### "I want to make the game harder"
1. Open [`constants.py`](constants.py)
2. Find `GAME_LEVEL_WAVES`
3. Increase enemy counts or add more waves
4. Run `python test_level_progression.py` to verify
5. Test in-game: `python top_down_game.py`

### "I want to understand how waves work"
1. Read [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) → "Wave Spawning Flow"
2. Check `top_down_game.py` → `update_game_level_progression()`
3. Run `test_level_progression.py` to see examples

### "I want to add a new feature"
1. Read [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Game Loop Architecture"
2. Identify which method to modify
3. Check `test_game.py` for existing tests
4. Add your code, run tests: `pytest test_game.py -v`

### "I want to debug an issue"
1. Add debug print statements to your code
2. Run: `python top_down_game.py`
3. Check console output
4. Use dev menu (press Esc, then click "Dev Menu") for in-game testing

### "I want to modify player upgrades"
1. Open [`constants.py`](constants.py)
2. Edit `WEAPON_UPGRADES` or `LINKED_UPGRADES`
3. Read [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Adding New Upgrades"

---

## 🎯 Key Concepts

### Game Level vs. Player Level
- **Game Level:** Difficulty progression (enemy waves) - Shown in orange
- **Player Level:** Upgrade progression (XP-based) - Shown in cyan
- They are independent! You can be on Level 3 (game) with Level 5 (player)

### Wave System
- Each game level has predefined waves of enemies
- Waves spawn at specific intervals throughout the level
- After all waves complete, 3-second rest period
- Then advance to next game level

### Update Loop
- Runs at 50 FPS (20ms per tick)
- Every tick: handle input, update entities, check collisions, spawn waves
- See [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Update Sequence"

### Coordinate System
- **Canvas coordinates:** Origin at top-left of canvas
- **Always use:** `self.window_width`, `self.window_height` (not global constants)
- Ensures correct behavior on different screen sizes

---

## 📚 Reference

### Document Sizes & Complexity

| Document | Size | Complexity | Best For |
|----------|------|-----------|----------|
| README.md | 2 KB | ⭐ Simple | Players, getting started |
| AUDIO_SETUP.md | 3 KB | ⭐ Simple | Sound effects setup |
| DEVELOPER_GUIDE.md | 12 KB | ⭐⭐ Medium | Understanding wave system |
| CODEBASE_DOCUMENTATION.md | 44 KB | ⭐⭐⭐ Deep | Full technical reference |

### Code Statistics

| File | Lines | Purpose | Complexity |
|------|-------|---------|-----------|
| top_down_game.py | ~1050 | Main game loop | ⭐⭐⭐ High |
| entities.py | ~1470 | Entity classes | ⭐⭐⭐ High |
| menus.py | ~610 | UI management | ⭐⭐ Medium |
| collision.py | ~370 | Collision logic | ⭐⭐ Medium |
| audio.py | ~200 | Sound system | ⭐ Simple |
| constants.py | ~210 | Configuration | ⭐ Simple |
| test_game.py | ~400 | Unit tests | ⭐⭐ Medium |

---

## ❓ FAQ

**Q: Where do I change how many enemies spawn per level?**
A: Edit `GAME_LEVEL_WAVES` in [`constants.py`](constants.py)

**Q: How do I add a new level?**
A: Add entry to `GAME_LEVEL_WAVES` dict with wave configuration

**Q: Can I add levels beyond 20?**
A: Yes! Either add to `GAME_LEVEL_WAVES` or let auto-generation handle it

**Q: How do I test my changes?**
A: Run `python test_level_progression.py` then play the game

**Q: Where's the game configuration?**
A: All constants in [`constants.py`](constants.py), main logic in [`top_down_game.py`](top_down_game.py)

**Q: How do I add a new upgrade?**
A: See [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Adding New Upgrades"

**Q: Where's the collision detection?**
A: See [`collision.py`](collision.py) and [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Critical Coordinate Systems"

---

## 🔗 Cross-References

**Learning Path for Wave System:**
1. Start: [`README.md`](README.md) → Game Progression section
2. Next: [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) → Quick Summary + System Architecture
3. Deep: [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → Game Level Progression System
4. Code: [`top_down_game.py`](top_down_game.py) → `update_game_level_progression()` method
5. Config: [`constants.py`](constants.py) → `GAME_LEVEL_WAVES` dict
6. Test: Run `python test_level_progression.py`

---

## 📞 Getting Help

1. **Something not working?** → Run `python -m pytest test_game.py -v`
2. **Don't understand architecture?** → Read [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md)
3. **Want to modify waves?** → See [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md)
4. **Need to add features?** → Check [`CODEBASE_DOCUMENTATION.md`](CODEBASE_DOCUMENTATION.md) → "Adding New Upgrades" pattern
5. **Game playing strangely?** → Enable dev menu in pause screen for testing tools

---

**Last Updated:** December 6, 2025  
**Wave System Version:** 1.0 (Production Ready)  
**All Tests:** ✅ Passing (28/28)
