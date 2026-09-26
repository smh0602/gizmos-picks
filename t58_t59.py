#!/usr/bin/env python3
"""
T58 AND T59 — THE TWO OWED TESTS, ACCUMULATING THEMSELVES.

🔒 BOTH SPECIFICATIONS ARE REPRODUCED VERBATIM FROM `claude/owed-tests.md`
so that running them cannot quietly become re-choosing them:

  T58  predictor: side in {over, under} on NFL player props
       PASS: over-minus-under gap <= -15 points AND p < 0.01 two-sided
       VOID: if CFB develops the same gap beyond +/-10 points
  T59  predictor: stated confidence, split at 60
       PASS: >=60 band beats <60 band by >= 10 points AND p < 0.01
       VOID: if either band holds fewer than 40 fresh rows
  BOTH sample: FRESH rows only, published AFTER 2026-09-15.
       n >= 120 fresh graded NFL rows across >= 3 distinct NFL WEEKS.

════════════════════════════════════════════════════════════════════════
⛔⛔ UNTIL BOTH MINIMUMS ARE MET THIS REPORTS PROGRESS ONLY AND NO
    STATISTIC. NOT FOR NFL AND NOT FOR CFB.
════════════════════════════════════════════════════════════════════════
No gap, no p-value, no win rate, no "currently trending". **A
pre-registration you have been watching is not a pre-registration** — if
the number is on screen every morning, the decision to keep waiting stops
being neutral, and the bar starts being something you can feel yourself
approaching. That is choosing the cutoff after seeing the data, arriving
one step earlier and wearing a progress bar.

⚠️ THE CFB SILENCE IS PART OF THE TEST, NOT POLITENESS. T58's VOID
condition is a statement about CFB, so CFB is the CONTROL. Computing it
early is peeking at the control, which is the same offence as peeking at
the treatment and is easier to talk yourself into.

✅ WHAT MAY BE PRINTED UNDER THE BAR: fresh n, distinct weeks so far,
rows per band, and how far each is from its bar. Nothing else. `STAT_WORDS`
below is the list this file refuses to emit, and `test_t58_t59.py` drives
the real renderer against the real record to prove none of them appear.

🔴 AND THE SAMPLE ITSELF IS GUARDED. If the fresh count ever DROPS between
runs — a rolled record window, an advanced `record_from`, a regrade that
dropped rows — that is a FINDING, not a smaller number. A sample that
quietly shrinks is how a test gets answered on rows nobody chose, and
nothing else in this repo would notice.

⚠️ THE PRIOR OBSERVATION LIVES IN THE ISSUE BODY, in a machine-readable
marker, the same idiom as `<!-- CRON TOTAL: N -->` in CLAUDE.md. ⛔ NOT in
a file this job would have to commit: this watcher has `contents: read`,
and a best-effort push that silently fails is a shrink guard that
silently stops guarding. ⛔ And NOT in the collector either — see the
note on T54 in the PR: `t54.py`'s own counter is wired into `fb-record`,
a mode no cron fires, so it has never written its file once.
"""
import argparse
import glob
import gzip
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════
# 🔒 THE REGISTER. ⛔ NOT ONE OF THESE MAY MOVE AFTER THE FIRST FRESH ROW.
# ══════════════════════════════════════════════════════════════════════
FRESH_AFTER = "2026-09-15"   # ⛔ STRICTLY after. 09-15 itself is NOT fresh.
MIN_FRESH = 120              # fresh graded NFL rows
MIN_WEEKS = 3                # distinct NFL weeks

T58_GAP = -15.0              # over-minus-under, percentage points
T58_P = 0.01                 # two-sided
T58_VOID_CFB = 10.0          # |CFB over-minus-under| beyond this -> VOID

T59_SPLIT = 60               # stated confidence, split at 60
T59_GAP = 10.0               # >=60 band must beat <60 by this much
T59_P = 0.01
T59_MIN_BAND = 40            # either band under this -> VOID

