# Audio Behavior

Audio is optional and degrades gracefully if a backend is unavailable.

## Backends
## Backends
- Primary: `pygame.mixer` (recommended for cross-platform)
- Fallback: `winsound` on Windows (used when `pygame` is not available)
- If no supported backend is available: audio is disabled and the game logs an informative message
- If none available: audio disabled with informative logs
- Background music toggled via Settings; stopped on Game Over and during transitions.
- Title Screen `Quit` stops music before exiting.

## Configuration
- Dependencies managed in `requirements.txt`.
- Initialization handled in `audio.py` with safe try/except blocks.

## Testing
- Audio calls are stubbed or made asynchronous to avoid blocking tests.
- No hard dependency on audio for game logic or progression.
