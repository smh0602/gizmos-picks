#!/usr/bin/env python3
"""THE `/coaches` PROBE, AND THE CLASS IT BELONGS TO.

🔴 THE DEFECT CLASS IS NOT "/coaches MIGHT BE WRONG". It is **A PROBE
QUIETLY BECOMING A PRODUCT.** `probe_news` says it in the file already:
*"a probe that ships its own findings is not a probe -- it is an
unreviewed deploy."* Sam's work order says the same thing about this one:
*"PROBE ONLY, DO NOT BUILD ... do not wire it into §7."*

⚠️ **AND THE EXISTING GUARD FOR THAT CLASS HAS A HOLE THIS MODE FALLS
STRAIGHT THROUGH.** `test_parity.py` asserts that a DIAGNOSTIC mode
writes only a probe artifact -- but it iterates `DIAGNOSTIC & SCHED[lg]`,
the modes the **cron schedule** names. ⛔ `coaches-probe` HAS NO CRON ARM
ON PURPOSE (it is dispatched by hand, once), so it is in neither set and
`test_parity.py` covers exactly none of it. A hand-maintained set of two
strings was never going to notice a third.

✅ **SO SECTION 1 GUARDS THE CLASS AND DERIVES ITS OWN MEMBERSHIP**: every
`mode == "*-probe"` arm `collect.py` contains, cron or no cron, must write
only files whose name says "probe". That is strictly more than
`test_parity.py` asks, and it covers `news-probe` and `nfl-probe`, which
nothing checked before today.

✅ **SECTION 2 IS THE OTHER HALF, AS A RATCHET.** Writing only a report is
half the contract; the other half is that nothing READS one. The set of
files that read a probe artifact is measured, not listed, and must not
grow -- the same shape as the blind-set ceiling in `test_vacuity.py`.
⛔ If this fails because you wired a probe into a product, that is the
check working.

Sections 3-7 drive `cfb.coaches_probe` itself against stub payloads.

# @vacuity the stored artifact's annotation cannot be quietly dropped
#   file: data/ncaaf/latest/coaches-probe.json
#   find:    "corrected_value": true,
#   with:    "corrected_value": false,
#
# @vacuity a probe mode may write ONLY its own report
#   file: cfb.py
#   find: p = f"{OUT}/{COACHES_PROBE_FILE}"
#   with: p = f"{OUT}/coaches.json"
#
# @vacuity the one-call budget is COUNTED, not promised in a comment
#   file: cfb.py
#   find:         rows = _counted_get("/coaches", {"year": season})
#   with:         rows = _counted_get("/coaches", {"year": season}); _counted_get("/teams/fbs", {"year": season})
#
# @vacuity the FREE-tuple landmark must not be repeated in a comment
#   file: collect.py
#   find:     # ⚠️ FREE OF **ODDS** CREDITS, which is the only thing this tuple
#   with:     # ⚠️ FREE OF **ODDS** CREDITS (the FREE = ( tuple), which is this tuple
#
# @vacuity the mode is FREE of Odds credits, or a missing key kills it
#   file: collect.py
#   find:             "coaches-probe",
#   with:             # "coaches-probe",
#
# @vacuity ⛔ a 429 is the finding — the probe must NOT retry into 4 credits
#   file: cfb.py
#   find:     return get(path, params, tries=1)
#   with:     return get(path, params)
#
# @vacuity a start DATE is a start year — the miss the first run made
#   file: cfb.py
#   find: _DATE_KEYS = ("hireDate", "hire_date", "startDate", "start_date")
#   with: _DATE_KEYS = ()
#
# @vacuity a year that does not VARY cannot answer "new this season"
#   file: cfb.py
#   find:     varying = sorted(k for k, v in vals.items() if v["distinct"] > 1)
#   with:     varying = sorted(k for k, v in vals.items() if v["distinct"] > 0)
#
# @vacuity FBS coverage is read off disk, never bought with a second call
#   file: cfb.py
#   find:     names = set(j.get("teams") or {})
#   with:     names = set()
#
# @vacuity an HTTP error is evidence about the REQUEST, not about CFBD
#   file: cfb.py
#   find: f"evidence about THIS REQUEST — the key's tier, the year, the "
#   with: f"proof the endpoint is not available. "
#
# ⚠️ ONE LINE PER FIELD. `vacuity.declarations()` stops reading a block at
#    the first line that is not `key: value`, so a `find` spread over four
#    lines loses its `with` and the harness reports MALFORMED — which it
#    did, and which is the harness doing its job on me.
# @vacuity §7 wiring the probe in is caught by the reader ratchet
#   file: dossier_fb.py
#   find:          "open_gap": ("⛔ COACHING CHANGES HAVE NO SOURCE IN THIS "
#   with:          "open_gap": ("see coaches-probe.json ⛔ COACHING CHANGES HAVE NO SOURCE IN THIS "
#
# @vacuity the artifact says in itself that nothing has adopted it
#   file: cfb.py
#   find:         "not_adopted": ("⛔ §7 does not read this file and must not until "
#   with:         "_na": ("⛔ §7 does not read this file and must not until "
"""
import io
import json
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

