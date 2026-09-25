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
import re as _re
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
#   find: said: c.stated, hit: c.n ? c.pct : null }, 'the record claimed');
#   with: said: c.predicted, hit: c.n ? c.pct : null }, 'the record claimed');
#
# @vacuity an empty bucket is "No sample", never a bar sitting at zero
#   file: index.html
#   find: hit: c.n ? c.pct : null }, 'the record claimed');
#   with: hit: c.pct || 0 }, 'the record claimed');
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
# @vacuity the football bands must not speak in MLB's first person
#   file: index.html
#   find: }, 'the record claimed');
#   with: });
#
# @vacuity MLB's RENDERED bands must be byte-identical to the frozen copy
#   file: index.html
#   find: gap.toFixed(1)
#   with: gap.toFixed(2)
#
# @vacuity the tab must draw every method's bands, not `calibration` alone
#   file: index.html
#   find: const calBlock = fbCalMethods(R);
#   with: const calBlock = fbCalBlock((R && R.calibration) || []);
#
# @vacuity a method other than the current one must still be drawn
#   file: index.html
#   find: const order = [cur, ...Object.keys(by).filter(m => m !== cur)];
#   with: const order = [cur];
#
# @vacuity each method's table carries its own label
#   file: index.html
#   find: : (m === FB_METHOD_BEFORE ? '2025-only method' : `earlier method (${m})`);
#   with: : (m === FB_METHOD_BEFORE ? '' : `earlier method (${m})`);
#
# @vacuity a method with no graded picks says so instead of drawing nothing
#   file: index.html
#   find: return label ? `${head}<div class="fb-cal-empty" style="margin:0 0 8px;font-size:12.5px;color:var(--mut)">No graded
#   with: return label ? `${head}<div class="fb-cal-empty" style="margin:0 0 8px;font-size:12.5px;color:var(--mut)">
#
# @vacuity the default voice is preserved for callers that pass none
#   find: ${saidAs || 'we said'}
#   file: index.html
#   with: ${saidAs || 'the record claimed'}
# ══════════════════════════════════════════════════════════════════════


def node(body, extra=""):
    """Run `body` under node with the page's real functions in scope.

    ⛔ THE IMPLEMENTATION IS PULLED OUT OF `index.html`, NEVER RETYPED. A
    copy of the function under test is a test of the copy.
    """
    src = "\n".join(js_block(n, IDX) for n in
                    ("bandRow", "fbCalBlock", "fbCalMethods", "fbDayRows",
                     "fbDayDetailHtml", "fbDetailLoad"))
    # ⚠️ `const FBDETAIL = {}` LIVES OUTSIDE THE FUNCTION, so js_block
    #    cannot reach it — and retyping it here would make the cache test
    #    a test of my copy. Pulled out of the page by its own declaration.
    import re as _re
    decl = _re.search(r"^const FBDETAIL = \{\};", open(IDX, encoding="utf-8")
                      .read(), _re.M)
    assert decl, "index.html no longer declares FBDETAIL"
    mdecl = _re.search(r"^const FB_METHOD_BEFORE = '[^']*';",
                       open(IDX, encoding="utf-8").read(), _re.M)
    assert mdecl, "index.html no longer declares FB_METHOD_BEFORE"
    prog = ("const LG_DATA = { mlb:'data', nfl:'data/nfl', ncaaf:'data/ncaaf' };\n"
            + decl.group(0) + "\n" + mdecl.group(0) + "\n"
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


# 🔴 EVERY METHOD'S BANDS, NOT `calibration` ALONE. `[2026-09-24]`
# ⛔ `calibration` is only the CURRENT card method's buckets, and the day
#    the method switched it was EMPTY — so every check below that drove it
#    ran on `[]` and several PASSED on nothing (one `.band` per bucket, 0
#    of 0). The real bands are every method's, concatenated.
def all_bands(rec):
    by = rec.get("calibration_by_method")
    if by is None:
        return list(rec.get("calibration") or [])
    return [c for v in by.values() for c in v]


BANDS = {lg: all_bands(REAL[lg]) for lg in REAL}

section("0. ⚠️ THE FUNCTIONS EXIST AND ARE ACTUALLY CALLED")
# 🔴 "DOES IT EXIST" IS THE QUESTION THAT GOT `fbScores` WRONG. The
#    question is who CALLS it.
_fbrec = js_block("fbRecord", IDX)
_wire = js_block("fbWireDayRows", IDX)
for _n in ("fbCalMethods", "fbDayRows", "fbWireDayRows"):
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
         % json.dumps(BANDS["nfl"]))
