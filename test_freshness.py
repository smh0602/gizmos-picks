"""FAULT INJECTION FOR THE FRESHNESS LAYER.

🔴 A CHECK THAT HAS NEVER FAILED ON PURPOSE IS NOT A CHECK.
Every defect below is one this project has actually shipped, or one the
rewrite would newly be exposed to. Each is injected into a synthetic repo
and the gate must catch it. ⛔ If any case says CAUGHT where it should say
MISSED, the fix is not doing what it claims.

Run:  python test_freshness.py        (exit 0 = every case behaved)

════════════════════════════════════════════════════════════════════════
🔴 `[2026-09-28]` THE CONTROL AND THE CASCADE HAD BEEN FAILING, AND THE
FILE STILL SAID "✅ all 5 checks passed".
════════════════════════════════════════════════════════════════════════
Cases 7-9 and the converge, workflow and midnight sections appended to a
local FAIL list that NOTHING gated (tcheck gates only `ck`). Run on
2026-09-28 it printed "[FALSE ALARM] control ... wrongly flagged:
[pitchers, record, runs]" and "[BROKEN] cascade" — and exited 0.
Three causes, all fixed together (any one alone turns the file red):
  1. `build()` wrote a hand list of files that went STALE when the MLB
     contract gained the pitcher tables, the drill-down and run status.
     ✅ It now writes every row `F.contract` returns for the tree it builds.
  2. The synthetic tree was judged against a row set read from the LIVE
     repo (`runs_writer_deployed()` reads the checked-out runs.yml): a
     synthetic tree and a live fact — never one of each. ✅ Pinned, and
     every case is driven in BOTH states of the run watcher.
  3. ✅ Every verdict goes through `ck`. The day-rollover case is PINNED to
     00:30Z (it used the real clock and only reached the rollover branch
     between 00:00Z and 04:30Z, about 19% of runs).

# @vacuity the CONTROL: a tree built inside every deadline flags nothing
#   file: freshness.py
#   find: stale = built is None or (due is not None and built < due)
#   with: stale = built is None or (due is not None and built <= now)
#
# @vacuity the CASCADE: a late props pull drags the join with it
#   file: freshness.py
#   find: "props-pitcher": ["props-board"],
#   with: "props-pitcher": [],
#
# @vacuity the DAY ROLLOVER: yesterday's snapshot directory is still read
#   file: freshness.py
#   find: dirs.append("/".join(y))
#   with: pass
#
# @vacuity converge runs the modes its plan names
#   file: collect.py
#   find: if not modes:
#   with: if True:
#
# @vacuity a failed HARD mode turns the converge run red
#   file: collect.py
#   find: return 1 if failed else 0
#   with: return 0
#
# @vacuity a failed SOFT mode does not
#   file: collect.py
#   find: return 1 if failed else 0
#   with: return 1
#
# @vacuity the published freshness report carries every field the page reads
#   file: collect.py
#   find: "artifacts": rows,
#   with: "artifacts": [{"mode": r["mode"]} for r in rows],
#
# @vacuity the workflow guards: the gate surveys the league it is asked about
#   file: verify_freshness.py
#   find: _DATA = "data" if _LEAGUE == "mlb" else f"data/{_LEAGUE}"
#   with: _DATA = "data"
#
# @vacuity the card is dated by its DEADLINE, never by a clock that rolls
#   file: freshness.py
#   find: ("card",     ("file", f"{picks}/{due_date(CARD, now)}.json"), CARD, False,
#   with: ("card",     ("file", f"{picks}/{slate_date(now)}.json"), CARD, False,
"""
import contextlib, datetime, gzip, io, json, os, re, shutil, sys, tempfile, time
import freshness as F
from tcheck import ck, note, shown   # the shared gate — see tcheck.py

UTC = datetime.timezone.utc
PASS, FAIL = [], []


@contextlib.contextmanager
def watcher(deployed):
    """Pin the run-status row: a synthetic tree is never judged against
    the checked-out repo's runs.yml (`runs_writer_deployed` reads it)."""
    live = F.runs_writer_deployed
    F.runs_writer_deployed = lambda root=None, _v=deployed: _v
    try:
        yield
    finally:
        F.runs_writer_deployed = live