SRC = io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE CLASS — EVERY `*-probe` MODE WRITES ONLY A REPORT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE MEMBERSHIP IS DISCOVERED, NOT LISTED. A list is what left
#    `coaches-probe` uncovered in `test_parity.py`, and rules 130/246 are
#    two earlier versions of the same mistake.
MODES = sorted(set(re.findall(r'mode == "([a-z0-9]+-probe)"', SRC)))
ck("every `*-probe` mode in collect.py is discovered, not listed",
   len(MODES) >= 4, "found: %s" % (MODES,))
ck("...and the mode this PR adds is one of them",
   "coaches-probe" in MODES, "MODES=%s" % (MODES,))

# ⛔ AND IT MUST BE ON THE **FREE** LIST. `FREE` decides one thing only:
#    whether a missing ODDS_API_KEY is fatal. `coaches-probe` never reads
#    that key, so leaving it off would kill the mode over a secret it does
#    not use -- and I only noticed because deleting the entry left this
#    file green at 51 checks. A contract nothing asserts is a comment.
import ast as _ast
_free = None
for _n in _ast.walk(_ast.parse(SRC)):
    if isinstance(_n, _ast.Assign) and any(
            isinstance(t, _ast.Name) and t.id == "FREE" for t in _n.targets):
        _free = [e.value for e in _ast.walk(_n.value)
                 if isinstance(e, _ast.Constant) and isinstance(e.value, str)]
        break
# 🔴🔴 AND THE LANDMARK MUST BE UNIQUE IN THE FILE. This is the guard for
#    the defect this PR caused: four separate test files locate that
#    tuple by searching collect.py for the eight characters that open its
#    assignment, and three of them then split on it. ⛔ A COMMENT THAT
#    REPEATS IT BECOMES THE FIRST MATCH — test_live_probe.py,
#    test_record_fb.py, test_drop16_fixes.py and test_team_directory.py
#    ALL went red at once on a collector that was correct.
# ⚠️ Guarding the CLASS is not available here without rewriting three
#    files this task does not own, so this guards the INSTANCE and says
#    so: the landmark those four depend on occurs exactly once.
#    ➡️ The standing fix is to give them one shared reader, the way
#    `wfroutes.py` and `jsblock.py` already do for the workflow and the
#    page (rule 117). That is a change for its own PR.
_LANDMARK = "FREE" + " = ("
ck("🔴 the landmark four test files search for occurs EXACTLY once",
   SRC.count(_LANDMARK) == 1,
   "⛔ a second occurrence — in a comment, in a docstring, anywhere — is "
   "read INSTEAD of the code by every one of them. found %d"
   % SRC.count(_LANDMARK))
ck("⚠️ the FREE tuple is PARSED, never string-matched near a landmark",
   _free is not None and len(_free) > 5, "parsed: %s" % (_free,))
ck("🔴 `coaches-probe` is on the FREE list — it spends CFBD, not Odds",
   "coaches-probe" in (_free or []),
   "⛔ off the list, a missing ODDS_API_KEY kills a mode that never reads "
   "it. FREE = %s" % (_free,))

# 🔴 `cfb-probe` IS THE ONE DECLARED EXCEPTION, AND THE EXCEPTION IS
#    CHECKED RATHER THAN TRUSTED. `test_parity.py` already says it: it is
#    "named like a probe and is not one -- it BUILDS THE TRENDS TABLES".
#    ⛔ So the exception must EARN itself: if `cfb-probe` ever stopped
#    writing product files, this line would be a stale excuse sitting in
#    a guard, and the check below turns that into a failure.
EXCEPT = {"cfb-probe": "builds the Trends tables; named like a probe, is not one"}


def _entry(arm):
    """The function the arm actually dispatches to.

    ⛔ NEVER DERIVED FROM THE MODE NAME — `test_parity.py` guessed
    `probe_live` from "live-probe" and went red on correct code. And
    never the FIRST call either: the `cfb-probe` arm opens with
    `_wait = _cfb_backoff_left()`, a back-off helper, and taking that
    would have made this check report on the wrong function entirely.
    ✅ When the arm imports a module, the dispatch is the call THROUGH
    that module's alias.
    """
    mod = re.search(r"import ([a-z_0-9]+) as (_[a-z_0-9]+)", arm)
    if mod:
        c = re.search(r"%s\.([a-z_][a-z_0-9]*)\(" % re.escape(mod.group(2)), arm)
        if c:
            return mod.group(1) + ".py", c.group(1)
        return mod.group(1) + ".py", None
    c = re.search(r"=\s*([a-z_][a-z_0-9]*)\(", arm)
    return "collect.py", (c.group(1) if c else None)


