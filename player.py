"""The player character: horizontal movement, lives, and post-hit i-frames."""

import math

import pygame

import os

import settings
from assets_loader import _assets_dir, _make_placeholder, load_sprite
from walk_rig import WalkRig


class Player(pygame.sprite.Sprite):
    def __init__(self, asset="player", glow=settings.P1_GLOW,
                 left_keys=(pygame.K_LEFT,), right_keys=(pygame.K_RIGHT,),
                 start_x=None):
        super().__init__()
        self.left_keys = left_keys
        self.right_keys = right_keys

        # Two poses at a shared height so the player never "jumps" when switching:
        #   stand = back view, arms raised (used when standing still)
        #   walk  = side profile (used when moving), articulated via a cutout rig
        h = settings.PLAYER_SIZE[1]
        self.stand_image = _add_outline(_load_by_height(asset, h, glow), color=glow)
        walk_clean = _load_by_height(asset + "_walk", h, glow)
        self.walk_image = _add_outline(walk_clean, color=glow)

        # build an articulated walk cycle and pre-bake the frames (with outline)
        rig = WalkRig(walk_clean)
        self._walk_frames = []
        for i in range(settings.WALK_FRAMES):
            ph = i / settings.WALK_FRAMES * 2 * math.pi
            self._walk_frames.append(_add_outline(rig.render(ph, False), color=glow))

        self.image = self.stand_image
        self.base_image = self.image

        if start_x is None:
            start_x = settings.WIDTH // 2
        bottom = settings.HEIGHT - settings.PLAYER_BOTTOM_MARGIN
        # hitbox width based on the (narrower) walk pose for fairness
        self.rect = self.stand_image.get_rect(midbottom=(start_x, bottom))
        # float x for smooth, frame-rate-independent movement
        self.x = float(self.rect.x)

        self.lives = settings.START_LIVES
        self.score = 0
        self.invuln = 0.0          # remaining seconds of invulnerability
        self._blink_timer = 0.0

        # --- animation state ---
        self._walk_phase = 0.0     # advances while moving -> selects the leg frame
        self._idle_phase = 0.0     # always advances -> gentle breathing when still
        self._pop = 0.0            # >0 right after catching a bonus (squash/jump)
        self._facing = 1           # last horizontal direction (for facing flip)
        self._moving = False

    @property
    def alive(self):
        return self.lives > 0

    @property
    def is_invulnerable(self):
        return self.invuln > 0

    @property
    def hitbox(self):
        """A smaller, centered collision rect so the glow/edges don't count as hits."""
        return self.rect.inflate(
            -self.rect.width * (1 - settings.PLAYER_HITBOX_SHRINK),
            -self.rect.height * (1 - settings.PLAYER_HITBOX_SHRINK),
        )

    def update(self, keys, dt):
        # Use this player's own key bindings.
        direction = 0
        if any(keys[k] for k in self.left_keys):
            direction -= 1
        if any(keys[k] for k in self.right_keys):
            direction += 1

        self.x += direction * settings.PLAYER_SPEED * dt
        # Clamp to screen bounds.
        self.x = max(0, min(self.x, settings.WIDTH - self.rect.width))
        self.rect.x = round(self.x)

        # --- drive the animation ---
        self._moving = direction != 0
        if self._moving:
            self._facing = direction
            self._walk_phase += dt * settings.WALK_CADENCE
        self._idle_phase += dt * 2.2
        if self._pop > 0:
            self._pop = max(0.0, self._pop - dt * 3.0)

        # i-frame blink
        if self.invuln > 0:
            self.invuln = max(0.0, self.invuln - dt)
            self._blink_timer += dt

        # kept for any external size checks
        self.base_image = self.walk_image if self._moving else self.stand_image
        self.image = self.base_image

    def pop(self):
        """Trigger a little squash/jump — called when the player catches a bonus."""
        self._pop = 1.0

    def draw(self, screen):
        """Draw the articulated sprite. While moving: pick the matching leg frame
        from the baked walk cycle, add a movement-driven double-bounce bob and a
        synced squash/stretch. While idle: the back-view 'arms up' pose breathing.
        """
        # skip frames while blinking after a hit
        if self.invuln > 0 and int(self._blink_timer * 12) % 2 == 1:
            return

        squash_mul = 1.0

        if self._moving:
            # select the leg frame for this stride phase
            n = settings.WALK_FRAMES
            idx = int(self._walk_phase / (2 * math.pi) * n) % n
            img = self._walk_frames[idx]
            if self._facing < 0:
                img = pygame.transform.flip(img, True, False)

            # body is LOWEST at each foot contact -> two dips per stride (abs sin)
            bob = -abs(math.sin(self._walk_phase)) * 7.0
            # squash at the low (contact), slight stretch at the high (passing)
            squash_mul = 1.0 + 0.05 * math.cos(self._walk_phase * 2)
        else:
            img = self.stand_image
            bob = math.sin(self._idle_phase) * 1.5

        # bonus-catch pop overrides with a bigger squash + hop
        if self._pop > 0:
            squash_mul *= 1.0 + 0.18 * self._pop * math.sin(self._pop * math.pi)
            bob -= 8 * self._pop

        if abs(squash_mul - 1.0) > 0.005:
            w = max(1, int(img.get_width() / squash_mul))
            h = max(1, int(img.get_height() * squash_mul))
            img = pygame.transform.smoothscale(img, (w, h))

        draw_rect = img.get_rect(midbottom=(self.rect.centerx,
                                            self.rect.bottom + round(bob)))
        screen.blit(img, draw_rect)

    def hit(self):
        """Take damage if not currently invulnerable. Returns True if a life was lost."""
        if self.is_invulnerable:
            return False
        self.lives -= 1
        self.invuln = settings.INVULN_TIME
        self._blink_timer = 0.0
        return True