def build(root, ages_min, no_stamp=(), corrupt=(), now=None):
    """A synthetic repo where each artifact is `ages_min` minutes old.

    ✅ THE FILES ARE THE CONTRACT'S. Every row `F.contract` returns for
    this tree at `now` is written: a `file` row at its path, stamped
    `ages_min[mode]` minutes old; a `dir` row as one snapshot in the
    directory for the UTC DAY IT WAS WRITTEN. ⛔ A hand list here went
    stale three times as the MLB contract grew, and the control case then
    flagged the rows nobody had added.
    """
    now = now or datetime.datetime.now(UTC)
    os.makedirs(f"{root}/data/latest", exist_ok=True)
    os.makedirs(f"{root}/picks", exist_ok=True)

    def ts(mode):
        return (now - datetime.timedelta(minutes=ages_min.get(mode, 0))
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

    def put(path, mode):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = {} if mode in no_stamp else {"pulled_at": ts(mode)}
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "wt") as fh:
            fh.write("{not json" if mode in corrupt else json.dumps(body))

    # 🔴 THE CARD IS DATED BY ITS DEADLINE, NOT BY THE WALL CLOCK, and the
    # results by the SLATE date: both come from the contract's own paths.
    # ⛔ This harness once wrote `picks/<et_date>.json` and therefore
    # ENCODED THE BUG IT WAS SUPPOSED TO CATCH -- inside the midnight-to-
    # 10am window it built the file the broken contract asked for, so the
    # control case passed while production went red every night.
    for mode, (kind, path), _t, _pd, _w in F.contract(
            data=f"{root}/data", picks=f"{root}/picks", now=now):
        if kind == "file":
            put(path, mode)
            continue
        # 🔴 A snapshot lands in the directory for the UTC DAY IT WAS
        # WRITTEN, so an artifact older than today belongs in an earlier
        # directory. Modelling that correctly is what exposed the
        # day-rollover bug in newest_age_minutes.
        when = now - datetime.timedelta(minutes=ages_min.get(mode, 0))
        d = os.path.join(os.path.dirname(os.path.dirname(path)),
                         when.strftime("%Y-%m-%d"), os.path.basename(path))
        os.makedirs(d, exist_ok=True)
        with gzip.open(f"{d}/{when.strftime('%H%M')}.json.gz", "wt") as fh:
            fh.write("{}")
    return root


def check(name, root, must_flag, mtime_now=True, now=None):
    """`must_flag` = set of modes the survey MUST report stale."""
    if mtime_now:
        # 🔴 SIMULATE A FRESH `git checkout`: every mtime becomes now.
        # This is the condition that defeated the old guard.
        for dp, _, fs in os.walk(root):
            for f in fs:
                os.utime(os.path.join(dp, f), None)
    rows = F.survey(data=f"{root}/data", picks=f"{root}/picks", now=now)
    stale = {r["mode"] for r in rows if r["stale"]}
    ok = must_flag <= stale
    (PASS if ok else FAIL).append(name)
    ck(name, ok,
       "" if ok else f"expected stale {sorted(must_flag)}, "
                     f"actually stale {sorted(stale)}")
    return rows


