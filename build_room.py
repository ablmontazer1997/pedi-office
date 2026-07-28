"""Step 1 of rebuilding the office: the floor and the two walls only.

The two pictures we were given do not share one projection. The floor sheet is
drawn on a 174x97 diamond and the wall segment runs at a 1:0.48 slope, while the
reference shot is a clean 2:1 isometric on a 64x32 grid. So both assets are
warped onto one 2:1 grid here before anything is laid out: after that a wall
course and a floor edge run exactly parallel, which is the thing the eye checks.

Nothing is invented — the bricks and the tiles are the supplied pixels, only
rescaled.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
OUT = os.path.join(HERE, "static", "office")

# frame and grid: the reference is 1844x1128 on a 64 wide tile, this is the same
# room at 0.7 of that size
W, H = 1300, 795
# a softer iso than 2:1 (5:2), so the back of the room reads as further away
TW, TH = 45, 18

# the inside corner where the two walls meet, pushed right up into the frame
CX, CY_TOP = 726, 6

FLOOR_SLOPE = 0.615        # measured on the supplied floor sheet, not guessed
BRICK_W = 100              # brick width along the wall in the supplied segment
BRICK = 40                 # ... and how wide it is drawn here: under one floor
                           # tile, which is what puts the wall in the distance
WALL_SLOPE = 0.4797        # measured on that segment
COURSE = 68                # brick course height in that segment
EXTRA = 0                  # extra courses: the reference wall is taller than one segment


KX = BRICK / BRICK_W
KY = KX * (TH / TW) / WALL_SLOPE       # the y stretch that puts courses on the grid
STEP = (BRICK, round(BRICK * TH / TW))  # one brick along the axis


def base_y(x):
    """floor level at column x: the seam both walls stand on"""
    return CY_BASE + abs(x - CX) * (TH / TW)


# ---------------------------------------------------------------- floor
def floor(im):
    """The supplied floor sheet, untouched, at its own width so the tiles keep
    the size they are drawn at. It is shorter than the room, so it carries on
    downwards by whole lattice rows and the copies fade into each other — the
    pixels stay exactly as they arrived, only where one copy ends is softened."""
    f = Image.open(os.path.join(ART, "floor2.png")).convert("RGBA")
    a = np.asarray(f)[:, :, 3]
    solid = np.nonzero((a > 250).all(1))[0]          # rows with no transparent gap
    f = f.crop((0, solid.min(), f.width, solid.max() + 1)).convert("RGB")

    # squash so the sheet's 0.57 diamonds line up with the walls' 0.4 slope
    r = (TH / TW) / FLOOR_SLOPE
    k = W / f.width
    f = f.resize((W, round(f.height * k * r)), Image.LANCZOS).convert("RGBA")
    dia = 186 * k * r * FLOOR_SLOPE                  # a diamond's height after that

    step = round(dia * int(f.height * 0.6 / dia))    # whole rows, ~40% overlap
    ramp = Image.linear_gradient("L").resize((W, f.height - step))
    lay = Image.new("RGBA", (W, H))
    y, first = CY_BASE, True
    while y < H:
        c = f.copy()
        if not first:                                # fade this copy in on top
            m = Image.new("L", f.size, 255)
            m.paste(ramp, (0, 0))
            c.putalpha(m)
        lay.alpha_composite(c, (0, round(y)))
        y += step
        first = False

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(
        [(0, H), (0, base_y(0)), (CX, CY_BASE), (W, base_y(W)), (W, H)], fill=255)
    lay.putalpha(Image.composite(lay.getchannel("A"), Image.new("L", (W, H), 0), mask))
    im.alpha_composite(lay)


# ---------------------------------------------------------------- wall
def wall_slab():
    """One brick-wide vertical slice of the segment, warped so its courses run
    at exactly 2:1. Repeating it along the axis rebuilds a wall of any length —
    a whole brick step maps every course back onto itself, so the bond keeps
    running instead of restarting."""
    s = Image.open(os.path.join(ART, "wall_seg.png")).convert("RGBA")
    s = s.resize((round(s.width * KX), round(s.height * KY)), Image.LANCZOS)
    x0 = round(820 * KX)                  # a clean interior slice, no end caps
    return s.crop((x0, 0, x0 + STEP[0], s.height))


def walls(im):
    slab = wall_slab()
    bw, bh = STEP
    a = np.asarray(slab)[:, :, 3] > 40
    foot = np.nonzero(a[:, bw // 2])[0].max()      # base of that slice
    steps = W // bw + 2
    for flip in (False, True):
        sp = slab.transpose(Image.FLIP_LEFT_RIGHT) if flip else slab
        for i in range(steps):
            x = CX + (-bw * (i + 1) if flip else bw * i)
            if x + bw < 0 or x > W:
                continue
            # the slab is placed by its middle column, so both walls sit at
            # the same height where they meet: half a brick from the corner
            y = round(CY_BASE + bh * (i + 0.5)) - foot
            im.alpha_composite(sp, (x, y))


def shadow(im):
    """the soft dark line the wall drops onto the floor"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(16):
        a = int(90 * (1 - k / 16) ** 2)
        d.line([(0, base_y(0) + k), (CX, CY_BASE + k), (W, base_y(W) + k)],
               fill=(8, 5, 14, a), width=3)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))


