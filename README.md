# Top Down Game

A fast-paced top-down shooter where you control a player dodging and defeating enemies while upgrading your weapon through a progressive level system!

## How to Play

**Controls (Dvorak Layout):**
- `,` - Move Up
- `O` - Move Down  
- `A` - Move Left
- `E` - Move Right
- `SPACE` - Toggle Auto-Fire
- `ESC` - Pause Menu
- `CLICK` - Fire projectile

**Game Progression:**
- **Game Level**: Progresses through 20+ difficulty levels (separate from player upgrades)
  - Each level has predefined waves of enemies
  - Waves spawn at specific times throughout the level
  - 3-second rest period between levels to recover
  - Enemies become progressively harder (more health, higher damage)
  
- **Player Level**: Increases as you gain XP (for upgrades)
  - Kill enemies to gain XP and level up
  - Regular enemies: 1 XP
  - Triangle enemies: 3 XP each
  - Pentagon enemies: 7 XP each
  - Choose one upgrade at each player level-up

**Available Upgrades:**
- `Extra Bounce` - Projectile bounces more times before returning
- `Shrapnel` - Projectile spawns shards on impact that kill enemies
- `Speed Boost` - Increases projectile speed
- `Black Hole` - Create damaging vortexes
- `Shield` - Protective barrier around player
- `Rapid Fire` - Faster projectile firing
- `Summon Minion` - Spawn friendly minions to attack enemies

**Enemy Types:**
- **Basic Enemies** - Circular, 1 hit to kill, 1 XP (Levels 1-20)
- **Triangle Enemies** - Purple triangles, 3 hits to kill, 3 XP (Levels 5+)
- **Pentagon Enemies** - Green pentagons, 5 hits to kill, 7 XP (Levels 10+)


## Quick Start

### Run from Python (macOS/Linux/Windows)
1. Install Python 3.12.
2. In Terminal/Command Prompt:
  ```sh
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
  pip install -r requirements.txt
  python top_down_game.py
  ```

### Run tests (headless)
```sh
source .venv/bin/activate
pytest -q
```

## Files

- `top_down_game.py` - Main game loop and `Game` class
- `entities.py` - Player, enemies, projectiles, particles, shards
- `constants.py` - Tunables (sizes, speeds, waves, upgrade defaults)
- `systems/` - Weapon, input, progression systems
- `ui/hud.py` - Heads-up display
- `audio.py` - Audio backend and helpers
- `docs/` - Architecture, progression, testing, audio docs

## Build

To build a standalone executable (Windows):
1. Install Python 3.12
2. Run:
  ```sh
  pip install -r requirements.txt
  build_game.bat
  ```
3. The executable will be created per the PyInstaller spec.

## Credits

Made with Python and Tkinter.

More details in `docs/`:
- `docs/architecture.md` — systems overview and update loop
- `docs/progression.md` — levels, waves, timers, boss
- `docs/testing.md` — headless tests and coverage
- `docs/audio.md` — audio behavior and fallbacks

Enjoy the game!
