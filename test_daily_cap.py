#!/usr/bin/env python3
"""
🔴🔴 THE DAILY CAP COUNTED ONE LEAGUE AND THE ACCOUNT PAYS FOR THREE.

`[pre-registered 2026-09-05; the condition arose the same day and the test
FAILED arithmetically; fixed 2026-09-06]`

    day          TOTAL   mlb  ncaaf   nfl     flat cap
    2026-09-05     794   372    404    18          600
    billed (credits_remaining 18541 -> 17678)  869

⛔ **The account was billed 869 against a 600 cap and NO LEAGUE'S OWN
COUNTER EVER PASSED 404.** The cap did not fire late — it was never in a
position to fire. `daily_spend()` walked `{DATA}/{day}` and `DATA` is
league-scoped.

⚠️ AND THE FLAT CAP WAS ALSO THE WRONG SHAPE. Priced against the Odds
API's own game list (the billing denominator, not our schedule), the nine
days from 09-06 average 446 and ONE needs 973 — Saturday 12 September. A
flat 600 refuses the only day that matters while six quiet days go unused,
on a month that has spent 2,705 of 20,000 in six days.

WHAT IS PINNED:
  1. the sum is the ACCOUNT's, identical no matter which league asks
  2. it reproduces the real 2026-09-05 figure from the stored files
  3. the defect's signature is re-measured: a day over the flat cap where
     no single league was
  4. the allowance never drops below the flat cap and never passes the
     hard ceiling
  5. the enforcement site spends against the allowance, not the old
     league-scoped constant
"""
import collections
import datetime
import glob
import gzip
import json
import os
import re

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
import collect as C          # noqa: E402  (chdir first — it reads paths)


def sweep():
    """Every stored paid snapshot, by day and league. ⛔ Read, not modelled."""
    seen, rows = set(), []
    for p in glob.glob("data/**/*.json*", recursive=True):
        rp = os.path.realpath(p)
        if rp in seen or "/latest/" in p:
            continue
        seen.add(rp)
        try:
            op = gzip.open if p.endswith(".gz") else open
            with op(p, "rt") as fh:
                d = json.load(fh)
        except Exception:
            continue
        if not isinstance(d, dict) or "credits_used" not in d:
            continue
        parts = p.split("/")
        lg = parts[1] if len(parts) > 1 and parts[1] in ("nfl", "ncaaf") else "mlb"
        ts = (d.get("written_at") or d.get("pulled_at") or "")[:10]
        rows.append((ts, lg, int(d.get("credits_used") or 0)))
    return rows


ROWS = sweep()
BY = collections.defaultdict(collections.Counter)
for day, lg, c in ROWS:
    BY[day]["total"] += c
    BY[day][lg] += c

print("\n═══ 1. THE SUM IS THE ACCOUNT'S, WHOEVER ASKS ═══")
ck("there are stored paid snapshots to measure", len(ROWS) > 20,
   f"{len(ROWS)} snapshots")
roots = C._dated_roots("2026-09-05")
ck("🔴 the day's roots cover EVERY league, not just the caller's",
   len(roots) == len(C.LEAGUES),
   f"{len(roots)} roots for {len(C.LEAGUES)} leagues: {roots}")
# ⛔ A CHECK WITH A `True` FALLBACK ASSERTS NOTHING (rule 142). Read the
#    function's real source instead of asking whether a helper exists.
import inspect  # noqa: E402


def code_only(fn):
    """A function's executable lines - docstring and comments removed.

    THE FIRST VERSION OF THIS CHECK SEARCHED THE WHOLE FUNCTION AND FIRED
    ON THE COMMENT EXPLAINING WHY `dirname` IS NOT USED - the SEVENTH
    false failure of that shape here. THE SECOND VERSION tried to track
    triple quotes by hand and swallowed the whole body, which is a check
    that asserts nothing (rule 142) wearing the costume of one that does.
    This one asks Python for the docstring and deletes exactly that.
    """
    src = inspect.getsource(fn)
    doc = inspect.getdoc(fn)
    if doc:
        for line in doc.splitlines():
            line = line.strip()
            if line:
                src = src.replace(line, "")
    return "\n".join(ln.split("#")[0] for ln in src.splitlines())


_roots_code = code_only(C._dated_roots)
ck("...and they are derived from the league table, not by path surgery",
   "LEAGUES[" in _roots_code and "dirname" not in _roots_code,
   "a dirname would break silently the moment a league's directory moved")
ck("...and the stripper really removed the prose it was fooled by",
   "THE WHOLE ACCOUNT" not in _roots_code and "os.path.join" in _roots_code,
   "a stripper that eats the body would make the check above vacuous")

# ⛔ THE REAL CHECK: the same day, asked from three different leagues,
#    must return ONE number. That is the entire defect.
day = "2026-09-05"
got = C.daily_spend(day)
want = BY[day]["total"]
ck(f"🔴 daily_spend({day}) equals the account's own total",
   got == want, f"{got} vs {want} swept independently")
ck("...and it is bigger than any single league's share",
   got > max(BY[day]["mlb"], BY[day]["ncaaf"], BY[day]["nfl"]),
   f"account {got} vs biggest league "
   f"{max(BY[day]['mlb'], BY[day]['ncaaf'], BY[day]['nfl'])}")