# ⛔ THE WORDS THIS FILE REFUSES TO PRINT BEFORE THE BAR IS MET. A count
#    of rows is not a statistic; a rate, a gap or a p-value is. ⚠️ `%` is
#    on the list deliberately — progress needs no percentage at all, so
#    any percent sign in a progress report is a number that escaped.
STAT_WORDS = ("%", "p=", "p<", "gap", "hit rate", "win rate", "trend",
              "over-minus-under", "points", "z=", "delivered", "beats")

MARKER = "T58T59-STATE"
_MARKER_RE = re.compile(r"<!--\s*" + MARKER + r"\s*(\{.*?\})\s*-->", re.S)


# ─────────────────────────────────────────────── the sample
def week_map(root=ROOT):
    """ET date -> (season, week), from the NFL schedule the collector stores.

    🔴 THE LEAGUE'S OWN ANSWER, NOT A RULE I INVENTED. "3 distinct NFL
    weeks" is part of a fixed specification, so deriving a week from the
    calendar — Thursday-to-Wednesday, ISO week, anything — would be
    choosing what the spec meant after the fact. `schedule-<season>.json.gz`
    carries `week` per game and `start` in ET.
    ⚠️ (season, week), never the bare week: week 3 of two seasons is two
    weeks, and this test will outlive one season if the slates are thin.
    ⚠️ VERIFIED, not assumed `[2026-09-16]`: 121 mapped dates, no date
    carrying two weeks, and every one of the 125 NFL graded rows resolves.
    """
    out = {}
    for p in sorted(glob.glob(os.path.join(root, "data", "nfl", "latest",
                                           "schedule-*.json.gz"))):
        try:
            j = json.load(gzip.open(p, "rt"))
        except Exception:
            continue
        season = j.get("season")
        for g in j.get("games") or []:
            d = (g.get("start") or "")[:10]
            if d and g.get("week") is not None:
                out[d] = (season, g["week"])
    return out


def et_date(commence):
    """The ET calendar date of a kickoff. ⛔ IMPORTED, not re-implemented.

    `card_fb.et_date` is the repo's one answer to this and it already
    carries the reasoning (a Saturday 8pm ET kickoff is 00:00Z Sunday).
    ⚠️ A second copy would be a second thing to drift — rule 66.
    """
    import card_fb
    return card_fb.et_date(commence)


def fresh_rows(root=ROOT, league="nfl"):
    """Graded rows PUBLISHED AFTER `FRESH_AFTER`. -> (rows, unreadable)

    ⛔ `>`, NEVER `>=`. The register says "published AFTER 2026-09-15", so
    a row dated 09-15 is not fresh. One character decides whether a test
    is answered on the rows it pre-registered or on the rows that were
    already there, and `test_t58_t59.py` drives both sides of it.
    ⛔ GRADED: `won is None` is a void, an unresolved row or an ungradeable
    market, and the register excludes those from every denominator.
    """
    p = os.path.join(root, "data", league, "latest", "record-detail.json.gz")
    try:
        d = json.load(gzip.open(p, "rt"))
    except Exception as e:
        return [], "%s: %s" % (p, e)
    out = []
    for day, rows in (d.get("days") or {}).items():
        if not (day > FRESH_AFTER):
            continue
        for r in rows or []:
            if r.get("won") is None:
                continue
            out.append(dict(r, _day=day))
    return out, None


def weeks_of(rows, wmap):
    """-> (distinct (season, week) set, rows whose week could not be found).

    ⚠️ AN UNRESOLVED WEEK IS COUNTED AND SAID OUT LOUD. It still counts
    toward `n` — it is a fresh graded NFL row — but it contributes no week,
    and a silent unknown is the shape of every calibration bug in this
    repo.
    """
    seen, lost = set(), 0
    for r in rows:
        w = wmap.get(et_date(r.get("commence")))
        if w is None:
            lost += 1
        else:
            seen.add(w)
    return seen, lost


