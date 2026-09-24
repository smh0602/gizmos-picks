#!/usr/bin/env python3
"""fb_ledger.py — "What the model showed, graded": the football models'
published picks, frozen before kickoff and graded after, exactly as
`research/fb_model_live_spec.md` fixes it (Sam, 2026-09-24; committed
before this file existed).

    LEAGUE=nfl python fb_ledger.py     # snapshot now, grade, write the ledger

⛔ FROZEN. Snapshots and grades are written through `daystore`, which never
overwrites; a pick graded once is never re-graded (spec §3), so the past
is never recalculated.
⛔ It changes no model, never edits the card or a published card pick, and
never reads MLB.
⚠️ STDLIB ONLY.
"""
import datetime
import glob
import gzip
import json
import os
import sys

import daystore                     # archive: the ONE dated, write-once writer
import fb_model as F                # grade, L — the walk-forward's own grader
import fb_props_model as M          # load_logs, name_index, resolve, game_row, league
import record_fb                    # _played, _val, _won — the card's own grader

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
LEDGER_FROM = "2026-09-24"          # ⛔ spec §2 (Sam): "It starts today"
MODELS = ("game_model", "props_model")


def log(m):
    print(m, flush=True)


def L(value, basis):
    return F.L(value, basis)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _val(x):
    return x.get("value") if isinstance(x, dict) else x


