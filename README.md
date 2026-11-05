# Night Shift Detective - Gothic Edition 2.0

A gothic mystery for the browser, powered by a tiny Python server (standard library only, nothing to install).

## Run it in VS Code
1. Unzip and open the folder in VS Code (File > Open Folder).
2. Open the terminal (Ctrl+`) and run: `python app.py` (or `python3 app.py`).
3. Your browser opens at http://127.0.0.1:8000. Press Ctrl+C in the terminal to stop.

## Run it on Android (Termux)
1. Install Termux from F-Droid, then run `pkg install python`.
2. `cd` into this folder and run `python app.py`.
3. Open http://localhost:8000 in Chrome.

## Detective names (no password)
Type a name to enter the college. There is no password: the name keeps your record (cases played, closed, cold and so on) and your saved cases. Names use 3 to 20 letters, numbers or underscores. Anyone who types your name opens your record, so this suits a personal device.

## How to play
- Open **The Detective's Guide** from the menu, the Guide tab, or the pause screen. It explains everything in eight short pages.
- Pick a detective and a difficulty. Each night you get 3 actions at one of 4 to 6 places: Interview, Search or Follow.
- Trust and Time start full and drain as you work. Evidence starts empty and builds as you find clues (60 proves the case).
- Walk between places with the arrow buttons. The header arrows move back and forward through the screens you have visited.
- Board: tap two clues that point at the same thing and connect them to reveal a hidden scene.
- Suspects: build rapport to 60 to unlock a secret. Accuse at any time, or keep a secret for a quiet ending.

## Pause, save and return
- Tap **Pause** in a case to save it into Case File I, II or III, open the guide, or leave to the menu.
- The game also saves itself at the start of every night (Autosave).
- From the menu choose **Resume the latest case** or **Case files** to load one.
- Files are stored in `saves/<your name>/`. Delete a folder to remove a detective's saves. `users.json` holds the records.

## Fonts
The look uses Google Fonts (Cinzel, EB Garamond, UnifrakturCook). With no internet connection it falls back to your system serif fonts and still works.

## Copyright
Copyright © 2026 Wilfred Wanyoike. All rights reserved. See COPYRIGHT.txt.
