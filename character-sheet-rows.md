# Office Character Sheet — One Prompt Per Row (v3)

Your current sheet has 6 rows. Below there is **one self-contained prompt per row**: copy a
single fenced block, change only the two knobs at its top (`FACING`, `LEAN_ANGLE`), and generate.
Each block repeats the style lock on purpose, so blocks never drift from each other.

**Rule that matters most:** generate one block at a time, one facing at a time. Never ask for the
whole sheet in a single image; that is what broke the scale and cropped the last row.

---

## How to use

1. Pick the row you want.
2. Set `FACING` to one of the 8 iso directions in the table below. **Run each row at least for
   `S`, `E`, `N` and `NE`** — `N` and `NE` are the back views that are missing today.
3. Keep every other word identical between runs.
4. Paste the negative prompt (bottom of this file) into the negative field every time.

### The 8 iso facings

| FACING | what the sprite shows | on-screen movement |
|---|---|---|
| `S`  | front, facing camera, both eyes | down |
| `SE` | front 3/4, right shoulder leading | down-right |
| `E`  | side-front, one eye, far arm partly hidden, top of head visible | right, slightly down |
| `NE` | **back 3/4**, only a sliver of cheek and one ear | up-right |
| `N`  | **full back**, no face at all | up |
| `NW` | back 3/4, mirrored | up-left |
| `W`  | side-front, mirrored | left, slightly up |
| `SW` | front 3/4, mirrored | down-left |

### Back-view rule (`N`, `NE`, `NW`) — paste this into any row you render from behind

> Back view: no facial features whatsoever, not even cheated eyes. Show the back of the skull with
> the hair whorl, the messy fringe silhouetted at the edges, both ears in silhouette, the hood
> lying flat between the shoulder blades with a visible seam, the hoodie's back yoke, the rear
> pocket line of the jeans, and the heel and back sole of both shoes. Shoulder blades shift with
> the arm swing. The head is still seen slightly from above because the camera is at 26.57°.

---

## ROW 1 — WALK CYCLE

```
FACING = S            # run again for SE, E, NE, N, NW, W, SW
LEAN_ANGLE = 8        # 2 strolling, 8 normal, 16 hurrying, 24 carrying something heavy

A single horizontal row of 8 pixel-art sprite frames, left to right in time order, one walk
cycle. True 2:1 game isometric, orthographic camera, elevation 26.57 degrees, azimuth 45
degrees, no perspective and no vanishing point. Transparent background. Each cell is 64x64 px,
one pose per cell, the character is 44 px tall, the feet rest on the bottom-center pixel of the
cell and that anchor does not drift more than 1 px between frames, and the head height is
identical in every frame.
Full body in every frame, head to soles, never cropped.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles, warm tan skin, friendly face. 32x32-base pixel art, 3-tone
shading, dark outline on the silhouette only, soft elliptical contact shadow under the feet.
Facing FACING.
Frames in order: contact, down, passing, up, contact mirrored, down, passing, up.
The torso leans LEAN_ANGLE degrees forward along the direction of travel while the hips stay on
the anchor; the head bobs 1 px down on the two down frames and 1 px up on the two up frames.
The rear foot lifts far enough that the top face of its sole is visible, which is what proves
the isometric camera. Arms swing opposite the legs, the far arm is partly occluded by the torso.
No text, no labels, no frame numbers, no background scenery.
```

---

## ROW 2 — IDLE AND TURN IN PLACE

```
FACING = S            # run again for E, N, NE
LEAN_ANGLE = 2

A single horizontal row of 6 pixel-art sprite frames, left to right, an idle loop. True 2:1 game
isometric, orthographic camera, elevation 26.57 degrees, azimuth 45 degrees, no perspective.
Transparent background. Each cell is 64x64 px, character 44 px tall, feet anchored to the
bottom-center pixel of the cell, identical head height in every frame.
Full body in every frame, never cropped.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles, warm tan skin. 32x32-base pixel art, 3-tone shading, dark
silhouette outline, soft elliptical contact shadow.
Facing FACING.
Frames in order: neutral stance, chest rises 1 px, chest falls, eyes closed for a blink, weight
shifts onto the other hip, back to neutral. The torso leans LEAN_ANGLE degrees forward. The
character never leaves the anchor and never takes a step.
No text, no labels, no background scenery.
```

---

## ROW 3 — SITTING AT THE DESK, TYPING

```
FACING = SE           # run again for S, E, NE  (NE is the over-the-shoulder back view)

A single horizontal row of 8 pixel-art sprite frames, left to right, a typing loop of a person
sitting on an office chair at a desk. True 2:1 game isometric, orthographic camera, elevation
26.57 degrees, azimuth 45 degrees, no perspective. Transparent background. Each cell is 64x64
px, identical scale and identical seat height in every frame, the chair's caster base rests on
the bottom-center anchor of the cell.
The whole figure is visible from head to shoes, including both feet on the floor or on the chair
base. Never cropped at the waist or the desk edge.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles. 32x32-base pixel art, 3-tone shading, dark silhouette outline.
Props, drawn in the same isometric projection: a black office chair with armrests and a
five-caster base, a dark desk, a flat monitor whose screen glows faint purple, a keyboard.
Facing FACING.
Frames in order: hands hover, left hand strikes, both hands typing, right hand strikes, pause and
read the screen, lean 3 px closer to the monitor, type fast, settle back.
Each frame must be visibly different from its neighbours: change finger position, elbow angle,
shoulder height and head tilt, not just one pixel.
No text on the screen beyond a small glowing logo, no labels, no background scenery.
```

