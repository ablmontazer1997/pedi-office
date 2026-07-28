"""Turn a raw piece of art into something that stands on the room's grid.

Every sprite we are sent is drawn on its own projection: the desk's top-face
edges run at -0.376 and +0.464, the sofa's at -0.400 and +0.575, and so on. The
room is a single 5:2 isometric. So each sprite is measured — by looking for the
direction its own grain, seams and panel lines run in — and then sheared onto
the room's two axes, with its verticals left vertical.

Measured slopes live in art/assets.json so they can be corrected by hand; the
editor writes to the same file.
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
RAW = os.path.join(ART, "raw")                       # one png per placeable piece
OUT = os.path.join(HERE, "static", "office", "assets")
INDEX = os.path.join(ART, "assets.json")

SLOPE = 0.4                     # the room's own isometric, TH / TW


# ---------------------------------------------------------------- measuring
def _lines(im, lo, hi):
    """How strongly the picture is striped by lines of each slope in the range.

    Shearing the image by -s makes lines of slope s horizontal, and horizontal
    lines show up as variance between row averages. The peak is the slope the
    art is actually drawn on."""
    hp = (np.asarray(im).astype(float)
          - np.asarray(im.filter(ImageFilter.GaussianBlur(8))).astype(float))
    h, w = hp.shape
    xs = np.arange(w)
    best = (0.0, None)
    for s in np.arange(lo, hi, 0.004):
        off = int(abs(s) * w) + 2
        acc = np.zeros(h + 2 * off)
        cnt = np.zeros_like(acc)
        for y in range(h):
            np.add.at(acc, (y + off + s * xs).astype(int), hp[y])
            np.add.at(cnt, (y + off + s * xs).astype(int), 1)
        m = acc / np.maximum(cnt, 1)
        keep = m[cnt > w * 0.3]
        v = float(keep.var()) if keep.size else 0.0
        if v > best[0]:
            best = (v, round(float(s), 3))
    return best


def measure(im):
    """The two top-face slopes of a piece, or None when it is not striped
    enough to tell — a small round pot, say, which needs no shear anyway."""
    g = im.convert("L")
    up, uv = _lines(g, 0.20, 0.70)[::-1]            # rises to the right
    dn, dv = _lines(g, -0.70, -0.20)[::-1]
    if uv < 1.0 or dv < 1.0:
        return None
    if not (0.25 <= up <= 0.75 and 0.25 <= abs(dn) <= 0.75):
        return None       # no real top face, only the noise of leaves or foliage
    if not (0.6 <= up / abs(dn) <= 1.7):
        return None       # the two sides disagree, so one of them is not an edge
    return (-up, -dn)                                # (mA negative, mB positive)


# ---------------------------------------------------------------- warping
def to_room(im, want_w, edges):
    """x' = A x, y' = C x + D y. Both top-face edges land on the room's axes and
    the legs stay vertical. Without measured edges the piece is only scaled."""
    A = want_w / im.width
    if not edges:
        return im.resize((round(im.width * A), round(im.height * A)), Image.LANCZOS)
    mA, mB = edges
    D = 2 * SLOPE * A / (mB - mA)
    C = -SLOPE * A - D * mA
    w = round(A * im.width)
    # the shear tilts the picture either way, so the canvas has to cover both
    # corners of the tilt or one end of the piece is cut off
    top = min(0.0, C * im.width)
    h = round(D * im.height + abs(C) * im.width)
    inv = (1 / A, 0, 0, -C / (A * D), 1 / D, top / D)
    return im.transform((w, h), Image.AFFINE, inv, Image.BICUBIC)


# ---------------------------------------------------------------- library
def load_index():
    return json.load(open(INDEX)) if os.path.exists(INDEX) else {}


def save_index(ix):
    json.dump(ix, open(INDEX, "w"), indent=1, sort_keys=True)


def add(name, src_png, width=None):
    """Register a raw png: measure it, remember the numbers, render it."""
    ix = load_index()
    im = Image.open(src_png).convert("RGBA")
    im = im.crop(im.getbbox())
    im.save(os.path.join(RAW, name + ".png"))
    e = ix.get(name, {}).get("edges", "auto")
    if e == "auto":
        e = measure(im)
    ix[name] = {"edges": e, "width": width or ix.get(name, {}).get("width", 160)}
    save_index(ix)
    render(name, ix[name])
    return ix[name]


def render(name, spec):
    im = Image.open(os.path.join(RAW, name + ".png")).convert("RGBA")
    sp = to_room(im, spec["width"], spec.get("edges"))
    os.makedirs(OUT, exist_ok=True)
    sp.save(os.path.join(OUT, name + ".png"))
    return sp


def rebuild():
    ix = load_index()
    for name, spec in ix.items():
        render(name, spec)
    return ix


def manifest():
    """What the editor needs: every piece, its size on the floor and its
    measured slopes."""
    out = []
    for name, spec in sorted(load_index().items()):
        p = os.path.join(OUT, name + ".png")
        if not os.path.exists(p):
            render(name, spec)
        w, h = Image.open(p).size
        out.append({"name": name, "w": w, "h": h,
                    "width": spec["width"], "edges": spec.get("edges")})
    return out


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    print(json.dumps(rebuild(), indent=1))
