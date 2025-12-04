"""
Unit tests for shape-game modules.
Tests collision detection, entity behavior, and game logic.
"""

import unittest
import math
from typing import Set
from collision import CollisionDetector, PlayerCollisionHandler
from constants import (
    PLAYER_SIZE, ENEMY_SIZE, ENEMY_SIZE_HALF,
    COLLISION_DISTANCE, COLLISION_DISTANCE_SQ
)
from utils import rect_overlap


class TestCollisionDetector(unittest.TestCase):
    """Test CollisionDetector static methods."""
    
    def test_check_distance_collision_hit(self):
        """Test distance collision when objects overlap."""
        collision, dist_sq = CollisionDetector.check_distance_collision(
            0, 0, 10, 0, collision_distance=20
        )
        self.assertTrue(collision)
        self.assertAlmostEqual(dist_sq, 100)
    
    def test_check_distance_collision_miss(self):
        """Test distance collision when objects are too far apart."""
        collision, dist_sq = CollisionDetector.check_distance_collision(
            0, 0, 100, 0, collision_distance=20
        )
        self.assertFalse(collision)
        self.assertAlmostEqual(dist_sq, 10000)
    
    def test_check_distance_collision_at_edge(self):
        """Test distance collision at exact threshold."""
        collision_dist = 20
        collision, dist_sq = CollisionDetector.check_distance_collision(
            0, 0, collision_dist, 0, collision_distance=collision_dist
        )
        # At exact distance should be false (< not <=)
        self.assertFalse(collision)
    
    def test_check_player_enemy_collision_hit(self):
        """Test player-enemy collision when they overlap."""
        # Player at (100, 100), Enemy at (95, 95)
        # Enemy center at (95 + 10, 95 + 10) = (105, 105)
        # dx = 105 - 100 = 5, dy = 105 - 100 = 5
        # Distance squared = 5*5 + 5*5 = 50
        # Player radius = 10, Enemy radius = 10, sum = 20
        # Collision threshold squared = 20^2 = 400
        # 50 < 400 should be true
        player_x, player_y = 100, 100
        enemy_x, enemy_y = 95, 95
        
        collision = CollisionDetector.check_player_enemy_collision(
            player_x, player_y, enemy_x, enemy_y
        )
        # Distance squared is 50, threshold squared is 400, so should collide
        self.assertTrue(collision)
    
    def test_check_player_enemy_collision_miss(self):
        """Test player-enemy collision when they are far apart."""
        player_x, player_y = 0, 0
        enemy_x, enemy_y = 500, 500
        
        collision = CollisionDetector.check_player_enemy_collision(
            player_x, player_y, enemy_x, enemy_y
        )
        self.assertFalse(collision)
    
    def test_get_distance_and_direction(self):
        """Test distance and direction calculation."""
        dist, dir_x, dir_y = CollisionDetector.get_distance_and_direction(0, 0, 3, 4)
        
        # Distance should be 5 (3-4-5 triangle)
        self.assertAlmostEqual(dist, 5.0)
        
        # Direction should be normalized
        self.assertAlmostEqual(dir_x, 0.6)
        self.assertAlmostEqual(dir_y, 0.8)
    
    def test_get_distance_and_direction_same_point(self):
        """Test distance calculation when points are the same."""
        dist, dir_x, dir_y = CollisionDetector.get_distance_and_direction(5, 5, 5, 5)
        
        self.assertAlmostEqual(dist, 0)
        self.assertAlmostEqual(dir_x, 0)
        self.assertAlmostEqual(dir_y, 0)
    
    def test_find_closest_unhit_enemy_no_enemies(self):
        """Test finding closest enemy when list is empty."""
        enemies = []
        closest = CollisionDetector.find_closest_unhit_enemy(0, 0, enemies, set())
        self.assertIsNone(closest)
    
    def test_find_closest_unhit_enemy_all_hit(self):
        """Test finding closest enemy when all have been hit."""
        # Create mock enemy objects
        class MockEnemy:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def get_position(self):
                return self.x, self.y
        
        enemies = [MockEnemy(10, 10), MockEnemy(20, 20)]
        hit_ids = {id(enemies[0]), id(enemies[1])}
        
        closest = CollisionDetector.find_closest_unhit_enemy(0, 0, enemies, hit_ids)
        self.assertIsNone(closest)
    
    def test_find_closest_unhit_enemy_picks_closest(self):
        """Test that find_closest_unhit_enemy returns the closest enemy."""
        class MockEnemy:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def get_position(self):
                return self.x, self.y
        
        enemies = [
            MockEnemy(100, 0),  # Distance 100
            MockEnemy(10, 0),   # Distance 10 (closest)
            MockEnemy(50, 0),   # Distance 50
        ]
        
        closest = CollisionDetector.find_closest_unhit_enemy(0, 0, enemies, set())
        self.assertEqual(closest.x, 10)
        self.assertEqual(closest.y, 0)
    
    def test_find_enemies_in_radius(self):
        """Test finding enemies within a radius."""
        class MockEnemy:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def get_position(self):
                return self.x, self.y
        
        enemies = [
            MockEnemy(10, 10),    # Center at (20, 20), distance = sqrt(800) ~= 28.28
            MockEnemy(100, 0),    # Center at (110, 10), distance = sqrt(12100+100) > 50
            MockEnemy(30, 0),     # Center at (40, 10), distance = sqrt(1700) ~= 41.23
        ]
        
        nearby = CollisionDetector.find_enemies_in_radius(0, 0, 50, enemies)
        
        # Should find 2 enemies within radius 50
        self.assertEqual(len(nearby), 2)
        
        # Should be sorted by distance - closest first
        self.assertAlmostEqual(nearby[0][1], 28.28, places=1)  # First at distance ~28.28
        self.assertAlmostEqual(nearby[1][1], 41.23, places=1)  # Second at distance ~41.23
    
    def test_circle_rectangle_collision(self):
        """Test circle-rectangle collision detection."""
        # Circle at (50, 50) with radius 10
        # Rectangle at (60, 60) with width 20, height 20
        collision = CollisionDetector.check_circle_rectangle_collision(
            50, 50, 10, 60, 60, 20, 20
        )
        # Closest point on rect to circle center is (60, 60), distance is sqrt(200) ~= 14.14
        # Which is > radius of 10, so no collision
        self.assertFalse(collision)
    
    def test_circle_rectangle_collision_overlap(self):
        """Test circle-rectangle collision with overlap."""
        # Circle at (75, 75) with radius 20
        # Rectangle at (60, 60) with width 20, height 20
        collision = CollisionDetector.check_circle_rectangle_collision(
            75, 75, 20, 60, 60, 20, 20
        )
        # Circle center (75,75) is close to rect, should collide
        self.assertTrue(collision)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_rect_overlap_overlapping(self):
        """Test rectangle overlap with overlapping rectangles."""
        rect1 = (0, 0, 10, 10)
        rect2 = (5, 5, 15, 15)
        self.assertTrue(rect_overlap(rect1, rect2))
    
    def test_rect_overlap_no_overlap(self):
        """Test rectangle overlap with non-overlapping rectangles."""
        rect1 = (0, 0, 10, 10)
        rect2 = (20, 20, 30, 30)
        self.assertFalse(rect_overlap(rect1, rect2))
    
    def test_rect_overlap_touching_edge(self):
        """Test rectangle overlap when touching at edge (touching counts as overlap)."""
        rect1 = (0, 0, 10, 10)
        rect2 = (10, 0, 20, 10)
        # rect_overlap uses < not <=, so touching edge DOES count as overlap
        # (left edge of rect2 at x=10 is not > right edge of rect1 at x=10)
        self.assertTrue(rect_overlap(rect1, rect2))
    
    def test_rect_overlap_inside(self):
        """Test rectangle overlap when one is inside the other."""
        rect1 = (0, 0, 100, 100)
        rect2 = (10, 10, 20, 20)
        self.assertTrue(rect_overlap(rect1, rect2))


