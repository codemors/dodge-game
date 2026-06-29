"""משחק התחמקות — יצר טוב בורח מיצר רע ואוסף קדושה.

מצבים: תפריט -> משחק -> סיום (-> חזרה לתפריט). הקצב מתגבר לאט עם הזמן, עם תקרה.
"""

import random

import math

import pygame

import settings
from assets_loader import load_sprite
from collectible import Collectible
from effects import Effects
import hud
from obstacle import Obstacle
from player import Player
from text_he import he_font, title_font, shape

# מצבי משחק
MENU = "menu"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"
SETTINGS = "settings"        # תפריט הגדרות מוזיקה/אפקטים

# פריטי התפריט הראשי: (תווית בעברית, מספר שחקנים / פעולה)
MENU_ITEMS = [
    ("שחקן אחד", 1),
    ("שני שחקנים", 2),
    ("מוזיקה", "settings"),    # opens the audio-settings submenu
    ("יציאה", "quit"),
]

# פריטי תפריט הגדרות המוזיקה: (תווית, פעולה) — התוויות מתעדכנות לפי המצב
SETTINGS_ITEMS = [
    ("מוזיקת רקע", "music"),
    ("אפקטים", "sfx"),
    ("חזרה", "back"),
]

# פריטי תפריט ההשהיה: (תווית, פעולה)
PAUSE_ITEMS = [
    ("המשך", "resume"),
    ("חזרה לתפריט הראשי", "menu"),
]


def build_background():
    """משתמש ב-assets/background.png אם קיים; אחרת גרדיאנט שמיים עם כוכבים."""
    import os
    from assets_loader import _assets_dir

    path = os.path.join(_assets_dir(), "background.png")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert()
            return pygame.transform.smoothscale(img, (settings.WIDTH, settings.HEIGHT))
        except pygame.error:
            pass  # נפילה חזרה לרקע המחושב

    bg = pygame.Surface((settings.WIDTH, settings.HEIGHT))
    top, bottom = settings.BG_TOP, settings.BG_BOTTOM
    for y in range(settings.HEIGHT):
        t = y / settings.HEIGHT
        color = tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        pygame.draw.line(bg, color, (0, y), (settings.WIDTH, y))
    rng = random.Random(42)
    for _ in range(110):
        x = rng.randint(0, settings.WIDTH)
        y = rng.randint(0, settings.HEIGHT)
        r = rng.choice([1, 1, 1, 2])
        shade = rng.randint(150, 255)
        pygame.draw.circle(bg, (shade, shade, min(255, shade + 10)), (x, y), r)
    return bg


class AnimatedBackground:
    """Looping video-style background built from a folder of extracted frames
    (assets/bg_frames/f001.jpg …). Plays forward then backward forever
    (ping-pong) so the loop reverses seamlessly. Frames are kept at their source
    size; only the currently-shown frame is scaled to the screen (and cached),
    which keeps memory low even at high screen resolutions."""

    FPS = 8.0  # must match the fps the frames were extracted at

    def __init__(self):
        import os
        from assets_loader import _assets_dir
        self.frames = []        # source frames at their extracted size
        self.order = []         # ping-pong index sequence into self.frames
        self.t = 0.0
        self._cache_key = None  # (frame_index, screen_size) of the cached surface
        self._cache_surf = None
        fdir = os.path.join(_assets_dir(), "bg_frames")
        if os.path.isdir(fdir):
            names = sorted(n for n in os.listdir(fdir)
                           if n.lower().endswith((".jpg", ".jpeg", ".png")))
            for n in names:
                try:
                    self.frames.append(
                        pygame.image.load(os.path.join(fdir, n)).convert())
                except pygame.error:
                    pass
        n = len(self.frames)
        if n > 2:
            # 0,1,…,n-1, n-2,…,1  → reverses without repeating the endpoints
            self.order = list(range(n)) + list(range(n - 2, 0, -1))
        else:
            self.order = list(range(n))

    @property
    def ok(self):
        return len(self.frames) > 0

    def update(self, dt):
        self.t += dt

    def draw(self, screen):
        frame_idx = self.order[int(self.t * self.FPS) % len(self.order)]
        size = (settings.WIDTH, settings.HEIGHT)
        key = (frame_idx, size)
        if key != self._cache_key:
            self._cache_surf = pygame.transform.smoothscale(
                self.frames[frame_idx], size)
            self._cache_key = key
        screen.blit(self._cache_surf, (0, 0))


