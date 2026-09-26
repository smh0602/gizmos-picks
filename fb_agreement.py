#!/usr/bin/env python3
"""fb_agreement.py — does the props card agree with the props model?

    LEAGUE=nfl python fb_agreement.py

Every row the football props card or the props model publishes gets one
label, exactly as `research/fb_agreement_spec.md` fixes it (Sam, 2026-09-25;
committed on its own before this file existed):

  AGREE       both probabilities on the same side of the row's break-even
  SPLIT       one above the break-even, one below
  ONE SOURCE  only one of them rates the row

⛔ A NOTE, NEVER A LEVER. The label removes, hides, re-ranks and re-prices
nothing, and feeds neither model. Whether it ever may is Sam's decision.
⛔ RULE 55. The label is DESCRIPTIVE; the props model's probability is MODEL;
the card's keeps the card's own basis (RECORD for football — a record rate
never wears MODEL); the break-even is MARKET.
⛔ FROZEN AND GRADED ONCE. Labels are archived through `daystore` every card
run they change; a row is graded on the last copy frozen before kickoff,
with the card's own grader, and a grade is never recomputed.
⚠️ STDLIB ONLY. Rides the free `card-fb` run, after the props model.
"""
import datetime
import glob
import gzip
import hashlib
import json
import math
import os
import sys

import daystore                     # the ONE dated, write-once writer
import fb_ledger                    # grade_prop_pick — the card's own join and grader
import fb_model as F                # record (clustered by game), monday
import fb_props_model as M          # load_logs, name_index, league

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
LEAGUES = ("nfl", "ncaaf")
LABELS = ("AGREE", "SPLIT", "ONE SOURCE")
MIN_AGREE, MIN_SPLIT, MIN_WEEKS, ALPHA = 300, 100, 3, 0.05     # ⛔ spec §3b
BASES = {"label": "DESCRIPTIVE", "model_p": "MODEL", "break_even": "MARKET",
         "price": "MARKET", "line": "MARKET"}   # card_p: the card's own `card_basis`


def log(m):
    print(m, flush=True)


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
    except (OSError, ValueError, EOFError):
        return None


def _data(lg, root=None):
    return os.path.join(root or ROOT, "data", lg)


def key_of(game_id, player, market, side, line):
    return "%s|%s|%s|%s|%s" % (game_id, player, market, side, "" if line is None else float(line))


def label(card_p, model_p, be):
    """spec §3a. ≥ the break-even is one side, < it the other."""
    if card_p is None and model_p is None:
        return None
    if card_p is None or model_p is None:
        return "ONE SOURCE"
    return "AGREE" if (card_p >= be) == (model_p >= be) else "SPLIT"


def rows(card, model):
    """Every row the card or the model publishes, labelled, each once."""
    rated = {key_of(r["game_id"], r["player"], r["market"], r["side"], r["line"]): r["p"]
             for r in (model or {}).get("rated") or []}
    out = {}
    for r in (card or {}).get("picks") or []:
        if r.get("confidence") is None or r.get("break_even") is None:
            continue
        k = key_of(r["game_id"], r["player"], r["market"], r["side"], r["line"])
        out[k] = {"key": k, "game_id": r["game_id"], "game": r.get("game"), "commence": r.get("commence"),
                  "player": r["player"], "market": r["market"], "side": r["side"], "line": r["line"],
                  "price": r.get("price"), "break_even": r["break_even"],
                  "card_p": r["confidence"], "card_basis": r.get("confidence_basis") or "RECORD",
                  "model_p": rated.get(k), "on_card": True}
    for r in (model or {}).get("picks") or []:
        k = key_of(r["game_id"], r["player"], r["market"], r["side"], _val(r["line"]))
        if k in out:
            continue
        out[k] = {"key": k, "game_id": r["game_id"], "game": r.get("game"), "commence": r.get("commence"),
                  "player": r["player"], "market": r["market"], "side": r["side"], "line": _val(r["line"]),
                  "price": _val(r.get("price")), "break_even": _val(r["break_even"]),
                  "card_p": None, "card_basis": None,
                  "model_p": _val(r.get("model_probability")), "on_card": False}
    for r in out.values():
        r["label"] = label(r["card_p"], r["model_p"], r["break_even"])
    return sorted(out.values(), key=lambda r: (r["commence"] or "", r["player"], r["market"]))


# ── freeze ───────────────────────────────────────────────────────────────
def freeze(lg, rs, root=None, now=None, log=log):
    now = now or _now()
    ahead = [r for r in rs if (r.get("commence") or "") > _iso(now)]
    if not ahead:
        return None
    fp = hashlib.sha256(json.dumps(ahead, sort_keys=True).encode("utf-8")).hexdigest()
    arch = sorted(glob.glob(os.path.join(_data(lg, root), "20*", "agreement", "*.json.gz")))
    if arch and (_gz(arch[-1]) or {}).get("fingerprint") == fp:
        return None
    p, wrote = daystore.archive({"league": lg, "taken_at": _iso(now), "fingerprint": fp,
                                 "rows": ahead, "bases": BASES}, _data(lg, root), "agreement",
                                log=log, when=now)
    return p if wrote else None


