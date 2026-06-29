"""All tunable game constants live here. Tune the whole game from this one file."""

# --- Window ---
WIDTH = 800
HEIGHT = 600
FPS = 60
TITLE = "Dodge Game"
TITLE_HE = "הנצחון האמיתי"

# --- Colors (RGB) ---
BG_TOP = (12, 14, 30)              # night-sky gradient top
BG_BOTTOM = (40, 30, 70)           # night-sky gradient bottom
STAR_COLOR = (220, 225, 255)
TEXT_COLOR = (235, 235, 245)
GOLD_COLOR = (255, 210, 120)       # bonus text / accents
FUCHSIA_COLOR = (255, 0, 160)      # game-title color (fuchsia pink)
PLAYER_COLOR = (210, 220, 255)     # placeholder fallback tint
OBSTACLE_COLOR = (60, 55, 75)      # placeholder fallback tint
HEART_COLOR = (255, 70, 110)       # placeholder fallback tint

# --- Floor (cloud bank the players stand on) ---
FLOOR_HEIGHT = 42                  # thickness of the cloud floor at the bottom
FLOOR_COLOR = (245, 248, 255)      # bright cloud white
FLOOR_SHADE = (205, 214, 235)      # soft bluish under-shadow

# --- Players (side-profile walking girls) — narrow & tall ---
PLAYER_SIZE = (60, 130)            # ~1:2.16 ratio, matches the profile artwork (20% larger)
PLAYER_SPEED = 440                 # pixels per second
PLAYER_BOTTOM_MARGIN = 36          # players stand on top of the cloud floor
PLAYER_HITBOX_SHRINK = 0.6         # collision box = sprite * this (forgiving)
START_LIVES = 3
INVULN_TIME = 1.2                  # seconds of i-frames after a hit (blinking)

# Glow halo colors that distinguish the two players.
P1_GLOW = (255, 180, 210)          # pink  (player 1)
P2_GLOW = (150, 200, 255)          # blue  (player 2)

# Walk animation: legs are swung procedurally; this many baked stride frames.
WALK_FRAMES = 8                    # 8 = smooth stride (4 per leps), pre-baked
WALK_CADENCE = 9.0                 # stride speed (radians/sec while moving)

# --- Obstacles (יצר רע) — wide sprite ---
OBSTACLE_SIZE = (84, 72)
OBSTACLE_HITBOX_SHRINK = 0.7

# --- Collectibles (מעשים טובים / יצר טוב bonuses) ---
COLLECTIBLE_SIZE = (66, 66)        # 10% larger
COLLECTIBLE_FALL = 200             # they fall a bit slower than obstacles
COLLECTIBLE_SPAWN = 2.2            # seconds between bonus spawns (more frequent)
CROWN_POINTS = 5
TORAH_POINTS = 10

# --- Difficulty ramp (the "speeds up but not too much" requirement) ---
# Fall speed grows from BASE_FALL toward MAX_FALL as time passes.
BASE_FALL = 220                    # pixels per second at game start
MAX_FALL = 520                     # hard cap so it never runs away
RAMP_SPEED = 6                     # px/sec added per second elapsed

# Spawn interval shrinks from BASE_SPAWN toward MIN_SPAWN (more obstacles).
BASE_SPAWN = 1.10                  # seconds between spawns at start
MIN_SPAWN = 0.40                   # hard floor
RAMP_SPAWN = 0.012                 # seconds removed per second elapsed


# --- Resolution scaling -----------------------------------------------------
# All sizes/speeds above are authored against a 600px-tall reference screen.
# apply_scale() multiplies the pixel-based ones to match the real window height
# so the game looks the same on any resolution (including fullscreen).
_REF_HEIGHT = 600
_BASE = {  # name -> reference value at 600px tall
    "FLOOR_HEIGHT": 42,
    "PLAYER_SIZE": (60, 130), "PLAYER_SPEED": 440, "PLAYER_BOTTOM_MARGIN": 36,
    "OBSTACLE_SIZE": (84, 72), "COLLECTIBLE_SIZE": (66, 66),
    "COLLECTIBLE_FALL": 200,
    "BASE_FALL": 220, "MAX_FALL": 520, "RAMP_SPEED": 6,
}


def apply_scale(height):
    """Scale all pixel-based constants to the given screen height."""
    g = globals()
    s = height / _REF_HEIGHT
    for name, val in _BASE.items():
        if isinstance(val, tuple):
            g[name] = (round(val[0] * s), round(val[1] * s))
        else:
            g[name] = round(val * s)
