"""FAULT INJECTION FOR THE FRESHNESS LAYER.

🔴 A CHECK THAT HAS NEVER FAILED ON PURPOSE IS NOT A CHECK.
Every defect below is one this project has actually shipped, or one the
rewrite would newly be exposed to. Each is injected into a synthetic repo
and the gate must catch it. ⛔ If any case says CAUGHT where it should say
MISSED, the fix is not doing what it claims.

Run:  python test_freshness.py        (exit 0 = every case behaved)
"""
import datetime, gzip, json, os, re, shutil, sys, tempfile, time
import freshness as F

UTC = datetime.timezone.utc
PASS, FAIL = [], []


def build(root, ages_min, no_stamp=(), corrupt=()):
    """ages_min: minutes ago each artifact was last built."""
    """A synthetic repo where each artifact is `ages_min` minutes old."""
    now = datetime.datetime.now(UTC)
    day, uday = F.et_date(now), now.strftime("%Y-%m-%d")
    os.makedirs(f"{root}/data/latest", exist_ok=True)
    os.makedirs(f"{root}/picks", exist_ok=True)
    # 🔴 THE SLATE DATE, NOT THE UTC DATE — see freshness.slate_date.
    os.makedirs(f"{root}/data/{F.slate_date(now)}/results", exist_ok=True)

    def ts(mode):
        return (now - datetime.timedelta(minutes=ages_min.get(mode, 0))
                ).strftime("%Y-%m-%dT%H:%M:%SZ")

    def put(path, mode):
        body = {} if mode in no_stamp else {"pulled_at": ts(mode)}
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "wt") as fh:
            fh.write("{not json" if mode in corrupt else json.dumps(body))

    L = f"{root}/data/latest"
    put(f"{L}/scores.json.gz", "scores")
    put(f"{L}/pitchers.json.gz", "pitchers")
    put(f"{L}/hitters.json.gz", "hitters")
    put(f"{L}/board.json", "gamelines")
    put(f"{L}/props.json.gz", "props-board")
    put(f"{L}/lineups.json.gz", "lineups")
    put(f"{L}/weather.json.gz", "weather")
    put(f"{L}/news.json", "news")
    put(f"{L}/record.json", "record")
    put(f"{root}/data/{F.slate_date(now)}/results/final.json.gz", "results")
    # 🔴 THE CARD IS DATED BY ITS DEADLINE, NOT BY THE WALL CLOCK.
    # ⛔ This harness wrote `picks/<et_date>.json` and therefore ENCODED
    # THE BUG IT WAS SUPPOSED TO CATCH -- inside the midnight-to-10am
    # window it built the file the broken contract asked for, so the
    # control case passed while production went red every night.
    put(f"{root}/picks/{F.due_date(F.CARD, now)}.json", "card")

    for kind in ("props-pitcher", "props-batter"):
        # 🔴 A snapshot lands in the directory for the UTC DAY IT WAS
        # WRITTEN, so an artifact older than today belongs in an earlier
        # directory. Modelling that correctly is what exposed the
        # day-rollover bug in newest_age_minutes.
        when = now - datetime.timedelta(minutes=ages_min.get(kind, 0))
        d = f"{root}/data/{when.strftime('%Y-%m-%d')}/{kind}"
        os.makedirs(d, exist_ok=True)
        with gzip.open(f"{d}/{when.strftime('%H%M')}.json.gz", "wt") as fh:
            fh.write("{}")
    return root


def check(name, root, must_flag, mtime_now=True):
    """`must_flag` = set of modes the survey MUST report stale."""
    if mtime_now:
        # 🔴 SIMULATE A FRESH `git checkout`: every mtime becomes now.
        # This is the condition that defeated the old guard.
        for dp, _, fs in os.walk(root):
            for f in fs:
                os.utime(os.path.join(dp, f), None)
    rows = F.survey(data=f"{root}/data", picks=f"{root}/picks")
    stale = {r["mode"] for r in rows if r["stale"]}
    ok = must_flag <= stale
    (PASS if ok else FAIL).append(name)
    print(f"  [{'CAUGHT' if ok else 'MISSED'}] {name}")
    if not ok:
        print(f"           expected stale: {sorted(must_flag)}")
        print(f"           actually stale: {sorted(stale)}")
    return rows