# 🔴 A WRITE SITE, NOT A PATH-SHAPED STRING. The first form of this check
#    swept every `f"{OUT}/..."` in the body and counted `teams.json` --
#    which the probe READS -- as something it writes. ⛔ It failed the
#    probe for reading a file, which is the "guard that fires on correct
#    code" failure `CLAUDE.md` names as the other half of the rule.
# ⚠️ EVERY PATTERN CAPTURES AN **EXPRESSION**, quotes included. The first
#    form captured the string's CONTENTS for `write(...)` and the bare
#    expression for `open(...)`, so `_resolve` -- which expects an
#    expression -- could not read either of the two collector probes and
#    called them unresolvable.
_WRITE_SITES = (
    # ⛔ `(?<![.\w])` OR THIS READS PROSE. `fh.write("--- {y} ---")` in the
    #    cfb back-fill report is a HANDLE write, not a path, and without
    #    the lookbehind nine lines of report text were being reported as
    #    nine files the mode writes.
    re.compile(r'(?<![.\w])write\(\s*(f?"[^"]+")'),   # collect.write(path, obj)
    re.compile(r'open\(\s*([^,]+?),\s*"w"'),          # open(x, "w")
    re.compile(r'gzip\.open\(\s*([^,]+?),\s*"wt"'),  # gzip.open(x, "wt")
)


def _code_only(src):
    """The slice with its `#` comments removed.

    🔴 A COMMENT IS NOT A WRITE SITE. `cfb.py` explains its own truncation
    behaviour with the words `with open(..., "w")` inside a comment, and
    the first form of this extractor read that as a fifth write whose
    path it then could not resolve. ⛔ A guard that reads prose is the
    same defect as a guard that matches nothing -- it is measuring the
    wrong text (rules 67, 244, 249).
    ⚠️ Quote-aware, because `"#"` inside a string is not a comment.
    """
    out = []
    for line in src.splitlines():
        q, i = None, 0
        while i < len(line):
            c = line[i]
            if q:
                if c == "\\":
                    i += 1
                elif c == q:
                    q = None
            elif c in "\"'":
                q = c
            elif c == "#":
                line = line[:i]
                break
            i += 1
        out.append(line)
    return "\n".join(out)


def _resolve(expr, slice_, whole):
    """Turn a write target into a filename. ⚠️ Returns None when it CANNOT,
    which is different from 'it writes nothing' and is treated as such.

    ⛔ THE ASSIGNMENT IS LOOKED UP IN THE FUNCTION THAT WROTE, NOT IN A
    CONCATENATION OF ALL OF THEM. The first form of this joined every
    helper into one string, and `_fbs_on_disk`'s `p = f"{OUT}/teams.json"`
    (a READ) resolved `_write_coaches_probe`'s own `p` -- reporting that
    the probe writes the FBS team list. A variable name is only unique
    inside its own scope.
    """
    expr = expr.strip()
    m = re.match(r'^f?"([^"]+)"$', expr)
    if not m:
        a = re.search(r'^\s*%s\s*=\s*(f?"[^"]+")' % re.escape(expr),
                      slice_, re.M)
        if not a:
            return None
        m = re.match(r'^f?"([^"]+)"$', a.group(1))
        if not m:
            return None
    path = m.group(1)
    leaf = path.rsplit("/", 1)[-1]
    c = re.match(r"^\{([A-Z_]+)\}$", leaf)
    if c:                       # a constant -- resolve to its literal
        lit = re.search(r'^%s = "([^"]+)"' % re.escape(c.group(1)), whole, re.M)
        return lit.group(1) if lit else None
    return leaf


