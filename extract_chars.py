"""Cut the two hand-made character sheets into frames.

Unlike the AI pack these arrive as clean PNGs with a real alpha channel, so a
frame is simply a connected run of opaque pixels: split into row bands first,
then into columns inside each band.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "art", "chars")
INBOX = "/home/rade/.claude/channels/telegram-gorzali/inbox/"

SHEETS = {
    # sheet A is a 2x upscale of its native art, sheet B is already native
    "a": (INBOX + "1785137897745-AgAD0R0AAkfmOFM.png", 2),
    "b": (INBOX + "1785137910588-AgAD0h0AAkfmOFM.png", 1),
}
# the sleep row and the emote row of sheet A touch, so that band is split by hand
SPLIT = {"a": [(1202, 1560), (1565, 1905)]}


def bands(v, gap):
    out, s, g = [], None, 0
    for i, x in enumerate(v):
        if x:
            if s is None:
                s = i
            g = 0
        elif s is not None:
            g += 1
            if g > gap:
                out.append((s, i - g))
                s = None
    if s is not None:
        out.append((s, len(v) - 1))
    return out


def cut(tag):
    path, up = SHEETS[tag]
    im = Image.open(path).convert("RGBA")
    if up != 1:
        im = im.resize((im.width // up, im.height // up), Image.NEAREST)
    a = np.asarray(im)
    m = a[:, :, 3] > 40
    rows = bands(m.any(1), 20 // up)
    rows = [r for r in rows for r in (SPLIT.get(tag, {}) and [])] or rows
    if tag in SPLIT:
        rows = [(y0 // up, y1 // up) for y0, y1 in SPLIT[tag]] + \
               [r for r in rows if r[1] < SPLIT[tag][0][0] // up]
        rows.sort()
    d = os.path.join(OUT, tag)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    grid = []
    for ri, (y0, y1) in enumerate(rows):
        cols = bands(m[y0:y1 + 1].any(0), 12 // up)
        row = []
        for ci, (x0, x1) in enumerate(cols):
            sp = im.crop((x0, y0, x1 + 1, y1 + 1))
            sp = sp.crop(sp.getbbox())
            name = "r%d_%02d" % (ri, ci)
            sp.save(os.path.join(d, name + ".png"))
            row.append((name, sp))
        grid.append(row)
        print(tag, "row", ri, len(row), "frames", [s.size for _, s in row][:3])
    contact(tag, grid)


def contact(tag, grid):
    cell = max(max(s.width for _, s in r) for r in grid) + 16
    cellh = max(max(s.height for _, s in r) for r in grid) + 30
    cols = max(len(r) for r in grid)
    sheet = Image.new("RGB", (cell * cols, cellh * len(grid)), (28, 24, 44))
    d = ImageDraw.Draw(sheet)
    for ri, row in enumerate(grid):
        for ci, (name, sp) in enumerate(row):
            x, y = ci * cell, ri * cellh
            sheet.paste(sp, (x + (cell - sp.width) // 2, y + 26 + (cellh - 30 - sp.height)), sp)
            d.rectangle([x, y, x + cell - 1, y + cellh - 1], outline=(64, 56, 96))
            d.text((x + 6, y + 8), "%s %dx%d" % (name, sp.width, sp.height), fill=(255, 216, 88))
    sheet.save(os.path.join(OUT, "contact_%s.png" % tag))
    print("->", os.path.join(OUT, "contact_%s.png" % tag), sheet.size)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for t in (sys.argv[1:] or list(SHEETS)):
        cut(t)


# ---------------------------------------------------------------- game poses
# These two characters bring their own chair, desk and monitor, so a slot that
# uses one needs no baked desk under it. The desk only exists in the typing
# frames, so it is cut out once and re-pasted in front of the other poses.
GAME = os.path.join(HERE, "static", "office", "spr")

CHARS = {
    # sprite slot -> sheet, downscale, desk box inside the typing frame
    4: {"tag": "a", "k": 1, "desk": (82, 60, 154, 148),
        "type_a": "r1_00", "type_a2": "r1_03", "sit": "r2_05", "sleep": "r3_01",
        "walk": ["r0_00", "r0_02", "r0_05", "r0_07"],
        # nudge the desk clear of the mug the seated pose holds
        "adj": {"type_b": (28, 0), "sleep": (6, 0)}},
    5: {"tag": "b", "k": 2, "desk": (178, 118, 330, 282),
        "type_a": "r1_00", "type_a2": "r1_03", "sit": "r2_00", "sleep": "r3_01",
        "walk": ["r0_00", "r0_02", "r0_05", "r0_07"],
        "adj": {"type_b": (20, 0), "sleep": (8, 0)}},
}
BUBBLE = ("a", "r4_08", (0, 0, 93, 62))      # the white ✕ speech bubble


def fr(tag, name):
    return Image.open(os.path.join(OUT, tag, name + ".png")).convert("RGBA")


def half(im, k):
    return im if k == 1 else im.resize((im.width // k, im.height // k), Image.BOX)


def head_x(im):
    """centre of the topmost slab of the sprite — the head, our one landmark
    that survives every pose"""
    a = np.asarray(im)[:, :, 3] > 40
    top = a[:max(12, im.height // 12)]
    xs = np.nonzero(top.any(0))[0]
    return (xs.min() + xs.max()) / 2 if len(xs) else im.width / 2


def compose(body, desk, dx, dy):
    """body with the desk in front; both are anchored bottom-left of the result"""
    w = max(body.width, dx + desk.width)
    h = max(body.height, dy + desk.height)
    out = Image.new("RGBA", (w, h))
    out.alpha_composite(body, (0, h - body.height))
    out.alpha_composite(desk, (dx, dy))
    return out.crop(out.getbbox())


def poses():
    os.makedirs(GAME, exist_ok=True)
    bub = half(fr(*BUBBLE[:2]).crop(BUBBLE[2]), 1)
    for slot, c in CHARS.items():
        k = c["k"]
        typ = half(fr(c["tag"], c["type_a"]), k)
        typ2 = half(fr(c["tag"], c["type_a2"]), k)
        dbox = [v // k for v in c["desk"]]
        desk = typ.crop(dbox)
        # where the desk sits relative to the typing frame's head and floor
        hx, foot = head_x(typ), typ.height
        out = {"type_a": typ, "type_a2": typ2, "error": None}
        for name in ("sit", "sleep"):
            body = half(fr(c["tag"], c[name]), k)
            key = "type_b" if name == "sit" else "sleep"
            ax, ay = c.get("adj", {}).get(key, (0, 0))
            dx = int(round(dbox[0] - hx + head_x(body))) + ax
            dy = int(round(max(body.height, dbox[3]) - (foot - dbox[1]))) + ay
            out[key] = compose(body, desk, max(0, dx), max(0, dy))
        # the bubble floats clear above the head instead of sitting on the hair
        err = Image.new("RGBA", (typ.width, typ.height + bub.height - 18))
        err.alpha_composite(typ, (0, bub.height - 18))
        err.alpha_composite(bub, (max(0, int(head_x(typ)) - bub.width + 20), 0))
        out["error"] = err
        for name, im in out.items():
            im.save(os.path.join(GAME, "bot%d_%s.png" % (slot, name)))
        for i, w in enumerate(c["walk"]):
            half(fr(c["tag"], w), k).save(os.path.join(GAME, "bot%d_walk%d.png" % (slot, i)))
        print("slot", slot, {n: im.size for n, im in out.items()})
