#!/usr/bin/env python3
"""📰 KEEPING THE NEWS WE ALREADY PULL.

🔴 WE FETCHED IT HOURLY, FREE, AND KEPT NONE OF IT. `latest/news.json` is
overwritten in place 24 times a day, and on `main` before this
`find data -name "news*" -not -path "*/latest/*"` returned NOTHING.
`daystore.archive()` already existed and already served two callers.

⛔ WHAT THIS FILE DOES **NOT** CLAIM: that the news predicts anything.
Rule 284 — a backtest asks whether a number PREDICTS, never whether it is
correct. There is no archive to test against yet, which is the whole
point of shipping the archive first.

# @vacuity ⛔ `first_seen` is OUR clock, never the outlet's `published`
#   file: collect.py
#   find:             row["first_seen"] = pulled_at
#   with:             row["first_seen"] = it.get("published")
#
# @vacuity the archive keeps only what THIS pull saw first
#   file: collect.py
#   find:         prev = seen.get(k)
#   with:         prev = None
#
# @vacuity ⛔ dedupe is on the normalised LINK, never the title
#   file: collect.py
#   find:         k = _news_link_key(it.get("link"))
#   with:         k = it.get("title")
#
# @vacuity a re-title is a REVISION, not a silent drop
#   file: collect.py
#   find:             row["revision"] = int(prev.get("revision") or 0) + 1
#   with:             continue
#
# @vacuity ...and a revision keeps the ORIGINAL first_seen
#   file: collect.py
#   find:             row["first_seen"] = prev.get("first_seen")
#   with:             row["first_seen"] = pulled_at
#
# @vacuity 🔴 the dated archive has a freshness contract entry
#   file: freshness.py
#   find:         ("news-archive", ("dir", f"{data}/{utc_day}/news"), T["news"], False,
#   with:         ("news-archive-DISABLED", ("file", f"{latest}/news.json"), T["news"], False,
#
# @vacuity ⛔ ONE CLOCK — the day scanned and the day written are the same
#   file: collect.py
#   find:     day_dir = os.path.join(data, when.strftime("%Y-%m-%d"), "news")
#   with:     day_dir = os.path.join(data, now().strftime("%Y-%m-%d"), "news")
"""
import ast
import datetime
import glob
import gzip
import io
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import collect                                            # noqa: E402
import freshness as F                                     # noqa: E402

UTC = datetime.timezone.utc
CSRC = io.open(os.path.join(ROOT, "collect.py"), encoding="utf-8").read()
Q = lambda *a, **k: None                                  # noqa: E731


def T(h, m=0, day=18):
    return datetime.datetime(2026, 9, day, h, m, tzinfo=UTC)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def item(link, title, published="2026-09-18T12:00:00Z", source="X"):
    return {"link": link, "title": title, "published": published,
            "source": source, "summary": "s", "image": "i"}


def read(p):
    with gzip.open(p, "rt") as fh:
        return json.load(fh)


def files(d, lg_dir=""):
    return sorted(glob.glob(os.path.join(d, lg_dir, "*", "news",
                                         "*.json.gz")))


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE ARCHIVE IS THE DELTA, AND IT IS WRITE-ONCE")
# ══════════════════════════════════════════════════════════════════════
d = tempfile.mkdtemp()
A = [item("https://ex.com/a", "Alpha"), item("https://ex.com/b", "Bravo")]
p1, w1, n1, r1 = collect.archive_news(A, iso(T(18)), data=d, log=Q, when=T(18))
ck("the first pull archives everything it saw",
   w1 is True and n1 == len(A) and r1 == 0,
   "wrote=%s new=%s revised=%s" % (w1, n1, r1))
_first_bytes = open(p1, "rb").read()

# ⛔ AN OVERLAPPING SECOND PULL KEEPS ONLY WHAT IS NEW.
B = A + [item("https://ex.com/c", "Charlie")]
p2, w2, n2, r2 = collect.archive_news(B, iso(T(19)), data=d, log=Q, when=T(19))
ck("🔴 the second pull archives ONLY the item it had not seen",
   w2 is True and n2 == 1 and r2 == 0,
   "⛔ an hourly pull is ~97%% repeats; archiving the snapshot would "
   "store the same headlines 24 times a day. new=%s" % (n2,))
