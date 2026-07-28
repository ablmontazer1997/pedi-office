# Isometric Office Character Sheet — Editable Prompt (v2)

Fix-list this version addresses in the existing sheet:
1. bottom row is bust-only (cut at the waist) → **every cell is full body, feet included**
2. walk cycle is flat side-view (side-scroller profile) → **true 2:1 game isometric**
3. no back views → **8 iso directions, back and back-3/4 included**
4. rows drawn at different scales / different head sizes → **one fixed cell grid and one fixed character height**
5. sitting rows are near-duplicates → **explicit, distinct pose per frame**

---

## 0. EDITABLE PARAMETERS (change only these, keep the rest verbatim)

```
CHARACTER      = young man, messy black hair, dark navy-black hoodie with hood down,
                 dark jeans, white-soled black sneakers, warm tan skin, friendly face
ART_STYLE      = 32x32-base pixel art, modern-interiors / LimeZu palette,
                 soft 3-tone shading, dark outline only on the silhouette
CELL           = 64 x 64 px cell, character occupies 44 px of height
LEAN_ANGLE     = 8        # forward torso lean while walking, in degrees from vertical
TORSO_LENGTH   = 24       # px, hip pivot to neck, used by the lean formula below
WALK_FRAMES    = 8
IDLE_FRAMES    = 6
DIRECTIONS     = S, SE, E, NE, N, NW, W, SW      # iso compass, see section 2
BACKGROUND     = fully transparent
```

---

## 1. GLOBAL RENDER CONTRACT (do not change)

- **Camera: true game isometric, 2:1 dimetric.** Elevation **26.57°**, azimuth **45°**, **orthographic**.
  No vanishing point, no perspective convergence, no foreshortening toward the horizon.
  One world tile is a **2:1 diamond** (64 px wide, 32 px tall).
- **Full body in every single cell.** Head to soles. Nothing is cropped at the waist, chest or
  knees. Bust-only / portrait cells are forbidden, including for emotion states.
- **One uniform grid.** Every cell is exactly `CELL`, one pose per cell, no cell bleed,
  no shared outlines between neighbouring cells.
- **Fixed anchor.** The character's feet sit on the **bottom-center pixel of the cell**;
  that pixel is the sprite pivot and it must not drift by more than 1 px across frames of the
  same animation. Head height must be identical (±1 px) across every cell of the whole sheet.
- **Contact shadow:** a soft dark ellipse under the feet, on its own visual layer, same size in
  every cell. Never a long cast shadow, never baked over the body.
- **Props are separate.** Chair, desk, monitor, mug, phone are drawn as separate iso objects on
  their own sheet rows so the character can be composited over any office furniture.
- Transparent background. No text, no labels, no frame numbers, no watermark, no border.

---

## 2. THE 8 ISOMETRIC DIRECTIONS

In 2:1 iso, the four world-cardinal headings project as **screen diagonals**. Draw them as:

| Name | Character shows | Moves on screen toward |
|---|---|---|
| S  | front, facing the camera, both eyes visible | down |
| SE | front 3/4, right shoulder forward | down-right |
| E  | side-front profile, one eye visible, far arm partly hidden | right, slightly down |
| NE | back 3/4, ~1/4 of the cheek visible, ear visible | up-right |
| N  | full back, no face, hair whorl and hood seam visible | up |
| NW | back 3/4 mirrored | up-left |
| W  | side-front profile mirrored | left, slightly up |
| SW | front 3/4 mirrored | down-left |

Rules:
- The E/W cells are **not** flat side-scroller profiles. The camera still looks down at 26.57°,
  so the shoulders, the top of the head and the top face of the shoes stay visible.
- N and NE/NW must read as genuinely "away from camera": no floating face, no cheated eyes.
- W/NW/SW may be pixel mirrors of E/NE/SE only if the character is symmetric; if anything is
  side-specific (bag strap, watch, hair parting), redraw instead of mirroring.

---

## 3. LEAN AND GAIT

The torso leans **`LEAN_ANGLE`° forward from vertical, in the character's own sagittal plane** —
it leans toward wherever the character is walking, not toward the screen bottom.

Convert the lean into pixels with the 2:1 projection, for a heading angle `phi` on the ground
plane (`phi = 0` is world +X = the screen-right-down diagonal):

```
d   = TORSO_LENGTH * sin(LEAN_ANGLE)        # how far the neck moves along the heading
dz  = TORSO_LENGTH * (1 - cos(LEAN_ANGLE))  # how much the neck drops

head_dx = (cos(phi) - sin(phi)) * d
head_dy = (cos(phi) + sin(phi)) * d * 0.5 - dz
```

