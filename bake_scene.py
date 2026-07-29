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
import math
import os
import shutil

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
OUT = os.path.join(HERE, "static", "office")
LAYOUT = os.path.join(HERE, "layout.json")
SEATS = os.path.join(HERE, "seats.json")
WALK = os.path.join(HERE, "walk.json")

CELL = 10                      # collision cell, in room pixels
BODY = 2                       # cells of clearance kept around every obstacle.
                               # The pathfinder only ever tests the cell under
                               # the feet, but a character is about seven cells
                               # wide, so without this his shoulder walks
                               # straight through the side of a desk.
MARGIN = 26                    # keep the character off the near edge of the floor
WALL = 54                      # and further off the back walls: the wall is part
                               # of the backdrop, so anyone who gets that high is
                               # drawn on top of it and appears to stand in the
                               # window
# How big people are and where exactly they sit. These are the numbers nobody
# can work out from first principles — they are eyeballed against the art — so
# they live in seats.json and are tuned on static/seats.html rather than here.
TUNE = {
    "stand": 140,                       # height of a standing sprite, room px
    "rowScale": {"r1": 1.15, "r13": 1.00, "r2": 0.90, "r3": 0.90, "r11": 0.90},
    "desk": {"sit": [-61, -18]},        # fallback only: a desk with no chair
    "chair": {"sit": [0, -4]},          # where the body sits on the chair it was
                                        # given, measured off the chair's own foot
    # the sofa seats three: one offset for the middle cushion and the step from
    # one cushion to the next, which in an isometric room is a move along the
    # floor's own axis rather than straight sideways
    "sofa": {"sit": [34, -58], "step": [52, -18], "seats": 3},
    "couch": {"sit": [4, -18]},         # the single armchair by the bookcase
}


def pair_chairs(items):
    """Match every desk with the chair that was put in front of it.

    The seat used to hang off the desk by a fixed offset, which is why the body
    floated a hand's width above a chair that had been dragged somewhere slightly
    else. The chair is what a viewer reads as the seat, so the chair decides where
    the body sits. Nearest pair first, one chair per desk, so two desks standing
    close together cannot both claim the same chair.
    """
    desks = [it for it in items if it["asset"] == "desk"]
    chairs = [it for it in items if it["asset"] == "chair"]
    pairs = sorted(((math.hypot(d["x"] - c["x"], d["y"] - c["y"]), i, j)
                    for i, d in enumerate(desks) for j, c in enumerate(chairs)),
                   key=lambda p: p[0])
    out, tookD, tookC = {}, set(), set()
    for dist, i, j in pairs:
        if i in tookD or j in tookC or dist > 200:
            continue
        tookD.add(i); tookC.add(j)
        out[id(desks[i])] = chairs[j]
    return out


def tune():
    t = json.loads(json.dumps(TUNE))
    if os.path.exists(SEATS):
        saved = json.load(open(SEATS))
        for k, v in saved.items():
            if isinstance(v, dict) and isinstance(t.get(k), dict):
                t[k].update(v)
            else:
                t[k] = v
    return t


def walk_marks():
    """Cells the editor forced open or forced shut, in grid coordinates."""
    if not os.path.exists(WALK):
        return {}
    try:
        return json.load(open(WALK))
    except ValueError:
        return {}


def _meta():
    return json.load(open(os.path.join(OUT, "room_meta.json")))


def _base_y(m, x):
    """floor level at column x: the seam both walls stand on"""
    return m["cy"] + abs(x - m["cx"]) * (m["th"] / m["tw"])


def _uv(x, y, m):
    """screen point -> the floor's own two axes

    The floor runs along (tw, th) and (-tw, th), so a point is u tiles down one
    of them and v down the other. Distance from the eye is u + v, which is why
    sorting by screen y works at all for a dot on the floor; the whole point of
    keeping u and v apart is that a *thing* covers a range of both, and two
    things side by side along one axis do not hide each other whatever their
    y says.
    """
    u = (x / m["tw"] + y / m["th"]) / 2.0
    v = (y / m["th"] - x / m["tw"]) / 2.0
    return u, v


