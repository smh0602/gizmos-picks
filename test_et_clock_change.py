#!/usr/bin/env python3
r"""test_et_clock_change.py — every Eastern time is right on both sides of the clock change.

`[2026-10-27]` US daylight time ends 2026-11-01 at 06:00Z; Eastern goes from UTC-4 to
UTC-5. Three places on the page read Eastern time at a FIXED -4, right only under
daylight time:
- `fbKickedOff` read an nflverse kickoff ("2026-11-01 13:00", Eastern wall time, no zone)
  at -04:00, so a 1:00pm EST game (18:00Z) counted as kicked off at noon and its box
  said "No score stored for this game yet." for the hour before kickoff;
- `todayET` was `Date.now() - 4h`, so every night from 11pm EST read as TOMORROW;
- the Scores tab's ESPN day list read each start at -4, so an 11pm EST kickoff (Hawai'i's)
  was asked of ESPN under the next day.
⚠️ ROOT CAUSE: the season these were written in was all inside daylight time, so a fixed
-4 was never wrong while anyone was looking. Fixed: the IANA zone (`etDate`, `etWallDate`,
`fbStartDate`, `fbEspnDay`).

⛔ THE CLASS, NOT THE THREE LINES. §2 fails on ANY fixed Eastern offset in the page's code
(-04:00, -05:00, 4*3600 ...), whatever it is called. §3 counts every fixed Eastern offset
in the repo's Python and fails on one that is not named here WITH ITS REASON, so a new one
is a decision written down, never a copy that goes wrong in November.

✅ THE CONTRACT STAYS AT A FIXED -4, ON PURPOSE (§4). Its deadlines are the minutes its
crons fire, and a GitHub cron is UTC and does not move in November: a contract read in
real Eastern time would put every deadline an hour after the run planned for it. So from
11-01 each deadline is an hour earlier by the wall clock ("10:00" is 9:00 EST), the same
UTC minute. ⛔ Moving the contract means moving the crons, which only Sam's upload does.
The game-day injury check is the one row on real Eastern time (`Moments`).

# @vacuity an unzoned nflverse kickoff is read at Eastern time by the zone, not at -04:00
#   file: index.html
#   find:   return /[Zz]|[+\-]\d\d:?\d\d$/.test(s) ? new Date(s) : etWallDate(s);
#   with:   return /[Zz]|[+\-]\d\d:?\d\d$/.test(s) ? new Date(s) : new Date(s.replace(' ', 'T') + '-04:00');
#
# @vacuity today's ET date is the zone's, not Date.now() - 4h
#   file: index.html
#   find: const todayET = () => etDate(Date.now());
#   with: const todayET = () => new Date(Date.now() - 4*3600*1000).toISOString().slice(0,10);
#
# @vacuity ESPN's day is the ET date of the start, not the UTC one
#   file: index.html
#   find:   return isFinite(d) ? etDate(d.getTime()).replace(/-/g, '') : null;
#   with:   return isFinite(d) ? d.toISOString().slice(0, 10).replace(/-/g, '') : null;
#
# @vacuity a wall time is corrected by the zone's offset, not taken as UTC
#   file: index.html
#   find:   return new Date(asUtc + behind(asUtc + behind(asUtc)));
#   with:   return new Date(asUtc);
#
# @vacuity a new fixed Eastern offset on the page is found
#   file: index.html
#   find:   const d = new Date(iso);
#   with:   const d = new Date(new Date(iso).getTime() - 4 * 3600 * 1000);
#
# @vacuity a new fixed Eastern offset in the Python is found
#   file: card_fb.py
#   find:     return et(t).strftime("%Y-%m-%d")
#   with:     return (t - timedelta(hours=4)).strftime("%Y-%m-%d")
#
# @vacuity the contract's deadlines stay its crons' UTC minutes in November
#   file: freshness.py
#   find: ET_OFFSET = datetime.timedelta(hours=4)
#   with: ET_OFFSET = datetime.timedelta(hours=5)
"""
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tokenize

