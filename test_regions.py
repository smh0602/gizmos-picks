#!/usr/bin/env python3
"""Does the BATTER side ever get the five-book pull?

🔴 WHY THIS EXISTS. `props_regions()` took no argument and scanned BOTH
prop directories. Converge builds pitcher first, which writes a snapshot
stamped `us,us2`; the batter side asked ONE SECOND LATER, saw the
PITCHER's full pull, and downgraded itself to Hard Rock alone.
⛔ THE BATTER SIDE COULD NEVER TAKE THE FIVE-BOOK PULL ON ANY DAY, BY
CONSTRUCTION -- five consecutive cards, 8/27 to 8/31, priced every hitter
row off one book.
⛔ IT WAS WRITTEN UP AS FIXED ON 8/29 AND NEVER LANDED ON MAIN, and
nothing in the project could tell the two apart, because what was checked
was the patch and not the next day's stored `regions`.

⚠️ THIS TEST IS WRITTEN BOTH WAYS ON PURPOSE. A test that only passes on
the fix cannot tell you the fix was needed. This one asserts the SHAPE
that made the bug impossible to have: the pitcher's snapshot must not
change the batter's answer.
"""
import gzip, json, os, shutil, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def ck(name, ok, detail=""):
    print(("  [OK  ] " if ok else "  [FAIL] ") + name + (f"  {detail}" if detail else ""))
    if not ok:
        FAIL.append(name)


def snap(root, day, kind, hhmm, regions):
    d = os.path.join(root, day, kind)
    os.makedirs(d, exist_ok=True)
    with gzip.open(os.path.join(d, f"{hhmm}.json.gz"), "wt") as fh:
        json.dump({"regions": regions, "credits_used": 1}, fh)


root = tempfile.mkdtemp(prefix="regions-")
try:
    import collect

    day = collect.now().strftime("%Y-%m-%d")
    collect.DATA = root
    # 🔴 FORCE THE WINDOW. This test ran at 23Z and SKIPPED its three
    # most important assertions -- the ones that actually reproduce the
    # bug. ⛔ A suite that quietly skips its core case when CI happens to
    # run at the wrong hour is the same failure as a date bug you cannot
    # see outside its window. The clock is pinned instead.
    import datetime as _dt
    _real_now = collect.now
    collect.now = lambda: _dt.datetime(2026, 8, 31, 11, 7,
                                       tzinfo=_dt.timezone.utc)
    day = collect.now().strftime("%Y-%m-%d")
    in_window = True

    # ── 1. NOTHING PULLED YET: both sides must want the full pull ──────
    if in_window:
        ck("pitcher asks for both regions when nothing has been pulled",
           collect.props_regions("pitcher") == collect.REGIONS_FULL)
        ck("batter asks for both regions when nothing has been pulled",
           collect.props_regions("batter") == collect.REGIONS_FULL)

        # ── 2. THE BUG ITSELF. Pitcher takes its full pull FIRST. ──────
        snap(root, day, "props-pitcher", "1107", "us,us2")
        ck("pitcher stands down after its OWN full pull",
           collect.props_regions("pitcher") == collect.REGIONS_CHEAP)
        ck("🔴 THE BUG: the batter side STILL asks for both regions — the "
           "pitcher's snapshot must not answer the batter's question",
           collect.props_regions("batter") == collect.REGIONS_FULL,
           f"got {collect.props_regions('batter')!r}; a batter pull at "
           f"'us2' here is the defect that mispriced five cards")

        # ── 3. NO DOUBLE SPEND. Once batter has its own, it stands down.
        snap(root, day, "props-batter", "1108", "us,us2")
        ck("batter stands down after its OWN full pull (no double spend)",
           collect.props_regions("batter") == collect.REGIONS_CHEAP)
    # ⛔ AND PROVE THE CLOCK GUARD STILL WORKS, so pinning it above did
    # not quietly disable the 4pm Hard-Rock-only rule.
    collect.now = lambda: _dt.datetime(2026, 8, 31, 20, 13,
                                       tzinfo=_dt.timezone.utc)
    ck("outside the morning window BOTH sides are Hard Rock only",
       collect.props_regions("pitcher") == collect.REGIONS_CHEAP
       and collect.props_regions("batter") == collect.REGIONS_CHEAP)
    collect.now = _real_now

    # ── 4. THE SHAPE, CHECKABLE AT ANY HOUR ───────────────────────────
    import inspect
    sig = inspect.signature(collect.props_regions)
    ck("props_regions takes the kind as an argument",
       len(sig.parameters) == 1, str(sig))
    src = inspect.getsource(collect.props_regions)
    ck("it does NOT loop over both prop directories",
       'for kind in ("props-pitcher", "props-batter")' not in src)
    import re
    # ⚠️ CODE LINES ONLY. A comment that mentions props_regions() is not
    # a call site, and counting it made this test fail on its own prose.
    _src = [l for l in open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "collect.py")).read().splitlines()
        if not l.lstrip().startswith("#")]
    calls = re.findall(r"props_regions\(([^)]*)\)", "\n".join(_src))
    bare = [c for c in calls if not c.strip()]
    ck("every call site passes a kind", not bare,
       f"{len(bare)} bare call(s) — a bare call is the old bug")
finally:
    shutil.rmtree(root, ignore_errors=True)

print()
if FAIL:
    print(f"⛔ {len(FAIL)} FAILED: {FAIL}")
    sys.exit(1)
print("✅ the batter side can take the five-book pull")
