#!/usr/bin/env python3
"""Build the art and the collision data the world page needs.

Two things happen here that would be painful in the browser:

1. The control room is composed from Room Builder tiles + Television Studio
   furniture, so every bot gets its own desk with a monitor and 192px of elbow
   room. It is written as two layers, like the pack's own prebuilt rooms:
   layer_1 goes under the characters, layer_2 (the chair backs) over them.

2. A walkable mask per room. The prebuilt designs are flat PNGs with no
   metadata, so "floor" is found by frequency: a 32x32 tile that repeats inside
   the room is floor, anything unique is furniture or wall. A 16px cell is
   walkable when it sits on a floor tile and nothing in the upper layers covers
   it. The page turns those masks into one world grid and paths on it.
"""
import json
import os
from PIL import Image

PACK = "/tmp/pack/b/1_Interiors/32x32/"
RB = PACK + "Room_Bulder_subfiles_32x32/"
ANIM = "/tmp/pack/b/3_Animated_objects/32x32/spritesheets/"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "static", "limezu")
ROOMS = os.path.join(OUT, "rooms")
CELL = 16

floors = Image.open(RB + "Room_Builder_Floors_32x32.png").convert("RGBA")
walls = Image.open(RB + "Room_Builder_Walls_32x32.png").convert("RGBA")
tv = Image.open(PACK + "Theme_Sorter_32x32/23_Television_and_Film_Studio_32x32.png").convert("RGBA")
conf = Image.open(PACK + "Theme_Sorter_32x32/13_Conference_Hall_32x32.png").convert("RGBA")


def blk(sheet, tx, ty, tw, th):
    return sheet.crop((tx * 32, ty * 32, (tx + tw) * 32, (ty + th) * 32))


# ------------------------------------------------------------ shared tiles
os.makedirs(OUT + "/office", exist_ok=True)
blk(floors, 12, 21, 3, 3).save(OUT + "/office/corridor.png")    # the floor between rooms
# 1x copies of the two UI pieces the canvas draws itself (name plates)
ui = Image.open("/tmp/pack/a/Modern_User_Interface_v1.0/32x32/Modern_UI_Style_1_32x32.png").convert("RGBA")
ui.crop((124, 206, 164, 216)).save(OUT + "/ui/pill1x.png")      # 40x10 name plate
ui.crop((116, 338, 172, 396)).save(OUT + "/ui/frame1x.png")     # 56x58 rounded frame
Image.open(ANIM + "animated_door_1_32x32.png").convert("RGBA").save(OUT + "/office/door.png")
# the block that fills the leftover pockets between rooms, so the corridors stay
# one constant width instead of bleeding into odd coves
walls.crop((32, 160, 64, 192)).save(OUT + "/office/block.png")


# ------------------------------------------------------------- hand props
# the pack draws held objects separately (the way its own "gift" animation does),
# so the two the bots need get cut out here
os.makedirs(OUT + "/props", exist_ok=True)
gym8 = Image.open(PACK + "Theme_Sorter_32x32/8_Gym_32x32.png").convert("RGBA")
ice = Image.open(PACK + "Theme_Sorter_32x32/24_Ice_Cream_Shop_32x32.png").convert("RGBA")


def trim(im, name):
    b = im.getbbox()
    im.crop(b).save(OUT + "/props/" + name + ".png")


trim(gym8.crop((384, 928, 416, 960)), "dumbbell")
trim(ice.crop((64, 96, 96, 128)), "icecream")


def shell(w, h, floor_block, wall_y, wallh=64):
    """A blank room the way the pack builds one: floor, back wall, side and near
    walls. Returns the under layer, ready to have furniture put in it."""
    im = Image.new("RGBA", (w, h))
    # one tile, repeated: the 3x3 blocks have a border row that reads as a seam
    tile = blk(floors, floor_block[0] + 1, floor_block[1] + 1, 1, 1)
    for y in range(wallh, h, 32):
        for x in range(0, w, 32):
            im.alpha_composite(tile, (x, y))
    wl = walls.crop((0, wall_y, 32, wall_y + 64))
    wm = walls.crop((32, wall_y, 64, wall_y + 64))
    wr = walls.crop((64, wall_y, 96, wall_y + 64))
    im.alpha_composite(wl, (0, 0))
    im.alpha_composite(wr, (w - 32, 0))
    for x in range(32, w - 32, 32):
        im.alpha_composite(wm, (x, 0))
    base = wm.crop((0, 32, 32, 64))
    for x in range(0, w, 32):
        im.alpha_composite(base, (x, h - 32))
    side = base.rotate(90, expand=True)
    for y in range(wallh, h - 32, 32):
        im.alpha_composite(side, (0, y))
        im.alpha_composite(side, (w - 32, y))
    return im