from tcheck import ck, note, section  # noqa: E402
import jsblock

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HERE, "index.html")
SRC = jsblock.source(HTML)
UTC = datetime.timezone.utc


def Z(s):
    return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


# ═══ §1 the page's own functions, at summer and winter moments ═══════════════
section("§1 the page reads Eastern time by the zone")
NODE = shutil.which("node")
ck(bool(NODE), "node is on the PATH (it runs the page's own functions)")
_et = re.search(r"const etDate = [\s\S]*?\n};", SRC)
_today = re.search(r"const todayET = [^\n]*;", SRC)
ck(bool(_et and _today), "the page declares etDate and todayET where this file reads them")
BLOCKS = [jsblock.js_block(n, HTML) for n in ("etWallDate", "fbStartDate", "fbKickedOff", "fbEspnDay")]

# (what, now as UTC, call) -> expected
CASES = [
    # nflverse writes Eastern wall time: 1pm on 10-25 is EDT (17:00Z), on 11-01 EST (18:00Z)
    ("10-25 1pm EDT kickoff, at 16:30Z (12:30 EDT): not yet", "2026-10-25T16:30Z",
     "fbKickedOff({start: '2026-10-25 13:00'})", False),
    ("10-25 1pm EDT kickoff, at 17:05Z: kicked off", "2026-10-25T17:05Z",
     "fbKickedOff({start: '2026-10-25 13:00'})", True),
    ("11-01 1pm EST kickoff, at 17:30Z (12:30 EST): not yet", "2026-11-01T17:30Z",
     "fbKickedOff({start: '2026-11-01 13:00'})", False),
    ("11-01 1pm EST kickoff, at 18:05Z: kicked off", "2026-11-01T18:05Z",
     "fbKickedOff({start: '2026-11-01 13:00'})", True),
    ("a zoned start is read as written", "2026-11-01T17:30Z",
     "fbKickedOff({start: '2026-11-01T18:00:00Z'})", False),
    ("an 8:20pm EST Sunday-night stamp is 01:20Z Monday", "2026-11-01T12:00Z",
     "etWallDate('2026-11-08 20:20').toISOString()", "2026-11-09T01:20:00.000Z"),
    ("00:30 on 11-01 is still daylight time (04:30Z)", "2026-11-01T12:00Z",
     "etWallDate('2026-11-01 00:30').toISOString()", "2026-11-01T04:30:00.000Z"),
    ("March 2027: 1pm EDT again (17:00Z)", "2027-03-20T12:00Z",
     "etWallDate('2027-03-20 13:00').toISOString()", "2027-03-20T17:00:00.000Z"),
    ("no stamp is no moment", "2026-11-01T12:00Z", "isNaN(etWallDate('').getTime())", True),
    # todayET: 04:30Z is 11:30pm EST the day before, 12:30am EDT the same day
    ("todayET at 2026-11-02T04:30Z is 11-01 (11:30pm EST)", "2026-11-02T04:30Z",
     "todayET()", "2026-11-01"),
    ("todayET at 2026-10-27T04:30Z is 10-27 (12:30am EDT)", "2026-10-27T04:30Z",
     "todayET()", "2026-10-27"),
    ("todayET at 2026-11-02T05:30Z is 11-02 (12:30am EST)", "2026-11-02T05:30Z",
     "todayET()", "2026-11-02"),
    # ESPN's day: an 11:30pm EST kickoff stays on its own Saturday
    ("ESPN day of a 2026-11-08T04:30Z kickoff is 20261107 (11:30pm EST Sat)",
     "2026-11-01T12:00Z", "fbEspnDay('2026-11-08T04:30:00Z')", "20261107"),
    ("ESPN day of a 2026-10-11T03:30Z kickoff is 20261010 (11:30pm EDT Sat)",
     "2026-10-01T12:00Z", "fbEspnDay('2026-10-11T03:30:00Z')", "20261010"),
    ("ESPN day of an unzoned 8:20pm stamp is its own day", "2026-11-01T12:00Z",
     "fbEspnDay('2026-11-08 20:20')", "20261108"),
    ("ESPN day of nothing is null", "2026-11-01T12:00Z", "fbEspnDay('')", None),
]