tmp = tempfile.mkdtemp()
try:
    print("FAULT INJECTION — each case must be CAUGHT\n")
    for _dep in (False, True):
        _w = " (run watcher %s)" % ("deployed" if _dep else "not deployed")
        with watcher(_dep):
            # 1 — the actual 2026-08-28 defect
            r = build(f"{tmp}/{_dep}f1", {"props-pitcher": 900, "props-batter": 900})
            check("props 15 hours old (the live defect)" + _w, r,
                  {"props-pitcher", "props-batter"})

            # 2 — the same, stated as the mechanism that hid it
            print("       ^ mtimes were reset to 'now' before every check above,")
            print("         which is exactly what defeated os.path.getmtime.\n")

            # 3 — the card missed its 10:00am build
            r = build(f"{tmp}/{_dep}f3", {"card": 24*60})
            check("card not rebuilt since yesterday (due 10:00am)" + _w, r, {"card"})

            # 4 — an artifact carrying NO timestamp must never read as fresh
            r = build(f"{tmp}/{_dep}f4", {}, no_stamp=("record",))
            check("artifact with no timestamp at all" + _w, r, {"record"})

            # 5 — a corrupt artifact must fail loudly, not crash or pass
            r = build(f"{tmp}/{_dep}f5", {}, corrupt=("board.json", "gamelines"))
            check("unreadable/corrupt artifact" + _w, r, {"gamelines"})

            # 6 — the track-record hole: results stale
            r = build(f"{tmp}/{_dep}f6", {"results": 5000, "scores": 5000})
            check("results + scores 3.5 days old (missed 6:00am)" + _w, r,
                  {"results", "scores"})

            # 7 — CONTROL: everything built since its deadline -> NOTHING flagged
            r = build(f"{tmp}/{_dep}f7", {})
            rows = F.survey(data=f"{r}/data", picks=f"{r}/picks")
            stale = {x["mode"] for x in rows if x["stale"]}
            (PASS if not stale else FAIL).append("control" + _w)
            ck("🔴 control: everything current reports NOTHING stale" + _w,
               not stale and len(rows) >= 16,
               "⛔ a false alarm here is a banner nobody can clear. wrongly "
               "flagged: %s; rows surveyed: %d" % (sorted(stale), len(rows)))

            # 8 — the cascade
            r = build(f"{tmp}/{_dep}f8", {"props-pitcher": 24*60})
            modes, _ = F.plan(data=f"{r}/data", picks=f"{r}/picks")
            (PASS if modes == ["props-pitcher", "props-board"] else FAIL).append(
                "cascade" + _w)
            ck("🔴 cascade: a late props pull drags the join with it — and "
               "NOT the card" + _w,
               modes == ["props-pitcher", "props-board"],
               "⛔ the 10am card is the 10am card, so the 4pm odds pull must "
               "not quietly rebuild it. plan -> %s" % modes)

            # 9 — THE DAY-ROLLOVER CASE, added after the suite caught it.
            #     At 00:30Z (8:30pm ET) yesterday's 4pm pull is 4.5h old and
            #     STILL SATISFIES the 4pm deadline. It must NOT be re-bought.
            # 🔴 `[2026-09-28]` PINNED TO 00:30Z. It used the real clock, so
            #    the snapshot only landed in YESTERDAY's directory when the
            #    suite ran between 00:00Z and 04:30Z; the rest of the day the
            #    rollover branch was never reached and the case passed on a
            #    broken rollover. The tree and the clock are pinned together.
            #    ⚠️ 265 minutes, not 270: the pull lands at 20:05Z (4:05pm
            #    ET), five minutes after the 4pm deadline rather than on it.
            roll = datetime.datetime(2026, 8, 31, 0, 30, tzinfo=UTC)
            r = build(f"{tmp}/{_dep}f10", {"props-pitcher": 265, "props-batter": 265},
                      now=roll)
            rows = F.survey(data=f"{r}/data", picks=f"{r}/picks", now=roll)
            pp = [x for x in rows if x["mode"] == "props-pitcher"][0]
            _yday = os.path.isdir(f"{r}/data/2026-08-30/props-pitcher") and \
                not os.path.isdir(f"{r}/data/2026-08-31/props-pitcher")
            (PASS if not pp["missing"] else FAIL).append("day rollover" + _w)
            ck("🔴 day rollover: a pull from the previous UTC day is still "
               "visible at 00:30Z" + _w,
               _yday and not pp["missing"] and not pp["stale"],
               "⛔ MISSING here re-buys a paid pull every night. snapshot only "
               "in yesterday's directory: %s; age %sm, missing %s, stale %s"
               % (_yday, pp["age_min"], pp["missing"], pp["stale"]))

            # 10 — a FUTURE timestamp (clock skew) must not read as infinitely
            #     fresh in a way that hides a real problem. Age floors at 0,
            #     which is the safe direction ONLY if the writer is
            #     trustworthy; recorded here so the behaviour is known rather
            #     than discovered.
            r = build(f"{tmp}/{_dep}f9", {"card": -600})
            rows = F.survey(data=f"{r}/data", picks=f"{r}/picks")
            card = [x for x in rows if x["mode"] == "card"][0]
            if _dep:
                print(f"\n  [KNOWN] a future timestamp reads as age "
                      f"{card['age_min']}m (floored at 0), i.e. FRESH.")
                print( "          ⚠️ Clock skew on the runner would therefore hide")
                print( "             staleness. Not a defect today (one writer, UTC),")
                print( "             but it is the blind spot of a content-based clock.")

finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{len(PASS)} behaved, {len(FAIL)} did not")
if FAIL:
    print("FAILED:", FAIL)


# ======================================================================
# WORKFLOW GUARD — added 2026-08-28 after the schedule rewrite silently
# deleted the `push:` trigger. ⛔ A workflow that no longer reacts to an
# upload is invisible: nothing errors, the run simply never happens.
# ======================================================================
def check_workflow():
    """⛔ NO YAML DEPENDENCY. The runner installs nothing beyond stdlib,
    and a guard that needs a package is a guard that gets skipped."""
    p = ".github/workflows/collect.yml"
    if not os.path.exists(p):
        p = "collect.yml"
    if not os.path.exists(p):
        print("  [SKIP] collect.yml not found next to this test")
        return True
    text = open(p).read()
    # the `on:` block runs until the next top-level key
    m = re.search(r"^on:\n(.*?)(?=^\S)", text, re.M | re.S)
    on = m.group(1) if m else ""
    ok = True
    for want in ("schedule", "push", "workflow_dispatch"):
        got = re.search(r"^  " + want + r":", on, re.M) is not None
        ok &= got
        print(f"  [{'OK  ' if got else 'GONE'}] workflow reacts to {want}")
    # 🔴 ~~five named files must appear in the push `paths:` allow-list~~
    # REPLACED 2026-09-04 AND THE REPLACEMENT IS STRICTLY HARDER. The old
    # check asked whether FIVE files were listed. `[measured]` **30 of the
    # 35 root code and test files were NOT** -- card_fb.py, cfb.py,
    # nfl.py, verify_board.py, verify_record.py, card_gate.py and EVERY
    # test file -- and the old check was green the whole time, because it
    # only ever asked about the five that were there.
    # ⛔ A CHECK THAT ENUMERATES WHAT IS PRESENT CANNOT SEE WHAT IS
    # MISSING. The new form enumerates the REPO instead of the list, so a
    # file added tomorrow is covered without anyone editing this test.
    pm = re.search(r"^  push:\n(.*?)(?=^  \S)", on, re.M | re.S)
    pushblk = pm.group(1) if pm else ""
    ign = re.findall(r'-\s*"([^"]+)"', pushblk)
    ck_has = "paths-ignore:" in pushblk
    print(f"  [{'OK  ' if ck_has else 'GONE'}] push uses an ignore-list, not an allow-list")
    ok &= ck_has

    def _ignored(path):
        """GitHub path-filter semantics for the shapes used here."""
        for g in ign:
            if g.endswith("/**") and path.startswith(g[:-2]):
                return True
            if g.startswith("**") and path.endswith(g[2:]):
                return True
            if g == path:
                return True
        return False

    import glob as _g
    _root = sorted(_g.glob("*.py") + _g.glob("*.js") + _g.glob("*.html"))
    _dead = [f for f in _root if _ignored(f)]
    print(f"  [{'OK  ' if not _dead else 'GONE'}] all {len(_root)} root code/test "
          f"files trigger a run", _dead[:4] if _dead else "")
    ok &= not _dead
    _wf = ".github/workflows/collect.yml"
    ok &= not _ignored(_wf)
    print(f"  [{'OK  ' if not _ignored(_wf) else 'GONE'}] and so does the workflow itself")
    # ⛔ AND THE LOOP GUARD MUST HOLD: the collector commits to data/ and
    # picks/ and nothing else. If those ever start triggering, every
    # converge commit starts another run.
    for _p in ("data/latest/board.json", "picks/2026-09-04.json"):
        _q = _ignored(_p)
        print(f"  [{'OK  ' if _q else 'LOOP!'}] a collector commit to {_p.split('/')[0]}/ "
              f"does NOT retrigger")
        ok &= _q
    # 🔴 MLB-ONLY STEPS MUST STAY BEHIND THE LEAGUE GUARD. Football
    # writes to data/nfl and picks/nfl; grading it against the MLB
    # contract is a bug in both directions -- a red football run for a
    # baseball reason, or a green one hiding real football staleness.
    # ~~verify_freshness.py was in this list~~ REMOVED 2026-09-04, AND
    # THE REPLACEMENT IS STRICTLY HARDER. The guard was a PROXY for
    # "football is never graded against baseball's deadlines". It bought
    # that by never running the gate for football at all -- which also
    # meant **football staleness was never checked by anything**, and a
    # gate that cannot fire is not a gate.
    # ✅ Football now has its own contract rows, so the gate runs for
    # every league and gets its league from `LEAGUE`, exactly as every
    # other tool here does. ⛔ The proxy is replaced by a check on the
    # THING IT WAS A PROXY FOR: that the gate actually surveys the league
    # it was asked about. A workflow guard could never prove that; this
    # can, and it would catch a `survey()` call that silently defaulted
    # back to MLB -- which the old check could not.
    for cmd in ("verify_card.py", "verify_board.py", "verify_record.py"):
        i = text.find("python " + cmd)
        seg = text[:i] if i > 0 else ""
        guarded = seg.rfind('LEAGUE_NAME" = "mlb"') > seg.rfind("\n            fi")
        print(f"  [{'OK  ' if guarded else 'LOOSE'}] {cmd} runs only for MLB")
        ok &= guarded
    import importlib as _il, os as _oe
    _prev = _oe.environ.get("LEAGUE")
    try:
        import verify_freshness as _vf
        for _lg, _want in (("ncaaf", "data/ncaaf"), ("nfl", "data/nfl"),
                           ("mlb", "data")):
            _oe.environ["LEAGUE"] = _lg
            _il.reload(_vf)
            _got = _vf._DATA == _want
            print(f"  [{'OK  ' if _got else 'WRONG'}] the gate surveys "
                  f"{_lg} at {_vf._DATA!r}")
            ok &= _got
    finally:
        if _prev is None:
            _oe.environ.pop("LEAGUE", None)
        else:
            _oe.environ["LEAGUE"] = _prev

    # 🔴 THE ACCEPTED-FAILURE GATE MUST STAY WIRED IN AND HONEST.
    # If `card_gate.py` stops being called, every card failure turns the
    # run red again; if `card-accepted.txt` goes missing, an accepted
    # failure silently becomes unaccepted. Neither shows up as an error.
    for need, why in (("card_gate.py", "the accepted-failure gate is called"),
                      ("verify_card.py", "the card is still verified")):
        got = need in text
        print(f"  [{'OK  ' if got else 'GONE'}] {why}")
        ok &= got
    import os as _os
    got = _os.path.exists("card-accepted.txt")
    print(f"  [{'OK  ' if got else 'GONE'}] card-accepted.txt exists")
    ok &= got

    # every cron must map to something the runner understands
    crons = re.findall(r'- cron: "([^"]+)"', on)
    print(f"  [{'OK  ' if crons else 'GONE'}] {len(crons)} cron entries present")
    ok &= bool(crons)
    return ok


