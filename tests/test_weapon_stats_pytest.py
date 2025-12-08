import pytest
from top_down_game import Game
from constants import WEAPON_STATS
from tests.helpers.mock_canvas import MockCanvas

@pytest.fixture
def game():
    canvas = MockCanvas()
    g = Game(root=None, canvas=canvas)
    g.active_upgrades = []
    g.computed_weapon_stats = g.compute_weapon_stats()
    yield g

def test_base_stats(game):
    stats = game.compute_weapon_stats()
    for k, v in WEAPON_STATS.items():
        assert stats[k] == v

def test_rapid_fire_and_bounce_stack(game):
    assert game.add_upgrade('rapid_fire')
    assert game.add_upgrade('extra_bounce')
    stats = game.computed_weapon_stats
    assert stats['projectile_speed'] > WEAPON_STATS['projectile_speed']
    assert stats['return_speed'] > WEAPON_STATS['return_speed']
    assert stats.get('bounces', 0) >= 1

def test_linked_upgrade_requires(game):
    # chain_lightning requires extra_bounce
    assert not game.add_upgrade('chain_lightning')
    assert game.add_upgrade('extra_bounce')
    assert game.add_upgrade('chain_lightning')
