"""Centralized font definitions for the game UI.

Define font tuples here so the rest of the code can import and use a consistent
set of font families/sizes. This makes it easier to change the look across the
project and select a platform-appropriate default.
"""
from typing import Tuple

# Primary family. On Windows 'Segoe UI' looks native; fallback will be handled
# by Tk if the family is not available.
FAMILY: str = 'Segoe UI'
MONO_FAMILY: str = 'Courier'

# Convenience constants used across the UI
FONT_64_BOLD: Tuple = (FAMILY, 64, 'bold')
FONT_48_BOLD: Tuple = (FAMILY, 48, 'bold')
FONT_42_BOLD: Tuple = (FAMILY, 42, 'bold')
FONT_36_BOLD: Tuple = (FAMILY, 36, 'bold')
FONT_32_BOLD: Tuple = (FAMILY, 32, 'bold')
FONT_28_BOLD: Tuple = (FAMILY, 28, 'bold')
FONT_24_BOLD: Tuple = (FAMILY, 24, 'bold')

FONT_24: Tuple = (FAMILY, 24)
FONT_20_BOLD: Tuple = (FAMILY, 20, 'bold')
FONT_20: Tuple = (FAMILY, 20)
FONT_18_BOLD: Tuple = (FAMILY, 18, 'bold')
FONT_18: Tuple = (FAMILY, 18)
FONT_16: Tuple = (FAMILY, 16)
FONT_14: Tuple = (FAMILY, 14)
FONT_14_BOLD: Tuple = (FAMILY, 14, 'bold')
FONT_12: Tuple = (FAMILY, 12)
FONT_12_BOLD: Tuple = (FAMILY, 12, 'bold')
FONT_10: Tuple = (FAMILY, 10)
FONT_8: Tuple = (FAMILY, 8)

# Monospace
MONO_10: Tuple = (MONO_FAMILY, 10)
