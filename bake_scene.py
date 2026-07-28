"""Bake everything the live room page needs out of layout.json.

The page cannot ask for /api/layout (that route is behind the token) and it must
not guess where a desk ends, so the geometry is worked out here once and written
next to the art as scene.json:

  props      what to draw and in which order, same rule build_room.py bakes with
  blocked    a coarse grid of cells the character may not stand in, taken from
             the bottom band of each sprite, which is the part that touches the
             floor
  spots      the places the behaviour code aims at: the free chairs, the sofa
             seat and the coffee counter

The character frames are copied under static/ too, with their trimmed sizes, so
the page can anchor every frame on its own feet.
"""
import json
import os
import shutil

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
OUT = os.path.join(HERE, "static", "office")
LAYOUT = os.path.join(HERE, "layout.json")

CELL = 10                      # collision cell, in room pixels
FOOT = 0.62                    # bottom fraction of a sprite that stands on the floor.
                               # A desk sprite is 151 px tall but the monitor and
                               # the plant on it are drawn *above* the floor, not
                               # on it: only the body of the desk down to the feet
                               # is ground the character may not walk into.
MARGIN = 26                    # keep the character off the very edge of the floor
CHAIR_AT = (-46, -46)          # where a desk's chair stands, relative to the desk


def _meta():
    return json.load(open(os.path.join(OUT, "room_meta.json")))


def _base_y(m, x):
    """floor level at column x: the seam both walls stand on"""
    return m["cy"] + abs(x - m["cx"]) * (m["th"] / m["tw"])


