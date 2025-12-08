import pytest
from top_down_game import Game
from tests.helpers.mock_canvas import MockCanvas

@pytest.fixture
def game():
    canvas = MockCanvas()
    g = Game(root=None, canvas=canvas)
    yield g

def test_rest_only_counts_down_when_no_enemies(game):
    game.is_resting = True
    game.level_rest_timer = 40
    # With enemies present, timer should not change
    game.enemies = [object()]
    game.progression.tick()
    assert game.level_rest_timer == 40
    # Remove enemies; timer should count down and advance level
    game.enemies = []
    game.progression.tick()
    assert game.level_rest_timer == 20
    game.progression.tick()
    assert game.is_resting is False
    assert game.game_level >= 2

def test_wave_timer_spawns_on_expiry(game):
    game.game_level = 3
    game.start_game_level()
    # Force next wave immediately
    game.wave_timer = 0
    prev_wave = game.current_wave
    game.progression.tick()
    assert game.current_wave == prev_wave + 1