def cut(sheet, a, b, c, d):
    r = sheet.crop((a * 32, b * 32, c * 32, d * 32))
    bb = r.getbbox()
    return r.crop(bb) if bb else r


# --------------------------------------------- the game room and the music room
# Both are laid out after the two store pictures the owner sent. The pack ships
# the furniture for them on its theme sheets but no finished room file, so the
# rooms are assembled here from those same tiles.
basement = Image.open(PACK + "Theme_Sorter_32x32/14_Basement_32x32.png").convert("RGBA")
music = Image.open(PACK + "Theme_Sorter_32x32/6_Music_and_sport_32x32.png").convert("RGBA")
generic = Image.open(PACK + "Theme_Sorter_32x32/1_Generic_32x32.png").convert("RGBA")

# game room: arcade cabinets, a telly with armchairs, a bar with stools and a
# row of pool tables, like the basement in the picture
GW_, GH_ = 512, 608
g1 = shell(GW_, GH_, (0, 30), 128, 64)
g2 = Image.new("RGBA", (GW_, GH_))
arcade = cut(basement, 4, 41, 6, 43)
pool_g = cut(basement, 4, 25, 8, 28)
pool_t = cut(basement, 0, 27, 4, 30)
pool_b = cut(basement, 4, 28, 8, 31)
cues = cut(basement, 3, 25, 5, 27)
telly = cut(basement, 10, 29, 12, 31)
tvunit = cut(basement, 6, 47, 10, 50)
arm = cut(basement, 6, 33, 8, 35)
bar = cut(basement, 6, 14, 10, 16)
stool = cut(basement, 10, 19, 11, 21)
plant = cut(generic, 13, 29, 14, 31)
for x in (48, 120, 192):
    g1.alpha_composite(arcade, (x, 56))
g1.alpha_composite(cues, (300, 250))
g1.alpha_composite(tvunit, (336, 96))
g1.alpha_composite(arm, (332, 168))
g1.alpha_composite(arm, (396, 168))
g1.alpha_composite(bar, (40, 248))
g1.alpha_composite(bar, (120, 248))
for x in (55, 105, 155):
    g1.alpha_composite(stool, (x, 300))
g1.alpha_composite(plant, (452, 254))
g1.alpha_composite(arcade, (264, 56))
g1.alpha_composite(pool_g, (40, 392))
g1.alpha_composite(pool_t, (180, 392))
g1.alpha_composite(pool_b, (320, 392))
g1.save(ROOMS + "/Game_Room_layer_1.png")
g2.save(ROOMS + "/Game_Room_layer_2.png")

# music room: pianos, drum kits, guitars on stands, harp, amps and keyboards
MW_, MH_ = 640, 448
m1 = shell(MW_, MH_, (0, 12), 192, 64)
m2 = Image.new("RGBA", (MW_, MH_))
amp = cut(music, 0, 37, 2, 40)
upright = cut(music, 0, 10, 2, 12)
upright2 = cut(music, 2, 10, 4, 12)
grand = cut(music, 0, 12, 2, 15)
bench = cut(music, 0, 17, 1, 18)
drum = cut(music, 0, 18, 2, 20)
drum2 = drum
harp = cut(music, 8, 40, 10, 43)
guitar = cut(music, 6, 31, 7, 34)
guitar2 = cut(music, 6, 34, 7, 36)
bass = cut(music, 7, 31, 8, 34)
keyb = cut(music, 8, 17, 10, 18)
keyb2 = cut(music, 10, 17, 12, 18)
mic = cut(music, 6, 15, 8, 17)
conga = cut(music, 12, 11, 13, 13)
djembe = cut(music, 14, 11, 15, 13)
m1.alpha_composite(amp, (36, 44))
m1.alpha_composite(amp, (104, 44))
m1.alpha_composite(upright, (196, 74))
m1.alpha_composite(upright2, (266, 74))
m1.alpha_composite(drum, (400, 62))
m1.alpha_composite(drum2, (492, 62))
m1.alpha_composite(grand, (86, 196))
m1.alpha_composite(bench, (104, 276))
m1.alpha_composite(harp, (296, 194))
m1.alpha_composite(guitar, (420, 210))
m1.alpha_composite(guitar2, (456, 222))
m1.alpha_composite(bass, (492, 214))
m1.alpha_composite(conga, (146, 330))
m1.alpha_composite(djembe, (176, 326))
m1.alpha_composite(mic, (322, 320))
m1.alpha_composite(keyb, (448, 342))
m1.alpha_composite(keyb2, (512, 342))
m1.alpha_composite(plant, (584, 190))
m1.save(ROOMS + "/Music_Room_layer_1.png")
m2.save(ROOMS + "/Music_Room_layer_2.png")


