"""Wall art for the office: a row of small framed slogans and the light over them.

Everything here is drawn flat, the way it would look face on, and then sheared
onto the wall. The left wall runs one tile across for every 0.4 tiles down, so a
column of the picture drops by that much for every pixel it moves right; a plain
per-column shift keeps the pixels exactly as drawn instead of resampling them
into mush. The little depth on the left edge and the lighter sliver along the
top are the box the sign is, seen from where the room is seen from.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "static", "office", "assets")
META = json.load(open(os.path.join(HERE, "static", "office", "room_meta.json")))
RATIO = META["th"] / META["tw"]          # 0.4: the room's own slope
DX, DY = 8, 3                            # how far a sign stands off the wall

# a 5x7 face, drawn once so the letters land on whole pixels
FONT = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 11011 10001",
    "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    "?": "01110 10001 00001 00010 00100 00000 00100",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    ".": "00000 00000 00000 00000 00000 00000 00100",
    ",": "00000 00000 00000 00000 00000 00100 01000",
    "'": "00100 00100 00000 00000 00000 00000 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
    ":": "00000 00100 00000 00000 00000 00100 00000",
    " ": "00000 00000 00000 00000 00000 00000 00000",
}
GW, GH = 5, 7


# The room is drawn at 1300 across and shown a little smaller than that with
# nearest-neighbour scaling, which simply drops every tenth row and column: a
# one-pixel stroke comes out with holes in it. So every dot of the face is laid
# down as a two-by-two block, which leaves the letters six across and fourteen
# down and every stroke two pixels thick, the same weight the room's own signs
# are drawn at.
ADV, LINE = GW + 2, GH * 2


def text_w(s):
    return len(s) * ADV - 1 if s else 0


def text(d, s, x, y, col):
    for i, ch in enumerate(s.upper()):
        rows = FONT.get(ch, FONT[" "]).split()
        for ry, row in enumerate(rows):
            for rx, on in enumerate(row):
                if on == "1":
                    px, py = x + i * ADV + rx, y + ry * 2
                    d.rectangle([px, py, px + 1, py + 1], col)


def shear(im, ratio=RATIO):
    """slide every column up the wall's slope, pixel for pixel"""
    w, h = im.size
    k = int(round(ratio * (w - 1)))
    out = Image.new("RGBA", (w, h + k), (0, 0, 0, 0))
    for x in range(w):
        out.paste(im.crop((x, 0, x + 1, h)), (x, k - int(round(ratio * x))))
    return out, k


def box(face, k, side=(30, 24, 40), top=(86, 74, 106)):
    """the sign as a slab: its left cheek and the lit strip along its top"""
    w, h = face.size
    out = Image.new("RGBA", (w + DX, h + DY), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    tl, tr = (DX, DY + k), (DX + w - 1, DY)
    bl = (DX, DY + h - 1)
    d.polygon([tl, bl, (bl[0] - DX, bl[1] - DY), (tl[0] - DX, tl[1] - DY)], fill=side)
    d.polygon([tl, tr, (tr[0] - DX, tr[1] - DY), (tl[0] - DX, tl[1] - DY)], fill=top)
    out.alpha_composite(face, (DX, DY))
    return out


def dim(c, f):
    return tuple(int(v * f) for v in c)


def plaque(lines, accent, w=64, h=42):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(40, 32, 52))
    d.line([(0, 0), (w - 1, 0)], fill=(58, 48, 74))
    d.line([(0, 0), (0, h - 1)], fill=(58, 48, 74))
    d.line([(0, h - 1), (w - 1, h - 1)], fill=(22, 16, 30))
    d.line([(w - 1, 0), (w - 1, h - 1)], fill=(22, 16, 30))
    d.rectangle([4, 4, w - 5, h - 5], fill=(17, 13, 25), outline=dim(accent, 0.42))
    # four screws, because a board on a wall has them
    for sx, sy in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        d.point((sx, sy), (96, 84, 118))

    block = len(lines) * LINE + (len(lines) - 1) * 4
    y = 4 + ((h - 8) - block) // 2
    for i, ln in enumerate(lines):
        x = (w - text_w(ln)) // 2
        col = accent if i == 0 else dim(accent, 0.82)
        text(d, ln, x, y + i * (LINE + 4), col)
    return im


