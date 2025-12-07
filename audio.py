"""
Audio management system for Top Down Game
Handles sound effects, beeps, and background music playback
"""

import threading
import os
import sys
import time
from typing import Dict, Optional
from constants import SOUND_COOLDOWN_MS

# Try to import pygame for cross-platform audio support
try:
    import pygame
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    AUDIO_BACKEND: str = 'pygame'
    AUDIO_AVAILABLE: bool = True
    print("[AUDIO] Using pygame.mixer for audio playback")
except ImportError:
    # Fallback to winsound on Windows only
    try:
        import winsound
        AUDIO_BACKEND: str = 'winsound'
        AUDIO_AVAILABLE: bool = True
        print("[AUDIO] Using winsound for audio playback (Windows only)")
    except ImportError:
        AUDIO_BACKEND: str = None
        AUDIO_AVAILABLE: bool = False
        print("[AUDIO] No audio backend available - audio features will be disabled")


# Determine the base directory for resources (handles both dev and bundled exe)
if getattr(sys, 'frozen', False):
    BASE_DIR: str = sys._MEIPASS
else:
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))

# Sound effects dictionary - maps sound names to file paths
SOUND_EFFECTS: Dict[str, str] = {
    'black_hole_detonate': os.path.join(BASE_DIR, 'sounds/black_hole_detonate.wav'),
    'projectile_hit': os.path.join(BASE_DIR, 'sounds/projectile_hit.wav'),
    'enemy_death': os.path.join(BASE_DIR, 'sounds/enemy_death.wav'),
    'powerup': os.path.join(BASE_DIR, 'sounds/powerup.wav'),
}

# Background music file
BACKGROUND_MUSIC: str = os.path.join(BASE_DIR, 'sounds/bit track space.wav')


