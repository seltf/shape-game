#!/usr/bin/env python3
"""
Quick test to verify the level progression system is working correctly.
This script demonstrates the wave structure for each level.
"""

from constants import GAME_LEVEL_WAVES, LEVEL_REST_DURATION

def display_level_info():
    """Display wave structure for each game level."""
    print("=" * 70)
    print("GAME LEVEL PROGRESSION SYSTEM")
    print("=" * 70)
    print(f"\nRest Period Between Levels: {LEVEL_REST_DURATION}ms ({LEVEL_REST_DURATION/1000}s)\n")
    
    for level, waves in sorted(GAME_LEVEL_WAVES.items()):
        total_enemies = sum(wave[1] for wave in waves)
        print(f"Level {level}: {len(waves)} wave(s), {total_enemies} total enemies")
        
        for wave_idx, (enemy_type, count, delay) in enumerate(waves, 1):
            print(f"  Wave {wave_idx}: {count}x {enemy_type:8s} @ {delay:4d}ms")
        print()

def analyze_difficulty():
    """Analyze difficulty progression."""
    print("\n" + "=" * 70)
    print("DIFFICULTY ANALYSIS")
    print("=" * 70 + "\n")
    
    for level in [1, 5, 10, 15, 20]:
        if level in GAME_LEVEL_WAVES:
            waves = GAME_LEVEL_WAVES[level]
            total_enemies = sum(wave[1] for wave in waves)
            num_waves = len(waves)
            
            # Count by enemy type
            square = sum(wave[1] for wave in waves if wave[0] == 'square')
            triangle = sum(wave[1] for wave in waves if wave[0] == 'triangle')
            pentagon = sum(wave[1] for wave in waves if wave[0] == 'pentagon')
            
            # Calculate wave duration (last wave delay + estimated spawn time)
            last_wave_delay = waves[-1][2] if waves else 0
            duration = last_wave_delay + 2000  # +2s for last wave to complete
            
            print(f"Level {level}:")
            print(f"  Total Enemies: {total_enemies}")
            print(f"  - Square:   {square}")
            print(f"  - Triangle: {triangle}")
            print(f"  - Pentagon: {pentagon}")
            print(f"  Number of Waves: {num_waves}")
            print(f"  Estimated Duration: {duration}ms ({duration/1000:.1f}s)")
            print()

if __name__ == '__main__':
    display_level_info()
    analyze_difficulty()
    
    print("=" * 70)
    print("Level progression system test complete!")
    print("=" * 70)
