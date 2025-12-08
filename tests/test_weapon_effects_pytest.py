import pytest
from tests.helpers.mock_canvas import MockCanvas
from constants import ENEMY_SIZE_HALF, ENEMY_SIZE
from top_down_game import Game
from entities import TriangleEnemy


def setup_game():
    canvas = MockCanvas()
    game = Game(canvas=canvas)
    # Ensure chain lightning level
    game.computed_weapon_stats['chain_lightning'] = 2
    return game, canvas


def test_chain_lightning_strikes_targets():
    game, canvas = setup_game()
    # Spawn a few enemies
    enemies = []
    for i in range(3):
        e = TriangleEnemy(canvas, 100 + i*40, 100, ENEMY_SIZE)
        enemies.append(e)
        game.enemies.append(e)
    origin = enemies[0]
    ox, oy = origin.get_position()
    center = (ox + ENEMY_SIZE_HALF, oy + ENEMY_SIZE_HALF)
    # Trigger chain
    game.weapon.handle_chain_lightning(origin, center)
    # At least one enemy should be struck or removed depending on health
    # We can assert that canvas created some line items as a proxy for visuals
    line_items = [item for item in canvas.items.values() if item['type'] == 'line']
    assert len(line_items) >= 1


def test_black_hole_spawns_with_chance(monkeypatch):
    game, canvas = setup_game()
    game.computed_weapon_stats['black_hole'] = 1
    # Force random to trigger
    monkeypatch.setattr('random.random', lambda: 0.0)
    game.weapon.try_spawn_black_hole(200, 200)
    assert len(game.black_holes) == 1
