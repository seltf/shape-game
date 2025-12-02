# Top Down Game

A fast-paced top-down shooter where you control a player dodging and defeating enemies while upgrading your weapon!

## How to Play

**Controls (Dvorak Layout):**
- `,` - Move Up
- `O` - Move Down  
- `A` - Move Left
- `E` - Move Right
- `SPACE` - Dash (short burst of speed)
- `ESC` - Pause Menu
- `CLICK` - Fire projectile (auto-fires at closest enemy)

**Game Mechanics:**
- **Score**: Tracks total enemy kills
- **Level**: Increases as you gain XP
- **XP System**: Kill enemies to gain XP and level up
  - Regular enemies: 1 XP
  - Triangle enemies (Level 5+): 3 XP each
- **Upgrades**: Choose one at each level-up

**Available Upgrades:**
- `Extra Bounce` - Projectile bounces more times before returning
- `Shrapnel` - Projectile spawns shards on impact that kill enemies
- `Speed Boost` - Increases projectile speed

**Enemy Types:**
- **Square Enemies** - Red, weak, 1 hit to kill
- **Triangle Enemies** - Orange, tough, 3 hits to kill (appears at Level 5+)

**Gameplay Tips:**
- Position yourself to maximize bounces
- Stack the same upgrades for better scaling (Extra Bounce x3 is powerful!)
- Triangle enemies are worth 3x the XP, use them to level up faster
- Dash away from enemy clusters
- Shrapnel shards only kill one enemy each

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
- `config.py` - Game constants and weapon stats
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