def blocked_grid(items, m):
    W, H = m["w"], m["h"]
    gw, gh = W // CELL, H // CELL
    grid = np.zeros((gh, gw), np.uint8)

    # off the floor: above the wall seam, or outside the margins
    for gy in range(gh):
        for gx in range(gw):
            x, y = gx * CELL + CELL // 2, gy * CELL + CELL // 2
            if y < _base_y(m, x) + MARGIN or y > H - MARGIN or x < MARGIN or x > W - MARGIN:
                grid[gy, gx] = 1

    for it in items:
        sp = Image.open(os.path.join(OUT, "assets", it["asset"] + ".png")).convert("RGBA")
        if it.get("flip"):
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.asarray(sp)[:, :, 3] > 40
        y0 = int(sp.height * (1 - FOOT))
        left = round(it["x"] - sp.width / 2)
        top = round(it["y"] - sp.height)
        ys, xs = np.nonzero(a[y0:])
        if not len(xs):
            continue
        for cx, cy in zip((left + xs) // CELL, (top + y0 + ys) // CELL):
            if 0 <= cy < gh and 0 <= cx < gw:
                grid[cy, cx] = 1

    # grow every obstacle by one cell: standing with a toe inside a desk reads as
    # walking through it, because the desk sprite is tall and covers him
    # two cells of clearance: the sprite is about five cells wide, so one cell
    # still let his shoulder sit inside a desk
    grown = grid.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= np.roll(np.roll(grid, dy, 0), dx, 1)

    # keep only the floor you can actually walk on: the pockets left between a
    # sofa and a rug are "free" cells the pathfinder can never reach, and a
    # target that lands in one leaves the character standing still forever
    # 4-connected on purpose: the page's A* refuses to cut a corner, so two
    # areas that only touch diagonally are *not* connected for the character,
    # and labelling them as one region is what left him staring at a sofa he
    # could never walk to.
    lab, n = ndimage.label(grown == 0, ndimage.generate_binary_structure(2, 1))
    if n > 1:
        sizes = ndimage.sum(grown == 0, lab, range(1, n + 1))
        main = int(np.argmax(sizes)) + 1
        grown[(lab != main) & (lab != 0)] = 1
    return grown


def spots(items, m):
    """Where the character is sent.

    Each spot has two parts: `walk` is a place on the floor the pathfinder can
    actually reach, `sit` is where the sprite is drawn once he is there, with the
    depth key it must sort by — a chair behind a desk has to draw *before* the
    desk or the desk stops hiding his legs.
    """
    out = {"desks": [], "sofa": None, "coffee": None}
    for it in items:
        a, x, y = it["asset"], it["x"], it["y"]
        if a == "desk":
            # every desk has a real chair behind it (see CHAIR_AT), and that
            # chair is the seat: the person is drawn one pixel deeper than it so
            # they sit *in* it, and the desk, being nearer the viewer, still
            # covers them from the waist down
            cx_, cy_ = x + CHAIR_AT[0], y + CHAIR_AT[1]
            out["desks"].append({"walk": {"x": x - 96, "y": y + 62},
                                 "sit": {"x": cx_, "y": cy_ + 10, "sortY": cy_ + 1}})
        elif a == "sofa" and out["sofa"] is None:
            # the coffee table sits right against the front of the sofa, so the
            # only floor next to it is off its right arm: seat him on the right
            # cushion too, or he crosses the whole sofa in one frame
            out["sofa"] = {"walk": {"x": x + 176, "y": y + 6},
                           "sit": {"x": x + 55, "y": y - 26, "sortY": y + 2,
                                   "z": it.get("z", 0)}}
        elif a.startswith("coffee") and out["coffee"] is None:
            # `coffee-frame` is the neon sign on the wall, not the counter: stand
            # in front of whatever piece of furniture is under it, otherwise the
            # counter is drawn last and swallows him
            under = [p for p in items if p is not it and abs(p["x"] - x) < 140
                     and y < p["y"] < m["h"] * 0.55]
            cy = (max(p["y"] for p in under) + 40) if under else max(y + 58, _base_y(m, x) + 46)
            out["coffee"] = {"walk": {"x": x, "y": cy}, "sit": {"x": x, "y": cy, "sortY": cy}}
    if out["coffee"] is None and out["desks"]:
        out["coffee"] = json.loads(json.dumps(out["desks"][0]))
    return out


def snap(out, grid):
    """Pull every approach point onto floor the character can really stand on.

    A chair in front of a desk and the gap beside the sofa are guessed from the
    sprite's own anchor, so some of them land a few pixels inside the rug or the
    coffee table. Left alone the pathfinder aims at a cell it can never occupy
    and he stalls; snapping to the closest free cell keeps the intent (stand by
    this piece of furniture) without the dead end.
    """
    gh, gw = grid.shape

    def fix(p):
        gx, gy = int(p["x"]) // CELL, int(p["y"]) // CELL
        if 0 <= gy < gh and 0 <= gx < gw and not grid[gy, gx]:
            return True
        for r in range(1, 26):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    nx, ny = gx + dx, gy + dy
                    if 0 <= ny < gh and 0 <= nx < gw and not grid[ny, nx]:
                        p["x"], p["y"] = nx * CELL + CELL // 2, ny * CELL + CELL // 2
                        return True
        return False

    for k in ("sofa", "coffee"):
        if out.get(k) and not fix(out[k]["walk"]):
            out[k] = None
    # a desk walled in behind other furniture has no approach at all. Keeping it
    # on the list only means somebody claims it, never gets there and stands
    # still; it is dropped instead.
    keep = [d for d in out["desks"] if fix(d["walk"])]
    if len(keep) != len(out["desks"]):
        print("   %d desk(s) unreachable, dropped" % (len(out["desks"]) - len(keep)))
    out["desks"] = keep
    return out


# the model framed some rows tighter than others, so a frame's own height is not
# the character's height. Each row is normalised against the walk row instead:
# standing poses match it, seated poses are the same person folded up.
SEATED = {"r1", "r2", "r3", "r11", "r13"}
SEATED_REL = 0.9


SHRINK = 0.5                   # the model draws a walk frame about 320 px tall
                               # and the page paints it at 140: shipping the
                               # originals is 64 MB of PNG for pixels nobody
                               # ever sees, so they are halved on the way out


def anchor_x(im):
    """Where the body is inside its own frame.

    Every frame is trimmed to its own pixels, so a stride frame with both legs
    thrown wide is much broader than a passing frame. Centring on the frame
    then slides the whole person sideways twice per step. The torso barely
    moves, so its middle is the point the sprite is hung from instead.
    """
    a = np.asarray(im)[:, :, 3] > 40
    band = a[int(im.height * 0.22):int(im.height * 0.55)]
    xs = np.nonzero(band.any(0))[0]
    return int(round((xs.min() + xs.max()) / 2)) if len(xs) else im.width // 2


def chars(tag="rade"):
    src = os.path.join(ART, "chars", tag)
    dst = os.path.join(OUT, "chars", tag)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    rows = {}
    for f in sorted(os.listdir(src)):
        if not f.endswith(".png"):
            continue
        im = Image.open(os.path.join(src, f)).convert("RGBA")
        im = im.resize((max(1, round(im.width * SHRINK)), max(1, round(im.height * SHRINK))),
                       Image.LANCZOS)
        im.quantize(colors=192, method=Image.FASTOCTREE).save(os.path.join(dst, f))
        row = f.split("_")[0]
        rows.setdefault(row, []).append({"f": f[:-4], "w": im.width, "h": im.height,
                                         "ax": anchor_x(im)})

    def med(r):
        hs = sorted(d["h"] for d in rows[r])
        return hs[len(hs) // 2]

    base = med("r0")
    out = {}
    for r in rows:
        rows[r].sort(key=lambda d: d["f"])
        rel = SEATED_REL if r in SEATED else 1.0
        out[r] = {"k": round(rel * base / med(r), 4), "f": rows[r]}
    # `base` is the median walk frame, not the first one: the model draws one
    # frame of the cycle a few pixels taller than the rest, and scaling everyone
    # by whichever frame happened to land first is why they ended up different
    # heights on screen.
    return {"base": base, "rows": out}


def cast():
    """Every folder under art/chars is somebody who lives in this office."""
    root = os.path.join(ART, "chars")
    tags = sorted(t for t in os.listdir(root)
                  if os.path.isdir(os.path.join(root, t))
                  and any(f.endswith(".png") for f in os.listdir(os.path.join(root, t))))
    return {t: chars(t) for t in tags}


def build():
    m = _meta()
    items = json.load(open(LAYOUT)) if os.path.exists(LAYOUT) else []
    # the page paints with the same rule build_room.py bakes with: the editor's
    # z first, then how far down the piece stands
    props = [{"a": it["asset"], "x": it["x"], "y": it["y"],
              "z": it.get("z", 0), "flip": bool(it.get("flip"))} for it in items]

    # The editor lifted the sofa to z=1, which also lifts it over the coffee
    # table standing in front of it — and over anyone sitting on it. Anything
    # that stands closer to the viewer than the sofa and overlaps it is pushed
    # one layer higher so the table keeps its place in front.
    sofa = next((p for p in props if p["a"] == "sofa"), None)
    if sofa:
        for p in props:
            if p is not sofa and p["z"] >= 0 and sofa["y"] < p["y"] < sofa["y"] + 130 \
               and abs(p["x"] - sofa["x"]) < 210:
                p["z"] = sofa["z"] + 1

    props.sort(key=lambda p: (p["z"], p["y"]))

    grid = blocked_grid(items, m)
    scene = {
        "world": [m["w"], m["h"]],
        "cell": CELL,
        "grid": ["".join(str(v) for v in row) for row in grid],
        "props": props,
        "spots": snap(spots(items, m), grid),
        "chars": cast(),
    }
    json.dump(scene, open(os.path.join(OUT, "scene.json"), "w"))
    free = int((grid == 0).sum())
    print("-> scene.json  %d props  %d free cells of %d" % (len(props), free, grid.size))


if __name__ == "__main__":
    build()
