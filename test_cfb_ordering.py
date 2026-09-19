#!/usr/bin/env python3
"""THE DIAGNOSIS MUST STAY A MEASUREMENT, NOT BECOME A STORY.

`research/cfbd_plays_ordering.md` says one thing that matters: of eight
ways CFBD's `/plays` rows could be ordered, exactly one reproduces the
live signature, and the next-best candidate misses by seven times as much.

⚠️ THAT IS A CLAIM WITH NUMBERS IN IT, AND RULE 166 APPLIES — a number
written down is a claim about the world and it goes stale. So this file
re-derives every figure the report quotes and fails if the prose and the
evidence have parted company.

🔴🔴 THE SIMULATION LIVES HERE, IN THE TEST, AND THAT IS NOT TIDINESS —
IT IS THE ONLY PLACE TWO STANDING GUARDS BOTH ALLOW IT.

  · `test_harness.py` refuses a top-level import of anything that is not
    stdlib and not a TOP-LEVEL file of this repo. The runner installs a
    bare Python, and that check exists because a Playwright import once
    turned the collector red on every run. So the simulation could not
    sit in `research/` and be imported.
  · `test_coaches_probe.py` refuses to let any non-test top-level file
    NAME a probe artifact — *"a probe becoming a source is a decision Sam
    makes, not a diff"* — with a ratchet at zero. The simulation reads the
    snapshotted possession probe. So it could not sit at top level either.

⛔ NEITHER CHECK WAS TOUCHED. Widening the first would let a
`research/numpy.py` whitelist `numpy`; raising the second's ceiling is the
thing its own comment forbids. ✅ And the second names the way out
itself — *"a test READING a probe artifact is its job"* — which is exactly
what this is: a diagnostic, run by the suite, reading the evidence its
report rests on.

🔴🔴 THE HARDER HALF: A SIMULATION THAT HAS DRIFTED FROM THE CODE IT
SIMULATES MEASURES NOTHING. The pairing loop below re-implements
`possession_from_plays`'s. If its constants, its clock parser or its
bucketing drift, every verdict becomes a fact about a program nobody
runs. So:

  1. the H0 baseline must reproduce `possession_from_plays`'s OWN report —
     the real function, run on the same fixture, to the digit;
  2. the loop must READ `cfb`'s constants rather than carry copies,
     asserted on the PARSED AST so a comment cannot satisfy it.

⛔ WHAT THIS DOES NOT CLAIM: that H1 is what CFBD does. The report is
explicit that a fixture cannot settle a question about a different
distributor, and the discriminating test runs on CFBD's own rows. This
file guards the reasoning, not the conclusion.

⚠️ No network, no CFBD calls, no credits. One committed fixture, one
snapshotted probe.
"""
import ast
import collections
import gzip
import io
import json
import os
import random
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import cfb


# ══════════════════════════════════════════════════════════════════════
# @vacuity a bar moved to make the refusal pass is caught
#   file: cfb.py
#   find: CFB_ANOMALY_MAX_PCT = 2.0
#   with: CFB_ANOMALY_MAX_PCT = 40.0
# ══════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════
# THE SIMULATION
# ══════════════════════════════════════════════════════════════════════
FIXTURE = os.path.join(ROOT, "research", "cfb_clock_sample_2019.json.gz")
SNAPSHOT = os.path.join(ROOT, "research", "cfbd_top_probe_2026_20260918.json")

# ⛔ THE SEED IS FIXED so the shuffled hypotheses are a measurement rather
#    than a mood. Three of the eight below permute rows.
SEED = 36


def live_signature(path=SNAPSHOT):
    """The four numbers to explain, READ FROM THE ARTIFACT, never typed.

    ⛔ Rule 166: a number written down is a claim about the world and it
    goes stale. These come out of the probe the failed run actually
    wrote, snapshotted because `latest/` is overwritten every cfbd run
    and nothing archives this file by date.
    """
    d = json.load(open(path, encoding="utf-8"))
    return {"anom": d["anomaly_pct"],
            "neg": 100.0 * d["negative"] / d["pairs"],
            "over": 100.0 * d["over_max"] / d["pairs"],
            "med": d["coverage_median"],
            "mx": d["coverage_max"]}


def load_buckets(path=FIXTURE):
    """The fixture, bucketed EXACTLY as `possession_from_plays` buckets."""
    rows = json.load(gzip.open(path, "rt", encoding="utf-8"))["plays"]
    b = collections.defaultdict(list)
    for p in rows:
        gid, per = p.get("gameId"), p.get("period")
        if gid is None or per is None or int(per) > cfb.CFB_REG_PERIODS:
            continue
        secs = cfb._clock_secs(p)
        if secs is None:
            continue
        b[(gid, int(per))].append(
            {"n": p.get("playNumber"), "team": (p.get("offense") or "").strip(),
             "secs": secs, "drive": p.get("driveId")})
    return b


