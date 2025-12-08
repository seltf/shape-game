import pytest
from tests.helpers.mock_canvas import MockCanvas
from top_down_game import Game


def test_weapon_cooldown_blocks_fire_until_zero():
    canvas = MockCanvas()
    game = Game(root=None, canvas=canvas)
    game.show_main_menu()  # ensure menus initialized
    # Start playing state
    game.start_game_from_menu()
    # Initially can fire
    assert game.weapon.can_fire()
    fired = game.attack()  # uses weapon cooldown
    assert fired is None  # attack returns None but sets cooldown
    assert not game.weapon.can_fire()
    # Tick logic enough to clear cooldown (WEAPON_COOLDOWN_MS defaults to 200)
    for _ in range(10):
        game.weapon.tick(20)
    assert game.weapon.can_fire()


def test_weapon_fire_spawns_projectile():
    canvas = MockCanvas()
    game = Game(root=None, canvas=canvas)
    game.start_game_from_menu()
    # Ensure no main projectile
    assert not any(p for p in game.projectiles if not getattr(p, 'is_mini_fork', False))
    game.attack()
    assert any(p for p in game.projectiles if not getattr(p, 'is_mini_fork', False))