# --------------------------------------------------------- the control room
OW, OH = 640, 448
WALLH = 64
DESK = tv.crop((96, 276, 224, 318))       # 128x42 console with screens in it
CHAIR = conf.crop((384, 224, 416, 256))   # 32x32 office chair seen from behind
RACK = tv.crop((256, 256, 288, 448))      # 32x192 equipment rack

# station = where a bot's feet go; desk sits above it, chair over the bot
STATIONS = [(112, 236), (320, 236), (528, 236), (112, 404), (320, 404), (528, 404)]

l1 = Image.new("RGBA", (OW, OH))
l2 = Image.new("RGBA", (OW, OH))

tile = blk(floors, 4, 33, 3, 3)
for y in range(WALLH, OH, 96):
    for x in range(0, OW, 96):
        l1.alpha_composite(tile, (x, y))

wl, wm, wr = walls.crop((0, 128, 32, 192)), walls.crop((32, 128, 64, 192)), walls.crop((64, 128, 96, 192))
l1.alpha_composite(wl, (0, 0))
l1.alpha_composite(wr, (OW - 32, 0))
for x in range(32, OW - 32, 32):
    l1.alpha_composite(wm, (x, 0))
# the near wall is only its top edge in this projection, same as the pack's own
# prebuilt rooms, and the side walls are the same strip turned on its side
base = wm.crop((0, 32, 32, 64))
for x in range(0, OW, 32):
    l1.alpha_composite(base, (x, OH - 32))
side = base.rotate(90, expand=True)
for y in range(WALLH, OH - 32, 32):
    l1.alpha_composite(side, (0, y))
    l1.alpha_composite(side, (OW - 32, y))

# the chair goes under the worker: seen from behind he hides most of it, which
# is what a chair pulled up to a monitor actually looks like from here
for sx, sy in STATIONS:
    l1.alpha_composite(DESK, (sx - 64, sy - 92))
    l1.alpha_composite(CHAIR, (sx - 16, sy - 36))
l1.alpha_composite(RACK, (OW - 72, WALLH + 6))

l1.save(ROOMS + "/Control_Room_layer_1.png")
l2.save(ROOMS + "/Control_Room_layer_2.png")


# ------------------------------------------------------------- walkability
# (id, [layer files], interior box) -- the box excludes the walls, everything
# inside it is decided by the tile-frequency test
DEFS = [
    ("office", ["Control_Room_layer_1.png", "Control_Room_layer_2.png"], (36, 66, 604, 414)),
    ("studio", ["Tv_Studio_Design_layer_1_32x32.png", "Tv_Studio_Design_layer_2_32x32.png",
                "Tv_Studio_Design_layer_3_32x32.png"], (32, 64, 320, 288)),
    ("gym", ["Gym_layer_1_32x32.png", "Gym_layer_2_32x32.png"], (32, 24, 578, 408)),
    ("music", ["Music_Room_layer_1.png", "Music_Room_layer_2.png"], (36, 130, 604, 414)),
    ("cafe", ["Ice_Cream_Shop_Design_layer_1_32x32.png", "Ice_Cream_Shop_Design_layer_2_32x32.png",
              "Ice_Cream_Shop_Design_layer_3_32x32.png"], (40, 96, 348, 288)),
    ("home", ["Generic_Home_1_Layer_1_32x32.png", "Generic_Home_1_Layer_2_32x32.png"], (32, 32, 416, 400)),
    ("jp", ["Japanese_Home_1_Layer_1_32x32.png", "Japanese_Home_1_Layer_2_32x32.png"], (32, 32, 580, 396)),
    ("range", ["Shooting_Range_Design_layer_1_32x32.png", "Shooting_Range_Design_layer_2_32x32.png"], (24, 32, 296, 300)),
    ("lobby", ["Condominium_Design_layer_1_32x32.png", "Condominium_Design_layer_2_32x32.png"], (24, 32, 424, 320)),
    ("game", ["Game_Room_layer_1.png", "Game_Room_layer_2.png"], (36, 66, 476, 574)),
    ("hall", ["Condominium_Design_2_layer_1_32x32.png", "Condominium_Design_2_layer_2_32x32.png"], (16, 32, 432, 176)),
]