# ======================================================================
# CONVERGE END-TO-END — added 2026-08-28 after a KeyError shipped.
# ======================================================================
# 🔴 THE BUG THIS EXISTS TO CATCH. The contract was rewritten from
# "max age" to "due time", and `converge()`'s own survey printout still
# referenced `r['max_age_min']`. Every test passed -- because every test
# called `survey()` and `plan()` DIRECTLY and none of them ever ran
# `converge`. On the runner it raised KeyError on the third line of every
# job, so nothing collected at all.
# ⛔ TESTING THE PARTS IS NOT TESTING THE THING. This runs the real
# converge with only the network stubbed out.
def check_converge():
    import importlib
    os.environ.setdefault("ODDS_API_KEY", "test")
    # 🔴 PINNED TO MLB, AND THE REASON MATTERS. `converge` is an MLB-only
    # concept -- `collect.main()` sends every other league down the
    # `converge-off` path -- but this test imports `collect`, which reads
    # LEAGUE from the environment AT IMPORT. On a football dispatch the
    # runner has LEAGUE=nfl, so `collect` pointed at `data/nfl/latest`
    # while this test looked for the report under `data/latest`, and the
    # whole suite failed with FileNotFoundError.
    # ⛔ THAT WAS THE TEST BEING WRONG, NOT THE COLLECTOR: `write()`
    # creates its own directories and production never calls converge for
    # a non-MLB league. **A suite that fails on a correct run is worse
    # than no suite — it teaches you to ignore red.**
    os.environ["LEAGUE"] = "mlb"
    root = tempfile.mkdtemp()
    cwd = os.getcwd()
    ok = True
    # 🔴 `[2026-09-28]` PINNED, AND GATED. The tree is synthetic, so the
    #    run-status row is pinned rather than read off the checked-out
    #    runs.yml, and every verdict below is a `ck` — before this they
    #    only printed, and a FAIL list nothing read carried the result.
    with watcher(True):
        # ⛔ a SOFT mode is what `soft_fail` below makes fail, and its
        #    artifact must be stale for converge to run it at all.
        build(f"{root}/x", {"props-pitcher": 900, "card": 24 * 60,
                            "news": 24 * 60})
        try:
            os.chdir(f"{root}/x")
            import collect
            importlib.reload(collect)
            ran = []
            collect.run_mode = lambda m: ran.append(m)
            collect.daily_spend = lambda: 0

            def converge():
                # ⚠️ CAPTURED, THEN PRINTED THROUGH `shown()`. converge writes
                #    `::error::` for a failed mode, and printed raw from here
                #    that was an ERROR annotation on every collect run
                #    `[2026-09-26]` (tcheck's watcher now fails the file).
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    c = collect.converge()
                print(shown(buf.getvalue()), end="")
                return c
            code = converge()          # 🔴 the real thing
            ok &= ck("converge ran the modes its plan names",
                     "props-pitcher" in ran and "card" in ran,
                     "ran %s and returned %s" % (ran, code))

            # a HARD mode failing must turn the run red
            def hard_fail(m):
                if m == "card":
                    raise RuntimeError("card blew up")
            collect.run_mode = hard_fail
            code = converge()
            ok &= ck("🔴 a failed CARD returns non-zero — the run goes red",
                     bool(code), "returned %s" % code)

            # a SOFT mode failing must not
            _soft = []

            def soft_fail(m):
                if m in ("news", "weather", "lineups"):
                    _soft.append(m)
                    raise RuntimeError("feed down")
            collect.run_mode = soft_fail
            code = converge()
            ok &= ck("⛔ a failed NEWS returns zero — headlines are not worth "
                     "a red run", "news" in _soft and not code,
                     "soft modes that failed: %s; returned %s" % (_soft, code))

            # the published report must carry every field the page reads
            # [Sam, 2026-10-01] the page has no stale bar now and reads only
            # `built_at`. This is a DATA check and stands unchanged: the
            # report keeps every field (CLAUDE.md), and the watchdog reads
            # `mode` and `stale` off these same rows.
            rep = json.load(open("data/latest/freshness.json"))
            need = {"mode", "stale", "missing", "late_min", "due_et", "age_min"}
            miss = need - set(rep["artifacts"][0])
            ok &= ck("freshness.json carries every field the banner reads",
                     not miss, "missing %s" % sorted(miss))
        except Exception as e:
            ok &= ck("converge ran without raising", False,
                     "%s: %s" % (type(e).__name__, e))
        finally:
            os.chdir(cwd)
            shutil.rmtree(root, ignore_errors=True)
    return ok