def score(buckets, order_fn):
    """Run the derivation's pairing rules over one ordering. -> signature."""
    pairs = neg = over = 0
    per_game = collections.defaultdict(lambda: collections.defaultdict(int))
    for (gid, _per), rs in buckets.items():
        rs = order_fn([dict(r) for r in rs])
        for a in range(len(rs) - 1):
            pairs += 1
            elapsed = rs[a]["secs"] - rs[a + 1]["secs"]
            if elapsed < 0:
                neg += 1
                continue
            if elapsed > cfb.CFB_MAX_PLAY_SECS:
                over += 1
                continue
            if rs[a]["team"]:
                per_game[gid][rs[a]["team"]] += elapsed
    cov = sorted(sum(t.values()) / float(cfb._poss.GAME_CLOCK_SECS)
                 for t in per_game.values())
    return {"anom": round(100.0 * (neg + over) / pairs, 3),
            "neg": 100.0 * neg / pairs, "over": 100.0 * over / pairs,
            "med": statistics.median(cov), "mx": cov[-1]}


def miss(sig, live):
    """Mean relative distance from the live signature, over four components.

    ⚠️ `anom` is deliberately NOT one of them — it is `neg + over`, so
    counting it as well would weight the same evidence twice.
    """
    return sum(abs(sig[k] - live[k]) / live[k]
               for k in ("neg", "over", "med", "mx")) / 4.0


# ── the orderings ─────────────────────────────────────────────────────
def h0_true(rs):
    """playNumber is the play's ordinal within the GAME — what the code assumes."""
    rs.sort(key=lambda r: (r["n"] is None, r["n"]))
    return rs


def h1_drive_local(rs):
    """playNumber RESTARTS AT 1 INSIDE EACH DRIVE, so the sort interleaves drives."""
    seen = collections.Counter()
    for r in h0_true(list(rs)):
        seen[r["drive"]] += 1
        r["_k"] = seen[r["drive"]]
    rs.sort(key=lambda r: r["_k"])
    return rs


def h1b_drive_local_tiebroken(rs):
    """H1, with the ties inside one ordinal broken by drive rather than left stable."""
    seen = collections.Counter()
    for r in h0_true(list(rs)):
        seen[r["drive"]] += 1
        r["_k"] = seen[r["drive"]]
    rs.sort(key=lambda r: (r["_k"], str(r["drive"])))
    return rs


def h2_shuffled(rs):
    """No usable order at all."""
    random.shuffle(rs)
    return rs


def h3_drives_out_of_order(rs):
    """Plays intact inside a drive; the drives themselves emitted out of order."""
    by = collections.OrderedDict()
    for r in h0_true(list(rs)):
        by.setdefault(r["drive"], []).append(r)
    ks = list(by)
    random.shuffle(ks)
    return [r for k in ks for r in by[k]]


def h12_drives_by_string(rs):
    """Drives ordered by driveId compared as a STRING — a classic id-sort bug."""
    by = collections.OrderedDict()
    for r in h0_true(list(rs)):
        by.setdefault(r["drive"], []).append(r)
    return [r for k in sorted(by, key=str) for r in by[k]]


def h11_by_offense(rs):
    """Rows grouped by the team on offence, time-ordered inside each group."""
    o = h0_true(list(rs))
    first = o[0]["team"] if o else ""
    return [r for r in o if r["team"] == first] + \
           [r for r in o if r["team"] != first]


def h4_ascending(rs):
    """The sort runs the wrong way round."""
    rs.sort(key=lambda r: r["secs"])
    return rs


def r1_drive_number(rs):
    """✅ THE REMEDY: under H1, re-sort by (driveNumber, playNumber).

    ⚠️ The input is SHUFFLED first on purpose — the claim is that this key
    recovers the true order from ANY input order, not that it happens to
    preserve one.
    """
    o = h0_true([dict(r) for r in rs])
    dn, seen = {}, collections.Counter()
    for r in o:
        dn.setdefault(r["drive"], len(dn))      # driveNumber, by construction
        seen[r["drive"]] += 1
        r["_dn"], r["_k"] = dn[r["drive"]], seen[r["drive"]]
    random.shuffle(o)
    o.sort(key=lambda r: (r["_dn"], r["_k"]))
    return o


HYPOTHESES = [
    ("H0  true order — playNumber is the game ordinal", h0_true),
    ("H1  playNumber RESTARTS PER DRIVE", h1_drive_local),
    ("H1b ...ties broken by drive id", h1b_drive_local_tiebroken),
    ("H3  drives emitted out of order", h3_drives_out_of_order),
    ("H12 drives ordered by driveId as a string", h12_drives_by_string),
    ("H11 rows grouped by the offence", h11_by_offense),
    ("H2  no usable order (shuffled)", h2_shuffled),
    ("H4  sorted ascending by clock", h4_ascending),
]


