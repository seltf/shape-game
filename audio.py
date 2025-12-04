"""
Audio management system for Top Down Game
Handles sound effects, beeps, and background music playback
"""

import winsound
import threading
import os
import sys
import time
from constants import SOUND_COOLDOWN_MS


# Determine the base directory for resources (handles both dev and bundled exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Audio is available on Windows with winsound
AUDIO_AVAILABLE = True

# Sound effects dictionary - maps sound names to file paths
SOUND_EFFECTS = {
    'black_hole_detonate': os.path.join(BASE_DIR, 'sounds/black_hole_detonate.wav'),
    'projectile_hit': os.path.join(BASE_DIR, 'sounds/projectile_hit.wav'),
    'enemy_death': os.path.join(BASE_DIR, 'sounds/enemy_death.wav'),
    'powerup': os.path.join(BASE_DIR, 'sounds/powerup.wav'),
}

# Background music file
BACKGROUND_MUSIC = os.path.join(BASE_DIR, 'sounds/bit track space.wav')


class AudioManager:
    """Manages all audio playback including effects, beeps, and background music."""
    
    def __init__(self):
        """Initialize audio manager with throttling and state tracking."""
        self._last_sound_time = {}  # Track when each sound was last played
        self._music_thread = None
        self._music_stop_event = None
        self.sound_enabled = True
        self.music_enabled = True
    
    def play_sound_async(self, sound_name: str, frequency: int = None, 
                        duration: int = None) -> None:
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
            # Try to load custom sound file using winsound
            if sound_name in SOUND_EFFECTS and AUDIO_AVAILABLE:
                sound_path = SOUND_EFFECTS[sound_name]
                if os.path.exists(sound_path):
                    try:
                        print(f"  -> Playing file: {sound_path}")
                        winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        return  # Successfully played file, don't play fallback
                    except Exception as e:
                        print(f"  -> Failed to play file {sound_path}: {e}")
                        # Fall through to beep fallback
            
            # Fallback to beep if custom sound unavailable or couldn't be loaded
            if frequency is not None and duration is not None:
                try:
                    print(f"  -> Playing beep fallback: {frequency}Hz for {duration}ms")
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
        if not self.sound_enabled:
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
                winsound.Beep(frequency, duration)
            except Exception as e:
                print(f"[SOUND] Failed to play beep: {e}")
        
        thread = threading.Thread(target=beep, daemon=True)
        thread.start()
    
    def start_background_music(self) -> None:
        """Start looping background music."""
        # Check if sound and music are enabled
        if not self.sound_enabled or not self.music_enabled:
            return
        
        # Stop any existing music
        self.stop_background_music()
        
        if not AUDIO_AVAILABLE or not os.path.exists(BACKGROUND_MUSIC):
            return
        
        # Create stop event for this music session
        self._music_stop_event = threading.Event()
        
        def loop_music():
            try:
                while not self._music_stop_event.is_set():
                    winsound.PlaySound(BACKGROUND_MUSIC, winsound.SND_FILENAME)
                    # Check stop event periodically
                    self._music_stop_event.wait(timeout=0.1)
            except Exception as e:
                print(f"Failed to play background music: {e}")
        
        self._music_thread = threading.Thread(target=loop_music, daemon=True)
        self._music_thread.start()
    
    def stop_background_music(self) -> None:
        """Stop the looping background music."""
        if self._music_stop_event is not None:
            self._music_stop_event.set()
        
        # Stop winsound playback
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        
        # Wait for thread to finish
        if self._music_thread is not None and self._music_thread.is_alive():
            self._music_thread.join(timeout=1.0)
        
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


# Global audio manager instance
audio_manager = None


def get_audio_manager() -> AudioManager:
    """Get or create the global audio manager instance."""
    global audio_manager
    if audio_manager is None:
        audio_manager = AudioManager()
    return audio_manager


# Legacy module-level functions for backward compatibility
def play_sound_async(sound_name: str, frequency: int = None, 
                    duration: int = None, game_instance=None) -> None:
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