def load_logo(target_w):
    """The show-name logo (assets/logo.png) scaled to target_w, keeping aspect.
    Returns None if the file is missing."""
    import os
    from assets_loader import _assets_dir
    path = os.path.join(_assets_dir(), "logo.png")
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
    except pygame.error:
        return None
    iw, ih = img.get_size()
    h = max(1, round(target_w * ih / iw))
    return pygame.transform.smoothscale(img, (target_w, h))


def build_floor():
    """A fluffy cloud bank along the bottom that the players stand on.

    Built from several rows of overlapping puffs (back rows tinted, front rows
    bright) so it reads as a soft, deep cloud rather than a flat white bar.
    """
    h = settings.FLOOR_HEIGHT
    rise = 46  # how far puffs rise above the solid band
    surf = pygame.Surface((settings.WIDTH, h + rise), pygame.SRCALPHA)
    top_y = rise

    # solid base band the puffs sit on
    pygame.draw.rect(surf, settings.FLOOR_COLOR, (0, top_y, settings.WIDTH, h))

    rng = random.Random(7)
    # back row (shaded, sits a touch lower) then front row (bright, on top)
    for row, (color, dy, rmin, rmax) in enumerate([
        (settings.FLOOR_SHADE, 12, 30, 50),
        (settings.FLOOR_COLOR, -2, 26, 46),
    ]):
        x = -10
        while x < settings.WIDTH + 40:
            r = rng.randint(rmin, rmax)
            cy = top_y + dy + rng.randint(-5, 5)
            pygame.draw.circle(surf, color, (x, cy), r)
            if row == 1:
                hi = tuple(min(255, c + 7) for c in settings.FLOOR_COLOR)
                pygame.draw.circle(surf, hi, (x - r // 4, cy - r // 4), r // 2)
            x += rng.randint(30, 46)
    return surf


def _render_he(font, text, color):
    """מרנדר טקסט עברי (כולל סידור RTL) למשטח, חתוך לתיבה התוחמת בפועל.

    רינדור עברי דרך SDL_ttf משאיר לעיתים ריפוד לא-סימטרי בצדדים, מה שגורם
    לטקסט "ממורכז" להיראות מוסט. חיתוך ל-bounding-box האמיתי מבטיח מרכוז נכון.
    """
    surf = font.render(shape(text), True, color)
    bounds = surf.get_bounding_rect()
    if bounds.width and bounds.height:
        return surf.subsurface(bounds).copy()
    return surf


def _blit_text(screen, font, text, color, topright=None, center=None):
    """מצייר טקסט עברי עם קו מתאר כהה לקריאות על כל רקע."""
    shadow = _render_he(font, text, (20, 20, 30))
    main = _render_he(font, text, color)
    if center is not None:
        rect = main.get_rect(center=center)
    else:
        rect = main.get_rect(topright=topright)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
        screen.blit(shadow, rect.move(dx, dy))
    screen.blit(main, rect)
    return rect


def draw_center_text(screen, font, text, y, color=None):
    color = color or settings.TEXT_COLOR
    return _blit_text(screen, font, text, color, center=(settings.WIDTH // 2, y))


def draw_text_at(screen, font, text, cx, y, color=None):
    """Hebrew text centred horizontally on an arbitrary x (not the screen middle)."""
    color = color or settings.TEXT_COLOR
    return _blit_text(screen, font, text, color, center=(cx, y))


def draw_volume_bar(screen, right_x, cy, fs, level, selected):
    """A segmented volume bar of 10 cells, filled to `level` (0..1).

    Drawn growing to the LEFT from right_x (so it sits left of an RTL label).
    Gold cells when selected, muted blue otherwise.
    """
    cells = 10
    cw = int(20 * fs)
    ch = int(26 * fs)
    cgap = int(5 * fs)
    filled = int(round(level * cells))
    on_col = settings.GOLD_COLOR if selected else (210, 180, 100)
    off_col = (60, 78, 120)
    border = (245, 220, 140) if selected else (180, 160, 110)
    total_w = cells * cw + (cells - 1) * cgap
    x0 = right_x - total_w
    top = cy - ch // 2
    for i in range(cells):
        cx = x0 + i * (cw + cgap)
        col = on_col if i < filled else off_col
        pygame.draw.rect(screen, col, (cx, top, cw, ch), border_radius=int(4 * fs))
        pygame.draw.rect(screen, border, (cx, top, cw, ch),
                         width=max(1, int(1.5 * fs)), border_radius=int(4 * fs))
    return pygame.Rect(x0, top, total_w, ch)


def draw_player_hud(screen, label, player, side):
    """מצייר כמוסת ניקוד + כמוסת לבבות לשחקן, בצד שלו (שמאל/ימין)."""
    scale = settings.HEIGHT / 600
    margin = int(18 * scale)
    top = int(14 * scale)
    gap = int(12 * scale)               # מרווח אופקי בין הניקוד ללבבות
    hearts_w = _hearts_width(scale)
    hearts_h = _hearts_height(scale)
    # הלבבות ממורכזים אנכית מול כמוסת הניקוד (גובה זהה: 45)
    hearts_y = top + int((45 * scale - hearts_h) / 2)
    if side == "left":
        score_rect = hud.draw_score(screen, margin, top, scale,
                                    label, player.score, anchor="left")
        # לבבות מימין לניקוד
        hud.draw_hearts(screen, score_rect.right + gap, hearts_y,
                        scale, player.lives, settings.START_LIVES)
    else:
        right = settings.WIDTH - margin
        score_rect = hud.draw_score(screen, right, top, scale,
                                    label, player.score, anchor="right")
        # לבבות משמאל לניקוד
        hud.draw_hearts(screen, score_rect.left - gap - hearts_w, hearts_y,
                        scale, player.lives, settings.START_LIVES)


def _hearts_width(scale):
    return int(133 * scale)


def _hearts_height(scale):
    return int(45 * scale)


def draw_score_columns(screen, s1, s2, t, counting, winner):
    """Two side-by-side score columns (one per player) on the result screen.

    Each column shows the player's label and a big climbing number — the same
    look as the single-player score, just two of them. The winning column is
    highlighted once counting finishes.
    """
    fs = settings.HEIGHT / 600
    cy = settings.HEIGHT // 2 - int(20 * fs)
    label_font = he_font(int(34 * fs), bold=True)

    # match the in-game sides: player 1 (arrows) on the right, player 2 (A/D) on the left
    cols = [
        ("שחקן 2", s2, settings.P2_GLOW, settings.WIDTH // 4, 2),
        ("שחקן 1", s1, settings.P1_GLOW, 3 * settings.WIDTH // 4, 1),
    ]
    for label, shown, color, cx, who in cols:
        is_winner = (not counting) and (winner == who)
        # label
        draw_text_at(screen, label_font, label, cx,
                     cy - int(70 * fs), color)
        # big number, pulsing while counting, extra-large for the winner
        pulse = 1.0 + (0.14 * abs(math.sin(t * 8)) if counting else 0)
        base = 80 if is_winner else 68
        num_font = he_font(int(base * fs * pulse), bold=True)
        num_col = settings.GOLD_COLOR if is_winner else (255, 255, 255)
        draw_text_at(screen, num_font, f"{shown:,}", cx,
                     cy + int(10 * fs), num_col)
        # a small star marker over the winner
        if is_winner:
            draw_text_at(screen, label_font, "★", cx,
                         cy - int(120 * fs), settings.GOLD_COLOR)


def main():
    pygame.init()
    pygame.display.set_caption(settings.TITLE)

    # background music for the lobby (menu) and the game-over screen
    import os
    from assets_loader import _assets_dir
    music_ok = False
    collect_sfx = None
    hurt_sfx = None
    try:
        pygame.mixer.init()
        music_path = os.path.join(_assets_dir(), "menu_music.mp3")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.5)
            music_ok = True
        # sound effect played when a good item is collected
        sfx_path = os.path.join(_assets_dir(), "collect_sfx.mp3")
        if os.path.exists(sfx_path):
            collect_sfx = pygame.mixer.Sound(sfx_path)
            collect_sfx.set_volume(0.7)
        # sound effect played when hit by a bad obstacle (יצר הרע)
        hurt_path = os.path.join(_assets_dir(), "hurt_sfx.mp3")
        if os.path.exists(hurt_path):
            hurt_sfx = pygame.mixer.Sound(hurt_path)
            hurt_sfx.set_volume(0.7)
    except pygame.error:
        music_ok = False
        collect_sfx = None
        hurt_sfx = None

    # independent 0.0–1.0 volumes for background music and sound effects
    music_vol = 0.5
    sfx_vol = 0.7
    VOL_STEP = 0.1

    def music_start():
        """Start the endless background loop (plays through every screen)."""
        if music_ok:
            pygame.mixer.music.set_volume(music_vol)
            pygame.mixer.music.play(-1)  # loop forever, never stops

    def set_music_vol(v):
        nonlocal music_vol
        music_vol = max(0.0, min(1.0, round(v, 2)))
        if music_ok:
            pygame.mixer.music.set_volume(music_vol)

    def set_sfx_vol(v):
        nonlocal sfx_vol
        sfx_vol = max(0.0, min(1.0, round(v, 2)))

    # Open fullscreen at the desktop resolution, and make WIDTH/HEIGHT match it so
    # every layout value (background, floor, spawns, player bounds) scales to fit.
    is_fullscreen = True
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    settings.WIDTH, settings.HEIGHT = screen.get_size()
    settings.apply_scale(settings.HEIGHT)

    clock = pygame.time.Clock()

    # scale fonts to the screen height (designed against a 600px-tall reference)
    fs = settings.HEIGHT / 600
    font_big = he_font(int(58 * fs), bold=True)
    font_title = title_font(int(78 * fs))   # decorative shluk font for the title
    font_med = he_font(int(34 * fs), bold=True)
    font_small = he_font(int(24 * fs))
    heart_img = load_sprite("heart", (int(28 * fs), int(28 * fs)),
                            settings.HEART_COLOR, shape="heart")
    logo_img = load_logo(int(280 * fs))   # show-name logo, bottom-left of the menu
    anim_bg = AnimatedBackground()   # looping video-style background (if frames exist)
    background = build_background()   # static fallback / used when no frames
    floor_img = build_floor()
    floor_y = settings.HEIGHT - settings.FLOOR_HEIGHT  # where the cloud band starts

    def draw_background(screen):
        if anim_bg.ok:
            anim_bg.draw(screen)
        else:
            screen.blit(background, (0, 0))

    def toggle_fullscreen():
        nonlocal screen, is_fullscreen, background, floor_img, floor_y
        nonlocal font_big, font_title, font_med, font_small, heart_img, logo_img
        is_fullscreen = not is_fullscreen
        if is_fullscreen:
            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((960, 720))
        settings.WIDTH, settings.HEIGHT = screen.get_size()
        settings.apply_scale(settings.HEIGHT)
        # rebuild everything that depends on the resolution
        f = settings.HEIGHT / 600
        font_big = he_font(int(58 * f), bold=True)
        font_title = title_font(int(78 * f))
        font_med = he_font(int(34 * f), bold=True)
        font_small = he_font(int(24 * f))
        heart_img = load_sprite("heart", (int(28 * f), int(28 * f)),
                                settings.HEART_COLOR, shape="heart")
        logo_img = load_logo(int(280 * f))
        background = build_background()
        floor_img = build_floor()
        floor_y = settings.HEIGHT - settings.FLOOR_HEIGHT

    state = MENU
    menu_index = 0
    pause_index = 0
    settings_index = 0
    num_players = 2
    players = []
    obstacles = None
    collectibles = None
    effects = None
    elapsed = 0.0
    spawn_timer = 0.0
    bonus_timer = 0.0
    result_text = ""
    over_time = 0.0       # seconds elapsed inside the GAME_OVER animation
    menu_rects = []  # (rect, index) for mouse hit-testing
    pause_rects = []  # (rect, index) for the pause menu
    settings_rects = []  # (rect, index) for the settings submenu

    def start_game(n):
        nonlocal players, obstacles, collectibles, effects, elapsed, spawn_timer, bonus_timer, num_players
        num_players = n
        # Arrow-key player sits on the RIGHT; A/D player sits on the LEFT.
        p1 = Player(asset="player", glow=settings.P1_GLOW,
                    left_keys=(pygame.K_LEFT,), right_keys=(pygame.K_RIGHT,),
                    start_x=(2 * settings.WIDTH // 3 if n == 2 else settings.WIDTH // 2))
        players = [p1]
        if n == 2:
            p2 = Player(asset="player2", glow=settings.P2_GLOW,
                        left_keys=(pygame.K_a,), right_keys=(pygame.K_d,),
                        start_x=settings.WIDTH // 3)
            players.append(p2)
        obstacles = pygame.sprite.Group()
        collectibles = pygame.sprite.Group()
        effects = Effects(he_font(30, bold=True))
        elapsed = 0.0
        spawn_timer = 0.0
        bonus_timer = 0.0

    def choose_menu():
        """מבצע את פריט התפריט הנבחר."""
        nonlocal state
        label, action = MENU_ITEMS[menu_index]
        if action == "quit":
            return False
        if action == "settings":
            state = SETTINGS     # open the audio-settings submenu
            return True
        start_game(action)
        state = PLAYING
        return True

    def choose_settings():
        """Enter על פריט בתפריט ההגדרות — רלוונטי רק ל'חזרה'."""
        nonlocal state
        label, action = SETTINGS_ITEMS[settings_index]
        if action == "back":
            state = MENU

    def adjust_settings(delta):
        """חיצים ימינה/שמאלה משנים את עוצמת השורה הנבחרת."""
        label, action = SETTINGS_ITEMS[settings_index]
        if action == "music":
            set_music_vol(music_vol + delta * VOL_STEP)
        elif action == "sfx":
            set_sfx_vol(sfx_vol + delta * VOL_STEP)

    def choose_pause():
        """מבצע את פריט תפריט ההשהיה הנבחר."""
        nonlocal state
        label, action = PAUSE_ITEMS[pause_index]
        if action == "resume":
            state = PLAYING
        elif action == "menu":
            state = MENU

    def draw_scene():
        """מצייר את ספרייטי המשחק וה-HUD (משותף ל-PLAYING ול-PAUSED)."""
        collectibles.draw(screen)
        obstacles.draw(screen)
        # cloud floor: drawn over falling items (they vanish into it) but under players
        screen.blit(floor_img, (0, floor_y - (floor_img.get_height() - settings.FLOOR_HEIGHT)))
        for p in players:
            if p.alive:
                p.draw(screen)
        if effects is not None:
            effects.draw(screen)
        if num_players == 1:
            draw_player_hud(screen, "ניקוד", players[0], "left")
        else:
            draw_player_hud(screen, "שחקן 1", players[0], "right")
            draw_player_hud(screen, "שחקן 2", players[1], "left")

    music_start()  # background music starts once and loops through every screen

    running = True
    while running:
        dt = clock.tick(settings.FPS) / 1000.0
        anim_bg.update(dt)   # advance the looping background

        # --- אירועים ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                elif event.key == pygame.K_ESCAPE:
                    if state == MENU:
                        running = False
                    elif state == PLAYING:
                        state = PAUSED       # השהיה — לא מאבד את המשחק
                        pause_index = 0
                    elif state == PAUSED:
                        state = PLAYING      # המשך מהשהיה
                    elif state == SETTINGS:
                        state = MENU         # חזרה מתפריט ההגדרות
                    else:                    # GAME_OVER
                        state = MENU
                elif state == MENU:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        menu_index = (menu_index - 1) % len(MENU_ITEMS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        menu_index = (menu_index + 1) % len(MENU_ITEMS)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        running = choose_menu()
                elif state == SETTINGS:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        settings_index = (settings_index - 1) % len(SETTINGS_ITEMS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        settings_index = (settings_index + 1) % len(SETTINGS_ITEMS)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        adjust_settings(-1)   # שמאל = פחות
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        adjust_settings(+1)   # ימין = יותר
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        choose_settings()
                elif state == PAUSED:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        pause_index = (pause_index - 1) % len(PAUSE_ITEMS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        pause_index = (pause_index + 1) % len(PAUSE_ITEMS)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        choose_pause()
                elif state == GAME_OVER:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_r):
                        start_game(num_players)
                        state = PLAYING

            elif event.type == pygame.MOUSEMOTION:
                if state == MENU:
                    for rect, idx in menu_rects:
                        if rect.collidepoint(event.pos):
                            menu_index = idx
                elif state == PAUSED:
                    for rect, idx in pause_rects:
                        if rect.collidepoint(event.pos):
                            pause_index = idx
                elif state == SETTINGS:
                    for rect, idx in settings_rects:
                        if rect.collidepoint(event.pos):
                            settings_index = idx

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == MENU:
                    for rect, idx in menu_rects:
                        if rect.collidepoint(event.pos):
                            menu_index = idx
                            running = choose_menu()
                elif state == PAUSED:
                    for rect, idx in pause_rects:
                        if rect.collidepoint(event.pos):
                            pause_index = idx
                            choose_pause()
                elif state == SETTINGS:
                    for rect, idx in settings_rects:
                        if rect.collidepoint(event.pos):
                            settings_index = idx
                            choose_settings()

        draw_background(screen)

        if state == MENU:
            title_y = int(settings.HEIGHT * 0.26)
            subtitle_y = title_y + int(58 * fs)
            draw_center_text(screen, font_title, settings.TITLE_HE,
                             title_y, settings.FUCHSIA_COLOR)
            draw_center_text(screen, font_small,
                             "מתחמקים מהיצר הרע ואוספים זכויות ומעשים טובים",
                             subtitle_y, settings.TEXT_COLOR)

            menu_rects = []
            # פריטי התפריט בשליש התחתון של המסך, עם ריווח צפוף יותר ביניהם
            base_y = int(settings.HEIGHT * 0.66)
            gap = int(54 * fs)
            for i, (label, action) in enumerate(MENU_ITEMS):
                selected = (i == menu_index)
                color = settings.GOLD_COLOR if selected else settings.TEXT_COLOR
                item_y = base_y + i * gap
                # הטקסט תמיד באותו מיקום (מרכז); ה-hover משנה רק צבע + מוסיף סמן
                rect = draw_center_text(screen, font_med, label, item_y, color)
                if selected:
                    # הסמן ◆ מימין לטקסט, בלי להזיז את המילים עצמן
                    mark = draw_text_at(screen, font_med, "◆",
                                        rect.right + int(26 * fs), item_y,
                                        settings.GOLD_COLOR)
                # אזור לחיצה רחב יותר לעכבר
                hit = pygame.Rect(0, 0, int(320 * fs), int(48 * fs))
                hit.center = (settings.WIDTH // 2, item_y)
                menu_rects.append((hit, i))

            # show-name logo in the bottom-left corner of the main menu
            if logo_img is not None:
                m = int(24 * fs)
                screen.blit(logo_img, (m, settings.HEIGHT - logo_img.get_height() - m))

        elif state == SETTINGS:
            title_y = int(settings.HEIGHT * 0.26)
            draw_center_text(screen, font_big, "מוזיקה", title_y,
                             settings.GOLD_COLOR)
            draw_center_text(screen, font_small,
                             "חיצים ימינה/שמאלה לכוונון העוצמה",
                             title_y + int(58 * fs), settings.TEXT_COLOR)

            settings_rects = []
            base_y = int(settings.HEIGHT * 0.55)
            gap = int(72 * fs)
            cx = settings.WIDTH // 2
            for i, (label, action) in enumerate(SETTINGS_ITEMS):
                selected = (i == settings_index)
                color = settings.GOLD_COLOR if selected else settings.TEXT_COLOR
                row_y = base_y + i * gap
                if action == "back":
                    rect = draw_center_text(screen, font_med, label, row_y, color)
                    if selected:
                        draw_text_at(screen, font_med, "◆",
                                     rect.right + int(26 * fs), row_y,
                                     settings.GOLD_COLOR)
                else:
                    vol = music_vol if action == "music" else sfx_vol
                    # label to the right, volume bar to the left (RTL layout)
                    draw_text_at(screen, font_med, label,
                                 cx + int(190 * fs), row_y, color)
                    draw_volume_bar(screen, cx - int(40 * fs), row_y, fs, vol,
                                    selected)
                hit = pygame.Rect(0, 0, int(460 * fs), int(54 * fs))
                hit.center = (cx, row_y)
                settings_rects.append((hit, i))

        elif state == PLAYING:
            elapsed += dt
            fall_speed = min(settings.BASE_FALL + elapsed * settings.RAMP_SPEED,
                             settings.MAX_FALL)
            spawn_interval = max(settings.BASE_SPAWN - elapsed * settings.RAMP_SPAWN,
                                 settings.MIN_SPAWN)

            spawn_timer += dt
            if spawn_timer >= spawn_interval:
                spawn_timer = 0.0
                if num_players == 2:
                    # two players "compete" — drop one obstacle toward each half so
                    # both always have something to dodge (never idle = boring)
                    obstacles.add(Obstacle(fall_speed, half="left"))
                    obstacles.add(Obstacle(fall_speed, half="right"))
                else:
                    obstacles.add(Obstacle(fall_speed))

            bonus_timer += dt
            if bonus_timer >= settings.COLLECTIBLE_SPAWN:
                bonus_timer = 0.0
                if num_players == 2:
                    # one bonus per side so each player has something to chase
                    collectibles.add(Collectible(half="left"))
                    collectibles.add(Collectible(half="right"))
                else:
                    collectibles.add(Collectible())

            keys = pygame.key.get_pressed()
            for obs in obstacles:
                obs.update(dt)
            for item in collectibles:
                item.update(dt)
            effects.update(dt)

            living = [p for p in players if p.alive]
            for p in living:
                p.update(keys, dt)

                phit = p.hitbox
                struck = [obs for obs in obstacles
                          if phit.colliderect(obs.hitbox)]
                if struck:
                    if p.is_invulnerable:
                        # While blinking the player can't be hurt — but obstacles
                        # touching her must be removed so none stay lodged inside
                        # and strike the instant i-frames end.
                        for obs in struck:
                            obs.kill()
                    else:
                        for obs in struck:
                            obs.kill()
                        p.hit()  # one life lost regardless of how many hit at once
                        if hurt_sfx is not None and sfx_vol > 0:
                            hurt_sfx.set_volume(sfx_vol)
                            hurt_sfx.play()
                        effects.burst(p.rect.centerx, p.rect.centery,
                                      (255, 90, 90), count=16)

                for item in list(collectibles):
                    # an item can only be caught while it is still above the
                    # cloud floor — once it sinks into the floor it's gone.
                    if (item.alive() and item.rect.centery < floor_y
                            and p.rect.colliderect(item.rect)):
                        p.score += item.points
                        cx, cy = item.rect.center
                        item.kill()
                        p.pop()  # squash/jump
                        if collect_sfx is not None and sfx_vol > 0:
                            collect_sfx.set_volume(sfx_vol)
                            collect_sfx.play()
                        effects.burst(cx, cy, settings.GOLD_COLOR, count=18)
                        effects.popup(cx, cy, f"+{item.points}", settings.GOLD_COLOR)

            for obs in list(obstacles):
                if obs.is_off_screen():
                    # dodging an obstacle no longer scores — points come only
                    # from catching good items (collectibles).
                    obs.kill()
            for item in list(collectibles):
                # remove once it has sunk into the cloud floor (where it vanishes
                # visually) rather than waiting for the bottom of the screen.
                if item.rect.top > floor_y or item.is_off_screen():
                    item.kill()

            # סיום: אף שחקן לא נותר באוויר. עוברים לאנימציית הספירה.
            if not any(p.alive for p in players):
                state = GAME_OVER
                over_time = 0.0

            draw_scene()

        elif state == PAUSED:
            # מציירים את הסצנה הקפואה, מחשיכים אותה, ומציגים תפריט השהיה.
            draw_scene()
            shade = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            shade.fill((10, 12, 28, 160))
            screen.blit(shade, (0, 0))

            draw_center_text(screen, font_big, "מושהה", 150, settings.GOLD_COLOR)
            pause_rects = []
            base_y = 300
            for i, (label, _) in enumerate(PAUSE_ITEMS):
                selected = (i == pause_index)
                color = settings.GOLD_COLOR if selected else settings.TEXT_COLOR
                item_y = base_y + i * 64
                rect = draw_center_text(screen, font_med, label, item_y, color)
                if selected:
                    draw_text_at(screen, font_med, "◆",
                                 rect.right + int(26 * fs), item_y,
                                 settings.GOLD_COLOR)
                hit = pygame.Rect(0, 0, 420, 56)
                hit.center = (settings.WIDTH // 2, item_y)
                pause_rects.append((hit, i))
            draw_center_text(screen, font_small,
                             "Esc להמשך · חיצים + Enter · עכבר נתמך",
                             settings.HEIGHT - 50)

        elif state == GAME_OVER:
            over_time += dt

            # darken the frozen game behind the result for contrast
            collectibles.draw(screen)
            obstacles.draw(screen)
            shade = pygame.Surface((settings.WIDTH, settings.HEIGHT), pygame.SRCALPHA)
            shade.fill((10, 12, 28, 150))
            screen.blit(shade, (0, 0))

            COUNT_DUR = 1.6  # seconds for the scores to climb to their final value
            progress = min(over_time / COUNT_DUR, 1.0)
            eased = 1 - (1 - progress) ** 2  # ease-out so it decelerates into place
            counting = progress < 1.0

            draw_center_text(screen, font_big, "המשחק נגמר", 90,
                             settings.OBSTACLE_COLOR)

            if num_players == 1:
                shown = int(players[0].score * eased)
                pulse = 1.0 + (0.12 * abs(math.sin(over_time * 8)) if counting else 0)
                big = he_font(int(76 * pulse), bold=True)
                draw_center_text(screen, big, str(shown),
                                 settings.HEIGHT // 2 - 10, settings.GOLD_COLOR)
                draw_center_text(screen, font_med, "הניקוד שלך",
                                 settings.HEIGHT // 2 - 80, settings.TEXT_COLOR)
            else:
                p1, p2 = players
                s1 = int(p1.score * eased)
                s2 = int(p2.score * eased)
                # who won (0 = tie)
                winner = 1 if p1.score > p2.score else (2 if p2.score > p1.score else 0)
                draw_score_columns(screen, s1, s2, over_time, counting, winner)

                if not counting:
                    # Winner announcement (steady, no blink).
                    if winner == 1:
                        msg, col = "שחקן 1 ניצח!", settings.P1_GLOW
                    elif winner == 2:
                        msg, col = "שחקן 2 ניצח!", settings.P2_GLOW
                    else:
                        msg, col = "תיקו!", settings.GOLD_COLOR
                    win_font = he_font(int(54 * (settings.HEIGHT / 600)), bold=True)
                    draw_center_text(screen, win_font, msg,
                                     settings.HEIGHT - int(130 * (settings.HEIGHT / 600)), col)

            if not counting:
                draw_center_text(screen, font_small,
                                 "Enter לשחק שוב · Esc לתפריט",
                                 settings.HEIGHT - 45)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