def _writes_of(mode):
    """(where, write sites found, filenames written) for `mode`'s arm.

    ⛔ ZERO SITES AND AN UNRESOLVABLE SITE ARE DIFFERENT ANSWERS. `nfl-probe`
    genuinely writes nothing -- that is its documented contract -- and a
    check that cannot tell that from a broken extractor is asking the
    wrong question.
    """
    # ⛔ THE ARM ENDS AT THE NEXT ARM, NOT AT THE NEXT `elif`. `cfb-probe`
    #    has an `elif` INSIDE it (the back-off stand-down), so a
    #    non-greedy stop at the first `elif ` cut the arm off two lines in
    #    and lost `_cfb.probe(log)` entirely -- the extractor then
    #    reported it could not find the entry point at all.
    #    ✅ Anchor on the dispatch chain's own indentation.
    m = re.search(r'\n( +)elif mode == "%s"\s*:\s*\n(.*?)\n\1(?:elif |else:)'
                  % mode, SRC, re.S)
    if not m:
        return None, None, None
    arm = m.group(2)
    where, fname = _entry(arm)
    if not fname:
        return where, None, None
    whole = SRC if where == "collect.py" else io.open(
        os.path.join(ROOT, where), encoding="utf-8").read()
    i = whole.find("def %s(" % fname)
    if i < 0:
        return where, None, None
    # ⚠️ EACH BODY STAYS ITS OWN SLICE. Following delegation is required
    #    ("I found no write" is not "it writes nothing" when the write is
    #    one call away) -- merging the slices is not.
    slices = [whole[i:whole.find("\ndef ", i + 1)]]
    entry = slices[0]
    for h in sorted(set(re.findall(r"(_[a-z_0-9]+)\(", entry))):
        j = whole.find("def %s(" % h)
        if j >= 0:
            slices.append(whole[j:whole.find("\ndef ", j + 1)])
    script = re.search(r'\[sys\.executable, "([a-z_0-9]+\.py)"', entry)
    if script and os.path.exists(os.path.join(ROOT, script.group(1))):
        where += " -> " + script.group(1)
        slices.append(io.open(os.path.join(ROOT, script.group(1)),
                              encoding="utf-8").read())
    sites, names = 0, []
    for sl in map(_code_only, slices):
        for rx in _WRITE_SITES:
            for hit in rx.findall(sl):
                sites += 1
                names.append(_resolve(hit, sl, whole))
    return where, sites, names


_exception_earned = []
for m in MODES:
    where, sites, writes = _writes_of(m)
    ck("`%s`: its dispatch arm and its entry point were both found" % m,
       where is not None and sites is not None,
       "where=%s sites=%s" % (where, sites))
    if sites is None:
        continue
    unresolved = [w for w in writes if w is None]
    ck("⚠️ `%s`: every write site it has resolves to a filename" % m,
       not unresolved,
       "⛔ %d of %d write site(s) in %s could not be read. That is a "
       "BROKEN EXTRACTOR, not a clean mode, and it must not be allowed to "
       "look like one." % (len(unresolved), sites, where))
    named = [w for w in writes if w]
    if m in EXCEPT:
        _exception_earned.append((m, [w for w in named if "probe" not in w]))
        continue
    # ⛔ AND IT MAY NOT PASS ON AN EMPTY SET. `all()` over nothing is
    #    True, which is rule 67 exactly: a mode with one unreadable write
    #    site would sail through here while the site above reddens.
    ck("🔴 `%s` writes ONLY probe artifacts — %d site(s) in %s"
       % (m, sites, where),
       len(named) == sites and all("probe" in w for w in named),
       "⛔ a probe that writes a product file is an unreviewed deploy. "
       "writes: %s" % (named or "NOTHING — and %d write site(s) were "
                       "found, so that is measured" % sites))
    if sites == 0:
        # ✅ A PROBE THAT WRITES NOTHING AT ALL IS THE STRONGEST FORM OF
        #    THE CONTRACT, and it is stated rather than passed over in
        #    silence -- otherwise it is indistinguishable from a miss.
        note("`%s` has NO write site anywhere in %s — it answers and "
             "stops" % (m, where))

# ⛔ AND THE EXCEPTION MUST STILL BE TRUE. A declared exception nobody
#    re-checks is how a rule outlives its reason.
for m, product in _exception_earned:
    ck("⚠️ the `%s` exception is still EARNED, not just declared" % m,
       bool(product),
       "it is excepted because it %s — if it writes only probe files now, "
       "DELETE the exception rather than keeping a dead excuse. "
       "non-probe writes: %s" % (EXCEPT[m], product))


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 THE OTHER HALF — NOTHING READS A PROBE ARTIFACT (RATCHET)")
# ══════════════════════════════════════════════════════════════════════
# 🔴 WRITING ONLY A REPORT IS HALF THE CONTRACT. §7 could read
#    `coaches-probe.json` tomorrow and every check in section 1 would
#    still be green. ⛔ So the READERS are counted too.
# ⚠️ DERIVED, NOT LISTED, AND A RATCHET RATHER THAN A FIXED SET: the
#    number may go DOWN freely and going UP is a deliberate act with a
#    reason, the same shape as the blind-file ceiling in test_vacuity.py.
PROBE_ART = re.compile(r"[A-Za-z0-9_.-]*probe[A-Za-z0-9_.-]*\.json")
readers = {}
for fn in sorted(os.listdir(ROOT)):
    if not (fn.endswith(".py") or fn.endswith(".html") or fn.endswith(".js")):
        continue
    if fn.startswith("test_"):
        continue          # a test READING a probe artifact is its job
    txt = io.open(os.path.join(ROOT, fn), encoding="utf-8", errors="replace").read()
    hits = sorted(set(PROBE_ART.findall(txt)))
    if hits:
        readers[fn] = hits
