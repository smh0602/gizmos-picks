#!/usr/bin/env python3
"""fb_refit.py — THE FOOTBALL GAME MODEL'S WEEKLY CONTEST AND SCOREBOARD.
`[Sam, 2026-10-12]` "how do we make sure the model knows these teams better
than they do or in the least is learning how to do so". T65, frozen in
`research/fb_refit_spec.md` §2 before any challenger result.

    python fb_refit.py weekly     # both leagues -> data/<lg>/latest/fb-refit.json

Run every Monday by its own workflow (docs/upload/fb-refit.yml), on GitHub,
from the repo's own files only. Its email text is status.py's (⛔ status and
the watchdog never import this: fb_model drags in card_fb, which exits under mlb). ⛔ It never calls Claude, never opens a PR and
never touches main: when a challenger WINS it pushes ONE branch,
fb/champion-<lg>-<name>-<date>, whose only change is that league's
`fb_model.CHAMPION` entry, and the Monday status email tells Sam.
⛔ The scoreboard is a report; it decides nothing. Stdlib only.
"""
import datetime
import glob
import json
import math
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

import dossier_fb as D
import fb_challengers as FC
import fb_model as FM
import mlb_refit                     # paired_test_clustered: the ONE clustered paired test

ROOT = FM.ROOT
LEAGUES = (("nfl", "NFL"), ("ncaaf", "College"))
SEASON = 2026                        # the scoreboard's season
REGISTERED_FROM = "2026-10-19"       # ⛔ §2: the first Monday after T65's PR
MIN_SCORED = 300                     # ⛔ §2
ALPHA = 0.01                         # ⛔ §2, divided by the league's registered count
WITHDRAW_ALPHA = 0.05                # ⛔ §2, P and T only
Z90 = 1.645


def log(m):
    print(m, flush=True)


def loss(p, y):
    p = min(1.0 - 1e-12, max(1e-12, p))
    return -math.log(p if y else 1.0 - p)


def monday_on_or_after(day):
    d = datetime.date.fromisoformat(day)
    return (d + datetime.timedelta(days=(7 - d.weekday()) % 7)).isoformat()


class Fits:
    """One feature function's walk-forward fits, each made once: train on the
    labelled rows dated before the Monday (walk_forward's cut), fit(zmax=ZMAX)."""

    def __init__(self, rows, feat):
        self.rows, self.feat, self.data, self.models = rows, feat, {}, {}

    def model(self, wk, mk):
        if (wk, mk) not in self.models:
            if mk not in self.data:
                self.data[mk] = [(r["day"], self.feat(r, mk), FM.label(r, mk))
                                 for r in self.rows if FM.label(r, mk) is not None]
            tr = [(x, y) for d, x, y in self.data[mk] if d < wk]
            self.models[(wk, mk)] = FM.fit([x for x, _ in tr], [y for _, y in tr], zmax=FM.ZMAX)
        return self.models[(wk, mk)]

    def predictions(self, mk, keep=lambda r: True):
        """{game_id: (p, y, Monday, row)} for every final labelled row it prices."""
        out = {}
        for r in self.rows:
            y = FM.label(r, mk)
            if y is None or not keep(r):
                continue
            wk = FM.monday(r["day"])
            m = self.model(wk, mk)
            if m:
                out[r["id"]] = (FM.predict(m, self.feat(r, mk)), y, wk, r)
        return out


def challenger_feat(name):
    return lambda r, mk, M=None: FC.extend(name, r, mk, FM.features(r, mk, M=M), M)


# ══════════════════════════════════════════════════════════════════════
# THE CONTEST (§2)
# ══════════════════════════════════════════════════════════════════════
def first_added(paths, root=ROOT):
    """The day the last of `paths` first reached the repo (git), or None."""
    days = []
    for p in paths:
        if not os.path.exists(p):
            return None
        r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cs", "--", os.path.relpath(p, root)],
                           capture_output=True, text=True, cwd=root)
        got = r.stdout.split() if r.returncode == 0 else []
        if not got:
            return None
        days.append(got[-1])
    return max(days) if days else None


def registration(name, root=ROOT, added=None):
    """§2: the later of its registration Monday (REGISTERED_FROM; T66's carry
    their own, §3a) and the first Monday on or after the day its data first
    exists for every season it reads. None: no data yet. A challenger that
    reads no new file (S) is registered on its Monday."""
    c = FC.CHALLENGERS[name]
    start = c.get("registered_from", REGISTERED_FROM)
    paths = [os.path.join(FC.latest(c["league"], root), f.format(s=s))
             for s in FM.SEASONS for f in c["files"]]
    if not paths:
        return start
    day = (added or {}).get(name) if added and name in added else first_added(paths, root)
    return max(start, monday_on_or_after(day)) if day else None