def mask_for(files, box):
    ims = [Image.open(os.path.join(ROOMS, f)).convert("RGBA") for f in files]
    base, above = ims[0], ims[1:]
    W, H = base.size
    bpx = base.load()
    apx = [im.load() for im in above]

    counts = {}
    keys = {}
    for ty in range(H // 32):
        for tx in range(W // 32):
            k = base.crop((tx * 32, ty * 32, tx * 32 + 32, ty * 32 + 32)).tobytes()
            keys[(tx, ty)] = k
            # only tiles whose centre is inside the room proper get a vote, so a
            # long outside wall cannot win the popularity contest
            cx, cy = tx * 32 + 16, ty * 32 + 16
            if box[0] <= cx < box[2] and box[1] <= cy < box[3]:
                counts[k] = counts.get(k, 0) + 1
    floor = {k for k, n in counts.items() if n >= 4}
    # the tile test is 32px coarse, so a chair leg poisons a whole tile. For the
    # tiles it rejects, compare the 16px cell against the floor tile that belongs
    # at that spot (the pack's floors repeat every 3 tiles): if the pixels match,
    # nothing was drawn there and the cell is really free.
    phase = {}
    for (tx, ty), k in keys.items():
        if k in floor:
            ph = (tx % 3, ty % 3)
            phase.setdefault(ph, {})
            phase[ph][k] = phase[ph].get(k, 0) + 1
    phase_tile = {}
    for ph, d in phase.items():
        best = max(d.items(), key=lambda kv: kv[1])[0]
        phase_tile[ph] = Image.frombytes("RGBA", (32, 32), best).load()

    gw, gh = W // CELL, H // CELL
    rows = []
    for gy in range(gh):
        row = []
        for gx in range(gw):
            x0, y0 = gx * CELL, gy * CELL
            # the box only decides which tiles get a vote for "this is floor";
            # walkability is judged everywhere, so the openings the designs
            # already have -- their own doorways -- stay open
            ok = keys.get((x0 // 32, y0 // 32)) in floor
            if not ok:
                ref = phase_tile.get(((x0 // 32) % 3, (y0 // 32) % 3))
                if ref is not None:
                    ok = all(bpx[x, y] == ref[x % 32, y % 32]
                             for y in range(y0, y0 + CELL)
                             for x in range(x0, x0 + CELL))
            # a cell that is empty in every layer is not part of the building at
            # all: it is the corridor showing through, so it stays walkable
            cx0, cy0 = x0 + CELL // 2, y0 + CELL // 2
            inside = box[0] <= cx0 < box[2] and box[1] <= cy0 < box[3]
            if not ok and not inside:
                pts = [(x, y) for y in range(y0, y0 + CELL, 2) for x in range(x0, x0 + CELL, 2)]
                if (all(bpx[x, y][3] == 0 for x, y in pts)
                        and all(px[x, y][3] == 0 for px in apx for x, y in pts)):
                    rows_ok = True
                    row.append("1")
                    continue
            if ok:
                for px in apx:
                    if any(px[x, y][3] > 0
                           for y in range(y0, y0 + CELL, 2)
                           for x in range(x0, x0 + CELL, 2)):
                        ok = False
                        break
            row.append("1" if ok else "0")
        rows.append("".join(row))
    return W, H, rows


data = {}
for rid, files, box in DEFS:
    W, H, rows = mask_for(files, box)
    data[rid] = {"w": W, "h": H, "cell": CELL, "mask": rows}
    open_n = sum(r.count("1") for r in rows)
    print("%-8s %4dx%-4d cells %5d walkable %5d (%.0f%%)"
          % (rid, W, H, len(rows) * len(rows[0]), open_n,
             100.0 * open_n / (len(rows) * len(rows[0]))))

data["_stations"] = STATIONS
with open(os.path.join(OUT, "world_data.json"), "w") as f:
    json.dump(data, f, separators=(",", ":"))
print("wrote world_data.json")
