#!/usr/bin/env python3
"""
THE HALFTIME PROBE IS PAID, AND UNTIL TODAY NOTHING DROVE IT.

🔴 THE GAP THIS FILE CLOSES. `probe_halftime()` shipped on 2026-09-11,
ran for the first time on 2026-09-12, and **no test file mentioned it**.
`test_budget.py` priced it and `test_parity.py` classified it; neither one
ever called it. ⛔ A mode that spends Sam's credits and whose whole output
is a DECISION DOCUMENT had its first execution in production, against the
live API, with the answer landing straight in a project doc.

⚠️ IT IS THE EXACT SHAPE OF RULE 217 — a feature that produces nothing is
indistinguishable from one never built — one step earlier: **a feature
nothing drives is indistinguishable from one that does the wrong thing.**

════════════════════════════════════════════════════════════════════════
🔴 AND THE FIRST RUN FOUND THE DEFECT THE PROBE WAS BLIND TO
════════════════════════════════════════════════════════════════════════

`[measured 2026-09-12, data/ncaaf/latest/halftime-probe.json]`

    bulk   HTTP 422          the endpoint REFUSES the market key
    event  billed 2          totals_h1 x4 books, team_totals_h1 x1 book
    verdict  EVENT

✅ The endpoint question was answered correctly. ⛔ **The PRODUCT question
was not asked at all.** The probe requested `regions=us`, and **Hard Rock
lives in `us2`** — the book this project prices every card against. So a
market Hard Rock never posts could come back CARRIED and read as a green
light, and `team_totals_h1` — *the market Sam actually asked for* — came
back from **ONE bookmaker**, unnamed.

➡️ **"THE MARKET EXISTS" AND "SAM CAN BET THE MARKET" ARE DIFFERENT
FINDINGS, AND ONLY THE SECOND ONE JUSTIFIES SPENDING AGAINST A CEILING.**
The event ask now uses both regions and records WHICH BOOKS, and this file
drives every branch of it.
"""
import json
import os
import re
import subprocess
import sys

from tcheck import ck, note

ROOT = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════
# 🔴 THE PROBE IS DRIVEN, NOT READ. `odds_get` is replaced so no credit is
#    spent and no network is touched, and everything else — the branch
#    logic, the region strings, the book filter, the verdict wording — is
#    the REAL code. ⛔ A test that re-implements the branch checks its own
#    `if` (rule 202).
CHILD = r'''
import json, os, sys, tempfile
sys.path.insert(0, %(root)r)
import collect as C

SCEN = %(scen)r
CALLS = []

def fake(path, params):
    CALLS.append({"path": path, "params": dict(params)})
    for pat, resp in SCEN:
        if pat in path:
            if isinstance(resp, str):          # an exception to raise
                raise Exception(resp)
            return resp[0], resp[1], 99999
    return None, 0, 99999

C.odds_get = fake
d = tempfile.mkdtemp()
os.chdir(d)
C.probe_halftime()
p = os.path.join(d, C.LATEST, "halftime-probe.json")
out = json.load(open(p)) if os.path.exists(p) else None
print("@@@" + json.dumps({"calls": CALLS, "out": out,
                          "wrote": os.path.exists(p)}))
'''


def drive(scen, lg="ncaaf"):
    """Run the REAL probe against a stubbed feed. Returns calls + output."""
    env = dict(os.environ, LEAGUE=lg)
    src = CHILD % {"root": ROOT, "scen": scen}
    p = subprocess.run([sys.executable, "-c", src], cwd=ROOT, env=env,
                       capture_output=True, text=True, timeout=300)
    m = re.search(r"@@@(\{.*\})", p.stdout)
    if not m:
        raise AssertionError("probe child produced no result.\n%s\n%s"
                             % (p.stdout[-2000:], p.stderr[-2000:]))
    return json.loads(m.group(1))


def _bm(book, *markets):
    return {"key": book, "markets": [{"key": k} for k in markets]}


# ══════════════════════════════════════════════════════════════════════
print("═══ 1. 🔴 THE CHEAP ANSWER STOPS THE EXPENSIVE ASK ═══")
# ⛔ THE WHOLE POINT OF THE PROBE IS THAT IT DOES NOT PAY TWICE. If the
#    bulk endpoint carries the market, the per-game call must never fire —
#    the bulk answer is both cheaper AND the better outcome, and asking
#    anyway would spend credits to learn nothing.
r = drive([("/odds", ([{"bookmakers": [_bm("draftkings", "totals_h1")]}],
                      2))])
_paths = [c["path"] for c in r["calls"]]
ck("🔴 a BULK hit fires exactly one call",
   len(r["calls"]) == 1 and _paths[0].endswith("/odds"),
   "⛔ the event endpoint bills PER GAME. Asking it after the bulk call "
   "already answered is the 11x branch bought for nothing. Called: %s"
   % _paths)
ck("✅ ...and the verdict is BULK",
   r["out"]["verdict"].startswith("BULK"),
   "got %r" % r["out"]["verdict"][:60])
