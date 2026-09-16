#!/usr/bin/env python3
"""
THE FOOTBALL RECORD TAB: MLB'S BANDS, AND A DAY YOU CAN OPEN.

🔴 THE JAVASCRIPT IS EXECUTED, NOT READ. `[jsblock.py's own lesson, and
rule 197]` `fbScores` once carried a complete `<tr>` builder that was
defined and never called; the tab rendered nothing and the source looked
perfect. So every check below RUNS the page's own function under node and
asserts on what came back.

⛔ AND THE TRAP THIS FILE EXISTS FOR IS ONE FILE OVER. `card_fb.py` was
bitten on 2026-09-16 by reading MLB's `predicted` from a football record
that names the field `stated`; the defaulted result publishes **0%** on a
board that claimed 84. `bandRow` is MLB's and takes `said`. The mapping
happens at the FOOTBALL CALL SITE, and the check that matters most drives
a record carrying `stated` and no `predicted` at all.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

from tcheck import ck, eq, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsblock import js_block, calls  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
IDX = os.path.join(ROOT, "index.html")


# ══════════════════════════════════════════════════════════════════════
# @vacuity the football bands must render through bandRow, not a table
#   file: index.html
#   find: const band = c => bandRow({
#   with: const band = c => '<table>' + JSON.stringify({
#
# @vacuity the claimed figure is `stated`; MLB's `predicted` finds nothing
#   file: index.html
#   find: said: c.stated, hit: c.n ? c.pct : null });
#   with: said: c.predicted, hit: c.n ? c.pct : null });
#
# @vacuity an empty bucket is "No sample", never a bar sitting at zero
#   file: index.html
#   find: hit: c.n ? c.pct : null });
#   with: hit: c.pct || 0 });
#
# @vacuity a graded day row must carry data-date, or nothing can open it
#   file: index.html
#   find: <tr class="${open ? 'dayrow' : ''}"${open ? ` data-date="${d.date}"` : ''}${
#   with: <tr class="${open ? 'dayrow' : ''}"${open ? `` : ''}${
#
# @vacuity the detail cache is keyed BY LEAGUE, never one shared slot
#   file: index.html
#   find: const key = lg;
#   with: const key = 'one';
#
# @vacuity a missing detail file degrades to a note, never an exception
#   file: index.html
#   find: cell.innerHTML = `<div class="note"><b>No detail file yet.</b> The grader
#   with: cell.innerHTML = `<div class="x"><b>nothing at all</b> The grader
#
# @vacuity MLB's bandRow stays byte-identical to main
#   file: index.html
#   find: const verdict = gap == null ? 'No sample'
#   with: const verdict = gap == null ? 'no sample'
# ══════════════════════════════════════════════════════════════════════


def node(body, extra=""):
    """Run `body` under node with the page's real functions in scope.

    ⛔ THE IMPLEMENTATION IS PULLED OUT OF `index.html`, NEVER RETYPED. A
    copy of the function under test is a test of the copy.
    """
    src = "\n".join(js_block(n, IDX) for n in
                    ("bandRow", "fbCalBlock", "fbDayRows", "fbDayDetailHtml",
                     "fbDetailLoad"))
    # ⚠️ `const FBDETAIL = {}` LIVES OUTSIDE THE FUNCTION, so js_block
    #    cannot reach it — and retyping it here would make the cache test
    #    a test of my copy. Pulled out of the page by its own declaration.
    import re as _re
    decl = _re.search(r"^const FBDETAIL = \{\};", open(IDX, encoding="utf-8")
                      .read(), _re.M)
    assert decl, "index.html no longer declares FBDETAIL"
    prog = ("const LG_DATA = { mlb:'data', nfl:'data/nfl', ncaaf:'data/ncaaf' };\n"
            + decl.group(0) + "\n"
            "const sgn = v => v == null ? '-' : (v > 0 ? '+' + v : '' + v);\n"
            + extra + "\n" + src + "\n"
            + "(async () => { " + body + " })().catch(e => {"
            "  console.log('__ERR__' + (e && e.message)); process.exit(3); });")
    d = tempfile.mkdtemp(prefix="fbrec-")
    f = os.path.join(d, "probe.js")
    open(f, "w", encoding="utf-8").write(prog)
    p = subprocess.run(["node", f], capture_output=True, text=True, timeout=120,
                       cwd=ROOT)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def out(body, extra=""):
    """-> the JSON the probe printed, or a dict describing the failure."""
    rc, o = node(body, extra)
    for line in o.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except ValueError:
                pass
    return {"__rc": rc, "__out": o[-400:]}


REAL = {lg: json.load(open(os.path.join(ROOT, "data", lg, "latest",
                                        "record.json"), encoding="utf-8"))
        for lg in ("nfl", "ncaaf")}

section("0. ⚠️ THE FUNCTIONS EXIST AND ARE ACTUALLY CALLED")
# 🔴 "DOES IT EXIST" IS THE QUESTION THAT GOT `fbScores` WRONG. The
#    question is who CALLS it.
_fbrec = js_block("fbRecord", IDX)
_wire = js_block("fbWireDayRows", IDX)
for _n in ("fbCalBlock", "fbDayRows", "fbWireDayRows"):
    ck(calls(_n, IDX) >= 1 and (_n + "(") in _fbrec,
       "⛔ fbRecord CALLS %s" % _n,
       "🔴 a renderer defined and never called is the defect jsblock.py "
       "was written for — the source reads perfectly and the tab is "
       "blank. Called %d time(s) anywhere; in fbRecord: %s"
       % (calls(_n, IDX), (_n + "(") in _fbrec))
for _n in ("fbDetailLoad", "fbDayDetailHtml"):
    ck(calls(_n, IDX) >= 1 and (_n + "(") in _wire,
       "⛔ ...and the click handler calls %s" % _n,
       "a cache nothing reaches is not a cache, and a detail renderer "
       "nothing reaches is a blank box")

section("1. 🔴🔴 THE BANDS RENDER THROUGH bandRow — AND NOT A TABLE")
_r = out("const h = fbCalBlock(%s);"
         "console.log(JSON.stringify({bands:(h.match(/class=\"band\"/g)||[]).length,"
         "tables:(h.match(/<table/g)||[]).length,"
         "verdicts:[...h.matchAll(/class=\"verd [^\"]*\">([^<]*)</g)].map(m=>m[1]).length,"
         "pts:(h.match(/pts</g)||[]).length, html:h}));"
         % json.dumps(REAL["nfl"]["calibration"]))
eq(_r.get("bands"), len(REAL["nfl"]["calibration"]),
   "🔴 one `.band` per bucket, off the REAL nfl record")
eq(_r.get("tables"), 0,
   "⛔ AND NOT ONE `<table>` — the bare table is gone, not hidden beside "
   "the bars")
eq(_r.get("verdicts"), len(REAL["nfl"]["calibration"]),
   "   every band carries MLB's one-word verdict",
   )
# ⚠️ COUNTED INSIDE THE `verd` DIV, not anywhere on the page. The legend
#    repeats "Beat the claim" as a key, so a loose match counted 8 for 7
#    bands — a check that would have stayed green if a band lost its
#    verdict and the legend kept its label.
eq(_r.get("pts"), len(REAL["nfl"]["calibration"]),
   "   ...and the gap in points")

section("2. 🔴🔴 THE CLAIMED FIGURE COMES FROM `stated`, NEVER 0")
# ⛔ THE MUTATION THAT MATTERS MOST. A record carrying `stated` and NO
#    `predicted` — which is every football record — must still produce
#    real percentages. `said: c.predicted` yields `left:undefined%` and a
#    band claiming nothing at all.
_SYN = [{"bucket": "80-90%", "stated": 84.1, "w": 11, "n": 23, "pct": 47.8},
        {"bucket": "60-70%", "stated": 65.1, "w": 14, "n": 32, "pct": 43.8}]
ck(all("predicted" not in b for b in _SYN),
   "⚠️ the fixture carries NO `predicted` key at all",
   "⛔ if it carried one, MLB's mapping would work here and this section "
   "would prove nothing (rule 67)")
ck(all("predicted" not in c for c in REAL["nfl"]["calibration"]),
   "⚠️ ...and neither does the real record",
   "🔴 this is why the verbatim copy fails: the key simply is not there")
_r2 = out("const h = fbCalBlock(%s);"
          "const said=[...h.matchAll(/left:([^%%;\"]*)%%/g)].map(m=>m[1]);"
          "const wide=[...h.matchAll(/width:([^%%;\"]*)%%/g)].map(m=>m[1]);"
          "console.log(JSON.stringify({said, wide, "
          "claimed:[...h.matchAll(/claimed ([^<]*)%%/g)].map(m=>m[1])}));"
          % json.dumps(_SYN))
eq(_r2.get("claimed"), ["84.1", "65.1"],
   "🔴🔴 THE BARS CLAIM 84.1% AND 65.1%, THE RECORD'S OWN NUMBERS",
   )
ck("0" not in (_r2.get("claimed") or ["0"]),
   "⛔ ...and nothing claims 0%",
   "🔴 THE TWIN OF THE card_fb.py DEFECT: `.predicted` on a football "
   "record finds nothing, and the band publishes a claim nobody made. "
   "Got %s" % _r2.get("claimed"))
eq(_r2.get("said"), ["84.1", "65.1"], "   the marker sits at the claim")
eq(_r2.get("wide"), ["47.8", "43.8"], "   the bar is the delivered rate")

section("3. ⚠️ THE GEOMETRY HOLDS AT FOOTBALL'S RANGE, WHICH MLB NEVER HITS")
# Football bands reach -36 and -53 points; MLB's worst is -50.9 on n=16.
# ⛔ The gap does not touch the geometry — `width` is `hit` and `left` is
#    `said`, each 0-100 by construction — but "by construction" is a claim,
#    so it is DRIVEN at both extremes of the real records.
_EDGE = [{"bucket": "0-10%", "stated": 0.0, "w": 0, "n": 1, "pct": 0.0},
         {"bucket": "90-100%", "stated": 100.0, "w": 1, "n": 1, "pct": 100.0},
         {"bucket": "80-90%", "stated": 94.2, "w": 0, "n": 30, "pct": 0.0}]
_all = REAL["nfl"]["calibration"] + REAL["ncaaf"]["calibration"] + _EDGE
_r3 = out("const h = fbCalBlock(%s);"
          "const num=re=>[...h.matchAll(re)].map(m=>parseFloat(m[1]));"
          "console.log(JSON.stringify({left:num(/left:([^%%;\"]*)%%/g),"
          "width:num(/width:([^%%;\"]*)%%/g)}));" % json.dumps(_all))
_left, _width = _r3.get("left") or [], _r3.get("width") or []
ck(len(_left) == len(_all) and len(_width) == len(_all),
   "⚠️ every band produced a marker and a bar",
   "⛔ a check over a short list proves nothing. Got %d/%d of %d"
   % (len(_left), len(_width), len(_all)))
# ⚠️ NOT-A-NUMBER IS A FAILURE HERE, NOT A CRASH. `left:undefined%` comes
#    back from `parseFloat` as NaN and through JSON as `null`; comparing
#    that with `<=` KILLED this file under the `predicted` mutation and
#    cost every check after it its turn. Same assertion, one class wider.
_bad = [v for v in _left + _width
        if not isinstance(v, (int, float)) or not (0 <= v <= 100)]
ck(not _bad,
   "🔴 EVERY BAR IS A REAL NUMBER IN 0-100%, at a -53 point gap or anywhere",
   "⛔ `.track` clips with overflow:hidden, so a negative or absent width "
   "is a SILENTLY missing bar rather than a visibly broken one — and "
   "`undefined` is how the `predicted` mistake shows up here. Offenders: "
   "%s (left=%s width=%s)" % (_bad, _left, _width))
_worst = min((c["pct"] - c["stated"]) for c in _all if c["n"])   # incl. synthetic edges
note("   the widest gap driven here is %+.1f points — MLB's own worst "
     "band is -50.9, so this path is untested by construction on that "
     "side of the page." % _worst)

section("4. ⚠️ AN EMPTY BUCKET IS 'No sample', NOT A BAR AT ZERO")
_r4 = out("const h = fbCalBlock([{bucket:'70-80%',stated:75.0,n:0,pct:0}]);"
          "console.log(JSON.stringify({h, nosample:h.includes('No sample'),"
          "bar:(h.match(/class=\"hit/g)||[]).length}));")
ck(_r4.get("nosample"), "   a bucket nobody bet says so",
   "⛔ a bucket nobody bet is not a bucket that lost")
eq(_r4.get("bar"), 0, "   ...and draws no bar at all")

section("5. 🔴 EVERY GRADED DAY ROW IS CLICKABLE, AND ONLY THE GRADED ONES")
_DAYS = [{"date": "2026-09-09", "w": 5, "n": 10, "carded": 12, "voids": 0,
          "unresolved": 2},
         {"date": "2026-09-10", "w": 0, "n": 0, "carded": 4, "voids": 0,
          "unresolved": 4}]
_r5 = out("const h = fbDayRows(%s, {});"
          "console.log(JSON.stringify({dates:[...h.matchAll(/data-date=\"([^\"]*)\"/g)]"
          ".map(m=>m[1]), rows:(h.match(/class=\"dayrow/g)||[]).length,"
          "detail:[...h.matchAll(/id=\"fbdd-([^\"]*)\"/g)].map(m=>m[1]),"
          "carets:(h.match(/class=\"caret\"/g)||[]).length}));" % json.dumps(_DAYS))
eq(_r5.get("dates"), ["2026-09-10", "2026-09-09"][1:],
   "🔴 the graded day carries data-date")
eq(_r5.get("detail"), ["2026-09-09"],
   "   ...and a detail row to open into")
eq(_r5.get("carets"), 1, "   ...and exactly one caret")
ck("2026-09-10" not in (_r5.get("dates") or []),
   "⛔ the day with NOTHING graded is not clickable",
   "🔴 a caret that opens an empty box reads as a broken page, not as an "
   "honest empty state")
_r5b = out("const h = fbDayRows([], {record_from:'2026-09-07'});"
           "console.log(JSON.stringify({h, rows:(h.match(/dayrow/g)||[]).length}));")
eq(_r5b.get("rows"), 0, "   an empty record wires nothing")
ck("Nothing graded since 2026-09-07" in (_r5b.get("h") or ""),
   "   ...and keeps the sentence record_fb.py computed",
   "rule 132: the page prints the grader's number, it does not carry one")

section("6. ⛔⛔ THE DETAIL CACHE IS KEYED BY LEAGUE")
# 🔴 MLB's `loadRecordDetail()` caches in ONE module-level `RECDETAIL` and
#    hard-codes `data/latest/`. A football copy of that shape serves nfl's
#    picks under ncaaf the moment you switch — SILENTLY, AND LOOKING
#    CORRECT. This drives exactly that: load nfl, then ncaaf, and assert
#    the second is not the first.
_r6 = out(
    "const a = await fbDetailLoad('nfl', {detail_file:'NFL'});"
    "const b = await fbDetailLoad('ncaaf', {detail_file:'NCAAF'});"
    "const c = await fbDetailLoad('nfl', {detail_file:'NFL'});"
    "console.log(JSON.stringify({a:a.who, b:b.who, c:c.who, fetches:FETCHED}));",
    extra="let FETCHED=[];"
          "async function jgetGz(p){ FETCHED.push(p); return {who:p}; }")
eq(_r6.get("a"), "NFL", "   nfl serves the nfl file")
eq(_r6.get("b"), "NCAAF",
   "🔴🔴 ...AND NCAAF SERVES THE COLLEGE FILE, NOT NFL'S",
   )
eq(_r6.get("c"), "NFL", "   ...and nfl still serves nfl afterwards")
eq(_r6.get("fetches"), ["NFL", "NCAAF"],
   "⚠️ fetched ONCE PER LEAGUE and cached — the third call hit no network",
   )
_r6b = out(
    "const a = await fbDetailLoad('nfl', null);"
    "console.log(JSON.stringify({path:a.who}));",
    extra="async function jgetGz(p){ return {who:p}; }")
eq(_r6b.get("path"), "data/nfl/latest/record-detail.json.gz",
   "   ⚠️ ...and a record with no detail_file falls back to the league path")
for _lg in ("nfl", "ncaaf"):
    eq(REAL[_lg].get("detail_file"),
       "data/%s/latest/record-detail.json.gz" % _lg,
       "   the real %s record carries its own detail_file" % _lg)

section("7. ⛔ A MISSING DETAIL FILE DEGRADES TO A NOTE, NOT AN EXCEPTION")
_r7 = out(
    "let msg='';"
    "try { await fbDetailLoad('nfl', {detail_file:'gone'}); msg='NO THROW'; }"
    "catch(e){ msg='threw: ' + e.message; }"
    "console.log(JSON.stringify({msg}));",
    extra="async function jgetGz(p){ throw new Error(p + ' -> 404'); }")
ck((_r7.get("msg") or "").startswith("threw:"),
   "   the loader propagates the failure to its caller",
   "⛔ swallowing it inside the loader would cache `undefined` as the "
   "league's detail forever. Got %r" % _r7.get("msg"))
_WIRE = js_block("fbWireDayRows", IDX)
ck("catch" in _WIRE and "No detail file yet" in _WIRE,
   "🔴 ...and the CALLER catches it and writes the note",
   "⛔ before the first graded card there is no detail file and that is "
   "not an error — a broken tab would say the product is broken when it "
   "is merely new")
ck("record-detail.json.gz" in _WIRE,
   "   ...naming the file the grader will write")
_r7b = out("const h = fbDayDetailHtml(null);"
           "const g = fbDayDetailHtml([]);"
           "console.log(JSON.stringify({h, g}));")
ck("No rows stored" in (_r7b.get("h") or "")
   and "No rows stored" in (_r7b.get("g") or ""),
   "   ⚠️ and a day present in the file with no rows says so too",
   "an undefined day and an empty day are both 'nothing to show'")

section("8. ⛔⛔ MLB IS UNTOUCHED — BYTE-IDENTICAL, NOT 'I DIDN'T MEAN TO'")
# 🔒 EVERY HASH BELOW WAS TAKEN FROM `origin/main` ON 2026-09-16, BEFORE
#    THIS CHANGE. ⛔ DO NOT UPDATE ONE TO MAKE THIS PASS. The freeze says
#    MLB does not change; teaching `bandRow` about `stated` would be
#    editing MLB through the back door, and this is the check that refuses
#    it. If a hash is red, the answer is to revert the MLB function.
_MAIN = {"bandRow": "647b8b356b15b9e5",
         "renderRecord": "20cb8492840fbdc4",
         "dayDetailHtml": "cf90d3ea7c684cf9",
         "loadRecordDetail": "a6fff37555f03ce7"}
for _n, _want in sorted(_MAIN.items()):
    _got = hashlib.sha256(js_block(_n, IDX).encode()).hexdigest()[:16]
    eq(_got, _want, "🔒 %s is byte-identical to main" % _n)
# ⚠️ AND THE HASHES ARE NOT THE WHOLE CLAIM. A hash says "unchanged"; this
#    says WHAT must stay true, so a deliberate MLB edit still trips it.
_BR = js_block("bandRow", IDX)
for _k in ("stated", "pct", "bucket"):
    ck(_k not in _BR,
       "⛔ bandRow knows nothing of `%s` — the mapping is at the call site"
       % _k,
       "🔴 MLB depends on this function. Teaching it football's key names "
       "is touching MLB through the back door")
ck("said" in _BR and "hit" in _BR,
   "   ...and still takes MLB's own `said`/`hit`")
_IDXSRC = open(IDX, encoding="utf-8").read()
eq(_IDXSRC.count("${P.calibration_warning}"), 1,
   "⛔ the MLB card's own render is still exactly one occurrence")
eq(_IDXSRC.count("said: c.predicted"), 1,
   "⛔ ...and `said: c.predicted` appears ONCE — MLB's call site only",
   )
eq(_IDXSRC.count("said: c.stated"), 1,
   "   while football's `said: c.stated` is its own, separate call")
note("⛔ WHAT THIS DOES NOT CLAIM: that the tab LOOKS right. It claims the "
     "bands come from bandRow with football's own numbers, that a graded "
     "day can be opened, that the cache cannot serve the wrong league, "
     "and that MLB's four record functions are byte-for-byte what main "
     "has. Rendering it in a browser is still the only way to see it.")
