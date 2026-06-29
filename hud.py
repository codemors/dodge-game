"""Polished HUD widgets: a glossy blue-gold capsule holding hearts or the score.

Everything is drawn procedurally (no image assets) and cached per (size, state)
so it's cheap to redraw every frame.
"""

import os

import pygame

from text_he import he_font, shape
from assets_loader import _assets_dir

# palette pulled from the reference art
_BLUE_DARK = (18, 52, 120)
_BLUE_MID = (40, 96, 196)
_BLUE_LIGHT = (90, 150, 240)
_GOLD = (235, 196, 90)
_GOLD_HI = (255, 232, 150)
_HEART_RED = (228, 40, 48)
_HEART_HI = (255, 120, 120)
_HEART_EMPTY = (28, 40, 70)
_WHITE = (250, 250, 255)

_cache = {}


def _capsule(w, h):
    """A glossy blue capsule with a gold rim, rounded to a pill shape."""
    key = ("cap", w, h)
    if key in _cache:
        return _cache[key]
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    radius = h // 2

    # vertical blue gradient body
    body = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / h
        # darker top & bottom, brighter middle
        m = 1 - abs(t - 0.45) * 1.6
        m = max(0.0, min(1.0, m))
        col = tuple(round(_BLUE_DARK[i] + (_BLUE_LIGHT[i] - _BLUE_DARK[i]) * m)
                    for i in range(3))
        pygame.draw.line(body, col, (0, y), (w, y))

    # mask to a rounded-rect (pill)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(body, (0, 0))

    # top glossy highlight
    gloss = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(gloss, (255, 255, 255, 60),
                     (radius // 2, 3, w - radius, h // 2 - 2),
                     border_radius=radius // 2)
    surf.blit(gloss, (0, 0))

    # gold rim (single clean ring — no inner highlight pill that read as a
    # second floating gold line behind the capsule)
    pygame.draw.rect(surf, _GOLD, (0, 0, w, h), width=max(2, h // 16),
                     border_radius=radius)

    _cache[key] = surf
    return surf


# The lives display uses two supplied art assets: a blue-gold bar with three
# heart-shaped recesses (hearts_bar.png) and a glossy red heart (heart_full.png)
# laid into the filled slots. Loaded once and cached scaled-to-size.
# The three slot centers sit at these fractions of the bar's width/height.
_SLOT_FRACS_X = (0.27, 0.50, 0.73)
_SLOT_FRAC_Y = 0.535       # vertical center of each heart recess
_HEART_FILL = 0.60          # red heart size as a fraction of the bar height

_art = {}


def _load_art(name):
    if name in _art:
        return _art[name]
    path = os.path.join(_assets_dir(), name)
    img = pygame.image.load(path).convert_alpha() if os.path.exists(path) else None
    _art[name] = img
    return img


def _hearts_bar(w):
    """The lives bar scaled to width w (keeps the art's aspect). Returns surf."""
    bar = _load_art("hearts_bar.png")
    if bar is None:
        return None
    key = ("bar", w)
    if key in _cache:
        return _cache[key]
    iw, ih = bar.get_size()
    h = max(1, round(w * ih / iw))
    surf = pygame.transform.smoothscale(bar, (w, h))
    _cache[key] = surf
    return surf


def _heart_img(d):
    """The red heart scaled to fit a d×d box (keeps aspect). Returns surf."""
    heart = _load_art("heart_full.png")
    if heart is None:
        return None
    key = ("heartimg", d)
    if key in _cache:
        return _cache[key]
    iw, ih = heart.get_size()
    s = d / max(iw, ih)
    surf = pygame.transform.smoothscale(
        heart, (max(1, round(iw * s)), max(1, round(ih * s))))
    _cache[key] = surf
    return surf


def draw_hearts(screen, x, y, scale, lives, max_lives):
    """Draw the lives capsule with `lives` red hearts laid on top. (x,y)=top-left.

    Uses the same smooth blue-gold pill as the score capsule (no carved heart
    slots) and overlays evenly-spaced red hearts. Falls back to the procedural
    capsule if the art assets are missing.
    Returns the capsule's rect.
    """
    w = int(133 * scale)
    h = int(45 * scale)
    cap = _score_cap(w, h)
    if cap is None:
        return _draw_hearts_fallback(screen, x, y, scale, lives, max_lives)
    screen.blit(cap, (x, y))

    heart_d = int(h * 0.62)
    heart = _heart_img(heart_d)
    if heart:
        # space the hearts evenly across the inner area of the pill
        inner = w - h            # leave a rounded-cap margin on each side
        step = inner / max_lives
        cy = y + h // 2
        for i in range(max_lives):
            if i < lives:
                cx = x + h // 2 + int((i + 0.5) * step)
                screen.blit(heart, heart.get_rect(center=(cx, cy)))
    return pygame.Rect(x, y, w, h)


def _draw_hearts_fallback(screen, x, y, scale, lives, max_lives):
    """Procedural lives capsule (used only if the art assets are missing)."""
    d = int(30 * scale)
    gap = int(8 * scale)
    pad_x = int(18 * scale)
    pad_y = int(10 * scale)
    w = pad_x * 2 + max_lives * d + (max_lives - 1) * gap
    h = d + pad_y * 2
    screen.blit(_capsule(w, h), (x, y))
    for i in range(max_lives):
        hx = x + pad_x + i * (d + gap)
        s = pygame.Surface((d, d), pygame.SRCALPHA)
        color = _HEART_RED if i < lives else _HEART_EMPTY
        r = d // 4
        pygame.draw.circle(s, color, (r + 1, r + 2), r)
        pygame.draw.circle(s, color, (d - r - 1, r + 2), r)
        pygame.draw.polygon(s, color, [(1, r + 3), (d - 1, r + 3), (d // 2, d - 1)])
        screen.blit(s, (hx, y + pad_y))
    return pygame.Rect(x, y, w, h)


def _score_cap(w, h):
    """The blue-gold pill (score_capsule.png) sized to w×h using 3-slice
    scaling so the rounded gold end caps keep their shape while only the
    middle stretches. Falls back to the procedural capsule if art is missing.
    """
    art = _load_art("score_capsule.png")
    if art is None:
        return _capsule(w, h)
    key = ("scorecap", w, h)
    if key in _cache:
        return _cache[key]

    iw, ih = art.get_size()
    # scale the source so its height matches h
    sh = h
    sw = max(1, round(iw * h / ih))
    scaled = pygame.transform.smoothscale(art, (sw, sh))
    cap_w = sh  # end-cap slice width ~ one capsule height (covers the rounded end)
    cap_w = min(cap_w, sw // 2 - 1)

    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if w >= 2 * cap_w + 2:
        left = scaled.subsurface(pygame.Rect(0, 0, cap_w, h))
        right = scaled.subsurface(pygame.Rect(sw - cap_w, 0, cap_w, h))
        mid_src = scaled.subsurface(pygame.Rect(cap_w, 0, sw - 2 * cap_w, h))
        mid = pygame.transform.smoothscale(mid_src, (w - 2 * cap_w, h))
        surf.blit(left, (0, 0))
        surf.blit(mid, (cap_w, 0))
        surf.blit(right, (w - cap_w, 0))
    else:
        surf.blit(pygame.transform.smoothscale(scaled, (w, h)), (0, 0))

    _cache[key] = surf
    return surf


def draw_score(screen, x, y, scale, label, score, anchor="left"):
    """Draw a score capsule with a Hebrew label and big number.

    anchor 'left' => (x,y) is top-left; 'right' => (x,y) is top-right.
    Returns the rect.
    """
    label_font = he_font(int(12 * scale), bold=True)
    num_font = he_font(int(18 * scale), bold=True)

    num_txt = f"{score:,}"
    num_surf = num_font.render(num_txt, True, _WHITE)
    lab_surf = label_font.render(shape(label), True, _GOLD_HI)

    # fixed size so the score capsule matches the hearts capsule exactly
    w = int(133 * scale)
    h = int(45 * scale)
    if anchor == "right":
        x = x - w

    cap = _score_cap(w, h)
    screen.blit(cap, (x, y))

    cx = x + w // 2
    # label near the top
    screen.blit(lab_surf, lab_surf.get_rect(center=(cx, y + int(14 * scale))))
    # number below, with a soft shadow
    shadow = num_font.render(num_txt, True, (10, 20, 50))
    nrect = num_surf.get_rect(center=(cx, y + int(31 * scale)))
    screen.blit(shadow, nrect.move(2, 2))
    screen.blit(num_surf, nrect)

    return pygame.Rect(x, y, w, h)
