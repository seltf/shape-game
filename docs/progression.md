# Progression System

This doc outlines level progression, waves, timers, and boss flow.

## Concepts
- **Game Level**: Difficulty stage with predefined waves.
- **Player Level**: XP-driven upgrades; independent from game level.
- **Rest Timer**: Short pause between levels.
- **Boss**: Special enemy with unique health and rewards.

## Flow
1. Level starts → spawn waves according to schedule.
2. All waves completed → start rest timer.
3. After rest → advance to next level.
4. Boss levels: spawn boss and manage fight loop.

## Configuration
- Defined in `constants.py` (e.g., `GAME_LEVEL_WAVES`, enemy counts, timings).
- Linked upgrades (prerequisites) enforced in `Game.add_upgrade()`.
- Base enemy speeds tuned in `top_down_game.py` to adjust difficulty (slower by default).

## Implementation
- `systems/progression.py` manages timers and wave spawning.
- `top_down_game.py` delegates level/boss/update orchestration to ProgressionSystem.

## Upgrades
- Base stats computed into `game.computed_weapon_stats`.
- Weapon effects use those stats to apply behavior consistently.

## Testing
- See `test_progression_pytest.py` and `test_progression_timers_pytest.py`.
- Boss-level and rest-timer behaviors verified.
