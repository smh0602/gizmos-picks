#!/usr/bin/env python3
"""test_prereg_gate.py — no test code before Sam approves the test.

`[added 2026-09-22 with research/t60r_spec.md]` CLAUDE.md rule 13: the
backtest direction rule "must be approved before anyone looks at
signal-vs-outcome data." The way someone looks is by writing the script
that computes it. So:

⛔ A spec in `research/<id>_spec.md` whose `Status:` line says PROPOSED
blocks every `<id>*.py` in the repo root and in `research/`. The block
lifts only when the line reads `APPROVED BY SAM <yyyy-mm-dd>`.

✅ THE CLASS, NOT ONE FILE: it applies to every spec that declares a
`Status:` line, not only T60R. ⚠️ Specs written before 2026-09-22 carry
no such line and are not covered; that is said here rather than implied.

🔴 AND ONCE SAM APPROVES ONE, THE RULE IS FROZEN. `[Sam, 2026-09-22:
"The rule is frozen once approved; weekly grading adds new games but
never changes the rule."]` ⛔ The approved sections are HASHED here. An
edit to them — a threshold nudged after a bad week, a bar relaxed — goes
red. Adding a season, or grading more games, touches neither.

It also recomputes T60R's power table, because a number written down is a
claim that can be wrong (rule 166).

# @vacuity a wrong figure in the bar table must not read as plausible
#   file: research/t60r_spec.md
#   find: | 1,000 | +5.0 pts (57.4%) | +3.9 pts (56.3%) |
#   with: | 1,000 | +4.0 pts (57.4%) | +3.9 pts (56.3%) |
"""
import glob
import hashlib
import os
import re
import shutil
import tempfile
from statistics import NormalDist

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))
APPROVED = re.compile(r"APPROVED BY SAM \d{4}-\d\d-\d\d")


def blocked(root):
    """Return [(spec, code file)] for every code file a PROPOSED spec forbids."""
    out = []
    for spec in sorted(glob.glob(os.path.join(root, "research", "*_spec.md"))):
        m = re.search(r"(?m)^Status:(.*)$", open(spec, encoding="utf-8").read())
        if not m or APPROVED.search(m.group(1)):
            continue
        tid = os.path.basename(spec)[:-len("_spec.md")]
        for d in (root, os.path.join(root, "research")):
            for py in sorted(glob.glob(os.path.join(d, tid + "*.py"))):
                out.append((os.path.basename(spec), os.path.relpath(py, root)))
    return out


_real = blocked(ROOT)
ck("🔴 no code exists for a pre-registered test Sam has not approved",
   not _real,
   "⛔ CLAUDE.md rule 13: the direction rule and the bar are approved "
   "BEFORE anyone computes signal-vs-outcome. Found: %r" % (_real,))

# ⚠️ PROVEN TO BITE, on a scratch tree, every run.
_tmp = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(_tmp, "research"))
    spec = os.path.join(_tmp, "research", "t99_spec.md")

    def _case(status, code):
        with open(spec, "w", encoding="utf-8") as f:
            f.write("# T99\n\nStatus: %s\n" % status)
        for p in glob.glob(os.path.join(_tmp, "*.py")) + \
                glob.glob(os.path.join(_tmp, "research", "*.py")):
            os.remove(p)
        for c in code:
            open(os.path.join(_tmp, c), "w").close()
        return blocked(_tmp)

    ck("⛔ ...it FAILS on a PROPOSED spec with code in the root",
       bool(_case("PROPOSED — NOT APPROVED BY SAM", ["t99.py"])))
    ck("⛔ ...and with code in research/",
       bool(_case("PROPOSED", ["research/t99_fit.py"])))
    ck("✅ ...it passes once Sam's dated approval is on the line",
       not _case("APPROVED BY SAM 2026-09-30", ["t99.py"]))
    ck("✅ ...and on a PROPOSED spec with no code yet",
       not _case("PROPOSED", []))
    ck("⛔ ...an approval with no date does not count",
       bool(_case("APPROVED BY SAM", ["t99.py"])))
