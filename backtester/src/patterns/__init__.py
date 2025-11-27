"""Pattern recognition module for identifying chart patterns."""

from .peaks import find_peaks, find_troughs
from .double_patterns import detect_double_top, detect_double_bottom

__all__ = [
    'find_peaks',
    'find_troughs',
    'detect_double_top',
    'detect_double_bottom'
]
