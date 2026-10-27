#!/usr/bin/env python3
"""fb_refit.py — THE FOOTBALL GAME MODEL'S WEEKLY CONTEST AND SCOREBOARD.
`[Sam, 2026-10-12]` "how do we make sure the model knows these teams better
than they do or in the least is learning how to do so". T65, frozen in
`research/fb_refit_spec.md` §2 before any challenger result.
`[Sam, 2026-10-26]` T73 (§3g): *"instead of having it need 300 scored prediction
can we just use games from last season and the ones played this season for both
cfb and nfl"*. The verdict reads each challenger's COUNTED predictions: every
2025-2026 walk-forward week, except for the eight shaped on those games
(`SCORED_ONLY`), which still count only the weeks from registration.

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
# ⛔ §2; `[Sam, 2026-10-26]` §3g: ~~300 scored predictions~~ 300 COUNTED predictions in which
#    the challenger's prediction differs from the champion's (one equal to it carries no evidence).
MIN_SCORED = 300
ALPHA = 0.01                         # ⛔ §2, divided by the league's registered count
WITHDRAW_ALPHA = 0.05                # ⛔ §2, P and T only
# ⛔ §3g, FROZEN: the eight still judged only on games after registration (§2), each designed or
#    registered after its results on these same games were seen. Every other challenger counts
#    every walk-forward week of the stored seasons (`fb_model.SEASONS`). test_fb_refit_counted.py
#    pins this list to §3g's own text.
SCORED_ONLY = ("S", "TS", "AV", "AVC", "AT", "ATC", "SM", "SMC")
# ⛔ §3g: P and T's withdrawal reads §2's history window, the weeks before 2026-10-19, fixed:
#    a champion switch moves `scored_from`, never this.
WITHDRAW_BEFORE = "2026-10-19"
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


def challenger_fits(rows, name, lg, root=ROOT):
    """A challenger's walk-forward fits; §3d's H / HC also train on the history rows."""
    extra = FC.history_rows(lg, root) if FC.CHALLENGERS[name].get("history") else []
    return Fits(list(rows) + extra, challenger_feat(name))


def challenger_feat(name):
    return lambda r, mk, M=None, T=None: FC.extend(name, r, mk, FM.features(r, mk, M=M, T=T), M, T)


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


def merged_on(name, root=ROOT):
    """§3e: the day challenger `name`'s entry first reached this checkout's
    first-parent line (on main: its PR's merge day), or None without git history."""
    needle = '"%s": {"league": "%s"' % (name, FC.CHALLENGERS[name]["league"])
    r = subprocess.run(["git", "log", "--first-parent", "--format=%cs", "-S", needle, "--", "fb_challengers.py"],
                       capture_output=True, text=True, cwd=root)
    got = r.stdout.split() if r.returncode == 0 else []
    return got[-1] if got else None


def registration(name, root=ROOT, added=None):
    """§2: the later of its registration Monday (REGISTERED_FROM; T66's carry
    their own, §3a) and the first Monday on or after the day its data first
    exists for every season it reads. None: no data yet. A challenger that
    reads no new file (S) is registered on its Monday. §3e (T71): an `on_merge`
    challenger, the later of its Monday and the first Monday AFTER its merge day
    (~~on or after~~: a Monday-evening merge would score that night's game)."""
    c = FC.CHALLENGERS[name]
    start = c.get("registered_from", REGISTERED_FROM)
    if c.get("on_merge"):
        merged = (added or {}).get(name) if added and name in added else merged_on(name, root)
        after = (datetime.date.fromisoformat(merged) + datetime.timedelta(days=1)).isoformat() if merged else None
        return max(start, monday_on_or_after(after)) if after else None
    paths = [os.path.join(FC.latest(c["league"], root), f.format(s=s))
             for s in c.get("seasons", FM.SEASONS) for f in c["files"]]
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


def contest(rows, champ, name, start, registered, fits=None, entered=True):
    """One challenger: history (weeks before `start`) and scored (from it on), kept for information.
    `[Sam, 2026-10-26]` §3g: the verdict reads `counted`: EVERY walk-forward prediction for a
    challenger not in SCORED_ONLY (`counts` "all"), only the scored weeks for one in it ("scored"),
    nothing before its registration Monday (`entered` False) and nothing once WITHDRAWN.
    `differing` is how many of them differ from the champion's (§3g's floor). P and T's
    withdrawal reads the weeks before WITHDRAW_BEFORE, whatever `start` a champion switch set."""
    c = FC.CHALLENGERS[name]
    out = {"name": name, "what": c["what"], "markets": list(c["markets"]), "registered": registered,
           "scored_from": start, "counts": "scored" if name in SCORED_ONLY else "all"}
    if not registered:
        return dict(out, verdict="NO DATA")
    fits = fits or Fits(rows, challenger_feat(name))
    preds = []                                   # (Monday, (champion loss, challenger loss, game), differs)
    for mk in c["markets"]:
        a = champ.predictions(mk)
        # `[R1, 2026-10-18]` only the games the champion prices: a pair needs both, so this
        #    changes no number, and H / HC no longer fit every history-row Monday (test_fb_refit §16).
        for gid, (p_x, y, wk, _r) in fits.predictions(mk, lambda r: r["id"] in a).items():
            if gid in a:
                preds.append((wk, (loss(a[gid][0], y), loss(p_x, y), gid), p_x != a[gid][0]))
    scored = [x for x in preds if x[0] >= start]
    out["history"] = test([pair for wk, pair, _df in preds if wk < start])
    h = test([pair for wk, pair, _df in preds if wk < WITHDRAW_BEFORE]) if c["withdrawable"] else None
    out["withdrawn"] = bool(c["withdrawable"] and h["mean_d"] is not None and h["mean_d"] < 0
                            and h["p_wrong_way"] is not None and h["p_wrong_way"] < WITHDRAW_ALPHA)
    if h is not None:
        out["withdrawal_window"] = dict(h, before=WITHDRAW_BEFORE)
    out["scored"] = test([] if out["withdrawn"] else [pair for _wk, pair, _df in scored])
    counted = [] if out["withdrawn"] or not entered else scored if name in SCORED_ONLY else preds
    out["counted"] = dict(test([pair for _wk, pair, _df in counted]),
                          differing=sum(1 for _wk, _pair, df in counted if df))
    return out


def verdicts(results):
    """§2: WINS needs ~~MIN_SCORED predictions~~, mean d > 0 and p < ALPHA / the
    number of challengers registered and not withdrawn in the league (k, unchanged).
    `[Sam, 2026-10-26]` §3g: on the COUNTED predictions (contest), at least MIN_SCORED
    of them differing from the champion's; the test itself runs over all of them."""
    k = sum(1 for x in results if x["registered"] and not x.get("withdrawn"))
    for x in results:
        if not x["registered"]:
            continue
        x["alpha"] = ALPHA / k if k else None
        if x.get("verdict") == "NOT APPLICABLE":      # §4: counted in k, never scored
            continue
        s = x["counted"]
        if x["withdrawn"]:
            x["verdict"] = "WITHDRAWN"
        elif s["differing"] < MIN_SCORED:
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
    # `[Sam, 2026-10-26]` §3g: `since` cuts only the scored weeks (SCORED_ONLY's count restarts);
    #    every other challenger is judged against the new champion over every week, and the
    #    withdrawal window stays the weeks before WITHDRAW_BEFORE. Before its registration
    #    Monday a challenger has not entered the contest: nothing is counted for it yet.
    champ = Fits(rows, FM.features)
    res = []
    for n in names:
        reg = registration(n, root, added)
        if reg and rows and not FC.applies(n, rows[0]):
            c = FC.CHALLENGERS[n]           # §4 `[2026-10-16]`: never a crash, never scored
            res.append({"name": n, "what": c["what"], "markets": list(c["markets"]), "registered": reg,
                        "scored_from": None, "withdrawn": False, "verdict": "NOT APPLICABLE",
                        "why": "its frozen inputs cannot be built against champion %s" % champion})
            continue
        res.append(contest(rows, champ, n, max(reg, since or "") if reg else None, reg,
                           entered=bool(reg) and reg <= today,
                           fits=challenger_fits(rows, n, lg, root) if reg else None))
    sb = {mk: gap(list(champ.predictions(mk, lambda r: r["season"] == SEASON).values()), mk)
          for mk in FM.MARKETS}
    return {"league": lg, "kind": "DESCRIPTIVE", "spec": "research/fb_refit_spec.md",
            "built_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "champion": champion,
            "champion_since": since, "season": SEASON, "floor": MIN_SCORED,
            "scoreboard": sb, "miss": misses(rows),
            "line_moves": line_moves(rows, champ, snapshots(lg, root)),
            "challengers": verdicts(res)}


def set_champion(src, lg, name):
    """fb_model.py's text with ONE change: that league's CHAMPION entry, from None.
    `[R1, 2026-10-18]` ⛔ Never over a named champion (~~`(None|"[A-Z]+")`~~): a
    challenger is scored as the champion PLUS its own input, so naming it alone would
    put a model on the site that was never scored (push_branch's NEEDS SAM)."""
    if re.search(r'(?m)^CHAMPION = \{.*"%s": "[A-Z]+"' % lg, src):
        raise RuntimeError("fb_model.py already names a %s CHAMPION: NEEDS SAM, no switch" % lg)
    out, n = re.subn(r'(?m)^(CHAMPION = \{.*"%s": )None\b' % lg, r'\g<1>"%s"' % name, src)
    if n != 1:
        raise RuntimeError("CHAMPION line not found once in fb_model.py")
    return out


# `[R1, 2026-10-18]` The note a WINS carries when push_branch pushes nothing because the
#    league already has a champion. ⚠️ spec §3 would switch; it was written before stacked
#    champions were thought through, so how a second switch works is Sam's (an ordered list).
NEEDS_SAM = ("NEEDS SAM: %s is already the %s champion and %s was scored as %s plus its own input, so "
             "switching to %s alone would put a model on the site that was never scored. No branch was "
             "pushed; how a second switch works (an ordered CHAMPION list) is a frozen spec rule, yours")


def push_branch(lg, name, day, root=ROOT, run=subprocess.run):
    """⛔ ONE branch per league while any fb/champion-<lg>-* is on origin; never main, never a PR.
    `[R1, 2026-10-18]` ⛔ And none while the league already has a CHAMPION: -> (None, False),
    and weekly() writes NEEDS_SAM on the WINS (status.py puts it under "Needs you")."""
    if FM.CHAMPION.get(lg):
        return None, False

    def edit(tmp):
        p = os.path.join(tmp, "fb_model.py")
        with open(p, encoding="utf-8") as fh:
            src = fh.read()
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(set_champion(src, lg, name))
    return push_change("fb/champion-%s-" % lg, "fb/champion-%s-%s-%s" % (lg, name, day), edit,
                       "fb: challenger %s won T65 (%s) — champion switch for Sam" % (name, lg), root, run)


def _git(run, cwd, *a):
    r = run(["git"] + list(a), capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (" ".join(a), (r.stderr or "").strip()))
    return r.stdout


def branch_file(prefix, path, root=ROOT, run=subprocess.run):
    """-> (the first `<prefix>*` branch on origin, its `path` text) or (None, None).
    ⛔ Raises when git cannot answer: an unknown never reads as "no branch"."""
    have = _git(run, root, "ls-remote", "--heads", "origin", "refs/heads/%s*" % prefix).split()
    if not have:
        return None, None
    branch = have[1].replace("refs/heads/", "")
    _git(run, root, "fetch", "origin", branch)
    return branch, _git(run, root, "show", "FETCH_HEAD:%s" % path)


def push_change(prefix, branch, edit, message, root=ROOT, run=subprocess.run):
    """`edit(tree)` applied to a fresh worktree of origin/main, committed and pushed as `branch`, for
    Sam to merge. ⛔ ONE branch while any `<prefix>*` is on origin; never main, never a PR.
    -> (the branch, pushed now?). `[2026-10-17]` also the injury backtest's (`fb_inj_backtest.auto`)."""
    def git(*a, cwd=root):
        return _git(run, cwd, *a)
    have = git("ls-remote", "--heads", "origin", "refs/heads/%s*" % prefix).split()
    if have:
        return have[1].replace("refs/heads/", ""), False
    tmp = tempfile.mkdtemp(prefix="fb-branch-")
    os.rmdir(tmp)
    git("fetch", "origin", "main")
    git("worktree", "add", "-b", branch, tmp, "origin/main")
    try:
        edit(tmp)
        git("-c", "user.name=github-actions[bot]",
            "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
            "commit", "-am", message, cwd=tmp)
        git("push", "origin", "%s:refs/heads/%s" % (branch, branch), cwd=tmp)
    finally:
        run(["git", "worktree", "remove", "--force", tmp], capture_output=True, text=True, cwd=root)
    return branch, True


def branch_order(results):
    """`[Sam, 2026-10-26]` §3g: every WINS, the one that gets the league's one branch first: the
    largest mean d over its counted predictions; a tie, the smaller p, then the earlier name in
    `fb_challengers.CHALLENGERS`. The others are reported, and get no branch.
    ⚠️ `[review, 2026-10-26]` Ordered on the numbers the report prints (`test()` rounds mean d
    and p to 6 decimals), so Sam can check it from the report: two mean d's within 1e-6 are a
    tie and go to the smaller p (two p's that round to 0 are a tie too), then the name."""
    order = list(FC.CHALLENGERS)
    return sorted((x for x in results if x.get("verdict") == "WINS"),
                  key=lambda x: (-x["counted"]["mean_d"], x["counted"]["p"], order.index(x["name"])))


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
        wins = branch_order(doc["challengers"])
        for x in doc["challengers"]:
            if x["verdict"] == "WINS":
                if x is not wins[0]:          # §3g: every WINS is reported; ONE branch, to the first
                    x["branch"], x["branch_pushed"], x["outranked_by"] = None, False, wins[0]["name"]
                    continue
                x["branch"], x["branch_pushed"] = push_branch(lg, x["name"], now.strftime("%Y-%m-%d"), root, run)
                if not x["branch"]:
                    c = FM.CHAMPION.get(lg)
                    x["needs_sam"] = NEEDS_SAM % (c, lg.upper(), x["name"], c, x["name"])
        # `[Sam, 2026-10-17]` the injury test fixed in advance (research/cfb_injuries_design.md §4),
        #    run once its data is stored, its result kept here; ⛔ never raises, never switches main.
        _was = (prev or {}).get("injury_backtest")
        try:
            import fb_inj_backtest
            doc["injury_backtest"] = fb_inj_backtest.auto(lg, root, now, run, prev=_was)
        except Exception as e:
            doc["injury_backtest"] = dict(_was or {}, error="%s: %s" % (type(e).__name__, e))
        # `[R1, 2026-10-18]` the league's own run time, kept: the job's limit is 90 minutes and
        #    the first real run (2026-10-19) is the first measurement on real data.
        doc["elapsed_seconds"] = round(time.time() - t0, 1)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1)
        log("%s: %s (%.0fs)" % (lg, "; ".join("%s %s" % (x["name"], x["verdict"])
                                              for x in doc["challengers"]), doc["elapsed_seconds"]))


if __name__ == "__main__":
    if sys.argv[1:] != ["weekly"]:
        sys.exit("usage: python fb_refit.py weekly")
    weekly()
