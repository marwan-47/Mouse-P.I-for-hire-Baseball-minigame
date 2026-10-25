"""Where the cards of the player's hand sit on a 1920x1080 screen.

Matches the game's own layout code: cards are spaced evenly around the
screen centre, lifted along a curve and tilted by a few degrees.
"""
import cv2
import numpy as np

SPACING = 171        # px between neighbouring cards
TOP_EDGE_Y = 968     # y of the top badge of the outermost cards
CURVE = 62           # how much higher the middle card sits
MAX_ROT = 5.0        # degrees (measured on screen)


def slots(n):
    """Returns (x, y, angle) of the top-centre badge for each of n cards."""
    out = []
    mid = (n - 1) / 2
    for j in range(n):
        t = (j - mid) / mid if n > 1 else 0.0
        x = 960 + (j - mid) * SPACING
        y = TOP_EDGE_Y - (1 - t * t) * CURVE
        ang = -t * MAX_ROT
        out.append((x, y, ang))
    return out


def upright_card(img, x, y, ang, w=230, h=300):
    """Rotates the screen so the card at (x, y) is upright and crops it.
    The top-centre badge ends up at (w/2, 70) in the crop."""
    M = cv2.getRotationMatrix2D((x, y), -ang, 1.0)
    M[0, 2] += w / 2 - x
    M[1, 2] += 70 - y
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0))


def card_point_to_screen(x, y, ang, px, py, w=230):
    """Maps a point inside an upright crop back to screen coordinates."""
    dx, dy = px - w / 2, py - 70
    a = np.deg2rad(ang)
    # the crop was rotated by -ang, so rotate back by +ang (screen y points down)
    sx = x + dx * np.cos(a) + dy * np.sin(a)
    sy = y - dx * np.sin(a) + dy * np.cos(a)
    return int(round(sx)), int(round(sy))