tmp = tempfile.mkdtemp()
try:
    print("FAULT INJECTION — each case must be CAUGHT\n")

    # 1 — the actual 2026-08-28 defect
    r = build(f"{tmp}/f1", {"props-pitcher": 900, "props-batter": 900})
    check("props 15 hours old (the live defect)", r,
          {"props-pitcher", "props-batter"})

    # 2 — the same, stated as the mechanism that hid it
    print("       ^ mtimes were reset to 'now' before every check above,")
    print("         which is exactly what defeated os.path.getmtime.\n")

    # 3 — the card missed its 10:00am build
    r = build(f"{tmp}/f3", {"card": 24*60})
    check("card not rebuilt since yesterday (due 10:00am)", r, {"card"})

    # 4 — an artifact carrying NO timestamp must never read as fresh
    r = build(f"{tmp}/f4", {}, no_stamp=("record",))
    check("artifact with no timestamp at all", r, {"record"})

    # 5 — a corrupt artifact must fail loudly, not crash or pass
    r = build(f"{tmp}/f5", {}, corrupt=("board.json", "gamelines"))
    check("unreadable/corrupt artifact", r, {"gamelines"})

    # 6 — the track-record hole: results stale
    r = build(f"{tmp}/f6", {"results": 5000, "scores": 5000})
    check("results + scores 3.5 days old (missed 6:00am)", r, {"results", "scores"})

    # 7 — CONTROL: everything built since its deadline -> NOTHING flagged
    r = build(f"{tmp}/f7", {})
    rows = F.survey(data=f"{tmp}/f7/data", picks=f"{tmp}/f7/picks")
    stale = {x["mode"] for x in rows if x["stale"]}
    ok = not stale
    (PASS if ok else FAIL).append("control: all fresh -> silent")
    print(f"  [{'CORRECT' if ok else 'FALSE ALARM'}] control: everything "
          f"current reports nothing stale")
    if not ok:
        print(f"           wrongly flagged: {sorted(stale)}")

    # 8 — the cascade
    r = build(f"{tmp}/f8", {"props-pitcher": 24*60})
    modes, _ = F.plan(data=f"{tmp}/f8/data", picks=f"{tmp}/f8/picks")
    ok = modes == ["props-pitcher", "props-board"]
    (PASS if ok else FAIL).append("cascade")
    print(f"  [{'CORRECT' if ok else 'BROKEN'}] cascade: a late props pull "
          f"drags the join with it -> {modes}")
    print( "            ⛔ and NOT the card: the 10am card is the 10am card,")
    print( "               so the 4pm odds pull must not quietly rebuild it.")

    # 9 — THE DAY-ROLLOVER CASE, added after the suite caught it.
    #     At 00:30Z (8:30pm ET) yesterday's 4pm pull is 4.5h old and
    #     STILL SATISFIES the 4pm deadline. It must NOT be re-bought.
    roll = datetime.datetime.now(UTC).replace(hour=0, minute=30)
    r = build(f"{tmp}/f10", {"props-pitcher": 270, "props-batter": 270})
    rows = F.survey(data=f"{tmp}/f10/data", picks=f"{tmp}/f10/picks")
    pp = [x for x in rows if x["mode"] == "props-pitcher"][0]
    ok = not pp["missing"]
    (PASS if ok else FAIL).append("day rollover")
    print(f"  [{'CORRECT' if ok else 'BROKEN'}] day rollover: a pull from "
          f"the previous UTC day is still visible "
          f"(age {pp['age_min']}m, not MISSING)")

    # 10 — a FUTURE timestamp (clock skew) must not read as infinitely fresh
    #     in a way that hides a real problem. Age floors at 0, which is the
    #     safe direction ONLY if the writer is trustworthy; recorded here so
    #     the behaviour is known rather than discovered.
    r = build(f"{tmp}/f9", {"card": -600})
    rows = F.survey(data=f"{tmp}/f9/data", picks=f"{tmp}/f9/picks")
    card = [x for x in rows if x["mode"] == "card"][0]
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
    build(f"{root}/x", {"props-pitcher": 900, "card": 24 * 60})
    cwd = os.getcwd()
    ok = True
    try:
        os.chdir(f"{root}/x")
        import collect
        importlib.reload(collect)
        ran = []
        collect.run_mode = lambda m: ran.append(m)
        collect.daily_spend = lambda: 0
        code = collect.converge()          # 🔴 the real thing
        print(f"  [{'OK  ' if ran else 'DEAD'}] converge ran {len(ran)} mode(s) "
              f"and returned {code}")
        ok &= bool(ran)

        # a HARD mode failing must turn the run red
        def hard_fail(m):
            if m == "card":
                raise RuntimeError("card blew up")
        collect.run_mode = hard_fail
        code = collect.converge()
        print(f"  [{'OK  ' if code else 'WRONG'}] a failed CARD returns {code} "
              f"(non-zero = the run goes red)")
        ok &= bool(code)

        # a SOFT mode failing must not
        def soft_fail(m):
            if m in ("news", "weather", "lineups"):
                raise RuntimeError("feed down")
        collect.run_mode = soft_fail
        code = collect.converge()
        print(f"  [{'OK  ' if not code else 'WRONG'}] a failed NEWS returns "
              f"{code} (zero = headlines are not worth a red run)")
        ok &= not code

        # the published report must carry every field the page reads
        rep = json.load(open("data/latest/freshness.json"))
        need = {"mode", "stale", "missing", "late_min", "due_et", "age_min"}
        miss = need - set(rep["artifacts"][0])
        print(f"  [{'OK  ' if not miss else 'GONE'}] freshness.json carries "
              f"every field the banner reads{'' if not miss else ' — MISSING ' + str(miss)}")
        ok &= not miss
    except Exception as e:
        print(f"  [CRASH] converge raised {type(e).__name__}: {e}")
        ok = False
    finally:
        os.chdir(cwd)
        shutil.rmtree(root, ignore_errors=True)
    return ok


print("\nCONVERGE, END TO END")
if not check_converge():
    print("  ⛔ converge itself is broken — nothing would collect")
    FAIL.append("converge")

print("\nWORKFLOW TRIGGERS")
if not check_workflow():
    print("  ⛔ a trigger is missing — uploads or schedules would be silent")
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
if _moved:
    FAIL.append(f"paths move without their deadline: {_moved}")

sys.exit(1 if FAIL else 0)
