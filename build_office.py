"""Compose the RADE OFFICE room (dashboard v2) out of the sprites cut from the pack.

The reference shot frames the room close up: one long back wall across the top,
big night windows in it, and a floor that runs off every edge. That is what the
geometry here reproduces. Two scales are deliberate — the floor keeps the pack's
native tile so the grid stays fine, while furniture and bots are doubled, because
in the reference a desk is about two and a half tiles wide and the pack's desk
sprite is barely one.

Everything that never moves is baked into one PNG; the bots, the desk monitors
and the screen glow are drawn live by the page, so all this file has to get right
is the geometry, which it writes out next to the PNG as JSON.
"""
import json
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "art", "sprites")
OUT = os.path.join(HERE, "static", "office")

W, H = 1040, 590
TW, TH = 76, 38               # floor diamond, kept at the pack's own size
K = 2                         # furniture / character upscale

# the wall/floor seam: nearly level, dropping very slightly to the left
BASE0, SLOPE = 232.0, -0.085


def base(x):
    return BASE0 + SLOPE * x


_cache = {}


def s(name, flip=False, k=1):
    key = (name, flip, k)
    if key not in _cache:
        im = Image.open(os.path.join(SPR, name + ".png")).convert("RGBA")
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if k != 1:
            im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST)
        _cache[key] = im
    return _cache[key]


def put(im, sp, x, y):
    """anchor a sprite by its bottom centre"""
    im.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height)))


# ---------------------------------------------------------------- floor
FLOOR = os.path.join(HERE, "art", "floor.png")
FLOOR_TOP = 120          # it starts above the wall seam; the wall covers the rest


def floor(im):
    """One painted floor rather than a tiled one. Its whole width is fitted to
    the room so the tiles stay as fine as they are in the source picture, and
    only the height is cropped."""
    f = Image.open(FLOOR).convert("RGBA")
    k = W / f.width
    f = f.resize((W, round(f.height * k)), Image.LANCZOS)
    h = H - FLOOR_TOP
    y0 = (f.height - h) // 2 + 40    # the middle of the source is the lit part
    im.alpha_composite(f.crop((0, y0, W, y0 + h)), (0, FLOOR_TOP))


# ---------------------------------------------------------------- wall
BRICK_A = (58, 49, 72)
BRICK_B = (51, 43, 64)
MORTAR = (39, 32, 50)
SKIRT = (32, 26, 42)
STONE = (146, 126, 112)