print("\nCONVERGE, END TO END")
if not check_converge():
    print("  ⛔ converge itself is broken — nothing would collect")
    FAIL.append("converge")

print("\nWORKFLOW TRIGGERS")
_wf_ok = check_workflow()
ck("🔴 the workflow still reacts to uploads and schedules, and every guard "
   "above holds", _wf_ok,
   "⛔ a missing trigger is invisible: nothing errors, the run simply never "
   "happens. See the [GONE]/[LOOSE]/[WRONG] lines above.")
if not _wf_ok:
    FAIL.append("workflow triggers")

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE DATE-ROLL WINDOW. A date bug is invisible unless you are standing
# inside its window, so this test STANDS INSIDE IT ON PURPOSE rather than
# trusting the wall clock to be in the right place when CI happens to run.
# `[measured 2026-08-30 06:58Z]` the card row built its FILENAME from
# et_date and its DEADLINE from last_due. Between midnight and 10am ET
# those disagree, so the contract demanded a card that was not due for
# another seven hours and reported the site out of contract. THE RUN WENT
# RED EVERY NIGHT. The identical bug had already been found and fixed for
# `results` on 2026-08-29 and the fix was never carried to `card`.
# ══════════════════════════════════════════════════════════════════════
print("\nTHE MIDNIGHT-TO-10AM WINDOW")
_UTC = datetime.timezone.utc
_win = [
    ("2026-08-30T03:00:00", "2026-08-29", "11pm ET — still last night's slate"),
    ("2026-08-30T06:58:00", "2026-08-29", "2:58am ET — the hour it actually failed"),
    ("2026-08-30T13:00:00", "2026-08-29", "9am ET — today's card is not due yet"),
    ("2026-08-30T15:00:00", "2026-08-30", "11am ET — now today's card IS due"),
]
_bad = 0
for _t, _want, _why in _win:
    _n = datetime.datetime.fromisoformat(_t).replace(tzinfo=_UTC)
    _row = [r for r in F.contract(now=_n) if r[0] == "card"][0]
    _got = _row[1][1].rsplit("/", 1)[-1].replace(".json", "")
    _ok = _got == _want
    print(f"  [{'OK  ' if _ok else 'FAIL'}] {_why}: card -> {_got}")
    if not _ok:
        _bad += 1
        print(f"         expected {_want}; a card is dated by its DEADLINE, "
              f"never by the wall clock")
