"""
InputSystem: centralizes key mapping and normalized input state.
"""
from dataclasses import dataclass
from typing import Set, Dict

@dataclass
class InputState:
    move_up: bool = False
    move_down: bool = False
    move_left: bool = False
    move_right: bool = False
    fire: bool = False
    pause: bool = False
    auto_fire_toggle: bool = False

class InputSystem:
    def __init__(self, keysym_map: Dict[str, str]):
        self.keysym_map = keysym_map
        self.pressed_keys: Set[str] = set()
        self.state = InputState()

    def map_key(self, keysym: str) -> str:
        return self.keysym_map.get(keysym, '')

    def on_press(self, keysym: str):
        self.pressed_keys.add(keysym)
        action = self.map_key(keysym)
        if action == 'up':
            self.state.move_up = True
        elif action == 'down':
            self.state.move_down = True
        elif action == 'left':
            self.state.move_left = True
        elif action == 'right':
            self.state.move_right = True
        elif keysym in ('space', 'Space'):
            self.state.auto_fire_toggle = True
        elif keysym in ('Escape', 'esc', 'ESC'):
            self.state.pause = True
        elif keysym in ('Button-1', 'Click'):
            self.state.fire = True

    def on_release(self, keysym: str):
        if keysym in self.pressed_keys:
            self.pressed_keys.remove(keysym)
        action = self.map_key(keysym)
        if action == 'up':
            self.state.move_up = False
        elif action == 'down':
            self.state.move_down = False
        elif action == 'left':
            self.state.move_left = False
        elif action == 'right':
            self.state.move_right = False
        elif keysym in ('space', 'Space'):
            self.state.auto_fire_toggle = False
        elif keysym in ('Escape', 'esc', 'ESC'):
            self.state.pause = False
        elif keysym in ('Button-1', 'Click'):
            self.state.fire = False

    def clear(self):
        self.pressed_keys.clear()
        self.state = InputState()
