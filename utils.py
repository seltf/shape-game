"""
utils.py
Utility functions for the top-down game.
"""
from typing import Tuple

def rect_overlap(r1: Tuple[float, float, float, float], 
                 r2: Tuple[float, float, float, float]) -> bool:
    """
    Check if two rectangles (x1, y1, x2, y2) overlap.
    Returns True if they overlap, False otherwise.
    
    Args:
        r1: Rectangle 1 as (x1, y1, x2, y2)
        r2: Rectangle 2 as (x1, y1, x2, y2)
    
    Returns:
        True if rectangles overlap, False otherwise
    """
    return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])