note("files naming a probe artifact: %s" % (sorted(readers) or "none"))

# ⛔ A FILE THAT WRITES ITS OWN REPORT NAMES IT, AND THAT IS NOT A READ.
#    The distinction is the whole point, so it is made explicitly.
WRITERS = {"cfb.py", "collect.py", "liveprobe.py", "nfl.py"}
CEILING = 0      # ⬅ product-side readers. It may go DOWN. Never up silently.
product_readers = {k: v for k, v in readers.items() if k not in WRITERS}
ck("🔴🔴 NO PRODUCT FILE READS A PROBE ARTIFACT (%d against a ceiling of %d)"
   % (len(product_readers), CEILING),
   len(product_readers) <= CEILING,
   "⛔ IF THIS FAILS BECAUSE YOU WIRED A PROBE INTO A PRODUCT, THAT IS "
   "THE CHECK WORKING — a probe becoming a source is a decision Sam "
   "makes, not a diff. Offenders: %s" % (product_readers or "none"))
ck("...and §7 in particular does not read the coaches report",
   "coaches-probe" not in io.open(
       os.path.join(ROOT, "dossier_fb.py"), encoding="utf-8").read(),
   "the dossier still records coaching changes as MISSING")


# ══════════════════════════════════════════════════════════════════════
section("3. THE PROBE ITSELF — ONE CALL, ONE FILE")
# ══════════════════════════════════════════════════════════════════════
import cfb


def drive(payload, teams=None, season=2026, raise_with=None):
    """Run the probe in a temp tree with a stubbed CFBD. Returns the report."""
    d = tempfile.mkdtemp()
    out = os.path.join(d, "data", "ncaaf", "latest")
    os.makedirs(out)
    if teams is not None:
        with io.open(os.path.join(out, "teams.json"), "w",
                     encoding="utf-8") as fh:
            json.dump({"season": season, "source": "CFBD /teams/fbs",
                       "built_at": "2026-09-17T07:27:43Z",
                       "teams": {t: {} for t in teams}}, fh)
    asked = []

    def fake_get(path, params, **kw):
        # ⚠️ THE KWARGS ARE RECORDED, NOT DISCARDED. `tries=` is part of
        #    what "one call" means and a stub that drops it cannot see it.
        asked.append((path, dict(params or {}), dict(kw)))
        if raise_with:
            raise raise_with
        return payload

    old_get, old_out, old_key = cfb.get, cfb.OUT, cfb.KEY
    cfb.get, cfb.OUT, cfb.KEY = fake_get, out, "stub"
    try:
        ok = cfb.coaches_probe(log=lambda *a: None, season=season)
    finally:
        cfb.get, cfb.OUT, cfb.KEY = old_get, old_out, old_key
    files = sorted(os.listdir(out))
    with io.open(os.path.join(out, "coaches-probe.json"), encoding="utf-8") as fh:
        rep = json.load(fh)
    return rep, asked, files, ok


FBS = ["Alabama", "Air Force", "Akron", "Georgia"]

# 🔴 THE TRAP CASE FIRST: `/coaches?year=N` filtered to N. Every row
#    carries year N, so a naive "is there a year column" check says YES
#    and the answer is worthless.
FLAT = [{"first_name": "A", "last_name": "One", "school": "Alabama",
         "year": 2026, "games": 12},
        {"first_name": "B", "last_name": "Two", "school": "Georgia",
         "year": 2026, "games": 12}]
rep, asked, files, ok = drive(FLAT, teams=FBS)

ck("the probe returns cleanly", bool(ok), "returned %r" % (ok,))
ck("🔴 it made EXACTLY ONE call", len(asked) == 1, "calls: %s" % (asked,))
ck("...to /coaches, for the season it was asked for",
   asked[0][0] == "/coaches" and asked[0][1].get("year") == 2026,
   "asked: %s" % (asked,))
# 🔴 ONE CALL IS TWO THINGS: one CALL SITE, and no RETRY behind it.
#    `cfb.get()` defaults to `tries=4` and retries on 429 — so a probe
#    that leaves the default takes the one response that means "stop
#    asking" and asks three more times. ⛔ Measured against the real
#    default rather than asserted: the check reads what `get` would do.
_sig = re.search(r"def get\(path, params, timeout=\d+, tries=(\d+)\)",
                 io.open(os.path.join(ROOT, "cfb.py"), encoding="utf-8").read())
