# Testing Guide

Headless tests validate gameplay without a GUI.

## Running
```sh
source .venv/bin/activate
pytest -q
```

## Headless Canvas
- `tests/helpers/mock_canvas.py` implements minimal Tk canvas API:
  - `create_text`, `create_oval`, `create_polygon`, `create_rectangle`, `create_line`
  - `itemconfig`, `coords`, `delete`, `bind`, `after`, `winfo_*`
- Enables entity and weapon-effect rendering logic to run in tests.

## Suite Coverage
- `test_game.py`: core loop and interactions
- `test_weapon_system_pytest.py`: cooldown gating, firing
- `test_weapon_stats*`: upgrades and linked prerequisites
- `test_progression*`: waves, rest, boss
- `test_entity_lifecycle_pytest.py`: BaseEntity lifecycle
- `test_weapon_effects_pytest.py`: chain lightning visuals, black hole spawn

## CI (optional)
- GitHub Actions can run `pytest` across macOS/Linux/Windows with Python 3.12.
- Add a matrix workflow to ensure cross-OS stability.
