"""Falling bonus items — good deeds (מעשים טובים) and good-inclination spirits
(יצר טוב: ויתור, פירגון, עין טובה / לב זהב, נתינה). Collect them for bonus
points. Each is one of several art variants chosen at random per spawn."""

import os
import random

import pygame

import settings
from assets_loader import _assets_dir, load_sprite

# Each variant: (asset file, points, spawn weight). Glowing good-deed gift boxes
# (חסד / נתינה / מעשים טובים / לב זהב) — all worth the same, equally common.
_VARIANT_DEFS = [
    ("collect_hesed.png", settings.CROWN_POINTS, 1),    # חסד
    ("collect_netina.png", settings.CROWN_POINTS, 1),   # נתינה
    ("collect_maasim.png", settings.CROWN_POINTS, 1),   # מעשים טובים
    ("collect_lev.png", settings.CROWN_POINTS, 1),      # לב זהב
]

_VARIANTS = None        # list of (image, points), loaded once


def _fit(image, box):
    """Scale `image` to fit within `box` (w, h) preserving aspect ratio."""
    iw, ih = image.get_size()
    s = min(box[0] / iw, box[1] / ih)
    return pygame.transform.smoothscale(image, (max(1, round(iw * s)),
                                                max(1, round(ih * s))))


def _get_variants():
    global _VARIANTS
    if _VARIANTS is None:
        box = settings.COLLECTIBLE_SIZE
        adir = _assets_dir()
        variants = []
        for fname, points, weight in _VARIANT_DEFS:
            path = os.path.join(adir, fname)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    variants.append((_fit(img, box), points, weight))
                    continue
                except pygame.error:
                    pass
        if not variants:
            # fallback to a simple placeholder so the game still runs
            img = load_sprite("collectible", box, settings.GOLD_COLOR, "circle")
            variants = [(img, settings.CROWN_POINTS, 1)]
        _VARIANTS = variants
    return _VARIANTS


class Collectible(pygame.sprite.Sprite):
    def __init__(self, half=None):
        super().__init__()
        variants = _get_variants()
        image, points, _ = random.choices(
            variants, weights=[v[2] for v in variants], k=1)[0]
        self.points = points
        self.image = image
        w = self.image.get_width()
        # half="left"/"right" keeps the bonus on one side (2-player mode)
        if half == "left":
            lo, hi = 0, settings.WIDTH // 2 - w
        elif half == "right":
            lo, hi = settings.WIDTH // 2, settings.WIDTH - w
        else:
            lo, hi = 0, settings.WIDTH - w
        x = random.randint(lo, max(lo, hi))
        self.rect = self.image.get_rect(topleft=(x, -self.image.get_height()))
        self.y = float(self.rect.y)

    def update(self, dt):
        self.y += settings.COLLECTIBLE_FALL * dt
        self.rect.y = round(self.y)

    def is_off_screen(self):
        return self.rect.top > settings.HEIGHT