def frozen_rows(lg, root=None):
    """spec §3a: each row from the LAST copy frozen before its kickoff."""
    chosen = {}
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "agreement", "*.json.gz"))):
        d = _gz(p) or {}
        for r in d.get("rows") or []:
            if d.get("taken_at", "") < (r.get("commence") or ""):
                chosen[r["key"]] = dict(r, taken_at=d["taken_at"], league=lg)
    return list(chosen.values())


NOT_FROZEN = "no label was frozen before kickoff"


def settle(rs, frozen, now):
    """What the page file shows once a game has kicked off.

    🔴 `[2026-09-26, the defect this fixes]` The props model rates only games
    NOT yet started, so a label recomputed after kickoff finds no model
    number and reads ONE SOURCE — measured on the live file 2026-09-25
    07:14Z: 25/25 NFL and 23/23 college rows ONE SOURCE, while the frozen
    record was right. ⛔ So a row whose game has kicked off NEVER gets a
    fresh label: it shows its last copy frozen before kickoff (the same row
    the record grades), marked as such, and a row that was never frozen
    shows no label and says so — never a fresh ONE SOURCE.
    ⚠️ A started game shows exactly the rows its card still shows, each with
    its own frozen label. A frozen row the card no longer shows (a line that
    moved) stays in the record but is not counted on the board.
    """
    now_s = _iso(now)
    started = {r["game_id"] for r in rs if (r.get("commence") or "") <= now_s}
    out = [r for r in rs if r["game_id"] not in started]
    by_game = {}
    for f in frozen:
        if f["game_id"] in started:
            by_game.setdefault(f["game_id"], {})[f["key"]] = f
    for r in rs:
        if r["game_id"] not in started:
            continue
        f = by_game.get(r["game_id"], {}).get(r["key"])
        if f:
            out.append(dict(f, frozen_before_kickoff=True, frozen_at=f["taken_at"]))
        else:
            out.append(dict(r, label=None, model_p=None, frozen_before_kickoff=False, label_note=NOT_FROZEN))
    return sorted(out, key=lambda r: (r["commence"] or "", r["player"], r["market"], r["side"]))


# ── grade, once ──────────────────────────────────────────────────────────
def stored_grades(lg, root=None):
    out = {}
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "agreement-grades", "*.json.gz"))):
        for g in (_gz(p) or {}).get("grades") or []:
            out.setdefault(g["key"], g)                # ⛔ the FIRST stored grade stands
    return out


def grade_new(lg, frozen, stored, root=None, now=None, log=log, logs=None):
    todo = [r for r in frozen if r["key"] not in stored]
    if not todo:
        return []
    logs = logs if logs is not None else M.load_logs(lg, root)
    idx = M.name_index(logs)
    new = []
    with M.league(lg):
        for r in todo:
            state, won = fb_ledger.grade_prop_pick(lg, r, logs, idx)
            if state in ("graded", "void"):
                new.append({"key": r["key"], "state": state, "won": won, "graded_at": _iso(now or _now())})
    if new:
        daystore.archive({"league": lg, "grades": new}, _data(lg, root), "agreement-grades",
                         log=log, when=now)
    return new


# ── the record and the question ─────────────────────────────────────────
def graded(frozen, grades):
    return [dict(r, won=grades[r["key"]]["won"]) for r in frozen
            if r["key"] in grades and grades[r["key"]]["state"] == "graded"]


def record_by_label(g):
    return {lb: F.record([{"won": r["won"], "break_even": r["break_even"] / 100.0,
                           "game_id": r["game_id"], "assumed": False} for r in g if r["label"] == lb])
            for lb in LABELS}


