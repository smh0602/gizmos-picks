#!/usr/bin/env python3
"""
🔴 THE SCORES TAB, AND THE TWO INDEPENDENT FAULTS THAT LOOKED LIKE ONE.

Sam, 2026-09-08: *"the cfb scores arent updating, its not live and they
havent even udpated from the games on 9/7."*

⛔ FAULT 1 — THE LIVE LAYER ONLY EVER SAW ESPN'S **CURRENT WEEK**, and the
   source comment called it "today". Measured in a real browser at the
   product's own origin, 2026-09-08:

       scoreboard?groups=80                 -> 09-11, 09-12, 09-13
       scoreboard?groups=80&dates=20260906  -> 6 events, 6 FINAL
       scoreboard?groups=80&dates=20260907  -> 1 event,  1 FINAL

   On 2026-09-05 the current week WAS the reader's week, which is why the
   "103 of 103" coverage check passed and why nothing looked wrong. Three
   days later the identical code answers for next weekend.
   ⚠️ A CHECK THAT CAN ONLY BE RUN ON THE DAY IT PASSES IS NOT A CHECK.

⛔ FAULT 2 — THE STORED FALLBACK WAS ALSO FROZEN, for an unrelated reason:
   CFBD returned **429 on every endpoint** from 2026-09-06, so
   `schedule-2026.json.gz` went two days without a rebuild — and NOTHING
   WENT RED, because the `scores` deadline was Sat 21:30 + Sun 09:30 only.
   Rule 137 a second time.

✅ Verified live before this file was written: the 7 stored games that
   render blank (6 on 09-06, 1 on 09-07) resolve **7 of 7** through the
   per-day layer, every one `Final` with a real score.

WHAT IS PINNED HERE:
  1. the polled query is UNCHANGED — no regression to the proven path
  2. the day layer asks PER DAY, never per range (a range drops days)
  3. the polled layer WINS over the day cache for the same game
  4. the day layer is cached per selection, not polled every 45s
  5. `scores` is due on every day the league actually plays
  6. `fb-scores` stands down behind the same CFBD back-off as `cfb-probe`
  7. a CFBD failure records its HTTP STATUS, not just "HTTPError"
"""
import os
import re

import freshness as F
from tcheck import ck, note


def code_only(src):
    """A module's executable text — comments and docstrings removed,
    **with the original line and column layout preserved**.

    🔴 THREE STRIPPERS HAVE BEEN WRONG IN THIS REPO AND THIS IS THE
    FOURTH ATTEMPT. The failures, in order:
      1. `str.split("#")` — read a `#` inside a string literal as a
         comment and truncated real code.
      2. a hand-rolled triple-quote tracker — swallowed whole function
         bodies, so every check built on it was VACUOUSLY TRUE.
      3. `"\n".join(token.string for ...)` — tokenising is right, but
         re-joining tokens with newlines DESTROYS ADJACENCY: the text
         `_cfb_backoff_left()` comes back as three lines, and every
         multi-token `in` test silently fails. `[measured 2026-09-08 —
         it failed five of its own checks]`
    ✅ So: blank the comment SPANS in place and drop the docstring LINES
    that `ast` itself identifies. Nothing is re-joined, nothing moves.
    ⚠️ The result is size-checked and content-checked before use.
    """
    import ast as _ast
    import io as _io
    import tokenize as _tk
    lines = src.splitlines()
    try:
        for tok in _tk.generate_tokens(_io.StringIO(src).readline):
            if tok.type == _tk.COMMENT:
                r, c = tok.start
                lines[r - 1] = lines[r - 1][:c]
    except Exception:
        pass
    try:
        tree = _ast.parse(src)
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.Module, _ast.FunctionDef,
                                 _ast.AsyncFunctionDef, _ast.ClassDef)):
                if not getattr(node, "body", None):
                    continue
                if _ast.get_docstring(node, clean=False) is None:
                    continue
                d = node.body[0]
                for r in range(d.lineno, (d.end_lineno or d.lineno) + 1):
                    if 0 < r <= len(lines):
                        lines[r - 1] = ""
    except Exception:
        pass
    return "\n".join(lines)


ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
H = open("index.html", encoding="utf-8").read()

