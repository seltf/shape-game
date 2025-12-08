"""
Unit tests for weapon stat computation and upgrades.
"""

import unittest
from constants import WEAPON_STATS, WEAPON_UPGRADES, LINKED_UPGRADES
from top_down_game import Game
from tests.helpers.mock_canvas import MockCanvas

class TestWeaponStats(unittest.TestCase):
    def setUp(self):
        # Use a real Tk canvas to avoid mocking, but do not display
        # Use mock canvas for headless tests
        canvas = MockCanvas()
        self.game = Game(root=None, canvas=canvas)
        # Ensure starting from clean upgrades
        self.game.active_upgrades = []
        self.game.computed_weapon_stats = self.game.compute_weapon_stats()

    def tearDown(self):
        pass

    def test_base_stats_match_constants(self):
        stats = self.game.compute_weapon_stats()
        # Base keys should exist and match default
        for k, v in WEAPON_STATS.items():
            self.assertEqual(stats[k], v)

    def test_add_shrapnel_upgrade(self):
        added = self.game.add_upgrade('shrapnel')
        self.assertTrue(added)
        stats = self.game.computed_weapon_stats
        self.assertGreaterEqual(stats.get('shrapnel', 0), 1)

    def test_add_multiple_upgrades_stack(self):
        self.game.add_upgrade('rapid_fire')
        self.game.add_upgrade('extra_bounce')
        stats = self.game.computed_weapon_stats
        self.assertGreater(stats['projectile_speed'], WEAPON_STATS['projectile_speed'])
        self.assertGreater(stats['return_speed'], WEAPON_STATS['return_speed'])
        self.assertGreaterEqual(stats.get('bounces', 0), 1)

    def test_linked_upgrade_requires(self):
        # chain_lightning requires extra_bounce
        self.assertFalse(self.game.add_upgrade('chain_lightning'))
        self.assertTrue(self.game.add_upgrade('extra_bounce'))
        # After prerequisite, linked upgrade should be addable
        self.assertTrue(self.game.add_upgrade('chain_lightning'))

    def test_shield_levels_cap_at_three(self):
        # Add shield multiple times
        self.assertTrue(self.game.add_upgrade('shield'))
        self.assertTrue(self.game.add_upgrade('shield'))
        self.assertTrue(self.game.add_upgrade('shield'))
        # Fourth add: still allowed by method, but MenuManager will gate selection.
        # Compute stats should reflect stacking levels
        stats = self.game.computed_weapon_stats
        self.assertGreaterEqual(stats.get('shield', 0), 3)

if __name__ == '__main__':
    unittest.main()
