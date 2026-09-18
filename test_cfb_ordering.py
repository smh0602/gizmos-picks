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
ck("⛔ ...and cfb.py still does NOT use it — this PR diagnoses only",
   "driveNumber" not in io.open(os.path.join(ROOT, "cfb.py"),
                                encoding="utf-8").read(),
   "🔴 the brief says diagnose and stop, and a fixture cannot settle a "
   "question about a different distributor. If this fails because the "
   "fix shipped, DELETE THIS CHECK IN THAT PR and say so — do not leave "
   "it asserting a state the repo has deliberately left.")

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