print("\n═══ 1. 🔴 PER DAY, NOT PER RANGE — THIS IS THE MEASURED BIT ═══")
# ⛔ `dates=20260905-20260907` returned only 09-05 and 09-06: ESPN
#    resolves a range to the WEEK the range starts in and drops the rest.
#    A future session WILL be tempted to collapse the loop into one range
#    request, and it will look like it works.
ck("🔴 the day layer builds one query per DAY",
   "dates=${d}" in H,
   "a single `dates=A-B` range silently loses the last day — measured")
ck("⛔ ...and never a range",
   not re.search(r"dates=\$\{[^}]+\}-\$\{", H) and "dates=${a}-${b}" not in H,
   "no A-B range interpolation anywhere in the page")
ck("⚠️ the reason is written down where the code is",
   "resolves a range to the WEEK" in H,
   "so the next person to 'simplify' it reads the measurement first")

print("\n═══ 2. ⛔ THE PROVEN POLLED PATH IS UNCHANGED ═══")
ck("the bare scoreboard query is still there",
   "scoreboard?limit=400" in H, "same URL the live layer always used")
ck("...still both college divisions, still none for the NFL",
   "FB_LIVE_GROUPS = { ncaaf: ['80', '81'], nfl: [null] }" in H,
   "sending groups to the NFL returns an EMPTY scoreboard (rule 141)")
ck("...still 45 seconds",
   "FB_LIVE_MS = 45000" in H, "one value, one meaning")

print("\n═══ 3. 🔴 WHICH LAYER WINS, AND WHY ═══")
# The polled layer is seconds old; the day cache is a snapshot from when
# the week was selected. For a game IN PROGRESS they disagree.
m = re.search(r"function fbLiveOf\(g\)\{(.*?)\n\}", H, re.S)
ck("fbLiveOf consults both layers", bool(m) and "FB_DAY" in (m.group(1) if m else ""),
   "the day cache is useless if the renderer never reads it")
if m:
    body = m.group(1)
    ck("🔴 the POLLED layer is consulted FIRST",
       body.index("FB_LIVE.byId") < body.index("FB_DAY["),
       "a stale snapshot must never beat a live clock")
    ck("⛔ still keyed on the ID, never a team name",
       "g.espn || g.id" in body, "ledger rule 54")

print("\n═══ 4. ⚠️ THE DAY LAYER IS CACHED, NOT POLLED ═══")
# A 45s poll over 8 days x 2 divisions is 16 requests every 45 seconds
# aimed at somebody else's server, for days that cannot change.
ck("it is keyed by the selection and returns early on a repeat",
   "if (key === FB_DAY_KEY) return;" in H,
   "fetched once per season|week, not once per tick")
ck("🔴 and fbTick does NOT call it",
   bool(re.search(r"async function fbTick\(\)\{(?:(?!\n\})[\s\S])*\}", H))
   and "fbDayLoad" not in re.search(
       r"async function fbTick\(\)\{(?:(?!\n\})[\s\S])*\}", H).group(0),
   "the poll refreshes the live week only")
ck("⛔ the number of days is capped",
   "days.slice(0, 8)" in H, "a season picker must not ask for 100 days")
ck("a day-layer failure does not kill the live layer",
   "FB_DAY = null; FB_DAY_KEY = key;" in H,
   "one quiet miss; the polled query and the stored file still render")

print("\n═══ 5. 🔴 THE ET DAY, NOT THE UTC DAY (rule 149) ═══")
ck("the day list is built from an ET-shifted date",
   "4 * 3600 * 1000" in H,
   "a 10pm ET kickoff is the NEXT UTC day; asking ESPN for it would "
   "return the wrong slate")
ck("...and only for the season we actually poll",
   "if (fbScSeason === liveSeason){" in H,
   "asking ESPN about 2025 while the reader is in 2025 tells them nothing")