def _json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gz(path):
    try:
        return json.load(gzip.open(path, "rt", encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _data(lg, root=None):
    return os.path.join(root or ROOT, "data", lg)


# ══════════════════════════════════════════════════════════════════════
# 1. THE SNAPSHOT — what each model is showing, for games not yet kicked off
# ══════════════════════════════════════════════════════════════════════
def snapshot(lg, root=None, when=None, log=log):
    """Write the picks both models are showing now, for games that have
    not kicked off, via daystore (write-once). -> (path, wrote?) or None."""
    when = when or _now()
    now = _iso(when)
    latest = os.path.join(_data(lg, root), "latest")
    gm = _json(os.path.join(latest, "fb-model.json"))
    pm = _json(os.path.join(latest, "fb-props-model.json"))
    game = [p for p in gm.get("picks") or [] if (p.get("commence") or "") > now]
    props = [p for p in pm.get("picks") or [] if (p.get("commence") or "") > now]
    if not game and not props:
        return None
    doc = {"league": lg, "taken_at": now, "game_model": game, "props_model": props,
           "spec": "research/fb_model_live_spec.md"}
    return daystore.archive(doc, _data(lg, root), "model-picks", log=log, when=when)


def snapshots(lg, root=None):
    """Every snapshot dated on or after LEDGER_FROM, oldest first."""
    out = []
    for p in glob.glob(os.path.join(_data(lg, root), "*", "model-picks", "*.json.gz")):
        day = os.path.basename(os.path.dirname(os.path.dirname(p)))
        if day < LEDGER_FROM:
            continue
        d = _gz(p)
        if d and d.get("taken_at"):
            out.append(d)
    return sorted(out, key=lambda d: d["taken_at"])


def pick_key(model, p):
    if model == "game_model":
        return "%s|%s|%s" % (model, p.get("game_id"), p.get("market"))
    return "%s|%s|%s|%s" % (model, p.get("game_id"), p.get("player"), p.get("market"))


def ledger_picks(snaps):
    """spec §3: for each game and model, the picks from the LAST snapshot
    taken before its kickoff in which that game had a pick."""
    chosen = {}
    for s in snaps:
        for model in MODELS:
            by_game = {}
            for p in s.get(model) or []:
                by_game.setdefault(p.get("game_id"), []).append(p)
            for gid, ps in by_game.items():
                if s["taken_at"] < (ps[0].get("commence") or ""):
                    chosen[(model, gid)] = (s["taken_at"], ps)
    out = []
    for (model, _gid), (taken, ps) in chosen.items():
        for p in ps:
            out.append(dict(p, model=model, snapshot=taken, key=pick_key(model, p)))
    return out


# ══════════════════════════════════════════════════════════════════════
# 2. GRADING — once, then frozen
# ══════════════════════════════════════════════════════════════════════
def stored_grades(lg, root=None):
    """{key: grade} from every earlier grades file. ⛔ The FIRST stored
    grade of a pick is the one that stands (spec §3)."""
    out = {}
    files = sorted(glob.glob(os.path.join(_data(lg, root), "*", "ledger-grades", "*.json.gz")))
    for p in files:
        for g in (_gz(p) or {}).get("grades") or []:
            out.setdefault(g["key"], g)
    return out


def schedule_by_id(lg, root=None):
    out = {}
    for s in (2025, 2026):
        d = _gz(os.path.join(_data(lg, root), "latest", "schedule-%d.json.gz" % s)) or {}
        for g in d.get("games") or []:
            out[str(g.get("id"))] = g
    return out


def grade_game_pick(p, sched):
    """(state, won) against the schedule's final score, via fb_model.grade."""
    g = sched.get(str(p.get("game_id")))
    if not g or not g.get("final") or g.get("home_score") is None or g.get("away_score") is None:
        return "pending", None
    r = {"final": True, "hs": g["home_score"], "as": g["away_score"]}
    won = F.grade(r, p.get("market"), {"side": p.get("side"), "line": _val(p.get("line"))})
    return ("void", None) if won is None else ("graded", won)


def grade_prop_pick(lg, p, logs, idx):
    """(state, won) via record_fb's join and grader, as the card is graded."""
    pid = M.resolve(idx, p.get("player"))
    if pid is None:
        return "pending", None
    _s, g = M.game_row(logs, pid, p.get("commence"))
    if g is None:
        return "pending", None
    ok, _why = record_fb._played(g)
    if not ok:
        return "void", None
    side, line = p.get("side"), _val(p.get("line"))
    val = record_fb._val(g, p.get("market"))
    if side in ("over", "under") and val is not None and line is not None and val == line:
        return "void", None
    won = record_fb._won(val, line, side)
    return ("pending", None) if won is None else ("graded", bool(won))


def grade_new(lg, picks, stored, root=None, when=None, log=log):
    """Grade every pick not yet stored; store the definitive ones, once."""
    sched = schedule_by_id(lg, root)
    logs = M.load_logs(lg, root)
    idx = M.name_index(logs)
    new = []
    with M.league(lg):
        for p in picks:
            if p["key"] in stored:
                continue
            if p["model"] == "game_model":
                state, won = grade_game_pick(p, sched)
            else:
                state, won = grade_prop_pick(lg, p, logs, idx)
            if state in ("graded", "void"):
                new.append({"key": p["key"], "state": state, "won": won,
                            "graded_at": _iso(when or _now())})
    if new:
        daystore.archive({"league": lg, "grades": new}, _data(lg, root), "ledger-grades",
                         log=log, when=when)
    return new


# ══════════════════════════════════════════════════════════════════════
# 3. THE RECORD THE PAGE SHOWS
# ══════════════════════════════════════════════════════════════════════
def build(lg=None, root=None, out=None, when=None, log=log):
    lg = (lg or LEAGUE).lower()
    when = when or _now()
    snapshot(lg, root, when, log)
    snaps = snapshots(lg, root)
    picks = ledger_picks(snaps)
    stored = stored_grades(lg, root)
    for g in grade_new(lg, picks, stored, root, when, log):
        stored.setdefault(g["key"], g)
    latest = os.path.join(_data(lg, root), "latest")
    verdicts = {"game_model": {mk: (v.get("verdict") or {}) for mk, v in
                               (_json(os.path.join(latest, "fb-model.json")).get("record") or {}).items()},
                "props_model": {mk: (v.get("verdict") or {}) for mk, v in
                                (_json(os.path.join(latest, "fb-props-model.json")).get("record") or {}).items()}}
    rows = []
    for p in picks:
        g = stored.get(p["key"]) or {}
        state = g.get("state") or "pending"
        rows.append({"model": p["model"], "market": p.get("market"),
                     "market_label": p.get("market_label") or p.get("market"),
                     "game": p.get("game"), "player": p.get("player"), "team": p.get("team"),
                     "side": p.get("side"), "line": p.get("line"), "price": p.get("price"),
                     "book": p.get("book"), "model_probability": p.get("model_probability"),
                     "break_even": p.get("break_even"), "commence": p.get("commence"),
                     "shown_at": p["snapshot"], "state": state, "won": g.get("won")})
    rows.sort(key=lambda r: (r["commence"] or "", r["model"], r["market"] or ""), reverse=True)
    record = {}
    for model in MODELS:
        for mk in sorted({r["market"] for r in rows if r["model"] == model}):
            gr = [r for r in rows if r["model"] == model and r["market"] == mk and r["state"] == "graded"]
            bes = [_val(r["break_even"]) for r in gr if _val(r["break_even"]) is not None]
            hits = sum(1 for r in gr if r["won"])
            record.setdefault(model, {})[mk] = {
                "picks": L(len(gr), "DESCRIPTIVE"), "hits": L(hits, "DESCRIPTIVE"),
                "hit_rate": L(round(100.0 * hits / len(gr), 1) if gr else None, "DESCRIPTIVE"),
                "break_even": L(round(sum(bes) / len(bes), 1) if bes else None, "MARKET"),
                "pending": L(sum(1 for r in rows if r["model"] == model and r["market"] == mk
                                 and r["state"] == "pending"), "DESCRIPTIVE"),
                "verdict": verdicts[model].get(mk)}
    doc = {"league": lg, "kind": "DESCRIPTIVE", "title": "What the model showed, graded",
           "from": LEDGER_FROM, "built_at": _iso(when), "snapshots": len(snaps),
           "spec": "research/fb_model_live_spec.md", "record": record, "picks": rows,
           "note": ("Every pick the models showed before kickoff, saved and frozen, then graded. "
                    "Nothing here is recalculated after it is graded.")}
    path = out or os.path.join(latest, "model-ledger.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    log("%s ledger: %d snapshot(s), %d pick(s), %d graded" % (
        lg, len(snaps), len(rows), sum(1 for r in rows if r["state"] == "graded")))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
