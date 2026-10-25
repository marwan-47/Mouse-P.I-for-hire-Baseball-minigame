"""Plays the Baseball Cards minigame in MOUSE: P.I. For Hire until you reach a win target.

Usage (game in 1920x1080 fullscreen, standing at the Baseball Cards table):
    python bot.py                  # play until 30 baseball wins in total
    python bot.py --target 30 --max-matches 40
    python bot.py --dry-run        # only look and print decisions, never click

Stop it any time with F10, or by moving the mouse into the top-left corner of the screen.
It only clicks while the game window is in front, so Alt+Tab away pauses it.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import datetime
import glob
import json
import os
import time

import cv2
import mss
import numpy as np

import ocr
import vision

ctypes.windll.shcore.SetProcessDpiAwareness(2)
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(os.environ["USERPROFILE"], r"AppData\LocalLow\Fumi Games\MOUSE\Save\profile.rsf")
LOG = os.path.join(HERE, "bot_log.txt")
SHOTS = os.path.join(HERE, "debug_shots")

# ---------------------------------------------------------------- helpers


def log(msg):
    line = f"{datetime.datetime.now():%H:%M:%S}  {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_shot(img, tag):
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, f"{datetime.datetime.now():%H%M%S}_{tag}.jpg")
    cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return path


def baseball_wins():
    """Total Baseball Cards wins, read from the game's profile file."""
    for _ in range(5):
        try:
            with open(PROFILE, encoding="utf-8") as f:
                return int(json.load(f)["g"]["BaseballCards"])
        except (OSError, ValueError, KeyError):
            time.sleep(0.3)
    return None


# ---------------------------------------------------------------- screen

_sct = mss.MSS()


def grab():
    shot = _sct.grab(_sct.monitors[1])
    return cv2.cvtColor(np.asarray(shot), cv2.COLOR_BGRA2BGR)


TEMPLATES = {os.path.basename(p)[:-4]: cv2.imread(p, 0) for p in glob.glob(os.path.join(HERE, "templates", "*.png"))}
# where on the screen each template is searched for: (y0, y1, x0, x1)
REGIONS = {
    "play": (880, 1000, 100, 520),
    "discard": (880, 1000, 1400, 1850),
    "close": (980, 1080, 1650, 1920),
    "banned": (120, 280, 500, 1400),
    "ban_play": (880, 1020, 700, 1250),
    "scoreboard": (150, 320, 20, 300),
}


def find(gray, name, threshold=0.7):
    """Returns the screen centre of a template if it is visible, else None."""
    y0, y1, x0, x1 = REGIONS[name]
    t = TEMPLATES[name]
    res = cv2.matchTemplate(gray[y0:y1, x0:x1], t, cv2.TM_CCOEFF_NORMED)
    _, score, _, (x, y) = cv2.minMaxLoc(res)
    if score < threshold:
        return None
    return x0 + x + t.shape[1] // 2, y0 + y + t.shape[0] // 2


def hand_raised(gray):
    return gray[960:1060, 640:1280].mean() > 110


def at_table(img):
    text = ocr.read_text(img[560:820, 500:1420], 2)
    return "Baseball Cards" in text


# ---------------------------------------------------------------- input

INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
MOUSEEVENTF_MOVE, MOUSEEVENTF_ABSOLUTE = 0x0001, 0x8000
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
KEYEVENTF_SCANCODE, KEYEVENTF_KEYUP = 0x0008, 0x0002
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD), ("time", wt.DWORD),
                ("dwExtraInfo", ULONG_PTR)]


