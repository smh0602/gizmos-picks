#!/usr/bin/env python3
"""The news collector, after it was made league-aware.

🔴 WHY THIS EXISTS. `NEWS_FEEDS` was a LIST and is now a DICT keyed by
league. ⛔ THAT TOUCHES A LIVE MLB FEED ON A LIVE PAGE. The refactor is
worth nothing if it costs MLB its news tab, so the first thing pinned here
is that MLB's three feeds are byte-identical to what has always shipped.

✅ WHAT THIS PINS, AND WHY EACH WOULD LOOK FINE IF BROKEN:
  1. 🔴 MLB's feed list is UNCHANGED -- exact sources, exact URLs, exact
     order. A typo here breaks a working page and nothing else fails.
  2. ⛔ A league with NO adopted feed writes NOTHING. An empty news.json
     overwriting a real one is worse than no file, and football has no
     adopted feed until a probe report has been READ.
  3. The one parser handles the shapes the real feeds actually use --
     `<description>`, `content:encoded`, media art with NO file
     extension, and an undated item.
  4. 🔴 THE PROBE AND THE COLLECTOR SHARE THE PARSER. Checked
     STRUCTURALLY, via AST: `probe_news` must not fetch or parse XML on
     its own. ⛔ A probe with its own copy measures code that will never
     run -- it is a check that cannot fail on the defect it exists to
     catch.
  5. The bars are applied as written and are NOT relaxed by the code.

⚠️ No network. Every feed here is a string.
"""
import ast
import gzip
import io
import json
import os
import sys

os.environ.setdefault("LEAGUE", "mlb")
import collect as C

fails = []


def eq(got, want, label):
    ok = got == want
    print(f"  {'ok  ' if ok else '🔴 FAIL'} {label:<52} {got!r}")
    if not ok:
        fails.append(f"{label} (got {got!r} want {want!r})")


print("1. 🔴 MLB's LIVE FEED LIST IS UNTOUCHED BY THE REFACTOR")
eq(C.NEWS_FEEDS["mlb"], [
    ("MLB.com", "https://www.mlb.com/feeds/news/rss.xml"),
    ("ESPN MLB", "https://www.espn.com/espn/rss/mlb/news"),
    ("CBS Sports", "https://www.cbssports.com/rss/headlines/mlb/"),
], "the three MLB feeds, same order")

print("\n2. ⛔ A LEAGUE WITH NO ADOPTED FEED WRITES NOTHING")
for lg in ("nfl", "ncaaf"):
    eq(C.NEWS_FEEDS.get(lg), [], f"{lg} ships no feed until a probe is read")
wrote = []
old_write, old_league = C.write, C.LEAGUE
C.write = lambda *a, **k: wrote.append(a)
try:
    C.LEAGUE = "nfl"
    eq(C.collect_news(), None, "returns None on an empty list")
    eq(wrote, [], "🔴 and wrote NO file at all")
finally:
    C.write, C.LEAGUE = old_write, old_league

print("\n3. the one parser, on the shapes the real feeds use")
RSS = """<?xml version="1.0"?>
<rss xmlns:media="http://search.yahoo.com/mrss/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
 <channel>
  <item>
   <title>Team wins game</title><link>https://x.test/1</link>
   <pubDate>Wed, 02 Sep 2026 18:30:00 GMT</pubDate>
   <description>&lt;p&gt;Some &lt;b&gt;html&lt;/b&gt; body&amp;nbsp;here.&lt;/p&gt;</description>
   <media:thumbnail url="https://img.test/upload/t_16x9/w_1024/abc"/>
  </item>
  <item>
   <title>Undated item</title><link>https://x.test/2</link>
   <content:encoded>Body from content encoded</content:encoded>
  </item>
  <item>
   <title>No link so dropped</title>
  </item>
 </channel>
</rss>"""


class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False


old_open = C.urllib.request.urlopen
C.urllib.request.urlopen = lambda req, timeout=None: _Resp(RSS.encode())
try:
    got = C._news_items("Test", "https://x.test/rss")
finally:
    C.urllib.request.urlopen = old_open

eq(len(got), 2, "the item with no link is dropped")
eq(got[0]["title"], "Team wins game", "title read")
eq(got[0]["published"], "2026-09-02T18:30:00Z", "pubDate -> UTC iso")
eq(got[0]["summary"], "Some html body here.", "html and entities stripped")
eq(got[0]["image"], "https://img.test/upload/t_16x9/w_1024/abc",
   "🔴 art with NO file extension is still art")
eq(got[1]["published"], None, "an undated item is None, not a crash")
eq(got[1]["summary"], "Body from content encoded", "content:encoded read")
eq("image" in got[1], False, "no art -> the key is absent, not null")

print("\n4. 🔴 THE PROBE DOES NOT CARRY ITS OWN PARSER (structural, via AST)")
tree = ast.parse(open(C.__file__).read())
probe = next((n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "probe_news"), None)
eq(probe is not None, True, "probe_news exists")
if probe:
    src = ast.dump(probe)
    eq("urlopen" in src, False, "⛔ it does not fetch on its own")
    eq("fromstring" in src, False, "⛔ it does not parse XML on its own")
    calls = {n.func.id for n in ast.walk(probe)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    eq("_news_items" in calls, True, "✅ it calls the collector's parser")

print("\n5. the bars are what the file says, and the code uses them")
eq((C.NEWS_MIN_ITEMS, C.NEWS_MIN_DATED, C.NEWS_MIN_LINKED), (8, 0.90, 1.00),
   "bars fixed before the probe ran")
if probe:
    names = {n.id for n in ast.walk(probe) if isinstance(n, ast.Name)}
    for b in ("NEWS_MIN_ITEMS", "NEWS_MIN_DATED", "NEWS_MIN_LINKED"):
        eq(b in names, True, f"  {b} is actually read")
    # ⛔ the report must carry the SAMPLE -- numbers alone cannot tell you
    # a feed is the right sport, and that is the failure this guards.
    consts = {n.value for n in ast.walk(probe)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    eq("sample" in consts, True, "🔴 the report carries sample headlines")

print()
if fails:
    print(f"🔴 {len(fails)} FAILED:")
    for f in fails:
        print("   " + f)
    sys.exit(1)
print("✅ news collector OK — MLB untouched, football fails closed")