def test(pairs):
    d = [a - b for a, b, _g in pairs]
    n, mean, _t, p, G = mlb_refit.paired_test_clustered(d, [g for _a, _b, g in pairs])
    _n, _m, _t2, p_wrong, _G = mlb_refit.paired_test_clustered([-x for x in d], [g for *_x, g in pairs])
    r = lambda v: None if v is None else round(v, 6)  # noqa: E731
    return {"predictions": n, "games": G, "mean_d": r(mean), "p": r(p), "p_wrong_way": r(p_wrong),
            "champion_log_loss": r(sum(a for a, _b, _g in pairs) / n) if n else None,
            "challenger_log_loss": r(sum(b for _a, b, _g in pairs) / n) if n else None}


def contest(rows, champ, name, start, registered, fits=None):
    """One challenger: history (weeks before `start`) and scored (from it on)."""
    c = FC.CHALLENGERS[name]
    out = {"name": name, "what": c["what"], "markets": list(c["markets"]), "registered": registered,
           "scored_from": start}
    if not registered:
        return dict(out, verdict="NO DATA")
    fits = fits or Fits(rows, challenger_feat(name))
    hist, scored = [], []
    for mk in c["markets"]:
        a = champ.predictions(mk)
        for gid, (p_x, y, wk, _r) in fits.predictions(mk).items():
            if gid in a:
                (scored if wk >= start else hist).append((loss(a[gid][0], y), loss(p_x, y), gid))
    out["history"] = test(hist)
    h = out["history"]
    out["withdrawn"] = bool(c["withdrawable"] and h["mean_d"] is not None and h["mean_d"] < 0
                            and h["p_wrong_way"] is not None and h["p_wrong_way"] < WITHDRAW_ALPHA)
    out["scored"] = test([] if out["withdrawn"] else scored)
    return out


def verdicts(results):
    """§2: WINS needs MIN_SCORED predictions, mean d > 0 and p < ALPHA / the
    number of challengers registered and not withdrawn in the league."""
    k = sum(1 for x in results if x["registered"] and not x.get("withdrawn"))
    for x in results:
        if not x["registered"]:
            continue
        x["alpha"] = ALPHA / k if k else None
        s = x["scored"]
        if x["withdrawn"]:
            x["verdict"] = "WITHDRAWN"
        elif s["predictions"] < MIN_SCORED:
            x["verdict"] = "NOT YET MEASURABLE"
        elif s["mean_d"] > 0 and s["p"] is not None and s["p"] < x["alpha"]:
            x["verdict"] = "WINS"
        else:
            x["verdict"] = "NOT YET"
    return results


# ══════════════════════════════════════════════════════════════════════
# THE SCOREBOARD (a report; it decides nothing)
# ══════════════════════════════════════════════════════════════════════
def interval(v):
    n = len(v)
    m = sum(v) / n
    h = Z90 * statistics.stdev(v) / math.sqrt(n) if n > 1 else None
    return m, (None if h is None else m - h), (None if h is None else m + h)


def side(lo, hi, below, above, neither):
    return neither if lo is None else below if hi < 0 else above if lo > 0 else neither


def gap(preds, mk):
    """The champion's log loss minus the books' (moneyline: pml; spread and total 0.5)."""
    rows = [(loss(p, y), loss(r["pml"] if mk == "moneyline" else 0.5, y), wk) for p, y, wk, r in preds]
    if not rows:
        return {"predictions": 0}
    g = [a - b for a, b, _w in rows]
    m, lo, hi = interval(g)
    out = {"predictions": len(g), "model_log_loss": round(sum(a for a, _b, _w in rows) / len(g), 4),
           "books_log_loss": round(sum(b for _a, b, _w in rows) / len(g), 4),
           "gap": round(m, 4), "lo": lo and round(lo, 4), "hi": hi and round(hi, 4),
           "state": side(lo, hi, "ahead", "behind", "level")}
    weeks = sorted({w for *_x, w in rows})
    A, B = weeks[-4:], weeks[-8:-4]
    a = [x for x, (_p, _q, w) in zip(g, rows) if w in A]
    b = [x for x, (_p, _q, w) in zip(g, rows) if w in B]
    t = {"weeks": A, "before": B, "state": "no clear change yet"}
    if len(a) > 1 and len(b) > 1:
        diff = sum(a) / len(a) - sum(b) / len(b)
        se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
        lo, hi = diff - Z90 * se, diff + Z90 * se
        t.update(diff=round(diff, 4), lo=round(lo, 4), hi=round(hi, 4),
                 state=side(lo, hi, "closer", "further", "no clear change yet"))
    out["trend"] = t
    said = [max(p, 1 - p) for p, *_x in preds]
    hit = [(y == 1) == (p >= 0.5) for p, y, *_x in preds]
    out["said"] = round(100 * sum(said) / len(said), 1)
    out["hit"] = round(100 * sum(hit) / len(hit), 1)
    return out


