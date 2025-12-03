# Custom Audio Setup Guide

This game supports custom sound effects using playsound, a simple zero-dependency audio library. If playsound is not installed, the game will fallback to system beeps.

## Installation

To enable custom audio support, install playsound:

```bash
pip install playsound
```

That's it! No additional dependencies needed.

## Adding Custom Sounds

1. Create a `sounds` folder in the game directory (same level as `top_down_game.py`)
2. Add your audio files as WAV files to this folder
3. Update the `SOUND_EFFECTS` dictionary in `top_down_game.py` to map sound names to file paths

### Example Sound Files

Place these files in the `sounds/` directory:

- `black_hole_detonate.wav` - Plays when a black hole detonates
- `projectile_hit.wav` - Plays when a projectile hits an enemy
- `enemy_death.wav` - Plays when an enemy dies
- `powerup.wav` - Plays when picking up a powerup

## Sound Effects Dictionary

Edit the `SOUND_EFFECTS` dictionary in the code to add or modify sounds:

```python
SOUND_EFFECTS = {
    'black_hole_detonate': 'sounds/black_hole_detonate.wav',
    'projectile_hit': 'sounds/projectile_hit.wav',
    'enemy_death': 'sounds/enemy_death.wav',
    'powerup': 'sounds/powerup.wav',
}
```

## Using Custom Sounds

In the code, use `play_sound_async()` with a sound name:

```python
play_sound_async('black_hole_detonate', game_instance=self.game)
```

Or with a beep fallback:

```python
play_sound_async('projectile_hit', frequency=400, duration=30, game_instance=self.game)
```

## Audio Format Support

Playsound supports:
- **WAV files** (recommended)
- **MP3 files** (Windows)
- Other formats depending on your OS

## Fallback Behavior

If a custom sound file is not found or playsound is not installed:
1. The code will fallback to generating a beep with the specified frequency and duration
2. If no frequency/duration is provided, no sound will play
3. The game will continue normally - audio issues won't crash the game

## Disabling Audio

Audio can be toggled in-game through the pause menu, or disabled by setting `sound_enabled = False` in the game initialization.

## Troubleshooting

- If sounds don't play, verify playsound is installed: `pip list | grep playsound`
- Check that sound files exist in the `sounds/` directory
- Ensure file paths in `SOUND_EFFECTS` are correct
- WAV files work best with playsound
- Check Windows Volume Mixer to ensure the application isn't muted

## Quick Start

1. ✓ Already installed! (playsound)
2. Create `sounds/` folder in your game directory
3. Add your WAV files from your friend to `sounds/`
4. Update `SOUND_EFFECTS` dict with your file names
5. The game will automatically play them!


