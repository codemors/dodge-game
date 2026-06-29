"""Falling obstacles (יצר הרע). Each one is a random dark sprite from a set of
seven variants, so the falling evil elements look varied instead of identical.
Spawn at a random x along the top and fall straight down."""

import os
import random

import pygame

import settings
from assets_loader import _assets_dir, load_sprite

# The seven evil-shape variants (obstacle1.png … obstacle7.png). Loaded once and
# shared across all obstacles. Each is scaled to fit the obstacle box while
# preserving its own aspect ratio (the shapes are not all the same proportions).
_VARIANTS = None


def _fit(image, box):
    """Scale `image` to fit within `box` (w, h) preserving aspect ratio."""
    iw, ih = image.get_size()
    s = min(box[0] / iw, box[1] / ih)
    return pygame.transform.smoothscale(image, (max(1, round(iw * s)),
                                                max(1, round(ih * s))))


def _get_variants():
    global _VARIANTS
    if _VARIANTS is None:
        # the evil shapes are fit a bit smaller so they don't dominate the screen
        box = (round(settings.OBSTACLE_SIZE[0] * 0.7225),
               round(settings.OBSTACLE_SIZE[1] * 0.7225))
        adir = _assets_dir()
        variants = []
        for i in range(1, 8):
            path = os.path.join(adir, f"obstacle{i}.png")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    variants.append(_fit(img, box))
                    continue
                except pygame.error:
                    pass
        if not variants:
            # fall back to the single legacy sprite / placeholder
            variants = [load_sprite("obstacle", settings.OBSTACLE_SIZE,
                                    settings.OBSTACLE_COLOR, shape="circle")]
        _VARIANTS = variants
    return _VARIANTS


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, fall_speed, half=None):
        super().__init__()
        self.image = random.choice(_get_variants())
        w = self.image.get_width()
        # half="left"/"right" restricts the spawn x to that side of the screen
        # (used in 2-player mode so each player gets their own falling obstacle)
        if half == "left":
            lo, hi = 0, settings.WIDTH // 2 - w
        elif half == "right":
            lo, hi = settings.WIDTH // 2, settings.WIDTH - w
        else:
            lo, hi = 0, settings.WIDTH - w
        x = random.randint(lo, max(lo, hi))
        self.rect = self.image.get_rect(topleft=(x, -self.image.get_height()))
        self.y = float(self.rect.y)
        self.fall_speed = fall_speed

    def update(self, dt):
        self.y += self.fall_speed * dt
        self.rect.y = round(self.y)

    @property
    def hitbox(self):
        return self.rect.inflate(
            -self.rect.width * (1 - settings.OBSTACLE_HITBOX_SHRINK),
            -self.rect.height * (1 - settings.OBSTACLE_HITBOX_SHRINK),
        )

    def is_off_screen(self):
        return self.rect.top > settings.HEIGHT