# ─────────────────────────────────────────────── the statistics
def two_prop(w1, n1, w2, n2):
    """Pooled two-proportion z-test. -> (diff in points, z, two-sided p).

    🔒 FIXED HERE, BEFORE ANY FRESH ROW EXISTS. Both registers say
    "p < 0.01" of a comparison between two groups, and the pooled
    two-proportion z is the standard reading of that. ⛔ Writing it down
    now is the point: choosing the test after seeing the split is the
    same offence as choosing the threshold.
    """
    if n1 <= 0 or n2 <= 0:
        return None
    p1, p2 = float(w1) / n1, float(w2) / n2
    pool = float(w1 + w2) / (n1 + n2)
    se = math.sqrt(pool * (1.0 - pool) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return (100.0 * (p1 - p2), None, None)
    z = (p1 - p2) / se
    return (100.0 * (p1 - p2), z, math.erfc(abs(z) / math.sqrt(2.0)))


def _split(rows, pred):
    yes = [r for r in rows if pred(r)]
    no = [r for r in rows if not pred(r)]
    return (sum(1 for r in yes if r["won"]), len(yes),
            sum(1 for r in no if r["won"]), len(no))


def t58(nfl, cfb):
    """⛔ CALLED ONLY WHEN THE BAR IS MET. See the module header."""
    ow, on, uw, un = _split(nfl, lambda r: r.get("side") == "over")
    res = {"test": "T58", "over_n": on, "under_n": un}
    cw, cn, cuw, cun = _split(cfb, lambda r: r.get("side") == "over")
    cfb_st = two_prop(cw, cn, cuw, cun)
    res["cfb_gap"] = None if cfb_st is None else round(cfb_st[0], 2)
    # ⚠️ VOID IS TESTED FIRST. It is a condition on the CONTROL, so a
    #    result that the control invalidates was never a result.
    if cfb_st is not None and abs(cfb_st[0]) > T58_VOID_CFB:
        res["verdict"] = "VOID"
        res["why"] = ("CFB developed the same asymmetry — %+.1f points "
                      "over %d over / %d under rows, beyond the +/-%.0f "
                      "the register voids on. A split that shows up in "
                      "both leagues is not an NFL finding."
                      % (cfb_st[0], cn, cun, T58_VOID_CFB))
        return res
    st = two_prop(ow, on, uw, un)
    if st is None:
        res["verdict"] = "VOID"
        res["why"] = ("one side has no fresh rows (%d over, %d under), so "
                      "the comparison the register names does not exist"
                      % (on, un))
        return res
    d, z, p = st
    res.update({"gap": round(d, 2), "p": p})
    if d <= T58_GAP and p is not None and p < T58_P:
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
    res["why"] = ("over %d/%d vs under %d/%d — %+.1f points, p=%.5f "
                  "against a bar of <= %.0f points and p < %.2f"
                  % (ow, on, uw, un, d, -1.0 if p is None else p,
                     T58_GAP, T58_P))
    return res


def t59(nfl):
    """⛔ CALLED ONLY WHEN THE BAR IS MET. See the module header."""
    hw, hn, lw, ln = _split(nfl, lambda r: (r.get("confidence") or 0)
                            >= T59_SPLIT)
    res = {"test": "T59", "high_n": hn, "low_n": ln}
    if hn < T59_MIN_BAND or ln < T59_MIN_BAND:
        res["verdict"] = "VOID"
        res["why"] = ("the >=%d band holds %d fresh rows and the <%d band "
                      "%d; the register voids below %d in either."
                      % (T59_SPLIT, hn, T59_SPLIT, ln, T59_MIN_BAND))
        return res
    d, z, p = two_prop(hw, hn, lw, ln)
    res.update({"gap": round(d, 2), "p": p})
    if d >= T59_GAP and p is not None and p < T59_P:
        res["verdict"] = "PASS"
    else:
        res["verdict"] = "FAIL"
    res["why"] = (">=%d band %d/%d vs <%d band %d/%d — %+.1f points, "
                  "p=%.5f against a bar of >= %.0f points and p < %.2f"
                  % (T59_SPLIT, hw, hn, T59_SPLIT, lw, ln, d,
                     -1.0 if p is None else p, T59_GAP, T59_P))
    return res


# ─────────────────────────────────────────────── the run
def prior_of(text):
    """The previous observation, out of the last issue body. -> dict or None."""
    m = _MARKER_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def run(root=ROOT, prior=None):
    nfl, bad_nfl = fresh_rows(root, "nfl")
    cfb, bad_cfb = fresh_rows(root, "ncaaf")
    if bad_nfl or bad_cfb:
        return {"state": "UNREADABLE",
                "why": "; ".join(x for x in (bad_nfl, bad_cfb) if x)}

    wmap = week_map(root)
    weeks, lost = weeks_of(nfl, wmap)
    high = [r for r in nfl if (r.get("confidence") or 0) >= T59_SPLIT]
    rep = {
        "state": "PROGRESS", "fresh_nfl": len(nfl), "fresh_cfb": len(cfb),
        "weeks": len(weeks), "weeks_seen": sorted("%s w%s" % w for w in weeks),
        "week_unresolved": lost,
        "band_high": len(high), "band_low": len(nfl) - len(high),
        "need_rows": max(0, MIN_FRESH - len(nfl)),
        "need_weeks": max(0, MIN_WEEKS - len(weeks)),
        "fresh_after": FRESH_AFTER,
    }

    # 🔴 THE SAMPLE GUARD, BEFORE ANYTHING ELSE LOOKS AT THE SAMPLE.
    was = (prior or {}).get("fresh_nfl")
    rep["prior_fresh_nfl"] = was
    if isinstance(was, int) and len(nfl) < was:
        rep["state"] = "SHRANK"
        rep["why"] = ("the fresh NFL sample FELL from %d rows to %d. ⛔ A "
                      "pre-registered sample does not get smaller on its "
                      "own — a rolled record window, an advanced "
                      "`record_from` or a regrade dropped rows the test "
                      "was going to be answered on. Find out which BEFORE "
                      "the bar is met." % (was, len(nfl)))
        return rep

    # ⛔ THE BAR. Nothing below this line is computed unless BOTH minimums
    #    are met — not for NFL and not for CFB.
    if len(nfl) < MIN_FRESH or len(weeks) < MIN_WEEKS:
        rep["why"] = ("%d of %d fresh graded NFL rows, across %d of %d "
                      "distinct NFL weeks."
                      % (len(nfl), MIN_FRESH, len(weeks), MIN_WEEKS))
        return rep

    rep["state"] = "ANSWERED"
    rep["t58"] = t58(nfl, cfb)
    rep["t59"] = t59(nfl)
    rep["why"] = ("the bar is met: %d fresh graded NFL rows across %d "
                  "distinct NFL weeks. Both tests computed ONCE, against "
                  "the thresholds fixed before any of these rows existed."
                  % (len(nfl), len(weeks)))
    return rep


# 🔴 A COUNTER SAYS SO, FOR SELF-REPAIR TRIAGE. `[2026-09-26]` Issue #42
#    (this file's) was handed to the repair agent on every pass of 09-24/25
#    and five of them ran out of turns looking for a defect that does not
#    exist. PROGRESS and ANSWERED are counters; SHRANK is a finding (rows
#    disappeared) and UNREADABLE says nothing, so both stay in the queue.
from self_repair import COUNTER  # noqa: E402  ⛔ one copy (self_repair.py)


def marker(rep):
    keep = ("fresh_nfl", "fresh_cfb", "weeks", "band_high", "band_low")
    return "<!-- %s %s -->" % (MARKER, json.dumps(
        {k: rep[k] for k in keep if k in rep}, sort_keys=True))


def render(rep):
    o = []
    if rep["state"] == "UNREADABLE":
        o.append("⚠️ **COULD NOT LOOK** — %s\n" % rep["why"])
        o.append("_\"I could not read the record\" is not \"the sample is "
                 "fine\", and it never closes this issue._")
        return "\n".join(o)

    if rep["state"] == "SHRANK":
        o.append("🔴🔴 **THE PRE-REGISTERED SAMPLE SHRANK.**\n")
        o.append(rep["why"])
        o.append("")
        o.append("⛔ **Do not re-baseline this away.** The fix is to find "
                 "what removed the rows, not to write the smaller number "
                 "down as the new normal.")
        o.append("")
        o.append(marker(rep))
        return "\n".join(o)

    if rep["state"] == "ANSWERED":
        o.append("# ✅ THE BAR IS MET — T58 AND T59 ARE ANSWERED\n")
        o.append(rep["why"] + "\n")
        for k in ("t58", "t59"):
            t = rep[k]
            o.append("## %s — **%s**\n" % (t["test"], t["verdict"]))
            o.append(t["why"] + "\n")
        o.append("⛔ **These thresholds were fixed before any of these "
                 "rows existed and are not re-decided now.** Re-running "
                 "with a different bar, a different split or a different "
                 "test is the one thing the register exists to stop.")
        o.append("")
        o.append("_This issue closes itself here: the owed test is no "
                 "longer owed. The verdict above is the record of it._")
        o.append("")
        o.append(marker(rep))
        o.append(COUNTER)      # ANSWERED: it closes itself; nothing to repair
        return "\n".join(o)

    # ── PROGRESS. ⛔ COUNTS ONLY. See STAT_WORDS and the module header.
    o.append("**Two owed tests are accumulating. Neither can be read "
             "yet.**\n")
    o.append("| | so far | needed |")
    o.append("|---|---|---|")
    o.append("| fresh graded NFL rows | %d | %d |"
             % (rep["fresh_nfl"], MIN_FRESH))
    o.append("| distinct NFL weeks | %d | %d |" % (rep["weeks"], MIN_WEEKS))
    o.append("| rows in the 60-and-over band | %d | %d |"
             % (rep["band_high"], T59_MIN_BAND))
    o.append("| rows in the under-60 band | %d | %d |"
             % (rep["band_low"], T59_MIN_BAND))
    o.append("")
    o.append("Still needed: **%d** more rows and **%d** more weeks."
             % (rep["need_rows"], rep["need_weeks"]))
    if rep["weeks_seen"]:
        o.append("Weeks seen: %s." % ", ".join(rep["weeks_seen"]))
    if rep["week_unresolved"]:
        o.append("⚠️ **%d fresh row(s) could not be matched to an NFL "
                 "week** from the stored schedule. They count toward the "
                 "row total and toward no week." % rep["week_unresolved"])
    o.append("")
    o.append("⛔ **NO STATISTIC APPEARS ABOVE, AND THAT IS THE DESIGN.** "
             "Not for the NFL rows and not for the college ones — T58's "
             "void condition is a statement about college football, which "
             "makes it the control, and reading a control early is the "
             "same offence as reading the treatment early. A "
             "pre-registration you have been watching is not a "
             "pre-registration.")
    o.append("")
    o.append("_One issue, updated in place. It closes itself when the bar "
             "is met and both verdicts are in — until then this is a "
             "counter, not a finding. Football only; MLB is frozen and is "
             "never read here._")
    o.append("")
    o.append(marker(rep))
    o.append(COUNTER)          # PROGRESS: a counter, not a finding
    return "\n".join(o)


EXIT_PROGRESS, EXIT_SHRANK, EXIT_UNREADABLE, EXIT_ANSWERED = 0, 1, 2, 3


def verdict(rep):
    """The report -> the exit code. ⛔ NOTHING ELSE MAY DECIDE IT.

    ✅ Extracted for the same reason `runs_report.py` and `vacuity.py`
    extract theirs: a judgement inlined in `main()` is a judgement no test
    can drive, and that hole has been found in this repo twice.
    """
    return {"UNREADABLE": EXIT_UNREADABLE, "SHRANK": EXIT_SHRANK,
            "ANSWERED": EXIT_ANSWERED}.get(rep.get("state"), EXIT_PROGRESS)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--prior", help="file holding the last issue body")
    a = ap.parse_args(argv)
    prior = None
    if a.prior and os.path.exists(a.prior):
        prior = prior_of(open(a.prior, encoding="utf-8").read())
    rep = run(prior=prior)
    print(render(rep))
    return verdict(rep)


if __name__ == "__main__":
    sys.exit(main())