if NODE and _et and _today:
    js = "\n".join([
        "const out = [];",
        _et.group(0), _today.group(0), *BLOCKS,
        "const CASES = %s;" % json.dumps([[c[1], c[2]] for c in CASES]),
        "const realNow = Date.now;",
        "for (const [now, call] of CASES) {",
        "  const t = Date.parse(now.replace('Z', ':00Z'));",
        "  Date.now = () => t;",
        "  try { out.push({v: eval(call)}); } catch (e) { out.push({err: String(e)}); }",
        "  Date.now = realNow;",
        "}",
        "console.log(JSON.stringify(out));",
    ])
    # TZ=America/Los_Angeles: the answers must not depend on the VIEWER's zone
    env = dict(os.environ, TZ="America/Los_Angeles")
    p = subprocess.run([NODE, "-e", js], capture_output=True, text=True, env=env, timeout=60)
    ck(p.returncode == 0, "node ran the page's functions", (p.stderr or "")[-300:])
    try:
        got = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        got = []
    ck(len(got) == len(CASES), "every case came back", "%d of %d" % (len(got), len(CASES)))
    for (what, _now, call, want), g in zip(CASES, got):
        ck(g.get("v", "ERR") == want, what, "%s -> %r, want %r" % (call, g.get("v", g.get("err")), want))