_d2 = read(p2)
ck("...and it is the right item",
   [i["title"] for i in _d2["items"]] == ["Charlie"],
   "items=%s" % ([i["title"] for i in _d2["items"]],))
ck("🔴 ...and the FIRST file is byte-identical afterwards",
   open(p1, "rb").read() == _first_bytes,
   "⛔ write-once. daystore refuses to rewrite, which is why the delta "
   "shape is the one that fits it.")
ck("...two readings on disk, one per pull", len(files(d)) == 2,
   "files=%s" % ([os.path.relpath(f, d) for f in files(d)],))

# ⛔ TWO PULLS INSIDE THE SAME MINUTE — the second LEAVES THE FIRST ALONE.
_before = open(p2, "rb").read()
p3, w3, n3, r3 = collect.archive_news(
    B + [item("https://ex.com/z", "Zulu")], iso(T(19)), data=d, log=Q,
    when=T(19))
ck("🔴 a second pull in the SAME MINUTE writes nothing",
   w3 is False and p3 == p2,
   "⛔ daystore's contract, asserted through THIS caller. wrote=%s" % (w3,))
ck("...and the existing reading is untouched",
   open(p2, "rb").read() == _before, "the minute's file is write-once")
ck("...and no third file appeared", len(files(d)) == 2,
   "files=%s" % ([os.path.relpath(f, d) for f in files(d)],))
shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 first_seen IS OUR CLOCK, NEVER THE OUTLET'S")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `published` is the outlet's claim about when it WROTE. `first_seen`
#    is when WE could have known. "Did the news precede the move" is a
#    question about what was KNOWABLE, so answering it with `published`
#    would answer an easier question and flatter every result.
d = tempfile.mkdtemp()
_OLD = "2026-09-01T00:00:00Z"          # published long before we saw it
p, _w, _n, _r = collect.archive_news(
    [item("https://ex.com/a", "Alpha", published=_OLD)],
    iso(T(18)), data=d, log=Q, when=T(18))
_it = read(p)["items"][0]
ck("🔴 first_seen is the pull time",
   _it["first_seen"] == iso(T(18)),
   "first_seen=%r pull=%r" % (_it["first_seen"], iso(T(18))))
ck("🔴 ...and it is NOT the published time",
   _it["first_seen"] != _it["published"],
   "⛔ published %r is 17 days before we saw it. Using it would make "
   "every story look like it preceded every move." % (_it["published"],))
ck("⚠️ BOTH are recorded, and neither is derived from the other",
   _it.get("published") == _OLD and bool(_it.get("first_seen")),
   "published=%r first_seen=%r" % (_it.get("published"), _it.get("first_seen")))
shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("3. ⛔ DEDUPE ON THE NORMALISED LINK, NOT THE TITLE")
# ══════════════════════════════════════════════════════════════════════
for _a, _b in (("https://WWW.EX.com/a", "https://www.ex.com/a"),
               ("https://ex.com/a?utm_source=rss", "https://ex.com/a"),
               ("https://ex.com/a#frag", "https://ex.com/a")):
    ck("%r and %r are the same story" % (_a[:34], _b[:28]),
       collect._news_link_key(_a) == collect._news_link_key(_b),
       "⛔ a tracking parameter is not a new story. %r vs %r"
       % (collect._news_link_key(_a), collect._news_link_key(_b)))
ck("...but a different path is NOT",
   collect._news_link_key("https://ex.com/a")
   != collect._news_link_key("https://ex.com/b"),
   "over-normalising would silently drop real stories")

d = tempfile.mkdtemp()
collect.archive_news([item("https://ex.com/a?utm_source=rss", "Alpha")],
                     iso(T(18)), data=d, log=Q, when=T(18))
_p, _w, _n, _r = collect.archive_news(
    [item("https://ex.com/a", "Alpha")], iso(T(19)), data=d, log=Q,
    when=T(19))
