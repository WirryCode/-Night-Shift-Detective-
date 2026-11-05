#!/usr/bin/env python3
# Night Shift Detective (Gothic Edition 2.0) - Copyright © 2026 Wilfred Wanyoike. All rights reserved. See COPYRIGHT.txt.
"""Night Shift Detective - a gothic mystery that runs in your browser.
Run:  python app.py      (Python 3.8+, standard library only, no installs)"""
import json, os, random, re, secrets, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SAVEDIR = os.path.join(HERE, "saves")          # saves/<name>/auto.json, 1.json, 2.json, 3.json
USERS_FILE = os.path.join(HERE, "users.json")  # detective profiles + stats (no passwords)
SLOTS = ("auto", "1", "2", "3")
ROMAN = {"1": "I", "2": "II", "3": "III"}
NEED = 60  # Evidence needed to close the case
BASE = {"interview": 3, "search": 2, "follow": 4}
DIFF = {"rookie": dict(time=.75, lie=0, rh=2, hp=.08),
        "detective": dict(time=1, lie=.15, rh=4, hp=.16),
        "inspector": dict(time=1.4, lie=.35, rh=7, hp=.28)}
FIRST = ["Maya", "Jonas", "Priya", "Theo", "Lena", "Omar", "Iris", "Caleb", "Nadia", "Felix"]
LAST = ["Okafor", "Lindqvist", "Rao", "Brennan", "Haddad", "Voss", "Tanaka", "Moreau", "Kamau", "Reyes"]
MAJORS = ["Chemistry", "Philosophy", "Theology", "Fine Art", "Law", "Astronomy", "Anatomy", "Classics"]
ITEMS = ["a green velvet ribbon", "a cracked pocket watch", "a mustard wool scarf", "a tarnished silver signet ring", "an ink-stained leather glove"]
HABITS = ["limps slightly", "is left-handed", "hums hymns while walking", "smells of clove and candle smoke", "never removes their gloves"]
SECRETS = ["is secretly failing two courses", "writes the anonymous gossip sheet slipped under doors", "sells copied lecture notes",
           "is courting a teaching assistant", "has been sleeping among the stacks", "works nights to pay tuition",
           "wrote their roommate’s essay", "hosts séances in the cellar"]
MOTIVES = ["owed a moneylender their tuition", "faced expulsion if the truth surfaced", "was shielding a sibling’s mistake"]
LOCS = [("Reading Vault", "Candles gutter between towers of unread books. Somewhere, a page turns by itself."),
        ("Alchemy Lab", "Green glass glimmers on the shelves. Something in a flask is watching you."),
        ("Common Hall", "Long tables, dying embers, and portraits whose eyes follow your steps."),
        ("Bell Tower", "Wind howls through the louvres. The great bell sways, though no one rings it."),
        ("Print Cellar", "Damp ink and iron presses. Each page left to dry seems freshly written."),
        ("Cloister Walk", "Fog creeps between the arches and swallows the lamps one by one."),
        ("Chapel Crypt", "Cold stone, old names, and a single candle that should have burned out."),
        ("Refectory", "A lone kettle sighs on the hob. A chair is pulled out, as if for you."),
        ("Boiler Rooms", "Pipes groan like chained things. Warm, wet air carries a whisper."),
        ("Observatory", "The dome stands open to a bruised sky. The telescope points at nothing."),
        ("Gargoyle Gate", "Stone beasts watch the road. One of them has, you swear, moved."),
        ("Map Archive", "Charts of drowned villages. Someone has circled the college in red.")]
WIT = ["the night porter", "the bell-ringer", "a hollow-eyed graduate", "the college watchman", "the groundskeeper"]
CRIMES = [("the sealed examination papers vanished from the Registrar’s iron strongbox", "the Registrar’s Office"),
          ("the Founder’s Fund, four thousand pounds in a locked casket, went missing", "the Bursar’s Study"),
          ("the Blackwood Codex, a priceless manuscript, disappeared from its glass case", "the Rare Books Gallery"),
          ("the college ledger was torn out the night before the Governors’ audit", "the Governors’ Chamber")]