def misses(rows):
    """Mean |own number - final| beside mean |the books' line - final|."""
    ok = [r for r in rows if r["season"] == SEASON and r["final"] and r["hs"] is not None and None not in (
        r["M"], r["T"], r["sig"].get("own_m"), r["sig"].get("own_t"))]
    if not ok:
        return {"games": 0}
    mean = lambda v: round(sum(v) / len(v), 2)  # noqa: E731
    mg = [float(r["hs"]) - float(r["as"]) for r in ok]
    tt = [float(r["hs"]) + float(r["as"]) for r in ok]
    return {"games": len(ok),
            "margin_model": mean([abs(r["sig"]["own_m"] - m) for r, m in zip(ok, mg)]),
            "margin_books": mean([abs(r["M"] - m) for r, m in zip(ok, mg)]),
            "total_model": mean([abs(r["sig"]["own_t"] - t) for r, t in zip(ok, tt)]),
            "total_books": mean([abs(r["T"] - t) for r, t in zip(ok, tt)])}


def snapshots(lg, root=ROOT):
    """{(home, away): [(commence day, pulled_at, snap)]} — every stored snapshot
    pulled before kickoff, Sam's three books, matched as fb_model.board_prices."""
    resolve, ok, out = D.team_codes(lg), FM.books_ok(lg), {}
    for f in sorted(glob.glob(os.path.join(root, "data", lg, "20*", "gamelines", "*.json.gz"))):
        doc = FM.jz(f) or {}
        pulled = doc.get("pulled_at") or ""
        for g in doc.get("games") or []:
            c = g.get("commence") or ""
            home, away = resolve(g.get("home")), resolve(g.get("away"))
            bk = {k: v for k, v in (g.get("books") or {}).items() if k in ok}
            if pulled and c and pulled < c and home and away and bk:
                out.setdefault((home, away), []).append(
                    (c[:10], pulled, {"names": (g.get("home"), g.get("away")), "books": bk}))
    return out


def line_of(snap):
    bl = FM.book_lines(snap)
    med = lambda v: statistics.median(v) if v else None  # noqa: E731
    return (med([m for _b, m, _h, _a in bl["spread"]]), med([t for _b, t, _o, _u in bl["total"]]),
            med([FM.devig(h, a) for _b, h, a in bl["moneyline"] if h is not None and a is not None]))


def line_moves(rows, fits, snaps):
    """Toward / against / unmoved per market. ⛔ Only snapshots pulled on or after
    the row's Monday 00:00Z, the model's information cut; at least two."""
    out = {mk: {"toward": 0, "against": 0, "unmoved": 0} for mk in FM.MARKETS}
    games = 0
    for r in rows:
        if r["season"] != SEASON:
            continue
        wk = FM.monday(r["day"])
        k = datetime.datetime.strptime(r["day"], "%Y-%m-%d")
        got = sorted((pulled, s) for d, pulled, s in snaps.get((r["home"], r["away"]), [])
                     if D._near(d, k) and pulled >= wk + "T00:00:00Z")
        if len(got) < 2:
            continue
        (M0, T0, p0), (M1, T1, p1) = line_of(got[0][1]), line_of(got[-1][1])
        games += 1
        for mk, a, b, kw in (("spread", M0, M1, {"M": M0}), ("total", T0, T1, {"T": T0}),
                             ("moneyline", p0, p1, {})):
            m = fits.model(wk, mk)
            if a is None or b is None or not m:
                continue
            p = FM.predict(m, FM.features(r, mk, **kw))
            up = p > (p0 if mk == "moneyline" else 0.5)
            still = abs(b - a) < 0.005 if mk == "moneyline" else b == a
            out[mk]["unmoved" if still else "toward" if (b > a) == up else "against"] += 1
    for v in out.values():
        n = v["toward"] + v["against"]
        v["toward_share"] = round(100.0 * v["toward"] / n, 1) if n else None
    return dict(out, games=games)


