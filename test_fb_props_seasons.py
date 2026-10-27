#!/usr/bin/env python3
r"""test_fb_props_seasons.py — §3i T74: the props model on last season plus this one.

`[Sam, 2026-10-27]` *"set up the monday contest to train it on 25-26"*, then, shown the six
rules (research/fb_refit_spec.md §3i), *"build as written"*. Every check runs on planted data:
no walk-forward of the stored logs, no stored report, nothing read from production.
⛔ The switch's state is SET here, never read: the branch a WINS pushes flips the live
`card_fb.PROPS_SEASONS`, and this file must pass on that branch too (test_props_switch_branch.py).

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
#   with: PROPS_MIN = 499                      # ⛔ §3i rule 4: paired predictions in the league
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
# @vacuity a season the champion has no log of is NO DATA, never "0 of the 500"
#   file: fb_refit.py
#   find:     if season not in PM.SEASONS:
#   with:     if False:
#
# @vacuity the champion trains on every season, the challenger on the last two (rules 1, 2)
#   file: fb_refit.py
#   find:         wf = {"challenger": PM.walk_forward(lg, root, logs), "champion": PM.walk_forward(lg, root, PM.load_logs(lg, root))}
#   with:         wf = {"champion": PM.walk_forward(lg, root, logs), "challenger": PM.walk_forward(lg, root, PM.load_logs(lg, root))}
#
# @vacuity nothing counts before the Monday after the merge day (rule 6)
#   file: fb_refit.py
#   find:     return monday_on_or_after((datetime.date.fromisoformat(merged) + datetime.timedelta(days=1)).isoformat())
#   with:     return monday_on_or_after(merged)
#
# @vacuity the merge day is the day it reached main, not the day it was written (rule 6)
#   file: fb_refit.py
#   find:         r = subprocess.run(["git", "log", "--first-parent", "--format=%cs", "-S", PROPS_MARK, "--", "fb_refit.py"],
#   with:         r = subprocess.run(["git", "log", "--format=%cs", "-S", PROPS_MARK, "--", "fb_refit.py"],
#
# @vacuity the weekly job runs the contest
#   file: fb_refit.py
#   find:             ps = props_contest(lg, root, now, added)
#   with:             ps = {"verdict": "NOT RUN"}
#
# @vacuity a WINS pushes the switch branch
#   file: fb_refit.py
#   find:                     ps["branch"], ps["branch_pushed"] = push_props_branch(lg, now.strftime("%Y-%m-%d"), root, run)
#   with:                     ps["branch"], ps["branch_pushed"] = None, False
#
# @vacuity a WINS whose push fails is still a WINS
#   file: fb_refit.py
#   find:                     ps["branch_error"] = "%s: %s" % (type(e).__name__, e)
#   with:                     raise
#
# @vacuity the branch switches only that league
#   file: fb_refit.py
#   find:     out, n = re.subn(r'(?m)^(    "%s": )"all",(?=\r?$)' % lg, r"\g<1>LAST_TWO,", src)
#   with:     out, n = re.subn(r'(?m)^(    "(?:nfl|ncaaf)": )"all",(?=\r?$)', r"\g<1>LAST_TWO,", src)
#
# @vacuity one branch per league: another league's branch blocks nothing
#   file: fb_refit.py
#   find:     return push_change("fb/props-seasons-%s-" % lg, "fb/props-seasons-%s-%s" % (lg, day), edit,
#   with:     return push_change("fb/props-seasons-", "fb/props-seasons-%s-%s" % (lg, day), edit,
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
#   find:     logs = train_logs(lg, root, now) if logs is None else logs
#   with:     logs = load_logs(lg, root) if logs is None else logs
#
# ⚠️ The two leagues' switch lines kept apart (so both branches merge, §6) cannot be declared as
#    a one-line mutation: putting them back side by side was checked by hand (the merge conflicts).
#
# @vacuity the email gives the props contest's sentence
#   file: status.py
#   find:     ps = props_summary(doc)
#   with:     ps = None
#
# @vacuity a props WINS is under "Needs you"
#   file: status.py
#   find:     won = [w for name, d, doc in refit for w in refit_wins(doc, name) + props_wins(
#   with:     won = [w for name, d, doc in refit for w in refit_wins(doc, name) + 0 * props_wins(
#
# @vacuity ...never once main holds the switch
#   file: status.py
#   find:     if ps.get("verdict") != "WINS" or switched:
#   with:     if ps.get("verdict") != "WINS":
"""
import datetime
import gzip
import json
import os
import re
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
ORIG = dict(CF.PROPS_SEASONS)
# ⛔ the switch is SET, never read: this file runs on the branch a WINS pushes too
CF.PROPS_SEASONS.update(nfl="all", ncaaf="all")  # SET, never read
UNSWITCHED =re.sub(r'(?m)^(    "(?:nfl|ncaaf)": )LAST_TWO,', r'\g<1>"all",',
                    open(os.path.join(ROOT, "card_fb.py"), encoding="utf-8").read())


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


