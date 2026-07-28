"""Cut the six extra office people out of their generated rows.

They were drawn from the same reference as `rade`, but only in the nine poses
that are worth generating: the three left facing walks are the mirror image of
the right facing ones, so they are flipped here instead of asked for again.

    python3 extract_cast.py /tmp/gen6        # <tag>__<pose>.png in one folder
"""
import os
import sys

from PIL import Image

from extract_rade import cut, key_out, frames, CHARS

# pose -> row index, same row meaning the live page reads
POSE = {
    "walk_S": 0, "type_S": 1, "walk_SE": 4, "walk_E": 5, "walk_NE": 6,
    "walk_N": 7, "react_S": 12, "sofa_sit_SE": 13, "drink_stand_S": 14,
}
MIRROR = {8: 5, 9: 6, 10: 4}          # W from E, NW from NE, SW from SE


def build(gen, tag):
    made = {}
    for pose, row in POSE.items():
        p = os.path.join(gen, "%s__%s.png" % (tag, pose))
        if not os.path.exists(p):
            print("  missing", pose)
            continue
        n, _ = cut(p, tag, row)
        made[row] = n
    d = os.path.join(CHARS, tag)
    for row, src in MIRROR.items():
        if src not in made:
            continue
        for i in range(made[src]):
            f = os.path.join(d, "r%d_%02d.png" % (src, i))
            Image.open(f).transpose(Image.FLIP_LEFT_RIGHT).save(
                os.path.join(d, "r%d_%02d.png" % (row, i)))
        made[row] = made[src]
    print("%-5s %s" % (tag, " ".join("r%d:%d" % (r, made[r]) for r in sorted(made))))


if __name__ == "__main__":
    gen = sys.argv[1]
    tags = sys.argv[2:] or sorted({f.split("__")[0] for f in os.listdir(gen) if "__" in f})
    for t in tags:
        build(gen, t)
