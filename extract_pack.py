"""Cut the RADE pixel-office sheet into individual sprites.

The sheet is one flat image: every sprite sits on the same dark panel colour, so
a sprite is just a connected blob of "not the panel background". Filling the
holes of each blob gives a silhouette, and keeping the original pixels inside
that silhouette preserves the dark details (hair, monitors) that a per-pixel
colour key would punch out.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SHEET = os.path.join(HERE, "art", "pack.jpg")
OUT = os.path.join(HERE, "art", "sprites")

# interiors of the labelled panels, minus their titles
PANELS = {
    # panel interiors only: the rounded frame and the title would otherwise come
    # out as one blob that swallows the first row of sprites
    "floor":   (438, 42, 772, 100),
    "wall":    (438, 136, 772, 246),
    "door":    (438, 278, 772, 496),
    "furni":   (16, 528, 534, 824),
    "elec":    (554, 528, 772, 686),
    "deco":    (554, 710, 772, 824),
    "extra":   (16, 858, 306, 1016),
    "anim":    (324, 868, 946, 1016),
    "chars":   (796, 56, 1526, 496),
    "ui":      (796, 576, 1294, 710),
    "fx":      (1316, 576, 1526, 810),
    "logico":  (966, 858, 1324, 892),
    "weather": (966, 904, 1324, 1006),
}

# how far to grow blobs before grouping: characters need their speech bubble
# and their body treated as one sprite, plain objects do not
DILATE = {"chars": 3, "anim": 2}

MIN_AREA = 40

# Sprites the blob finder cannot separate: on the sheet they touch each other
# (desk row) or share a drop shadow (seated poses), so their boxes are read off
# the sheet by hand.
CHAR_ROW_Y = [60, 155, 248, 343, 438]
CHAR_POSE = {           # x0, x1, y offset from the row top, height
    "type_a":  (874, 942, 0, 76),
    "type_b":  (936, 1004, 0, 76),
    "error":   (1286, 1352, 0, 78),
    "sleep":   (1355, 1452, 0, 82),
    "cheer":   (1452, 1532, 0, 78),
}
MANUAL = {
    "desk":       (12, 532, 81, 596),
    "chair_a":    (95, 527, 142, 599),
    "chair_b":    (156, 527, 202, 599),
    "station":    (215, 526, 278, 588),
    "monitor":    (285, 526, 332, 576),
    "keyboard":   (333, 536, 364, 564),
    "mouse":      (303, 566, 322, 582),
    "rack_a":     (554, 534, 614, 630),
    "rack_b":     (626, 534, 686, 630),
    "rack_c":     (693, 538, 748, 600),
    "rack_d":     (713, 590, 780, 655),
    "switch":     (573, 628, 652, 670),
    "door_server": (543, 285, 637, 457),
    "door_rade":  (608, 283, 700, 457),
    "neon_rade":  (650, 288, 703, 338),
    "poster":     (709, 295, 759, 373),
}


def panel_bg(a):
    """Most common colour in the panel — the flat backdrop."""
    flat = a.reshape(-1, 3).astype(np.int32)
    key = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    vals, counts = np.unique(key, return_counts=True)
    k = vals[counts.argmax()]
    return np.array([(k >> 16) & 255, (k >> 8) & 255, k & 255], np.int32)


def cut(name, box, thresh=26, dilate=1, min_area=MIN_AREA):
    im = Image.open(SHEET).convert("RGB").crop(box)
    a = np.asarray(im).astype(np.int32)
    bg = panel_bg(a)
    d = np.abs(a - bg).sum(2)
    mask = d > thresh
    # JPEG ringing leaves single stray pixels; drop them before grouping
    mask = ndimage.binary_opening(mask, np.ones((2, 2)))
    grown = ndimage.binary_dilation(mask, np.ones((dilate * 2 + 1, dilate * 2 + 1)))
    lab, n = ndimage.label(grown)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        blob = (lab[sl] == i)
        h, w = blob.shape
        # leftovers of the panel frame: a hairline that spans most of the panel
        if blob.sum() < min_area or h < 5 or w < 5 or w > 0.55 * a.shape[1]:
            continue
        solid = ndimage.binary_fill_holes(blob)
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        rgb = a[sl].astype(np.uint8)
        alpha = (solid * 255).astype(np.uint8)
        sp = np.dstack([rgb, alpha])
        out.append({
            "box": [box[0] + x0, box[1] + y0, box[0] + x1, box[1] + y1],
            "w": x1 - x0, "h": y1 - y0,
            "img": Image.fromarray(sp, "RGBA"),
        })
    # reading order: rows top-to-bottom, then left-to-right inside a row
    out.sort(key=lambda s: (round(s["box"][1] / 40), s["box"][0]))
    for i, s in enumerate(out):
        s["id"] = "%s_%02d" % (name, i)
        s["img"].save(os.path.join(OUT, s["id"] + ".png"))
    return out


def contact(name, sprites, cell=200, cols=8):
    """Fixed cells so one oversized blob cannot squash the rest."""
    if not sprites:
        return
    from PIL import ImageDraw
    rows = (len(sprites) + cols - 1) // cols
    sheet = Image.new("RGB", (cell * cols, cell * rows), (28, 24, 44))
    d = ImageDraw.Draw(sheet)
    for i, s in enumerate(sprites):
        x, y = (i % cols) * cell, (i // cols) * cell
        k = min(4, max(1, int(min((cell - 24) / s["w"], (cell - 30) / s["h"]))))
        im = s["img"].resize((s["w"] * k, s["h"] * k), Image.NEAREST)
        sheet.paste(im, (x + (cell - im.width) // 2, y + 22 + (cell - 30 - im.height) // 2), im)
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(60, 52, 90))
        d.text((x + 5, y + 6), "%d  %dx%d" % (i, s["w"], s["h"]), fill=(255, 220, 90))
    sheet.save(os.path.join(HERE, "art", "contact_%s.png" % name))


def cut_one(name, box, thresh=26):
    """Hand-picked box: key out the backdrop, keep the largest silhouette."""
    im = Image.open(SHEET).convert("RGB").crop(box)
    a = np.asarray(im).astype(np.int32)
    bg = panel_bg(a)
    mask = np.abs(a - bg).sum(2) > thresh
    mask = ndimage.binary_opening(mask, np.ones((2, 2)))
    lab, n = ndimage.label(ndimage.binary_dilation(mask, np.ones((5, 5))))
    if n:
        keep = 1 + np.argmax([(lab == i).sum() for i in range(1, n + 1)])
        solid = ndimage.binary_fill_holes(lab == keep)
    else:
        solid = mask
    sp = np.dstack([a.astype(np.uint8), (solid * 255).astype(np.uint8)])
    im = Image.fromarray(sp, "RGBA").crop(Image.fromarray(sp, "RGBA").getbbox())
    im.save(os.path.join(OUT, name + ".png"))
    return {"id": name, "w": im.width, "h": im.height, "box": list(box)}


def manual():
    out = []
    for name, box in MANUAL.items():
        out.append(cut_one(name, box))
    for b, top in enumerate(CHAR_ROW_Y, start=1):
        for pose, (x0, x1, dy, h) in CHAR_POSE.items():
            out.append(cut_one("bot%d_%s" % (b, pose), (x0, top + dy, x1, top + dy + h)))
    contact("manual", [dict(s, img=Image.open(os.path.join(OUT, s["id"] + ".png"))) for s in out], cols=6)
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1:] or list(PANELS) + ["manual"]
    index = {}
    if "manual" in want:
        want.remove("manual")
        index["manual"] = manual()
        print("manual", len(index["manual"]))
    for name in want:
        sprites = cut(name, PANELS[name], dilate=DILATE.get(name, 1))
        contact(name, sprites)
        index[name] = [{"id": s["id"], "w": s["w"], "h": s["h"], "box": s["box"]} for s in sprites]
        print(name, len(sprites))
    p = os.path.join(HERE, "art", "index.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(index)
    json.dump(old, open(p, "w"), indent=1)
