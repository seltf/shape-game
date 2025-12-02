"""
utils.py
Utility functions for the top-down game.
"""

def rect_overlap(r1, r2):
    """
    Check if two rectangles (x1, y1, x2, y2) overlap.
    Returns True if they overlap, False otherwise.
    """
    return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])