print("\n═══ 6. 🔴 SCORES ARE DUE ON EVERY DAY THE LEAGUE PLAYS ═══")
for lg in ("ncaaf", "nfl"):
    t = F.FB_TIMES[lg]["scores"]
    days = set()
    for x in t:
        days |= (x[2] if len(x) > 2 else set(range(7)))
    ck(f"🔴 {lg}: the scores deadline is DAILY",
       days == set(range(7)), f"{t} -> days {sorted(days)}")
note("⛔ it was Sat 21:30 + Sun 09:30 (college) and Sun 21:30 + Mon 23:30 "
     "(NFL). College plays 304 games off Saturday and the NFL 44 off "
     "Sunday — including every Thursday night game.")
note("⚠️ test_fb_freshness.py measures the game days from the STORED "
     "SCHEDULE and requires the deadline to cover them, so this cannot "
     "drift back to a hand-written day set.")

print("\n═══ 7. ⛔ ONE SOURCE, ONE BACK-OFF ═══")
# 🔴 PROVE THE STRIPPER BEFORE TRUSTING ANYTHING BUILT ON IT. A stripper
#    that returns "" makes every `in` check below silently FALSE, and one
#    that strips nothing makes them pass off a comment. Both have shipped
#    here before.
_raw = open("collect.py", encoding="utf-8").read()
C = code_only(_raw)
ck("⚠️ the comment stripper is not vacuous",
   0.20 < len(C) / max(1, len(_raw)) < 0.98
   and "def converge(explicit=(), allow_paid=True):" in C,
   f"{len(_raw)} -> {len(C)} chars ({len(C)/max(1,len(_raw)):.0%} kept); "
   "a real multi-token line still matches, so adjacency survived")
ck("⚠️ ...and it really does remove comments",
   "ONE SOURCE, ONE BACK-OFF" not in C,
   "if this fails, every check below is reading prose, not code")
ck("🔴 fb-scores stands down behind the CFBD back-off",
   "SKIPPING fb-scores[ncaaf]" in C,
   "it was the only CFBD caller still hammering /games at 429")
ck("...reading the same report cfb-probe reads",
   C.count("_cfb_backoff_left()") >= 2,
   "two pieces of state would eventually disagree about one source")

# ══════════════════════════════════════════════════════════════════════
# 🔴 IT BACKS OFF WHEN CFBD REFUSES US, NOT WHEN *WE* BREAK.
# `[2026-09-10]` The stored college schedule sat at 2026-09-06T16:50Z for
# **101 hours** while CFBD was healthy. `_cfb_backoff_left()` returns a
# wait on ANY recorded failure, and `cfb-probe` was recording a
# RuntimeError in OUR OWN verify — so a fine, 2-call, different-endpoint
# fetch stood down behind a bug in a different builder, every run.
# ⛔ THE CLASSIFIER IS THE ONE THIS REPO ALREADY HAS. A second place to
# record "is the source up" is a second thing to drift.
ck("🔴 the fb-scores gate asks whether the SOURCE refused us",
   "source_block(" in C and 'state") == "refused"' in C,
   "not merely whether the last back-fill failed — our own RuntimeError "
   "is not a reason to stop asking CFBD for a 2-call file")
ck("⛔ ...and an ignored back-off is ANNOUNCED, not silent",
   "a CFBD back-off is armed" in _raw,
   "a mode that 'should' have stood down and did not must say why, or "
   "the next reader calls it a bug")
ck("⚠️ cfb-probe KEEPS its unconditional back-off",
   re.search(r"_wait = _cfb_backoff_left\(\)\s*\n\s*if _wait > 0:", C)
   is not None,
   "15 calls a rebuild against a 3,000/month plan — retrying OUR failure "
   "hourly really would spend the month. Two modes, two costs, two rules")