---

## ROW 4 — SITTING IN THE CHAIR WITH A MUG

```
FACING = SE           # run again for S, E, NE

A single horizontal row of 8 pixel-art sprite frames, left to right, one full drink cycle of a
person seated in an office chair holding a mug. True 2:1 game isometric, orthographic camera,
elevation 26.57 degrees, azimuth 45 degrees, no perspective. Transparent background. Cells are
64x64 px, identical scale and seat height in every frame, the chair base on the bottom-center
anchor.
Full figure visible, head to shoes, never cropped.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles. 32x32-base pixel art, 3-tone shading, dark silhouette outline.
Prop: a black office chair with armrests and a five-caster base, and a white ceramic mug.
Facing FACING.
Frames in order: mug resting on the lap, both hands lift it to chest height, lift to chin, tilt
and sip with the eyes closed, hold the sip, lower to chest, a small curl of steam rises and the
character exhales with a content half-smile, mug returns to the lap.
The mug must be at a clearly different height in each of the first six frames.
No text, no labels, no background scenery.
```

---

## ROW 5 — FALLING ASLEEP

```
FACING = SE           # run again for S, E, NE
VARIANT = chair       # chair = slumping back in the office chair, desk = head down on the desk

A single horizontal row of 8 pixel-art sprite frames, left to right, a person gradually falling
asleep. True 2:1 game isometric, orthographic camera, elevation 26.57 degrees, azimuth 45
degrees, no perspective. Transparent background. Cells are 64x64 px, identical scale and seat
height in every frame, anchored at the bottom-center.
Full figure visible, head to shoes, never cropped.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles. 32x32-base pixel art, 3-tone shading, dark silhouette outline.
Prop: a black office chair with armrests and a five-caster base; for VARIANT desk also a dark
desk in the same projection.
Facing FACING.
Frames for VARIANT chair, in order: sitting upright and tired, a wide yawn with one hand near the
mouth, eyelids at half, head tips back against the backrest, arms go slack over the armrests,
legs slide forward, fully asleep and slumped, a small white pixel "zzz" floats up and to the
right of the head.
Frames for VARIANT desk, in order: upright, yawning, elbows onto the desk, head sinks onto the
folded forearms, cheek flattens against the sleeve, shoulders settle, deep sleep, "zzz" floats up.
The "zzz" appears only in the last two or three frames and never overlaps the head.
No text beyond the zzz, no labels, no background scenery.
```

---

## ROW 6 — REACTIONS AND EMOTES (full body, not portraits)

```
FACING = S            # run again for SE, and for N if you want back-facing reactions

A single horizontal row of 8 pixel-art sprite frames, left to right, eight different emotional
reactions of the same standing character. True 2:1 game isometric, orthographic camera,
elevation 26.57 degrees, azimuth 45 degrees, no perspective. Transparent background. Cells are
64x64 px, the character is 44 px tall in every single frame with identical head size, feet
anchored to the bottom-center pixel.
Every frame is a FULL BODY standing sprite, head to shoes. No portraits, no busts, no headshots,
nothing cropped at the chest.
Character: young man, messy black hair, dark navy-black hoodie with the hood down, dark jeans,
black sneakers with white soles. 32x32-base pixel art, 3-tone shading, dark silhouette outline,
soft elliptical contact shadow.
Facing FACING.
Frames in order:
1 happy, standing tall, arms relaxed, wide smile
2 waving, one arm raised beside the head
3 thinking, one hand on the chin, weight on one hip, small white "?" floating above the head
4 sad, shoulders dropped, head down, a single blue tear pixel
5 worried, hands clasped in front, a blue sweat drop beside the temple
6 angry, fists clenched at the sides, leaning forward, a small red anger cross above the head
7 celebrating, both arms straight up, one foot off the ground, two small white motion strokes
8 error, arms half raised in a shrug, a small white speech bubble above with a red X in it
Emotion is carried by the whole-body posture; the floating icon is a small accent only, and it
never replaces the body.
No text apart from the icons described, no labels, no background scenery.
```

---

## NEGATIVE PROMPT (use with every row)

```
side-scroller profile, flat 2D platformer view, front orthographic view, top-down 90 degree view,
perspective camera, vanishing point, cropped at the waist, bust, portrait, headshot, half body,
missing feet, missing legs, inconsistent character height, changing head size between frames,
different palette between frames, duplicated identical frames, blurry, anti-aliased edges,
gradient shading, 3D render, vector art, cast shadow baked onto the body, floor tiles, room
background, text, labels, frame numbers, watermark, signature, grid lines, border
```
