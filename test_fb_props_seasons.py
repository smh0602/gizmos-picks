#!/usr/bin/env python3
r"""test_fb_props_seasons.py — §3i T74: the props model on last season plus this one.

`[Sam, 2026-10-27]` *"set up the monday contest to train it on 25-26"*, then, shown the six
rules (research/fb_refit_spec.md §3i), *"build as written"*. Every check runs on planted data:
no walk-forward of the stored logs, no stored report, nothing read from production.

# @vacuity only the season in progress is scored (rule 3)
#   file: fb_refit.py
#   find:             if fb_why.season_of(str(r.get("day") or r.get("commence") or "")[:10]) != season:
#   with:             if False:
#
# @vacuity a line only one model prices is not counted (rule 3)
#   file: fb_refit.py
#   find:     keys = sorted(k for k in set(a) & set(b) if a[k]["y"] == b[k]["y"])
#   with:     keys = sorted(k for k in set(a) | set(b) if k in a and k in b or True)
#
# @vacuity d is the champion's loss minus the challenger's (rule 3)
#   file: fb_refit.py
#   find:     return ([(loss(a[k]["p_model"], a[k]["y"]), loss(b[k]["p_model"], b[k]["y"]), a[k]["game"]) for k in keys],
#   with:     return ([(loss(b[k]["p_model"], b[k]["y"]), loss(a[k]["p_model"], a[k]["y"]), a[k]["game"]) for k in keys],
#
# @vacuity under 500 paired predictions is NOT YET MEASURABLE (rule 4)
#   file: fb_refit.py
#   find: PROPS_MIN = 500                      # ⛔ §3i rule 4: paired predictions in the league
#   with: PROPS_MIN = 50                       # ⛔ §3i rule 4: paired predictions in the league
#
# @vacuity the bar is one-sided p under 0.01 (rule 4)
#   file: fb_refit.py
#   find: PROPS_ALPHA = 0.01                   # ⛔ §3i rule 4: one-sided
#   with: PROPS_ALPHA = 0.05                   # ⛔ §3i rule 4: one-sided
#
# @vacuity a switched league tests nothing (rule 5)
#   file: fb_refit.py
#   find:     if CF.PROPS_SEASONS.get(lg) == CF.LAST_TWO:      # rule 5: the champion IS the challenger
#   with:     if False:
#
# @vacuity nothing counts before the Monday after the merge day (rule 6)
#   file: fb_refit.py
#   find:     return monday_on_or_after((datetime.date.fromisoformat(merged) + datetime.timedelta(days=1)).isoformat())
#   with:     return monday_on_or_after(merged)
#
# @vacuity the weekly job runs the contest
#   file: fb_refit.py
#   find:             ps = props_contest(lg, root, now, added)
#   with:             ps = {"verdict": "NOT RUN"}
#
# @vacuity a WINS pushes the switch branch
#   file: fb_refit.py
#   find:                 ps["branch"], ps["branch_pushed"] = push_props_branch(lg, now.strftime("%Y-%m-%d"), root, run)
#   with:                 ps["branch"], ps["branch_pushed"] = None, False
#
# @vacuity the branch switches only that league
#   file: fb_refit.py
#   find:     out, n = re.subn(r'(?m)^(PROPS_SEASONS = \{.*"%s": )"all"' % lg, r"\g<1>LAST_TWO", src)
#   with:     out, n = re.subn(r'(?m)^(PROPS_SEASONS = \{.*)"all"', r"\g<1>LAST_TWO", src)
#
# @vacuity the challenger rolls: the season in progress and the one before (rule 2)
#   file: fb_props_model.py
#   find:     return (cur - 1, cur)
#   with:     return (2025, 2026)
#
# @vacuity a switched league's live model trains on last season plus this one
#   file: fb_props_model.py
#   find:     if card_fb.PROPS_SEASONS.get(lg) == card_fb.LAST_TWO:
#   with:     if False:
#
# @vacuity the live build trains on the switch's logs
#   file: fb_props_model.py
#   find:     logs = train_logs(lg, root) if logs is None else logs
#   with:     logs = load_logs(lg, root) if logs is None else logs
#
# @vacuity the email gives the props contest's sentence
#   file: status.py
#   find:     ps = props_summary(doc)
#   with:     ps = None
#
# @vacuity a props WINS is under "Needs you"
#   file: status.py
#   find: refit_wins(doc, name) + props_wins(doc, name) + injury_branch(
#   with: refit_wins(doc, name) + injury_branch(
"""
import datetime
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.environ["LEAGUE"] = "nfl"
from tcheck import ck, eq, section  # noqa: E402