# ══════════════════════════════════════════════════════════════════════
# 🔴 ~~"and it still exits non-zero — skipping is not hiding"~~
# ⛔ **STRUCK 2026-09-10 — IT ASSERTED THE OPPOSITE OF WHAT THIS REPO
#    DECIDED, AND PASSED BY ACCIDENT.** It searched for a `sys.exit(1)`
#    within 700 CHARACTERS of the SKIPPING log — a TEXT-PROXIMITY proxy
#    for a behaviour — and the `sys.exit(1)` it kept finding belongs to
#    the "NOTHING WRITTEN" path, a different branch entirely.
# 🔴 AND LEDGER RULE 172 REVERSED THE THING IT WAS ASSERTING: a
#    stand-down is a DECISION and exits 0; an attempted fetch that
#    returns nothing is an EVENT and exits 1. `test_source_block.py`
#    DRIVES both and asserts `exit == 0` for this exact mode — so two
#    files in one suite were claiming opposite things, and this one only
#    stayed green because of where a brace happened to fall.
# ✅ The behaviour is owned by `test_source_block.py`, which RUNS the
#    collector instead of reading it. What is checked here is the thing a
#    source read can actually establish: that the two outcomes are
#    DISTINCT branches rather than one shared exit.
# ══════════════════════════════════════════════════════════════════════
ck("🔴 a stand-down and a failed fetch are DIFFERENT branches",
   "NOTHING FETCHED" in C and "NOTHING WRITTEN --" in C,
   "rule 172 — a decision and an event must not share an exit code; "
   "test_source_block.py drives the exit codes themselves")
note("⚠️ THE EXIT CODES ARE ASSERTED BY DRIVING, IN test_source_block.py "
     "(`a back-off stand-down exits 0`). ⛔ Do not re-add a "
     "character-distance regex here — the one removed today searched 700 "
     "chars for a `sys.exit(1)` that belonged to another branch, and a "
     "longer log message was all it took to flip it.")
ck("⛔ the NFL is not held behind a CFBD back-off",
   "SKIPPING fb-scores[nfl]" not in C,
   "nflverse is a different source and was healthy throughout")

print("\n═══ 8. 🔴 A FAILURE MUST NAME ITS STATUS CODE (rule 148) ═══")
K = code_only(open("cfb.py", encoding="utf-8").read())
ck("build_schedule records the HTTP status",
   '"http_status": code' in K,
   'the stored probe read `["regular: HTTPError", "postseason: '
   'HTTPError"]` for two days — that is not a cause')
ck("...and says who owns each outcome",
   all(s in K for s in ("REJECTED OUR KEY", "OVER QUOTA")),
   "401 is ours to fix, 429 is ours to wait out, 5xx is theirs")
ck("⚠️ the error body is truncated before it is stored",
   'decode("utf-8", "replace")[:160]' in K,
   "this repo is PUBLIC and an error body can echo a request")


print("\n═══ 9. 🔴 THE TRENDS TAB SAYS HOW OLD IT IS ═══")
# Sam, 2026-09-08: *"the trends tab is still not updated."* ⛔ The page
# drew a full, confident table built on 2026-09-04 and said nothing about
# the date, so the only way to know was to ask. While CFBD is answering
# 429 no code can make the numbers newer — but the page can stop
# presenting four-day-old numbers as current.
ck("🔴 the table's build date is read from the file",
   "const builtAt = doc.built_at || null;" in H,
   "never a constant, never 'nightly' in prose")
ck("...and it is actually RENDERED, not just computed",
   "${ageNote}" in H,
   "rule 130 — this repo has shipped a renderer nobody called")
ck("⚠️ the 'late' threshold is each league's own cadence",
   "LEAGUE === 'ncaaf' ? 48 : 216" in H,
   "college rebuilds daily and the NFL weekly — one threshold would be "
   "wrong for one of them")
ck("⛔ and a late table says so plainly, with the date",
   "has not rebuilt since" in H and "they are that old" in H,
   "a stale number that announces itself is a different product")

print("\n═══ 10. ⛔ THE PAGE NEVER ASKS FOR A MANUAL RUN (rule 125) ═══")
# Sam's standing instruction: the only manual work is uploading files.
ck("🔴 no tab tells the reader to dispatch anything by hand",
   "dispatch <code>" not in H and "One free dispatch" not in H,
   "the Trends empty-state used to say 'dispatch cfb-probe once'")
ck("...and the cadence it quotes is the one that actually runs",
   "every morning at 3am ET" in H and "Sunday morning, after Saturday" not in H,
   "it advertised a Sunday rebuild after the cron moved to 3am daily")
