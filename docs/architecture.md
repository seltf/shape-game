# Architecture Overview

This document provides a lean overview of the current game architecture for quick onboarding and future maintenance.

## Core Modules
- `top_down_game.py`: Orchestrates game loop, state, spawning, input, and rendering.
- `entities.py`: Player, enemies, projectiles, particles, shards, minions.
- `systems/weapon.py`: WeaponSystem for cooldowns, firing, and effects (chain, splits, black hole).
- `systems/progression.py`: Level progression, waves, rest/boss timers.
- `systems/input.py`: Normalized key/mouse input mapping.
- `ui/hud.py`: Heads-up display for stats, timers, and perf.
- `collision.py`: Collision checks and helpers.
- `constants.py`: Tunables: sizes, speeds, waves, upgrade defaults.

## Update Loop
- Logic tick: 50 FPS (~20ms)
- Render tick: separate canvas updates to keep UI responsive
- Sequence (logic):
  1. Process input
  2. Progression tick (waves/boss/rest)
  3. Weapon tick (cooldowns)
  4. Update entities (move, handle effects)
  5. Collisions and cleanup
  6. HUD update

## Weapon Effects
- Centralized in `WeaponSystem`:
  - `fire()`: spawns a projectile and applies cooldown.
  - `handle_chain_lightning(enemy, pos)`: draws chain lines, strikes targets, creates forks.
  - `create_split_projectiles(x, y, vx, vy)`: two split shots at fixed angle.
  - `try_spawn_black_hole(x, y)`: chance-based spawn; one at a time.
- `Projectile` delegates effect hooks to `WeaponSystem`.

## Entities Lifecycle
- All entities inherit `BaseEntity` with `alive`, `cleanup()`, and `get_position()`.
- Enemies implement `take_damage()` and visuals cleanup.
- Projectiles track bounces, returning behavior, and effect triggers.

## State & UI
- Game state handled in `Game` (Main Menu/Title Screen, Playing, Paused, Upgrade, Dev, Game Over).
- Title Screen is a standalone state, rendered via `MenuManager`.
- Title Screen background: starfield + animated tilted galaxy.
- Pause menu `Quit`: returns to Title Screen (does not exit app).
- Title Screen `Quit`: exits the application.
- HUD updates via `ui/hud.py` with minimal canvas ops.

## Design Principles
- Centralize cross-cutting logic (weapon/progression/input/HUD) in systems.
- Keep gameplay unchanged while improving testability.
- Prefer canvas dimension queries over global width/height.
- Render loop always flushes UI across states to avoid blank screens.
