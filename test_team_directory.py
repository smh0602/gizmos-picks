#!/usr/bin/env python3
"""The college logo directory must REPAIR ITSELF, not depend on a lucky run.

🔴 WHAT WENT WRONG. `data/ncaaf/latest/teams.json` is what puts a crest
next to every college team on the page. The writer was built, wired to a
mode, and then **named by no cron at all** — so the file existed only
because one ad-hoc converge run happened to call it. Sam reported "mo team
logos"; the fix at the time was to embed the 32 NFL logos in the page,
which papered over the college half.

⛔ A WEEKLY CRON ALONE IS NOT A FIX, AND THIS REPO ALREADY KNOWS WHY.
Measured 2026-08-26: only **29 of 70** gamelines hour-slots produced a
file. GitHub drops scheduled runs. A weekly rebuild whose run is dropped
is a **fortnight** of a page with no logos and nothing to notice it.

✅ SO THERE ARE TWO MECHANISMS AND THIS TEST PINS BOTH:
  1. the weekly cron NAMES `cfb-teams` (section 3), and
  2. `collect.py` rebuilds ON DEMAND whenever the directory is missing,
     unreadable, empty, or stamped with the wrong season (section 1).

⚠️ SECTION 2 IS THE ONE THAT MATTERS IN AUGUST. A directory built for
last season is **not a smaller problem than a missing one** — realignment
moves schools between conferences every year, so a stale file is wrong
rather than merely old, and it would never announce itself. The file
stamps its own `season`, so the check ASKS it instead of guessing.

⛔ IT MUST NEVER BE FATAL. A missing directory costs LOGOS, not data, and
it stands in front of a PAID odds pull whose history cannot be re-bought.
Section 4 pins that a rebuild failure is swallowed.

⚠️ No network and no credits — every case is a temp directory.
"""
import json
import os
import shutil
import sys
import tempfile

os.environ.setdefault("LEAGUE", "ncaaf")
import collect as C
import freshness as _fresh

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<62} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<62} {detail}")
    if not cond:
        fails.append(label)


def write_dir(root, doc):
    d = os.path.join(root, "data", "ncaaf", "latest")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "teams.json")
    if doc is None:
        if os.path.exists(p):
            os.remove(p)
    elif isinstance(doc, str):
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(doc)
    else:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
    return p


def state_in(root, doc):
    """Run the real check with `root` as the working directory."""
    write_dir(root, doc)
    cwd = os.getcwd()
    try:
        os.chdir(root)
        return C.cfb_team_directory_state()
    finally:
        os.chdir(cwd)


SEASON = _fresh.current_football_season()
GOOD = {"season": SEASON, "n": 138,
        "teams": {"Alabama": {"logo": "https://x/1.png"}}}

print("\n1. THE DEFECTS THAT MUST TRIGGER A REBUILD")
root = tempfile.mkdtemp()
try:
    need, why = state_in(root, None)
    eq(need, True, "a MISSING directory needs a rebuild")
    ck("does not exist" in why, "  and it says so", why)

    need, why = state_in(root, "{not json")
    eq(need, True, "an UNREADABLE directory needs a rebuild")
    ck("unreadable" in why, "  and it says so", why)

    need, _ = state_in(root, {"season": SEASON, "teams": {}})
    eq(need, True, "an EMPTY directory needs a rebuild")

    need, _ = state_in(root, {"season": SEASON})
    eq(need, True, "a directory with NO teams key needs a rebuild")
finally:
    shutil.rmtree(root, ignore_errors=True)

print("\n2. 🔴 A DIRECTORY BUILT FOR ANOTHER SEASON IS WRONG, NOT MERELY OLD")
print("   Realignment moves schools every August. A stale file is a page")
print("   showing last year's conferences and it never says so.")
root = tempfile.mkdtemp()
try:
    stale = dict(GOOD, season=SEASON - 1)
    need, why = state_in(root, stale)
    eq(need, True, f"season {SEASON - 1} against a current season of {SEASON}")
    ck(str(SEASON - 1) in why and str(SEASON) in why,
       "  the reason names BOTH seasons", why)

    need, _ = state_in(root, dict(GOOD, season=str(SEASON)))
    eq(need, True, "a season stored as a STRING is not the current season")

    need, why = state_in(root, GOOD)
    eq(need, False, "⛔ a CURRENT, populated directory is left alone")
    ck("138" in why, "  and the reason reports what it found", why)
finally:
    shutil.rmtree(root, ignore_errors=True)

print("\n3. THE WEEKLY CRON NAMES THE MODE — the backstop, read from the")
print("   workflow itself rather than asserted from memory")
WF = ".github/workflows/collect.yml"
wf = open(WF, encoding="utf-8").read() if os.path.exists(WF) else ""
ck(bool(wf), f"{WF} is readable", f"{len(wf)} bytes")
ck("cfb-teams" in wf, "🔴 some cron names `cfb-teams`",
   "it was in NONE before 2026-09-04")
# ⛔ Not just present -- present on a line that ROUTES A SCHEDULE, so a
# mention inside a comment cannot satisfy this.
routes = [l for l in wf.splitlines()
          if "cfb-teams" in l and "MODES=" in l and "LEAGUE=" in l]
ck(len(routes) >= 1, "  and it is on a real schedule-routing line",
   routes[:1])
ck(all("ncaaf" in l for l in routes), "  routed as ncaaf", routes[:1])

print("\n4. ⛔ FREE, AND NEVER FATAL")
# The mode must be on the FREE list, or a missing ODDS_API_KEY would kill
# a mode that never touches the Odds API.
src = open("collect.py", encoding="utf-8").read()
i = src.index("FREE = (")
ck('"cfb-teams"' in src[i:i + 500],
   "`cfb-teams` is on the FREE list (it calls CFBD, never the Odds API)")
# 🔴 The on-demand rebuild must swallow its own failure. Proven by making
# the rebuild raise and checking the caller returns normally.
import types
root = tempfile.mkdtemp()
cwd = os.getcwd()
try:
    write_dir(root, None)          # missing -> a rebuild will be attempted
    os.chdir(root)
    sys.path.insert(0, cwd)
    boom = types.ModuleType("cfb")

    def _raise(*a, **k):
        raise RuntimeError("CFBD is down")
    boom.fbs_conferences = _raise
    sys.modules["cfb"] = boom
    C._ensure_cfb_team_directory()
    ck(True, "🔴 a rebuild that RAISES does not take the odds pull down",
       "logos are cosmetic; odds history cannot be re-bought")
except Exception as e:
    ck(False, "a rebuild that RAISES does not take the odds pull down",
       f"{type(e).__name__}: {e}")
finally:
    sys.modules.pop("cfb", None)
    os.chdir(cwd)
    shutil.rmtree(root, ignore_errors=True)

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ team directory: all checks passed")
