#!/usr/bin/env python3
"""
🔴 EVERY FETCH ON THE PAGE ASKS THE SERVER FOR THE NEWEST FILE.

`[measured 2026-10-17]` While #294 was checked live, the college card was
rebuilt at 16:54Z and the page kept drawing the 16:36Z card for minutes.
The page's one data loader was `jget(u){ const r = await fetch(u); ... }`:
a plain fetch, so the browser served its own cached copy, and GitHub Pages
sends `Cache-Control: max-age=600`, so a visitor could see the previous
card for up to 10 minutes after a rebuild. A fetch with `cache: 'no-store'`
got the new card at once. It was never #294's doing: every tab of every
league reads through `jget` / `jgetGz`.

✅ THE FIX: every fetch passes a cache mode that goes to the server.
`'no-cache'` revalidates by the file's ETag (an unchanged file is a 304,
not a download); `'no-store'` and `'reload'` always download. `'default'`,
`'force-cache'`, `'only-if-cached'` or no mode at all may serve a stale
copy. ⛔ No query-string buster (`?t=` + Date.now()): it defeats the ETag
and downloads every file in full on every load.

🔴 THE GUARD IS ON THE CLASS, NOT ON `jget`. A check naming the one loader
that broke covers exactly that loader (rules 246, 130), and the page had
four plain fetches, not one. So this file reads EVERY `fetch(` in the
page's own code, comments removed (`jsblock.script_code`), and also fails
if the page reaches the network some way the scan cannot see: `fetch`
passed around by name, or XMLHttpRequest. Then it runs the page's own
`jget` and `jgetGz` in node against a recording fetch, so the option is
proved to reach the network call and the error text is proved unchanged.

⛔ IT ASKS THE CODE, NEVER PRODUCTION: no request to GitHub Pages is made.

# @vacuity 🔴 every fetch on the page passes a cache mode that goes to the server
#   file: index.html
#   find: async function jget(u){ const r = await fetch(u, {cache: 'no-cache'}); if(!r.ok)
#   with: async function jget(u){ const r = await fetch(u); if(!r.ok)
#
# @vacuity 🔴 every fetch on the page passes a cache mode that goes to the server (jgetGz, the gzipped loader)
#   file: index.html
#   find: fetch(u, {cache: 'no-cache'});   // revalidated, as jget's (test_fetch_fresh.py)
#   with: fetch(u);   // revalidated, as jget's (test_fetch_fresh.py)
#
# @vacuity 🔴 every fetch on the page passes a cache mode that goes to the server (a HEAD probe too)
#   file: index.html
#   find: fetch(fbPath(y, sd), {method: 'HEAD', cache: 'no-cache'})
#   with: fetch(fbPath(y, sd), {method: 'HEAD'})
#
# @vacuity 🔴 every fetch on the page passes a cache mode that goes to the server (a NEW loader nobody named)
#   file: index.html
#   find: try { BOARD = await jget('data/latest/board.json'); }
#   with: try { BOARD = await (await fetch('data/latest/board.json')).json(); }
#
# @vacuity 🔴 every fetch on the page passes a cache mode that goes to the server (a mode that may serve a stale copy)
#   file: index.html
#   find: {cache: 'no-store'});
#   with: {cache: 'force-cache'});
#
# @vacuity nothing on the page reaches the network around the scan
#   file: index.html
#   find: try { FRESH = await jget('data/latest/freshness.json'); }
#   with: try { const get = fetch; FRESH = await (await get('data/latest/freshness.json')).json(); }
#
# @vacuity no fetch defeats the ETag with a query-string buster
#   file: index.html
#   find: try { FRESH = await jget('data/latest/freshness.json'); }
#   with: try { FRESH = await jget('data/latest/freshness.json?t=' + Date.now()); }
"""
import base64
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section  # noqa: E402

import jsblock  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")

# The cache modes that go to the server every time (Fetch standard, Request.cache).
FRESH_MODES = {"no-cache", "no-store", "reload"}
LOADERS = ("jget", "jgetGz")