import card_fb as CF  # noqa: E402
import fb_props_model as PM  # noqa: E402
import fb_refit as R  # noqa: E402
import status as S  # noqa: E402

UTC = datetime.timezone.utc
NOW = datetime.datetime(2026, 11, 2, 10, 0, tzinfo=UTC)
TREES = []


def tree():
    t = tempfile.mkdtemp(prefix="props-seasons-")
    TREES.append(t)
    return t


def put(path, doc):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if path.endswith(".gz"):
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(doc, fh)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)


def row(game, player, p, y, day="2026-10-11", market="player_receptions", line=3.5):
    return {"game": game, "player": player, "market": market, "line": line, "p_model": p, "y": y, "day": day}


def wfs(n_games, per_game, champ_p, chal_p):
    """Two walk-forwards over the same lines: every line's outcome is 1, so the model whose P is
    nearer 1 has the lower log loss. Varied a little per game so the clustered test has spread."""
    a, b = [], []
    for g in range(n_games):
        for k in range(per_game):
            j = 0.02 * ((g * 7 + k * 3) % 5) - 0.04
            a.append(row("nfl:%d" % g, "P%d" % k, champ_p + j, 1))
            b.append(row("nfl:%d" % g, "P%d" % k, chal_p + j, 1))
    return {"champion": {"graded": a}, "challenger": {"graded": b}}


