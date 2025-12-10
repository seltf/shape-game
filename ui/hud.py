"""
HUD: Heads-up display management for score, level, xp, timer, perf text.
"""
import tkinter as tk
from typing import Optional
from ui import fonts

class HUD:
    def __init__(self, canvas: tk.Canvas, window_width: int, window_height: int, version: str):
        self.canvas = canvas
        self.version_text = self.canvas.create_text(10, window_height - 10, anchor='sw', fill='gray', font=fonts.FONT_10, text=f"v{version}")
        self.score_text = self.canvas.create_text(window_width//2, 30, anchor='n', fill='yellow', font=fonts.FONT_24, text="0")
        self.level_text = self.canvas.create_text(window_width//2, 70, anchor='n', fill='cyan', font=fonts.FONT_20, text="Level: 0")
        self.xp_text = self.canvas.create_text(window_width//2, 100, anchor='n', fill='green', font=fonts.FONT_16, text="XP: 0/10")
        self.game_level_text = self.canvas.create_text(window_width//2, 130, anchor='n', fill='orange', font=fonts.FONT_16, text="Game Level: 1")
        self.timer_text = self.canvas.create_text(window_width - 80, 30, anchor='n', fill='white', font=fonts.FONT_16, text="Time: 0:00")
        self.perf_text: Optional[int] = None

    def set_score(self, score: int):
        self.canvas.itemconfig(self.score_text, text=str(score))

    def set_player_level(self, level: int):
        self.canvas.itemconfig(self.level_text, text=f"Level: {level}")

    def set_xp(self, xp: int, next_level: int):
        self.canvas.itemconfig(self.xp_text, text=f"XP: {xp}/{next_level}")

    def set_game_level(self, game_level: int):
        self.canvas.itemconfig(self.game_level_text, text=f"Game Level: {game_level}")

    def set_time(self, time_str: str):
        self.canvas.itemconfig(self.timer_text, text=f"Time: {time_str}")

    def setup_perf(self):
        if self.perf_text is None:
            self.perf_text = self.canvas.create_text(
                10, 30, anchor='nw', fill='lime', font=fonts.MONO_10, text="FPS: 0"
            )
        return self.perf_text

    def rescale(self, game: Any) -> None:
        """Reposition HUD elements based on current window dimensions (screen-space, not world-space)."""
        try:
            w = game.window_width
            h = game.window_height
            # version in bottom-left
            try:
                self.canvas.coords(self.version_text, 10, h - 10)
            except Exception:
                pass
            # center-top items
            try:
                self.canvas.coords(self.score_text, w // 2, 30)
                self.canvas.coords(self.level_text, w // 2, 70)
                self.canvas.coords(self.xp_text, w // 2, 100)
                self.canvas.coords(self.game_level_text, w // 2, 130)
            except Exception:
                pass
            # timer on top-right
            try:
                self.canvas.coords(self.timer_text, w - 80, 30)
            except Exception:
                pass
            # perf text (if exists) keep top-left
            try:
                if self.perf_text is not None:
                    self.canvas.coords(self.perf_text, 10, 30)
            except Exception:
                pass
        except Exception:
            pass

    def set_perf(self, text: str):
        if self.perf_text:
            self.canvas.itemconfig(self.perf_text, text=text)