ck("⚠️ cfb.get() really does default to retrying, so this matters",
   bool(_sig) and int(_sig.group(1)) > 1,
   "⛔ if this ever reads 1, the check below is guarding nothing and "
   "should be re-stated. default tries=%s" % (_sig and _sig.group(1),))
ck("🔴 ...and the probe overrides it — a 429 is the finding, not a retry",
   asked[0][2].get("tries") == 1,
   "⛔ four tries on a 429 is four credits to learn what the first one "
   "said. kwargs: %s" % (asked[0][2],))
ck("...and the artifact carries that count, not a comment's promise",
   (rep.get("cost") or {}).get("calls_made") == 1,
   "cost=%s" % (rep.get("cost"),))
ck("🔴 it wrote ONE file and it is the report",
   [f for f in files if f != "teams.json"] == ["coaches-probe.json"],
   "files: %s" % (files,))
ck("the report says in itself that nothing has adopted it",
   bool(rep.get("not_adopted")), "not_adopted=%r" % (rep.get("not_adopted"),))


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A YEAR THAT DOES NOT VARY CANNOT SAY \"NEW THIS SEASON\"")
# ══════════════════════════════════════════════════════════════════════
sy = rep.get("start_year") or {}
ck("the year column IS found", "year" in (sy.get("found") or []),
   "found=%s" % (sy.get("found"),))
ck("🔴 ...and it is still reported NOT computable, because it is constant",
   sy.get("new_this_season_computable") is False,
   "⛔ every row carries the year we ASKED for. A column that exists is "
   "not a column that answers. per_key=%s" % (sy.get("per_key"),))
ck("the report names the candidates it looked for, so a miss reads as a miss",
   len(sy.get("candidates_looked_for") or []) >= 5,
   "candidates=%s" % (sy.get("candidates_looked_for"),))

# ✅ AND THE OTHER DIRECTION, or this check only proves it can say no.
VARY = [{"first_name": "A", "last_name": "One", "school": "Alabama",
         "seasons": [{"school": "Alabama", "year": 2024},
                     {"school": "Alabama", "year": 2026}]},
        {"first_name": "B", "last_name": "Two", "school": "Georgia",
         "seasons": [{"school": "Georgia", "year": 2026}]}]
rep2, asked2, files2, _ = drive(VARY, teams=FBS)
sy2 = rep2.get("start_year") or {}
ck("✅ a year that VARIES is reported computable",
   sy2.get("new_this_season_computable") is True,
   "found=%s varying=%s" % (sy2.get("found"), sy2.get("varying")))
ck("...and the nested column is read, not only the top level",
   any("[]" in k or "." in k for k in (sy2.get("found") or [])),
   "found=%s" % (sy2.get("found"),))
ck("the nested school is counted toward coverage too",
   (rep2.get("fbs_coverage") or {}).get("distinct_schools") == 2,
   "coverage=%s" % (rep2.get("fbs_coverage"),))
ck("⛔ and reading one level down still cost NOTHING extra",
   len(asked2) == 1, "calls: %s" % (asked2,))


# ══════════════════════════════════════════════════════════════════════
section("5. FBS COVERAGE IS READ OFF DISK, NOT BOUGHT")
# ══════════════════════════════════════════════════════════════════════
cov = rep.get("fbs_coverage") or {}
ck("coverage was measured", cov.get("fbs_reference_n") == len(FBS),
   "cov=%s" % (cov,))
ck("the schools that matched are counted", cov.get("fbs_matched") == 2,
   "matched=%s" % (cov.get("fbs_matched"),))
ck("🔴 the schools NOT covered are NAMED, not summarised away",
   sorted(cov.get("fbs_missing") or []) == ["Air Force", "Akron"],
   "missing=%s" % (cov.get("fbs_missing"),))
ck("...and the report names the file the comparison came from",
   (rep.get("fbs_reference") or {}).get("file", "").endswith("teams.json"),
   "ref=%s" % (rep.get("fbs_reference"),))
ck("⛔ an exact-string caveat rides with it",
   "spelled differently" in (cov.get("caveat") or ""),
   "a name miss and a coverage gap are not the same finding. caveat=%r"
   % (cov.get("caveat"),))

