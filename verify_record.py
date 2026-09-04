#!/usr/bin/env python3
"""Re-grades every published pick a SECOND way and checks record.json.

🔴 WHY THIS EXISTS. Sam asked, 2026-08-26: "can we verify that the track
record tab is accurate". The honest answer is not to check it once -- it is
to check it every time it is built. The track-record page is the one thing
the spec calls a REQUIREMENT rather than a feature: it is what separates
this from every other picks site, and a hit rate nobody can audit is worth
nothing.

⛔ NOTHING HERE READS A TOTAL OUT OF record.json AND CALLS IT VERIFIED.
It re-reads picks/<date>.json, re-reads the stored box scores, decides each
pick from scratch, and only then compares. A check that reuses the number
it is checking proves the file is readable, not that it is right.
"""
import glob
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
def _read_json(path, what):
    """json.load(open(path)) that says WHICH FILE when it fails.

    🔴 A run on 2026-08-26 died with `JSONDecodeError: Expecting value:
    line 1 column 1 (char 0)` -- an empty file -- and the traceback named
    only Python's decoder. Nothing in the repo was empty by the time it
    could be inspected, so the file could never be identified. An error
    that cannot be diagnosed after the fact is barely an error message.
    """
    import json as _json
    try:
        with open(path) as fh:
            raw = fh.read()
    except FileNotFoundError:
        raise SystemExit(f"MISSING: {what} at {path} does not exist.")
    if not raw.strip():
        raise SystemExit(f"EMPTY: {what} at {path} is zero bytes. "
                         f"Nothing was verified. Re-run the job that writes it.")
    try:
        return _json.loads(raw)
    except Exception as e:
        raise SystemExit(f"UNREADABLE: {what} at {path} is not valid JSON "
                         f"({type(e).__name__}: {e}). First 120 chars: {raw[:120]!r}")


fails = []


def ck(name, ok, detail=""):
    print(("  PASS " if ok else "  FAIL ") + name + ("  " + detail if detail else ""))
    if not ok:
        fails.append(name)


if not os.path.exists("data/latest/record.json"):
    print("No record.json yet -- nothing to verify.")
    sys.exit(0)
REC = _read_json("data/latest/record.json", "the track record")

# Results are filed under the RUN date and name their slate inside.
BY_SLATE, UNSETTLED = {}, {}
for p in glob.glob("data/*/results/final.json.gz"):
    r = json.load(gzip.open(p, "rt"))
    # 🔴 A SLATE THAT HAS NOT FINISHED CANNOT BE GRADED, AND ITS PICKS ARE
    # NOT VOIDS. `[measured 2026-08-31 23:09Z]` the 8/31 results file held
    # 12 games, ALL `Scheduled`, `n_final: 0` -- not one pitch thrown --
    # and this verifier graded that night's card against it, produced
    # 0/0, called all FIFTY picks VOIDS, and failed the run.
    # ⛔ VOID MEANS "THE GAME WAS PLAYED AND HE NEVER TOOK THE FIELD."
    # UNGRADED MEANS "IT HAS NOT HAPPENED YET." Conflating them turns
    # every evening into a red run, between the 10am card and the next
    # morning's grading.
    # 🔴 AND THE RULE ALREADY EXISTED: `collect_record()` has skipped
    # unsettled slates since it was written. THE BUILDER AND ITS OWN
    # VERIFIER DISAGREED ABOUT WHICH SLATES COUNT.
    # ⛔ THIS FILE DERIVES SETTLEDNESS ITSELF RATHER THAN TRUSTING
    # record.json's `skipped` LIST, because this file's own docstring
    # forbids reusing the number it is checking -- and if the builder has
    # not run since the card was written, that list does not mention the
    # slate at all. THAT IS EXACTLY WHAT HAPPENED ON 8/31.
    n_g, n_f = r.get("n_games", 0), r.get("n_final", 0)
    if n_g and n_f >= n_g:
        BY_SLATE.setdefault(r["slate_date"], r)
    else:
        UNSETTLED[r["slate_date"]] = f"{n_f}/{n_g} final"
if UNSETTLED:
    print("  NOT GRADED — the slate has not finished: "
          + ", ".join(f"{d} ({w})" for d, w in sorted(UNSETTLED.items())))

BAT = {"batter_hits": lambda b: b["H"],
       "batter_total_bases": lambda b: b["tb"],
       "batter_home_runs": lambda b: b["hr"],
       "batter_rbis": lambda b: b["rbi"],
       "batter_hits_runs_rbis": lambda b: b["H"] + b["r"] + b["rbi"]}


def actual(slate, pid, market):
    r = BY_SLATE.get(slate)
    if not r or pid is None:
        return None
    pid = int(pid)
    for g in r["games"]:
        if market in ("strikeouts", "outs"):
            for x in g.get("pitchers") or []:
                if x["id"] == pid and x.get("started"):
                    return x["k"] if market == "strikeouts" else x["outs"]
        elif market in BAT:
            for x in g.get("batters") or []:
                if x["id"] == pid:
                    return BAT[market](x)
    return None


mine, byday, bykind = {"w": 0, "n": 0}, {}, {"pitcher": {"w": 0, "n": 0},
                                            "hitter": {"w": 0, "n": 0}}
