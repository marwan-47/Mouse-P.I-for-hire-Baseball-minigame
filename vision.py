"""Reads the player's hand from a 1920x1080 screenshot."""
import os
import cv2
import numpy as np
import layout

_HERE = os.path.dirname(os.path.abspath(__file__))
_data = np.load(os.path.join(_HERE, "train", "badges.npz"))
_POS = _data["pos"].astype(np.float32)
_POS_LABELS = list(_data["pos_labels"])
_NEG = _data["neg"].astype(np.float32)
R = 22           # badge templates are 44x44
PAD = 4          # allow a few px of misalignment


def _normalize(stack):
    flat = stack.reshape(len(stack), -1)
    flat = flat - flat.mean(axis=1, keepdims=True)
    flat /= (np.linalg.norm(flat, axis=1, keepdims=True) + 1e-6)
    return flat

_POS_N = _normalize(_POS)
_NEG_N = _normalize(_NEG)
RI = 14          # inner square that holds just the digit
_POS_IN = _normalize(_POS[:, R - RI:R + RI, R - RI:R + RI])


def _classify(gray, x, y):
    """Best (label, score) for a badge candidate centred near (x, y)."""
    best_label, best_pos, best_neg = None, -1.0, -1.0
    for dy in range(-PAD, PAD + 1, 2):
        for dx in range(-PAD, PAD + 1, 2):
            cx, cy = x + dx, y + dy
            if cy - R < 0 or cx - R < 0 or cy + R > gray.shape[0] or cx + R > gray.shape[1]:
                continue
            patch = gray[cy - R:cy + R, cx - R:cx + R].astype(np.float32)
            p = _normalize(patch[None])[0]
            sp = float((_POS_N @ p).max())
            sn = float((_NEG_N @ p).max())
            if sp > best_pos:
                best_pos, best_at = sp, patch
            best_neg = max(best_neg, sn)
    if best_pos < 0:
        return None, -1.0, -1.0
    # decide which digit it is from the centre only, allowing a small shift
    inner = _normalize(best_at[None, R - RI:R + RI, R - RI:R + RI])[0]
    best_label, best_in = None, -1.0
    for dy in (-2, 0, 2):
        for dx in (-2, 0, 2):
            sub = best_at[R - RI + dy:R + RI + dy, R - RI + dx:R + RI + dx]
            if sub.shape != (2 * RI, 2 * RI):
                continue
            s = _POS_IN @ _normalize(sub[None])[0]
            i = int(s.argmax())
            if s[i] > best_in:
                best_in, best_label = float(s[i]), _POS_LABELS[i]
    return best_label, best_pos, best_neg


def find_badges(card_bgr):
    """Returns [(style, value, x, y, score)] for badges on an upright card crop.
    style is 'C' (round badge) or 'S' (shield badge)."""
    gray = cv2.cvtColor(card_bgr, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(cv2.medianBlur(gray, 3), cv2.HOUGH_GRADIENT, dp=1, minDist=30,
                               param1=120, param2=22, minRadius=16, maxRadius=24)
    found = []
    if circles is None:
        return found
    for x, y, _ in circles[0]:
        x, y = int(x), int(y)
        if x < 70:
            continue  # neighbouring card's badges peek in on the left
        label, sp, sn = _classify(gray, x, y)
        if label and sp > 0.72 and sp > sn + 0.03:
            found.append((label[0], int(label[1:]), x, y, round(sp, 3)))
    # drop duplicates that hit the same badge
    found.sort(key=lambda b: -b[4])
    out = []
    for b in found:
        if all(abs(b[2] - o[2]) > 18 or abs(b[3] - o[3]) > 18 for o in out):
            out.append(b)
    return out


def read_card(card_bgr):
    """Describes one card: {'kind': 'main'|'tactic'|None, ...}."""
    badges = find_badges(card_bgr)
    right = [b for b in badges if b[2] >= 150]
    centre = [b for b in badges if 85 <= b[2] < 150]
    circles = sorted([b for b in right if b[0] == "C"], key=lambda b: b[3])
    if circles:
        main = circles[0]
        shields = [b for b in right if b[0] == "S" and b[3] > main[3] + 20]
        return {"kind": "main", "value": main[1], "extra": shields[0][1] if shields else 0,
                "badge": (main[2], main[3])}
    if centre:
        b = max(centre, key=lambda b: b[4])
        return {"kind": "tactic", "style": b[0], "value": b[1], "badge": (b[2], b[3])}
    return {"kind": None, "badges": badges}


def read_hand(screen_bgr, n=5):
    """Reads all n cards in the hand. Each entry also has 'click': a screen point on that card."""
    cards = []
    for j, (x, y, ang) in enumerate(layout.slots(n)):
        crop = layout.upright_card(screen_bgr, x, y, ang)
        info = read_card(crop)
        info["slot"] = j
        # click a bit below the top badge, in the middle of the card's visible area
        bx, by = info.get("badge", (115, 70))
        info["click"] = layout.card_point_to_screen(x, y, ang, 100, by + 60)
        cards.append(info)
    return cards


def hand_count(screen_bgr):
    """Tries hand sizes 5..1 and returns the one whose cards read best."""
    best_n, best_known = 5, -1
    for n in (5, 4, 3, 2, 1):
        known = sum(1 for c in read_hand(screen_bgr, n) if c["kind"])
        if known == n:
            return n
        if known > best_known:
            best_n, best_known = n, known
    return best_n
