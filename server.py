"""RADE OFFICE — live status of every Claude bot on this box, plus the machine.

Each bot runs as `claude` inside its own tmux server (socket = bot name), so the
pane text is the single source of truth: if the session is gone the bot is off,
if the pane shows Claude's live spinner it is running, otherwise it is idle.

Everything reported here is measured. Nothing on the dashboard is a placeholder.
"""
import copy
import json
import os
import re
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
PORT = int(os.environ.get("BOTWORLD_PORT", "9271"))

# The page is reachable from the internet, so anything that can kill a bot needs
# the token; reading the status does not.
TOKEN = open(os.path.join(HERE, "token.txt")).read().strip()

# (tmux socket / session name, display name, owner, accent colour)
# The order is also the casting: the room hands its characters out down this
# list, so moving a name moves which body it wears.
BOTS = [
    ("gorzali", "Gorz Ali", "گرز علی", "#7cc4ff"),
    ("mardhesabi", "Mard Hesabi", "مرد حسابی", "#ff6b6b"),
    ("bijan", "Bijan", "بیژن", "#c77dff"),
    ("kolsoom", "Kolsoom Akbari", "کلثوم اکبری", "#ffb020"),
    ("sami", "Sami", "سمی", "#5ef08a"),
    ("tom", "Tom", "تام", "#4ecdc4"),
]

# These three are systemd units with Restart=always. Stopping them needs root,
# which this user does not have.
SYSTEMD = {"gorzali", "sami", "bijan"}

# While a turn runs Claude shows a live line like "✻ Sautéing… (4m 37s · ↓ 17k
# tokens)"; when the turn ends the same line is rewritten in the past tense
# ("✻ Cogitated for 11m 28s"), so the trailing "…" is what means "busy".
BUSY = re.compile(r"esc to interrupt|^\s*[✻✽✶✳✢✴✱*]\s+\S+…", re.M)
SPIN = re.compile(r"^\s*[✻✽✶✳✢✴✱*]\s+\w")
CTX_K = re.compile(r"ctx:\s*(\d+)k/(\d+)k")
CTX_PCT = re.compile(r"(\d+)%\s+context")
MODEL = re.compile(r"(Opus|Sonnet|Haiku)\s+([\d.]+)")

LOGS = deque(maxlen=300)
_log_seq = [0]
_last_line = {}
_last_state = {}
_busy_at = {}
# when a restart was asked for. Until the session answers again the bot is
# neither off nor idle, it is coming back, and the summary says so.
_restart_at = {}
RESTART_GRACE = 90
_cache = {"t": 0.0, "data": None}
_cpu_prev = [None]
_api = {"ok": None, "code": "…", "t": 0}

LOGIN = """<!doctype html><meta charset=utf-8><title>RADE OFFICE</title>
<meta name=viewport content="width=device-width,initial-scale=1">
<style>
@font-face{font-family:"BoldPixels";src:url("font/boldpixels.woff2") format("woff2"),
 url("font/boldpixels.woff") format("woff");font-display:swap}
*{box-sizing:border-box}
html,body{height:100%;margin:0;background:#0b0913;color:#f2ead9;
 font-family:"BoldPixels","Courier New",monospace;letter-spacing:.5px;
 display:grid;place-items:center;overflow:hidden}
/* the control room itself, blurred back, as the wallpaper */
#bg{position:fixed;inset:0;background:#0b0913 url("limezu/rooms/Tv_Studio_Design_layer_1_32x32.png")
 center/704px auto no-repeat;image-rendering:pixelated;opacity:.30}
#veil{position:fixed;inset:0;background:radial-gradient(60% 60% at 50% 45%,
 #0b091300,#0b0913dd 100%)}
form{position:relative;width:min(430px,92vw);text-align:center;color:#4a3524;
 border-style:solid;border-width:30px;
 border-image:url("limezu/ui/panel.png") 38 fill stretch;image-rendering:pixelated}
h1{font-size:17px;letter-spacing:3px;margin:2px 0 4px;color:#3a2a18}
p{font-size:11px;color:#7a5a3a;margin:0 0 16px}
input{font:inherit;font-size:13px;width:100%;height:44px;padding:0 14px;
 color:#3a2a18;background:none;border-style:solid;border-width:14px;
 border-image:url("limezu/ui/plate.png") 20 fill stretch;image-rendering:pixelated;
 text-align:center;letter-spacing:2px}
input:focus{outline:none;filter:brightness(1.08)}
button{font:inherit;font-size:12px;cursor:pointer;color:#4a3524;margin-top:14px;
 padding:8px 18px;min-width:150px;background:none;border-style:solid;border-width:13px;
 border-image:url("limezu/ui/frame2.png") 13 fill stretch;image-rendering:pixelated}
button:hover{filter:brightness(1.12)}
a{display:block;margin-top:16px;font-size:11px;color:#7a5a3a}
a:hover{color:#9a2f1e}
</style>
<div id=bg></div><div id=veil></div>
<form method=get>
 <h1>RADE OFFICE</h1>
 <p>ACCESS TOKEN REQUIRED</p>
 <input name=k type=password placeholder="• • • • • • • •" autofocus>
 <br><button>ENTER</button>
 <a href="world.html">or just look around &rsaquo;</a>
</form>"""


