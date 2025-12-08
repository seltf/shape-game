import pytest
from tests.helpers.mock_canvas import MockCanvas
from entities import TriangleEnemy, PentagonEnemy


def test_triangle_enemy_lifecycle():
    canvas = MockCanvas()
    tri = TriangleEnemy(canvas, x=100, y=100, size=20)
    assert tri.alive is True
    # Triangle has 2 health; two hits should kill
    assert tri.take_damage() is True  # health -> 1, alive True
    assert tri.alive is True
    assert tri.take_damage() is False  # health -> 0, alive False
    assert tri.alive is False
    # Cleanup should remove polygon from canvas
    item_id = tri.rect
    assert item_id in canvas.items
    tri.cleanup()
    assert item_id not in canvas.items
    assert tri.alive is False


def test_pentagon_enemy_lifecycle():
    canvas = MockCanvas()
    penta = PentagonEnemy(canvas, x=150, y=150, size=30)
    assert penta.alive is True
    # Pentagon has 5 health; five hits should kill
    for i in range(4):
        assert penta.take_damage() is True
        assert penta.alive is True
    # Fifth hit kills
    assert penta.take_damage() is False
    assert penta.alive is False
    # Cleanup should remove polygon from canvas
    item_id = penta.rect
    assert item_id in canvas.items
    penta.cleanup()
    assert item_id not in canvas.items
    assert penta.alive is False