def wall(im):
    d = ImageDraw.Draw(im)
    for x in range(W):
        b = base(x)
        d.line([(x, 0), (x, b)], fill=BRICK_A if (x // 26) % 2 else BRICK_B)
        # courses run level with the seam so the brick reads as one flat face
        for k in range(0, 14):
            y = b - 9 - k * 19
            if y > 0:
                d.point((x, y), fill=MORTAR)
        if (x // 13) % 2 == 0:
            for k in range(0, 14):
                y = b - 9 - k * 19
                if y > 0:
                    d.line([(x, y), (x, y - 18)], fill=MORTAR)
        # skirting board, and the shadow the wall drops on the floor
        d.line([(x, b - 8), (x, b)], fill=SKIRT)
        d.line([(x, b + 1), (x, b + 7)], fill=(24, 19, 32))


def window(im, x0, x1, y0, y1, panes=3):
    """A panoramic window: night city inside, stone frame and mullions outside."""
    city = s("weather_07")
    # tile the skyline instead of stretching it, or the towers come out smeared
    tile = city.crop((6, 6, city.width - 6, city.height - 6))
    tile = tile.resize((tile.width * 3, tile.height * 3), Image.NEAREST)
    tile = tile.crop((0, tile.height - (y1 - y0), tile.width, tile.height))
    strip = Image.new("RGBA", (x1 - x0, y1 - y0))
    for x in range(0, x1 - x0, tile.width):
        strip.alpha_composite(tile, (x, 0))
    im.alpha_composite(strip, (x0, y0))
    d = ImageDraw.Draw(im)
    for w in range(9):                                    # frame
        d.rectangle([x0 - w - 1, y0 - w - 1, x1 + w, y1 + w],
                    outline=STONE if 2 < w < 7 else (92, 78, 70))
    for i in range(1, panes):                             # mullions
        mx = x0 + (x1 - x0) * i // panes
        d.rectangle([mx - 6, y0, mx + 6, y1], fill=(112, 96, 86))
        d.line([(mx - 6, y0), (mx - 6, y1)], fill=STONE)
        d.line([(mx + 6, y0), (mx + 6, y1)], fill=(74, 62, 56))
    d.rectangle([x0 - 13, y1 + 8, x1 + 12, y1 + 19], fill=(120, 103, 92))   # sill
    d.rectangle([x0 - 13, y1 + 8, x1 + 12, y1 + 10], fill=(163, 143, 128))


def conduit(im):
    """the violet cable run that loops down the wall by the server door"""
    d = ImageDraw.Draw(im)
    pts = [(806, 0), (806, 60), (846, 84), (846, 150), (900, 178), (1040, 178)]
    for wdt, col in ((7, (60, 30, 88)), (3, (176, 96, 255))):
        d.line(pts, fill=col, width=wdt, joint="curve")


# ---------------------------------------------------------------- contents
KD = 2.2                       # desks read as big workstations in the reference

# every position below is the reference shot's own layout, scaled 0.84 into
# world pixels, so the room reads the same way it does there
DESKS = [(168, 392), (466, 392), (764, 392),
         (285, 534), (588, 534), (886, 534)]

# the two hand-drawn characters bring their own chair, desk and monitor, so
# their slots get nothing baked under them (see extract_chars.py)
OWN = [3, 4]

# name, x, y (floor anchor), scale
PROPS = [
    ("furni_25", 250, 242, 1.7), ("furni_31", 350, 248, 1.7),      # planters
    ("anim_08", 522, 204, 1.53),                                   # sofa, two bots on it
    ("furni_06", 615, 242, 1.62),                                  # coffee table
    ("furni_14", 628, 224, 1.25), ("furni_13", 726, 236, 1.7),     # fridge, coffee bar
    ("furni_16", 800, 248, 1.2),
    ("rack_a", 950, 250, 1.9), ("rack_b", 1016, 270, 1.7),
    ("furni_15", 44, 528, 1.65), ("furni_23", 108, 502, 1.9),      # cooler, palm
    ("furni_08", 986, 530, 1.9), ("furni_10", 1022, 480, 1.6),     # shelf, lamp table
    ("furni_17", 36, 574, 1.6),
    ("furni_34", 404, 334, 1.6), ("furni_29", 150, 270, 1.5),
]


def tint(sp, mul):
    """darken a sprite without touching its alpha — the pack's wood is far
    brighter than the reference's desks"""
    out = sp.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (int(r * mul), int(g * mul), int(b * mul * 1.06), a)
    return out


def lamp(im, sp, x, y):
    """hanging lamp plus the warm pool it throws on the wall behind it"""
    glow = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for r in range(84, 0, -1):
        a = int(26 * (1 - r / 84) ** 2)
        g.ellipse([85 - r, 85 - r * .8, 85 + r, 85 + r * .8], fill=(255, 196, 96, a))
    im.alpha_composite(glow, (int(x - 85), int(y - 40)))
    put(im, sp, x, y)


def vignette(im):
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    for i in range(70):
        a = int(74 * (1 - i / 70) ** 2)
        d.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(6, 4, 12, a))
    im.alpha_composite(v)


def build():
    im = Image.new("RGBA", (W, H), (13, 10, 20, 255))
    floor(im)
    wall(im)

    window(im, 242, 596, 18, 186, panes=3)
    conduit(im)

    put(im, s("neon_rade", k=2.2), 84, 104)
    put(im, s("poster", k=1.2), 186, 208)
    put(im, s("deco_00", k=1.1), 693, 90)         # COFFEE
    put(im, s("deco_04", k=1.7), 783, 112)        # corkboard
    lamp(im, s("deco_01", k=1.6), 330, 84)
    lamp(im, s("deco_02", k=1.6), 640, 80)
    put(im, s("door_00", k=1.6), 873, 190)

    items = [(y, name, x, k) for name, x, y, k in PROPS]
    items += [(y, "desk", x, KD) for i, (x, y) in enumerate(DESKS) if i not in OWN]
    for y, name, x, k in sorted(items):
        put(im, tint(s(name, k=k), .74) if name == "desk" else s(name, k=k), x, y)
        if name == "desk":
            put(im, s("door_10", k=1.15), x - 92, y + 6)   # the PC tower beside it
            put(im, s("furni_30", k=1.1), x + 62, y - 62)  # a plant on the desk
            put(im, s("furni_02", k=0.8), x - 58, y - 62)  # and a mug

    vignette(im)
    im.convert("RGB").save(os.path.join(OUT, "room.png"))
    json.dump({
        "world": [W, H],
        "desks": [{"x": x, "y": y} for x, y in DESKS],
        "own": OWN,
        "clock": {"x": 96, "y": 188},
        "scale": K,
    }, open(os.path.join(OUT, "room.json"), "w"), indent=1)
    print("->", os.path.join(OUT, "room.png"), im.size)


# ---------------------------------------------------------------- sprites for the page
POSES = ("type_a", "type_b", "error", "cheer", "sleep")
WALK = ("chars_10", "chars_11", "chars_12", "chars_13")


def hue_shift(im, deg):
    """Spin the hue so the sixth bot does not look like the first one."""
    import colorsys
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if not a:
                continue
            h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            r, g, b = colorsys.hls_to_rgb((h + deg / 360.0) % 1.0, l, sat)
            px[x, y] = (int(r * 255), int(g * 255), int(b * 255), a)
    return im


def ship():
    dst = os.path.join(OUT, "spr")
    os.makedirs(dst, exist_ok=True)
    # slots in OWN are written by extract_chars.py — never overwrite them here
    for b in range(1, 6):
        if b - 1 in OWN:
            continue
        for p in POSES:
            s("bot%d_%s" % (b, p), k=K).save(os.path.join(dst, "bot%d_%s.png" % (b, p)))
    for p in POSES:
        hue_shift(s("bot3_%s" % p, k=K).copy(), 150).save(os.path.join(dst, "bot6_%s.png" % p))
    for i, name in enumerate(WALK):
        s(name, k=K).save(os.path.join(dst, "walk_%d.png" % i))
    # the desk monitor is drawn after the bot, so the bot sits behind it
    s("station", k=K).save(os.path.join(dst, "station.png"))
    print("sprites ->", dst)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build()
    ship()
