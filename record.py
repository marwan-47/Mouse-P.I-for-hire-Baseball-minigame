"""Records one match so the bot can be calibrated.

Takes a screenshot every second and logs every mouse click and key press.
Stop it with Ctrl+C in this window, or it stops by itself after 8 minutes.
Output goes to the "recording" folder next to this script.
"""
import ctypes, json, os, time, threading
import mss
from PIL import Image
from pynput import mouse, keyboard

ctypes.windll.shcore.SetProcessDpiAwareness(2)  # real pixel coordinates

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recording")
os.makedirs(OUT, exist_ok=True)
START = time.time()
events = []
lock = threading.Lock()

def log(kind, **kw):
    with lock:
        events.append({"t": round(time.time() - START, 2), "kind": kind, **kw})

def on_click(x, y, button, pressed):
    if pressed:
        log("click", x=x, y=y, button=str(button))
        snap(f"click_{len(events):03d}")

def on_key(key):
    log("key", key=str(key))

sct_lock = threading.Lock()
def snap(name):
    with sct_lock, mss.MSS() as sct:
        img = sct.grab(sct.monitors[1])
        Image.frombytes("RGB", img.size, img.rgb).save(os.path.join(OUT, f"{name}.jpg"), quality=88)

mouse.Listener(on_click=on_click).start()
keyboard.Listener(on_press=on_key).start()

print("Recording starts in 5 seconds. Switch to the game and play one full match.")
time.sleep(5)
i = 0
try:
    while time.time() - START < 8 * 60:
        snap(f"frame_{i:04d}")
        i += 1
        with lock:
            json.dump(events, open(os.path.join(OUT, "events.json"), "w"), indent=1)
        time.sleep(1)
except KeyboardInterrupt:
    pass
with lock:
    json.dump(events, open(os.path.join(OUT, "events.json"), "w"), indent=1)
print(f"Done: {i} screenshots, {len(events)} inputs saved to {OUT}")