ck(len(BANDS["nfl"]) >= 3,
   "⚠️ the real nfl record has bands to draw (%d)" % len(BANDS["nfl"]),
   "⛔ one `.band` per bucket over zero buckets is the emptiest pass there "
   "is — and it is exactly what this section did the day `calibration` "
   "went empty")
eq(_r.get("bands"), len(BANDS["nfl"]),
   "🔴 one `.band` per bucket, off the REAL nfl record")
eq(_r.get("tables"), 0,
   "⛔ AND NOT ONE `<table>` — the bare table is gone, not hidden beside "
   "the bars")
eq(_r.get("verdicts"), len(BANDS["nfl"]),
   "   every band carries MLB's one-word verdict",
   )
# ⚠️ COUNTED INSIDE THE `verd` DIV, not anywhere on the page. The legend
#    repeats "Beat the claim" as a key, so a loose match counted 8 for 7
#    bands — a check that would have stayed green if a band lost its
#    verdict and the legend kept its label.
eq(_r.get("pts"), len(BANDS["nfl"]),
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
ck(BANDS["nfl"] and all("predicted" not in c for c in BANDS["nfl"]),
   "⚠️ ...and neither does the real record",
   "🔴 this is why the verbatim copy fails: the key simply is not there")
_r2 = out("const h = fbCalBlock(%s);"
          "const said=[...h.matchAll(/left:([^%%;\"]*)%%/g)].map(m=>m[1]);"
          "const wide=[...h.matchAll(/width:([^%%;\"]*)%%/g)].map(m=>m[1]);"
          "console.log(JSON.stringify({said, wide, "
          "claimed:[...h.matchAll(/nbsp; claimed ([^<]*)%%/g)]"
          ".map(m=>m[1])}));"
          % json.dumps(_SYN))
# ⚠️ ANCHORED ON THE VISIBLE LABEL, not on the word "claimed" anywhere.
#    The tooltip now reads "the record claimed 84.1%" too, and the loose
#    form counted every band twice — a check that would have stayed green
#    if the label lost its number and the tooltip kept one.
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
_all = BANDS["nfl"] + BANDS["ncaaf"] + _EDGE
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
# ⚠️ ~~`bandRow` pinned by hash~~ — REMOVED 2026-09-17, deliberately, and
#    replaced by section 9. The hash asked "did this source change?", and
#    the answer is now YES: it takes an optional label. ⛔ The question
#    that matters is whether MLB's RENDERED OUTPUT changed, and section 9
#    answers it by diffing MLB's real bands through a frozen copy of the
#    old function against the live one.
# 🔴 SAY WHAT THIS GIVES UP: a hash forbids every edit; a rendered diff
#    permits any edit MLB cannot see. That is the narrower licence Sam
#    granted for this change, and it is written down rather than implied.
# ⚠️ renderRecord re-baselined 2026-09-23 (~~20cb8492840fbdc4~~) on Sam's
#    instruction — MLB unfrozen 2026-09-22, and his MLB learning task puts the
#    labelled champion-vs-challenger panel on this tab. The same amendment is
#    recorded in research/mlb_render_frozen.json's `_why`.
_MAIN = {"renderRecord": "0975b831faa24360",
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
section("9. 🔴🔴 A SHARED COMPONENT CARRIES ITS FIRST CALLER'S VOICE")
# ⛔ `bandRow` was written for the MLB MODEL and its first person was
#    correct there and only there. Football renders through it, where the
#    number is the player's OWN 2025 record — rule 55, in a tooltip.
# 🔴 AND NOT ONLY FOOTBALL: today's MLB card is 25 MODEL rows and 25
#    RECORD rows through these same buckets. ⚠️ MLB's half is REPORTED,
#    NOT FIXED — see the PR body. The freeze means report and leave.
_FROZEN = os.path.join(ROOT, "research", "bandrow_pre_saidas.js")
_frozen_src = open(_FROZEN, encoding="utf-8").read()
_live_src = js_block("bandRow", IDX)
ck(_frozen_src.strip() and "function bandRow" in _frozen_src,
   "⚠️ the frozen oracle is there and is a bandRow",
   "⛔ a missing oracle would make every diff below compare nothing")
ck(_live_src not in _frozen_src,
   "⚠️ ...and it is NOT the live version",
   "🔴 RULE 67: the moment the oracle tracks the function it is meant to "
   "check, the diff passes by construction and proves nothing. If this "
   "is red, somebody updated the fixture instead of answering the "
   "question it asks.")

# 🔴 MLB'S OWN CALL SITE IS EXTRACTED, NOT RETYPED. If MLB ever changes
#    how it calls bandRow, this check follows it instead of testing a copy.
_CALL = _re.search(
    r"\(R\.calibration \|\| \[\]\)\.map\(c => bandRow\(\{[\s\S]*?\}\)\)\.join\(''\)",
    js_block("renderRecord", IDX))
ck(bool(_CALL), "⚠️ MLB's own bandRow call site was found in renderRecord",
   "⛔ if this regex stops matching, the diff below silently has nothing "
   "to render and the licence for this change evaporates")
_MLBREC = json.load(open(os.path.join(ROOT, "data", "latest", "record.json"),
                         encoding="utf-8"))
ck(len(_MLBREC.get("calibration") or []) >= 3,
   "⚠️ ...and MLB has real bands to diff (%d)"
   % len(_MLBREC.get("calibration") or []),
   "⛔ diffing two empty strings is the emptiest possible pass")
_r9 = out(
    "const oldFn = new Function(FROZEN + '; return bandRow;')();"
    "const newFn = NEWBAND;"
    "const render = fn => new Function('R','bandRow','return ' + CALL)(REC, fn);"
    "const a = render(oldFn), b = render(newFn);"
    "console.log(JSON.stringify({same: a === b, alen: a.length, blen: b.length,"
    " weSaid: (b.match(/we said/g)||[]).length}));",
    extra=("const FROZEN = " + json.dumps(_frozen_src) + ";\n"
           "const CALL = " + json.dumps(_CALL.group(0) if _CALL else "''") + ";\n"
           "const REC = " + json.dumps(_MLBREC) + ";\n"
           "const NEWBAND = bandRow;"))
ck(_r9.get("same") is True,
   "🔴🔴 MLB'S RENDERED BANDS ARE BYTE-IDENTICAL, OLD FUNCTION VS NEW",
   "⛔ THIS IS THE WHOLE LICENCE FOR TOUCHING A COMPONENT MLB DEPENDS "
   "ON. Not 'I did not change the MLB call site' — the strings. Got "
   "old=%s new=%s chars" % (_r9.get("alen"), _r9.get("blen")))
ck((_r9.get("weSaid") or 0) == len(_MLBREC["calibration"]),
   "   ✅ ...and MLB still says \"we said\" on every band",
   "the default is what keeps MLB unchanged; %s of %d bands carried it"
   % (_r9.get("weSaid"), len(_MLBREC["calibration"])))

_r9b = out("console.log(JSON.stringify({"
           "dflt: bandRow({name:'x',n:1,said:35,hit:40}),"
           "given: bandRow({name:'x',n:1,said:35,hit:40}, 'the record claimed')}));")
ck('title="we said 35%"' in (_r9b.get("dflt") or ""),
   "🔴 CALLED WITHOUT A LABEL, bandRow still says \"we said\"",
   "⛔ the parameter is OPTIONAL. A required one would have been a "
   "breaking change to MLB dressed as an addition")
ck('title="the record claimed 35%"' in (_r9b.get("given") or ""),
   "   ...and honours the label when one is passed")

# 🔴 EVERY METHOD'S BANDS, DRIVEN THROUGH THE TAB'S OWN ENTRY POINT.
# ⛔ This drove `calibration` alone, and the day the card switched method
#    that was `[]`: "no band says we said" became "no band at all" and went
#    red for the wrong reason. Now it drives `fbCalMethods` on the whole
#    record — every method, as the tab draws it — and a method with nothing
#    graded yet is REPORTED, not failed.
for _lg in ("nfl", "ncaaf"):
    _r9c = out("const h = fbCalMethods(%s);"
               "console.log(JSON.stringify({titles:[...h.matchAll("
               "/class=\"said\"[^>]*title=\"([^\"]*)\"/g)].map(m=>m[1]),"
               "bands:(h.match(/class=\"band\"/g)||[]).length}));"
               % json.dumps(REAL[_lg]))
    _t = _r9c.get("titles") or []
    ck(_t and not any("we said" in x for x in _t),
       "🔴🔴 NO %s BAND SAYS \"we said\" — driven on the real record, every method" % _lg,
       "⛔ `record.json`'s own no_model_note: \"No number here is a model "
       "output.\" Attributing it to \"we\" is a DESCRIPTIVE number in a "
       "MODEL voice. Got %s" % _t[:3])
    ck(len(_t) == len(BANDS[_lg]) and all("the record claimed" in x for x in _t),
       "   ...every one of the %d band(s) names the record instead" % len(BANDS[_lg]),
       "Got %d titles %s" % (len(_t), _t[:3]))
    for _m, _v in (REAL[_lg].get("calibration_by_method") or {}).items():
        if not _v:
            note("⚠️ %s method %r has no graded picks yet — reported, not "
                 "failed" % (_lg, _m))
    if REAL[_lg].get("card_method_current") not in (REAL[_lg].get("calibration_by_method") or {}):
        note("⚠️ %s: the current method %r has no graded picks yet — the tab "
             "says so under its own heading" % (_lg, REAL[_lg].get("card_method_current")))

section("9b. 🔴🔴 ONE LABELLED TABLE PER METHOD, AND AN EMPTY ONE SAYS SO")
# ⛔ SYNTHETIC ON PURPOSE: the real records hold one graded method today,
#    so "two methods drawn apart" cannot be driven on them yet.
_OLD = [{"bucket": "80-90%", "stated": 84.1, "w": 20, "n": 49, "pct": 40.8},
        {"bucket": "60-70%", "stated": 65.1, "w": 24, "n": 48, "pct": 50.0}]
_NEW = [{"bucket": "70-80%", "stated": 74.0, "w": 3, "n": 4, "pct": 75.0}]
_PROBE = ("const h = fbCalMethods(REC);"
          "const heads=[...h.matchAll(/Was the record right\\? <span[^>]*>&mdash; ([^<]*)</g)].map(m=>m[1]);"
          "const parts=h.split('Was the record right?').slice(1)"
          ".map(x=>(x.match(/class=\"band\"/g)||[]).length);"
          "console.log(JSON.stringify({heads, parts, empty:(h.match(/No graded\\s+picks under the ([^<]*?) yet/)||[])[1]||null,"
          "weSaid:(h.match(/we said/g)||[]).length}));")
_s1 = out(_PROBE, extra="const REC = " + json.dumps(
    {"card_method_current": "season-blend", "calibration": [],
     "calibration_by_method": {"2025-only": _OLD}}) + ";")
eq(_s1.get("heads"), ["current method", "2025-only method"],
   "🔴 the new method with nothing graded still gets its own heading, "
   "FIRST, and the old method follows under its own")
eq(_s1.get("empty"), "current method",
   "🔴🔴 ...and the empty one SAYS it has no graded picks yet",
   )
eq(_s1.get("parts"), [0, 2],
   "   the old method's bands sit under the old method's heading only")
_s2 = out(_PROBE, extra="const REC = " + json.dumps(
    {"card_method_current": "season-blend", "calibration": _NEW,
     "calibration_by_method": {"2025-only": _OLD, "season-blend": _NEW}}) + ";")
eq(_s2.get("parts"), [1, 2],
   "🔴 both methods graded: each draws ONLY its own bands — never pooled")
eq(_s2.get("empty"), None, "   ...and nothing claims to be empty")
eq(_s2.get("weSaid"), 0, "   ...and no band, in either table, says \"we said\"")
_s3 = out(_PROBE, extra="const REC = " + json.dumps(
    {"calibration": _OLD}) + ";")
eq(_s3.get("parts"), [2],
   "⚠️ a record written before the split still draws its bands, as the "
   "one method it is")

note("📌 THE CLASS, SWEPT AND REPORTED `[2026-09-17]`: of the renderers "
     "BOTH boards share — pickCard, bandRow, freshness, startedToggle, "
     "splitStarted, cardStaleNote — `bandRow` was the ONLY one with a "
     "hard-coded voice in rendered output. `pickCard` already branches on "
     "the row's own `confidence_basis` and prints 'RECORD — no model' "
     "where that is what the row is. `cardStaleNote` says 'projections' "
     "but is called only by MLB's renderPicks and renderParlays, so its "
     "voice matches its only callers. ⛔ Nothing else was fixed here.")

note("⛔ WHAT THIS DOES NOT CLAIM: that the tab LOOKS right. It claims the "
     "bands come from bandRow with football's own numbers, that a graded "
     "day can be opened, that the cache cannot serve the wrong league, "
     "and that MLB's four record functions are byte-for-byte what main "
     "has. Rendering it in a browser is still the only way to see it.")