def lamp(wf=110, hf=84, bar=(9, 101), y0=6, y1=16):
    im = Image.new("RGBA", (wf, hf), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cxm = wf // 2

    # the cone of light first, so the fitting sits on top of it
    # a cone with a hard edge reads as a grey wedge painted on the bricks, so it
    # fades sideways as well as downwards
    ys = np.arange(hf).reshape(-1, 1)
    xs = np.arange(wf).reshape(1, -1)
    t = np.clip((ys - y1) / float(hf - y1), 0, 1)
    half = 29 + 25 * t
    side = np.clip(1 - (np.abs(xs - cxm) / half) ** 2, 0, 1) ** 1.4
    a = 126 * (1 - t) ** 1.35 * side
    a[: y1 + 1] = 0
    glow = np.zeros((hf, wf, 4), np.uint8)
    glow[:, :, 0], glow[:, :, 1], glow[:, :, 2] = 255, 202, 130
    glow[:, :, 3] = a.astype(np.uint8)
    im.alpha_composite(Image.fromarray(glow, "RGBA"))

    for ax in (bar[0] + 18, bar[1] - 22):
        d.rectangle([ax, 0, ax + 3, y0], fill=(104, 76, 32, 255))
    d.rectangle([bar[0], y0, bar[1], y1], fill=(168, 122, 48, 255))
    d.line([(bar[0], y0), (bar[1], y0)], fill=(214, 163, 66, 255))
    d.line([(bar[0], y0 + 1), (bar[1], y0 + 1)], fill=(192, 142, 56, 255))
    d.line([(bar[0], y1), (bar[1], y1)], fill=(112, 80, 30, 255))
    d.rectangle([bar[0] + 3, y1 + 1, bar[1] - 3, y1 + 1], fill=(255, 244, 208, 255))
    return im, bar, y0


def lamp_asset():
    flat, bar, y0 = lamp()
    face, k = shear(flat)
    w, h = face.size
    out = Image.new("RGBA", (w + DX, h + DY), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    # only the fitting is a solid thing; the light on the wall has no side to it
    p = lambda fx, fy: (DX + fx, DY + fy + k - int(round(RATIO * fx)))
    tl, tr = p(bar[0], y0), p(bar[1], y0)
    bl = p(bar[0], y0 + 10)
    d.polygon([tl, bl, (bl[0] - DX, bl[1] - DY), (tl[0] - DX, tl[1] - DY)], fill=(96, 68, 28))
    d.polygon([tl, tr, (tr[0] - DX, tr[1] - DY), (tl[0] - DX, tl[1] - DY)], fill=(228, 178, 78))
    out.alpha_composite(face, (DX, DY))
    return out


SIGNS = [
    ("sign_works", ["IT WORKS", "ON MY PC"], (124, 196, 255)),
    ("sign_friday", ["SHIP IT", "FRIDAY!"], (255, 176, 32)),
    ("sign_bugs", ["0 BUGS", "SO FAR"], (94, 240, 138)),
]


def place(px, wc, hb):
    """where to hang a sprite so its lowest row sits `hb` above the floor seam"""
    return int(round(META["cy"] + RATIO * (META["cx"] - px)
                     + RATIO * wc / 2 - RATIO * DX - hb))


def main():
    made = []
    for name, lines, accent in SIGNS:
        face, k = shear(plaque(lines, accent))
        im = box(face, k)
        im.save(os.path.join(OUT, name + ".png"))
        made.append((name, im.size))
    lam = lamp_asset()
    lam.save(os.path.join(OUT, "wall_lamp.png"))
    made.append(("wall_lamp", lam.size))
    for n, s in made:
        print("%-12s %dx%d" % (n, s[0], s[1]))
    print("hang at:", [(n, place(px, s[0], 78))
                       for (n, s), px in zip(made[:3], (218, 302, 386))],
          ("wall_lamp", place(302, lam.size[0], 63)))


if __name__ == "__main__":
    main()