# 🔴 NO REFERENCE ON DISK IS "NOT MEASURED", NEVER "NOT COVERED".
rep3, asked3, _, _ = drive(FLAT, teams=None)
cov3 = rep3.get("fbs_coverage") or {}
ck("🔴 with no FBS file on disk, coverage reads NOT MEASURED",
   "NOT measured" in (cov3.get("caveat") or "")
   and "fbs_matched" not in cov3,
   "⛔ an absence in our own tree is evidence about our tree. cov=%s" % (cov3,))
ck("...and it still did not buy the answer with a second call",
   len(asked3) == 1, "calls: %s" % (asked3,))


# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 A FAILED CALL IS EVIDENCE ABOUT THE REQUEST")
# ══════════════════════════════════════════════════════════════════════
# ⚠️ `CLAUDE.md`: "an absence in an API response is evidence about the
#    API, never about the sportsbook" — written down after being got
#    wrong FIVE times. The same trap is one HTTP code away here: a 401 on
#    a tier that does not carry /coaches is not "/coaches does not exist".
import urllib.error
rep4, asked4, files4, ok4 = drive(
    None, teams=FBS,
    raise_with=urllib.error.HTTPError("u", 401, "Unauthorized", {}, None))
ck("a 401 still writes a readable report rather than dying",
   bool(ok4) and "coaches-probe.json" in files4, "files=%s" % (files4,))
ck("🔴 ...and the verdict blames the REQUEST, not CFBD",
   "THIS REQUEST" in (rep4.get("verdict") or "")
   and "401" in (rep4.get("verdict") or ""),
   "⛔ a fact about a query is not a fact about the world. verdict=%r"
   % (rep4.get("verdict"),))
ck("...and it is not recorded as 'the endpoint does not exist'",
   rep4.get("exists") is False and "error" in rep4,
   "exists=%r error=%s" % (rep4.get("exists"), rep4.get("error")))
ck("a failed call still reports what it cost", (rep4.get("cost") or {}).get("calls_made") == 1,
   "cost=%s" % (rep4.get("cost"),))


# ══════════════════════════════════════════════════════════════════════
section("7. THE COLUMN LIST IS THE ENDPOINT'S, NOT ROW ZERO'S")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `rows[0].keys()` is a claim about ONE COACH. A feed that drops a null
#    field would make the schema a property of whoever sorted first.
RAGGED = [{"school": "Alabama", "year": 2026},
          {"school": "Georgia", "year": 2026, "hire_year": 2019}]
rep5, _, _, _ = drive(RAGGED, teams=FBS)
cols = rep5.get("columns") or {}
ck("🔴 a column present on only ONE row is still in the list",
   "hire_year" in cols, "columns=%s" % (cols,))
ck("...and the list says how many rows carried each one",
   cols.get("hire_year") == 1 and cols.get("school") == 2,
   "columns=%s" % (cols,))
ck("a second year candidate is picked up by name",
   "hire_year" in ((rep5.get("start_year") or {}).get("found") or []),
   "found=%s" % ((rep5.get("start_year") or {}).get("found"),))


# ══════════════════════════════════════════════════════════════════════
section("8. 🔴 A START **DATE** IS A START YEAR — THE REAL SHAPE")
# ══════════════════════════════════════════════════════════════════════
# ⛔ THIS SECTION EXISTS BECAUSE THE FIRST RUN GOT IT WRONG. The live
#    response carries `hireDate` on every row, and the probe's candidate
#    list was year-SHAPED only — so it found `seasons[].year`, saw it
#    pinned to the season it had asked for, and published "new this
#    season is NOT COMPUTABLE" with the answer in the next column.
# ⚠️ THE FIXTURE IS THE MEASURED SHAPE, NOT AN INVENTED ONE: copied from
#    `sample_row` in the artifact the 2026-09-18 run committed.
REAL = [{"firstName": "Scott", "lastName": "Abell", "id": 1826,
         "hireDate": "2024-11-26T00:00:00.000Z",
         "seasons": [{"school": "Rice", "conference": "American Athletic",
                      "year": 2026, "games": 0, "wins": 0, "losses": 0}]},
        {"firstName": "New", "lastName": "Guy", "id": 99,
         "hireDate": "2026-01-09T00:00:00.000Z",
         "seasons": [{"school": "Alabama", "conference": "SEC",
                      "year": 2026, "games": 0, "wins": 0, "losses": 0}]}]
rep8, asked8, _, _ = drive(REAL, teams=FBS, season=2026)
sy8 = rep8.get("start_year") or {}
ck("the year column is STILL reported constant — that part was right",
   (sy8.get("per_key") or {}).get("seasons[].year", {}).get("distinct") == 1,
   "per_key=%s" % (sy8.get("per_key"),))
ck("🔴 ...but hireDate is found, and it is what answers the question",
   "hireDate" in (sy8.get("found") or []),
   "⛔ a date is not a second-class year. found=%s" % (sy8.get("found"),))