TPL = {"search": {"item": "Caught on an iron railing near {CP}: {v}, still warm.",
                  "habit": "Near {CP}, the dust is disturbed in a way that suggests the intruder {v}.",
                  "haunt": "A stamped pass from the {v}, dropped near {CP}."},
       "interview": {"item": "The night porter swears the figure fleeing {CP} near {T} had {v}.",
                     "habit": "The bell-ringer noticed that the intruder {v}.",
                     "haunt": "A shaken scholar says the thief fled toward the {v} after {T}."},
       "follow": {"item": "You follow a figure through the fog. They carry {v} and make for {CP}.",
                  "habit": "You follow a cloaked figure near {T}. Unmistakably, this person {v}.",
                  "haunt": "You follow a hooded figure straight to the {v}, where the fog swallows them."}}
HID = {"item": "❦ The Match. Porter and railing agree: whoever owns {v} was at the scene. The pattern closes like a lock.",
       "habit": "❦ Two Witnesses, One Shadow. Your pursuit and the bell-ringer describe the same soul, the one who {v}.",
       "haunt": "❦ The Hidden Door. Pass and sighting converge on the {v}. That is where your thief hides."}
ENDS = {"Case Closed": "The name is spoken, the proof laid bare. The Governors nod in the grey dawn, and the bells of Hallowmere ring for the first time in weeks.",
        "Partial Solution": "You name the right soul, but the proof is thin. They slip away through a gap in the law, and you alone know the truth.",
        "Cold Case": "The last hour tolls. The file is sealed in the archive beneath a wax stamp, and the guilty walk free beneath the fog.",
        "False Accusation": "You accused the wrong soul. By dawn the whole college knows, and the real culprit smiles from the shadows."}
KEY = {"Case Closed": "closed", "Partial Solution": "partial", "Cold Case": "cold", "False Accusation": "false"}
GAMES, SESS, LOCK = {}, {}, threading.RLock()  # games by user, browser sessions, file lock
cap = lambda s: s[:1].upper() + s[1:]


def mk(G, t, a, i):
    s = G["sus"][i]
    return dict(t=t, a=a, w=i, ok=(i == G["cul"]), text=TPL[t][a].format(v=s[a], CP=G["cp"], T=G["T"]))


def new_game(det, diff, user):
    r = random
    if det not in ("eye", "talker", "lab") or diff not in DIFF:
        raise KeyError(det)
    names = r.sample([f + " " + l for f in FIRST for l in LAST], 5)
    items, habits, hn = r.sample(ITEMS, 5), r.sample(HABITS, 5), r.sample(LOCS, 5)
    cul, (crime, cp) = r.randrange(5), r.choice(CRIMES)
    secs = r.sample(SECRETS, 4)
    sus = [dict(name=names[i], major=r.choice(MAJORS), item=items[i], haunt=hn[i][0], habit=habits[i],
                secret=r.choice(MOTIVES) if i == cul else secs.pop(), trust=0, open=False, cleared=False)
           for i in range(5)]
    G = dict(user=user, counted=False, det=det, diff=diff, night=1, acts=3, m=dict(trust=100, evidence=0, time=100), sus=sus, cul=cul,
             crime=crime, cp=cp, T=r.choice(["10:15 PM", "11:40 PM", "12:20 AM", "1:05 AM"]), clues=[], hidden=[], over=None, final=False, cid=0,
             msg=[f"Hallowmere College, past midnight. {cap(crime)}. Five students are whispered about, and twelve nights remain before the Governors convene."])
    spec = [("search", "item"), ("interview", "item"), ("interview", "habit"), ("follow", "habit"),
            ("interview", "haunt"), ("follow", "haunt"), ("search", "habit"), ("search", "haunt"), ("follow", "item")]
    G["q"] = [mk(G, t, a, cul) for t, a in spec]
    inn = [i for i in range(5) if i != cul]
    G["rq"] = [mk(G, r.choice(list(BASE)), r.choice(["item", "habit", "haunt"]), r.choice(inn)) for _ in range(DIFF[diff]["rh"])]
    make_scenes(G)
    save_slot(G, "auto")
    return G


def make_scenes(G):
    out = []
    for n, d in random.sample(LOCS, random.randint(4, 6)):
        hs = [i for i, s in enumerate(G["sus"]) if s["haunt"] == n]
        who = hs[0] if hs and random.random() < .7 else (random.randrange(5) if random.random() < .25 else -1)
        out.append(dict(loc=n, txt=d, who=who, wit=random.choice(WIT)))
    G["scenes"] = out


# ---------- case files (saves) ----------
def slot_path(user, slot):
    return os.path.join(SAVEDIR, user, slot + ".json")