ck("🔴 the same story with a tracking parameter is not re-archived",
   _n == 0 and _r == 0,
   "⛔ new=%s revised=%s — it would double every syndicated item" % (_n, _r))
shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 A RE-TITLE IS A CORRECTION, KEPT AS A REVISION")
# ══════════════════════════════════════════════════════════════════════
# ⛔ NOT DROPPED (the change would be invisible) and NOT OVERWRITTEN
#    (write-once, and the earlier reading is the evidence).
d = tempfile.mkdtemp()
collect.archive_news([item("https://ex.com/a", "Ruled OUT")],
                     iso(T(18)), data=d, log=Q, when=T(18))
p, w, n, r = collect.archive_news(
    [item("https://ex.com/a", "Ruled QUESTIONABLE")],
    iso(T(19)), data=d, log=Q, when=T(19))
_rev = (read(p)["items"] or [{}])[0]
ck("🔴 the corrected story is archived, not dropped",
   w is True and r == 1 and n == 0,
   "wrote=%s new=%s revised=%s" % (w, n, r))
ck("...as a revision, counted",
   _rev.get("revision") == 1, "revision=%r" % (_rev.get("revision"),))
ck("...under the SAME link", _rev.get("link_key")
   == collect._news_link_key("https://ex.com/a"),
   "link_key=%r" % (_rev.get("link_key"),))
ck("🔴 ...and first_seen STAYS the original",
   _rev.get("first_seen") == iso(T(18)),
   "⛔ it is the same story — when we could FIRST have known did not "
   "change. first_seen=%r" % (_rev.get("first_seen"),))
ck("...with the moment of the correction recorded separately",
   _rev.get("revised_at") == iso(T(19)),
   "revised_at=%r" % (_rev.get("revised_at"),))
ck("...and the previous wording kept, so the change is VISIBLE",
   _rev.get("previous_title") == "Ruled OUT",
   "⛔ 'ruled out' becoming 'questionable' is the whole signal. "
   "previous_title=%r" % (_rev.get("previous_title"),))
shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ ONE CLOCK — THE DAY SCANNED IS THE DAY WRITTEN")
# ══════════════════════════════════════════════════════════════════════
# 🔴 FOUND BY DRIVING IT, NOT BY READING IT. The seen-set came from this
#    module's `now()` while the path came from `daystore`'s own clock.
# ⛔ Across UTC midnight those disagree: the seen-set is read from one day,
#    the file lands in the other, and EVERY ITEM RE-ARCHIVES AS NEW —
#    a duplicated day of headlines in the only dataset this exists for.
# ⛔ THE FIXTURE DATE MUST NOT BE TODAY, AND MY FIRST VERSION'S WAS.
#    With `when` on today's date the two clocks AGREE, so the mutation
#    that restores the bug changed nothing and the harness called this
#    declaration VACUOUS — correctly. ✅ The date is DERIVED from the real
#    clock so it is always a different day, and never a literal that goes
#    stale tomorrow.
d = tempfile.mkdtemp()
_REAL_TODAY = datetime.datetime.now(UTC)
_OTHER = (_REAL_TODAY - datetime.timedelta(days=3)).replace(
    hour=23, minute=59, second=0, microsecond=0)
_OTHER_DAY = _OTHER.strftime("%Y-%m-%d")
note("driving on %s, which is deliberately NOT today (%s)"
     % (_OTHER_DAY, _REAL_TODAY.strftime("%Y-%m-%d")))
ck("⚠️ the fixture day really is not today",
   _OTHER_DAY != _REAL_TODAY.strftime("%Y-%m-%d"),
   "⛔ if these are equal this whole section proves nothing")
collect.archive_news([item("https://ex.com/a", "Alpha")], iso(_OTHER),
                     data=d, log=Q, when=_OTHER)
_p, _w, _n, _r = collect.archive_news(
    [item("https://ex.com/a", "Alpha")], iso(_OTHER), data=d, log=Q,
    when=_OTHER)
ck("🔴 the same minute's seen-set and path agree",
   _n == 0 and _w is False,
   "⛔ with two clocks the seen-set is read from TODAY, finds nothing, "
   "and the item archives as new all over again. new=%s wrote=%s"
   % (_n, _w))