def cr1_diff(rows_):
    """spec §3b: Δ = mean d(AGREE) − mean d(SPLIT), CR1 by game, one-sided p."""
    ys = [(1.0 if r["won"] else 0.0) - r["break_even"] / 100.0 for r in rows_]
    xs = [1.0 if r["label"] == "AGREE" else 0.0 for r in rows_]
    n = len(ys)
    na = int(sum(xs))
    if na == 0 or na == n:
        return None, None
    ma = sum(y for y, x in zip(ys, xs) if x) / na
    ms = sum(y for y, x in zip(ys, xs) if not x) / (n - na)
    delta = ma - ms
    # X = [1, x]; beta = [ms, delta]; (X'X)^-1 in closed form
    sxx = [[n, na], [na, na]]
    det = sxx[0][0] * sxx[1][1] - sxx[0][1] * sxx[1][0]
    inv = [[sxx[1][1] / det, -sxx[0][1] / det], [-sxx[1][0] / det, sxx[0][0] / det]]
    meat = [[0.0, 0.0], [0.0, 0.0]]
    by = {}
    for r, y, x in zip(rows_, ys, xs):
        e = y - (ms + delta * x)
        s = by.setdefault(r["game_id"], [0.0, 0.0])
        s[0] += e
        s[1] += e * x
    for s in by.values():
        for i in range(2):
            for j in range(2):
                meat[i][j] += s[i] * s[j]
    G = len(by)
    if G < 2 or n <= 2:
        return delta, None
    c = (G / (G - 1.0)) * ((n - 1.0) / (n - 2.0))
    v11 = c * sum(inv[1][i] * meat[i][j] * inv[j][1] for i in range(2) for j in range(2))
    if v11 <= 0:
        return delta, None
    z = delta / math.sqrt(v11)
    return delta, 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def question(all_graded):
    """spec §3b, pooled across both leagues."""
    rs = [r for r in all_graded if r["label"] in ("AGREE", "SPLIT")]
    na = sum(1 for r in rs if r["label"] == "AGREE")
    ns = len(rs) - na
    weeks = len({F.monday(r["commence"][:10]) for r in rs if r.get("commence")})
    delta, p = cr1_diff(rs)
    if na < MIN_AGREE or ns < MIN_SPLIT or weeks < MIN_WEEKS:
        state = "NOT YET MEASURABLE"
    elif delta is not None and delta > 0 and p is not None and p < ALPHA:
        state = "PASSES"
    else:
        state = "FAILS"
    by = {}
    for lg in LEAGUES:
        sub = [r for r in rs if r.get("league") == lg]
        d, pp = cr1_diff(sub)
        by[lg] = {"agree": sum(1 for r in sub if r["label"] == "AGREE"),
                  "split": sum(1 for r in sub if r["label"] == "SPLIT"),
                  "delta_points": round(100 * d, 1) if d is not None else None,
                  "p": round(pp, 4) if pp is not None else None}
    return {"basis": "DESCRIPTIVE", "state": state, "agree_graded": na, "split_graded": ns,
            "weeks": weeks, "delta_points": round(100 * delta, 1) if delta is not None else None,
            "p": round(p, 4) if p is not None else None,
            "min": {"agree": MIN_AGREE, "split": MIN_SPLIT, "weeks": MIN_WEEKS}, "alpha": ALPHA,
            "by_league": by,
            "consequence": ("Nothing changes on its own. Whether the label may ever touch a pick, a "
                            "ranking or a price is Sam's decision, in a separate PR he asks for.")}


def build(lg=None, root=None, now=None, log=log, logs=None):
    lg = (lg or LEAGUE).lower()
    now = now or _now()
    card = _json(os.path.join(root or ROOT, "picks", "fb-%s-latest.json" % lg))
    model = _json(os.path.join(_data(lg, root), "latest", "fb-props-model.json"))
    fresh = rows(card, model)
    frz = freeze(lg, fresh, root, now, log)
    # ⛔ AFTER the freeze, and only for display: a started game's rows are
    #    its frozen pre-kickoff rows, never a label recomputed after kickoff.
    rs = settle(fresh, frozen_rows(lg, root), now)
    grades = stored_grades(lg, root)
    for g in grade_new(lg, frozen_rows(lg, root), grades, root, now, log, logs):
        grades.setdefault(g["key"], g)
    mine = graded(frozen_rows(lg, root), grades)
    both = list(mine)
    for other in LEAGUES:
        if other != lg:
            both += graded(frozen_rows(other, root), stored_grades(other, root))
    doc = {"league": lg, "kind": "DESCRIPTIVE", "spec": "research/fb_agreement_spec.md",
           "built_at": _iso(now), "bases": BASES, "rows": rs,
           "counts": {lb: sum(1 for r in rs if r["label"] == lb) for lb in LABELS},
           "not_frozen": sum(1 for r in rs if r.get("label_note") == NOT_FROZEN),
           "record": record_by_label(mine), "question": question(both),
           "note": ("A note on the row, never a lever: the label changes no pick, ranking or price. "
                    "The card's number is its own rate (RECORD); the model's is MODEL; the "
                    "break-even is the row's price (MARKET). Graded once from the result; rates "
                    "use the effective n clustered by game.")}
    with open(os.path.join(_data(lg, root), "latest", "agreement.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    log("agreement %s: %s; frozen %s; question %s" % (
        lg, doc["counts"], frz or "unchanged", doc["question"]["state"]))
    return doc


if __name__ == "__main__":
    build()
    sys.exit(0)