def _transparent(surface):
    """A fully transparent copy of a surface (used for the blink 'off' frame)."""
    blank = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    return blank


def _load_by_height(name, height, fallback_color):
    """Load assets/<name>.png scaled to a target height, preserving aspect ratio.

    Lets the back-view and profile poses share one height (so the player never
    jumps vertically) while keeping each pose's own width.
    """
    path = os.path.join(_assets_dir(), f"{name}.png")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            w, h = img.get_size()
            new_w = max(1, round(w * height / h))
            return pygame.transform.smoothscale(img, (new_w, height))
        except pygame.error:
            pass
    # fallback placeholder keeps the player's nominal size
    return _make_placeholder((settings.PLAYER_SIZE[0], height), fallback_color, "rect")


def _add_outline(sprite, color=(255, 255, 255), thickness=3):
    """Draw a clean colored outline around the sprite's silhouette.

    Looks crisp on detailed (human) sprites — unlike a blurred glow, which turns
    into an ugly ghost. The outline both separates the player from the background
    and identifies which player is which (pink vs blue).
    """
    w, h = sprite.get_size()
    pad = thickness + 1
    out = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)

    # A solid-colored copy of the silhouette (keeps original alpha).
    sil = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
    sil.fill(color + (255,))
    sil.blit(sprite, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    # Force the colored silhouette back to full opacity where the sprite exists.
    solid = sprite.copy()
    solid.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)

    cx, cy = out.get_width() // 2, out.get_height() // 2
    base_rect = solid.get_rect(center=(cx, cy))
    # Stamp the silhouette in a ring of offsets to form the outline.
    for angle in range(0, 360, 30):
        dx = round(math.cos(math.radians(angle)) * thickness)
        dy = round(math.sin(math.radians(angle)) * thickness)
        out.blit(solid, base_rect.move(dx, dy))

    out.blit(sprite, sprite.get_rect(center=(cx, cy)))
    return out
