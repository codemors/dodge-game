# Building the Windows `.exe`

PyInstaller produces a binary **for the operating system it runs on**. Building
on a Mac gives you a Mac binary — **not** a Windows `.exe`. So the real `.exe`
must be built **on a Windows machine**.

## On Windows

1. Install Python 3 from https://www.python.org (check "Add Python to PATH").
2. Open a terminal (Command Prompt or PowerShell) in this project folder.
3. Create a virtual environment and install the dependencies:

   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Build the standalone exe:

   ```
   pyinstaller --onefile --windowed --add-data "assets;assets" main.py
   ```

   - `--onefile` — one self-contained `.exe`.
   - `--windowed` — no console window pops up behind the game.
   - `--add-data "assets;assets"` — bundles the `assets/` folder, which includes
     the sprites **and `hebrew.ttf`** (the Hebrew font). On Windows the separator
     is a semicolon `;`.
   - The `python-bidi` package (for Hebrew right-to-left text) is bundled
     automatically by PyInstaller — no extra flag needed.

5. The result is **`dist\main.exe`** — a single file you can copy and run on any
   Windows PC, no Python required.

## Testing on Mac (optional)

You can build a Mac binary to sanity-check the packaging (uses a colon `:`
instead of `;`):

```
pyinstaller --onefile --windowed --add-data "assets:assets" main.py
```

This is only for local testing — distribute the Windows-built `.exe` to Windows
users.
