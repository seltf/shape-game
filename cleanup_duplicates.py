#!/usr/bin/env python3
"""Remove duplicate old code from top_down_game.py"""

with open('top_down_game.py', 'r') as f:
    lines = f.readlines()

# Find the real Game class by looking for specific marker
game_class_line = None
for i, line in enumerate(lines):
    if 'Main game class. Handles game state' in line:
        # Go back to find the 'class Game:' line
        for j in range(i-1, -1, -1):
            if 'class Game:' in lines[j]:
                game_class_line = j
                break
        break

if game_class_line is not None and game_class_line > 18:
    # Remove lines 18 through game_class_line-1
    kept_lines = lines[:18] + lines[game_class_line:]
    with open('top_down_game.py', 'w') as f:
        f.writelines(kept_lines)
    print(f"Removed {game_class_line - 18} lines of duplicate code")
    print(f"File now has {len(kept_lines)} lines (was {len(lines)})")
else:
    print(f"Could not find game class line or no duplicates to remove. game_class_line={game_class_line}")