def footprint(it, m):
    """the floor a piece of furniture stands on, as a box in (u, v)

    An isometric sprite is its floor tile swept upwards: the ground is the
    diamond at the bottom, as tall in the picture as the sprite is wide times
    the room's ratio. That diamond is a rectangle on the floor, so its four
    extremes give the range of u and of v the piece occupies.
    """
    sp = Image.open(os.path.join(OUT, "assets", it["asset"] + ".png")).convert("RGBA")
    if it.get("flip"):
        sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
    a = np.asarray(sp)[:, :, 3] > 40
    cols = np.nonzero(a.any(0))[0]
    if not len(cols):
        return None
    ratio = m["th"] / m["tw"]
    span = int(cols[-1] - cols[0] + 1)
    left = it["x"] - sp.width / 2.0 + cols[0]
    right = left + span
    deep = min(span * ratio, sp.height)
    y1, y0 = float(it["y"]), it["y"] - deep
    mid = (y0 + y1) / 2.0
    pts = [_uv(left, mid, m), _uv(right, mid, m),
           _uv((left + right) / 2.0, y0, m), _uv((left + right) / 2.0, y1, m)]
    us = [p[0] for p in pts]
    vs = [p[1] for p in pts]
    return [round(min(us), 3), round(max(us), 3), round(min(vs), 3), round(max(vs), 3)]