_rel = [os.path.relpath(f, d) for f in files(d)]
ck("⚠️ and the day directory is the day passed in, not a second clock",
   bool(_rel) and all(r.startswith(_OTHER_DAY + os.sep) for r in _rel),
   "files=%s" % (_rel,))
ck("⛔ the writer takes ONE `when` and hands it to daystore",
   'daystore.archive(doc, data, "news", log=log, when=when)' in CSRC,
   "two clocks is rule 66 — one source for one fact")
shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 THE FRESHNESS CONTRACT ENTRY IS LOAD-BEARING")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `top-<season>.json.gz` shipped with NO entry and the contract read
#    `stale: False, ok: True` while the file did not exist. An artifact
#    nothing watches can stop being written with nobody finding out.
for _lg in ("nfl", "ncaaf"):
    _modes = [r["mode"] for r in F.survey("data/%s" % _lg, "picks")]
    ck("%s: the dated news archive is IN the contract" % _lg,
       "news-archive" in _modes, "modes=%s" % (_modes,))
    _row = [r for r in F.survey("data/%s" % _lg, "picks")
            if r["mode"] == "news-archive"]
    _row = _row[0] if _row else {}
    ck("   ...probing the dated directory, not `latest/`",
       _row.get("kind") == "dir" and _row.get("path", "").endswith("/news"),
       "path=%r kind=%r" % (_row.get("path"), _row.get("kind")))
    ck("   ...hourly, the same deadline as the pull it rides on",
       len(F.FB_TIMES[_lg]["news"]) == 24,
       "⛔ the archive is written in the same code path as "
       "`latest/news.json`; a looser deadline would let them diverge for "
       "hours. deadlines=%d" % len(F.FB_TIMES[_lg]["news"]))

# ⚠️ AND MLB DOES NOT GAIN ONE. `mlb` has no news.json at all.
ck("⛔ MLB's contract is untouched",
   "news-archive" not in [r["mode"] for r in F.survey("data", "picks")],
   "the freeze stands and mlb has no news feed")

# 🔴 SOFT, AND THE REASON IS WRITTEN DOWN.
ck("⚠️ `news-archive` shares `news`'s soft status",
   "news-archive" in F.SOFT and "news" in F.SOFT,
   "⛔ both are written by one code path: when every feed fails, "
   "`collect_news` raises before either. Making the archive HARD would "
   "turn a third-party outage back into a red run — the exact regression "
   "this set exists to stop. SOFT=%s" % (sorted(F.SOFT),))


# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE REAL FAILURE IS DIVERGENCE, AND IT IS CHECKED HERE")
# ══════════════════════════════════════════════════════════════════════
# ⛔ A staleness deadline cannot say "fresh, but only one of the two".
#    `latest/news.json` fresh while the day's archive is empty means the
#    archive silently stopped — and THAT is the failure, not absence.
# ✅ So it is asserted as a check, driven both ways.
def diverged(latest_fresh, archive_files):
    """The condition, written once so both drives use the same one."""
    return bool(latest_fresh) and archive_files == 0


ck("🔴 latest fresh + an EMPTY archive day is a failure",
   diverged(True, 0) is True,
   "⛔ the archive stopped and nothing else would say so")
ck("...latest fresh + an archive present is fine",
   diverged(True, 3) is False, "the normal state")
ck("⚠️ ...and latest ABSENT with an empty archive is NOT this failure",
   diverged(False, 0) is False,
   "⛔ that is a dead feed, which `news` already reports softly — "
   "calling it this failure too would be crying wolf twice")

# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 AND AGAINST THE LIVE TREE — SELF-ARMING, BECAUSE A DEFERRED CHECK
#      WITH NO WAY BACK IS A PERMANENT NO-OP.
# ══════════════════════════════════════════════════════════════════════
# ⛔ `[found 2026-09-19]` THIS CHECK USED TO READ `isinstance(_n, int)`,
#    where `_n` was `len(glob(...))`. `len()` returns an int by the
#    language definition, so it COULD NOT FAIL. It was a `note()` wearing
#    a `ck()`.
# ✅ DEFERRING IT WAS RIGHT AND IS NOT BEING UNDONE. The archive had
#    never run, so asserting on day one would have reddened a correct
#    repo — the trap #51 fixed, and CLAUDE.md is explicit that a guard
#    firing on correct code is the other failure, not a safe one.
# ⛔ WHAT WAS MISSING WAS A WAY BACK. Nothing would ever have un-deferred
#    it, so from the first archived pull onward the real failure — the
#    one this whole task exists for — would have been defined,
#    unit-tested against a hand-written helper, and asserted NOWHERE.
# ➡️ THE CLASS: a check deferred on correct grounds, with nothing to
#    un-defer it, is a permanent no-op that reads like coverage.
# ✅ SO THE PRECONDITION IS READ OFF THE TREE. "Has this league ever
#    archived anything" is a question the tree answers, so the check arms
#    itself on the first archived pull and nobody has to remember to come
#    back for it.
# ⚠️ AND THE TWO COUNTS ARE DIFFERENT GLOBS. The old one globbed `*` for
#    the date — an ALL-TIME count — and then stood in for a question
#    about TODAY. Those are not the same number and conflating them was
#    its own small bug.
def _divergence(root, lg, utc_day, latest_stale):
    """-> (ever, today, fires). ⛔ ONE implementation, live and driven."""
    ever = len(glob.glob(os.path.join(root, "data", lg, "*", "news",
                                      "*.json.gz")))
    today = len(glob.glob(os.path.join(root, "data", lg, utc_day, "news",
                                       "*.json.gz")))
    # ⛔ DORMANT UNTIL THE LEAGUE HAS EVER ARCHIVED. `ever == 0` is "this
    #    has not started yet", which is not a divergence.
    return ever, today, bool(ever > 0 and diverged(not latest_stale, today))


_UTC_TODAY = datetime.datetime.now(UTC).strftime("%Y-%m-%d")

for _lg in ("nfl", "ncaaf"):
    _all = F.survey("data/%s" % _lg, "picks")
    # ══════════════════════════════════════════════════════════════════
    # 🔴 `[2026-09-26]` BY PATH, NOT BY MODE. A mode may own several rows,
    #    and since #170 `news` owns two: `latest/news.json` AND the daily
    #    `news-flags.json`. Keyed by mode, the LAST one won, so this read
    #    the flag file's freshness as if it were news.json's — and between
    #    midnight UTC and the first hourly pull it fired "the archive
    #    silently stopped" on a correct tree, every night.
    # ══════════════════════════════════════════════════════════════════
    _lat = next((r for r in _all if r["mode"] == "news"
                 and r["path"].replace("\\", "/").endswith("latest/news.json")), {})
    _arc = next((r for r in _all if r["mode"] == "news-archive"), {})
    ck("   ✅ %s: the 'latest' this reads is latest/news.json itself, though `news` owns %d row(s)"
       % (_lg, sum(1 for r in _all if r["mode"] == "news")),
       (_lat.get("path") or "").replace("\\", "/").endswith("latest/news.json"),
       "got %r" % _lat.get("path"))
    _ever, _today, _fires = _divergence(ROOT, _lg, _UTC_TODAY,
                                        _lat.get("stale"))
    note("%s: latest stale=%s (age %sm) · archived all-time %d · today %d"
         % (_lg, _lat.get("stale"), _lat.get("age_min"), _ever, _today))
    ck("🔴 %s: latest fresh + an EMPTY archive day" % _lg,
       not _fires,
       "⛔ the archive silently stopped — `latest/news.json` is current "
       "and today's archive holds nothing. ⚠️ DORMANT while the league "
       "has never archived (ever=%d); it ARMS ITSELF on the first "
       "archived pull. today=%d latest_stale=%s"
       % (_ever, _today, _lat.get("stale")))