def save_slot(G, slot):
    os.makedirs(os.path.join(SAVEDIR, G["user"]), exist_ok=True)
    G["saved"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOCK, open(slot_path(G["user"], slot), "w", encoding="utf-8") as f:
        json.dump(G, f)


def slots(user):
    out = []
    for s in SLOTS:
        try:
            with open(slot_path(user, s), encoding="utf-8") as f:
                g = json.load(f)
            out.append(dict(slot=s, night=g["night"], det=g["det"], diff=g["diff"], evidence=g["m"]["evidence"], saved=g.get("saved", "")))
        except (OSError, ValueError, KeyError):
            out.append(dict(slot=s, empty=True))
    return out


# ---------- detective profiles (name only, no password) ----------
def load_users():
    try:
        with open(USERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_users(U):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(U, f, indent=1)


def enter(name):
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", name):
        return None, "A name has 3 to 20 letters, numbers or underscores."
    k = name.lower()
    with LOCK:
        U = load_users()
        u = U.setdefault(k, dict(name=name, joined=time.strftime("%Y-%m-%d")))
        u.pop("salt", None), u.pop("hash", None)   # passwords are gone, wipe any old ones
        u.setdefault("stats", dict(played=0, closed=0, partial=0, cold=0, false=0, quiet=0))
        u.setdefault("tut", False)
        save_users(U)
    old = os.path.join(SAVEDIR, k + ".json")      # move a save from the older single-file layout
    if os.path.exists(old) and not os.path.exists(slot_path(k, "auto")):
        os.makedirs(os.path.join(SAVEDIR, k), exist_ok=True)
        os.replace(old, slot_path(k, "auto"))
    return k, None


def record(G):
    """Add a finished case to the detective's record (once)."""
    if not G or not G["over"] or G.get("counted"):
        return
    G["counted"] = True
    with LOCK:
        U = load_users()
        u = U.get(G["user"])
        if u:
            u["stats"]["played"] += 1
            u["stats"][KEY.get(G["over"]["t"], "quiet")] += 1
            save_users(U)


def profile(user):
    u = load_users().get(user) if user else None
    return dict(name=u["name"], joined=u["joined"], tut=u.get("tut", False), **u["stats"]) if u else None


def mark_tutorial(user):
    with LOCK:
        U = load_users()
        if user in U:
            U[user]["tut"] = True
            save_users(U)


# ---------- the game ----------
def cost(G, a):
    c = max(1, round(BASE[a] * DIFF[G["diff"]]["time"]))
    return max(1, c - 1) if G["det"] == "lab" and a == "search" else c


def finish(G, title, text):
    s = G["sus"][G["cul"]]
    G["over"] = dict(t=title, x=text + f" The culprit was {s['name']}, who {s['secret']}.")


def check(G):
    m = G["m"]
    for k in m:
        m[k] = max(0, min(100, m[k]))
    if not G["over"] and (m["time"] <= 0 or m["trust"] <= 0):
        finish(G, "Cold Case", ENDS["Cold Case"] + (" The Governors withdraw their faith in a detective nobody believes." if m["trust"] <= 0 else ""))


def give(G, c, q, L):
    G[q].remove(c)
    G["cid"] += 1
    c["id"] = G["cid"]
    G["clues"].append(c)
    ev = (8 + (3 if G["det"] == "lab" else 0)) if c["ok"] else 5
    G["m"]["evidence"] += ev
    L.append(f"✦ New clue: {c['text']} (Evidence +{ev})")


def act(G, si, a):
    if G["over"] or G["final"] or G["acts"] < 1 or a not in BASE:
        return
    sc, D, m, det, r, L = G["scenes"][si], DIFF[G["diff"]], G["m"], G["det"], random, []
    m["time"] -= cost(G, a)
    G["acts"] -= 1
    s = G["sus"][sc["who"]] if sc["who"] >= 0 else None
    who = s["name"] if s else sc["wit"]
    if a == "interview":
        m["trust"] += 2 + (2 if det == "talker" else 0)
        if s:
            s["trust"] += 27 if det == "talker" else 18
        L.append(f"You sit with {who} by guttering candlelight. The questions come softly.")
    elif a == "search":
        m["trust"] -= 5 if r.random() < .25 else 1
        L.append("Dust lifts in your lantern’s glow as you sift every shadow." if m["trust"] > 5 else "Someone has noticed you prowling.")
    else:
        m["trust"] -= 6 if r.random() < .25 else 3
        if s:
            s["trust"] -= 12
        L.append(f"You follow {who} through the fog, half a step behind.")
    p = {"interview": .5, "search": .55, "follow": .45}[a] + (.2 if det == "eye" and a != "interview" else 0)
    pool = lambda q: [c for c in G[q] if c["t"] == a]
    if a == "interview" and r.random() < D["lie"] * (.5 if det == "talker" else 1):
        L.append(f"{who} offers a smooth, too-tidy story.")
        if pool("rq"):
            give(G, pool("rq")[0], "rq", L)
    elif r.random() < p and pool("q"):
        give(G, r.choice(pool("q")), "q", L)
    elif r.random() < D["hp"] and pool("rq"):
        give(G, r.choice(pool("rq")), "rq", L)
    else:
        L.append("Nothing new. The night keeps its secrets.")
    if s and not s["open"] and s["trust"] >= 60:
        s["open"] = True
        fn = s["name"].split()[0]
        if sc["who"] == G["cul"]:
            m["evidence"] += 15
            L.append(f"✦ {fn} breaks their silence: {fn} {s['secret']}. That is motive. (Evidence +15)")
        else:
            s["cleared"] = True
            L.append(f"✦ {fn} confides: {fn} {s['secret']}. That explains the strange behavior. {fn} is no thief.")
    G["msg"] = L
    check(G)


def connect(G, x, y):
    c = {c["id"]: c for c in G["clues"]}
    a, b = c.get(x), c.get(y)
    if not a or not b or x == y:
        return
    key = f"{a['a']}{a['w']}"
    if a["a"] != b["a"] or a["w"] != b["w"] or a["t"] == b["t"]:
        G["msg"] = ["Those two do not belong together. Try another pair."]
    elif any(h["k"] == key for h in G["hidden"]):
        G["msg"] = ["You have already pulled that thread."]
    else:
        s = G["sus"][a["w"]]
        if a["ok"]:
            G["m"]["evidence"] += 12
            t = HID[a["a"]].format(v=s[a["a"]]) + " (Evidence +12)"
        else:
            G["m"]["time"] -= 3
            t = f"❦ A Dead End. The threads align, but {s['name']} has an alibi sworn on the chapel register. (Time -3)"
        G["hidden"].append(dict(k=key, text=t))
        G["msg"] = ["✧ A hidden scene unfolds…", t]
    check(G)


def end_night(G):
    if G["over"] or G["final"]:
        return
    G["night"] += 1
    G["acts"] = 3
    if G["night"] > 12:
        G["final"], G["scenes"] = True, []
        G["msg"] = ["The twelfth bell tolls. It is time to name the guilty."]
    else:
        make_scenes(G)
        G["msg"] = [f"The tower bell tolls. Night {G['night']} begins, and your progress is recorded."]
    save_slot(G, "auto")


def accuse(G, i):
    if G["over"]:
        return
    if i == G["cul"]:
        ok = G["m"]["evidence"] >= NEED
        finish(G, "Case Closed" if ok else "Partial Solution", ENDS["Case Closed" if ok else "Partial Solution"])
    elif G["diff"] == "inspector":
        finish(G, "False Accusation", ENDS["False Accusation"])
    else:
        s = G["sus"][i]
        s["cleared"] = True
        G["m"]["time"] -= 12
        G["m"]["trust"] -= 15
        G["msg"] = [f"{s['name']} produces an alibi no one can break. The wrong soul. (Time -12, Trust -15)"]
        check(G)


def spare(G, i):
    s = G["sus"][i]
    if G["over"] or not s["open"]:
        return
    fn = s["name"].split()[0]
    if i == G["cul"]:
        finish(G, "Second Chance", f"{fn} breaks, confesses, and returns what was taken, begging only that the reason be kept in the dark. The file closes without a whisper.")
    else:
        finish(G, "Keeper of Secrets", f"You swear {fn}’s secret will rest with you. The case closes quietly, and a debt of trust is yours to keep.")


def view(G):
    v = {k: G[k] for k in ("det", "diff", "night", "acts", "m", "over", "msg", "final", "T", "cp", "crime", "scenes")}
    v["need"], v["cost"] = NEED, {a: cost(G, a) for a in BASE}
    v["clues"] = [dict(id=c["id"], t=c["t"], a=c["a"], text=c["text"]) for c in G["clues"]]
    v["hidden"] = [h["text"] for h in G["hidden"]]
    v["sus"] = [dict(name=s["name"], major=s["major"], item=s["item"], haunt=s["haunt"], habit=s["habit"],
                     trust=max(0, min(100, s["trust"])), open=s["open"], cleared=s["cleared"],
                     secret=s["secret"] if s["open"] else None,
                     links=sum(1 for c in G["clues"] if c["w"] == i)) for i, s in enumerate(G["sus"])]
    return v


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, body, ct="application/json", cookie=None):
        b = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(b)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(b)

    def sid(self):
        m = re.search(r"(?:^|;\s*)sid=([0-9a-f]+)", self.headers.get("Cookie") or "")
        return m.group(1) if m else None

    def state(self, user, err=None, cookie=None, note=None):
        p = profile(user)
        G = GAMES.get(user) if p else None
        self.reply(json.dumps({"user": p["name"] if p else None, "profile": p, "error": err, "note": note,
                               "slots": slots(user) if p else [], "game": view(G) if G else None}), cookie=cookie)

    def do_GET(self):
        if self.path == "/api/state":
            return self.state(SESS.get(self.sid()))
        with open(os.path.join(HERE, "index.html"), "rb") as f:
            self.reply(f.read(), "text/html; charset=utf-8")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            b = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            b = {}
        p, user, err, cookie, note = self.path, SESS.get(self.sid()), None, None, None
        if p == "/api/enter":
            user, err = enter(str(b.get("name", "")).strip())
            if user:
                tok = secrets.token_hex(24)
                SESS[tok] = user
                cookie = f"sid={tok}; Path=/; HttpOnly; SameSite=Lax; Max-Age=2592000"
        elif p == "/api/logout":
            SESS.pop(self.sid(), None)
            user, cookie = None, "sid=; Path=/; Max-Age=0"
        elif user and profile(user):
            G, sl = GAMES.get(user), str(b.get("slot", ""))
            try:
                if p == "/api/new":
                    GAMES[user] = new_game(b["det"], b["diff"], user)
                elif p == "/api/load":
                    if sl == "latest":
                        have = [x for x in slots(user) if not x.get("empty")]
                        sl = max(have, key=lambda x: x["saved"])["slot"] if have else ""
                    if sl in SLOTS and os.path.exists(slot_path(user, sl)):
                        with open(slot_path(user, sl), encoding="utf-8") as f:
                            GAMES[user] = json.load(f)
                        GAMES[user]["user"] = user
                        note = "The case file is open once more."
                elif p == "/api/save" and G and not G["over"] and sl in ROMAN:
                    save_slot(G, sl)
                    note = f"The case is recorded in Case File {ROMAN[sl]}."
                elif p == "/api/delete" and sl in ROMAN and os.path.exists(slot_path(user, sl)):
                    os.remove(slot_path(user, sl))
                    note = "The case file is burned."
                elif p == "/api/exit":
                    GAMES.pop(user, None)
                elif p == "/api/tutorial":
                    mark_tutorial(user)
                elif G:
                    {"/api/act": lambda: act(G, b.get("i", 0), b.get("a")),
                     "/api/connect": lambda: connect(G, b.get("a"), b.get("b")),
                     "/api/night": lambda: end_night(G),
                     "/api/accuse": lambda: accuse(G, b.get("i", 0)),
                     "/api/spare": lambda: spare(G, b.get("i", 0)),
                     "/api/cold": lambda: finish(G, "Cold Case", ENDS["Cold Case"]) if not G["over"] else None,
                     }.get(p, lambda: None)()
            except (KeyError, IndexError, TypeError):
                pass
            record(GAMES.get(user))
        self.state(user, err, cookie, note)


if __name__ == "__main__":
    if "PORT" in os.environ:
        port = int(os.environ["PORT"])
        srv = ThreadingHTTPServer(("0.0.0.0", port), H)
        print(f"Night Shift Detective is live on port {port}")
    else:
        for port in range(8000, 8010):
            try:
                srv = ThreadingHTTPServer(("127.0.0.1", port), H)
                break
            except OSError:
                continue
        else:
            raise SystemExit("Ports 8000-8009 are all busy. Close other local servers and try again.")
        url = f"http://127.0.0.1:{port}"
        print(f"Night Shift Detective is open at {url}  (Ctrl+C to stop)")
        threading.Timer(.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nThe watch is over.")