ck("🔴 ...so \"new this season\" reads COMPUTABLE on the real shape",
   sy8.get("new_this_season_computable") is True,
   "varying=%s" % (sy8.get("varying"),))
ck("...and the count of coaches hired in the asked season is reported",
   (sy8.get("per_date_key") or {}).get("hireDate", {})
   .get("hired_in_asked_season") == 1,
   "⚠️ one of the two fixture coaches was hired in 2026. per_date_key=%s"
   % (sy8.get("per_date_key"),))
ck("...and a date it cannot parse is COUNTED, never silently dropped",
   "unparsed" in (sy8.get("per_date_key") or {}).get("hireDate", {}),
   "per_date_key=%s" % (sy8.get("per_date_key"),))
ck("⛔ and reading the date cost nothing extra", len(asked8) == 1,
   "calls: %s" % (asked8,))


# ══════════════════════════════════════════════════════════════════════
section("9. 🔴 THE STORED ARTIFACT MAY NOT CONTRADICT ITS OWN COLUMNS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PROBE HAS NO CRON, SO IT NEVER REGENERATES ITSELF. The file the
#    2026-09-18 run committed says "new this season" is NOT COMPUTABLE
#    while its own `columns` block records `hireDate` on 138 of 138 rows
#    and its own `sample_row` shows `2024-11-26` against a 2026 season.
#    ⛔ A published artifact that disproves itself is worse than a missing
#    one, because the wrong half is the half with a verdict attached.
# ⚠️ AND IT CANNOT BE FIXED BY RE-RUNNING: that is another CFBD credit.
#    So it is ANNOTATED, and this check is what makes the annotation
#    compulsory rather than optional.
# ✅ THE QUESTION IS SELF-CONTAINED: every start-year-shaped column the
#    artifact ITSELF records must either be in `start_year.found`, or be
#    named in a `superseded` block that states the corrected value. No
#    network, no second call, no appeal to anything outside the file.
# ⛔ THE KEY LISTS ARE READ OFF `cfb.py`, NOT RE-TYPED HERE. Rule 166 — a
#    list written down twice is a claim that goes stale in one copy.
_ART = os.path.join(ROOT, "data", "ncaaf", "latest", "coaches-probe.json")
ck("the stored probe artifact is present, so this is not a vacuous pass",
   os.path.exists(_ART),
   "⛔ an absent artifact must FAIL here, never pass quietly (rule 67). "
   "looked for %s" % _ART)
if os.path.exists(_ART):
    with io.open(_ART, encoding="utf-8") as _fh:
        _a = json.load(_fh)
    _shaped = set(cfb._YEAR_KEYS) | set(cfb._DATE_KEYS)

    def _leaf(k):
        return k.split("[")[0].split(".")[-1] if "." in k else k

    _recorded = {_leaf(k) for k in list(_a.get("columns") or {})
                 + list(_a.get("nested_columns") or {})} & _shaped
    _sy = _a.get("start_year") or {}
    _found = {_leaf(k) for k in (_sy.get("found") or [])}
    _missed = sorted(_recorded - _found)
    note("start-year-shaped columns the artifact records: %s; its parser "
         "found: %s" % (sorted(_recorded), sorted(_found)))
    _sup = _sy.get("superseded") or {}
    ck("🔴 every start-year column the file RECORDS was seen by the "
       "parser, or is named as superseded",
       not _missed or sorted(_sup.get("missed_columns") or []) == _missed,
       "⛔ the artifact records %s and its verdict was computed without "
       "it. That is a fact about the parser published as a fact about the "
       "feed. Annotate the file — do NOT spend a credit re-running it. "
       "superseded names: %s"
       % (_missed, sorted(_sup.get("missed_columns") or []) or "nothing"))
    if _missed:
        ck("...and the annotation states the CORRECTED value, not just "
           "that something was wrong",
           _sup.get("corrected_value") is not None
           and _sup.get("corrected_value") != _sy.get(
               "new_this_season_computable"),
           "a note that says 'this is wrong' without saying what is right "
           "leaves the reader where they started. superseded=%s" % (_sup,))
        ck("...and the verdict LINE itself is struck, not left to read "
           "as current",
           "SUPERSEDED" in (_a.get("verdict") or ""),
           "⛔ a reader who opens this file sees `verdict` first. "
           "verdict=%r" % ((_a.get("verdict") or "")[:120],))
        ck("...and it cites the evidence out of this same file",
           bool((_sup.get("evidence") or {})),
           "the contradiction is provable from `columns` and `sample_row`, "
           "so the annotation quotes them rather than asserting. "
           "evidence=%s" % (_sup.get("evidence"),))