finally:
    shutil.rmtree(_tmp)

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AN APPROVED RULE IS FROZEN, AND THE HASH IS WHAT MAKES THAT REAL.
# ══════════════════════════════════════════════════════════════════════
# ⛔ The frozen region is section 2 (the direction rule) through the end
#    of section 3a (the bar and how it is reported) — everything Sam
#    approved. The prose around it, the changelog and section 4's build
#    steps are NOT frozen and may be edited freely.
# ⚠️ If this fails, the answer is NEVER to paste the new hash in. It is
#    to put the rule back, or to register a NEW test with a new id.
FROZEN = {
    "t60r_spec.md": "a65d815a376c9f5b4e299ecebcaa6f2bdbe890b5b6fa879eef6ff15b9226ea6e",
    # [Sam, 2026-09-23] rule in section 2; section 3 fixed before any result.
    # ~~3bcac448819596f2e82f01b823e464cb8b1c3ba70fb65c5bf870a9f2ecefad43~~
    # RE-FROZEN 2026-09-23 ON SAM'S APPROVAL: the paired test tightened to
    # cluster by pitcher (spec 2a). STRICTER, made after the first run had
    # already failed — recorded in the spec's changelog. ⛔ This entry moved
    # because SAM changed the rule, not because a result was seen.
    "mlb_refit_spec.md": "25d526a42b119f08f6d2e4183a535964c8db5bde364428f02c61beed1a3bb1c0",
    # [Sam, 2026-09-24] rule in section 2, pre-registered before any result;
    # section 3 fixed by Claude before any scoring code existed.
    "fb_model_lambda_spec.md": "0d04a78d959d75097a24196e282d6aa48fed5455fdbfb00e9952fde67d54ca8b",
    # [Sam, 2026-09-24] rule in section 2 before any scoring; section 3
    # fixed by Claude before any scoring code existed.
    "fb_card_calibration_spec.md": "73e83ec67ddecc7df3d229c29d5423e238ced75ffc31990426433fc737e89bda",
    # [Sam, 2026-09-24] ship rule in section 2 before any result; the
    # formula and scoring in section 3 fixed by Claude before any scoring.
    "fb_card_fix_spec.md": "8162387a90aaae4228a661e898cbe72c9e8cd3ee4d6ed2ebbbfcfed7f05715a1",
    # [Sam, 2026-09-24] ledger, no cap and verdict rules in section 2;
    # definitions in section 3 fixed by Claude before any scoring code.
    "fb_model_live_spec.md": "04815a773c9986afa165ff7b07a7a0d96aed046e08d091cfb10b24c6f94af398",
    # [Sam, 2026-09-25] audit proposals C and D in section 2; the bar in
    # section 3 fixed by Claude before any scoring code existed.
    "mlb_pitcher_cal_spec.md": "4b8a9a77f13cdab57a88340f70399f189c2b9b7b00fe63bee7b8f38036935e12",
}


def frozen_region(text):
    """Section 2 through the end of 3a — what Sam approved."""
    i = text.find("\n## 2. ")
    j = text.find("\n## 4. ")
    return text[i:j] if i >= 0 and j > i else None


for _spec_path in sorted(glob.glob(os.path.join(ROOT, "research", "*_spec.md"))):
    _name = os.path.basename(_spec_path)
    _txt = open(_spec_path, encoding="utf-8").read()
    _m = re.search(r"(?m)^Status:(.*)$", _txt)
    if not (_m and APPROVED.search(_m.group(1))):
        continue
    _reg = frozen_region(_txt)
    ck("🔴 %s marks the sections Sam approved" % _name, _reg is not None,
       "⛔ expected `## 2. ` and `## 4. ` headings around the frozen rule")
    if _reg is None:
        continue
    _got = hashlib.sha256(_reg.encode("utf-8")).hexdigest()
    ck("🔴🔴 %s's approved rule and bar are UNCHANGED since approval" % _name,
       FROZEN.get(_name) == _got,
       "⛔ Sam froze this on approval. Do NOT paste the new hash in — put "
       "the rule back, or register a new test with a new id. want %s, got "
       "%s" % (FROZEN.get(_name), _got))

# 🔴 T60R's power table, recomputed from the formula T60 used.
_spec = os.path.join(ROOT, "research", "t60r_spec.md")
if os.path.exists(_spec):
    _z = NormalDist().inv_cdf
    P0 = 0.5238

    def n_for(p1, a, pw=0.8):
        return ((_z(1 - a) * (P0 * (1 - P0)) ** .5
                 + _z(pw) * (p1 * (1 - p1)) ** .5) / (p1 - P0)) ** 2

    def edge_at(n, a):
        lo, hi = 1e-4, 0.3
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if n_for(P0 + mid, a) > n else (lo, mid)
        return hi

    rows = re.findall(r"(?m)^\| ([\d,]+) \| \+([\d.]+) pts \(([\d.]+)%\) "
                      r"\| \+([\d.]+) pts \(([\d.]+)%\) \|$",
                      open(_spec, encoding="utf-8").read())
    ck("🔴 T60R's power table is present and machine-readable", len(rows) >= 4,
       "found %d rows" % len(rows))
    bad = []
    for n, e1, h1, e5, h5 in rows:
        n = int(n.replace(",", ""))
        for a, e, h in ((0.01, e1, h1), (0.05, e5, h5)):
            got = edge_at(n, a)
            if (abs(round(got * 100, 1) - float(e)) > 0.051
                    or abs(round((P0 + got) * 100, 1) - float(h)) > 0.051):
                bad.append((n, a, e, round(got * 100, 2)))
    ck("🔴 ...and every figure in it matches the formula", not bad,
       "(n, alpha, written, computed): %r" % bad)
    ck("🔴 ...and T60's registered n (2,774 at +3 pts, α=0.01) comes out, to within 1",
       abs(n_for(P0 + 0.03, 0.01) - 2774) < 1)
else:
    note("⚪ research/t60r_spec.md is not in this tree; power table not checked.")