# ══════════════════════════════════════════════════════════════════════
# ⛔ AND THE ARMING IS DRIVEN, IN A TEMP TREE — FOUR CASES, TWO OF WHICH
#    MUST NOT FIRE.
# ══════════════════════════════════════════════════════════════════════
# 🔴 A self-arming check is worth exactly as much as the proof that it
#    both arms AND stays quiet. ⛔ Nothing under this repo's `data/` is
#    written by any of this — every case is a throwaway tree.
def _synth(ever_day=None, today_day=None):
    """A tree with an archive file on the given day(s). -> root"""
    d = tempfile.mkdtemp(prefix="divarm-")
    for _day in (ever_day, today_day):
        if _day is None:
            continue
        _p = os.path.join(d, "data", "nfl", _day, "news")
        os.makedirs(_p, exist_ok=True)
        with gzip.open(os.path.join(_p, "0100.json.gz"), "wt",
                       encoding="utf-8") as _fh:
            _fh.write("[]")
    return d


# ══════════════════════════════════════════════════════════════════════
# ⛔ AND THE LIVE CHECK MUST ACTUALLY ASK `_divergence`, NOT SOMETHING
#    ALWAYS TRUE.
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE HOLE THIS CLOSES WAS MEASURED ON THIS VERY FILE. Restoring the
#    old spelling — `isinstance(_today, int)` — leaves every drive below
#    GREEN, because the drives exercise `_divergence()` while the live
#    assertion is a separate expression that can be hollowed out
#    independently. That is the same defect one level up: the thing that
#    proves the condition and the thing that asserts it had drifted
#    apart, and nothing was watching the join.
# ⚠️ Read from the PARSED AST, so a comment naming `_fires` cannot
#    satisfy it.
_own = ast.parse(io.open(os.path.abspath(__file__), encoding="utf-8").read())
# ⚠️ WALK EACH ARGUMENT. The condition is `not _fires` — a UnaryOp, not
#    a bare Name — so matching only top-level names finds nothing and
#    reddens on correct code, which is the other failure.
_live_ck = [n for n in ast.walk(_own)
            if isinstance(n, ast.Call)
            and getattr(n.func, "id", "") == "ck"
            and any(isinstance(x, ast.Name) and x.id == "_fires"
                    for a in n.args for x in ast.walk(a))]
ck("⛔ the live divergence check reads `_divergence`'s verdict, in CODE",
   len(_live_ck) == 1,
   "🔴 a condition that cannot be false is a `note()` wearing a `ck()` — "
   "which is exactly what this check was until 2026-09-19. The drives "
   "below exercise the helper; this asserts the LIVE check still asks "
   "it. ck calls referencing `_fires`: %d" % len(_live_ck))

_PAST = (datetime.datetime.now(UTC)
         - datetime.timedelta(days=4)).strftime("%Y-%m-%d")

for _name, _kw, _stale, _want_ever, _want_fire in (
        ("⚠️ DORMANT: never archived, empty day, latest fresh",
         {}, False, 0, False),
        ("🔴🔴 ARMED and FIRING: archived before, nothing today",
         {"ever_day": _PAST}, False, 1, True),
        ("✅ ARMED and quiet: archived before AND today",
         {"ever_day": _PAST, "today_day": _UTC_TODAY}, False, 2, False),
        ("⚠️ not crying wolf: latest STALE and today empty",
         {"ever_day": _PAST}, True, 1, False)):
    _d = _synth(**_kw)
    try:
        _e, _t, _f = _divergence(_d, "nfl", _UTC_TODAY, _stale)
    finally:
        shutil.rmtree(_d, ignore_errors=True)
    ck(_name, _e == _want_ever and _f is _want_fire,
       "⛔ ever=%d (wanted %d) fires=%s (wanted %s) today=%d — the four "
       "cases together are what make this an assertion rather than a "
       "note wearing a ck()" % (_e, _want_ever, _f, _want_fire, _t))


# ══════════════════════════════════════════════════════════════════════
section("8. ⛔ NO NEW API CALLS, AND THE PAGE DOES NOT CHANGE")
# ══════════════════════════════════════════════════════════════════════

_tree = ast.parse(CSRC)