def log(who, msg, level="info"):
    _log_seq[0] += 1
    LOGS.append({"n": _log_seq[0], "t": time.strftime("%H:%M:%S"),
                 "who": who, "msg": msg, "level": level})


def sh(args, timeout=5):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


# ------------------------------------------------------------------- machine
def cpu_percent():
    """Percentage busy since the previous call, straight from /proc/stat."""
    try:
        parts = [int(v) for v in open("/proc/stat").readline().split()[1:8]]
    except Exception:
        return None
    idle, total = parts[3] + parts[4], sum(parts)
    prev = _cpu_prev[0]
    _cpu_prev[0] = (idle, total)
    if not prev:
        return None
    di, dt = idle - prev[0], total - prev[1]
    return round((1 - di / dt) * 100) if dt > 0 else None


def machine():
    mem = {}
    for line in open("/proc/meminfo"):
        k, _, v = line.partition(":")
        mem[k] = int(v.split()[0])
    total, avail = mem["MemTotal"], mem.get("MemAvailable", mem["MemFree"])
    st = os.statvfs("/")
    disk_used = 1 - st.f_bavail / st.f_blocks
    up = float(open("/proc/uptime").read().split()[0])
    d, r = divmod(int(up), 86400)
    h, r = divmod(r, 3600)
    return {
        "cpu": cpu_percent(),
        "ram": round((1 - avail / total) * 100),
        "ram_gb": round(total / 1048576, 1),
        "disk": round(disk_used * 100),
        "disk_free_gb": round(st.f_bavail * st.f_frsize / 1e9),
        "load": round(os.getloadavg()[0], 2),
        "cores": os.cpu_count(),
        "uptime": "%dd %dh %dm" % (d, h, r // 60),
        "clock": time.strftime("%H:%M:%S"),
        "date": time.strftime("%a %d %b").upper(),
    }


def api_probe():
    """Is the Anthropic API actually reachable through the bots' proxy?"""
    while True:
        try:
            op = urllib.request.build_opener(urllib.request.ProxyHandler(
                {"https": "http://127.0.0.1:10808", "http": "http://127.0.0.1:10808"}))
            req = urllib.request.Request("https://api.anthropic.com/v1/models", method="GET")
            try:
                with op.open(req, timeout=20) as r:
                    code = r.status
            except urllib.error.HTTPError as e:
                code = e.code          # 401 still proves the endpoint answered
            was = _api["ok"]
            _api.update(ok=True, code="%d OK" % code if code < 400 else "%d AUTH" % code,
                        t=time.time())
            if was is False:
                log("system", "API connection restored", "ok")
        except Exception as e:
            was = _api["ok"]
            _api.update(ok=False, code=type(e).__name__[:14], t=time.time())
            if was is not False:
                log("system", "API unreachable: %s" % type(e).__name__, "err")
        time.sleep(45)


# --------------------------------------------------------------- token usage
# What a bot has actually spent today, read off the transcript Claude Code
# writes as it works. The pane can only ever show the turn in progress, so it is
# the transcript or nothing — and nothing is not an option here, a made up
# number on this dashboard would be worse than an empty field.
HOMEDIR = os.path.expanduser("~")
PROJDIR = os.path.join(HOMEDIR, "projects")
USAGE = [("in", "input_tokens"), ("out", "output_tokens"),
         ("read", "cache_read_input_tokens"), ("write", "cache_creation_input_tokens")]
_tok = {}                      # bot -> today's counters
_toff = {}                     # transcript -> bytes already counted


def transcripts(bot_id):
    """The folder Claude Code logs this bot's session into.

    Three of these bots run against their own CLAUDE_CONFIG_DIR, so the path
    cannot be assumed: it is read from the same bring-up script systemd runs,
    which is the only place that knows.
    """
    cfg = os.path.join(HOMEDIR, ".claude")
    cwd = os.path.join(PROJDIR, bot_id)
    try:
        txt = open(os.path.join(PROJDIR, bot_id, "bring-up.sh")).read()
    except OSError:
        txt = ""
    m = re.search(r'CLAUDE_CONFIG_DIR="?([^"\n]+)"?', txt)
    if m:
        cfg = m.group(1)
    m = re.search(r'^cd "?([^"\n]+)"?', txt, re.M)
    if m:
        cwd = m.group(1)
    for a, b in (("${HOME}", HOMEDIR), ("$HOME", HOMEDIR), ("~", HOMEDIR)):
        cfg, cwd = cfg.replace(a, b), cwd.replace(a, b)
    return os.path.join(cfg, "projects", cwd.replace("/", "-"))


def _local_day(ts):
    try:
        import calendar
        return time.strftime("%Y-%m-%d",
                             time.localtime(calendar.timegm(time.strptime(ts[:19],
                                                            "%Y-%m-%dT%H:%M:%S"))))
    except (ValueError, TypeError):
        return None


def count_tokens(bot_id):
    """Add up today's usage, reading only what has been written since last time.

    A live transcript is hundreds of megabytes, so it is never re-read: every
    file remembers how far it was counted and each pass picks up from there,
    stopping at the last complete line so a half-written record is not lost.
    """
    day = time.strftime("%Y-%m-%d")
    acc = _tok.get(bot_id)
    if not acc or acc["day"] != day:
        # only the day's tally starts again; the offsets do not, or every line
        # already counted would be counted a second time
        acc = _tok[bot_id] = {"day": day, "in": 0, "out": 0, "read": 0,
                              "write": 0, "turns": 0}
    d = transcripts(bot_id)
    if not os.path.isdir(d):
        return acc
    now = time.time()
    for name in sorted(os.listdir(d)):
        if not name.endswith(".jsonl"):
            continue
        p = os.path.join(d, name)
        try:
            st = os.stat(p)
        except OSError:
            continue
        if now - st.st_mtime > 26 * 3600:      # yesterday's sessions are done
            continue
        off = _toff.get(p, 0)
        if st.st_size < off:                   # truncated or replaced
            off = 0
        if st.st_size <= off:
            continue
        with open(p, "rb") as fh:
            fh.seek(off)
            buf = fh.read(st.st_size - off)
        cut = buf.rfind(b"\n")
        if cut < 0:
            continue
        _toff[p] = off + cut + 1
        for raw in buf[:cut].split(b"\n"):
            if b'"usage"' not in raw:          # most lines are tool output
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                continue
            u = (rec.get("message") or {}).get("usage")
            if not u or _local_day(rec.get("timestamp")) != day:
                continue
            for k, field in USAGE:
                acc[k] += u.get(field) or 0
            if u.get("output_tokens"):
                acc["turns"] += 1
    return acc


def token_loop():
    while True:
        for sock, _, _, _ in BOTS:
            try:
                count_tokens(sock)
            except Exception:
                pass
        time.sleep(60)


# ---------------------------------------------------------------------- bots
def probe(sock):
    alive = subprocess.run(["tmux", "-L", sock, "has-session", "-t", sock],
                           capture_output=True, timeout=5).returncode == 0
    if not alive:
        return {"state": "off", "ctx": None, "ctxk": None, "ctxmax": None,
                "model": None, "line": "", "pane": []}

    pane = sh(["tmux", "-L", sock, "capture-pane", "-p", "-t", sock])
    ctx = ctxk = ctxmax = None
    m = CTX_K.search(pane)
    if m:
        ctxk, ctxmax = int(m.group(1)), int(m.group(2))
        ctx = round(ctxk / max(ctxmax, 1) * 100)
    else:
        m = CTX_PCT.search(pane)
        if m:
            ctx = int(m.group(1))
    mm = MODEL.search(pane)
    line = ""
    for l in reversed(pane.splitlines()):
        if SPIN.match(l):
            line = l.strip()
            break
    # capture-pane sometimes lands mid-redraw and misses the spinner for a frame,
    # which made the state flap every poll; hold "running" for a few seconds after
    # the last time the spinner was actually seen.
    if BUSY.search(pane):
        _busy_at[sock] = time.time()
    state = "running" if time.time() - _busy_at.get(sock, 0) < 8 else "idle"
    # a session whose context is full cannot take another turn: that is a fault,
    # not idleness, and it is exactly what you want the dashboard to shout about
    if ctx is not None and ctx >= 98:
        state = "error"
    # the tail of the session itself, so the monitors on the dashboard can show
    # what the bot is actually doing rather than a decorative glow
    tail = [l.rstrip() for l in pane.splitlines() if l.strip()][-22:]
    return {"state": state, "ctx": ctx, "ctxk": ctxk, "ctxmax": ctxmax,
            "model": (mm.group(0) if mm else None), "line": line, "pane": tail}


def status():
    if time.time() - _cache["t"] < 2.0 and _cache["data"]:
        return _cache["data"]
    out = []
    for i, (sock, label, fa, colour) in enumerate(BOTS):
        info = probe(sock)
        since = time.time() - _restart_at.get(sock, 0)
        if since < RESTART_GRACE and info["state"] in ("off", "idle"):
            info["updating"] = True          # asked to restart, not back yet
        elif sock in _restart_at and info["state"] == "running":
            _restart_at.pop(sock, None)      # it answered: it is just working now
        info.update({"id": sock, "name": label, "fa": fa, "color": colour,
                     "n": i + 1, "managed": sock in SYSTEMD,
                     "tokens": dict(_tok.get(sock) or {})})
        out.append(info)

        if _last_state.get(sock) != info["state"]:
            if _last_state.get(sock) is not None:
                lvl = {"running": "ok", "error": "err", "off": "warn"}.get(info["state"], "info")
                log(label, "state -> %s" % info["state"].upper(), lvl)
            _last_state[sock] = info["state"]
        # the spinner line ticks its elapsed time every second; only log it when
        # the actual activity changes, or the log becomes one bot shouting
        key = re.sub(r"^\S+\s+", "", info["line"]).split("(")[0].strip()
        if info["line"] and _last_line.get(sock) != key:
            _last_line[sock] = key
            log(label, info["line"], "ok" if info["state"] == "running" else "info")

    data = {"ts": int(time.time()), "bots": out, "machine": machine(),
            "api": {"ok": _api["ok"], "code": _api["code"]},
            "logs": list(LOGS)[-60:]}
    _cache.update(t=time.time(), data=data)
    return data


def act(bot_id, action):
    """restart / stop / start a bot. Returns (ok, message)."""
    known = {b[0]: b[1] for b in BOTS}
    if bot_id not in known:
        return False, "unknown bot"
    name = known[bot_id]
    runner = os.path.join("/home/rade/projects", bot_id, "run-service.sh")
    managed = bot_id in SYSTEMD

    if action == "stop" and managed:
        return False, "needs root: systemd would restart it"

    if action in ("restart", "stop"):
        subprocess.run(["tmux", "-L", bot_id, "kill-server"], capture_output=True, timeout=10)
        log(name, "%s requested" % action, "warn")
        if action == "restart":
            _restart_at[bot_id] = time.time()
        if action == "stop":
            return True, "stopped"
        if managed:
            return True, "restarting via systemd"
        time.sleep(1)

    if action in ("restart", "start"):
        if managed:
            return True, "systemd will bring it back"
        if not os.path.isfile(runner):
            return False, "run-service.sh not found"
        _restart_at[bot_id] = time.time()
        subprocess.Popen(["setsid", "bash", runner], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
        log(name, "start requested", "ok")
        return True, "started"

    return False, "bad action"


# what a visitor without the token may load: the world page and its art only
PUBLIC_PAGES = {"world.html", "world.js", "room.html", "live.html"}
PUBLIC_DIRS = {"limezu", "font", "office", "ui"}


def public_status():
    """The same payload with everything private stripped: no session text, no
    logs, no model, and a flag the page uses to hide its controls."""
    # status() hands back the live cache, so strip a copy or the next authed
    # request gets the gutted payload too
    d = copy.deepcopy(status())
    d["view"] = True
    d["logs"] = []
    for b in d["bots"]:
        b.pop("pane", None)
        b.pop("line", None)
        b.pop("model", None)
        b.pop("tokens", None)
    return d


# ---------------------------------------------------------------- room editor
# editor.html sits behind the token like the rest of the controls. It edits two
# things: the asset library (art/assets.json + the rendered pngs) and the room
# layout (layout.json), then asks for a bake, which is just build_room.build().
LAYOUT_FILE = os.path.join(HERE, "layout.json")
SEATS_FILE = os.path.join(HERE, "seats.json")
WALK_FILE = os.path.join(HERE, "walk.json")
# The top-down world's plan. Kept as a one-line JS assignment rather than JSON so
# world.html can read it with a plain <script> tag and stay synchronous — every
# size in that page is computed from the plan at module load.
WORLD_FILE = os.path.join(STATIC, "world.js")


def rebake():
    """Rebuild scene.json from whatever is now on disk."""
    import importlib
    import bake_scene
    importlib.reload(bake_scene)
    bake_scene.build()


def _room():
    """Imported late: the editor is the only thing that needs numpy/PIL, and the
    dashboard has to keep serving even if they are missing."""
    import assets
    import build_room
    return assets, build_room


def ed_layout(req):
    items = req if isinstance(req, list) else req.get("layout", [])
    # `seat` is from the era when people were painted into the room's picture.
    # A page opened before that changed still holds one and saves it straight
    # back, pointing at a character folder that no longer exists.
    items = [{k: v for k, v in it.items() if k != "seat"} for it in items]
    json.dump(items, open(LAYOUT_FILE, "w"), indent=1)
    return {"ok": True, "msg": "%d pieces" % len(items)}


def ed_asset(req):
    import base64
    assets, _ = _room()
    name = re.sub(r"[^A-Za-z0-9_-]", "_", req.get("name", "") or "piece")
    tmp = os.path.join(HERE, "art", "raw", "_upload.png")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    open(tmp, "wb").write(base64.b64decode(req["png"]))
    spec = assets.add(name, tmp)
    os.remove(tmp)
    log("system", "asset %s added" % name, "info")
    return {"ok": True, "name": name, "edges": spec["edges"], "width": spec["width"]}


def ed_size(req):
    assets, _ = _room()
    ix = assets.load_index()
    name = req["name"]
    ix[name]["width"] = max(8, min(1200, int(req["width"])))
    assets.save_index(ix)
    assets.render(name, ix[name])
    return {"ok": True}


def ed_fit(req):
    """Toggle a piece between measured and untouched.

    Measuring puts furniture back on the room's grid, which is the fix when its
    angle fights the floor tiles. On a round pot or anything with no clear grain
    the measurement is noise and only warps it, so the same button drops back to
    the plain drawing."""
    assets, _ = _room()
    from PIL import Image
    ix = assets.load_index()
    name = req["name"]
    if ix[name].get("edges"):
        e = None
    else:
        e = assets.measure(Image.open(os.path.join(assets.RAW, name + ".png")).convert("RGBA"))
    ix[name]["edges"] = e
    assets.save_index(ix)
    assets.render(name, ix[name])
    return {"ok": True, "edges": e}


def ed_bake(req):
    """Bake what is on screen, not what was last saved — pressing BAKE without
    pressing SAVE first used to quietly rebuild the old room.

    Two things are baked, because the room is drawn twice: build_room paints the
    still picture the editor previews, and bake_scene writes the scene.json the
    live room walks people around in. Baking only the first left furniture moved
    on the editor's canvas and standing where it was for everybody else."""
    _, build_room = _room()
    if isinstance(req, dict) and isinstance(req.get("layout"), list):
        ed_layout(req["layout"])
    build_room.build()
    rebake()
    out = os.path.join(STATIC, "office", "room_base.png")
    return {"ok": True, "at": time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(out)))}