# ══════════════════════════════════════════════════════════════════════
# THE WEEK
# ══════════════════════════════════════════════════════════════════════
def league(lg, root=ROOT, now=None, rows=None, prev=None, added=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    today = now.strftime("%Y-%m-%d")
    rows = FM.build_rows(lg, root) if rows is None else rows
    champion = FM.CHAMPION.get(lg)
    names = [n for n, c in FC.CHALLENGERS.items() if c["league"] == lg and n != champion]
    for n in names:
        FC.attach(n, lg, rows, root)
    since = (prev or {}).get("champion_since")
    if prev is not None and prev.get("champion") != champion:
        since = monday_on_or_after(today)          # §2: scored weeks restart at the next Monday
    champ = Fits(rows, FM.features)
    res = []
    for n in names:
        reg = registration(n, root, added)
        res.append(contest(rows, champ, n, max(reg, since or "") if reg else None, reg))
    sb = {mk: gap(list(champ.predictions(mk, lambda r: r["season"] == SEASON).values()), mk)
          for mk in FM.MARKETS}
    return {"league": lg, "kind": "DESCRIPTIVE", "spec": "research/fb_refit_spec.md",
            "built_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "champion": champion,
            "champion_since": since, "season": SEASON, "scoreboard": sb, "miss": misses(rows),
            "line_moves": line_moves(rows, champ, snapshots(lg, root)),
            "challengers": verdicts(res)}


def set_champion(src, lg, name):
    """fb_model.py's text with ONE change: that league's CHAMPION entry."""
    out, n = re.subn(r'(?m)^(CHAMPION = \{.*"%s": )(None|"[A-Z]+")' % lg, r'\g<1>"%s"' % name, src)
    if n != 1:
        raise RuntimeError("CHAMPION line not found once in fb_model.py")
    return out


def push_branch(lg, name, day, root=ROOT, run=subprocess.run):
    """⛔ ONE branch per league while any fb/champion-<lg>-* is on origin; never main, never a PR."""
    def git(*a, cwd=root):
        r = run(["git"] + list(a), capture_output=True, text=True, cwd=cwd)
        if r.returncode != 0:
            raise RuntimeError("git %s failed: %s" % (" ".join(a), r.stderr.strip()))
        return r.stdout
    have = git("ls-remote", "--heads", "origin", "refs/heads/fb/champion-%s-*" % lg).split()
    if have:
        return have[1].replace("refs/heads/", ""), False
    branch = "fb/champion-%s-%s-%s" % (lg, name, day)
    tmp = tempfile.mkdtemp(prefix="fb-champion-")
    os.rmdir(tmp)
    git("fetch", "origin", "main")
    git("worktree", "add", "-b", branch, tmp, "origin/main")
    try:
        p = os.path.join(tmp, "fb_model.py")
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(set_champion(src, lg, name))
        git("-c", "user.name=github-actions[bot]",
            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-am", "fb: challenger %s won T65 (%s) — champion switch for Sam" % (name, lg), cwd=tmp)
        git("push", "origin", "%s:refs/heads/%s" % (branch, branch), cwd=tmp)
    finally:
        run(["git", "worktree", "remove", "--force", tmp], capture_output=True, text=True, cwd=root)
    return branch, True


def weekly(root=ROOT, now=None, run=subprocess.run, added=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    for lg, _name in LEAGUES:
        t0 = time.time()
        path = os.path.join(root, "data", lg, "latest", "fb-refit.json")
        prev = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                prev = json.load(fh)
        doc = league(lg, root, now, prev=prev, added=added)
        for x in doc["challengers"]:
            if x["verdict"] == "WINS":
                x["branch"], x["branch_pushed"] = push_branch(lg, x["name"], now.strftime("%Y-%m-%d"), root, run)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
        log("%s: %s (%.0fs)" % (lg, "; ".join("%s %s" % (x["name"], x["verdict"])
                                              for x in doc["challengers"]), time.time() - t0))


if __name__ == "__main__":
    if sys.argv[1:] != ["weekly"]:
        sys.exit("usage: python fb_refit.py weekly")
    weekly()