# ══════════════════════════════════════════════════════════════════════
section("1. THE PAGE'S CODE IS READ, AND BOTH LOADERS ARE IN IT")
CODE = jsblock.script_code(PAGE)
SITES = jsblock.call_sites(CODE, "fetch")
ck(len(CODE) > 50000 and SITES,
   "the page's script is read, comments removed (%d chars, %d fetch call(s))"
   % (len(CODE), len(SITES)),
   "⛔ an empty read checks nothing and passes (rule 67)")
_in = {f: len(jsblock.call_sites(jsblock.strip_js(jsblock.js_block(f, PAGE)), "fetch"))
       for f in LOADERS}
ck(all(n == 1 for n in _in.values()),
   "   ...and the scan finds the one fetch inside each of %s" % ", ".join(LOADERS),
   "fetch calls found per loader: %s" % _in)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 EVERY FETCH GOES TO THE SERVER")


def mode_problem(args):
    """None when the call's options carry a cache mode in FRESH_MODES."""
    if len(args) < 2:
        return "no options, so the browser may serve its cached copy"
    opt = args[1]
    if not (opt.startswith("{") and opt.endswith("}")):
        return "options are not written in the call (%s), so the mode cannot be read" % opt
    if "..." in opt:
        return "a spread in the options could override the cache mode"
    modes = re.findall(r"""(?<![\w$])cache\s*:\s*(['"])([a-z-]+)\1""", opt)
    if not modes:
        return "no cache mode"
    bad = [m for _q, m in modes if m not in FRESH_MODES]
    return ("cache mode %s may serve a stale copy" % bad) if bad else None


_bad = [(text[:90], why) for text, args in SITES for why in [mode_problem(args)] if why]
ck(SITES and not _bad,
   "🔴 every fetch on the page passes a cache mode that goes to the server "
   "(%d call(s): %s)" % (len(SITES), ", ".join(sorted(FRESH_MODES))),
   "⛔ GitHub Pages sends max-age=600: a fetch without one of these can draw the previous "
   "card for up to 10 minutes after a rebuild. Offending: %s" % _bad)
note("   modes in use: %s" % sorted({m for _t, a in SITES if len(a) > 1
                                     for _q, m in re.findall(r"""cache\s*:\s*(['"])([a-z-]+)\1""",
                                                             a[1])}))

# ══════════════════════════════════════════════════════════════════════
section("3. NOTHING READS THE NETWORK AROUND THE SCAN")
_alias = [CODE[max(0, m.start() - 40):m.end() + 20]
          for m in re.finditer(r"(?<![\w$])fetch(?![\w$])(?!\s*\()", CODE)]
_other = re.findall(r"XMLHttpRequest|new EventSource|importScripts|\$\.(?:get|getJSON|ajax)\(",
                    CODE)
ck(not _alias and not _other,
   "nothing on the page reaches the network around the scan "
   "(fetch is only ever called, never passed by name; no XMLHttpRequest)",
   "⛔ a loader that escapes the scan escapes the rule. fetch by name: %s; other loaders: %s"
   % (_alias, _other))

# ══════════════════════════════════════════════════════════════════════
section("4. NO QUERY-STRING BUSTER")
# ⚠️ A value that changes on EVERY load, never a date the URL needs: MLB's standings
#    call asks for `season=${new Date().getFullYear()}`, which is correct, and an
#    earlier `new Date` here fired on it (a guard that fires on correct code).
BUSTER = re.compile(r"Date\.now|Math\.random|performance\.now|crypto\.|\bgetTime\s*\("
                    r"|\bvalueOf\s*\(|\+\s*new Date\b|\$\{\s*new Date\s*\(\s*\)\s*\}")
_bust = [text[:90] for f in ("fetch",) + LOADERS
         for text, args in jsblock.call_sites(CODE, f)
         if args and BUSTER.search(args[0])]
