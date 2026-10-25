# Baseball Cards bot for MOUSE: P.I. For Hire

A small Python bot that plays the **Baseball Cards** minigame in *MOUSE: P.I. For Hire* for you.
It watches your screen, reads the numbers on your cards, picks the best play and clicks for you,
match after match, until you reach the number of wins you want (30 by default).

It's useful if you're grinding baseball wins and don't want to play dozens of matches by hand.

> **Tested result:** in its first real run it won **26 of 37 matches (70%)** and stopped by itself
> at 30 total wins, with no stuck screens. Your results depend on which cards you own.
> Try it on a single match first (see [Quick start](#quick-start)), and please
> [open an issue](../../issues) if something goes wrong.

> Unofficial fan project. It isn't affiliated with or endorsed by the game's developers or publisher.
> It doesn't modify the game or its files. It only looks at the screen and clicks, like you would.
> Each match costs **$50 of in-game money**. Use it at your own risk.

---

## Contents

- [What it does](#what-it-does)
- [Requirements](#requirements)
- [Installation](#installation)
- [The "Run as administrator" problem](#the-run-as-administrator-problem)
- [Quick start](#quick-start)
- [Options](#options)
- [Stopping and pausing](#stopping-and-pausing)
- [How it plays](#how-it-plays)
- [How the minigame works](#how-the-minigame-works)
- [Logs and screenshots](#logs-and-screenshots)
- [Troubleshooting](#troubleshooting)
- [How the bot works (technical)](#how-the-bot-works-technical)
- [Files](#files)

---

## What it does

Each match, the bot:

1. Stands at the Baseball Cards table and presses **E** to pay $50 and start a match.
2. On the **Banned Cards** screen, clicks **PLAY** without banning any cards.
3. On each of your turns (5 batting and 5 pitching), reads your hand, picks a card and a
   booster, and clicks **PLAY**.
4. Clicks **CLOSE** on the result screen.
5. Repeats until you have the target number of baseball wins, or until it has played the maximum
   number of matches you allowed.

It counts wins with the game's own counter (the `"BaseballCards"` value in
`%USERPROFILE%\AppData\LocalLow\Fumi Games\MOUSE\Save\profile.rsf`). It only **reads** that file and
never writes to it.

---

## Requirements

| What | Details |
|---|---|
| **OS** | Windows 10 or 11 |
| **Screen** | Game in **fullscreen at 1920×1080**, and your Windows main display set to 1920×1080. Other resolutions are not supported (the bot checks this and refuses to start). |
| **Python** | 3.10 or newer (tested with 3.14). Get it from [python.org](https://www.python.org/downloads/) and tick **"Add python.exe to PATH"** during install. |
| **Game language** | **English.** The bot recognizes English text such as "Baseball Cards" and "BANNED CARDS". |
| **Key bindings** | Default **E** to interact. If you rebound it, see [Troubleshooting](#troubleshooting). |
| **Windows OCR** | The English (en-US) language pack, which is installed on almost every English Windows. The bot uses Windows' built-in text recognition. |
| **In-game money** | $50 per match. At a ~70% win rate, expect roughly 1.4 matches per win, so 30 wins ≈ 43 matches ≈ $2,150. |

---

## Installation

1. **Download the bot.** Either:
   - click the green **Code** button on this page → **Download ZIP**, then unzip it somewhere (for example `C:\mouse-baseball-bot`), or
   - with git:
     ```
     git clone https://github.com/marwan-47/Mouse-P.I-for-hire-Baseball-minigame.git
     ```

2. **Open a terminal in that folder.** In File Explorer, open the folder, click the address bar,
   type `cmd` and press Enter.

3. **Install the Python packages:**
   ```
   python -m pip install -r requirements.txt
   ```

4. **Check it starts** (this mode never clicks anything):
   ```
   python bot.py --dry-run --delay 0
   ```
   You should see `Starting. Baseball wins so far: ...`. Press **Ctrl+C** to stop it.

---

## The "Run as administrator" problem

Windows doesn't let a normal program click inside a program that runs **as administrator**.
If your game runs as administrator, the bot can see the screen but its clicks are ignored.
The bot checks for this at startup and tells you if it's the case.

Fix it with **one** of these:

- **Option A (recommended):** stop the game running as admin.
  1. Close the game.
  2. Right-click `MOUSE.exe` in the game's install folder → **Properties** → **Compatibility**.
  3. Untick **"Run this program as an administrator"** → **OK**.
  4. Start the game again.
- **Option B:** run the bot as admin too. Search Windows for **cmd**, right-click it →
  **Run as administrator**, `cd` to the bot folder, and run the bot from there.

---

## Quick start

1. Start the game in **1920×1080 fullscreen**.
2. Walk up to the **Baseball Cards** table until the prompt **"Baseball Cards  E  Play ($50)"** shows.
   Don't start a match yourself.
3. In the terminal (in the bot folder), run a **one-match test**:
   ```
   python bot.py --max-matches 1
   ```
4. You have **5 seconds** to switch to the game with **Alt+Tab**. Don't touch the mouse or keyboard after that.
5. Watch it play one match. If everything works, run it for real:
   ```
   python bot.py
   ```
   It stops on its own once you have **30 baseball wins in total**, or after **40 matches**,
   whichever comes first.

> The win target counts your **total** baseball wins, including wins from before you used the bot.
> If you already have 4 wins, `--target 30` plays until you have 30, so 26 more.

---

## Options

```
python bot.py [--target N] [--max-matches N] [--dry-run] [--delay SECONDS]
```

| Option | Default | What it does |
|---|---|---|
| `--target N` | `30` | Stop when your **total** baseball wins reach N. |
| `--max-matches N` | `40` | Never start more than N matches in this run. This caps spending at N × $50. |
| `--dry-run` | off | Only look at the screen and log what it would do. Never clicks or presses keys. |
| `--delay SECONDS` | `5` | How long to wait before starting, so you can switch to the game. |

Examples:

```
python bot.py --max-matches 1          # test on one match
python bot.py --target 50              # keep going until 50 total wins
python bot.py --max-matches 10         # spend at most $500 this run
```

---

## Stopping and pausing

- **Stop:** press **F10**, or move the mouse into the **top-left corner** of the screen.
- **Pause:** **Alt+Tab** away from the game. The bot only clicks while the game window is in front,
  and it carries on when you switch back.
- **Ctrl+C** in the terminal also stops it.

If you stop it in the middle of a match, finish that match yourself or give up as usual.

---

## How it plays

Every turn it plays:

- **Your highest card**: the highest batter value when batting, the highest pitcher value when
  pitching. Ties go to the card with the higher shield number (speed or fielding).
- **Plus one booster, if you have one:**
  1. **Power Swing** (batting) or **Pitch Focus** (pitching) first, because they raise the main number.
  2. Otherwise **Speed Boost** (batting) or **Fielding Play** (pitching).

It doesn't ban cards on the Banned Cards screen and doesn't use discards (yet).

---

## How the minigame works

Knowing the rules helps explain the bot's choices:

- A match is 2 innings: you **bat** for 5 rounds, then **pitch** for 5 rounds.
- Each round, the batter plays a **Batter** card and the pitcher plays a **Pitcher** card. Each
  side may add one booster.
- **Hit or out:** batter number (+ Power Swing) against pitcher number (+ Pitch Focus).
  The higher number wins; a **tie is decided by a coin flip**.
- **Home run:** if the batter beats the pitcher by a big enough margin, it's a home run.
- **Running the bases:** after a hit, runners move forward by **speed (shield number + Speed Boost)
  minus the pitcher's fielding (shield number + Fielding Play)**.
- A runner who gets all the way around scores a point. Most points after both innings wins.
- **The computer opponent plays random cards**, not its best ones. That's why always playing your
  strongest card wins more often than not.
- Your deck is the cards you own. The opponent's deck is every card in the game.

---

## Logs and screenshots

The bot creates these next to `bot.py`:

- **`bot_log.txt`**: everything it did, with times. Each turn's hand and choice, and each match result, for example:
  ```
  10:12:01  --- Match 3 (total wins 6) ---
  10:12:40    hand: power +3, card 4/2, speed/fielding +1, card 6/2, card 5/3  ->  play card 6/2 + power +3
  10:16:55  Match over: WIN. This run: 2/3 won. Total baseball wins: 7.
  ```
  `card 6/2` means a card with main number 6 and shield number 2.
- **`debug_shots/`**: a screenshot of every result screen, and of any screen it got stuck on.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `The game runs as administrator, so Windows blocks this script's clicks` | See [The "Run as administrator" problem](#the-run-as-administrator-problem). |
| `Your main screen is ...x.... This bot only works at 1920x1080` | Set Windows' display resolution and the game's resolution to 1920×1080. |
| It says `Paused: switch to the game window` | The game isn't the active window. Click into the game or Alt+Tab to it. |
| Nothing happens at the table | Make sure the "Baseball Cards  E  Play ($50)" prompt is on screen. The game must be in English. If you rebound the interact key, change `press("e")` in `bot.py` to your key and add it to `SCANCODES` (keyboard *scan codes*: E = `0x12`). |
| `Pressed E three times but no match started (out of money?)` | You probably don't have $50 left, or a popup is in the way. Check `debug_shots/`. |
| `Don't recognise the screen for 90s` | A screen the bot doesn't know, such as a popup or tutorial. Deal with it by hand and the bot carries on. A screenshot is saved in `debug_shots/`. |
| It picks strange cards | Check the `hand:` lines in `bot_log.txt`. If numbers are read wrong, please open an issue with the screenshot. |
| `ModuleNotFoundError` | Run `python -m pip install -r requirements.txt` again in the bot folder. |
| `python` is not recognized | Reinstall Python and tick "Add python.exe to PATH", or use `py` instead of `python`. |

### Reporting a problem

`record.py` takes a screenshot every second and logs your clicks while you play a match by hand.
These recordings are what the bot was calibrated with.

```
python record.py
```

> ⚠️ It records your **whole screen**, so close anything private first. The files go to
> `recording/`, which is never uploaded by git.

---

## How the bot works (technical)

- **Screen capture:** [`mss`](https://github.com/BoboTiG/python-mss) grabs the screen a few times per second.
- **Which screen is showing:** small reference images in `templates/` (PLAY, DISCARD, CLOSE, the
  Banned Cards title, the scoreboard) are found with OpenCV template matching. The table prompt
  is read with the **Windows built-in OCR** (`ocr.py`).
- **Reading the hand** (`layout.py`, `vision.py`):
  - The game lays out the hand at fixed positions along a curve, each card tilted a few degrees.
    The bot rotates each card upright, finds the round and shield badges, and recognizes the digit
    in each badge using labelled samples in `train/badges.npz`.
  - A **round badge top-right** is the card's main number (batting or pitching); a **shield below it**
    is speed or fielding.
  - A **badge at the top-centre** marks a booster: round for Power Swing / Pitch Focus, shield for
    Speed Boost / Fielding Play.
  - It reads the hand twice, 0.3 s apart, and only acts when both reads agree, so it doesn't act
    while cards are still moving.
- **Clicking:** Windows `SendInput`, only while the game window is in front. After clicking a
  card, it waits for the game's PLAY button to appear before continuing. That way it never acts
  during the opponent's turn.

---

## Files

| File | Purpose |
|---|---|
| `bot.py` | The bot: start here. |
| `vision.py` | Reads the cards in your hand. |
| `layout.py` | Where each card of the hand sits on a 1920×1080 screen. |
| `ocr.py` | Small wrapper around the Windows built-in OCR. |
| `record.py` | Optional: records a match you play by hand, for calibration and bug reports. |
| `templates/` | Reference images of buttons and screens. |
| `train/badges.npz` | Labelled samples of card number badges. |
| `requirements.txt` | Python packages to install. |

---

## License

[MIT](LICENSE): free to use, modify and share, as long as the license notice stays included.