def ed_seats(req):
    """Save how big people are and where they sit, then rebuild the scene.

    These numbers are eyeballed against the art, so they are set on
    static/seats.html by dragging rather than guessed here. The same page also
    drags the chairs themselves, and a chair is a piece of furniture like any
    other, so those go back into the layout."""
    cfg = req.get("seats")
    if not isinstance(cfg, dict):
        return {"ok": False, "msg": "no seats in body"}
    with open(SEATS_FILE, "w") as f:
        json.dump(cfg, f, indent=1)
    if isinstance(req.get("layout"), list):
        ed_layout(req["layout"])
    rebake()
    return {"ok": True}


def ed_walk(req):
    """Save the cells painted open or shut on the floor, then rebuild.

    The grid is worked out from the sprites, and some of it the sprites cannot
    say: a rug is walkable and a low table is not, and both are a flat shape
    lying on the floor."""
    marks = req.get("walk")
    if not isinstance(marks, dict):
        return {"ok": False, "msg": "no walk in body"}
    keep = {k: [[int(a), int(b)] for a, b in marks.get(k, [])] for k in ("block", "open")}
    with open(WALK_FILE, "w") as f:
        json.dump(keep, f)
    rebake()
    return {"ok": True, "msg": "%d shut · %d open" % (len(keep["block"]), len(keep["open"]))}


