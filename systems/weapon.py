from typing import Any, List, Tuple, Optional
import math
import random
from entities import Projectile, TriangleEnemy
from constants import WEAPON_COOLDOWN_MS, ENEMY_SIZE_HALF, PROJECTILE_SPLIT_ANGLE, BLACK_HOLE_TRIGGER_CHANCE, BLACK_HOLE_BASE_RADIUS

class WeaponSystem:
    """Handles firing logic, cooldowns, and projectile spawning."""
    def __init__(self, game: Any) -> None:
        self.game = game
        self.cooldown_ms: int = 0

    def tick(self, dt_ms: int = 20) -> None:
        if self.cooldown_ms > 0:
            self.cooldown_ms = max(0, self.cooldown_ms - dt_ms)

    def can_fire(self) -> bool:
        return self.cooldown_ms == 0

    def fire(self) -> bool:
        """Fire a projectile if off cooldown. Returns True if fired."""
        if not self.can_fire():
            return False
        # Spawn projectile using current player position and stats
        px, py = self.game.player.get_center()
        stats = self.game.computed_weapon_stats
        speed = stats.get('projectile_speed', 6)
        # Aim towards last mouse position or center; here use rightward default
        vx, vy = speed, 0
        proj = Projectile(self.game.canvas, px, py, vx, vy, self.game)
        self.game.projectiles.append(proj)
        # Set cooldown
        self.cooldown_ms = WEAPON_COOLDOWN_MS
        return True

    # --- Orchestration hooks (preserve current behavior, centralize logic) ---
    def try_spawn_black_hole(self, x: float, y: float) -> None:
        """Check black hole upgrade and spawn effect based on chance."""
        stats = self.game.computed_weapon_stats
        level = stats.get('black_hole', 0)
        if level <= 0:
            return
        # Only allow one black hole at a time
        if len(self.game.black_holes) > 0:
            return
        trigger_chance = BLACK_HOLE_TRIGGER_CHANCE * level
        if random.random() > trigger_chance:
            return
        radius = BLACK_HOLE_BASE_RADIUS + (20 * level)
        from entities import BlackHole
        bh = BlackHole(self.game.canvas, x, y, radius, self.game, level)
        self.game.black_holes.append(bh)

    def handle_chain_lightning(self, origin_enemy: Any, origin_pos: Tuple[float, float]) -> None:
        """Trigger chain lightning with visuals and optional forks."""
        stats = self.game.computed_weapon_stats
        level = stats.get('chain_lightning', 0)
        if level <= 0:
            return
        # Reuse existing projectile logic by creating a temporary projectile to orchestrate chain
        proj = Projectile(self.game.canvas, origin_pos[0], origin_pos[1], 0, 0, self.game)
        proj.chain_lightning_level = level
        proj.is_mini_fork = False
        proj.bounces = 0
        proj.hit_enemies.add(id(origin_enemy))
        proj.current_target = origin_enemy
        # Execute chain: find targets, draw lines, strike, and create forks
        chain_range = 150 + (60 * level)
        range_multiplier = 0.8
        current_range = chain_range
        chain_targets: List[Tuple[Any, int]] = []
        current_center = origin_pos
        for bounce_index in range(level):
            next_target = None
            next_dist_sq = current_range * current_range
            for enemy in self.game.enemies:
                if id(enemy) in proj.hit_enemies:
                    continue
                ex, ey = enemy.get_position()
                ex_c = ex + ENEMY_SIZE_HALF
                ey_c = ey + ENEMY_SIZE_HALF
                dx = ex_c - current_center[0]
                dy = ey_c - current_center[1]
                dist_sq = dx*dx + dy*dy
                if dist_sq < next_dist_sq:
                    next_dist_sq = dist_sq
                    next_target = enemy
            if not next_target:
                break
            chain_targets.append((next_target, bounce_index))
            proj.hit_enemies.add(id(next_target))
            current_center = (next_target.get_position()[0] + ENEMY_SIZE_HALF,
                              next_target.get_position()[1] + ENEMY_SIZE_HALF)
            current_range *= range_multiplier
        # Draw chain lines between consecutive targets starting from origin_enemy
        if chain_targets:
            cur_ex, cur_ey = origin_enemy.get_position()
            current_center = (cur_ex + ENEMY_SIZE_HALF, cur_ey + ENEMY_SIZE_HALF)
            for chain_target, _bounce_index in chain_targets:
                tx, ty = chain_target.get_position()
                tx_center = (tx + ENEMY_SIZE_HALF, ty + ENEMY_SIZE_HALF)
                line_id = self.game.canvas.create_line(
                    current_center[0], current_center[1],
                    tx_center[0], tx_center[1],
                    fill='cyan', width=3
                )
                def delete_line(lid=line_id):
                    try:
                        self.game.canvas.delete(lid)
                    except Exception:
                        pass
                self.game.root.after(150, delete_line)
                current_center = tx_center
        # Strike targets and create forks on odd bounces
        for chain_target, bounce_index in chain_targets:
            proj._strike_lightning_target(chain_target)
            is_odd_bounce = (bounce_index % 2 == 0)
            if is_odd_bounce:
                self._create_fork_from_target(proj, chain_target)

    def _create_fork_from_target(self, proj: Projectile, target_enemy: Any) -> None:
        """Create fork lightning from a target to the closest nearby unhit enemy and strike it."""
        tx, ty = target_enemy.get_position()
        tx_center = tx + ENEMY_SIZE_HALF
        ty_center = ty + ENEMY_SIZE_HALF
        fork_range = 150 + (60 * proj.chain_lightning_level) * 0.8
        fork_range_sq = fork_range * fork_range
        fork_target: Optional[Any] = None
        fork_target_dist_sq = fork_range_sq
        for enemy in self.game.enemies:
            if id(enemy) in proj.hit_enemies:
                continue
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            dx = ex_center - tx_center
            dy = ey_center - ty_center
            dist_sq = dx*dx + dy*dy
            if dist_sq < fork_target_dist_sq:
                fork_target_dist_sq = dist_sq
                fork_target = enemy
        if not fork_target:
            return
        ftx, fty = fork_target.get_position()
        ftx_center = ftx + ENEMY_SIZE_HALF
        fty_center = fty + ENEMY_SIZE_HALF
        fork_line_id = self.game.canvas.create_line(
            tx_center, ty_center, ftx_center, fty_center, fill='white', width=2
        )
        def delete_fork_line(lid=fork_line_id):
            try:
                self.game.canvas.delete(lid)
            except Exception:
                pass
        self.game.root.after(150, delete_fork_line)
        proj._strike_lightning_target(fork_target)

    def create_split_projectiles(self, x: float, y: float, vx: float, vy: float) -> None:
        """Create split projectiles branching off current velocity if splits enabled."""
        stats = self.game.computed_weapon_stats
        if not stats.get('splits', True):
            return
        current_angle = math.atan2(vy, vx)
        split_angle_rad = math.radians(PROJECTILE_SPLIT_ANGLE)
        for angle_offset in (-split_angle_rad, split_angle_rad):
            new_angle = current_angle + angle_offset
            new_vx = math.cos(new_angle) * stats.get('projectile_speed', 6)
            new_vy = math.sin(new_angle) * stats.get('projectile_speed', 6)
            p = Projectile(self.game.canvas, x, y, new_vx, new_vy, self.game)
            p.homing_strength = stats.get('homing', 0)
            self.game.projectiles.append(p)