def run(buckets=None, live=None):
    """-> [(label, signature, miss)], ordered best-first."""
    random.seed(SEED)
    buckets = load_buckets() if buckets is None else buckets
    live = live_signature() if live is None else live
    out = []
    for label, fn in HYPOTHESES:
        sig = score(buckets, fn)
        out.append((label, sig, miss(sig, live)))
    out.sort(key=lambda t: t[2])
    return out


REPORT = os.path.join(ROOT, "research", "cfbd_plays_ordering.md")
_MD = io.open(REPORT, encoding="utf-8").read()
_SNAP = json.load(io.open(SNAPSHOT, encoding="utf-8"))

# ══════════════════════════════════════════════════════════════════════
section("1. ⚠️ THE EVIDENCE IS THERE AT ALL (rule 67)")
# ══════════════════════════════════════════════════════════════════════
_buckets = load_buckets()
ck("⚠️ the fixture bucketed into (game, period) buckets",
   len(_buckets) > 2000,
   "⛔ an empty fixture would make every comparison below pass having "
   "compared nothing. buckets=%d" % len(_buckets))
ck("⚠️ ...and the hypothesis field is wide enough to discriminate",
   len(HYPOTHESES) >= 6,
   "⛔ a 'winner' chosen from two candidates is not a diagnosis. "
   "hypotheses=%d" % len(HYPOTHESES))
ck("⚠️ the live signature is READ from the snapshot, not typed",
   all(k in _SNAP for k in ("anomaly_pct", "negative", "over_max",
                            "pairs", "coverage_median", "coverage_max")),
   "⛔ rule 166. The probe in `latest/` is overwritten every cfbd run, "
   "which is why the evidence is snapshotted. keys=%d" % len(_SNAP))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 THE SIM MEASURES THE SHIPPED DERIVATION, NOT A COPY")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THIS IS THE CHECK THAT MAKES EVERY OTHER ONE MEAN SOMETHING. Run the
#    REAL `possession_from_plays` over the same fixture and require the
#    sim's H0 to land on its report to the digit.
_top, _rep = cfb.possession_from_plays(
    json.load(__import__("gzip").open(FIXTURE, "rt", encoding="utf-8"))["plays"],
    2019, log=lambda *a, **k: None)
_h0 = score(_buckets, h0_true)

ck("🔴🔴 the sim's H0 REPRODUCES possession_from_plays's own anomaly_pct",
   _h0["anom"] == _rep["anomaly_pct"],
   "⛔ if these disagree the sim is a parallel implementation and its "
   "verdicts are about a program nobody runs (rule 117). "
   "sim=%s real=%s" % (_h0["anom"], _rep["anomaly_pct"]))
ck("🔴 ...and its coverage median and maximum, to the digit",
   round(_h0["med"], 4) == _rep["coverage_median"]
   and round(_h0["mx"], 4) == _rep["coverage_max"],
   "⛔ the coverage half is the symptom the report leans on hardest. "
   "sim med/max=%.4f/%.4f real=%s/%s"
   % (_h0["med"], _h0["mx"], _rep.get("coverage_median"),
      _rep.get("coverage_max")))

# ⛔ READ THE AST, NOT THE TEXT. A comment saying `cfb.CFB_MAX_PLAY_SECS`
#    satisfies a substring search and changes nothing at runtime — this
#    repo has shipped that mistake more than once.
_tree = ast.parse(io.open(os.path.abspath(__file__),
                          encoding="utf-8").read())