def code(name):
    for n in ast.walk(_tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            b = list(n.body)
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                b = b[1:]
            return "\n".join(ast.unparse(x) for x in b)
    raise AssertionError(name)


_all = "\n".join(code(n) for n in
                 ("archive_news", "_news_seen_today", "_news_link_key"))
for _bad in ("odds_get", "urlopen", "urllib.request", "feedparser", "fetch"):
    ck("⛔ the archive makes no request: %r absent" % _bad,
       _bad not in _all, "it re-uses the items the pull already returned")
ck("✅ it writes through the shared archive writer, not its own",
   "daystore.archive" in _all and "gzip.open" not in _all.replace(
       "gzip.open(f, 'rt')", ""),
   "rule 117: one dated write-once writer")

_page = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
for _t in ("link_key", "news/", "revision"):
    ck("⛔ %r does not reach the page" % _t, _t not in _page,
       "nothing is joined to a player and nothing is on the surface")
# ⚠️ `[Sam, 2026-09-25]` ONE FIELD NOW HAS ONE DOOR. A news FLAG on a board
#    row shows when the reviewer first saw it — Sam asked for exactly that
#    ("the source, the headline or status, its link, and first_seen"). ⛔ It
#    may appear ONLY inside the flag renderer, read off a flag; anywhere
#    else on the page (the archive's own field reaching the surface) is red.
from jsblock import js_block as _jsb  # noqa: E402
_door = _jsb("fbFlagOne", os.path.join(ROOT, "index.html"))
ck("⛔ 'first_seen' reaches the page ONLY through the news-flag renderer",
   _page.count("first_seen") == _door.count("first_seen") >= 1 and "f.first_seen" in _door,
   "page %d, fbFlagOne %d" % (_page.count("first_seen"), _door.count("first_seen")))
# ⛔ ORDER INSIDE THE FUNCTION, NOT POSITION IN THE FILE. My first form
#    compared `CSRC.index(...)` and matched the `def archive_news` that
#    sits ABOVE the writer — a check that reddened on correct code
#    because it was reading the wrong two things.
_news_body = code("collect_news")
_w = _news_body.find('{LATEST}/news.json')
_a = _news_body.find('archive_news(')
ck("⚠️ `latest/news.json` is still written, and first",
   _w >= 0 and _a >= 0 and _w < _a,
   "⛔ the page's file is the product; the archive rides AFTER it. "
   "write at %d, archive at %d" % (_w, _a))
# ══════════════════════════════════════════════════════════════════════
# 🔴 THE GATE READS **WHERE IT WOULD WRITE**, NOT WHICH LEAGUE IS SET.
# ⛔ `test_news.py` sets `C.LEAGUE = "nfl"` while `C.DATA` is still
#    `data` — MLB's root. A gate keyed on LEAGUE let a TEST RUN write a
#    real archive into MLB's tree, which is both "a test must not write
#    the product" and a change to a frozen area. Found by running it.
_call = code("collect_news")
ck("🔴 the archive is gated on DATA, the destination",
   "os.path.basename(DATA" in _call,
   "⛔ LEAGUE and DATA can disagree; only one of them decides where the "
   "bytes land. call=%r" % (_call[_call.find("archive_news") - 160:
                                  _call.find("archive_news") + 40],))
ck("⛔ ...and it is not gated on LEAGUE",
   "if LEAGUE in" not in _call,
   "two sources for one fact is the same bug as two clocks")
for _root, _want in (("data/nfl", True), ("data/ncaaf", True),
                     ("data", False), ("data/mlb", False)):
    ck("   %-11s archives: %s" % (_root, _want),
       (os.path.basename(_root.rstrip("/")) in ("nfl", "ncaaf")) == _want,
       "⛔ MLB is frozen and out of scope for this change")
ck("⚠️ and MLB really does have a news feed, so the gate does real work",
   bool(collect.NEWS_FEEDS.get("mlb"))
   and os.path.exists(os.path.join(ROOT, "data", "latest", "news.json")),
   "⛔ the brief said mlb has no news.json; measured, it is 21 KB on "
   "disk. The gate is a scope decision, not an empty case.")

ck("...and a failing archive cannot lose the news",
   "the news archive did not write" in CSRC
   and "IS FINE" in CSRC,
   "same contract the shadow record has on the card path")