ck(not _bust,
   "no fetch defeats the ETag with a query-string buster",
   "⛔ a URL that changes on every load is downloaded in full every time; the cache mode "
   "already gets the newest file. Found: %s" % _bust)

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 THE PAGE'S OWN jget AND jgetGz, RUN IN NODE")
DRIVER = r"""
const fs = require('fs');
const D = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const CALLS = [];
let REPLY = null;
async function fetch(u, init){
  CALLS.push([u, init === undefined ? null : init]);
  return REPLY;
}
const gz = Buffer.from(D.gz, 'base64');
const ok = (doc) => ({ok: true, status: 200, json: async () => doc,
                      arrayBuffer: async () => gz.buffer.slice(gz.byteOffset, gz.byteOffset + gz.length)});
const missing = {ok: false, status: 404, json: async () => ({}), arrayBuffer: async () => new ArrayBuffer(0)};
const page = new Function('fetch', D.jget + '\n' + D.jgetGz + '\nreturn {jget, jgetGz};')(fetch);
async function run(fn, u, reply){
  CALLS.length = 0; REPLY = reply;
  let got = null, err = null;
  try { got = await page[fn](u); } catch (e) { err = String(e.message); }
  return {got, err, calls: CALLS.slice()};
}
(async () => {
  const out = {
    jget: await run('jget', 'data/latest/board.json', ok({who: 'board'})),
    jget404: await run('jget', 'data/nfl/latest/none.json', missing),
    jgetGz: await run('jgetGz', 'data/latest/props.json.gz', ok(null)),
    jgetGz404: await run('jgetGz', 'data/ncaaf/latest/none.json.gz', missing),
  };
  console.log(JSON.stringify(out));
})().catch(e => { console.error(String(e && e.stack || e)); process.exit(1); });
"""
_gz = base64.b64encode(gzip.compress(json.dumps({"who": "props"}).encode())).decode()
tmp = tempfile.mkdtemp(prefix="fetchfresh-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump({"jget": jsblock.js_block("jget", PAGE), "jgetGz": jsblock.js_block("jgetGz", PAGE),
               "gz": _gz}, open(os.path.join(tmp, "d.json"), "w", encoding="utf-8"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, encoding="utf-8", timeout=120)
    ck(r.returncode == 0, "the page's own jget and jgetGz ran in node", (r.stderr or "")[-300:])
    R = json.loads(r.stdout) if r.returncode == 0 else {}
finally:
    shutil.rmtree(tmp, ignore_errors=True)


def one_call(case, url):
    """[url, options] of the one fetch a case made, when it was to `url` exactly."""
    calls = (R.get(case) or {}).get("calls") or []
    return calls[0] if len(calls) == 1 and calls[0][0] == url else None


for case, url, doc in (("jget", "data/latest/board.json", {"who": "board"}),
                       ("jgetGz", "data/latest/props.json.gz", {"who": "props"})):
    init = (one_call(case, url) or [None, None])[1]
    ck(isinstance(init, dict) and init.get("cache") in FRESH_MODES
       and (R.get(case) or {}).get("got") == doc,
       "🔴 %s asks for %s with cache %r, at that exact URL, and returns the file"
       % (case, url, (init or {}).get("cache")),
       "the call it made: %s; it returned %s"
       % ((R.get(case) or {}).get("calls"), (R.get(case) or {}).get("got")))
for case, url in (("jget404", "data/nfl/latest/none.json"),
                  ("jgetGz404", "data/ncaaf/latest/none.json.gz")):
    ck((R.get(case) or {}).get("err") == url + " -> 404" and one_call(case, url) is not None,
       "   ...and a missing file still throws %r, as before" % (url + " -> 404"),
       "threw %r" % (R.get(case) or {}).get("err"))
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that GitHub Pages answers a revalidation with a 304, "
     "or how fast a phone redraws. It claims every request the page makes goes to the "
     "server instead of the browser's 10-minute copy.")
