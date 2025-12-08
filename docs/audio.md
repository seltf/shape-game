# Audio Behavior

Audio is optional and degrades gracefully if a backend is unavailable.

## Backends
- Primary: `pygame.mixer` (recommended for cross-platform)
- Fallback: platform-specific alternatives if present
- If none available: audio disabled with informative logs

## Effects
- Short beep on enemy kill (non-blocking)
- Future: background music and richer SFX

## Configuration
- Dependencies managed in `requirements.txt`.
- Initialization handled in `audio.py` with safe try/except blocks.

## Testing
- Audio calls are stubbed or made asynchronous to avoid blocking tests.
- No hard dependency on audio for game logic or progression.