# ═══ §2 no fixed Eastern offset anywhere in the page's code ═══════════════════
section("§2 the page carries no fixed Eastern offset")
CODE = jsblock.script_code(HTML)
FIXED_JS = [
    (r"[+\-]0?[45]:00\b", "a -04:00 / -05:00 zone suffix"),
    (r"\b[45]\s*\*\s*(?:3600|60\s*\*\s*60)\b", "4 or 5 hours as 4*3600"),
    (r"\b(?:14400|18000)(?:000)?\b", "4 or 5 hours in seconds or ms"),
    (r"\b(?:240|300)\s*\*\s*60\b", "240 or 300 minutes"),
    (r"getTimezoneOffset", "the VIEWER's offset, which is not Eastern's"),
]
for pat, what in FIXED_JS:
    hits = [CODE[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")
            for m in re.finditer(pat, CODE)]
    ck(not hits, "no %s in the page's code" % what, " | ".join(hits[:3]))
ck(re.search(r"\bfbStartDate\(g\.start\)", jsblock.js_block("fbKickedOff", HTML)),
   "fbKickedOff reads its start through fbStartDate")
ck(jsblock.calls("fbEspnDay", HTML) >= 1, "the Scores tab's ESPN day list calls fbEspnDay")
_ESPN = CODE[CODE.find("if (fbScSeason === liveSeason){"):][:600]
ck(len(_ESPN) > 100 and "fbEspnDay(g.start)" in _ESPN, "the day list maps each start through fbEspnDay", _ESPN[:120])


# ═══ §3 every fixed Eastern offset in the Python is named, with its reason ═══════
section("§3 the Python's fixed Eastern offsets are each a decision")
MLB_DST = ("MLB: opening day to the last World Series game is inside daylight time "
           "(2026's Game 7 is 00:00Z 11-01, before the 06:00Z change)")
CONTRACT = ("the contract: its deadlines are its crons' UTC minutes, which do not move "
            "in November (§4)")
ALLOWED = {
    "card.py": (3, MLB_DST + "; first-pitch time, the card's date, today"),
    "collect.py": (3, MLB_DST + "; the finished slate and the results walk"),
    "mlb_game_model.py": (1, MLB_DST),
    "mlb_tables.py": (1, MLB_DST),
    "freshness.py": (11, CONTRACT + "; `_et_day` uses it only without a tz database, and "
                     "`_et_today`'s use is unreachable"),
    "cfb_injuries.py": (1, "not an offset: `hours=5` shifts the moment the computed US rule "
                        "(`_us_eastern_offset`) is asked about"),
}
FIXED_PY = re.compile(r"\bhours\s*=\s*-?\s*[45]\b|\bET_OFFSET\b|[+\-]0?[45]:00\b")


def fixed_offsets(path):
    """Fixed Eastern offsets in a module's CODE: comments and long strings (docstrings,
    prose) are skipped, short literals (a "-04:00") are kept."""
    keep = []
    with open(path, encoding="utf-8") as f:
        for t in tokenize.generate_tokens(io.StringIO(f.read()).readline):
            if t.type == tokenize.COMMENT or (t.type == tokenize.STRING and len(t.string) > 14):
                continue
            keep.append(t.string)
    return len(FIXED_PY.findall(" ".join(keep)))


found = {}
for name in sorted(os.listdir(HERE)):
    if name.endswith(".py") and not name.startswith("test_"):
        n = fixed_offsets(os.path.join(HERE, name))
        if n:
            found[name] = n
for name, n in sorted(found.items()):
    want, why = ALLOWED.get(name, (0, None))
    ck(n == want, "%s: %d fixed Eastern offset(s), %d named here" % (name, n, want),
       ("why: " + why) if why and n == want else
       "a fixed -4 is wrong from November: use the IANA zone or freshness.et_wall_utc, "
       "or name it in ALLOWED with its reason" if n > want else
       "fewer than named: update ALLOWED so it stays the truth")
for name in sorted(set(ALLOWED) - set(found)):
    ck(False, "%s is named in ALLOWED and has none" % name, "remove it from ALLOWED")
ck(fixed_offsets(os.path.join(HERE, "freshness.py")) > 0 and "card_fb.py" not in found,
   "the scan sees the contract's offsets and none in the football card")


# ═══ §4 the contract keeps its crons' UTC minutes through the change ═════════
section("§4 the contract's deadlines are the same UTC minute in summer and winter")
import freshness as F  # noqa: E402

ck(F.last_due(F.CARD, Z("2026-10-27T15:00Z")) == Z("2026-10-27T14:00Z"),
   "MLB's 10:00 card deadline is 14:00Z under daylight time")
ck(F.last_due(F.CARD, Z("2026-11-03T15:00Z")) == Z("2026-11-03T14:00Z"),
   "...and 14:00Z in November too (9:00 EST by the wall clock)")
for lg, row in (("nfl", "props"), ("nfl", "card"), ("ncaaf", "props"), ("ncaaf", "card")):
    times = F.FB_TIMES[lg][row]
    a = F.next_due(times, Z("2026-10-24T00:00Z"))
    b = F.next_due(times, Z("2026-11-07T00:00Z"))
    ck(a is not None and b is not None and (a.hour, a.minute) == (b.hour, b.minute),
       "%s %s: its first deadline of a day is the same UTC minute on 10-24 and 11-07" % (lg, row),
       "%s / %s" % (a, b))
ck(F.due_date(F.CARD, Z("2026-11-02T03:30Z")) == "2026-11-01",
   "a deadline's date is the contract's own day (11-01's card at 03:30Z on 11-02)")
ck(F.et_wall_utc(datetime.datetime(2026, 10, 25, 12, 0)) == Z("2026-10-25T16:00Z")
   and F.et_wall_utc(datetime.datetime(2026, 11, 1, 12, 0)) == Z("2026-11-01T17:00Z"),
   "the injury check's 12:00 is REAL Eastern: 16:00Z in October, 17:00Z from 11-01")
note("from 11-01 every contract deadline is an hour earlier by the Eastern wall clock "
     "(the same UTC minute); only Sam's upload of the crons could move them")