ck("⛔ no event ask means no event block",
   r["out"]["event"] is None,
   "an event block on a bulk hit would mean the branch ran and the file "
   "is reporting a cost that was not incurred")

print("\n═══ 2. 🔴 A 422 AND AN EMPTY 200 ARE DIFFERENT ANSWERS ═══")
# 🔴 THE DISTINCTION THAT THIS PROJECT HAS COLLAPSED FIVE TIMES, in the
#    other direction (rules 45-47). A 422 is the ENDPOINT REFUSING the
#    market key — it cannot serve it at any price, and re-asking next week
#    is pointless. An empty 200 is the endpoint serving the request with
#    nothing posted yet, which a later pull genuinely may change.
# ⛔ Collapsing them loses the STRONGER answer, and "re-read next Saturday"
#    is wrong advice for one of the two.
r422 = drive([("/sports/americanfootball_ncaaf/odds", "HTTP Error 422: Unprocessable Entity"),
              ("/events/", ({"bookmakers": [_bm("hardrockbet", "totals_h1")]}, 4)),
              ("/events", ([{"id": "E1"}], 0))])
ck("🔴 a 422 on the bulk ask is recorded as a REFUSAL",
   r422["out"]["bulk"].get("rejected") is True,
   "⛔ 'the endpoint will not serve this market' is a permanent fact and "
   "'no book has posted yet' is a Friday-night fact. Got %r"
   % r422["out"]["bulk"])
rEmpty = drive([("/sports/americanfootball_ncaaf/odds", ([], 2)),
                ("/events/", ({"bookmakers": [_bm("hardrockbet", "totals_h1")]}, 4)),
                ("/events", ([{"id": "E1"}], 0))])
ck("✅ ...and an empty 200 is NOT",
   rEmpty["out"]["bulk"].get("rejected") is False
   and rEmpty["out"]["bulk"].get("carried") is False,
   "got %r" % rEmpty["out"]["bulk"])
ck("⛔ both still fall through to the event ask",
   r422["out"]["event"] is not None and rEmpty["out"]["event"] is not None,
   "an unanswered bulk call is the ONLY reason the expensive branch is "
   "worth paying for")

print("\n═══ 3. 🔴🔴 THE EVENT ASK COVERS THE BOOK SAM ACTUALLY BETS ═══")
# 🔴 THE DEFECT MEASURED ON THE FIRST LIVE RUN. `regions=us` omits `us2`,
#    and `us2` is where HARD ROCK lives — the book every card in this repo
#    prices against. A CARRIED verdict read off a region that cannot
#    contain his primary book is a green light for a market he may not be
#    able to bet at all.
_ev = [c for c in r422["calls"] if "/events/" in c["path"]]
ck("🔴 the EVENT ask requests both regions",
   len(_ev) == 1 and _ev[0]["params"].get("regions") == "us,us2",
   "⛔ Hard Rock is a `us2` book. CLAUDE.md: 'a price from a book he "
   "cannot bet is not a better price' — and a MARKET from a book he "
   "cannot bet is not a market. Got %r"
   % (_ev[0]["params"].get("regions") if _ev else "NO EVENT CALL"))
_bulk = [c for c in r422["calls"] if c["path"].endswith("/sports/americanfootball_ncaaf/odds")]
ck("⛔ ...and the BULK ask deliberately does NOT",
   len(_bulk) == 1 and _bulk[0]["params"].get("regions") == "us",
   "the bulk ask is a question about an ENDPOINT, not about a book, and "
   "one region answers it for half the price. Got %r"
   % (_bulk[0]["params"].get("regions") if _bulk else "NO BULK CALL"))

print("\n═══ 4. 🔴 THE BOOKS ARE NAMED, AND FILTERED TO SAM'S FIVE ═══")
rbook = drive([
    ("/sports/americanfootball_ncaaf/odds", "HTTP Error 422: Unprocessable Entity"),
    ("/events/", ({"bookmakers": [
        _bm("hardrockbet", "totals_h1", "team_totals_h1"),
        _bm("draftkings", "totals_h1"),
        _bm("betrivers", "totals_h1"),        # ⛔ NOT one of Sam's five
        _bm("lowvig", "team_totals_h1"),      # ⛔ NOT one of Sam's five
    ]}, 4)),
    ("/events", ([{"id": "E1"}], 0))])
_sam = rbook["out"]["event"]["sam_books"]
ck("🔴 books outside Sam's five are excluded from `sam_books`",
   sorted(_sam.get("totals_h1") or []) == ["DraftKings", "Hard Rock"],
   "⛔ counting a book he has no account at is the same error as quoting "
   "a PrizePicks price — it is a number he cannot act on. Got %r"
   % _sam.get("totals_h1"))
ck("🔴 ...and a market only OUTSIDE books post reads as NONE of his",
   _sam.get("team_totals_h1") == ["Hard Rock"],
   "got %r" % _sam.get("team_totals_h1"))
ck("✅ the RAW book list is kept beside it, unfiltered",
   "betrivers" in (rbook["out"]["event"]["books_seen"].get("totals_h1") or []),
   "⛔ the filter is for the DECISION; throwing the raw answer away would "
   "make 'no book posts this' and 'no book of yours posts this' "
   "indistinguishable in the record — which is the rule 45 mistake with "
   "a different subject")