_attrs = {"%s.%s" % (n.value.id, n.attr)
          for n in ast.walk(_tree)
          if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
for _want in ("cfb.CFB_MAX_PLAY_SECS", "cfb.CFB_REG_PERIODS", "cfb._clock_secs"):
    ck("⛔ the sim reads %s from cfb, in CODE" % _want,
       _want in _attrs,
       "🔴 a copied constant drifts silently in the file you did not "
       "edit (rule 117), and the drift would show up as a wrong verdict "
       "rather than as a red test. attributes found: %d" % len(_attrs))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 ONE HYPOTHESIS FITS, AND IT IS NOT A CLOSE CALL")
# ══════════════════════════════════════════════════════════════════════
_ranked = run(_buckets)
_best_label, _best_sig, _best_miss = _ranked[0]
_runner = next((t for t in _ranked[1:] if not t[0].startswith("H1")), None)

ck("🔴 the closest hypothesis is the drive-local playNumber family",
   _best_label.startswith("H1"),
   "⛔ THE REPORT'S WHOLE CONCLUSION. If another ordering now fits better, "
   "the report is wrong and must be rewritten, not this check. "
   "winner=%r miss=%.3f" % (_best_label, _best_miss))
ck("⚠️ ...and BOTH members of that family beat every other candidate",
   all(l.startswith("H1") for l, _s, _m in _ranked[:2]),
   "⛔ a single lucky permutation is not a diagnosis; the two spellings "
   "of the same hypothesis should both land. top two: %s"
   % [l[:34] for l, _s, _m in _ranked[:2]])
ck("🔴🔴 the next-best NON-H1 candidate misses by at least 3x as much",
   _runner is not None and _runner[2] >= 3.0 * _best_miss,
   "⛔ THIS IS THE DIFFERENCE BETWEEN A DIAGNOSIS AND A PREFERENCE. "
   "A narrow win over a rival explanation is not something to act on. "
   "best=%.3f (%s)  runner-up=%.3f (%s)"
   % (_best_miss, _best_label[:26],
      _runner[2] if _runner else -1, _runner[0][:26] if _runner else "none"))

# ══════════════════════════════════════════════════════════════════════
section("4. ⛔ THE FIXTURE IS NOT EVIDENCE ABOUT CFBD, AND THAT IS MEASURED")
# ══════════════════════════════════════════════════════════════════════
# 🔴 `claude/possession-validation.md` carries this as a caveat in prose.
#    Here it is a number: the fixture's OWN ordering does not reproduce
#    the live signature and is nowhere near it.
_h0_entry = next(t for t in _ranked if t[0].startswith("H0"))
ck("⛔ the fixture's true ordering does NOT explain the live signature",
   _h0_entry[2] > 0.5,
   "🔴 if the known-good ordering landed near the live numbers, the live "
   "numbers would not be evidence of a defect at all. H0 miss=%.3f"
   % _h0_entry[2])

_live = live_signature()
ck("⚠️ the live anomaly really is over the bar the builder refuses on",
   _live["anom"] > cfb.CFB_ANOMALY_MAX_PCT,
   "⛔ the refusal is the premise of the whole report. live=%.3f bar=%.1f"
   % (_live["anom"], cfb.CFB_ANOMALY_MAX_PCT))
ck("⛔ and neither bar was moved to make anything pass",
   cfb.CFB_ANOMALY_MAX_PCT == 2.0 and cfb._poss.COVERAGE_MIN == 0.90,
   "🔴 CLAUDE.md's one rule that matters most. anomaly bar=%s floor=%s"
   % (cfb.CFB_ANOMALY_MAX_PCT, cfb._poss.COVERAGE_MIN))

# ══════════════════════════════════════════════════════════════════════
section("5. ✅ THE REMEDY PREDICTION RECOVERS THE TRUE ORDER EXACTLY")
# ══════════════════════════════════════════════════════════════════════
random.seed(SEED)
_r1 = score(_buckets, r1_drive_number)
ck("✅ (driveNumber, playNumber) rebuilds the truth from a SHUFFLED bucket",
   _r1 == _h0,
   "⛔ the report offers this as the fix to ship once CFBD's own rows "
   "confirm H1. If it no longer recovers the order, the report is "
   "offering something that does not work. r1=%s h0=%s" % (_r1, _h0))
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 ~~`"driveNumber" not in open("cfb.py").read()`~~ REPLACED, NOT
#      DELETED `[2026-09-19]`
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE OLD CHECK ASKED THE WRONG QUESTION. It was a SUBSTRING TEST ON
#    THE WHOLE FILE, so it could not tell MEASURING with `driveNumber`
#    from SORTING by it. Task 44 carries the field on the row and counts
#    with it — which the old check forbids and which changes nothing —
#    while the thing actually worth forbidding, a new sort key in the
#    possession path, it could never have seen on its own.
#    ➡️ Rule 249's shape: it guarded the instance, not the question.
# ✅ ITS OWN FAILURE TEXT SAID "DELETE THIS CHECK IN THAT PR". ⛔ That
#    would have been wrong. The check is doing real work — it is what
#    stops `cfb.py` quietly starting to re-sort — and CLAUDE.md allows a
#    check to change only when it asks the wrong question AND the
#    replacement is HARDER to pass. Both hold here.
# 🔴 THE REPLACEMENT PINS THE SORT KEY ITSELF, out of the parsed AST.
#    `driveNumber` may appear in the row dict and in the counters; the
#    derivation's own ordering expression must be byte-identical to what
#    it was. That catches a POSITIONAL change too — `r[1]` in place of
#    `r[0]` names nothing and the old check would have sailed past it.
_CFB_AST = ast.parse(io.open(os.path.join(ROOT, "cfb.py"),
                             encoding="utf-8").read())
_PFP = [n for n in ast.walk(_CFB_AST)
        if isinstance(n, ast.FunctionDef) and n.name == "possession_from_plays"]
ck("⚠️ `possession_from_plays` was found to inspect",
   len(_PFP) == 1,
   "⛔ if it cannot be located, every check below is vacuous — rule 67. "
   "found %d" % len(_PFP))

_SORTS = [ast.unparse(n) for n in ast.walk(_PFP[0])
          if isinstance(n, ast.Call)
          and (ast.unparse(n.func).endswith(".sort")
               or ast.unparse(n.func) == "sorted")]
ck("⚠️ ...and it really does sort, so the pin below has a subject",
   len(_SORTS) >= 1,
   "⛔ a pin over zero sorts proves nothing (rule 67). found: %s" % _SORTS)
# ⛔ EVERY SORT IN THE FUNCTION, NOT ONLY THE KEYED ONE. Filtering to
#    calls carrying `key=` would let a bare `sorted(...)` introduce an
#    ordering decision the pin never sees. The second entry sorts team
#    NAMES for an error message and orders no plays.
# 🔴🔴 ~~`"rows.sort(key=lambda r: (r[0] is None, r[0]))"`~~ REPOINTED
#      2026-09-19, ON SAM'S WORD AND NOT BEFORE.
# The pin's own text said *"shipping the remedy is Sam's decision, not a
# diff's"* — and that is still the rule. This branch IS that decision
# being put to him, with the measurement attached; it is not merged with
# the rest of the fix set. ⛔ The pin is NOT removed: it still names the
# exact expression, so the next unannounced re-sort is caught the same
# way this one was made deliberate.
_EXPECTED_SORTS = [
    "rows.sort(key=lambda r: (r[4] is None, r[4], r[0] is None, r[0]))",
    "sorted(bad)"]
ck("🔴🔴 THE DERIVATION'S SORT KEY IS EXACTLY THE DECLARED ONE",
   sorted(_SORTS) == sorted(_EXPECTED_SORTS),
   "⛔ THE CHECK THAT MATTERS. ⚠️ This pins the EXPRESSIONS, so a "
   "positional swap that names nothing is caught too, and so is a NEW "
   "sort call. got: %s" % _SORTS)
# ⚠️ ~~"no comparison inside it mentions driveNumber"~~ — that check was
#    the negative form of the pin above and is now subsumed by it: the
#    pin names the whole expression, so it catches a driveNumber
#    comparison AND everything else. Keeping both would be two readers
#    of one rule (rule 66). What replaces it is stronger: the tuple the
#    pairing loop unpacks must carry the field the sort reads, or the
#    sort is indexing something else.
_PAIR_FOR = [n for n in ast.walk(_PFP[0])
             if isinstance(n, ast.For)
             and "enumerate(rows[:-1])" in ast.unparse(n.iter)]
ck("⚠️ the pairing loop is findable, so the pin below has a subject",
   len(_PAIR_FOR) == 1,
   "⛔ rule 67 — a check over an empty set proves nothing. found %d "
   "`for ... in enumerate(rows[:-1])` loop(s)" % len(_PAIR_FOR))
_PAIR_ROW = [t for t in ast.walk(_PAIR_FOR[0].target)
             if isinstance(t, ast.Tuple)] if _PAIR_FOR else []
ck("⛔ ...and the row IT unpacks carries exactly the five fields",
   bool(_PAIR_ROW) and len(_PAIR_ROW[-1].elts) == 5,
   
   "🔴 the other way an ordering decision could enter the derivation "
   "without touching the sort call at all")
ck("✅ ...while the row and the counters MAY carry it, and do",
   "driveNumber" in ast.unparse(_PFP[0])
   or "driveNumber" in ast.unparse(_CFB_AST),
   "⛔ THE HALF THAT STOPS THIS BECOMING THE OLD CHECK AGAIN. If nothing "
   "carries the field, nothing is measuring the live question — which "
   "is the state #75 left and task 44 exists to end.")

# ══════════════════════════════════════════════════════════════════════
section("6. ⚠️ AND THE PROSE AGREES WITH THE EVIDENCE (rule 249)")
# ══════════════════════════════════════════════════════════════════════
for _label, _txt in (("anomaly_pct", "%.3f" % _SNAP["anomaly_pct"]),
                     ("pairs", "{:,}".format(_SNAP["pairs"])),
                     ("negative", "{:,}".format(_SNAP["negative"])),
                     ("over_max", "{:,}".format(_SNAP["over_max"])),
                     ("coverage_median", "%.4f" % _SNAP["coverage_median"])):
    ck("⚠️ the report quotes the snapshot's %s (%s)" % (_label, _txt),
       _txt in _MD,
       "⛔ rule 249 — a report whose numbers do not match the artifact it "
       "rests on is a report that has quietly become a story. If the "
       "artifact changed, re-run the sim and rewrite the prose.")

ck("⚠️ the report names what it could NOT answer",
   "cannot be answered from stored data" in _MD and "playType" in _MD,
   "⛔ three of the brief's four questions are unanswerable from disk. A "
   "report that quietly drops them reads as though they were answered.")

note("H0 miss %.1f%% · winner %s at %.1f%% · runner-up %s at %.1f%%"
     % (100 * _h0_entry[2], _best_label[:22], 100 * _best_miss,
        _runner[0][:22] if _runner else "none",
        100 * _runner[2] if _runner else -1))


# ══════════════════════════════════════════════════════════════════════
section("7. 🔴🔴 THE COUNTERS ANSWER THE LIVE QUESTION, ON REAL ROWS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 #75 SHIPPED THE REMEDY AS A PREDICTION AND TOUCHED NOTHING, so
#    nothing computed these on live data and the question was
#    UNANSWERABLE rather than unanswered. These checks are what make the
#    next already-paid run answer it.
# ⛔ A COUNTER THAT READS THE SAME ON BOTH INPUTS IS MEASURING NOTHING,
#    so every one below is driven against a known-good feed AND against
#    the same feed broken in H1's exact shape.
import collections as _c                                    # noqa: E402

_FIX = json.load(gzip.open(FIXTURE, "rt", encoding="utf-8"))["plays"]
_dn_of, _seen = {}, _c.Counter()
_H1 = []
for _p in _FIX:
    _q = dict(_p)
    _gid, _did = _p.get("gameId"), _p.get("driveId")
    if (_gid, _did) not in _dn_of:
        _dn_of[(_gid, _did)] = len([k for k in _dn_of if k[0] == _gid])
    _seen[(_gid, _did)] += 1
    # H1 exactly: playNumber restarts at 1 in each drive, driveNumber is
    # the drive's ordinal in the game, everything else identical.
    _q["playNumber"] = _seen[(_gid, _did)]
    _q["driveNumber"] = _dn_of[(_gid, _did)]
    _H1.append(_q)
_H0 = [dict(_p, driveNumber=_dn_of[(_p.get("gameId"), _p.get("driveId"))])
       for _p in _FIX]

_q = lambda *a, **k: None


def _n(x, default=-1.0):
    """A counter that could not be computed must make a check FAIL, never
    DIE. ⛔ `[caught by driving driveNumber away, 2026-09-19]` an
    unguarded `abs(None - 0.506)` raised a TypeError and this file died
    with 29 checks run and the rest never reached — which `tcheck`
    correctly refuses to call a pass, but which reports nothing about the
    counter that actually broke. ⚠️ The sentinel is out of range for
    every bar here, so a missing figure reads as a failed comparison."""
    return default if x is None else x
_r0 = cfb.possession_from_plays(_H0, 2019, log=_q)[1]
_r1 = cfb.possession_from_plays(_H1, 2019, log=_q)[1]
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 `_H1X` — H1 WITH `driveNumber` REMOVED, AND IT IS THE DIAGNOSIS'S
#      SUBJECT NOW THAT THE REMEDY SHIPS.
# ══════════════════════════════════════════════════════════════════════
# Every check below about the FAULT used to read `_r1`. Under the new
# sort key H1 derives cleanly — which is the point of the change — so
# reading `_r1` would make each of them pass on a feed that no longer
# has the thing they exist to detect. That is vacuity, arriving through
# the front door.
# ✅ Stripping `driveNumber` reproduces the ORIGINAL condition exactly:
# the sort falls back on the drive-local playNumber and the clock runs
# backwards again — measured 33.134%, the same figure H1 scored before
# the remedy. The diagnosis keeps its subject; only the subject's name
# changes.
_H1X = [dict(_p, driveNumber=None) for _p in _H1]
_r1x = cfb.possession_from_plays(_H1X, 2019, log=_q)[1]

ck("⚠️ both feeds produced a report with the counters on it",
   _r0.get("pn_monotonic_game_pct") is not None
   and _r1.get("pn_monotonic_game_pct") is not None,
   "⛔ rule 67 — a missing counter would make every comparison below "
   "vacuous. H0=%s H1=%s" % (_r0.get("pn_monotonic_game_pct"),
                             _r1.get("pn_monotonic_game_pct")))
# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE REMEDY, DRIVEN ON THE COMMITTED FIXTURE — NOT PROJECTED.
# ══════════════════════════════════════════════════════════════════════
# `_H1` is the live feed's exact shape: playNumber restarts at 1 in each
# drive, driveNumber is the drive's ordinal in the game. Measured here,
# offline, no CFBD call:
#
#     H0 (well ordered)          anomaly 0.506%   usable True
#     H1 (drive-local pn)        anomaly 33.134%  usable False  <- before
#     H1 under (dn, pn)          anomaly 0.506%   usable True   <- after
#
# ⚠️ 0.506% is the CONTROL's own rate. The remedy does not merely get
# under the 2.0 bar — it lands on the well-ordered feed's number to the
# digit, which is what says the ordering was the whole defect.
# ⛔ AND IT FAILS SAFE. If a season's feed does not support the new key
# the anomaly stays over the bar and the derivation refuses, exactly as
# it does today. It cannot ship a wrong table.
_rem_pay, _rem = cfb.possession_from_plays(_H1, 2019, log=_q)
ck("🔴🔴 the drive-local feed now DERIVES, where today it refuses",
   _rem_pay is not None and _rem.get("usable") is True,
   "⛔ THIS IS THE WHOLE CHANGE. Before it: 33.134%% anomalous and "
   "`writing NOTHING`. error=%s" % str(_rem.get("error"))[:120])
ck("🔴 ...at the CONTROL's own anomaly rate, to the digit",
   abs(_n(_rem.get("anomaly_pct")) - _n(_r0.get("anomaly_pct"))) < 0.001,
   "⛔ under the bar is not the claim; landing on the well-ordered "
   "feed's number is. H1=%s H0=%s"
   % (_rem.get("anomaly_pct"), _r0.get("anomaly_pct")))
ck("⚠️ ...and the well-ordered feed is unchanged by the new key",
   _r0.get("usable") is True and _n(_r0.get("anomaly_pct")) < 2.0,
   "⛔ a remedy that breaks the feed that already worked is not a "
   "remedy. H0 anomaly=%s usable=%s"
   % (_r0.get("anomaly_pct"), _r0.get("usable")))
# ⚠️ `_H1X` ALREADY IS THIS FEED — built above and read by every
#    diagnosis check below. ⛔ A second copy under a second name is two
#    readers of one fixture (rule 66), and the one that drifts is the one
#    nobody is looking at.
_nd_pay, _nd = cfb.possession_from_plays(_H1X, 2019, log=_q)
ck("⛔ ...and a feed with NO driveNumber still refuses, it does not guess",
   _nd_pay is None,
   "🔴 THE FAIL-SAFE HALF. With the ordering field absent the rows fall "
   "back on playNumber, the anomaly stays over the bar and the table is "
   "not written. §6 says UNAVAILABLE, which is today's state and the "
   "correct one. anomaly=%s" % _nd.get("anomaly_pct"))

ck("🔴🔴 `pn_monotonic_game_pct` COLLAPSES when playNumber goes drive-local",
   _n(_r0["pn_monotonic_game_pct"]) >= cfb.ORDER_HI
   and _n(_r1["pn_monotonic_game_pct"], 999.0) <= cfb.ORDER_LO,
   "⛔ THE COUNTER THE WHOLE DIAGNOSIS TURNS ON. If it read the same on "
   "an ordered and a drive-local feed it would be measuring nothing. "
   "H0=%s H1=%s" % (_r0["pn_monotonic_game_pct"],
                    _r1["pn_monotonic_game_pct"]))
ck("🔴 ...while `pn_monotonic_drive_pct` stays high on BOTH",
   _n(_r0["pn_monotonic_drive_pct"]) >= cfb.ORDER_HI
   and _n(_r1["pn_monotonic_drive_pct"]) >= cfb.ORDER_HI,
   "⛔ that pair — low per game, high per drive — IS the signature of a "
   "drive-local ordinal, and it is what separates H1 from plain "
   "disorder. H0=%s H1=%s" % (_r0["pn_monotonic_drive_pct"],
                              _r1["pn_monotonic_drive_pct"]))
# 🔴 ~~"the remedy's PROJECTED anomaly rate recovers the true one"~~ —
#    THE PROJECTION IS NOW THE REALISATION, so the question changed
#    under the answer. `dn_pn_anomaly_pct` existed to say what the rate
#    WOULD be under (driveNumber, playNumber); the derivation now sorts
#    by exactly that, so on any feed carrying the field the two must be
#    THE SAME NUMBER. ⛔ That is not a weaker question — it is the one
#    that keeps the counter honest now that it can be checked against a
#    realised figure instead of a hypothetical.
# ⚠️ `_r1x` cannot answer it at all: with driveNumber stripped the
#    projection has no buckets to read and is correctly None, which is
#    why this check reads `_r1` and the fault checks read `_r1x`.
ck("✅ the projection and the realised rate are the same number now",
   _r1["dn_pn_anomaly_pct"] is not None
   and abs(_r1["dn_pn_anomaly_pct"] - _n(_r1["anomaly_pct"])) < 0.01
   and abs(_n(_r1["anomaly_pct"]) - _n(_r0["anomaly_pct"])) < 0.01,
   "⛔ `dn_pn_anomaly_pct` is computed the same way `anomaly_pct` is, "
   "and the derivation now sorts by the same key — so a difference "
   "between them means one of the two is measuring something else. "
   "realised=%s projected=%s control=%s"
   % (_r1["anomaly_pct"], _r1["dn_pn_anomaly_pct"], _r0["anomaly_pct"]))
ck("⚠️ ...and with the field stripped the projection is None, not zero",
   _r1x["dn_pn_anomaly_pct"] is None,
   "⛔ a projection over zero readable buckets must report that it "
   "could not look. A 0.0 there would read as a perfect feed. got %s"
   % _r1x["dn_pn_anomaly_pct"])
ck("🔴 the backwards-game share separates feed-wide from outliers",
   _n(_r0["negative_games_share"], 999.0) < 0.5
   <= _n(_r1x["negative_games_share"]),
   "⛔ AND IT COUNTS BACKWARDS PAIRS ONLY. Built on `over_max` too it "
   "reads 0.498 on the KNOWN-GOOD fixture — long gaps are timeouts and "
   "drive ends, not ordering faults — which is exactly the bar it has "
   "to sit far from. H0=%s H1=%s"
   % (_r0["negative_games_share"], _r1x["negative_games_share"]))

section("8. ⛔ AND THE DERIVATION IS UNCHANGED BY ALL OF IT")
# 🔴 THE COUNTERS GATE NOTHING. Sam reads them and decides whether the
#    sort ships; that is a separate task.
ck("⛔ the ordered feed is still USABLE and still scores 0.506",
   _r0["usable"] is True and _r0["anomaly_pct"] == 0.506,
   "🔴 the figure #75 recorded. If measuring had moved it, the "
   "derivation was touched. got usable=%s anomaly=%s"
   % (_r0["usable"], _r0["anomaly_pct"]))
ck("⛔ ...and a feed that STILL carries the fault still REFUSES",
   _r1x["usable"] is False and "ordering" in (_r1x.get("error") or ""),
   "🔴 THE FAIL-SAFE HALF. The remedy does not make the derivation "
   "credulous: strip the ordering field and it goes back to refusing, "
   "at the same 33.134%% it always scored. usable=%s error=%r"
   % (_r1x["usable"], (_r1x.get("error") or "")[:70]))
ck("⛔ the bars are untouched",
   cfb.CFB_ANOMALY_MAX_PCT == 2.0 and cfb._poss.COVERAGE_MIN == 0.90,
   "🔴 CLAUDE.md's one rule that matters most. anomaly=%s floor=%s"
   % (cfb.CFB_ANOMALY_MAX_PCT, cfb._poss.COVERAGE_MIN))

section("9. ⚠️ AN ABSENT `driveNumber` IS REPORTED, NEVER READ AS ZERO")
# ⛔ If CFBD omits the field on some rows, every figure above is measuring
#    a smaller population than it appears to. That is part of the answer.
_rn = cfb.possession_from_plays(_FIX, 2019, log=_q)[1]   # fixture has none
ck("🔴 a feed with NO driveNumber reports 0% presence, not a silent zero",
   _rn["dn_present_pct"] == 0.0 and _n(_rn["dn_rows"]) > 1000,
   "⛔ `p.get(\"driveNumber\")` returns None and None must never become "
   "0 in a sort key or a count. present=%s of %s rows"
   % (_rn["dn_present"], _rn["dn_rows"]))
ck("⛔ ...and the buckets it could not read are COUNTED, not dropped quietly",
   _n(_rn["dn_pn_buckets_skipped_no_drivenumber"]) > 1000
   and _rn["dn_pn_monotonic_game_pct"] is None,
   "🔴 a percentage over the buckets that happened to carry the field "
   "would look like an answer about the feed. skipped=%s pct=%s"
   % (_rn["dn_pn_buckets_skipped_no_drivenumber"],
      _rn["dn_pn_monotonic_game_pct"]))
ck("✅ and with the field present it IS read",
   _r0["dn_present_pct"] == 100.0
   and _n(_r0["dn_pn_buckets_read"]) > 1000,
   "⛔ the other half — a counter that never reads anything is not "
   "reporting absence, it is broken. present=%s read=%s"
   % (_r0["dn_present_pct"], _r0["dn_pn_buckets_read"]))

section("10. 🔴 THE READING IS A DECISION TABLE, NOT A NUMBER")
ck("🔴 a feed that still carries the fault reads H1 CONFIRMED",
   "H1 CONFIRMED" in _r1x["order_reading"]["verdict"],
   "⛔ a counter with no interpretation is a number nobody can act on. "
   "got %r" % _r1x["order_reading"]["verdict"])
ck("⛔ ...and the ordered feed reads NO FAULT rather than explaining one",
   "NO ORDERING FAULT" in _r0["order_reading"]["verdict"],
   "🔴 `_order_reading` asks 'is there a fault at all' FIRST, and it is "
   "called AFTER `anomaly_pct` exists. Called earlier it read None, "
   "`(None or 0) <= 2.0` was True, and it announced NO FAULT on a 33.1%% "
   "anomaly — confidently, in the artifact. got %r"
   % _r0["order_reading"]["verdict"])
ck("⚠️ every reading says what FOLLOWS, not just what it means",
   all(k in _r1x["order_reading"] for k in ("verdict", "means", "follows"))
   and len(_r1x["order_reading"]["follows"]) > 20,
   "⛔ the same rule the repo watcher was held to. got %s"
   % sorted(_r1x["order_reading"]))
