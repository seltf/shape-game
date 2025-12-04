"""
Collision detection system for shape-game.
Handles all collision detection and response logic between game entities.
"""

import math
from typing import Tuple, List, Any, Optional, Set
from constants import (
    PLAYER_SIZE, ENEMY_SIZE, ENEMY_SIZE_HALF,
    COLLISION_DISTANCE, COLLISION_DISTANCE_SQ
)


class CollisionDetector:
    """Handles all collision detection between game entities."""
    
    @staticmethod
    def check_circle_rectangle_collision(
        circle_x: float, circle_y: float, circle_radius: float,
        rect_x: float, rect_y: float, rect_width: float, rect_height: float
    ) -> bool:
        """
        Check if a circle collides with an axis-aligned rectangle.
        
        Args:
            circle_x: Center X of circle
            circle_y: Center Y of circle
            circle_radius: Radius of circle
            rect_x: Left X of rectangle
            rect_y: Top Y of rectangle
            rect_width: Width of rectangle
            rect_height: Height of rectangle
            
        Returns:
            True if collision detected, False otherwise
        """
        # Find closest point on rectangle to circle center
        closest_x = max(rect_x, min(circle_x, rect_x + rect_width))
        closest_y = max(rect_y, min(circle_y, rect_y + rect_height))
        
        # Calculate distance between circle center and closest point
        dx = circle_x - closest_x
        dy = circle_y - closest_y
        dist_sq = dx * dx + dy * dy
        
        return dist_sq < (circle_radius * circle_radius)
    
    @staticmethod
    def check_distance_collision(
        x1: float, y1: float, 
        x2: float, y2: float,
        collision_distance: float
    ) -> Tuple[bool, float]:
        """
        Check if two points collide based on distance threshold.
        
        Args:
            x1: First point X
            y1: First point Y
            x2: Second point X
            y2: Second point Y
            collision_distance: Distance threshold for collision
            
        Returns:
            Tuple of (collision_detected, actual_distance_squared)
        """
        dx = x2 - x1
        dy = y2 - y1
        dist_sq = dx * dx + dy * dy
        collision_dist_sq = collision_distance * collision_distance
        
        return dist_sq < collision_dist_sq, dist_sq
    
    @staticmethod
    def check_player_enemy_collision(
        player_x: float, player_y: float,
        enemy_x: float, enemy_y: float,
        player_size: int = PLAYER_SIZE,
        enemy_size: int = ENEMY_SIZE
    ) -> bool:
        """
        Check if player collides with an enemy.
        
        Args:
            player_x: Player center X
            player_y: Player center Y
            enemy_x: Enemy top-left X
            enemy_y: Enemy top-left Y
            player_size: Player size
            enemy_size: Enemy size
            
        Returns:
            True if collision detected
        """
        # Calculate collision distance as sum of radii
        enemy_center_x = enemy_x + ENEMY_SIZE_HALF
        enemy_center_y = enemy_y + ENEMY_SIZE_HALF
        
        dx = enemy_center_x - player_x
        dy = enemy_center_y - player_y
        dist_sq = dx * dx + dy * dy
        
        collision_dist_sq = (player_size // 2 + enemy_size // 2) ** 2
        
        return dist_sq < collision_dist_sq
    
    @staticmethod
    def check_projectile_enemy_collision(
        projectile_x: float, projectile_y: float,
        enemy_x: float, enemy_y: float,
        already_hit: Set[int],
        enemy_id: int,
        collision_distance: int = COLLISION_DISTANCE
    ) -> Tuple[bool, float, float]:
        """
        Check if projectile collides with an enemy.
        
        Args:
            projectile_x: Projectile center X
            projectile_y: Projectile center Y
            enemy_x: Enemy position X (top-left for rect, varies for other shapes)
            enemy_y: Enemy position Y
            already_hit: Set of enemy IDs already hit
            enemy_id: ID of the enemy
            collision_distance: Distance threshold for collision
            
        Returns:
            Tuple of (collision_detected, enemy_center_x, enemy_center_y)
        """
        # Don't hit same enemy twice
        if enemy_id in already_hit:
            return False, 0, 0
        
        # Calculate enemy center
        enemy_center_x = enemy_x + ENEMY_SIZE_HALF
        enemy_center_y = enemy_y + ENEMY_SIZE_HALF
        
        dx = enemy_center_x - projectile_x
        dy = enemy_center_y - projectile_y
        dist_sq = dx * dx + dy * dy
        
        collision_detected = dist_sq < COLLISION_DISTANCE_SQ
        
        return collision_detected, enemy_center_x, enemy_center_y
    
    @staticmethod
    def check_shard_enemy_collision(
        shard_x: float, shard_y: float,
        enemy_x: float, enemy_y: float,
        collision_distance: int = COLLISION_DISTANCE
    ) -> Tuple[bool, float, float]:
        """
        Check if a shard collides with an enemy.
        
        Args:
            shard_x: Shard center X
            shard_y: Shard center Y
            enemy_x: Enemy position X
            enemy_y: Enemy position Y
            collision_distance: Distance threshold for collision
            
        Returns:
            Tuple of (collision_detected, enemy_center_x, enemy_center_y)
        """
        enemy_center_x = enemy_x + ENEMY_SIZE_HALF
        enemy_center_y = enemy_y + ENEMY_SIZE_HALF
        
        dx = enemy_center_x - shard_x
        dy = enemy_center_y - shard_y
        dist_sq = dx * dx + dy * dy
        
        collision_detected = dist_sq < COLLISION_DISTANCE_SQ
        
        return collision_detected, enemy_center_x, enemy_center_y
    
    @staticmethod
    def find_closest_unhit_enemy(
        projectile_x: float, projectile_y: float,
        enemies: List[Any],
        already_hit: Set[int],
        max_distance: Optional[float] = None
    ) -> Optional[Any]:
        """
        Find the closest unhit enemy to the projectile.
        
        Args:
            projectile_x: Projectile center X
            projectile_y: Projectile center Y
            enemies: List of enemies to check
            already_hit: Set of enemy IDs already hit
            max_distance: Maximum distance to consider (None = unlimited)
            
        Returns:
            Closest enemy or None if no enemy found
        """
        closest = None
        closest_dist_sq = float('inf') if max_distance is None else (max_distance * max_distance)
        
        for enemy in enemies:
            enemy_id = id(enemy)
            if enemy_id in already_hit:
                continue
            
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx = ex_center - projectile_x
            dy = ey_center - projectile_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest = enemy
        
        return closest
    
    @staticmethod
    def get_distance_and_direction(
        from_x: float, from_y: float,
        to_x: float, to_y: float
    ) -> Tuple[float, float, float]:
        """
        Calculate distance and normalized direction vector between two points.
        
        Args:
            from_x: Starting point X
            from_y: Starting point Y
            to_x: Target point X
            to_y: Target point Y
            
        Returns:
            Tuple of (distance, direction_x, direction_y)
            Direction is normalized (length 1), or (0, 0) if distance is 0
        """
        dx = to_x - from_x
        dy = to_y - from_y
        dist = math.hypot(dx, dy)
        
        if dist == 0:
            return 0, 0, 0
        
        dir_x = dx / dist
        dir_y = dy / dist
        
        return dist, dir_x, dir_y
    
    @staticmethod
    def find_enemies_in_radius(
        center_x: float, center_y: float,
        radius: float,
        enemies: List[Any],
        exclude_ids: Optional[Set[int]] = None
    ) -> List[Tuple[Any, float]]:
        """
        Find all enemies within a radius of a center point.
        
        Args:
            center_x: Center point X
            center_y: Center point Y
            radius: Search radius
            enemies: List of enemies to check
            exclude_ids: Optional set of enemy IDs to exclude
            
        Returns:
            List of (enemy, distance) tuples sorted by distance (closest first)
        """
        if exclude_ids is None:
            exclude_ids = set()
        
        nearby = []
        radius_sq = radius * radius
        
        for enemy in enemies:
            enemy_id = id(enemy)
            if enemy_id in exclude_ids:
                continue
            
            ex, ey = enemy.get_position()
            ex_center = ex + ENEMY_SIZE_HALF
            ey_center = ey + ENEMY_SIZE_HALF
            
            dx = ex_center - center_x
            dy = ey_center - center_y
            dist_sq = dx * dx + dy * dy
            
            if dist_sq < radius_sq:
                dist = math.sqrt(dist_sq)
                nearby.append((enemy, dist))
        
        # Sort by distance
        nearby.sort(key=lambda x: x[1])
        return nearby


class PlayerCollisionHandler:
    """Handles player-specific collision logic."""
    
    @staticmethod
    def handle_player_enemy_collision(
        game: Any,
        enemy: Any,
        player: Any,
        shield_immunity: int
    ) -> bool:
        """
        Handle collision between player and enemy.
        
        Args:
            game: Game instance
            enemy: Enemy entity
            player: Player entity
            shield_immunity: Current shield immunity frames
            
        Returns:
            True if damage was taken, False if blocked by shield
        """
        if shield_immunity > 0:
            return False
        
        if player.shield_active and player.shield_rings:
            # Shield blocks the damage (only if there are rings)
            print(f"[ACTION] Shield blocked enemy hit! Rings remaining: {len(player.shield_rings)}")
            from audio import play_beep_async
            play_beep_async(1200, 50, game)  # Blip sound on shield hit
            player.deactivate_shield(enemy=enemy)
            enemy.shield_immunity = 10  # Prevent re-collision for 10 frames
            return False
        else:
            # No shield - deal damage to player
            print(f"[ACTION] Enemy hit player! Health: {player.health} -> {player.health - 1}")
            player.health -= 1
            if player.health <= 0:
                print(f"[ACTION] Player died!")
                return True
            return False
    
    @staticmethod
    def check_and_handle_collision(
        game: Any,
        player: Any,
        enemy: Any
    ) -> bool:
        """
        Check for and handle player-enemy collision in one call.
        
        Args:
            game: Game instance
            player: Player entity
            enemy: Enemy entity
            
        Returns:
            True if game over, False otherwise
        """
        px, py = player.get_center()
        ex, ey = enemy.get_position()
        
        # Check if collision occurred
        if not CollisionDetector.check_player_enemy_collision(px, py, ex, ey):
            return False
        
        # Decrease immunity timer
        if enemy.shield_immunity > 0:
            enemy.shield_immunity -= 1
        
        # Handle the collision
        game_over = PlayerCollisionHandler.handle_player_enemy_collision(
            game, enemy, player, enemy.shield_immunity
        )
        
        return game_over
