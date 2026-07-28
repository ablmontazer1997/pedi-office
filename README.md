# pedi-office

A pixel-art office that shows the state of the Claude bots running on this box,
and a living room full of people who walk around inside it.

Two halves:

* **the status server** — `server.py` reads each bot's tmux pane, because the
  pane text is the only thing that actually knows whether a bot is running,
  idle or gone. Nothing on the dashboard is a placeholder.
* **the room** — `static/live.html` paints an isometric office on a canvas and
  walks seven characters around it with real collision, A\* pathfinding and
  depth sorting.

## The room

    layout.json          what the editor placed: asset, x, y, z, flip
    bake_scene.py        turns that into static/office/scene.json
    static/live.html     draws it and runs the people
    static/editor.html   drag the furniture around

`bake_scene.py` is where the geometry is decided once, so the page never has to
guess:

* **the collision grid** — 10 px cells. A prop blocks the bottom 62 % of its
  own sprite, which is the part standing on the floor; the monitor drawn above
  a desk is not floor. Obstacles grow by one cell, then only the largest
  4-connected region survives. It has to be 4-connected: the page's A\* refuses
  to cut a corner, so two areas touching only diagonally are not connected for
  a character, and calling them one region left people staring at a sofa they
  could never reach.
* **the spots** — where someone is sent (a desk, the sofa, the coffee counter)
  and where the sprite is drawn once there, with the depth key that furniture
  needs. Every approach point is snapped onto a cell that is genuinely
  standable.
* **the frames** — each character's PNGs, halved and quantised on the way out
  (64 MB of sheets becomes 7 MB of page), each with the x of its own torso so
  the sprite hangs from the body rather than from the middle of its bounding
  box. A full-stride frame is 240 px wide and a passing frame 157; centring on
  the frame throws the body sideways twice per step.

## The characters

`extract_rade.py` and `extract_cast.py` cut generated sheets into frames.

The sheets come back on a flat magenta field. The background is found by
connectivity, not by colour distance — bright pink hair sits close enough to
magenta that a colour key ate it — so any near-magenta region reaching the edge
of the sheet is background, and everything walled off inside the silhouette is
the character. Only the one pixel ring where they meet is un-mixed, which is
what removes the violet fringe.

Rows, as the page reads them:

    r0  walk S      r4  walk SE   r8   walk W     r12  reactions
    r1  at a desk   r5  walk E    r9   walk NW    r13  sitting
    r2  mug         r6  walk NE   r10  walk SW    r14  standing with a mug
    r3  asleep      r7  walk N    r11  at a desk, from behind

The three left-facing walks are mirrored from the right-facing ones.

## Running it

    python3 bake_scene.py       # layout.json -> static/office/scene.json
    python3 server.py           # serves static/ on :9271

`token.txt` holds the secret that anything destructive needs; reading status
does not. It is not in this repository.