def gitrepo():
    g = tree()

    def git(*a, d="2026-10-20T12:00:00"):
        return subprocess.run(["git"] + list(a), cwd=g, capture_output=True, text=True,
                              env=dict(os.environ, GIT_AUTHOR_DATE=d, GIT_COMMITTER_DATE=d,
                                       GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))
    git("init", "-q", "-b", "main")
    git("config", "core.autocrlf", "false")
    return g, git


try:
    # ═══ 1. registration ═══════════════════════════════════════════════════════
    section("1. 🔴 it enters the contest the first Monday AFTER its merge day (rule 6)")
    eq([R.props_registration(added={"P2526": d}) for d in ("2026-10-27", "2026-11-01", "2026-11-02")],
       ["2026-11-02", "2026-11-02", "2026-11-09"],
       "a Tuesday or Sunday merge enters the next Monday; a Monday merge the Monday after (never that night)")
    G, git = gitrepo()
    open(os.path.join(G, "fb_refit.py"), "w").write("x = 1\n")
    git("add", "fb_refit.py")
    git("commit", "-qm", "base")
    git("checkout", "-qb", "feature")
    open(os.path.join(G, "fb_refit.py"), "a").write("\n%sl, root):\n    pass\n" % R.PROPS_MARK)
    git("commit", "-qam", "the contest, written on a Tuesday", d="2026-10-20T13:00:00")
    git("checkout", "-q", "main")
    git("merge", "-q", "--no-ff", "-m", "merged a week later", "feature", d="2026-10-28T12:00:00")
    eq(R.props_registration(G), "2026-11-02",
       "🔴 read from git on main's own line: the MERGE day (10-28), not the day it was written (10-20)")
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
                          ("clearly better at exactly 500", wfs(125, 4, 0.55, 0.70), "WINS"),
                          ("better but only 496", wfs(124, 4, 0.55, 0.70), "NOT YET MEASURABLE")):
        got = R.props_contest("nfl", now=NOW, added={"P2526": "2026-10-27"}, wf=w)
        ck(got["verdict"] == want, "%s -> %s" % (what, want), got.get("counted"))
    eq([R.props_verdict(dict(predictions=n, mean_d=0.01, mean_d_exact=0.01, p=0.001, p_exact=0.001))
        for n in (499, 500)], ["NOT YET MEASURABLE", "WINS"], "🔴 the floor is 500: 499 is not enough, 500 is")
    eq([R.props_verdict(dict(predictions=600, mean_d=0.01, mean_d_exact=0.01, p=round(p, 6), p_exact=p))
        for p in (0.0099999, 0.01, 0.2)], ["WINS", "NOT YET", "NOT YET"],
       "🔴 p must be UNDER 0.01, on the unrounded number")

    # ═══ 4. the real path: which logs each model trains on ═════════════════════
    section("4. 🔴 the champion trains on every season, the challenger on the last two (rules 1, 2)")
    L = tree()
    for s in range(2021, 2027):
        put(os.path.join(L, "data", "nfl", "latest", "players-%d.json.gz" % s), {"season": s, "players": {"1": {}}})
    _seen, _wf = [], PM.walk_forward
    W2 = wfs(150, 4, 0.55, 0.70)

    def _walk(lg, root, logs):
        _seen.append(sorted(logs))
        return W2["challenger"] if sorted(logs) == [2025, 2026] else W2["champion"]
    try:
        PM.walk_forward = _walk
        got = R.props_contest("nfl", root=L, now=NOW, added={"P2526": "2026-10-27"})
    finally:
        PM.walk_forward = _wf
    eq(sorted(_seen), [[2021, 2022, 2023, 2024, 2025, 2026], [2025, 2026]],
       "🔴 run for real, the champion's walk-forward reads every stored season and the challenger's 2025-26")
    ck(got["verdict"] == "WINS" and got["counted"]["mean_d"] > 0,
       "🔴 ...and each result is scored as its own model's (the better one here is the challenger)", got.get("counted"))

    # ═══ 5. the other verdicts ═════════════════════════════════════════════════
    section("5. 🔴 not yet registered, switched, no data; the challenger's seasons roll (rule 2)")
    w = wfs(150, 4, 0.55, 0.70)
    eq(R.props_contest("nfl", now=NOW, added={"P2526": "2026-11-02"}, wf=w)["verdict"], "NOT YET REGISTERED",
       "🔴 a contest merged on the Monday itself counts nothing that day")
    try:
        CF.PROPS_SEASONS["nfl"] = CF.LAST_TWO
        got = R.props_contest("nfl", now=NOW, added={"P2526": "2026-10-27"}, wf=w)
        eq((got["verdict"], got["champion_seasons"]), ("SWITCHED", [2025, 2026]),
           "🔴 once Sam merged a switch, the champion IS the challenger: SWITCHED, nothing tested")
    finally:
        CF.PROPS_SEASONS.update(nfl="all", ncaaf="all")
    T = tree()
    put(os.path.join(T, "data", "nfl", "latest", "players-2025.json.gz"), {"season": 2025, "players": {"1": {}}})
    got = R.props_contest("nfl", root=T, now=NOW, added={"P2526": "2026-10-27"})
    eq((got["verdict"], got.get("why")), ("NO DATA", "no stored player log for 2026"),
       "🔴 a missing season of the challenger's is NO DATA, never a smaller challenger")
    got = R.props_contest("nfl", now=datetime.datetime(2027, 9, 15, 10, tzinfo=UTC), added={"P2526": "2026-10-27"}, wf=w)
    eq((got["verdict"], got["challenger_seasons"], got.get("why")),
       ("NO DATA", [2026, 2027], "the champion's seasons (fb_props_model.SEASONS) stop at 2026"),
       "🔴 in 2027 the champion reads no 2027 log (SEASONS ends at 2026): said, never '0 of the 500'")
    eq([PM.last_two(datetime.datetime(*d, tzinfo=UTC)) for d in ((2026, 11, 2), (2027, 1, 10), (2027, 9, 15))],
       [(2025, 2026), (2025, 2026), (2026, 2027)],
       "🔴 the challenger is the season in progress and the one before: 2025-26 now and in January, "
       "2026-27 next season")

    # ═══ 6. the switch: the live model and its branch ══════════════════════════
    section("6. 🔴 a switch makes the live model train on last season plus this one (rule 5)")
    eq(sorted(PM.train_logs("nfl", L, NOW)), list(range(2021, 2027)), "unswitched: every season in SEASONS")
    _seen = []
    try:
        CF.PROPS_SEASONS["nfl"] = CF.LAST_TWO
        eq(sorted(PM.train_logs("nfl", L, NOW)), [2025, 2026], "🔴 switched: last season plus this one")

        def _stop(lg, root, logs):
            _seen.append(sorted(logs))
            raise RuntimeError("stop")
        PM.walk_forward = _stop
        try:
            PM.build("nfl", L, out=os.path.join(L, "x.json"), now=NOW)
        except RuntimeError:
            pass
        eq(_seen, [[2025, 2026]], "🔴 ...and the live build trains on those logs")
    finally:
        PM.walk_forward = _wf
        CF.PROPS_SEASONS.update(nfl="all", ncaaf="all")
    eq((CF.props_suffix("nfl"), CF.METHOD_PROPS_MODEL), ("", "+props-own"), "unswitched: the method is unchanged")
    _block = lambda t: re.search(r"(?ms)^PROPS_SEASONS = \{.*?^\}", t).group(0)  # noqa: E731
    eq(_block(R.set_props_seasons(UNSWITCHED, "ncaaf")),
       'PROPS_SEASONS = {\n    "nfl": "all",\n    # (the line between)\n    "ncaaf": LAST_TWO,\n}',
       "🔴 the branch's one edit switches only the league that won")
    G2, git2 = gitrepo()
    open(os.path.join(G2, "card_fb.py"), "w", encoding="utf-8", newline="").write(UNSWITCHED)
    git2("add", "card_fb.py")
    git2("commit", "-qm", "base")
    for lg in ("nfl", "ncaaf"):
        git2("checkout", "-qb", lg, "main")
        open(os.path.join(G2, "card_fb.py"), "w", encoding="utf-8", newline="").write(
            R.set_props_seasons(UNSWITCHED, lg))
        git2("commit", "-qam", lg)
    git2("checkout", "-q", "nfl")
    m = git2("merge", "-q", "--no-edit", "ncaaf")
    eq((m.returncode, _block(open(os.path.join(G2, "card_fb.py"), encoding="utf-8").read())),
       (0, 'PROPS_SEASONS = {\n    "nfl": LAST_TWO,\n    # (the line between)\n    "ncaaf": LAST_TWO,\n}'),
       "🔴 both leagues' switch branches merge, one after the other, without a conflict")
    _cmds, _files = [], {}

    def _git(cmd, **k):
        _cmds.append(cmd[1])
        if cmd[1] == "ls-remote":
            want = cmd[-1].replace("refs/heads/", "").rstrip("*")
            return subprocess.CompletedProcess(cmd, 0, "".join(
                "abc\trefs/heads/%s\n" % b for b in _remote if b.startswith(want)), "")
        if cmd[1] == "worktree" and cmd[2] == "add":
            os.makedirs(cmd[-2])
            open(os.path.join(cmd[-2], "card_fb.py"), "w", encoding="utf-8", newline="").write(UNSWITCHED)
        if cmd[1] == "-c":                                        # the commit
            _files["card_fb"] = open(os.path.join(k["cwd"], "card_fb.py"), encoding="utf-8").read()
        if cmd[1] == "push":
            _files["push"] = cmd[-1]
        return subprocess.CompletedProcess(cmd, 0, "", "")
    _remote = ["fb/props-seasons-ncaaf-2026-10-26"]
    got = R.push_props_branch("nfl", "2026-11-02", ROOT, run=_git)
    ck(got == ("fb/props-seasons-nfl-2026-11-02", True)
       and _files.get("push") == "fb/props-seasons-nfl-2026-11-02:refs/heads/fb/props-seasons-nfl-2026-11-02"
       and '    "nfl": LAST_TWO,' in _files.get("card_fb", ""),
       "🔴 a WINS pushes ONE branch whose card_fb.py switches that league, never main (another league's "
       "branch on GitHub blocks nothing)", (got, _files.get("push")))
    _remote[:], _cmds[:] = ["fb/props-seasons-nfl-2026-10-26"], []
    eq((R.push_props_branch("nfl", "2026-11-02", ROOT, run=_git), _cmds),
       (("fb/props-seasons-nfl-2026-10-26", False), ["ls-remote"]),
       "   ...and none while the league's own older one is on GitHub (it is named instead)")

    # ═══ 7. the weekly job ═════════════════════════════════════════════════════
    section("7. 🔴 the Monday job runs it, keeps an error beside last week's report, pushes on a WINS")
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
        D = {lg: json.load(open(os.path.join(W, "data", lg, "latest", "fb-refit.json"), encoding="utf-8"))
             for lg in ("nfl", "ncaaf")}

        def _nopush(lg, day, root, run):
            raise RuntimeError("git push failed")
        R.push_props_branch = _nopush
        R.weekly(root=W, now=NOW, run=None)
        D2 = json.load(open(os.path.join(W, "data", "nfl", "latest", "fb-refit.json"), encoding="utf-8"))
    finally:
        R.league, R.props_contest, R.push_props_branch, IB.auto = _league, _contest, _push, _auto
    eq(D["nfl"].get("props_seasons"), {"name": "P2526", "verdict": "WINS", "branch": "fb/props-seasons-nfl-2026-11-02",
                                       "branch_pushed": True}, "🔴 a WINS is reported with its branch")
    eq(D["ncaaf"].get("props_seasons"), {"verdict": "NOT YET", "season": 2026, "error": "ValueError: planted"},
       "🔴 ...and a contest that fails keeps last week's report beside the error, never raises")
    eq(D2.get("props_seasons"), {"name": "P2526", "verdict": "WINS", "branch": None, "branch_pushed": False,
                                 "branch_error": "RuntimeError: git push failed"},
       "🔴 ...and a WINS whose push fails stays a WINS, with the push's error beside it")

    # ═══ 8. the email ══════════════════════════════════════════════════════════
    section("8. 🔴 the Monday email says where it stands, and a WINS is under Needs you")
    base = {"challenger_seasons": [2025, 2026], "champion_seasons": [2021, 2022, 2023, 2024, 2025, 2026],
            "floor": 500, "alpha": 0.01}
    cnt = {"predictions": 5568, "games": 107, "p": 0.0031, "challenger_log_loss": 0.6012,
           "champion_log_loss": 0.6123}
    nums = "log loss 0.6012 against 0.6123 over 5568 predictions in 107 games, one-sided p = 0.0031 (it needs under 0.01)"
    for v, extra, want in (
            ("NOT YET REGISTERED", {"registered": "2026-11-02"}, "it enters the contest on 2026-11-02."),
            ("NO DATA", {"why": "no stored player log for 2026"}, "its data is not stored yet (no stored player log for 2026)."),
            ("SWITCHED", {}, "switched: this league's props model trains on last season plus this one."),
            ("NOT YET MEASURABLE", {"counted": {"predictions": 320}}, "not yet measurable (320 of the 500 paired predictions it needs)."),
            ("NOT YET", {"counted": cnt}, "not better yet: " + nums + "."),
            ("WINS", {"counted": cnt, "branch": "fb/props-seasons-nfl-2026-11-02"},
             "it WINS: " + nums + "; the switch waits for you (Needs you)."),
            ("WINS", {"counted": cnt, "branch": None, "branch_error": "RuntimeError: git push failed"},
             "it WINS: " + nums + "; no branch was pushed (RuntimeError: git push failed).")):
        got = S.props_summary({"props_seasons": dict(base, verdict=v, **extra)})
        eq(got, "Props model trained on last season plus this one (2025-2026) against today's (2021-2026): " + want,
           "the email for %s%s" % (v, " with no branch" if "branch_error" in extra else ""))
    ck(S.props_summary({"props_seasons": dict(base, error="ValueError: planted")}).endswith(
       "(2021-2026): the contest could not be run this week (ValueError: planted)."),
       "   ...and for a week it failed")
    eq(S.props_summary({"challengers": []}), None, "   ...and nothing before its first report")
    E = tree()
    put(os.path.join(E, "data", "latest", "health.json"), {"checked_at": "2026-11-02T09:00:00Z", "findings": []})
    WIN = dict(base, verdict="WINS", counted=cnt, branch="fb/props-seasons-nfl-2026-11-02")
    put(os.path.join(E, "data", "nfl", "latest", "fb-refit.json"), {
        "league": "nfl", "built_at": "2026-11-02T10:05:00Z", "challengers": [], "props_seasons": WIN})
    open(os.path.join(E, "card_fb.py"), "w", encoding="utf-8").write(UNSWITCHED)
    body, needs = S.build(E, datetime.datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    ck("NFL props model trained on last season plus this one (2025-2026) beat today's (2021-2026)" in body
       and "compare/main...fb/props-seasons-nfl-2026-11-02" in body and needs,
       "🔴 a WINS is under Needs you with the branch to merge, click by click", body[:600])
    ck("it WINS: log loss 0.6012" in body, "   ...and the league's paragraph gives the contest's numbers")
    put(os.path.join(E, "data", "nfl", "latest", "fb-refit.json"), {
        "league": "nfl", "built_at": "2026-11-02T10:05:00Z", "challengers": [],
        "props_seasons": dict(WIN, error="ValueError: planted")})
    body, needs = S.build(E, datetime.datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    ck("compare/main...fb/props-seasons-nfl-2026-11-02" in body and "it won before" in body,
       "🔴 a week the contest fails keeps last week's win, and its branch, under Needs you", body[:400])
    open(os.path.join(E, "card_fb.py"), "w", encoding="utf-8").write(R.set_props_seasons(UNSWITCHED, "nfl"))
    body, needs = S.build(E, datetime.datetime(2026, 11, 2, 12, 0, tzinfo=UTC))
    ck("props-seasons-nfl" not in body.split("## Records")[0],
       "🔴 once main holds the switch (Sam merged it), Needs you stops asking", body[:400])
finally:
    CF.PROPS_SEASONS.clear()
    CF.PROPS_SEASONS.update(ORIG)
    for t in TREES:
        shutil.rmtree(t, ignore_errors=True)