class _U(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("pad", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def _send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _mouse(flags, x=0, y=0):
    i = INPUT(type=INPUT_MOUSE)
    i.u.mi = MOUSEINPUT(x, y, 0, flags, 0, 0)
    return i


def move(x, y):
    if DRY_RUN:
        return
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    ax, ay = int(x * 65535 / (sw - 1)), int(y * 65535 / (sh - 1))
    _send(_mouse(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, ax, ay))


DRY_RUN = False


def click(x, y, what=""):
    if DRY_RUN:
        log(f"  [dry-run] would click {what} at ({x}, {y})")
        return
    move(x, y)
    time.sleep(0.08)
    _send(_mouse(MOUSEEVENTF_LEFTDOWN))
    time.sleep(0.06)
    _send(_mouse(MOUSEEVENTF_LEFTUP))
    time.sleep(0.15)


SCANCODES = {"e": 0x12, "f": 0x21}


def press(key):
    if DRY_RUN:
        log(f"  [dry-run] would press {key.upper()}")
        return
    sc = SCANCODES[key]
    down = INPUT(type=INPUT_KEYBOARD)
    down.u.ki = KEYBDINPUT(0, sc, KEYEVENTF_SCANCODE, 0, 0)
    up = INPUT(type=INPUT_KEYBOARD)
    up.u.ki = KEYBDINPUT(0, sc, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, 0)
    _send(down)
    time.sleep(0.08)
    _send(up)


# ---------------------------------------------------------------- safety


class Stop(Exception):
    pass


VK_F10 = 0x79


def check_stop():
    if user32.GetAsyncKeyState(VK_F10) & 0x8000:
        raise Stop("F10 pressed")
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    if pt.x <= 2 and pt.y <= 2:
        raise Stop("mouse moved to the top-left corner")


def game_window():
    return user32.FindWindowW(None, "MOUSE")


def game_in_front():
    hwnd = game_window()
    return hwnd and user32.GetForegroundWindow() == hwnd


def sleep(sec):
    end = time.time() + sec
    while time.time() < end:
        check_stop()
        time.sleep(0.05)


def check_permissions():
    """Windows blocks clicks into a game that runs as admin unless this script does too."""
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    hwnd = game_window()
    if not hwnd:
        return True
    pid = wt.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    PROCESS_QUERY_INFORMATION, PROCESS_VM_READ = 0x0400, 0x0010
    h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid.value)
    if h:
        kernel32.CloseHandle(h)
        return True
    return False


# ---------------------------------------------------------------- strategy


def describe(c):
    if c["kind"] == "main":
        return f"card {c['value']}/{c['extra']}"
    if c["kind"] == "tactic":
        return f"{'power' if c['style'] == 'C' else 'speed/fielding'} +{c['value']}"
    return "?"


def choose(cards):
    """Strongest batter/pitcher, plus the best booster.
    Boosters that add to the main number (Power Swing / Pitch Focus, round badge) come first,
    then Speed Boost / Fielding Play (shield badge)."""
    mains = [c for c in cards if c["kind"] == "main"]
    if not mains:
        return None, None
    main = max(mains, key=lambda c: (c["value"], c["extra"]))
    tactics = [c for c in cards if c["kind"] == "tactic"]
    tactic = max(tactics, key=lambda c: (c["style"] == "C", c["value"]), default=None)
    return main, tactic


def read_stable_hand():
    """Reads the hand twice to make sure the cards have stopped moving."""
    img1 = grab()
    n = vision.hand_count(img1)
    a = vision.read_hand(img1, n)
    sleep(0.3)
    img2 = grab()
    b = vision.read_hand(img2, n)
    key = lambda h: [(c["kind"], c.get("value"), c.get("extra"), c.get("style")) for c in h]
    if key(a) != key(b):
        return None, img2
    return b, img2


# ---------------------------------------------------------------- one turn


def play_turn(stats):
    move(960, 420)  # keep the cursor off the cards while reading them
    sleep(0.25)
    cards, img = read_stable_hand()
    if not cards:
        return False
    unreadable = sum(1 for c in cards if not c["kind"])
    if unreadable:
        # cards are probably still being dealt; give it a few tries before playing anyway
        stats["unreadable_tries"] = stats.get("unreadable_tries", 0) + 1
        if stats["unreadable_tries"] < 6:
            return False
        save_shot(img, "unreadable_hand")
    stats["unreadable_tries"] = 0
    main, tactic = choose(cards)
    if not main:
        return False
    hand = ", ".join(describe(c) for c in cards)
    click(*main["click"], what="main card")
    # the PLAY button only shows up once it is really our turn and the card got selected
    for _ in range(8):
        sleep(0.15)
        if DRY_RUN or find(cv2.cvtColor(grab(), cv2.COLOR_BGR2GRAY), "play"):
            break
    else:
        return False  # not our turn yet; nothing was selected
    if tactic:
        click(*tactic["click"], what="booster")
        sleep(0.3)
    gray = cv2.cvtColor(grab(), cv2.COLOR_BGR2GRAY)
    at = find(gray, "play") or (320, 940)
    log(f"  hand: {hand}  ->  play {describe(main)}" + (f" + {describe(tactic)}" if tactic else ""))
    click(*at, what="PLAY")
    stats["turns"] += 1
    sleep(1.5)
    return True


# ---------------------------------------------------------------- main loop


def run(target, max_matches):
    wins = baseball_wins()
    log(f"Starting. Baseball wins so far: {wins}. Target: {target}. Max matches this run: {max_matches}.")
    if wins is not None and wins >= target:
        log("Target already reached, nothing to do.")
        return
    stats = {"matches": 0, "wins": 0, "turns": 0}
    wins_at_match_start = wins
    unknown_since = None
    waiting_logged = False
    table_presses = 0

    while True:
        check_stop()
        if not DRY_RUN and not game_in_front():
            if not waiting_logged:
                log("Paused: switch to the game window (Alt+Tab) and I'll continue.")
                waiting_logged = True
            sleep(0.5)
            continue
        if waiting_logged:
            log("Game is in front, continuing.")
            waiting_logged = False

        img = grab()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 1. result screen
        at = find(gray, "close")
        if at:
            if stats.get("result_logged_for") == stats["matches"]:
                # same result screen still showing after the first CLOSE click
                click(*at, what="CLOSE")
                sleep(2.5)
                continue
            stats["result_logged_for"] = stats["matches"]
            sleep(1.0)
            now = baseball_wins()
            won = now is not None and wins_at_match_start is not None and now > wins_at_match_start
            stats["wins"] += int(won)
            log(f"Match over: {'WIN' if won else 'no win (loss or draw)'}. "
                f"This run: {stats['wins']}/{stats['matches']} won. Total baseball wins: {now}.")
            save_shot(img, "result_" + ("win" if won else "nowin"))
            click(*at, what="CLOSE")
            sleep(2.5)
            unknown_since = None
            if now is not None and now >= target:
                log(f"Target of {target} wins reached. Done!")
                return
            continue

        # 2. card banning screen before a match: ban nothing, just start
        if find(gray, "banned"):
            at = find(gray, "ban_play") or (960, 948)
            log("Banning screen -> PLAY")
            click(*at, what="binder PLAY")
            sleep(2.0)
            unknown_since = None
            continue

        # 3. inside a match
        if find(gray, "scoreboard"):
            unknown_since = None
            table_presses = 0
            if find(gray, "play"):
                # something is already selected (e.g. after a hiccup): just play it
                log("  PLAY already showing -> pressing it")
                click(*find(gray, "play"), what="PLAY")
                sleep(1.5)
            elif hand_raised(gray):
                if not play_turn(stats):
                    sleep(0.5)
            else:
                sleep(0.4)
            continue

        # 4. standing at the table
        if at_table(img):
            unknown_since = None
            if stats["matches"] >= max_matches:
                log(f"Played {max_matches} matches this run, stopping as asked.")
                return
            if table_presses >= 3:
                log("Pressed E three times but no match started (out of money?). Stopping.")
                save_shot(img, "table_stuck")
                return
            wins_at_match_start = baseball_wins()
            stats["matches"] += 1
            table_presses += 1
            log(f"--- Match {stats['matches']} (total wins {wins_at_match_start}) ---")
            press("e")
            sleep(4.0)
            continue

        # 5. something else (animation, loading...)
        if unknown_since is None:
            unknown_since = time.time()
        elif time.time() - unknown_since > 90:
            log(f"Don't recognise the screen for 90s, saved {save_shot(img, 'unknown')}")
            unknown_since = time.time()
        sleep(0.4)


def main():
    global DRY_RUN
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=30, help="total baseball wins to reach")
    ap.add_argument("--max-matches", type=int, default=40, help="never start more matches than this")
    ap.add_argument("--dry-run", action="store_true", help="look and log, but never click")
    ap.add_argument("--delay", type=float, default=5, help="seconds to wait before starting")
    a = ap.parse_args()
    DRY_RUN = a.dry_run
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    if (sw, sh) != (1920, 1080):
        print(f"Your main screen is {sw}x{sh}. This bot only works at 1920x1080 "
              "(set the game and Windows display to 1920x1080).")
        return
    if not DRY_RUN and not check_permissions():
        print("The game runs as administrator, so Windows blocks this script's clicks.\n"
              "Either run this terminal as administrator, or untick 'Run this program as an administrator'\n"
              "in MOUSE.exe > Properties > Compatibility and restart the game.")
        return
    print(f"Starting in {a.delay:.0f}s - switch to the game now. Stop: F10 or mouse to top-left corner.")
    time.sleep(a.delay)
    try:
        run(a.target, a.max_matches)
    except Stop as e:
        log(f"Stopped: {e}")
    except KeyboardInterrupt:
        log("Stopped with Ctrl+C")


if __name__ == "__main__":
    main()
