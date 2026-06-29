"""Hebrew text helpers: bundled RTL font + bidi reordering for pygame.

pygame renders glyphs left-to-right, so Hebrew must be reordered for display.
python-bidi handles mixed Hebrew/numbers correctly (e.g. "שחקן 1: 42").
"""

import os

import pygame

from assets_loader import _assets_dir

try:
    from bidi import get_display
except ImportError:  # pragma: no cover - bidi is a hard dependency for Hebrew
    def get_display(s):
        return s[::-1]

_FONT_CACHE = {}


def _font_path():
    return os.path.join(_assets_dir(), "hebrew.ttf")


def he_font(size, bold=False):
    """A cached Hebrew-capable font at the given size (bundled with the game)."""
    key = (size, bold)
    if key not in _FONT_CACHE:
        path = _font_path()
        if os.path.exists(path):
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
        else:
            font = pygame.font.SysFont("arialunicode", size, bold=bold)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]


def title_font(size):
    """The decorative game-title font (shluk). Falls back to the regular
    Hebrew font if the title font is missing."""
    key = ("title", size)
    if key not in _FONT_CACHE:
        path = os.path.join(_assets_dir(), "title_font.otf")
        if os.path.exists(path):
            _FONT_CACHE[key] = pygame.font.Font(path, size)
        else:
            _FONT_CACHE[key] = he_font(size, bold=True)
    return _FONT_CACHE[key]


def shape(text):
    """Reorder a string for correct right-to-left display."""
    return get_display(text)
