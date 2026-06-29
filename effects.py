"""Lightweight visual feedback: sparkle particles and floating score popups.

All effects are purely procedural (no extra image assets) and self-expiring.
"""

import math
import random

import pygame


class Sparkle:
    """A small glowing dot that flies outward and fades — used on bonus pickup."""

    def __init__(self, x, y, color):
        ang = random.uniform(0, math.tau)
        speed = random.uniform(60, 200)
        self.vx = math.cos(ang) * speed
        self.vy = math.sin(ang) * speed - 40  # bias slightly upward
        self.x = x
        self.y = y
        self.color = color
        self.life = random.uniform(0.4, 0.8)
        self.age = 0.0
        self.size = random.randint(2, 4)

    def update(self, dt):
        self.age += dt
        self.vy += 240 * dt  # gravity
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.age < self.life

    def draw(self, screen):
        t = 1 - (self.age / self.life)
        alpha = max(0, min(255, int(255 * t)))
        r = max(1, int(self.size * t) + 1)
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.color + (alpha,), (r, r), r)
        screen.blit(surf, (self.x - r, self.y - r))


class Popup:
    """Floating "+5" style text that rises and fades."""

    def __init__(self, x, y, text, color, font):
        self.x = x
        self.y = y
        self.color = color
        self.life = 0.9
        self.age = 0.0
        self.surf = font.render(text, True, color)

    def update(self, dt):
        self.age += dt
        self.y -= 50 * dt
        return self.age < self.life

    def draw(self, screen):
        t = 1 - (self.age / self.life)
        alpha = max(0, min(255, int(255 * t)))
        img = self.surf.copy()
        img.set_alpha(alpha)
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        # soft shadow for readability
        shadow = self.surf.copy()
        shadow.fill((0, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        shadow.set_alpha(alpha)
        screen.blit(shadow, rect.move(2, 2))
        screen.blit(img, rect)


class Effects:
    """Owns all live particles/popups; one instance per game session."""

    def __init__(self, font):
        self.items = []
        self.font = font

    def burst(self, x, y, color, count=14):
        for _ in range(count):
            self.items.append(Sparkle(x, y, color))

    def popup(self, x, y, text, color):
        self.items.append(Popup(x, y, text, color, self.font))

    def update(self, dt):
        self.items = [e for e in self.items if e.update(dt)]

    def draw(self, screen):
        for e in self.items:
            e.draw(screen)
