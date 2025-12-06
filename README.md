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


## Installation

### Option 1: Run Executable (No Python needed)
1. Download the game folder
2. Double-click `TopDownGame.exe`
3. Play!

### Option 2: Run from Python (Requires Python 3.14+)
1. Make sure Python is installed
2. Open Command Prompt in the game folder
3. Run: `python top_down_game.py`

## Files

- `top_down_game.py` - Main game loop and Game class
- `entities.py` - All entity classes (Player, enemies, projectiles, particles, shards)
- `constants.py` - Game configuration (includes level/wave definitions)
- `sound.py` - Audio system
- `utils.py` - Utility functions

## Building Your Own Executable

If you want to rebuild the .exe:
1. Install Python 3.14+
2. Open Command Prompt in this folder
3. Run: `build_game.bat`
4. The new executable will be in the `dist/` folder

## Credits

Made with Python and Tkinter.

Enjoy the game!
