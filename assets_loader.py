"""Load PNG sprites from assets/, or generate a placeholder when none exists.

This lets the game run today with generated placeholders, and pick up real art
later with zero code changes: just drop player.png / obstacle.png / heart.png
into the assets/ folder.
"""

import os
import sys

import pygame


def _assets_dir():
    """Resolve the assets folder, working both from source and a frozen exe."""
    if getattr(sys, "frozen", False):
        # PyInstaller unpacks bundled data here at runtime.
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets")


def _make_placeholder(size, color, shape="rect"):
    """Build a simple colored Surface used when no PNG is provided."""
    surface = pygame.Surface(size, pygame.SRCALPHA)
    w, h = size
    if shape == "circle":
        pygame.draw.circle(surface, color, (w // 2, h // 2), min(w, h) // 2)
    elif shape == "heart":
        # Two circles + a triangle = a passable heart.
        r = w // 4
        pygame.draw.circle(surface, color, (r, r + 2), r)
        pygame.draw.circle(surface, color, (w - r, r + 2), r)
        pygame.draw.polygon(surface, color, [(2, r + 4), (w - 2, r + 4), (w // 2, h - 2)])
    else:
        pygame.draw.rect(surface, color, (0, 0, w, h), border_radius=10)
    return surface


def load_sprite(name, size, fallback_color, shape="rect"):
    """Return a Surface scaled to `size`.

    Loads assets/<name>.png if present; otherwise returns a generated
    placeholder in `fallback_color`.
    """
    path = os.path.join(_assets_dir(), f"{name}.png")
    if os.path.exists(path):
        try:
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(image, size)
        except pygame.error:
            pass  # fall through to placeholder if the file is unreadable
    return _make_placeholder(size, fallback_color, shape)