def light(im):
    """a warm pool in the middle of the room and dark corners, like the shot"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for r in range(70, 0, -1):
        a = int(30 * (1 - r / 70) ** 2)
        d.ellipse([CX - r * 12, 300 - r * 5, CX + r * 12, 300 + r * 5],
                  fill=(255, 208, 150, a))
    for i in range(120):
        a = int(96 * (1 - i / 120) ** 2)
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(5, 3, 11, a))
    im.alpha_composite(lay)


CY_BASE = 0     # filled in by build(), the floor level at the corner


def build():
    global CY_BASE
    slab = wall_slab()
    a = np.asarray(slab)[:, :, 3] > 40
    col = np.nonzero(a[:, STEP[0] // 2])[0]
    CY_BASE = CY_TOP + (col.max() - col.min())

    os.makedirs(OUT, exist_ok=True)
    bg = Image.new("RGBA", (W, H), (14, 11, 22, 255))
    floor(bg)
    walls(bg)
    shadow(bg)
    bg.convert("RGB").save(os.path.join(OUT, "room_bg.png"))   # what the editor draws on
    json.dump({"w": W, "h": H, "tw": TW, "th": TH, "cx": CX, "cy": int(CY_BASE)},
              open(os.path.join(OUT, "room_meta.json"), "w"))

    im = bg.copy()
    props(im)
    light(im)
    im.convert("RGB").save(os.path.join(OUT, "room_base.png"))
    print("->", os.path.join(OUT, "room_base.png"), im.size,
          "corner base y", CY_BASE, "wall px", col.max() - col.min())


# ---------------------------------------------------------------- furniture
# Where each piece stands comes from layout.json, which the editor page writes.
# The pieces themselves are prepared by assets.py: measured, sheared onto the
# room's grid and saved ready to paste.
LAYOUT = os.path.join(HERE, "layout.json")


def props(im):
    """Everything standing on the floor, painted back to front."""
    if not os.path.exists(LAYOUT):
        return
    items = []
    for i, it in enumerate(json.load(open(LAYOUT))):
        sp = Image.open(os.path.join(OUT, "assets", it["asset"] + ".png")).convert("RGBA")
        if it.get("flip"):
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        # z is the editor's layer override; how far down the piece stands decides
        # the rest, which is what depth on a floor means
        z = it.get("z", 0)
        items.append((z, it["y"], i, sp, it["x"]))
    for _, y, _, sp, x in sorted(items, key=lambda t: t[:3]):
        im.alpha_composite(sp, (round(x - sp.width / 2), round(y - sp.height)))



if __name__ == "__main__":
    build()