def blocked_grid(items, m):
    W, H = m["w"], m["h"]
    gw, gh = W // CELL, H // CELL
    grid = np.zeros((gh, gw), np.uint8)

    # off the floor: above the wall seam, or outside the margins
    for gy in range(gh):
        for gx in range(gw):
            x, y = gx * CELL + CELL // 2, gy * CELL + CELL // 2
            if y < _base_y(m, x) + WALL or y > H - MARGIN or x < MARGIN or x > W - MARGIN:
                grid[gy, gx] = 1

    ratio = m["th"] / m["tw"]
    hard = np.zeros_like(grid)     # what a piece of furniture actually stands on
    for it in items:
        sp = Image.open(os.path.join(OUT, "assets", it["asset"] + ".png")).convert("RGBA")
        if it.get("flip"):
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        a = np.asarray(sp)[:, :, 3] > 40
        cols = np.nonzero(a.any(0))[0]
        if not len(cols):
            continue
        # An isometric sprite is its floor tile swept upwards, so the ground it
        # stands on is the diamond at the bottom: as tall as the sprite is wide,
        # squashed by the room's own tile ratio. Taking a fixed fraction of the
        # sprite instead treated a monitor as if it were floor, and the desk's
        # real footprint as if it were air.
        span = cols[-1] - cols[0] + 1
        # A rug is its own floor tile and nothing more: as tall in the picture as
        # the diamond it covers. A table is half as wide again in picture as it
        # is in floor, because it has legs and a top. Anything close to flat is
        # something you walk on, not into — which is what the editor was being
        # used to say by hand, and those hand marks were opening the tables
        # standing on the rugs along with them.
        flat = sp.height <= span * ratio * 1.35
        if flat:
            continue
        diamond = sp.height - int(round(span * ratio)) - 4
        # ...and then a little more. A desk is only 74 px of floor but 151 px of
        # picture, so someone standing just behind its diamond is buried up to
        # the neck and reads as walking through it. Blocking the lower two
        # thirds of the picture as well keeps people out of the strip a tall
        # object hides.
        y0 = max(0, min(diamond, int(sp.height * 0.38)))
        left = round(it["x"] - sp.width / 2)
        top = round(it["y"] - sp.height)
        ys, xs = np.nonzero(a[y0:])
        if not len(xs):
            continue
        for cx, cy in zip((left + xs) // CELL, (top + y0 + ys) // CELL):
            if 0 <= cy < gh and 0 <= cx < gw:
                grid[cy, cx] = hard[cy, cx] = 1

    # every obstacle is inflated by half a body, which is the standard way to
    # plan for something wider than the cell it is tracked in: the feet then
    # never get close enough for the shoulders to overlap the furniture
    grown = ndimage.binary_dilation(grid.astype(bool), np.ones((3, 3)),
                                    iterations=BODY).astype(np.uint8)

    # ...and then whatever was painted by hand in the editor. Some of this the
    # sprites cannot say: a rug is walkable and a table is not, and both are a
    # flat shape on the floor. Painted last, so a hand-opened cell also gets to
    # join the walkable region below instead of being cut off by it.
    hand = walk_marks()
    for gx, gy in hand.get("block", []):
        if 0 <= gy < grown.shape[0] and 0 <= gx < grown.shape[1]:
            grown[gy, gx] = 1
    for gx, gy in hand.get("open", []):
        if 0 <= gy < grown.shape[0] and 0 <= gx < grown.shape[1]:
            grown[gy, gx] = 0
    # ...but a hand may only open the clearance around a thing, never the thing
    # itself. Opening the floor under a table is how people ended up walking
    # through the one in front of the sofa.
    grown[hard == 1] = 1

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


def spots(items, m, t):
    """Where the character is sent.

    Each spot has two parts: `walk` is a place on the floor the pathfinder can
    actually reach, `sit` is where the sprite is drawn once he is there, with the
    depth key it must sort by — a chair behind a desk has to draw *before* the
    desk or the desk stops hiding his legs.
    """
    out = {"desks": [], "seats": [], "coffee": None}
    seat_of = pair_chairs(items)
    for it in items:
        a, x, y = it["asset"], it["x"], it["y"]
        if a == "desk":
            # Who sits here is fixed to the desk, not to the chair: the seat has
            # to put their hands on that keyboard, and a chair is dragged around
            # for the look of the thing. Hanging the body off the chair meant
            # nudging a chair dragged the typist off their keyboard with it.
            #
            # They sit behind it and are drawn before it, so the desk keeps its
            # place in front of their legs. What decides whether their hands
            # land on the keyboard is their size, not the size of the desk:
            # shrinking the desk shrinks the keyboard with it and moves the
            # keys further away, while a bigger body reaches further down the
            # tabletop. That is what rowScale.r1 is for.
            ch = seat_of.get(id(it))
            if ch:
                cx, cy = t.get("chair", {}).get("sit", [0, -4])
                seat = {"x": ch["x"] + cx, "y": ch["y"] + cy}
                # stand on the far side of the chair from the desk, which is the
                # side the chair is pulled out towards
                wx = ch["x"] - 46 if ch["x"] <= x else ch["x"] + 46
                walk = {"x": wx, "y": ch["y"] + 34}
            else:
                sx, sy = t["desk"]["sit"]
                seat = {"x": x + sx, "y": y + sy}
                walk = {"x": x - 96, "y": y + 62}
            # drawn after its chair and before its desk, so the chair is behind
            # the body and the desk still hides the legs
            out["desks"].append({"walk": walk,
                                 "sit": {"x": seat["x"], "y": seat["y"], "sortY": y - 1,
                                         # he is on the desk's own patch of floor,
                                         # so nothing but the layer tells them
                                         # apart: he goes just under it
                                         "fp": footprint(it, m), "dz": -0.5},
                                 # which chair this desk owns, so the page can take
                                 # it away for the poses that bring their own
                                 "chair": {"x": ch["x"], "y": ch["y"]} if ch else None})
        elif a == "sofa":
            # A three seater is three seats. They sit along the sofa's own axis,
            # which runs up and to the right at the floor's ratio, and they are
            # drawn front cushion last so the near one is not hidden behind the
            # far one. The coffee table sits right against the front, so the only
            # floor to approach from is off the right arm, shared by all three.
            s = t["sofa"]
            sx, sy = s["sit"]
            dx, dy = s.get("step", [52, -18])
            n = int(s.get("seats", 3))
            for i in range(n):
                k = i - (n - 1) / 2.0                      # -1, 0, +1 for three
                out["seats"].append({
                    "walk": {"x": x + 176, "y": y + 6},
                    "sit": {"x": round(x + sx + dx * k), "y": round(y + sy + dy * k),
                            "sortY": y + 2 - k, "fp": footprint(it, m),
                            # all three share the sofa's floor, so the layer is
                            # all that keeps the near cushion in front
                            "dz": round(0.5 - 0.02 * k, 3)}})
        elif a == "single-couch":
            # This one is turned the other way: it opens to the south west, so
            # whoever sits in it is drawn mirrored. The sitting pose was only
            # ever drawn facing south east.
            cx0, cy0 = t.get("couch", {}).get("sit", [4, -18])
            out["seats"].append({"walk": {"x": x - 104, "y": y + 12},
                                 "sit": {"x": x + cx0, "y": y + cy0, "flip": True,
                                         "sortY": y + 2, "fp": footprint(it, m),
                                         "dz": 0.5}})
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

    if out.get("coffee") and not fix(out["coffee"]["walk"]):
        out["coffee"] = None
    out["seats"] = [s for s in out["seats"] if fix(s["walk"])]
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
SHRINK = 0.5                   # the model draws a walk frame about 320 px tall
                               # and the page paints it at 140: shipping the
                               # originals is 64 MB of PNG for pixels nobody
                               # ever sees, so they are halved on the way out


KEY = (255, 0, 255)            # the magenta the sheets were drawn against


def dekey(im):
    """Take the last of the magenta backdrop off a frame.

    The extractor cut the sheet on the key colour and left two kinds of crumb: a
    few solid magenta pixels the cut missed, and a half-transparent violet rim
    along every outline. Neither can be removed by colour alone — nia's hair is
    a pink close enough to the key to be deleted with it — so the test is colour
    *and* opacity: art is solid, so a pixel that is only part way opaque and
    leans magenta is backdrop, while a solid pixel has to be all but the key
    itself before it is thrown away.
    """
    a = np.asarray(im).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    d = np.maximum(np.maximum(abs(r - KEY[0]), abs(g - KEY[1])), abs(b - KEY[2]))
    drop = (al > 0) & ((d <= 60) | ((al < 255) & (d <= 140)))
    if not drop.any():
        return im
    out = a.copy()
    out[drop, 3] = 0
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def shrink(im):
    """Halve a frame without dragging the cut-away background back in.

    A transparent pixel still holds a colour, and a plain resize averages it
    with its neighbours as if it were solid: the violet ring the extractor
    deleted came straight back along every edge, one halving later. Resizing
    the colour weighted by alpha, then dividing the weight out again, is the
    ordinary fix and the only one that leaves the outline its own colour.
    """
    w, h = max(1, round(im.width * SHRINK)), max(1, round(im.height * SHRINK))
    a = np.asarray(im).astype(np.float32)
    al = a[:, :, 3:4] / 255.0
    pm = Image.fromarray((a[:, :, :3] * al).astype(np.uint8), "RGB").resize((w, h), Image.LANCZOS)
    am = Image.fromarray(a[:, :, 3].astype(np.uint8), "L").resize((w, h), Image.LANCZOS)
    p = np.asarray(pm).astype(np.float32)
    q = np.asarray(am).astype(np.float32)[:, :, None] / 255.0
    rgb = np.clip(np.divide(p, np.maximum(q, 1 / 255.0)), 0, 255)
    return Image.fromarray(np.dstack([rgb, q * 255]).astype(np.uint8), "RGBA")


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


REACT = "r12"                  # the one row that is allowed to change shape
# Poses drawn sitting on a chair the sheet drew in. Only rade's sheet has any:
# his mug, sleeping and typing-from-behind rows all come with an office chair,
# which is why the room has to take that desk's own chair away while he is in
# one. bod's sleeping frame was drawn later, without a chair, so it is not here.
# They are also left out of the width work below: squashing one squashes the
# chair with it.
WITH_CHAIR = {"rade": {"r2", "r3", "r11"}}


WALK_ROWS = {"r0", "r4", "r5", "r6", "r7", "r8", "r9", "r10"}
SLEEP, SIT = "r3", "r13"       # asleep, and the sitting pose a nap is made from


def torso_w(im):
    """The whole width of the body through the chest and the belly."""
    a = np.asarray(im)[:, :, 3] > 40
    h = a.shape[0]
    band = a[int(h * 0.34):int(h * 0.62)]
    xs = np.nonzero(band.any(0))[0]
    return int(xs.max() - xs.min() + 1) if len(xs) else 0


def steady(frames, base):
    """Keep the frames of a walk that were drawn as the same body.

    The model did not draw one man eight times. Measured through the chest, a
    single cycle swings by a fifth on average and by half at worst: he sets off
    lean and arrives heavy, twice per second. Nothing can be stretched out of
    that, it is a different drawing.

    But the frames alternate — one half of a cycle is consistent with itself and
    the other half is where the drawing wandered — so the walk is run on the
    half that agrees. Four frames is an ordinary pixel walk cycle; four frames
    of the same person is better than eight of two.
    """
    if len(frames) < 8:
        return frames
    w = [d["tw"] * base / d["h"] for d in frames]
    med = sorted(w)[len(w) // 2] or 1
    spread = lambda v: (max(v) - min(v)) / med
    full = spread(w)
    if full < 0.10:
        return frames
    halves = [(spread(w[0::2]), frames[0::2]), (spread(w[1::2]), frames[1::2])]
    best, keep = min(halves, key=lambda h: h[0])
    return keep if best <= full * 0.67 else frames


def body_w(im):
    """How wide this person is, measured at the shoulders.

    Not at the belly: a walking figure swings its arms across the waist, so the
    silhouette there changes by a third within one cycle and it should. The
    shoulders are the part that does not move, which makes them the only honest
    place to ask whether the model drew the same body twice.
    """
    a = np.asarray(im)[:, :, 3] > 40
    h = a.shape[0]
    band = a[int(h * 0.26):int(h * 0.34)]
    xs = np.nonzero(band.any(0))[0]
    return int(xs.max() - xs.min() + 1) if len(xs) else 0


def eye_line(im):
    """How far the eyes sit above the soles, as a share of the whole sprite.

    Holding everyone to the same total height does not make them the same size,
    because the hair is part of that height and it is not part of the person:
    rade's spikes take five per cent more of him than kip's cap takes of kip,
    so at an equal height rade is a smaller man wearing taller hair. The eyes
    are the landmark instead — they sit at the same place on every one of these
    bodies — and they are easy to find, being the only pure white on a face.
    """
    a = np.asarray(im).astype(int)
    h = a.shape[0]
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    white = (al > 40) & (r > 215) & (g > 215) & (b > 210)
    white[int(h * 0.55):] = False              # a white shirt is not an eye
    lab, n = ndimage.label(white)
    if not n:
        return None
    sizes = ndimage.sum(white, lab, range(1, n + 1))
    ys = [float(np.nonzero((lab == i + 1).any(1))[0].mean())
          for i, v in enumerate(sizes) if v >= 3]
    if not ys:
        return None
    lo = min(ys)                               # the eyes, and whatever glints
    near = [y for y in ys if y - lo <= 6]      # on the glasses beside them
    p = 1 - (sum(near) / len(near)) / h
    return p if 0.60 < p < 0.85 else None


def _eye_blobs(im):
    """The two whites of the eyes: the only pure white on a face."""
    a = np.asarray(im).astype(int)
    h = a.shape[0]
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    white = (al > 40) & (r > 215) & (g > 215) & (b > 210)
    white[int(h * 0.32):] = False                  # a white shirt is not an eye
    lab, n = ndimage.label(white)
    found = [((lab == i).sum(), lab == i) for i in range(1, n + 1)]
    found = [(s, m) for s, m in found if s >= 15]
    found.sort(key=lambda t: -t[0])
    return [m for _, m in found[:2]]


def _lum(c):
    return 0.3 * c[0] + 0.6 * c[1] + 0.1 * c[2]


def nap(im):
    """Make a sleeping frame out of a sitting one.

    Five of the seven were never drawn asleep, and the room was showing them at
    their keyboards with zZ over their heads, which is a picture of somebody
    working, not sleeping. Redrawing them needs the model that drew the sheets;
    until then this closes their eyes and lets the head nod, which is the whole
    of what "asleep" looks like at this size.

    Closing an eye means painting out the white and the pupil and laying a lid
    across it. Behind glasses the white is the lens, not the eye, so there the
    lens keeps its own colour and only what is dark inside it is painted out —
    the frame the lens sits in tells the two cases apart.
    """
    a = np.asarray(im).copy().astype(int)
    h, w = a.shape[:2]
    for m in _eye_blobs(im):
        ring = ndimage.binary_dilation(m, iterations=2) & ~m
        rc = a[ring & (a[..., 3] > 200)][:, :3]
        glasses = len(rc) and np.median([_lum(c) for c in rc]) < 95
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        box = np.zeros((h, w), bool)
        box[y0:y1 + 1, x0:x1 + 1] = True
        if glasses:
            fill = np.median(a[m][:, :3], axis=0)
            dark = box & (a[..., 3] > 0) & (np.apply_along_axis(_lum, 2, a[..., :3]) < 130)
            a[dark, :3] = fill
            lid = (fill * 0.35).astype(int)
        else:
            band = a[min(h - 1, y1 + 2):min(h, y1 + 6), x0:x1 + 1]
            skin = band[band[..., 3] > 200]
            fill = np.median(skin[:, :3], axis=0) if len(skin) else np.array([230, 190, 160])
            a[box & (a[..., 3] > 0), :3] = fill
            lid = (fill * 0.5).astype(int)
        my = (y0 + y1) // 2
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, (x1 - x0))
            yy = my + int(round(1.6 * math.sin(math.pi * t)))   # a shallow closed lid
            for dy in (0, 1):
                if 0 <= yy + dy < h and a[yy + dy, x, 3] > 0:
                    a[yy + dy, x, :3] = lid
    out = Image.fromarray(a.astype(np.uint8), "RGBA")
    # and the head drops onto the shoulders. Moved down rather than rotated:
    # turning a pixel face by a few degrees leaves it looking chewed.
    neck = int(h * 0.34)
    head = out.crop((0, 0, w, neck))
    body = out.copy()
    body.paste((0, 0, 0, 0), (0, 0, w, neck))
    body.alpha_composite(head, (2, 5))
    return body


def chars(tag, scale):
    src = os.path.join(ART, "chars", tag)
    dst = os.path.join(OUT, "chars", tag)
    shutil.rmtree(dst, ignore_errors=True)
    os.makedirs(dst)
    rows, eyes, sitting = {}, [], None

    def keep(name, im):
        im.quantize(colors=192, method=Image.FASTOCTREE).save(os.path.join(dst, name + ".png"))
        return {"f": name, "w": im.width, "h": im.height, "ax": anchor_x(im),
                "bw": body_w(im), "tw": torso_w(im)}

    for f in sorted(os.listdir(src)):
        if not f.endswith(".png"):
            continue
        im = shrink(dekey(Image.open(os.path.join(src, f)).convert("RGBA")))
        row = f.split("_")[0]
        rows.setdefault(row, []).append(keep(f[:-4], im))
        if row == SIT and sitting is None:     # the pose the nap is built from
            sitting = im
        if row == "r0":                        # the one row that faces the camera
            p = eye_line(im)
            if p:
                eyes.append(p)

    # nobody drew these five asleep, so the sitting pose is put to sleep instead
    synth = SLEEP not in rows and sitting is not None
    if synth:
        rows[SLEEP] = [keep(SLEEP + "_00", nap(sitting))]

    def med(r):
        hs = sorted(d["h"] for d in rows[r])
        return hs[len(hs) // 2]

    base = med("r0")
    out = {}
    for r in rows:
        rows[r].sort(key=lambda d: d["f"])
        if r in WALK_ROWS:
            rows[r] = steady(rows[r], base)
        # a made-up sleeping frame is the sitting pose, so it is sized like one
        rel = scale.get(SIT if (synth and r == SLEEP) else r, 1.0)
        # Every frame gets its own factor, so all eight of a walk come out the
        # same height. The model does not draw one person eight times: within a
        # single row it drew this one 13 % shorter and hunched, and one factor
        # for the row carried that straight to the screen as somebody who
        # shrinks twice per step. Height is what the eye tracks here, so it is
        # the height that is held still.
        for d in rows[r]:
            d["k"] = round(rel * base / d["h"], 4)
        out[r] = {"k": round(rel * base / med(r), 4), "f": rows[r]}
        if r in WITH_CHAIR.get(tag, ()):
            out[r]["chair"] = True      # this pose comes with its own seat
    # ...except a reaction, where changing shape is the whole point: a stretch
    # reaches up and is meant to be taller, and holding that to one height
    # shrinks the person for exactly as long as they stretch.
    for d in out.get(REACT, {}).get("f", []):
        d.pop("k", None)
    # `base` is the median walk frame, not the first one: the model draws one
    # frame of the cycle a few pixels taller than the rest, and scaling everyone
    # by whichever frame happened to land first is why they ended up different
    # heights on screen.
    return {"base": base, "rows": out,
            "p": round(sorted(eyes)[len(eyes) // 2], 4) if eyes else None}


def cast(scale):
    """Every folder under art/chars is somebody who lives in this office."""
    root = os.path.join(ART, "chars")
    tags = sorted(t for t in os.listdir(root)
                  if os.path.isdir(os.path.join(root, t))
                  and any(f.endswith(".png") for f in os.listdir(os.path.join(root, t))))
    for stale in os.listdir(os.path.join(OUT, "chars")):
        if stale not in tags:
            shutil.rmtree(os.path.join(OUT, "chars", stale), ignore_errors=True)
    out = {t: chars(t, scale) for t in tags}

    # Everyone is drawn to the same eye line, and their hair reaches as far
    # above it as it likes — which is what "the same size" means for people
    # with a cap, a bun and a spike. The line is the cast's own average, so
    # nobody is measured against a number picked out of the air.
    seen = [c["p"] for c in out.values() if c["p"]]
    if seen:
        target = sum(seen) / len(seen)
        for c in out.values():
            fix = target / c["p"] if c["p"] else 1.0
            for row in c["rows"].values():
                row["k"] = round(row["k"] * fix, 4)
                for d in row["f"]:
                    if "k" in d:
                        d["k"] = round(d["k"] * fix, 4)
            c.pop("p")
    widths(out)
    return out


def widths(cast):
    """Hold every frame of a person to the same build.

    Height was already held still; width was not, and the model treated it as a
    free hand. The same man is drawn a third wider halfway through his own walk
    and a fifth narrower the moment he turns a corner, which on screen reads as
    somebody who keeps gaining and losing weight.

    The correction is one factor for the whole row, not one per frame: a walk
    cycle's own flicker is dealt with by dropping the frames that disagree, and
    stretching each frame separately on top of that only adds a wobble of its
    own. What is left to fix is the step between views — the same person a fifth
    narrower the moment he turns — and the target for a view is the cast's own
    median ratio of that view to the front, so a profile stays properly narrower
    than a front view without any one sheet's mistake setting the rule. It is
    capped: past a point the drawing is wrong in a way stretching cannot mend.
    """
    CAP = (0.86, 1.16)

    def med(vals):
        v = sorted(vals)
        return v[len(v) // 2] if v else 0

    def rowsize(c, r):
        row = c["rows"][r]
        return med([d["bw"] * (d.get("k", row["k"])) for d in row["f"] if d["bw"]])

    front = {t: rowsize(c, "r0") for t, c in cast.items() if "r0" in c["rows"]}
    # what each view measures against the front view, as the whole cast agrees
    rho = {}
    for t, c in cast.items():
        for r in c["rows"]:
            if r == REACT or r in WITH_CHAIR.get(t, ()) or not front.get(t):
                continue
            s = rowsize(c, r)
            if s:
                rho.setdefault(r, []).append(s / front[t])
    rho = {r: med(v) for r, v in rho.items()}

    for t, c in cast.items():
        if not front.get(t):
            continue
        for r, row in c["rows"].items():
            if r == REACT or r in WITH_CHAIR.get(t, ()) or r not in rho:
                continue
            want, have = front[t] * rho[r], rowsize(c, r)
            if have:
                row["xk"] = round(min(CAP[1], max(CAP[0], want / have)), 4)
    for c in cast.values():
        for row in c["rows"].values():
            for d in row["f"]:
                d.pop("bw", None)
                d.pop("tw", None)
    return cast


def build():
    m = _meta()
    t = tune()
    items = json.load(open(LAYOUT)) if os.path.exists(LAYOUT) else []
    # the page paints with the same rule build_room.py bakes with: the editor's
    # z first, then how far down the piece stands
    props = [{"a": it["asset"], "x": it["x"], "y": it["y"],
              "z": it.get("z", 0), "flip": bool(it.get("flip"))} for it in items]

    # Every piece carries the floor it stands on, and the page sorts the room
    # from that rather than from one y per sprite. The layer is only the
    # tie-break for things sharing the same floor: a rug under a table, a lamp
    # on a wall over the boards it lights.
    for p, it in zip(props, items):
        fp = footprint(it, m)
        if fp:
            p["fp"] = fp

    props.sort(key=lambda p: (p["z"], p["y"]))

    grid = blocked_grid(items, m)
    spot = snap(spots(items, m, t), grid)
    # the chair each desk owns, as an index into the drawing order
    where = {(p["a"], p["x"], p["y"]): i for i, p in enumerate(props)}
    for d in spot["desks"]:
        ch = d.pop("chair", None)
        d["chairIdx"] = where.get(("chair", ch["x"], ch["y"]), -1) if ch else -1
    scene = {
        "world": [m["w"], m["h"]],
        "tile": [m["tw"], m["th"]],
        "cell": CELL,
        "grid": ["".join(str(v) for v in row) for row in grid],
        "props": props,
        "spots": spot,
        "chars": cast(t.get("rowScale", {})),
        "stand": t.get("stand", 140),
    }
    json.dump(scene, open(os.path.join(OUT, "scene.json"), "w"))
    free = int((grid == 0).sum())
    print("-> scene.json  %d props  %d free cells of %d" % (len(props), free, grid.size))


if __name__ == "__main__":
    build()
