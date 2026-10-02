#!/usr/bin/env python3
"""
🔴 THE HEADLINE TICKER CARRIES ALL THREE LEAGUES, ON EVERY TAB, AND MOVES.

`[Sam, 2026-10-01]` *"the news at the bottom of the page isn't slowly moving
at the bottom, we need to fix that and include news from across all 3
leagues on the bottom."* A reduced-motion rule froze the bar; it read only
MLB's news under one fixed "MLB" tag; and setLeague hid it on football.

ASKED OF THE SHIPPED PAGE: the ticker's own functions, cut out of
index.html and run in node on PLANTED news files, never the live ones. The
real browser is test_league_switch.py on pr-tests' render job.

# @vacuity 🔴 nothing hides the ticker on any league or tab
#   file: index.html
#   find: // headline ticker stays up in every league (it carries all three).
#   with: const tk = document.querySelector('#tick'); if (tk) tk.style.display = mlb ? '' : 'none';
#
# @vacuity 🔴 every headline wears its own league's mark
#   file: index.html
#   find: const TICK_SRC = [['MLB', 'data/latest/news.json'], ['NFL', 'data/nfl/latest/news.json'],
#   with: const TICK_SRC = [['NFL', 'data/latest/news.json'], ['MLB', 'data/nfl/latest/news.json'],
#
# @vacuity 🔴 no one fixed league tag on the bar
#   file: index.html
#   find: <div id="tick" hidden>
#   with: <div id="tick" hidden><div class="tag">MLB</div>
#
# @vacuity 🔴 newest first by the real time, the leagues mixed
#   file: index.html
#   find: return all.sort((a, b) => tickTime(b) - tickTime(a));
#   with: return all.sort((a, b) => String(b.published).localeCompare(String(a.published)));
#
# @vacuity 🔴 a missing league file leaves the other two
#   file: index.html
#   find: jget(path).then(N => [mark, N], () => [mark, null])));
#   with: jget(path).then(N => [mark, N])));
#
# @vacuity 🔴 an empty file, or one with no items, is skipped quietly
#   file: index.html
#   find: docs.forEach(([mark, N]) => ((N && N.items) || []).filter(i => i && i.title && i.link)
#   with: docs.forEach(([mark, N]) => N.items.filter(i => i && i.title && i.link)
#
# @vacuity 🔴 half speed under reduced motion
#   file: index.html
#   find: return reduce ? 27.5 : 55;
#   with: return 55;
#
# @vacuity 🔴 no style rule freezes it under reduced motion
#   file: index.html
#   find: body{padding-bottom:44px}
#   with: body{padding-bottom:44px} @media (prefers-reduced-motion:reduce){#tick .run{animation:none;padding-left:0}}
#
# @vacuity 🔴 the rail keeps its running animation
#   file: index.html
#   find: #tick .run{display:inline-block;padding-left:100%;animation:tickmove 180s linear infinite}
#   with: #tick .run{display:inline-block;padding-left:100%}
#
# @vacuity pause on hover is kept
#   file: index.html
#   find: #tick:hover .run{animation-play-state:paused}
#   with: #tick:hover .run{animation-play-state:running}
#
# @vacuity 🔴 an unchanged refresh leaves the bar where it is
#   file: index.html
#   find: if (html === TICK_HTML) return;
#   with: if (html === null) return;
#
# @vacuity a refresh with new headlines brings them in
#   file: index.html
#   find: if (html === TICK_HTML) return;
#   with: if (TICK_HTML) return;
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section  # noqa: E402

import jsblock  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()
CSS = jsblock.css_rules(PAGE)
# Sam's three files and marks, 2026-10-01: the REQUIREMENT, so written here.
FILES = {"MLB": "data/latest/news.json", "NFL": "data/nfl/latest/news.json",
         "CFB": "data/ncaaf/latest/news.json"}
WHO, WHEN = {}, {}


def doc(lg, times):
    """A planted news file. No title names a league, so no mark can be read off one."""
    for t in times:
        WHO["Story %d" % (len(WHO) + 1)], WHEN["Story %d" % len(WHO)] = lg, t
    return {"items": [{"title": k, "link": "https://example.test/" + k[6:], "source": "Desk",
                       "published": WHEN[k]} for k in list(WHO)[-len(times):]]}


D = "2026-10-02T%s:00Z"
MLB = doc("MLB", [D % t for t in ("00:50", "00:35", "00:20", "00:05")])
NFL = doc("NFL", [D % t for t in ("00:45", "00:30", "00:15", "00:00")])
# 🔴 one college time carries an OFFSET: the newest headline of all, and last by text.
CFB = doc("CFB", ["2026-10-01T21:30:00-04:00"] + [D % t for t in ("00:40", "00:25", "00:10")])
FRESH = doc("MLB", [D % "02:00"])["items"][0]
ALL = {FILES["MLB"]: MLB, FILES["NFL"]: NFL, FILES["CFB"]: CFB}
PLANT = {"all": [ALL], "reduce": [ALL], "missing": [{FILES["MLB"]: MLB, FILES["CFB"]: CFB}],
         "empty": [{FILES["MLB"]: {"n": 0}, FILES["NFL"]: NFL, FILES["CFB"]: {"items": []}}],
         "refresh": [ALL, ALL],
         "renew": [ALL, ALL, dict(ALL, **{FILES["MLB"]: {"items": [FRESH] + MLB["items"]}})]}
DRIVER = r"""
const S = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
let DOCS = {}, REDUCE = false, run = null, tick = null;
const $ = q => q === '#tickrun' ? run : q === '#tick' ? tick : null;
const window = {matchMedia: q => ({matches: REDUCE && /prefers-reduced-motion:\s*reduce/.test(q)})};
const requestAnimationFrame = f => f();
async function jget(u){ if (DOCS[u] === undefined) throw new Error(u + ' -> 404'); return DOCS[u]; }
function page(){ eval(S.code); return loadTicker; }   // a fresh page: its own TICK_HTML
(async () => {
  const out = {};
  for (const [name, loads] of Object.entries(S.plant)){
    REDUCE = name === 'reduce'; tick = {hidden: true};
    const st = {}, sets = [];
    run = {scrollWidth: 11000, writes: 0, h: '',
           style: new Proxy(st, {set(t, k, v){ t[k] = v; sets.push(k); return true; }})};
    Object.defineProperty(run, 'innerHTML', {get(){ return this.h; }, set(v){ this.h = v; this.writes++; }});
    const load = page(); let err = null;
    for (const d of loads){ DOCS = d; try { await load(); } catch(e){ err = String(e); } }
    out[name] = {html: run.h, writes: run.writes, hidden: tick.hidden, dur: st.animationDuration, sets, err};
  }
  process.stdout.write(JSON.stringify(out));
})();
"""
_m = re.search(r"\nconst TICK_SRC = .*?;\r?\n", SRC, re.S)
CODE = "\n".join([_m.group(0) if _m else "", "let TICK_HTML = '';"]
                 + [jsblock.js_block(n, PAGE) if re.search(r"\n(async )?function %s\(" % n, SRC)
                    else "" for n in ("tickTime", "tickItems", "tickHtml", "tickSpeed", "loadTicker")])
with tempfile.TemporaryDirectory(prefix="ticker-") as tmp:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"code": CODE, "plant": PLANT}, open(os.path.join(tmp, "d.json"), "w"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, timeout=120)
R = json.loads(r.stdout) if r.returncode == 0 else {}
R = {k: R.get(k) or {"html": "", "writes": 0, "hidden": True, "dur": None, "sets": [], "err": "-"}
     for k in PLANT}
if r.returncode:
    note("⛔ node did not run the ticker: %s" % (r.stderr or "")[-300:])


def shown(k):
    """[(mark, title)] as the bar shows them, once (the loop holds the list twice)."""
    a = re.findall(r'<span class="lg">([^<]*)</span>([^<]*?) <span class="src">', R[k]["html"])
    return a[:len(a) // 2] if a[:len(a) // 2] == a[len(a) // 2:] else a


def ok(k, lgs, n):
    return sorted({m for m, _t in shown(k)}) == lgs and len(shown(k)) == n \
        and not R[k]["hidden"] and R[k]["err"] is None


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 ON EVERY LEAGUE AND EVERY TAB")
_js = re.sub(r"/\*.*?\*/", "", SRC[SRC.index("<script>"):SRC.rindex("</script>")], flags=re.S)
_refs = [ln.strip() for ln in _js.splitlines() if not ln.strip().startswith("//")
         and re.search(r"#tick\b|getElementById\(\s*['\"]tick['\"]", ln)]
_hide = [s for s, d in CSS.items() if "#tick" in s + d and re.search(r"display:\s*none|visibility:\s*hidden", d)]
ck("🔴 nothing hides the ticker on any league or tab: the page names it once, to show it",
   _refs == ["$('#tick').hidden = false;"] and not _hide,
   "script lines naming #tick: %s; style rules hiding it: %s" % (_refs, _hide))

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 ALL THREE LEAGUES, NEWEST FIRST, EACH HEADLINE WEARING ITS OWN")
_all = [(WHO[t], t) for d in (MLB, NFL, CFB) for t in (i["title"] for i in d["items"])]
ck("🔴 every headline wears its own league's mark (MLB, NFL, CFB), from all three files",
   sorted(shown("all")) == sorted(_all) and ok("all", ["CFB", "MLB", "NFL"], 12), str(shown("all")))
_bar = SRC[SRC.index('<div id="tick"'):SRC.index("</main>")]
ck("🔴 no one fixed league tag on the bar: the only text is the headlines'",
   not re.sub(r"<[^>]+>|\s", "", _bar), _bar[:160])
_at = {t: datetime.fromisoformat(WHEN[t].replace("Z", "+00:00")) for _lg, t in _all}
ck("🔴 newest first by the real time, the leagues mixed (an offset sorts by its moment)",
   [t for _m, t in shown("all")] == sorted(_at, key=_at.get, reverse=True)
   and shown("all")[0] == ("CFB", "Story 9"), str([t for _m, t in shown("all")]))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A MISSING OR EMPTY FILE IS SKIPPED; THE OTHERS STILL SHOW")
ck("🔴 a missing league file leaves the other two", ok("missing", ["CFB", "MLB"], 8),
   "%s, error %s" % (shown("missing"), R["missing"]["err"]))
ck("🔴 an empty file, or one with no items, is skipped quietly", ok("empty", ["NFL"], 4),
   "%s, error %s" % (shown("empty"), R["empty"]["err"]))

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 IT MOVES FOR EVERYONE: SLOWLY, AND NEVER FROZEN")
ck("🔴 about 55 px a second off the real width, half that under reduced motion, never stopped",
   (R["all"]["dur"], R["reduce"]["dur"]) == ("200s", "400s")
   and set(R["all"]["sets"] + R["reduce"]["sets"]) == {"animationDuration"},
   "11000 px: %s, and %s under reduced motion; styles set %s"
   % (R["all"]["dur"], R["reduce"]["dur"], R["reduce"]["sets"]))
_stop = [s for s, d in CSS.items() if "#tick" in s + d and s != "#tick:hover .run"
         and re.search(r"animation(-name)?:\s*none|play-state:\s*paused", d)]
ck("🔴 no style rule freezes it, under reduced motion or otherwise, and the rail keeps its animation",
   not _stop and re.search(r"animation:\s*tickmove\b[^;]*\binfinite", CSS.get("#tick .run", "")),
   "rules stopping it: %s; #tick .run: %r" % (_stop, CSS.get("#tick .run")))
ck("pause on hover is kept",
   re.sub(r"\s|;$", "", CSS.get("#tick:hover .run", "")) == "animation-play-state:paused",
   repr(CSS.get("#tick:hover .run")))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 AN UNCHANGED REFRESH LEAVES IT WHERE IT IS")
ck("🔴 a refresh with the same headlines does not rewrite the bar or reset its speed",
   R["refresh"]["writes"] == 1 and R["refresh"]["sets"] == ["animationDuration"],
   "written %d time(s), speed set %d" % (R["refresh"]["writes"], len(R["refresh"]["sets"])))
ck("a refresh with new headlines brings them in",
   R["renew"]["writes"] == 2 and ("MLB", FRESH["title"]) in shown("renew"),
   "written %d time(s)" % R["renew"]["writes"])