def room_mask(files, cell=16):
    """Work out where a room's floor is, straight from its artwork.

    A room added in the editor has no walk mask, and a room with no mask is one
    nobody can enter: the page reads a missing mask as solid. So the mask is
    derived the same way build_world.py derives the others -- the tile that
    repeats across the room is the floor, anything drawn on an upper layer is
    furniture -- and only for rooms that do not have one yet.
    """
    from PIL import Image
    d = os.path.join(STATIC, "limezu", "rooms")
    ims = [Image.open(os.path.join(d, f)).convert("RGBA") for f in files]
    base, above = ims[0], [im.load() for im in ims[1:]]
    W, H = base.size
    bpx = base.load()

    counts, keys = {}, {}
    for ty in range(H // 32):
        for tx in range(W // 32):
            k = base.crop((tx * 32, ty * 32, tx * 32 + 32, ty * 32 + 32)).tobytes()
            keys[(tx, ty)] = k
            counts[k] = counts.get(k, 0) + 1
    floor = {k for k, n in counts.items() if n >= 4}
    # The pack's floors repeat every three tiles, so a tile the vote rejected can
    # still be bare floor: compare it against the floor tile of its own phase.
    phase = {}
    for (tx, ty), k in keys.items():
        if k in floor:
            phase.setdefault((tx % 3, ty % 3), {})
            phase[(tx % 3, ty % 3)][k] = phase[(tx % 3, ty % 3)].get(k, 0) + 1
    phase_tile = {ph: Image.frombytes("RGBA", (32, 32),
                                      max(d2.items(), key=lambda kv: kv[1])[0]).load()
                  for ph, d2 in phase.items()}

    rows = []
    for gy in range(H // cell):
        row = []
        for gx in range(W // cell):
            x0, y0 = gx * cell, gy * cell
            ok = keys.get((x0 // 32, y0 // 32)) in floor
            if not ok:
                ref = phase_tile.get(((x0 // 32) % 3, (y0 // 32) % 3))
                if ref is not None:
                    ok = all(bpx[x, y] == ref[x % 32, y % 32]
                             for y in range(y0, y0 + cell)
                             for x in range(x0, x0 + cell))
            if ok:
                for px in above:
                    if any(px[x, y][3] > 0
                           for y in range(y0, y0 + cell, 2)
                           for x in range(x0, x0 + cell, 2)):
                        ok = False
                        break
            row.append("1" if ok else "0")
        rows.append("".join(row))
    return {"w": W, "h": H, "cell": cell, "mask": rows}


def fill_masks(world):
    """Give every room a walk mask, adding only the ones that are missing."""
    path = os.path.join(STATIC, "limezu", "world_data.json")
    try:
        with open(path) as f:
            wd = json.load(f)
    except Exception:
        wd = {}
    added = []
    for r in world.get("rooms", []):
        rid, files = r.get("id"), r.get("L") or []
        if rid in wd or not files:
            continue
        try:
            wd[rid] = room_mask(files)
            added.append(rid)
        except Exception as e:
            log("system", "mask for %s failed: %s" % (rid, e), "warn")
    if added:
        with open(path, "w") as f:
            json.dump(wd, f, separators=(",", ":"))
    return added


def ed_world(req):
    """Save the plan of the top-down world: rooms, their spots and props, the
    row layout, the cast, the chief's desk."""
    w = req.get("world")
    if not isinstance(w, dict) or not isinstance(w.get("rooms"), list):
        return {"ok": False, "msg": "no world in body"}
    ids = [r.get("id") for r in w["rooms"]]
    if len(set(ids)) != len(ids) or not all(ids):
        return {"ok": False, "msg": "room ids must exist and be unique"}
    # Every id named by the layout has to be a room, or the page divides by a
    # room that is not there and the whole world fails to draw.
    known = set(ids)
    for row in w.get("layout", []):
        for rid in row:
            if rid not in known:
                return {"ok": False, "msg": "layout names a missing room: %s" % rid}
    if w.get("tall") and w["tall"] not in known:
        return {"ok": False, "msg": "tall names a missing room: %s" % w["tall"]}
    body = ("// The plan of the world. Edited by world-editor.html, read by world.html.\n"
            "// One file, so the page and the editor can never disagree about what exists.\n"
            "window.WORLD = %s;\n" % json.dumps(w, ensure_ascii=False, indent=1))
    with open(WORLD_FILE, "w") as f:
        f.write(body)
    added = fill_masks(w)
    return {"ok": True, "msg": "%d rooms · %d spots%s"
            % (len(w["rooms"]), sum(len(r.get("spots") or []) for r in w["rooms"]),
               (" · walk mask for " + ", ".join(added)) if added else "")}


def limezu_pack():
    """What art the pack actually has on disk, so the editor offers real files
    instead of a list someone has to keep in step by hand."""
    def ls(sub, ext=".png"):
        d = os.path.join(STATIC, "limezu", sub)
        try:
            return sorted(f for f in os.listdir(d) if f.lower().endswith(ext))
        except OSError:
            return []
    rooms = ls("rooms")
    # A room design is a set of layer files sharing a name: "Gym_layer_1_32x32.png",
    # "Gym_layer_2_32x32.png". Group them so the editor offers designs, not files.
    designs = {}
    for f in rooms:
        base = re.sub(r"[_-]?layer[_-]?\d+", "", f, flags=re.I)
        base = re.sub(r"_?32x32", "", base, flags=re.I).replace(".png", "").strip("_")
        designs.setdefault(base, []).append(f)
    return {"designs": [{"name": k, "layers": v} for k, v in sorted(designs.items())],
            "chars": ls("chars"), "anim": ls("anim"), "props": ls("props")}


EDIT_POST = {"layout": ed_layout, "asset": ed_asset, "asset-size": ed_size,
             "asset-fit": ed_fit, "bake": ed_bake, "seats": ed_seats, "walk": ed_walk,
             "world": ed_world}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, body, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if getattr(self, "_setcookie", False):
            self.send_header("Set-Cookie",
                             "bw=%s; Path=/; Max-Age=2592000; SameSite=Lax" % TOKEN)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(json.dumps(obj, ensure_ascii=False).encode(),
                   "application/json; charset=utf-8", code)

    def do_POST(self):
        path = self.path.split("?")[0]
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            req = {}
        key = req.get("key") if isinstance(req, dict) else None
        if key != TOKEN and self._authed() is None:
            self._json({"ok": False, "msg": "bad token"}, 403)
            return

        if path.startswith("/api/") and path[5:] in EDIT_POST:
            try:
                self._json(EDIT_POST[path[5:]](req))
            except Exception as e:
                self._json({"ok": False, "msg": "%s: %s" % (type(e).__name__, e)}, 500)
        elif path == "/api/action":
            ok, msg = act(req.get("id", ""), req.get("action", ""))
            _cache["t"] = 0.0
            self._json({"ok": ok, "msg": msg})
        elif path == "/api/restart-all":
            done = [b[1] for b in BOTS if act(b[0], "restart")[0]]
            _cache["t"] = 0.0
            self._json({"ok": True, "msg": "restarted %d bots" % len(done)})
        elif path == "/api/clear-logs":
            LOGS.clear()
            log("system", "logs cleared", "info")
            _cache["t"] = 0.0
            self._json({"ok": True, "msg": "logs cleared"})
        else:
            self._json({"ok": False, "msg": "not found"}, 404)

    # ---- token gate: the whole site, not only the controls ----------------
    def _authed(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if q.get("k", [""])[0] == TOKEN:
            return "set"
        cookie = self.headers.get("Cookie", "")
        return "ok" if ("bw=" + TOKEN) in cookie else None

    def do_GET(self):
        path = self.path.split("?")[0]
        auth = self._authed()
        # Visitors without the token get the world in read-only form: the page and
        # its art load, but the session text, the logs and every control stay behind
        # the token. Everything else still 401s.
        rel0 = "index.html" if path in ("/", "") else path.lstrip("/")
        public = rel0 in PUBLIC_PAGES or rel0.split("/")[0] in PUBLIC_DIRS \
            or path in ("/api/status", "/status.json")
        if not auth and not public:
            body = LOGIN.encode()
            self.send_response(401)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        # Remember the token so the query string does not have to be pasted again.
        # This used to answer with a 302 to `path`, but behind Caddy's
        # `uri strip_prefix /botworld` that path is "/" and the browser walked
        # off to the site root instead. Set the cookie on the real response.
        self._setcookie = (auth == "set")
        if path in ("/api/status", "/status.json"):
            self._json(status() if auth else public_status())
            return
        if path == "/api/limezu":
            self._json(limezu_pack())
            return
        if path == "/api/assets":
            assets, _ = _room()
            self._json(assets.manifest())
            return
        if path == "/api/seats":
            import bake_scene
            self._json(bake_scene.tune())
            return
        if path == "/api/walk":
            import bake_scene
            m = bake_scene.walk_marks()
            self._json({"block": m.get("block", []), "open": m.get("open", [])})
            return
        if path == "/api/layout":
            self._json(json.load(open(LAYOUT_FILE)) if os.path.exists(LAYOUT_FILE) else [])
            return
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        full = os.path.normpath(os.path.join(STATIC, rel))
        if not full.startswith(STATIC) or not os.path.isfile(full):
            self._send(b"not found", "text/plain", 404)
            return
        ctype = {".html": "text/html; charset=utf-8",
                 ".js": "application/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8",
                 ".png": "image/png",
                 ".woff2": "font/woff2",
                 ".woff": "font/woff",
                 ".ttf": "font/ttf"}.get(os.path.splitext(full)[1], "application/octet-stream")
        with open(full, "rb") as f:
            self._send(f.read(), ctype)


if __name__ == "__main__":
    cpu_percent()                       # prime the /proc/stat delta
    log("system", "dashboard started", "ok")
    threading.Thread(target=api_probe, daemon=True).start()
    threading.Thread(target=token_loop, daemon=True).start()
    ThreadingHTTPServer.allow_reuse_address = True
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