try:
    # ═══ 1. registration ═══════════════════════════════════════════════════════
    section("1. 🔴 it enters the contest the first Monday AFTER its merge day (rule 6)")
    eq([R.props_registration(added={"P2526": d}) for d in ("2026-10-27", "2026-11-01", "2026-11-02")],
       ["2026-11-02", "2026-11-02", "2026-11-09"],
       "a Tuesday or Sunday merge enters the next Monday; a Monday merge the Monday after (never that night)")
    G = tree()
    git = lambda *a, **e: subprocess.run(["git"] + list(a), cwd=G, capture_output=True, text=True,  # noqa: E731
                                         env=dict(os.environ, GIT_AUTHOR_DATE=e.get("d", ""),
                                                  GIT_COMMITTER_DATE=e.get("d", ""),
                                                  GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                                                  GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))
    git("init", "-q")
    open(os.path.join(G, "fb_refit.py"), "w").write("x = 1\n")
    git("add", "fb_refit.py")
    git("commit", "-qm", "base", d="2026-10-20T12:00:00")
    open(os.path.join(G, "fb_refit.py"), "a").write("\n%sl, root):\n    pass\n" % R.PROPS_MARK)
    git("commit", "-qam", "the contest", d="2026-10-28T12:00:00")
    eq(R.props_registration(G), "2026-11-02", "🔴 read from git: the day its line first reached the branch")
    eq(R.props_registration(tree()), None, "   ...and None with no git history (never guessed)")

    # ═══ 2. pairing ════════════════════════════════════════════════════════════
    section("2. 🔴 a prediction is one graded line both models price, this season only (rule 3)")
    A = {"graded": [row("g1", "a", 0.6, 1), row("g1", "a", 0.9, 0),       # a duplicate: the first stands
                    row("g1", "b", 0.5, 1), row("g2", "c", 0.7, 0, day="2025-11-30"),
                    row("g2", "d", 0.4, 1), row("g3", "e", None, 1), row("g3", "f", 0.5, None),
                    row("g4", "h", 0.55, 1, day="2027-01-03")]}                 # January: still 2026's season
    B = {"graded": [row("g1", "a", 0.8, 1), row("g1", "b", 0.5, 1), row("g2", "c", 0.6, 0, day="2025-11-30"),
                    row("g2", "d", 0.4, 0), row("g3", "e", 0.5, 1), row("g9", "z", 0.5, 1),
                    row("g4", "h", 0.65, 1, day="2027-01-03")]}
    pairs, only_a, only_b = R.props_pairs(A, B, 2026)
    eq([g for *_x, g in pairs], ["g1", "g1", "g4"],
       "only lines both price with the same result: 2025's line, an unpriced one, a void, a result "
       "that disagrees and a line only one model has are left out; January counts for the season")
    eq((only_a, only_b), (0, 2), "   ...and the lines only one model prices are counted on each side")
    eq(round(pairs[0][0] - pairs[0][1], 6), round(R.loss(0.6, 1) - R.loss(0.8, 1), 6),
       "🔴 d = the champion's loss minus the challenger's (positive: the challenger is better)")

    # ═══ 3. the bar ════════════════════════════════════════════════════════════
    section("3. 🔴 WINS at 500+ paired predictions, lower log loss, one-sided p < 0.01 (rule 4)")
    for what, w, want in (("clearly better over 600", wfs(150, 4, 0.55, 0.70), "WINS"),
                          ("clearly worse over 600", wfs(150, 4, 0.70, 0.55), "NOT YET"),
                          ("identical", wfs(150, 4, 0.6, 0.6), "NOT YET"),
                          ("better but only 496", wfs(124, 4, 0.55, 0.70), "NOT YET MEASURABLE")):
        got = R.props_contest("nfl", now=NOW, added={"P2526": "2026-10-27"}, wf=w)
        ck(got["verdict"] == want, "%s -> %s" % (what, want), got.get("counted"))
    eq([R.props_verdict(dict(predictions=600, mean_d=0.01, mean_d_exact=0.01, p=round(p, 6), p_exact=p))
        for p in (0.0099999, 0.01, 0.2)], ["WINS", "NOT YET", "NOT YET"],
       "🔴 p must be UNDER 0.01, on the unrounded number")

    # ═══ 4. the other verdicts ═════════════════════════════════════════════════
    section("4. 🔴 not yet registered, switched, no data; the challenger's seasons roll (rule 2)")
    w = wfs(150, 4, 0.55, 0.70)
    eq(R.props_contest("nfl", now=NOW, added={"P2526": "2026-11-02"}, wf=w)["verdict"], "NOT YET REGISTERED",
       "🔴 a contest merged on the Monday itself counts nothing that day")
    _saved = dict(CF.PROPS_SEASONS)
    try:
        CF.PROPS_SEASONS["nfl"] = CF.LAST_TWO
        got = R.props_contest("nfl", now=NOW, added={"P2526": "2026-10-27"}, wf=w)
        eq((got["verdict"], got["champion_seasons"]), ("SWITCHED", [2025, 2026]),
           "🔴 once Sam merged a switch, the champion IS the challenger: SWITCHED, nothing tested")
    finally:
        CF.PROPS_SEASONS.clear()
        CF.PROPS_SEASONS.update(_saved)
    T = tree()
    put(os.path.join(T, "data", "nfl", "latest", "players-2025.json.gz"), {"season": 2025, "players": {"1": {}}})
    got = R.props_contest("nfl", root=T, now=NOW, added={"P2526": "2026-10-27"})
    eq((got["verdict"], got.get("why")), ("NO DATA", "no stored player log for 2026"),
       "🔴 a missing season of the challenger's is NO DATA, never a smaller challenger")
    eq([PM.last_two(datetime.datetime(*d, tzinfo=UTC)) for d in ((2026, 11, 2), (2027, 1, 10), (2027, 9, 15))],
       [(2025, 2026), (2025, 2026), (2026, 2027)],
       "🔴 the challenger is the season in progress and the one before: 2025-26 now and in January, "
       "2026-27 next season")
    eq(R.props_contest("nfl", now=datetime.datetime(2027, 9, 15, 10, tzinfo=UTC), added={"P2526": "2026-10-27"},
                       wf=w)["challenger_seasons"], [2026, 2027], "   ...and the report says which")

    # ═══ 5. the switch: the live model and its branch ══════════════════════════
    section("5. 🔴 a switch makes the live model train on last season plus this one (rule 5)")
    L = tree()
    for s in range(2021, 2027):
        put(os.path.join(L, "data", "nfl", "latest", "players-%d.json.gz" % s), {"season": s, "players": {"1": {}}})
    eq(sorted(PM.train_logs("nfl", L, NOW)), list(range(2021, 2027)), "unswitched: every season in SEASONS")
    _seen, _wf = [], PM.walk_forward
    try:
        CF.PROPS_SEASONS["nfl"] = CF.LAST_TWO
        eq(sorted(PM.train_logs("nfl", L, NOW)), [2025, 2026], "🔴 switched: last season plus this one")

        def _stop(lg, root, logs):
            _seen.append(sorted(logs))
            raise RuntimeError("stop")
        PM.walk_forward = _stop
        try:
            PM.build("nfl", L, out=os.path.join(L, "x.json"))
        except RuntimeError:
            pass
        eq(_seen, [[2025, 2026]], "🔴 ...and the live build trains on those logs")
    finally:
        PM.walk_forward = _wf
        CF.PROPS_SEASONS.clear()
        CF.PROPS_SEASONS.update(_saved)
    eq((CF.props_suffix("nfl"), CF.METHOD_PROPS_MODEL), ("", "+props-own"), "unswitched: the method is unchanged")
    src = open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read()
    _lines = [x for x in R.set_props_seasons(src, "ncaaf").splitlines() if x.startswith("PROPS_SEASONS = ")]
    eq(_lines, ['PROPS_SEASONS = {"nfl": "all", "ncaaf": LAST_TWO}'],
       "🔴 the branch's one edit switches only the league that won")
    _cmds, _files = [], {}

    def _git(cmd, **k):
        _cmds.append(cmd[1])
        if cmd[1] == "ls-remote":
            return subprocess.CompletedProcess(cmd, 0, _remote[0], "")
        if cmd[1] == "worktree" and cmd[2] == "add":
            os.makedirs(cmd[-2])
            shutil.copy(os.path.join(ROOT, "card_fb.py"), cmd[-2])
        if cmd[1] == "-c":                                        # the commit
            _files["card_fb"] = open(os.path.join(k["cwd"], "card_fb.py"), encoding="utf-8").read()
        if cmd[1] == "push":
            _files["push"] = cmd[-1]
        return subprocess.CompletedProcess(cmd, 0, "", "")
    _remote = [""]
    got = R.push_props_branch("nfl", "2026-11-02", ROOT, run=_git)
    ck(got == ("fb/props-seasons-nfl-2026-11-02", True)
       and _files.get("push") == "fb/props-seasons-nfl-2026-11-02:refs/heads/fb/props-seasons-nfl-2026-11-02"
       and 'PROPS_SEASONS = {"nfl": LAST_TWO, "ncaaf": "all"}' in _files.get("card_fb", ""),
       "🔴 a WINS pushes ONE branch whose card_fb.py switches that league, never main", (got, _files.get("push")))
    _remote[0], _cmds[:] = "abc\trefs/heads/fb/props-seasons-nfl-2026-10-26\n", []
    eq((R.push_props_branch("nfl", "2026-11-02", ROOT, run=_git), _cmds),
       (("fb/props-seasons-nfl-2026-10-26", False), ["ls-remote"]),
       "   ...and none while an older one is on GitHub (it is named instead)")

    # ═══ 6. the weekly job ═════════════════════════════════════════════════════
    section("6. 🔴 the Monday job runs it, keeps an error beside last week's report, pushes on a WINS")
    import fb_inj_backtest as IB
    W = tree()
    os.makedirs(os.path.join(W, "data", "nfl", "latest"))
    put(os.path.join(W, "data", "ncaaf", "latest", "fb-refit.json"),
        {"league": "ncaaf", "props_seasons": {"verdict": "NOT YET", "season": 2026}})
    _league, _contest, _push, _auto = R.league, R.props_contest, R.push_props_branch, IB.auto
    try:
        R.league = lambda lg, root, now, prev=None, added=None: {"league": lg, "challengers": []}
        IB.auto = lambda *a, **k: {"state": "waiting"}

        def _pc(lg, root, now, added):
            if lg == "ncaaf":
                raise ValueError("planted")
            return {"name": "P2526", "verdict": "WINS"}
        R.props_contest = _pc
        R.push_props_branch = lambda lg, day, root, run: ("fb/props-seasons-%s-%s" % (lg, day), True)
        R.weekly(root=W, now=NOW, run=None)
    finally:
        R.league, R.props_contest, R.push_props_branch, IB.auto = _league, _contest, _push, _auto
    D = {lg: json.load(open(os.path.join(W, "data", lg, "latest", "fb-refit.json"), encoding="utf-8"))
         for lg in ("nfl", "ncaaf")}
    eq(D["nfl"].get("props_seasons"), {"name": "P2526", "verdict": "WINS", "branch": "fb/props-seasons-nfl-2026-11-02",
                                       "branch_pushed": True}, "🔴 a WINS is reported with its branch")
    eq(D["ncaaf"].get("props_seasons"), {"verdict": "NOT YET", "season": 2026, "error": "ValueError: planted"},
       "🔴 ...and a contest that fails keeps last week's report beside the error, never raises")

    # ═══ 7. the email ══════════════════════════════════════════════════════════
    section("7. 🔴 the Monday email says where it stands, and a WINS is under Needs you")
    base = {"challenger_seasons": [2025, 2026], "champion_seasons": [2021, 2022, 2023, 2024, 2025, 2026],
            "floor": 500, "alpha": 0.01}
    cnt = {"predictions": 5568, "games": 107, "p": 0.0031, "challenger_log_loss": 0.6012,
           "champion_log_loss": 0.6123}
    for v, extra, want in (
            ("NOT YET REGISTERED", {"registered": "2026-11-02"}, "it enters the contest on 2026-11-02."),
            ("NO DATA", {"why": "no stored player log for 2026"}, "its data is not stored yet (no stored player log for 2026)."),
            ("SWITCHED", {}, "switched: this league's props model trains on last season plus this one."),
            ("NOT YET MEASURABLE", {"counted": {"predictions": 320}}, "not yet measurable (320 of the 500 paired predictions it needs)."),
            ("NOT YET", {"counted": cnt}, "not better yet: log loss 0.6012 against 0.6123 over 5568 predictions in 107 games, one-sided p = 0.0031 (it needs under 0.01)."),
            ("WINS", {"counted": cnt}, "it WINS: log loss 0.6012 against 0.6123 over 5568 predictions in 107 games, one-sided p = 0.0031 (it needs under 0.01); the switch waits for you (Needs you).")):
        got = S.props_summary({"props_seasons": dict(base, verdict=v, **extra)})
        eq(got, "Props model trained on last season plus this one (2025-2026) against today's (2021-2026): " + want,
           "the email for %s" % v)
    ck(S.props_summary({"props_seasons": dict(base, error="ValueError: planted")}).endswith(
       "(2021-2026): the contest could not be run this week (ValueError: planted)."),
       "   ...and for a week it failed")
    eq(S.props_summary({"challengers": []}), None, "   ...and nothing before its first report")
    E = tree()
    put(os.path.join(E, "data", "latest", "health.json"), {"checked_at": "2026-11-02T09:00:00Z", "findings": []})
    put(os.path.join(E, "data", "nfl", "latest", "fb-refit.json"), {
        "league": "nfl", "built_at": "2026-11-02T10:05:00Z", "challengers": [],
        "props_seasons": dict(base, verdict="WINS", counted=cnt, branch="fb/props-seasons-nfl-2026-11-02")})
    body, needs = S.build(E, datetime.datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    ck("NFL props model trained on last season plus this one (2025-2026) beat today's (2021-2026)" in body
       and "compare/main...fb/props-seasons-nfl-2026-11-02" in body and needs,
       "🔴 a WINS is under Needs you with the branch to merge, click by click", body[:600])
    ck("it WINS: log loss 0.6012" in body, "   ...and the league's paragraph gives the contest's numbers")
finally:
    for t in TREES:
        shutil.rmtree(t, ignore_errors=True)
