"""Cut the generated isometric rows into single character frames.

The rows come back from the image model on a flat magenta field. A plain
threshold leaves a violet rim, because the model anti-aliases the sprite edge
against that field, so the key here is distance based and then de-spills what is
left: any edge pixel whose red and blue still sit above green is pulled back to
green's level, which is what removes the rim without eating the hoodie.

Each cleaned row is then split on its empty columns and every frame is trimmed
to its own pixels, so the frames land in art/chars/<tag>/ in exactly the shape
build_room.py already expects.
"""
import os
import sys

import numpy as np
from scipy import ndimage
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS = os.path.join(HERE, "art", "chars")

KEY = np.array([255, 0, 255], float)
NEAR, FAR = 75.0, 145.0        # fully keyed below NEAR, fully kept above FAR


def key_out(im):
    """Magenta field -> alpha.

    Judging every pixel by how close it is to magenta cannot work: bright pink
    hair sits only a third of the way from magenta to white, so a colour-only
    key ate it and turned it grey. The background is one flat field instead, so
    it is found by connectivity — the near-magenta region that reaches the edge
    of the sheet is the background, everything walled off inside the sprite is
    the character, whatever colour it happens to be.

    Only the single pixel where the two meet is ambiguous: the model blended the
    outline into the field there. That ring gets a coverage alpha and is
    un-mixed, which is what removes the violet fringe without touching the body.
    """
    a = np.asarray(im.convert("RGB"), float)
    bg = a[0, 0].copy()                       # the field itself, not an assumed magenta
    d = np.sqrt(((a - bg) ** 2).sum(2))

    lab, n = ndimage.label(d < 60, np.ones((3, 3)))
    edge = set(lab[0].tolist()) | set(lab[-1].tolist()) | \
        set(lab[:, 0].tolist()) | set(lab[:, -1].tolist())
    edge.discard(0)
    back = np.isin(lab, list(edge))
    if n:                                      # a pocket of field between an arm
        sizes = ndimage.sum(d < 60, lab, range(1, n + 1))   # and the body is field too
        big = {i + 1 for i, s in enumerate(sizes) if s > 400}
        back |= np.isin(lab, list(big - edge))

    rim = ndimage.binary_dilation(back, np.ones((3, 3))) & ~back
    alpha = np.where(back, 0.0, 1.0)
    cover = np.clip(d / 110.0, 0.2, 1.0)
    alpha = np.where(rim, cover, alpha)

    # un-mix the ring: what is left after the field's share is taken out
    a3 = alpha[..., None]
    mixed = np.clip((a - (1 - a3) * bg) / np.maximum(a3, 0.2), 0, 255)
    out = np.where(rim[..., None], mixed, a)

    return Image.fromarray(np.dstack([out, alpha * 255]).astype(np.uint8), "RGBA")


def frames(im, want=8):
    """Split a row on the transparent columns between the sprites."""
    a = np.asarray(im)[:, :, 3] > 24
    col = a.any(0)
    runs, start = [], None
    for x, on in enumerate(col):
        if on and start is None:
            start = x
        elif not on and start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, len(col)))
    runs = [r for r in runs if r[1] - r[0] > 12]

    # a stray floating icon (the "?" or a zzz) can split off as its own run;
    # merge any run that is much narrower than the median into its neighbour
    if len(runs) > want:
        med = sorted(r[1] - r[0] for r in runs)[len(runs) // 2]
        merged = [list(runs[0])]
        for s, e in runs[1:]:
            if e - s < med * 0.55 and s - merged[-1][1] < med * 0.8:
                merged[-1][1] = e
            elif merged[-1][1] - merged[-1][0] < med * 0.55 and s - merged[-1][1] < med * 0.8:
                merged[-1][1] = e
            else:
                merged.append([s, e])
        runs = [tuple(r) for r in merged]

    out = []
    for s, e in runs:
        f = im.crop((s, 0, e, im.height))
        box = f.getbbox()
        if box:
            out.append(f.crop(box))
    return out


def cut(src, tag, row, want=8):
    im = key_out(Image.open(src))
    fs = frames(im, want)
    d = os.path.join(CHARS, tag)
    os.makedirs(d, exist_ok=True)
    for i, f in enumerate(fs):
        f.save(os.path.join(d, "r%d_%02d.png" % (row, i)))
    return len(fs), [f.size for f in fs]


# row index -> the generated sheet that fills it, keeping build_room's meaning:
# r0 = walking, r1 = at the keyboard, r2 = mug, r3 = asleep
ROWS = [
    ("r0", "walk_S"), ("r1", "type_S"), ("r2", "mug_SE"), ("r3", "sleep_SE"),
    ("r4", "walk_SE"), ("r5", "walk_E"), ("r6", "walk_NE"), ("r7", "walk_N"),
    ("r8", "walk_W"), ("r9", "walk_NW"), ("r10", "walk_SW"),
    ("r11", "type_N"), ("r12", "react_S"),
    ("r13", "sofa_sit_SE"), ("r14", "drink_stand_S"),
]

if __name__ == "__main__":
    gen = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) > 2 else "rade"
    for i, (_, name) in enumerate(ROWS):
        p = os.path.join(gen, name + ".png")
        if not os.path.exists(p):
            print("missing", name)
            continue
        n, sizes = cut(p, tag, i)
        print("%-10s row %-3d %d frames  %s" % (name, i, n, sizes[:3]))