class AudioManager:
    """Manages all audio playback including effects, beeps, and background music."""
    
    def __init__(self) -> None:
        """Initialize audio manager with throttling and state tracking."""
        self._last_sound_time: Dict[str, float] = {}  # Track when each sound was last played
        self._music_thread: Optional[threading.Thread] = None
        self._music_stop_event: Optional[threading.Event] = None
        self.sound_enabled: bool = True  # Sound effects enabled by default
        self.music_enabled: bool = False  # Background music disabled by default
    
    def _generate_beep_pygame(self, frequency: int, duration_ms: int) -> None:
        """Generate a simple beep tone using pygame.sndarray."""
        if AUDIO_BACKEND != 'pygame':
            return
        
        try:
            import numpy as np
            sample_rate = 22050
            duration_sec = duration_ms / 1000.0
            num_samples = int(sample_rate * duration_sec)
            
            # Generate sine wave
            t = np.linspace(0, duration_sec, num_samples, False)
            wave = np.sin(frequency * 2 * np.pi * t)
            
            # Apply envelope to avoid clicks
            envelope = np.ones_like(wave)
            fade_samples = min(100, num_samples // 10)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            wave = wave * envelope
            
            # Convert to 16-bit PCM
            wave = (wave * 32767).astype(np.int16)
            
            # Create stereo sound (duplicate mono to both channels)
            stereo_wave = np.column_stack((wave, wave))
            
            # Create and play sound
            sound = pygame.sndarray.make_sound(stereo_wave)
            sound.play()
        except ImportError:
            # If numpy not available, skip beep generation
            print("[AUDIO] numpy not available for beep generation")
        except Exception as e:
            print(f"[AUDIO] Failed to generate beep: {e}")
    
    def play_sound_async(self, sound_name: str, frequency: Optional[int] = None, 
                        duration: Optional[int] = None) -> None:
        """
        Play a sound asynchronously. Can use custom sound file or fallback to beep.
        
        Args:
            sound_name: Name of the sound effect from SOUND_EFFECTS
            frequency: Frequency for beep fallback (Hz)
            duration: Duration for beep fallback (ms)
        """
        if not self.sound_enabled:
            return
        
        # Throttle sound effects to prevent overlapping/crunchy audio
        current_time = time.time() * 1000  # Convert to milliseconds
        if sound_name in self._last_sound_time:
            time_since_last = current_time - self._last_sound_time[sound_name]
            if time_since_last < SOUND_COOLDOWN_MS:
                print(f"[SOUND] SKIPPED sound effect: {sound_name} (too soon, {time_since_last:.0f}ms since last)")
                return  # Skip this sound, too soon after last one
        
        self._last_sound_time[sound_name] = current_time
        print(f"[SOUND] Playing sound effect: {sound_name} (freq={frequency}, dur={duration}ms)")
        
        def play():
            # Try to load custom sound file
            if AUDIO_AVAILABLE and sound_name in SOUND_EFFECTS:
                sound_path = SOUND_EFFECTS[sound_name]
                if os.path.exists(sound_path):
                    try:
                        print(f"  -> Playing file: {sound_path}")
                        if AUDIO_BACKEND == 'pygame':
                            sound = pygame.mixer.Sound(sound_path)
                            sound.play()
                            return
                        elif AUDIO_BACKEND == 'winsound':
                            import winsound
                            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                            return
                    except Exception as e:
                        print(f"  -> Failed to play file {sound_path}: {e}")
                        # Fall through to beep fallback
            
            # Fallback to beep if custom sound unavailable or couldn't be loaded
            if AUDIO_AVAILABLE and frequency is not None and duration is not None:
                try:
                    print(f"  -> Playing beep fallback: {frequency}Hz for {duration}ms")
                    if AUDIO_BACKEND == 'pygame':
                        # Generate a simple beep tone using pygame
                        self._generate_beep_pygame(frequency, duration)
                    elif AUDIO_BACKEND == 'winsound':
                        import winsound
                        winsound.Beep(frequency, duration)
                except Exception as e:
                    print(f"  -> Failed to play beep: {e}")
        
        thread = threading.Thread(target=play, daemon=True)
        thread.start()
    
    def play_beep_async(self, frequency: int, duration: int) -> None:
        """
        Play a beep asynchronously in a background thread.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        if not self.sound_enabled or not AUDIO_AVAILABLE:
            return
        
        # Throttle beeps by frequency to prevent overlapping
        beep_key = f"beep_{frequency}"
        current_time = time.time() * 1000
        if beep_key in self._last_sound_time:
            time_since_last = current_time - self._last_sound_time[beep_key]
            if time_since_last < SOUND_COOLDOWN_MS:
                print(f"[SOUND] SKIPPED beep: {frequency}Hz (too soon, {time_since_last:.0f}ms since last)")
                return  # Skip this beep, too soon after last one
        
        self._last_sound_time[beep_key] = current_time
        print(f"[SOUND] Playing beep: {frequency}Hz for {duration}ms")
        
        def beep():
            try:
                if AUDIO_BACKEND == 'pygame':
                    self._generate_beep_pygame(frequency, duration)
                elif AUDIO_BACKEND == 'winsound':
                    import winsound
                    winsound.Beep(frequency, duration)
            except Exception as e:
                print(f"[SOUND] Failed to play beep: {e}")
        
        thread = threading.Thread(target=beep, daemon=True)
        thread.start()
    
    def start_background_music(self) -> None:
        """Start looping background music."""
        # Check if sound and music are enabled
        if not self.sound_enabled or not self.music_enabled or not AUDIO_AVAILABLE:
            return
        
        # Stop any existing music
        self.stop_background_music()
        
        if not os.path.exists(BACKGROUND_MUSIC):
            return
        
        # Create stop event for this music session
        self._music_stop_event = threading.Event()
        
        def loop_music():
            try:
                if AUDIO_BACKEND == 'pygame':
                    pygame.mixer.music.load(BACKGROUND_MUSIC)
                    pygame.mixer.music.play(-1)  # Loop indefinitely
                    # Wait for stop event
                    self._music_stop_event.wait()
                    pygame.mixer.music.stop()
                elif AUDIO_BACKEND == 'winsound':
                    import winsound
                    while not self._music_stop_event.is_set():
                        winsound.PlaySound(BACKGROUND_MUSIC, winsound.SND_FILENAME)
                        self._music_stop_event.wait(timeout=0.1)
            except Exception as e:
                print(f"Failed to play background music: {e}")
        
        self._music_thread = threading.Thread(target=loop_music, daemon=True)
        self._music_thread.start()
    
    def stop_background_music(self) -> None:
        """Stop the looping background music."""
        if self._music_stop_event is not None:
            self._music_stop_event.set()
        
        # Don't call winsound.PlaySound(None, SND_PURGE) - it can hang on Windows
        # The music thread will stop when _music_stop_event is set
        
        # Don't wait for thread to finish - let it stop asynchronously
        # This prevents blocking the main game thread
        self._music_thread = None
        self._music_stop_event = None
    
    def toggle_sound(self) -> None:
        """Toggle sound on/off."""
        self.sound_enabled = not self.sound_enabled
    
    def toggle_music(self) -> None:
        """Toggle music on/off."""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_background_music()
        else:
            self.start_background_music()
    
    def play_beep_unthrottled(self, frequency: int, duration: int) -> None:
        """
        Play a beep without throttling. Used for rapid-fire attacks.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        if not self.sound_enabled or not AUDIO_AVAILABLE:
            return
        
        print(f"[SOUND] Playing unthrottled beep: {frequency}Hz for {duration}ms")
        
        def beep():
            try:
                if AUDIO_BACKEND == 'pygame':
                    self._generate_beep_pygame(frequency, duration)
                elif AUDIO_BACKEND == 'winsound':
                    import winsound
                    winsound.Beep(frequency, duration)
            except Exception as e:
                print(f"[SOUND] Failed to play beep: {e}")
        
        thread = threading.Thread(target=beep, daemon=True)
        thread.start()


# Global audio manager instance
audio_manager: Optional[AudioManager] = None


def get_audio_manager() -> AudioManager:
    """Get or create the global audio manager instance."""
    global audio_manager
    if audio_manager is None:
        audio_manager = AudioManager()
    return audio_manager


# Legacy module-level functions for backward compatibility
def play_sound_async(sound_name: str, frequency: Optional[int] = None, 
                    duration: Optional[int] = None, game_instance=None) -> None:
    """Legacy function - delegates to AudioManager."""
    manager = get_audio_manager()
    if game_instance is not None:
        manager.sound_enabled = game_instance.sound_enabled
    manager.play_sound_async(sound_name, frequency, duration)


def play_beep_async(frequency: int, duration: int, game_instance=None) -> None:
    """Legacy function - delegates to AudioManager."""
    manager = get_audio_manager()
    if game_instance is not None:
        manager.sound_enabled = game_instance.sound_enabled
    manager.play_beep_async(frequency, duration)


def play_beep_unthrottled(frequency: int, duration: int, game_instance=None) -> None:
    """Play a beep without throttling - for rapid-fire attacks."""
    manager = get_audio_manager()
    if game_instance is not None:
        manager.sound_enabled = game_instance.sound_enabled
    manager.play_beep_unthrottled(frequency, duration)


def start_background_music(game_instance=None) -> None:
    """Legacy function - delegates to AudioManager."""
    manager = get_audio_manager()
    if game_instance is not None:
        manager.music_enabled = game_instance.music_enabled
        manager.sound_enabled = game_instance.sound_enabled
    manager.start_background_music()


def stop_background_music() -> None:
    """Legacy function - delegates to AudioManager."""
    manager = get_audio_manager()
    manager.stop_background_music()