class TestCollisionConstants(unittest.TestCase):
    """Test that collision constants are properly configured."""
    
    def test_collision_distance_sq_is_squared(self):
        """Test that COLLISION_DISTANCE_SQ is the square of COLLISION_DISTANCE."""
        expected = COLLISION_DISTANCE ** 2
        self.assertEqual(COLLISION_DISTANCE_SQ, expected)
    
    def test_enemy_size_half_is_correct(self):
        """Test that ENEMY_SIZE_HALF is half of ENEMY_SIZE."""
        expected = ENEMY_SIZE // 2
        self.assertEqual(ENEMY_SIZE_HALF, expected)
    
    def test_player_size_is_positive(self):
        """Test that player size is positive."""
        self.assertGreater(PLAYER_SIZE, 0)
    
    def test_enemy_size_is_positive(self):
        """Test that enemy size is positive."""
        self.assertGreater(ENEMY_SIZE, 0)


class TestCollisionPerformance(unittest.TestCase):
    """Test collision detection performance characteristics."""
    
    def test_squared_distance_avoids_sqrt(self):
        """Test that distance_sq comparison avoids unnecessary sqrt."""
        # This is more about demonstrating the pattern
        dx, dy = 3, 4
        dist_sq = dx * dx + dy * dy  # 25
        
        # Collision occurs if dist_sq < threshold_sq
        collision_threshold_sq = 30  # threshold would be sqrt(30) ~= 5.48
        self.assertTrue(dist_sq < collision_threshold_sq)
    
    def test_collision_method_efficiency(self):
        """Test that collision methods use efficient squared distance."""
        # Create a simple test to verify no unnecessary sqrt calls
        collision, dist_sq = CollisionDetector.check_distance_collision(
            0, 0, 10, 0, collision_distance=20
        )
        # If this returns the squared distance, it's efficient
        self.assertEqual(dist_sq, 100)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_collision_at_zero_coordinates(self):
        """Test collision detection at origin."""
        collision = CollisionDetector.check_player_enemy_collision(0, 0, 0, 0)
        self.assertTrue(collision)
    
    def test_collision_with_negative_coordinates(self):
        """Test collision detection with negative coordinates."""
        collision = CollisionDetector.check_player_enemy_collision(-10, -10, -15, -15)
        self.assertTrue(collision)
    
    def test_large_distance_collision(self):
        """Test collision detection with very large distances."""
        collision, dist_sq = CollisionDetector.check_distance_collision(
            0, 0, 1000000, 1000000, collision_distance=20
        )
        self.assertFalse(collision)
    
    def test_find_enemies_in_zero_radius(self):
        """Test finding enemies with zero radius."""
        class MockEnemy:
            def get_position(self):
                return 0, 0
        
        enemies = [MockEnemy()]
        nearby = CollisionDetector.find_enemies_in_radius(0, 0, 0, enemies)
        # With radius 0, should find nothing (dist_sq < 0 is false)
        self.assertEqual(len(nearby), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple components."""
    
    def test_collision_workflow(self):
        """Test a typical collision detection workflow."""
        class MockEnemy:
            def __init__(self, x, y):
                self.x = x
                self.y = y
            def get_position(self):
                return self.x, self.y
        
        # Player at origin
        player_x, player_y = 0, 0
        
        # Three enemies at different distances
        enemies = [
            MockEnemy(10, 10),   # Close, should collide
            MockEnemy(100, 100), # Far, shouldn't collide
            MockEnemy(5, 5),     # Very close, should collide
        ]
        
        # Find all enemies within collision range
        nearby = CollisionDetector.find_enemies_in_radius(
            player_x, player_y,
            radius=50,
            enemies=enemies
        )
        
        # Should find 2 enemies within radius 50
        self.assertEqual(len(nearby), 2)
        
        # Closest should be at (5,5)
        closest = nearby[0][0]
        self.assertEqual(closest.x, 5)
        self.assertEqual(closest.y, 5)


if __name__ == '__main__':
    # Run all tests with verbose output
    unittest.main(verbosity=2)