ck("🔴 Hard Rock gets its own field, per market",
   rbook["out"]["event"]["hard_rock"] == {"totals_h1": True,
                                          "team_totals_h1": True},
   "the card prices against Hard Rock, so whether HARD ROCK posts it is "
   "the single fact the decision turns on — not one name inside a list "
   "somebody has to read. Got %r" % rbook["out"]["event"]["hard_rock"])

print("\n═══ 5. 🔴 THE VERDICT SAYS IT, IN WORDS, IN THE FILE ═══")
# ⛔ A FIELD NOBODY READS IS NOT A FINDING. The verdict string is what
#    lands in `claude/halftime-markets-decision.md` and what Sam decides
#    from, so the book answer has to be IN IT, not one key away.
ck("🔴 the EVENT verdict names the books he can bet it at",
   "Hard Rock" in rbook["out"]["verdict"]
   and "DraftKings" in rbook["out"]["verdict"],
   "got %r" % rbook["out"]["verdict"][-160:])
rnone = drive([
    ("/sports/americanfootball_ncaaf/odds", "HTTP Error 422: Unprocessable Entity"),
    ("/events/", ({"bookmakers": [_bm("betrivers", "totals_h1")]}, 4)),
    ("/events", ([{"id": "E1"}], 0))])
ck("🔴🔴 a market NONE of his books post says so, and calls it a NO",
   "NONE OF HIS FIVE" in rnone["out"]["verdict"]
   and "is a NO" in rnone["out"]["verdict"],
   "⛔ THIS IS THE ONE THAT MATTERS. The old verdict would have read "
   "'EVENT — halftime markets exist' on a market he cannot place a bet "
   "on, and that sentence goes straight into a spend decision. Got %r"
   % rnone["out"]["verdict"][-200:])

print("\n═══ 6. ⛔ IT IS A PROBE: ONE FILE, AND NOT ON MLB ═══")
rmlb = drive([("/odds", ([], 2))], lg="mlb")
ck("⛔ MLB is refused and nothing is called",
   not rmlb["calls"] and not rmlb["wrote"],
   "halftime is a football question; a baseball run must not spend a "
   "credit on it. Called: %s" % rmlb["calls"])
ck("⛔ the probe writes ONE file and it is not a board, card or props file",
   set(k for k in rbook["out"]) >= {"verdict", "billed_total"}
   and "picks" not in json.dumps(rbook["out"]),
   "a mode that could move a number on the page would not be a probe")

print("\n═══ 7. 🔴 THE BILL IS THE HEADER'S, AND BUDGET.PY AGREES ═══")
# 🔴 `x-requests-last` IS THE AUTHORITY, never our arithmetic — the rule
#    that established the billing formula on 2026-08-22. `billed_total`
#    must be the SUM OF WHAT THE HEADERS SAID, so a stub billing 4 on the
#    event call must show up as 4.
ck("🔴 billed_total is the sum of the headers, not a computed guess",
   rbook["out"]["billed_total"] == 4,
   "⛔ the stub billed 0 on the bulk refusal, 0 on the events list and 4 "
   "on the event ask. Got %r" % rbook["out"]["billed_total"])

# 🔴🔴 THE CROSS-FILE CHECK. `budget.py` prices this mode from a formula
#    and `collect.py` decides the regions — two files, one fact, and the
#    thing that goes stale is the one nobody drives. So the price is
#    re-derived FROM THE PROBE'S OWN REQUESTS and compared to what the
#    TOOL PRINTS. ⛔ Not to a number in budget.py's source: reading the
#    source would pass on a formula that never reaches the output.
_m = len(rbook["out"]["asked"])
_worst = sum(_m * len((c["params"].get("regions") or "").split(","))
             for c in rbook["calls"] if "markets" in c["params"]) + 1
_out = subprocess.run([sys.executable, "budget.py"], cwd=ROOT,
                      capture_output=True, text=True, timeout=300)
_pr = re.search(r"halftime-probe\s+(\d+)/run", _out.stdout)
ck("🔴 budget.py prices the probe at what the probe actually asks for",
   bool(_pr) and int(_pr.group(1)) == _worst,
   "⛔ the region count changed in collect.py and the price is computed "
   "in budget.py. Two files, one fact — and this repo has shipped that "
   "pair stale three times. budget says %s/run, the probe's own calls "
   "come to %d (markets %d x regions, + 1 for the events list)"
   % (_pr.group(1) if _pr else "NOTHING", _worst, _m))
note("worst case %d credits/run x 2 runs a week = %d/week, ~%d a month "
     "across both leagues — against 8,570 of measured headroom"
     % (_worst, _worst * 2, _worst * 2 * 52 // 12))

note("⛔ WHAT THIS FILE DOES NOT CLAIM: that halftime markets are worth "
     "buying. It owns that the probe ASKS THE RIGHT QUESTION and reports "
     "the answer honestly. Whether ~1,160 credits a month buys a surface "
     "worth having is Sam's decision and nothing here measures it.")
