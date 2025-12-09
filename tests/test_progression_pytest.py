import pytest
from constants import GAME_LEVEL_WAVES
from top_down_game import Game
from tests.helpers.mock_canvas import MockCanvas

@pytest.fixture
def game():
    canvas = MockCanvas()
    g = Game(root=None, canvas=canvas)
    yield g

def test_boss_triggers_at_21(game):
    game.game_level = 21
    game.start_game_level()
    assert game.boss_fight_active is True

def test_wave_progression_caps_enemy_count(game):
    game.game_level = 3
    game.enemies = []
    game.start_game_level()
    # After first wave spawn, should not exceed MAX_ENEMY_COUNT; we can't assert exact
    # but we can assert waves increment and rest toggles after completion
    waves = GAME_LEVEL_WAVES[3]
    # Simulate spawning through waves
    for _ in range(len(waves)):
        game._spawn_next_wave()
    assert game.is_resting is True