ck("🔴 the card is dated by its DEADLINE across the midnight-to-10am window",
   not _bad, "%d of %d instants filed the card under the wrong day (the run "
   "went red every night the last time)" % (_bad, len(_win)))
if _bad:
    FAIL.append("card date rolls with the clock instead of the deadline")

# ⛔ AND THE GENERAL RULE, ENFORCED RATHER THAN TRUSTED: no date-stamped
# path in the contract may move while its own deadline has not.
_a = F.contract(now=datetime.datetime.fromisoformat(
    "2026-08-30T06:58:00").replace(tzinfo=_UTC))
_b = F.contract(now=datetime.datetime.fromisoformat(
    "2026-08-30T13:00:00").replace(tzinfo=_UTC))
_moved = [x[0] for x, y in zip(_a, _b)
          if x[1][1] != y[1][1] and F.last_due(x[2], datetime.datetime
          .fromisoformat("2026-08-30T06:58:00").replace(tzinfo=_UTC))
          == F.last_due(y[2], datetime.datetime
          .fromisoformat("2026-08-30T13:00:00").replace(tzinfo=_UTC))]
print(f"  [{'OK  ' if not _moved else 'FAIL'}] no artifact path moves while "
      f"its deadline has not{'' if not _moved else ': ' + str(_moved)}")
ck("⛔ no artifact path moves while its own deadline has not",
   not _moved and len(_a) == len(_b) >= 16,
   "moved: %s (%d/%d rows compared)" % (_moved, len(_a), len(_b)))
if _moved:
    FAIL.append(f"paths move without their deadline: {_moved}")