voids = {}
# 🔴 THIS FILE NO LONGER READS `record.json`'s OWN `skipped` LIST, AND
# THAT IS THE POINT OF THIS FILE. `[measured 2026-09-04]` the builder wrote
# 2026-09-03 into `skipped` twice -- because two COLLEGE FOOTBALL cards in
# `picks/` carry `"date": "2026-09-03"` -- and this verifier believed it,
# dropped a legitimately graded MLB day, reconstructed 300/499 against a
# published 333/549, and failed EVERY RUN. ⛔ A verifier that takes its
# exclusions from the artifact under test cannot catch a wrong exclusion;
# it can only be misled by one.
# ✅ SO EVERY REASON TO SKIP IS DERIVED HERE, INDEPENDENTLY, and each one
# is strictly narrower than "the file said so":
#     not this sport      -> the card names a league that is not mlb
#     not a machine card  -> kind != "gizmos-card"  (8/22 is TABLE A)
#     not settled         -> the slate is not in BY_SLATE, derived above
#                            from the stored box scores, not from a list
# ⚠️ The date comes from the CARD, not the filename: `fb-ncaaf-latest.json`
# has no date in its name and every football card has one inside it.
for f in sorted(glob.glob("picks/*.json")):
    doc = _read_json(f, "a published card")
    if (doc.get("league") or "mlb").lower() != "mlb":
        continue
    if doc.get("kind") != "gizmos-card":
        continue
    date = doc.get("date") or os.path.basename(f)[:-5]
    if date not in BY_SLATE:
        continue
    day = byday.setdefault(date, {"w": 0, "n": 0})
    for row in doc.get("picks", []):
        mk, side, line = row.get("market"), row.get("side"), row.get("line")
        if mk not in BAT and mk not in ("strikeouts", "outs"):
            continue
        a = actual(date, row.get("pid"), mk)
        if a is None:                     # never took the field -> VOID
            voids[date] = voids.get(date, 0) + 1
            continue
        win = int((a > line) if side == "over" else (a < line))
        kind = "hitter" if row.get("kind") == "hitter" else "pitcher"
        for c in (mine, day, bykind[kind]):
            c["n"] += 1
            c["w"] += win

print(f"\nRE-GRADED INDEPENDENTLY from {len(byday)} card(s) and the stored box scores")
ck(f"overall reproduces ({mine['w']}/{mine['n']})",
   (mine["w"], mine["n"]) == (REC["overall"]["w"], REC["overall"]["n"]),
   f"record.json says {REC['overall']['w']}/{REC['overall']['n']}")
for k in ("pitcher", "hitter"):
    t = REC["by_kind"].get(k, {})
    ck(f"{k} reproduces ({bykind[k]['w']}/{bykind[k]['n']})",
       (bykind[k]["w"], bykind[k]["n"]) == (t.get("w"), t.get("n")),
       f"record.json says {t.get('w')}/{t.get('n')}")
recday = {x["date"]: x for x in REC.get("by_day", [])}
bad = [(d, f"{v['w']}/{v['n']}", f"{recday.get(d,{}).get('w')}/{recday.get(d,{}).get('n')}")
       for d, v in byday.items()
       if (v["w"], v["n"]) != (recday.get(d, {}).get("w"), recday.get(d, {}).get("n"))]
ck(f"every graded day reproduces ({len(byday)} days)", not bad, str(bad[:3]))

# 🔴 THE ARITHMETIC MUST CLOSE ON ITSELF TOO.
ck("pitcher + hitter equals the overall",
   REC["by_kind"]["pitcher"]["n"] + REC["by_kind"]["hitter"]["n"] == REC["overall"]["n"])
ck("the days sum to the overall",
   sum(x["n"] for x in REC["by_day"]) == REC["overall"]["n"],
   f"{sum(x['n'] for x in REC['by_day'])} vs {REC['overall']['n']}")
ck("over + under equals the overall",
   sum(v["n"] for v in REC["by_side"].values()) == REC["overall"]["n"])
_p = REC["overall"]
ck("the published percentage is the published fraction",
   _p["n"] == 0 or abs(round(100 * _p["w"] / _p["n"], 1) - _p["pct"]) < 0.05)

# ⛔ VOIDS MUST NOT BE IN ANY DENOMINATOR. A player who never took the
# field is a refund at the book, not a loss, and on 2026-08-24 one was
# being dropped from the file entirely rather than recorded.
ck(f"voids are recorded and excluded ({sum(voids.values())} found)",
   all(recday.get(d, {}).get("voids", 0) == v for d, v in voids.items()),
   str({d: (v, recday.get(d, {}).get("voids")) for d, v in voids.items()}))

# The detail file the page drills into must agree with the totals above it.
dp = "data/latest/record-detail.json.gz"
if os.path.exists(dp):
    D = json.load(gzip.open(dp, "rt"))["days"]
    bad = []
    for d, x in recday.items():
        rows = D.get(d) or []
        w = sum(1 for r in rows if r.get("won") is True)
        n = sum(1 for r in rows if r.get("won") is not None)
        if (w, n) != (x["w"], x["n"]):
            bad.append((d, f"{w}/{n}", f"{x['w']}/{x['n']}"))
    ck(f"the drill-down detail sums to the day totals ({len(D)} days)",
       not bad, str(bad[:3]))
else:
    print("  NOTE  no record-detail.json.gz yet -- the page will show a message")

print(f"\n{'THE TRACK RECORD RECONCILES' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