With `TORSO_LENGTH = 24` and `LEAN_ANGLE = 8` this gives `d = 3.3 px`, and:

| Heading | head_dx | head_dy | reads as |
|---|---|---|---|
| E (screen down-right) | +3 | +1 | head pushed right |
| S (screen down) | 0 | +2 | head pushed down, body slightly compressed |
| N (screen up, away) | 0 | −2 | head pushed up, back rounded |
| W (screen up-left) | −3 | −1 | head pushed left |

Round to whole pixels. **Keep the hips on the pivot** and move only the torso and head, so the
lean never breaks the foot anchor.

Walk cycle, `WALK_FRAMES` frames, evenly keyed:
`contact → down → pass → up → contact(mirrored) → down → pass → up`.
The head bobs 1 px down on the two "down" frames and 1 px up on the two "up" frames.
The rear foot lifts so the top of the sole is visible (this is what sells the iso camera).
Arms swing opposite the legs; the arm on the far side is partly occluded by the torso.

Optional variants driven by the same formula: `LEAN_ANGLE = 2` for an idle stroll,
`8` for a normal office walk, `16` for hurrying, `24` for carrying something heavy.

---

## 4. ACTION STATES

Group A — **all 8 directions** required:
- `idle` (`IDLE_FRAMES`, breathing, one blink, weight shift)
- `walk` (`WALK_FRAMES`)
- `carry_walk` (holding a mug in both hands, `WALK_FRAMES`)
- `talk` (4, one arm gesturing)

Group B — **4 directions** (S, SE, E, NE) are enough:
- `sit_down` and `stand_up` on an office chair (4 each, real transition poses, not copies)
- `sit_idle` on the chair (4)
- `sit_type` at the desk, hands on keyboard, monitor lit (6, fingers and shoulder motion)
- `sit_drink` — raise mug, sip, lower, exhale (8, four clearly different arm heights)
- `sleep_chair` — slump back, head tilts, zzz (4)
- `sleep_desk` — head down on folded arms, zzz (4)
- `push_chair`, `open_door`, `pick_up_from_floor`, `drag_box` (4 each)
- `whiteboard_write` and `present_to_room` (4 each)
- `handshake` (4)
- `phone_scroll` standing (4)

Group C — reactions, **S and SE only, still full body**:
- `wave`, `think` (hand on chin, "?" bubble), `celebrate` (both arms up), `frustrated`
  (red anger mark), `confused`, `sad`, `error` (white speech bubble with a red X),
  `faint` (collapsed on the floor, full body, 3 frames)

Emotion is expressed by **whole-body posture plus a small floating icon above the head**,
never by cropping in to the face.

---

## 5. SHEET LAYOUT

- One image per **state**, not one image for everything.
- Inside a state image: **one row per direction**, columns = frames, left to right in time order.
- Direction rows top to bottom in the exact order `S, SE, E, NE, N, NW, W, SW`.
- Equal margins, no labels drawn into the image.

If the generator can only hold a few cells at a time, generate **one direction row per call**
and keep every other word of the prompt byte-identical between calls so the style does not drift.

---

## 6. NEGATIVE PROMPT

```
side-scroller profile, flat 2D platformer view, top-down 90 degree view, perspective camera,
vanishing point, cropped at the waist, bust portrait, headshot, half body, missing feet,
inconsistent character height, changing head size between cells, different palette per row,
duplicated identical frames, blurry, anti-aliased edges, gradient shading, 3D render,
vector art, drop shadow baked onto the body, background scenery, floor tiles, text, labels,
frame numbers, watermark, signature, border
```

---

## 7. QUICK SINGLE-ROW VERSION

For one row at a time, paste this and fill the two blanks:

> 2:1 game isometric pixel art sprite row, orthographic camera at 26.57° elevation and 45°
> azimuth, transparent background, 64x64 px cells, character 44 px tall, feet anchored to the
> bottom-center of each cell, identical head height in every cell, **full body in every cell,
> never cropped**. Character: young man, messy black hair, dark navy-black hoodie, dark jeans,
> black sneakers with white soles, 3-tone pixel shading, dark silhouette outline, soft elliptical
> contact shadow. Action: **____**. Facing: **____** (see the direction table). Torso leans 8°
> forward along the heading; hips stay on the pivot. 8 frames left to right in time order,
> each frame clearly different. No text, no labels, no background.
