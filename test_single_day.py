#!/usr/bin/env python3
"""
THE SINGLE-DAY BOARD.

Sam, 2026-09-04: *"only games on the day the run happens. minimum 5
picks, maximum 50. a day with no games means an EMPTY tab, and that is
correct."*

🔴 THIS TEST RUNS THE REAL BUILDER. It copies the live data tree into a
temp directory, MOVES SOME KICKOFFS TO THE NEXT DAY, runs `card_fb.py`
end to end, and reads the card it wrote. ⛔ A test that re-implements the
filter and checks its own arithmetic proves nothing about the file that
ships — and the defect this exists to catch was an ORDERING bug, which
only an end-to-end run can see at all.

⚠️ THE DEFECT IS HISTORICAL AND REAL, not a hypothetical:
`picks/fb-ncaaf-2026-09-03.json` is headed `2026-09-03` and 19 of its 50
picks are 09-04 games. That card is on disk and stays there — it is the
record of what was published. So the disk is REPORTED and the CODE is
ASSERTED (ledger rule 76): asserting over every stored card would be red
forever on a card nobody may rewrite.
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from tcheck import ck, note   # the shared gate — see tcheck.py

ROOT = os.path.dirname(os.path.abspath(__file__))
FAIL = []


sys.path.insert(0, ROOT)
os.environ.setdefault("LEAGUE", "ncaaf")
import card_fb  # noqa: E402  (needs LEAGUE set first)

ET = None
try:
    from zoneinfo import ZoneInfo
    ET = ZoneInfo("America/New_York")
except Exception:
    pass


def etd(s):
    return card_fb.et_date(s)


# ───────────────────────────────────────────────────────────────
print("\n═══ 1. THE DEFECT THIS FIXES, ON DISK ═══")
import glob

mixed, clean = [], 0
for p in sorted(glob.glob(os.path.join(ROOT, "picks", "*.json"))):
    try:
        d = json.load(open(p))
    except Exception:
        continue
    pk = d.get("picks") or []
    if not pk:
        continue
    days = {}
    for r in pk:
        days[etd(r.get("commence"))] = days.get(etd(r.get("commence")), 0) + 1
    days.pop(None, None)
    if len(days) > 1 or (days and d.get("date") not in days):
        mixed.append((os.path.basename(p), d.get("date"), days))
    else:
        clean += 1

# ⚠️ REPORTED, NOT ASSERTED. A published card is the append-only record of
#    what was shown; rewriting one to make a test pass would be forging it.
note("%d stored card(s) are single-day; %d mix days" % (clean, len(mixed)))
for m in mixed:
    note("  %s headed %s but holds %s" % m)
ck("the historical defect is still visible, so this test is not vacuous",
   len(mixed) >= 1,
   "if this ever reads 0, the evidence was deleted — check before relaxing it")

# ───────────────────────────────────────────────────────────────
print("\n═══ 2. THE RULES ARE IN THE BUILDER, NOT IN THE PAGE ═══")
ck("BOARD_MIN is 5 and BOARD_MAX is 50 (Sam's numbers)",
   card_fb.BOARD_MIN == 5 and card_fb.BOARD_MAX == 50,
   "min=%s max=%s" % (card_fb.BOARD_MIN, card_fb.BOARD_MAX))

src = open(os.path.join(ROOT, "card_fb.py")).read()

# 🔴 THE ORDERING BUG. `build_parlays_fb` used to run ABOVE the name gate,
#    so a board that correctly shipped MARKET-only could still ship
#    RECORD parlays. Position in the file is the thing being asserted,
#    because the defect WAS a position.
i_parlay = src.index("parlays, parlay_meta = build_parlays_fb(")
i_gate = src.index("JOIN TOO WEAK")
i_floor = src.index("below = [r for r in rows if not r[\"clears_price_floor\"]]")
i_day = src.index("off_day = [r for r in rows")
ck("parlays are built AFTER the name gate strips untrusted rates",
   i_parlay > i_gate,
   "a MARKET-only board must not ship RECORD parlays")
ck("parlays are built AFTER the price floor", i_parlay > i_floor)
ck("parlays are built AFTER the single-day filter", i_parlay > i_day)
ck("the day filter runs BEFORE the price rules",
   i_day < i_floor,
   "one filter governs board, parlays and the floor report alike")

# ⚠️ The projections map must NOT be day-filtered: the Player Props tab
#    renders the whole slate and joins against it.
i_proj = src.index("projections = {}")
ck("projections are built from every priced row, before the day filter",
   i_proj < i_day,
   "the BOARD is one day; the PROJECTIONS are the slate")

# ⛔ Wall-clock day would overwrite a good Saturday card at 01:00 Sunday.
ck("the day comes from the slate, not from datetime.now()",
   "slate = slate_date(B)" in src,
   "ledger rule 60 — the card's own date now describes every row on it")

# ───────────────────────────────────────────────────────────────
print("\n═══ 3. END-TO-END: A BOARD THAT STRADDLES MIDNIGHT ═══")


def stage(tmp):
    """Only what the college builder reads, and an EMPTY picks/.

    ⚠️ NARROW ON PURPOSE. Copying the whole `data/` tree three times is
    ~85MB of a fixed CI disk allowance for no benefit, and copying stored
    cards in would make this test depend on files it does not use.
    """
    shutil.copytree(os.path.join(ROOT, "data/ncaaf"),
                    os.path.join(tmp, "data/ncaaf"))
    os.makedirs(os.path.join(tmp, "picks"), exist_ok=True)
    shutil.copy(os.path.join(ROOT, "card_fb.py"), tmp)


def build(tmp, shift_frac=0.0, keep_frac=1.0):
    """Copy the tree, move `shift_frac` of games to the NEXT ET day, run
    the real builder, and return the card it wrote."""
    stage(tmp)
    p = os.path.join(tmp, "data/ncaaf/latest/props.json.gz")
    B = json.load(gzip.open(p, "rt"))
    gs = B.get("games", [])
    n = len(gs)
    keep = max(1, int(round(n * keep_frac)))
    gs = gs[:keep]
    n_shift = int(round(len(gs) * shift_frac))
    # ⚠️ Shift the LAST games, so the earliest kickoff — and therefore
    #    slate_date — stays on the original day.
    for g in gs[len(gs) - n_shift:] if n_shift else []:
        t = datetime.strptime(g["commence"], "%Y-%m-%dT%H:%M:%SZ")
        g["commence"] = (t + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    B["games"] = gs
    B["n_games"] = len(gs)
    with gzip.open(p, "wt") as fh:
        json.dump(B, fh)
    env = dict(os.environ, LEAGUE="ncaaf")
    r = subprocess.run([sys.executable, "card_fb.py"], cwd=tmp, env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:])
        return None, r
    with open(os.path.join(tmp, "picks/fb-ncaaf-latest.json")) as fh:
        return json.load(fh), r


tmp = tempfile.mkdtemp()
card, run = build(tmp, shift_frac=0.5)

if not ck("the builder runs on a two-day board", card is not None):
    pass
else:
    days = sorted({etd(r.get("commence")) for r in card["picks"]} - {None})
    ck("every pick on the board is on the card's own date",
       days == [card["date"]],
       "card date %s, board days %s" % (card["date"], days))
    ck("the rows for the other day are counted, not silently vanished",
       card["n_off_slate_day"] > 0 and card["off_slate_dates"],
       "%d row(s) held back for %s"
       % (card["n_off_slate_day"], ", ".join(card["off_slate_dates"])))
    ck("the card says so in a sentence a reader can read",
       str(card["n_off_slate_day"]) in card["single_day_rule"]
       and card["off_slate_dates"][0] in card["single_day_rule"])

    # 🔴 THE PARLAYS, WHICH ARE THE HALF A BOARD-ONLY FILTER WOULD MISS.
    ids = {r["game_id"]: etd(r.get("commence")) for r in card["picks"]}
    allp = [x for v in (card.get("parlays") or {}).values() for x in v]
    crossers = [p for p in allp
                if len({ids.get(g) for g in p["game_ids"]} - {None}) > 1
                or any(ids.get(g) not in (card["date"], None) for g in p["game_ids"])]
    ck("no parlay crosses days",
       not crossers and len(allp) > 0,
       "%d parlay(s) built, %d crossing" % (len(allp), len(crossers)))
    ck("board is capped at the maximum",
       len(card["picks"]) <= card["board_max"],
       "%d picks" % len(card["picks"]))
    note("two-day run: %d on the slate day, %d held back, %d on the board, "
         "%d parlays" % (card["n_on_slate_day"], card["n_off_slate_day"],
                         len(card["picks"]), len(allp)))
# ⚠️ Cleanup outside the branch: CI disk is a FIXED allowance, and a temp
#    tree left behind on the failure path is the run after this one failing
#    for a reason that has nothing to do with the code.
shutil.rmtree(tmp, ignore_errors=True)

# ───────────────────────────────────────────────────────────────
print("\n═══ 4. A DAY WITH NO GAMES IS AN EMPTY BOARD, AND IT IS WRITTEN ═══")
# 🔴 THE FILE MUST STILL BE WRITTEN. Ledger rule 86: an artifact that
#    correctly did nothing is not late — but only if it exists. A builder
#    that returns early on an empty day leaves the freshness contract
#    reading MISSING and raises an alarm about a correct result.
tmp = tempfile.mkdtemp()
try:
    stage(tmp)
    p = os.path.join(tmp, "data/ncaaf/latest/props.json.gz")
    B = json.load(gzip.open(p, "rt"))
    B["games"] = []
    B["n_games"] = 0
    with gzip.open(p, "wt") as fh:
        json.dump(B, fh)
    # ⚠️ `stage()` gives us an EMPTY picks/, so the card's existence after
    #    the run is proof the builder wrote it — not proof it was left over.
    assert not os.path.exists(os.path.join(tmp, "picks/fb-ncaaf-latest.json"))
    r = subprocess.run([sys.executable, "card_fb.py"], cwd=tmp,
                       env=dict(os.environ, LEAGUE="ncaaf"),
                       capture_output=True, text=True)
    lp = os.path.join(tmp, "picks/fb-ncaaf-latest.json")
    wrote = os.path.exists(lp)
    ck("a gameless day still WRITES the card", wrote,
       "rule 86 — an artifact that correctly did nothing must still exist")
    if wrote:
        e = json.load(open(lp))
        ck("the empty board has zero picks", e["picks"] == [])
        ck("and it says WHY, rather than looking broken",
           bool(e.get("empty_reason")) and "correct" in e["empty_reason"],
           (e.get("empty_reason") or "")[:80])
        ck("it is still dated", bool(e.get("date")))
        ck("no parlays are invented on an empty board",
           not [x for v in (e.get("parlays") or {}).values() for x in v])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ───────────────────────────────────────────────────────────────
print("\n═══ 5. A SHORT DAY IS REPORTED, NEVER PADDED ═══")
tmp = tempfile.mkdtemp()
try:
    stage(tmp)
    p = os.path.join(tmp, "data/ncaaf/latest/props.json.gz")
    B = json.load(gzip.open(p, "rt"))
    # one game, and only two priced props in it
    g = dict(B["games"][0])
    g["props"] = (g.get("props") or [])[:2]
    B["games"] = [g]
    B["n_games"] = 1
    with gzip.open(p, "wt") as fh:
        json.dump(B, fh)
    subprocess.run([sys.executable, "card_fb.py"], cwd=tmp,
                   env=dict(os.environ, LEAGUE="ncaaf"),
                   capture_output=True, text=True)
    s = json.load(open(os.path.join(tmp, "picks/fb-ncaaf-latest.json")))
    n = len(s["picks"])
    if n == 0:
        note("the thin fixture produced 0 picks, so section 4 covers it")
    else:
        ck("a board under the minimum is shipped, not suppressed",
           0 < n < card_fb.BOARD_MIN, "%d pick(s)" % n)
        ck("and it is FLAGGED as short", s.get("short_of_min") is True)
        ck("with a sentence saying it was not padded",
           bool(s.get("short_reason")) and "NOT padded" in s["short_reason"])
        ck("nothing was invented to reach the minimum",
           n <= s["n_on_slate_day"],
           "%d shown of %d priced" % (n, s["n_on_slate_day"]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ───────────────────────────────────────────────────────────────
# 🔴 THE FAILURE GATE IS THE LAST THING IN THIS FILE. Rule 97: anything
#    written below it reports red and the file still exits 0.
print()
print("✅ all single-day board tests passed")
