# Dodge Game — יצר טוב vs יצר רע

A 2D arcade game for **2 players** sharing one screen. Each player is a glowing
good spirit (יצר טוב). **Dodge the falling dark spirits (יצר רע)** and **collect
crowns and Torah scrolls** for bonus points. Each player has 3 lives and their
own score. The pace speeds up slowly over time (capped, so it stays fair).

**The last spirit still flying wins** — if both fall together, the higher score
wins.

## Scoring

| Event | Points |
| --- | --- |
| Dodge a dark spirit (it leaves the bottom) | +1 |
| Collect a crown (כתר) | +5 |
| Collect a Torah scroll (ספר תורה) | +10 |

Hitting a dark spirit costs one life (with a brief invulnerability blink).

The game UI is in **Hebrew** (right-to-left), using the bundled `assets/hebrew.ttf`
font and `python-bidi` for correct RTL display.

## Menu (תפריט)

On launch you get a Hebrew menu — navigate with **arrow keys or the mouse**,
confirm with **Enter / click**:

- **שחקן אחד** — one player
- **שני שחקנים** — two players (competitive)
- **יציאה** — quit

## Controls

| Action | Player 1 (gold glow) | Player 2 (blue glow) |
| --- | --- | --- |
| Move left  | ← | A |
| Move right | → | D |

| Action | Key |
| --- | --- |
| Menu: navigate | ↑ ↓ / mouse |
| Menu: confirm | Enter / click |
| Restart (game over) | R |
| Back to menu / quit | Esc |

## Run it (Mac / development)

A virtual environment with the dependencies already lives in `venv/`:

```
./venv/bin/python main.py
```

To recreate the environment from scratch:

```
python3 -m venv venv
./venv/bin/python -m pip install -r requirements.txt
./venv/bin/python main.py
```

## Custom graphics

The game ships with simple generated placeholder shapes so it runs out of the
box. To use your own art, drop PNG files into the `assets/` folder — they are
picked up automatically with **no code changes**:

| File | What it replaces |
| --- | --- |
| `assets/player.png`   | player 1 (girl in a pink dress) |
| `assets/player2.png`  | player 2 (girl in a blue dress) |
| `assets/obstacle.png` | the falling obstacle (יצר רע) |
| `assets/crown.png`    | the crown bonus (כתר) |
| `assets/torah.png`    | the Torah scroll bonus (ספר תורה) |
| `assets/background.png` | the game background (a heavenly sky-city) |
| `assets/heart.png`    | the life icons in the HUD |
| `assets/hebrew.ttf`   | the Hebrew UI font (bundled for the exe) |

If `background.png` is missing, the game falls back to a generated night-sky
gradient with stars. The player sprite gets an automatic golden glow so it stays
visible on bright backgrounds.

Images are scaled automatically to the sizes defined in `settings.py`. Use
transparent PNGs for the best look — the current art was cut from source images
with an AI background remover so it sits cleanly on the night-sky background.

## Building a Windows `.exe`

See [build_exe.md](build_exe.md). Short version (run **on Windows**):

```
pyinstaller --onefile --windowed --add-data "assets;assets" main.py
```

Output: `dist\main.exe` — a standalone file that runs without Python installed.

## Tuning

All gameplay values (window size, speeds, difficulty ramp, caps, lives, colors)
live in `settings.py`. Edit that one file to rebalance the game.