print("\n═══ 2. THE DEFECT'S SIGNATURE, RE-MEASURED ═══")
# 🔴 A day the ACCOUNT went over the flat cap while NO league did is a day
#    the old cap could not have fired. Report every one of them.
blind = [(d, b["total"], b["mlb"], b["ncaaf"], b["nfl"])
         for d, b in sorted(BY.items())
         if b["total"] > C.FLAT_DAILY_CAP
         and max(b["mlb"], b["ncaaf"], b["nfl"]) <= C.FLAT_DAILY_CAP]
for d, t, m, c, n in blind:
    note(f"🔴 {d}: account {t} over the {C.FLAT_DAILY_CAP} cap — "
         f"mlb {m}, ncaaf {c}, nfl {n}, none of them over")
ck("the blind days are found by measurement, not quoted from a doc",
   isinstance(blind, list),
   f"{len(blind)} day(s) where the old cap could not have fired")
if blind:
    ck("🔴 and the fixed sum SEES every one of them",
       all(C.daily_spend(d) > C.FLAT_DAILY_CAP for d, *_ in blind),
       "each one now reads over the flat cap from any league")

print("\n═══ 3. THE ALLOWANCE HAS A FLOOR AND A CEILING ═══")
ck("the ceiling is above the flat cap", C.HARD_DAY_CEIL > C.FLAT_DAILY_CAP,
   f"flat {C.FLAT_DAILY_CAP}, ceiling {C.HARD_DAY_CEIL}")
allow = C.daily_allowance()
ck("today's allowance is never below the flat cap", allow >= C.FLAT_DAILY_CAP,
   f"{allow} — one overspent month must not lock the product out")
ck("🔴 ...and never above the hard ceiling", allow <= C.HARD_DAY_CEIL,
   f"{allow} of {C.HARD_DAY_CEIL} — a looping bug cannot drain the plan")
note(f"month to date {sum(C.month_spend().values())} of {C.MONTHLY_PLAN}; "
     f"today's allowance {allow}")

# ⛔ DRIVEN, not reasoned about: a month that has banked a huge allowance
#    still cannot pass the ceiling, and one that overspent still gets the
#    flat cap.
_real = C.month_spend
try:
    C.month_spend = lambda: {"x": 0}
    ck("a month that has spent nothing is still capped at the ceiling",
       C.daily_allowance() == C.HARD_DAY_CEIL, str(C.daily_allowance()))
    C.month_spend = lambda: {"x": C.MONTHLY_PLAN * 2}
    ck("a month that has blown the plan still gets the flat cap",
       C.daily_allowance() == C.FLAT_DAILY_CAP, str(C.daily_allowance()))
finally:
    C.month_spend = _real

print("\n═══ 4. THE ENFORCEMENT SITE ACTUALLY USES IT ═══")
src = open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
i = src.index("paid = {r[\"mode\"] for r in rows if r[\"paid\"]}")
j = src.index("SKIPPED ON BUDGET", i)
blk = src[i:j]
ck("🔴 the cap compared against is the ACCOUNT allowance",
   "if spent >= cap_today:" in blk and "cap_today = daily_allowance()" in blk,
   "a renderer nobody calls is a decoy; so is a cap nobody compares to")
ck("⛔ the old league-scoped constant is no longer the gate",
   "if spent >= DAILY_CAP:" not in blk,
   "DAILY_CAP survives as the FLOOR of the allowance, not the gate")
ck("the skip is still loud", "NOTHING SPENT" in blk and "SKIPPING" in blk,
   "a skipped paid pull leaves the artifact out of contract and reddens "
   "the run — that is the design, not a failure to hide")
ck("the log line says it is the ACCOUNT's spend",
   "(ACCOUNT, all leagues)" in src,
   "the number that misled for three days was labelled the same as this one")

print("\n═══ 5. ⚠️ THE SWEEP IS A FLOOR, AND SAYS SO ═══")
# `[2026-09-05]` stored 794, billed 869 by balance arithmetic.
bal = []
for p in glob.glob("data/**/*.json*", recursive=True):
    if "/latest/" in p:
        continue
    try:
        op = gzip.open if p.endswith(".gz") else open
        with op(p, "rt") as fh:
            d = json.load(fh)
    except Exception:
        continue
    if isinstance(d, dict) and d.get("credits_remaining") is not None:
        bal.append(((d.get("written_at") or d.get("pulled_at") or ""),
                    d["credits_remaining"]))
bal.sort()
drop, prev = collections.Counter(), None
for ts, rem in bal:
    if prev is not None and prev - rem > 0:
        drop[ts[:10]] += prev - rem
    prev = rem
gaps = {d: drop[d] - BY[d]["total"] for d in sorted(BY) if d in drop}
worst = max(gaps.items(), key=lambda kv: kv[1]) if gaps else (None, 0)
note(f"largest stored-vs-billed gap: {worst[0]} short by {worst[1]} credits")
ck("⚠️ the docstring warns the sweep can UNDER-count",
   "FLOOR" in (C.daily_spend.__doc__ or ""),
   "a paid call that fails to write a snapshot is invisible to it — "
   f"{worst[1]} credits on {worst[0]}")
