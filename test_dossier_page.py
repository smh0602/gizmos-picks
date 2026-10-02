#!/usr/bin/env python3
"""
🔴🔴 SAM'S EIGHT SIGNALS WERE COMPUTED, AUDITED, ARCHIVED — AND INVISIBLE.

    $ grep -c 'dossier' index.html
    0

`dossier_fb.py` has run on every `card-fb` arm since 2026-09-17, writing
eight checks for every game on both boards, gating itself on an audit and
keeping a dated write-once archive. ⛔ **Nothing read the file.** The page
fetched `board.json`, `freshness.json`, `news.json`, `props.json.gz`,
`record-detail.json.gz` and `record.json`, and nothing else.

⚠️ AND THE MISS THAT ALLOWED IT: reviewing PR #38 the artifact was
verified — 32 of 32 games, all eight sections — and reported as working.
⛔ **Nothing checked that anything READ it.** An artifact nothing renders
is not a feature, and "the file is correct" is a different claim from
"the product shows it".

🔴 SO THIS FILE ASKS THE SECOND QUESTION, AND IT ASKS IT BY RUNNING THE
SHIPPED CODE. It slices the panel out of `index.html`, evals it in node,
and renders THE REAL ARTIFACT for BOTH leagues — ledger rule 197: the
game-lines section existed, was wired, and simply never drew, and that
was found by loading the page rather than by reading it.

⛔ WHAT IT WILL NOT DO IS READ THE SOURCE AND BE SATISFIED. `calls()` is
used for the wiring, because a renderer nobody calls looks exactly like
the one that draws the page (rule 130) — but every claim about what the
reader SEES is made against rendered HTML.
"""

# ══════════════════════════════════════════════════════════════════════
# @vacuity the panel joins on the board's own id, never on team names
#   file: index.html
#   find: (((D || {}).dossiers) || []).forEach(x => { if (x.board_id) m.set(x.board_id, x); });
#   with: (((D || {}).dossiers) || []).forEach(x => { m.set((x.away_name||'') + (x.home_name||''), x); });
#
# @vacuity a section that cannot answer is SHOWN, never hidden
#   file: index.html
#   find: const gap = s.state !== 'OK';
#   with: const gap = s.state !== 'OK'; if (gap) return '';
#
# [Sam, 2026-10-01] ~~a partial game NAMES the side on a `dospart` flag~~ —
# no per-row flag on any tab: the header must be the two names and nothing
# else, and the refused sections are what still show the game is partial.
# @vacuity a partial game's header carries NO flag, only the two names
#   file: index.html
#   find: return `<div class="doshd">${x.away_name || ''} at ${x.home_name || ''}</div>
#   with: return `<div class="doshd">${x.away_name || ''} at ${x.home_name || ''}${x.unresolved_side ? `<span class="dospart">no season record for ${x.unresolved_side}</span>` : ''}</div>
#
# @vacuity a partial game still LOOKS partial: its refused sections are drawn as gaps
#   file: index.html
#   find: const secs = (x.sections || []).map(s => fbDosSection(s)).join('');
#   with: const secs = (x.sections || []).filter(s => !x.unresolved_side || s.state === 'OK').map(s => fbDosSection(s)).join('');
#
# @vacuity a section that CAN answer shows a stored value, not a sentence
#   file: index.html
#   find: return f.length ? `<ul class="df">${f.join('')}</ul>` : '';
#   with: return '';   // the values are dropped and only prose is drawn
#
# @vacuity the book count says WHAT IT COUNTS — books with a moneyline
#   file: index.html
#   find: li('Books with a moneyline', L.n_books);
#   with: li('Books priced', L.n_books);   // the label that read "priced 0"
#
# [Sam, 2026-10-01] ~~the zero is explained in a sentence under the count~~
# — no warning line under a number on any tab; the label carries it alone.
# @vacuity a zero book count carries NO warning sentence under it
#   file: index.html
#   find: if (L.n_books != null) li('Books with a moneyline', L.n_books);
#   with: if (L.n_books != null){ li('Books with a moneyline', L.n_books); if (!L.n_books && (L.total != null || L.run_line != null)) f.push(`<li>&#9888;&#65039; <b>That zero is about the moneyline only.</b> None is stored for this game, so there is no win&nbsp;% to show &mdash; the total and spread above are real prices a book is showing.</li>`); }
#
# ── [2026-09-28] THE PLANTED BOARD'S OWN QUESTIONS. Each one has its case
#    on every run, whatever today's slate holds (see section 3). ────────
# @vacuity a PLANTED section that cannot answer is drawn AS A GAP
#   file: index.html
#   find: <div class="dossec${gap ? ' gap' : ''}">
#   with: <div class="dossec">
#
# @vacuity a PLANTED refusal is the builder's own sentence, verbatim
#   file: index.html
#   find: <p class="dw">${s.why || ''}</p>
#   with: <p class="dw">${(s.why || '').slice(0, 40)}</p>
#
# @vacuity a PLANTED one-sided game is described, not dropped
#   file: dossier_fb.py
#   find: if not home and not away:
#   with: if not home or not away:
#
# @vacuity the builder NAMES the planted side we hold no record for
#   file: dossier_fb.py
#   find: "unresolved_side": missing,
#   with: "unresolved_side": None,
#
# @vacuity the jargon bar reads the builder's own refusal prose (planted)
#   file: dossier_fb.py
#   find: "in it. The price above is real; this comparison is not "
#   with: "in it (T23, measured null). The price above is real; this comparison is not "
#
# @vacuity every PLANTED college game renders a market section
#   file: dossier_fb.py
#   find: d = {"n": 1, "name": "Market", "state": "OK", "basis": MARKET,
#   with: d = {"n": 1, "name": "Markets", "state": "OK", "basis": MARKET,
# ══════════════════════════════════════════════════════════════════════

import datetime
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from jsblock import calls, js_block
from tcheck import ck, note, section

import dossier_fb as D          # noqa: E402  (nfl_table: the ONE parse)

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "index.html")
HTML = open(PAGE, encoding="utf-8").read()

# 🔴 THE JARGON BAR IS `verify_card.py`'s OWN LIST, READ OUT OF IT.
# ⛔ A second copy would be a second thing to drift (rule 66), and the
#    MLB card's bar is the standard Sam set — the football panel does not
#    get an easier one.
_VC = open(os.path.join(ROOT, "verify_card.py"), encoding="utf-8").read()
_m = re.search(r"_JARGON = (\[[^\]]*\])", _VC, re.S)
JARGON = eval(_m.group(1)) if _m else []

# ⚠️ AND A SECOND, STRICTER BAR THE PAGE NEEDS AND THE CARD DOES NOT:
#    filenames, paths, backticked code and collector mode names. Driving
#    this found one section `why` carrying "`top-2026.json.gz` under
#    `data/`" on all 32 NFL games — jargon-list clean and still unreadable
#    (Sam, 2026-08-26: "all of these things that a casual fine wont know
#    about has to go"). ⛔ It was fixed IN THE BUILDER, not filtered here.
OPERATOR = re.compile(r"`[^`]+`|[\w./-]+\.json(?:\.gz)?|nfl-logs|cfb-probe"
                      r"|props-board|card-fb|data/")


# ══════════════════════════════════════════════════════════════════════
# 🔴🔴 THE CASE IS PLANTED, NEVER WAITED FOR. `[2026-09-28]`
# Monday's NFL board held 7 games, mostly finished, and every head-to-head
# on it could answer. So "7 game(s) rendered through the shipped panel
# code" and "every section that cannot answer is DRAWN (0 of 0)" went red
# on CORRECT code (collect 36444412810, and three runs before it), and
# went green again on their own when the next week's odds posted. A floor
# that reads today's slate is a claim about the slate, not about the code.
# ⛔ And an EMPTY board — college from January to August — did worse: the
#    file DIED on `_doc["dossiers"][0]`, with its temp tree left behind.
# ✅ So every floor below is asked of a board THIS FILE WRITES into the
#    throwaway tree (the way #156 planted its case): 12 games named from
#    the league's OWN resolver table — `dossier_fb.nfl_table()` for NFL,
#    `teams.json` for college — and one away side no table holds, so the
#    REAL builder must refuse that game's pair-wise sections BY NAME on
#    every run. Today's board is still rendered, as an EXTRA: its checks
#    are asserted when it has the case, and reported when it does not.
# ⚠️ The kickoff is the REAL clock plus two days (a live tree gets the real
#    clock, never a frozen one); nothing asserted depends on the date.
# ══════════════════════════════════════════════════════════════════════
UNHELD = "Slippery Rock Aardvarks"   # a side no team table holds
PLANTED_N = 12                       # games planted; the floor is 10


def planted_board(lg, tree):
    """12 games from the league's own name table, one side unheld."""
    if lg == "nfl":
        names = sorted(D.nfl_table(tree))
    else:
        try:
            names = sorted(json.load(open(os.path.join(
                tree, "data", lg, "latest", "teams.json"),
                encoding="utf-8")).get("teams") or {})
        except (OSError, ValueError):
            names = []          # ⛔ the planted count check goes red, loudly
    names = names[:2 * PLANTED_N]
    now = datetime.datetime.now(datetime.timezone.utc)
    kick = (now + datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    games = [{"id": "planted-%s-%02d" % (lg, i), "commence": kick,
              "away": names[2 * i], "home": names[2 * i + 1],
              "total": 44.5, "run_line": -3.5,
              "run_line_team": names[2 * i + 1], "n_books": 4,
              "best_ml": {}, "vig_pct": 4.1}
             for i in range(len(names) // 2)]
    if games:
        games[0]["away"] = UNHELD
    return {"kind": "BOARD", "pulled_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "games": games}


def build(lg, planted=False):
    """The real builder, in a throwaway tree — on the PLANTED board, or
    (`planted=False`) on today's real one.

    ⛔ NOT THE COMMITTED ARTIFACT. `data/nfl/latest/dossiers.json.gz` on
    disk was written before `board_id` existed, so a check reading it
    would be asking about yesterday's builder.
    ⚠️ The tree is removed if anything here raises; the caller removes it
    otherwise (it leaked on every crash before 2026-09-28)."""
    d = tempfile.mkdtemp(prefix="dospage-")
    try:
        for f in os.listdir(ROOT):
            if f.endswith(".py") or f.endswith(".json"):
                shutil.copy(os.path.join(ROOT, f), d)
        shutil.copytree(os.path.join(ROOT, "data", lg),
                        os.path.join(d, "data", lg))
        if planted:
            with open(os.path.join(d, "data", lg, "latest", "board.json"),
                      "w", encoding="utf-8") as fh:
                json.dump(planted_board(lg, d), fh)
        p = os.path.join(d, "data", lg, "latest", "dossiers.json.gz")
        if os.path.exists(p):
            os.remove(p)
        r = subprocess.run([sys.executable, "-B", "dossier_fb.py"], cwd=d,
                           timeout=600, capture_output=True, text=True,
                           env=dict(os.environ, LEAGUE=lg))
        doc = json.load(gzip.open(p, "rt")) if os.path.exists(p) else None
    except BaseException:
        shutil.rmtree(d, ignore_errors=True)
        raise
    return d, doc, (r.stdout or "") + (r.stderr or "")


# ⚠️ ONE COPY OF THE DRIVER, WRITTEN OUT AT RUN TIME. It slices the panel
#    from the SHIPPED page rather than holding a copy of it — a copy is
#    the failure `test_banner.py`'s ancestor shipped, testing a file that
#    only existed in a scratch directory.
DRIVER = r"""
const fs = require('fs'), zlib = require('zlib');
const html = fs.readFileSync(process.argv[2], 'utf8');
const a = html.indexOf('const FBDOS = {};');
const b = html.indexOf('function fbOddsTable(list){');
if (a < 0 || b < 0 || b <= a){ console.error('PANEL_CODE_NOT_FOUND'); process.exit(2); }
const fn = new Function('LG_DATA','document','jgetGz', html.slice(a, b) +
  '\nreturn {fbDossierBy, fbDossierHtml};');
const M = fn({ mlb:'data', nfl:'data/nfl', ncaaf:'data/ncaaf' },
             { querySelectorAll: () => [], querySelector: () => null },
             async () => null);
const D = JSON.parse(zlib.gunzipSync(fs.readFileSync(process.argv[3])).toString());
const idx = M.fbDossierBy(D);
const rows = (D.dossiers || []).map(x => ({
  board_id: x.board_id || null,
  matched: idx.get(x.board_id) === x,
  unresolved_side: x.unresolved_side || null,
  n_sections: (x.sections || []).length,
  html: M.fbDossierHtml(idx.get(x.board_id))
}));
process.stdout.write(JSON.stringify({
  n_indexed: idx.size,
  miss_html: M.fbDossierHtml(idx.get('a-board-id-no-game-has')),
  rows
}));
"""


def drive(doc, tree):
    """Render every game through the SHIPPED panel code, in node."""
    dp = os.path.join(tree, "drive.js")
    open(dp, "w", encoding="utf-8").write(DRIVER)
    gz = os.path.join(tree, "doc.json.gz")
    with gzip.open(gz, "wt") as fh:
        json.dump(doc, fh)
    r = subprocess.run(["node", dp, PAGE, gz], cwd=tree, timeout=600,
                       capture_output=True, text=True)
    assert r.returncode == 0, "node driver failed: %s" % (r.stderr or "")[-500:]
    return json.loads(r.stdout)


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


section("1. 🔴🔴 THE PANEL IS REACHED — NOT MERELY DEFINED")
# ⛔ `calls()`, NOT `in HTML`. `fbScores` once carried a complete row
#    builder that was defined and never called; the tab rendered no live
#    game while the join worked perfectly (rule 130).
for _fn, _least in (("fbDossierLoad", 1), ("fbDossierBy", 1),
                    ("fbDossierHtml", 1), ("fbDosSection", 1),
                    ("fbDosFacts", 1), ("fbWireDossierRows", 1)):
    ck(calls(_fn, PAGE) >= _least,
       "   `%s` is CALLED (%d call site(s))" % (_fn, calls(_fn, PAGE)),
       "⛔ a renderer nobody calls looks exactly like the one that draws "
       "the page. THAT is how eight signals sat on disk unseen")
_odds = js_block("fbOddsTable", PAGE)
ck('class="dosrow"' in _odds and "data-bid=" in _odds,
   "🔴 the board row itself is the thing that opens (`tr.dosrow`)",
   "⛔ Sam asked for a game row that expands, the same shape as the "
   "`fbdd-<date>` rows. A panel with no handle is a panel nobody opens")
ck("fbdos-${g.id}" in _odds,
   "   ...and its detail row is keyed on the BOARD'S OWN id",
   "⛔ never the team names and never the kickoff")
ck("fbWireDossierRows" in js_block("fbOdds", PAGE),
   "   ...and `fbOdds` wires it AFTER drawing the rows",
   "🔴 `#fbview` is rebuilt from scratch by every football renderer, so "
   "a listener bound before the write is bound to a detached row — "
   "rule 197")

section("2. ⛔ THE JOIN IS ONE EXACT KEY, AND NOTHING IS INFERRED")
_by = js_block("fbDossierBy", PAGE)
for _forbidden, _why in (
        ("away_name", "a team-name key. CLAUDE.md: two legs are in "
                      "different games only if the GAME ID differs — a "
                      "live MLB card shipped four impossible parlays off "
                      "a name check, including its top recommendation"),
        ("home_name", "the same, for the other side"),
        ("commence", "a kickoff-time key. That is `boardFor()`'s "
                     "nearest-first-pitch problem, and re-solving it in "
                     "a second language is how the wrong-game bug put "
                     "six games' live odds on the next day's cards")):
    ck(_forbidden not in _by,
       "   the index does not key on `%s`" % _forbidden,
       "🔴 found %s" % _why)
ck("board_id" in _by,
   "🔴 ...it keys on `board_id`, which the BUILDER puts on the frame",
   "⛔ measured 2026-09-17: 0 of 32 dossier `game_id`s appear anywhere "
   "in `board.json` — they are different namespaces, so a page given "
   "only `game_id` cannot join at all")

section("3. 🔴🔴 IT RENDERS THE REAL ARTIFACT, BOTH LEAGUES — ON A PLANTED "
        "BOARD EVERY RUN, AND ON TODAY'S AS AN EXTRA")
# ══════════════════════════════════════════════════════════════════════
# ⛔ ONE SWEEP, RUN TWICE PER LEAGUE. On the PLANTED board every floor is a
# ck(): the case is there by construction, so a floor that fails is the
# code. On TODAY'S board the same checks run, but a floor that needs a
# case the slate lacks is REPORTED with note(), never failed — and every
# check that compares something the slate DOES hold is still asserted.
# ⚠️ Nothing was lowered: each bar below is the one this file had, and the
# planted twin adds three it never had (rendered == games on the board,
# the builder names the unheld side, and a count beside every sweep).
# ══════════════════════════════════════════════════════════════════════
_META = {"n", "name", "state", "basis"}
_PROSE = {"why", "remedy", "scale", "verdict", "open_gap", "known_gap",
          "coverage_note", "weather_note", "closing_note", "note"}


def sweep(tag, doc, R, planted):
    """Every section-3 question over one rendered document.

    -> (tag, games rendered, sections that could not answer, partial games).
    """
    rows = R["rows"]

    def floor(cond, label, why):
        """A rule-67 floor: ck() on the planted board, note() on today's."""
        if planted:
            ck(cond, label, why)
        else:
            note(label + ("" if cond else
                          " — not on today's board; the PLANTED board "
                          "carries this case on every run"))
        return bool(cond)

    if planted:
        ck(len(rows) == doc.get("n_board_games") and len(rows) >= 10,
           "   %s: %d game(s) rendered through the shipped panel code "
           "(%s on the board)" % (tag, len(rows), doc.get("n_board_games")),
           "⛔ rule 67: a sweep over one game proves nothing about a board, "
           "and a planted game that did not render was DROPPED")
        ck(any(r["unresolved_side"] == UNHELD for r in rows),
           "   %s: ...one of them a side we hold no record for, NAMED by "
           "the builder" % tag,
           "⛔ without it no section is guaranteed to refuse, and every "
           "gap check below would compare 0 with 0. Named: %s"
           % sorted({str(r["unresolved_side"]) for r in rows}))
    else:
        note("   %s: %d game(s) rendered through the shipped panel code — "
             "a fact about today's slate; the PLANTED board carries the "
             "floor" % (tag, len(rows)))
    ck("No signals stored" in R["miss_html"],
       "   %s: ...and a board id no game has matches NOTHING" % tag,
       "🔴 the fallback must be an honest empty state, never a "
       "neighbouring game. Got: %s" % text(R["miss_html"])[:120])
    if not rows:
        return (tag, 0, 0, 0)
    ck(R["n_indexed"] == len(rows) and all(r["matched"] for r in rows),
       "🔴 %s: EVERY game joins on `board_id` (%d of %d)"
       % (tag, R["n_indexed"], len(rows)),
       "⛔ a game with no panel is a gap; a game shown ANOTHER game's "
       "panel is misinformation. Unmatched: %s"
       % [r["board_id"] for r in rows if not r["matched"]][:4])
    # ── EVERY SECTION IS ON THE PAGE, AVAILABLE OR NOT ────────────────
    names = [s["name"] for s in doc["dossiers"][0]["sections"]]
    # ⚠️ The artifact's own declared count; files built before signal 9
    #    (9th section, 2026-09-24) declared nothing and carry eight.
    ck(len(names) == doc.get("sections_declared", 8) and len(names) >= 8,
       "   %s: the artifact carries every section it declares (%d)"
       % (tag, len(names)),
       "⛔ rule 67 again — eight is the premise of every check below. "
       "Got %s" % names)
    missing = [(r["board_id"], n) for r in rows for n in names
               if n not in r["html"]]
    ck(not missing,
       "🔴🔴 %s: ALL %d SECTIONS APPEAR FOR EVERY GAME" % (tag, len(names)),
       "⛔ HIDING A SECTION THAT CANNOT ANSWER IS THE WHOLE FAILURE THIS "
       "ARTIFACT EXISTS AGAINST — it would show a board where every game "
       "looks fully analysed. Missing: %s" % missing[:4])
    gaps = sum(len(re.findall(r'dossec gap', r["html"])) for r in rows)
    dgaps = sum(1 for x in doc["dossiers"] for s in x["sections"]
                if s["state"] != "OK")
    if floor(dgaps >= 1,
             "   %s: the artifact carries %d section(s) that cannot answer"
             % (tag, dgaps),
             "⛔ rule 67: the next check would compare 0 with 0"):
        ck(gaps == dgaps,
           "   %s: every section that cannot answer is DRAWN (%d of %d)"
           % (tag, gaps, dgaps),
           "⛔ the refusals are the honesty. Artifact says %d, page drew %d"
           % (dgaps, gaps))
    # ══════════════════════════════════════════════════════════════════
    # 🔴🔴 AND A SECTION THAT CAN ANSWER MUST SHOW ONE OF THE BUILDER'S
    # OWN VALUES, NOT ONLY ITS SENTENCE. `[2026-09-17 — the first draft
    # of the panel printed the `why` and nothing else, so "This season"
    # and "Versus position" read OK with a heading and a paragraph.]`
    # ⛔ That is the Task 27 disease one layer out: a section that knows
    # something and displays none of it looks exactly like one that
    # knows nothing, and the whole point of the eight is that a reader
    # can tell those apart.
    # ⚠️ THE EXPECTATION IS DERIVED FROM THE ARTIFACT, never a list of
    # section numbers. A section is owed a value only if the artifact
    # actually carries one for it — so this cannot fire on a section
    # that legitimately has nothing but its sentence, which is the other
    # failure CLAUDE.md names.
    # ══════════════════════════════════════════════════════════════════
    mute, owed = [], 0
    for r, x in zip(rows, doc["dossiers"]):
        frags = r["html"].split('<div class="dossec')
        for s in x["sections"]:
            if s["state"] != "OK":
                continue
            pay = {k: v for k, v in s.items()
                   if k not in _META and k not in _PROSE
                   and v not in (None, {}, [], "")}
            if not pay:
                continue
            owed += 1
            f = [g for g in frags if ">%s<" % s["name"] in g]
            if not f or "<li>" not in f[0]:
                mute.append((r["board_id"], s["name"], sorted(pay)))
    if floor(owed >= 1,
             "   %s: %d section(s) that CAN answer hold a stored value"
             % (tag, owed),
             "⛔ rule 67: the next check would sweep nothing"):
        ck(not mute,
           "🔴 %s: every section that CAN answer shows a stored value, not "
           "just a sentence (%d)" % (tag, owed),
           "⛔ a heading and a paragraph over data the artifact is holding "
           "is a section that looks empty while knowing something. "
           "Silent: %s" % mute[:4])
    owed_why = [(r, s) for r, x in zip(rows, doc["dossiers"])
                for s in x["sections"] if s["state"] != "OK" and s.get("why")]
    if floor(len(owed_why) >= 1,
             "   %s: %d refusal reason(s) to compare" % (tag, len(owed_why)),
             "⛔ rule 67: the next check would compare nothing"):
        reworded = [(r["board_id"], s["name"]) for r, s in owed_why
                    if s["why"] not in r["html"]]
        ck(not reworded,
           "   %s: ...carrying the BUILDER'S OWN reason, verbatim (%d)"
           % (tag, len(owed_why)),
           "⛔ a second sentence written in JavaScript is a second copy of "
           "the reasoning (rule 132). Reworded: %s" % reworded[:3])
    # ── THE REGISTER ─────────────────────────────────────────────────
    # ⚠️ On the planted board this reads the builder's REFUSAL prose too
    #    (`no_opponent`), which today's board carries only on a one-sided
    #    game — none on 2026-09-28 in either league.
    alltext = text(" ".join(r["html"] for r in rows))
    hits = sorted({j for j in JARGON if j in alltext})
    ck(not hits,
       "🔴 %s: ZERO jargon in the rendered panel (%d term(s) checked)"
       % (tag, len(JARGON)),
       "⛔ THE LIST IS `verify_card.py`'s OWN and the football panel does "
       "not get an easier one. Found %s" % hits)
    ops = sorted(set(OPERATOR.findall(alltext)))
    ck(not ops,
       "   %s: ...and nothing operator-facing either" % tag,
       "⛔ no filename, path, backticked code or collector mode name. A "
       "reader does not run the jobs. Found %s" % ops[:6])
    ck("MODEL" not in alltext and not re.search(
           r"\d{1,3}\s*%\s*(conf|chance)", alltext, re.I),
       "   %s: ...and no Gizmo's confidence anywhere on it (rule 55)" % tag,
       "⛔ every number in this artifact is the market's or a record; "
       "none is a model output, and none may sit beside one")
    return (tag, len(rows), dgaps,
            sum(1 for r in rows if r["unresolved_side"]))


# ⚠️ FOUR BUILDS, THE SAME AS BEFORE: sections 4 and 5 take their frames
#    from these documents instead of building again.
DOCS = {}
_seen = []
for _lg in ("nfl", "ncaaf"):
    for _planted in (True, False):
        _tag = ("planted " if _planted else "live ") + _lg
        _tree, _doc, _log = build(_lg, _planted)
        try:
            ck(_doc is not None,
               "⚠️ %s: the builder produced a dossier to render" % _tag,
               "⛔ every check below would pass over nothing (rule 67). %s"
               % _log[-300:])
            if _doc is not None:
                _R = drive(_doc, _tree)
                _seen.append(sweep(_tag, _doc, _R, _planted))
                DOCS[(_lg, _planted)] = (_doc, _R)
        finally:
            shutil.rmtree(_tree, ignore_errors=True)
note("   board / games rendered / sections that could not answer / "
     "partial games: %s" % (_seen,))

section("4. 🔴🔴 A PARTIAL GAME LOOKS PARTIAL — DRIVEN, NOT HOPED FOR")
# ══════════════════════════════════════════════════════════════════════
# ⛔ PLANTED ON PURPOSE, AND UNCONDITIONALLY. 16 of the 90 college
# games on today's board carry an opponent the season files do not cover
# — but that is a fact about THE BOARD: measured across 36 stored college
# boards it runs 0 to 41, and 2 of them carried ZERO. Asserting the real
# board holds one would redden this suite on a mid-Saturday board that is
# perfectly good, which is the other failure CLAUDE.md names.
# ✅ So the case comes from the PLANTED board of section 3, and the check
# is true every day. `[2026-09-28]` ~~Carved out of the LIVE build and
# injected by hand~~ — that needed two live games (it died on a 1-game
# board) and wrote the one-sided frame itself. The frame is now the REAL
# BUILDER's own one-sided game, which is the stronger claim.
# ══════════════════════════════════════════════════════════════════════
_src4 = (DOCS.get(("nfl", True)) or (None, None))[0]
ck(_src4 is not None, "⚠️ there is a PLANTED document to render from",
   "⛔ section 3 already failed the planted NFL build")
if _src4 is not None:
    _doc4 = json.loads(json.dumps(_src4))
    _one4 = [x for x in _doc4["dossiers"] if x.get("unresolved_side") == UNHELD]
    _two4 = [x for x in _doc4["dossiers"]
             if x.get("board_id") and not x.get("unresolved_side")]
    ck(bool(_one4) and bool(_two4),
       "⚠️ ...holding the builder's own one-sided game and a second frame "
       "(%d + %d)" % (len(_one4), len(_two4)),
       "⛔ rule 67: every check below would pass over nothing")
if _src4 is not None and _one4 and _two4:
    _g4 = _one4[0]
    # ⛔ AND A SECOND FRAME WITH NO `board_id` AT ALL, to prove the index
    #    SKIPS it rather than reaching for another key.
    _g5 = dict(_two4[0])
    _g5.pop("board_id", None)
    _doc4["dossiers"] = [_g4, _g5]
    _tree4 = tempfile.mkdtemp(prefix="dospage-")
    try:
        _R4 = drive(_doc4, _tree4)
    finally:
        shutil.rmtree(_tree4, ignore_errors=True)
    _h4 = _R4["rows"][0]["html"]
    ck(UNHELD in _h4,
       "🔴🔴 THE SIDE WITH NO SEASON RECORD IS NAMED ON THE PANEL",
       "⛔ NEVER RENDER A BLANK WHERE A TEAM NAME BELONGS. The board has "
       "the name and the builder carries it through — publishing nothing "
       "throws away the one thing we did know. Got: %s" % text(_h4)[:160])
    # ══════════════════════════════════════════════════════════════════
    # [Sam, 2026-10-01] ~~"...and the game is MARKED partial, not quietly
    # short" — a `span.dospart` on the header reading "no season record
    # for <side>"~~. Sam removed every per-row flag from every tab ("i
    # just want what's supposed to be in each tab to be in each tab"), so
    # the flag is now REQUIRED ABSENT: the header is the two names and
    # nothing else. ✅ THE GAME STILL LOOKS PARTIAL, through what still
    # renders: every section the builder refused is drawn as a gap, and
    # the refusals carry the builder's own sentence naming the side.
    # ══════════════════════════════════════════════════════════════════
    _hd4 = _h4.split('<div class="dosg">')[0]
    ck("dospart" not in _h4 and text(_hd4) == "%s at %s"
       % (_g4.get("away_name"), _g4.get("home_name")),
       "   ⛔ ...and the header is the two names, with NO partial flag "
       "[Sam, 2026-10-01]",
       "🔴 a flag on the game header is the per-row flag Sam removed from "
       "every tab. Got: %s" % text(_hd4)[:160])
    _ref4 = [s.get("why") or "" for s in _g4["sections"]
             if s["state"] != "OK"]
    ck(len(_ref4) >= 1 and _h4.count("dossec gap") == len(_ref4)
       and any(UNHELD in w and w in _h4 for w in _ref4),
       "   ...and the game still LOOKS partial: its %d refused section(s) "
       "are drawn as gaps, the builder's sentence naming the side"
       % len(_ref4),
       "⛔ 16 of 90 college games are like this. A panel that looks "
       "complete on one of them is the failure the eight exist against. "
       "Drew %d gap(s)" % _h4.count("dossec gap"))
    ck(" at </div>" not in _h4 and " at <span" not in _h4,
       "   ⛔ ...and the header has no empty team slot",
       "🔴 `X at ` with nothing after it is exactly the `Oregon vs None` "
       "shape, moved to the browser. Got: %s" % text(_h4)[:120])
    ck(_R4["n_indexed"] == 1 and not _R4["rows"][1]["matched"],
       "🔴 a frame with NO `board_id` is SKIPPED, not matched some other "
       "way (%d indexed of 2)" % _R4["n_indexed"],
       "⛔ this is the check that stops a name or time fallback creeping "
       "back in. Matched: %s" % [r["matched"] for r in _R4["rows"]])
section("5. 🔴🔴 THE BOOK COUNT SAYS WHAT IT COUNTS")
# ══════════════════════════════════════════════════════════════════════
# 🔴 "Books priced 0" SAT DIRECTLY BESIDE A TOTAL OF 67.5 THAT A NAMED
# BOOK WAS SHOWING. `[found in review, 2026-09-17]` `n_books` is
# `len(vigs)` in `collect.py` and `vigs` comes from the MONEYLINE de-vig,
# so it counts books showing a two-sided moneyline — not books pricing
# the game. MEASURED on the live college board: 15 of 90 games have an
# empty `best_ml` AND `n_books == 0`, the same 15, and all 15 still carry
# a total and a spread.
#
# ➡️ THE CLASS: A FIELD NAME NARROWER THAN IT READS IS HARMLESS UNTIL
# SOMETHING DISPLAYS IT. `n_books` had been correct and privately
# understood for weeks; the defect was created by putting it on the page
# beside the thing it does not count. ⚠️ AND I GUARDED THE INSTANCE, NOT
# THE CLASS, DELIBERATELY: "re-read what a field actually counts when it
# first reaches the surface" is a thing a person does, not a question a
# check can ask. What IS checkable is that THIS count names its subject
# and never reads as "nothing is priced" — so that is what is checked,
# on the real board and on an injected row.
#
# ⛔ THE ZERO IS NOT SUPPRESSED, and the check below insists on that: a
# game we hold no moneyline for is a real fact about a mismatch this
# size, and hiding it would make those 15 look like the other 75.
# ⚠️ "we hold none", not "no book will quote one" — CLAUDE.md: an absence
# in an API response is evidence about the API, never about the
# sportsbook, and this project has got that backwards five times.
# [Sam, 2026-10-01] ~~and a sentence under the zero says so~~ — the page
# draws no explanation under a number on any tab, so the label is the
# whole statement and the sentence is asked for its ABSENCE below.
# ══════════════════════════════════════════════════════════════════════
# ⛔ THE CONTRADICTION SHAPE, not the old literal. A label that reads as
#    "nothing is priced" beside a price is the defect whatever word it
#    reaches for, so the pattern covers priced/prices/pricing.
_PRICED0 = re.compile(r"pric(?:ed|es|ing)[^0-9<]{0,40}(?:<[^>]+>\s*)?0\b",
                      re.I)


def market_of(html):
    """The market section's own fragment, or '' if it is not there."""
    for g in html.split('<div class="dossec'):
        if ">Market<" in g:
            return g
    return ""


def market_sweep(tag, R, planted):
    """The book-count sweep over one rendered board.

    ⛔ It asserts ABSENCES, so it cannot false-alarm on a board that
    happens to carry no zero — the board-dependent floor is the mistake
    #51 fixed. ✅ Its rule-67 floor is asked of the PLANTED board, where
    every game has a market section by construction; today's board is an
    extra, swept when it has games and reported when it has none."""
    mkts = [(r["board_id"], market_of(r["html"])) for r in R["rows"]]
    if planted:
        ck(len(mkts) >= 10 and all(m for _b, m in mkts),
           "⚠️ %s: every game rendered a market section (%d)"
           % (tag, len(mkts)),
           "⛔ rule 67: the sweep below would pass over nothing. Missing: %s"
           % [b for b, m in mkts if not m][:4])
    elif not mkts:
        note("   %s: no games on today's board — nothing to sweep; the "
             "PLANTED board carries the case" % tag)
        return
    else:
        ck(all(m for _b, m in mkts),
           "⚠️ %s: every game rendered a market section (%d)"
           % (tag, len(mkts)),
           "⛔ the Market section is built for every game. Missing: %s"
           % [b for b, m in mkts if not m][:4])
    contra = [b for b, m in mkts if _PRICED0.search(m)]
    ck(not contra,
       "🔴 %s: no game reads as 'nothing is priced' beside a price" % tag,
       "⛔ THIS IS THE DEFECT: 'Books priced 0' next to a total of 67.5 "
       "that Hard Rock was showing. A reader who sees 0 beside a number "
       "they can bet stops trusting the page. Games: %s" % contra[:4])
    nolabel = [b for b, m in mkts if "Books" in m and "moneyline" not in m]
    ck(not nolabel,
       "   ⛔ %s: ...and every book count on it NAMES what it counts" % tag,
       "🔴 the count is of books showing a two-sided MONEYLINE, and a "
       "bare 'Books' is the reading that was wrong. Games: %s"
       % nolabel[:4])


for _planted in (True, False):
    _src5 = DOCS.get(("ncaaf", _planted))
    if _src5 is None:
        # ⚠️ section 3 already asserted the build; a planted miss is red
        #    there, and this line says why section 5 is thinner.
        note("   %s ncaaf: no document to sweep (section 3 says why)"
             % ("planted" if _planted else "live"))
        continue
    market_sweep(("planted " if _planted else "live ") + "ncaaf",
                 _src5[1], _planted)
if DOCS.get(("ncaaf", False)):
    _live5 = DOCS[("ncaaf", False)][0]
    note("   %d of %d real college games carry a zero book count — "
         "reported, NOT asserted (it is a fact about today's board)."
         % (len([1 for x in _live5["dossiers"]
                 for s_ in x["sections"]
                 if s_.get("n") == 1
                 and (s_.get("live") or {}).get("n_books") == 0]),
            len(_live5["dossiers"])))

# ── AND DRIVEN ON AN INJECTED ROW, unconditionally. ⛔ The real board
#    carried 15 today and could carry none tomorrow; the case this file
#    exists for must be driven either way. `[2026-09-28]` The frame is
#    taken from the PLANTED college document, never today's board, which
#    is empty from January to August (this line died on it).
_src6 = (DOCS.get(("ncaaf", True)) or (None, None))[0]
ck(_src6 is not None and bool(_src6.get("dossiers")),
   "⚠️ there is a PLANTED college frame to inject into",
   "⛔ rule 67: every check below would pass over nothing")
if _src6 is not None and _src6.get("dossiers"):
    _doc5 = json.loads(json.dumps(_src6))
    _g5 = _doc5["dossiers"][0]
    _m5 = [x for x in _g5["sections"] if x["n"] == 1][0]
    _m5.setdefault("live", {})
    _m5["live"]["n_books"] = 0
    _m5["live"]["total"] = 67.5
    _m5["live"]["run_line"] = -56.5
    _g6 = json.loads(json.dumps(_g5))
    _g6["board_id"] = "second-frame-for-the-positive-control"
    [x for x in _g6["sections"] if x["n"] == 1][0]["live"]["n_books"] = 4
    _doc5["dossiers"] = [_g5, _g6]
    _tree5 = tempfile.mkdtemp(prefix="dospage-")
    try:
        _R6 = drive(_doc5, _tree5)
    finally:
        shutil.rmtree(_tree5, ignore_errors=True)
    _z = market_of(_R6["rows"][0]["html"])
    _p = market_of(_R6["rows"][1]["html"])
    ck(bool(_z) and bool(_p),
       "⚠️ both injected rows rendered a market section",
       "⛔ rule 67 again — the checks below would pass over empty strings")
    ck(not _PRICED0.search(_z),
       "🔴🔴 A ZERO COUNT BESIDE A LIVE TOTAL DOES NOT SAY 'PRICED'",
       "⛔ THE WHOLE FINDING. Got: %s" % text(_z)[:200])
    ck("67.5" in _z,
       "   ⛔ ...and the total is still shown",
       "🔴 the price is real and it is the one thing we know for sure. "
       "Got: %s" % text(_z)[:200])
    ck("moneyline <b>0</b>" in _z,
       "   ⛔ ...and the ZERO IS NOT SUPPRESSED, it is LABELLED",
       "🔴 hiding it would make these games look like the rest of the "
       "board. Got: %s" % text(_z)[:200])
    ck("moneyline" in _z,
       "🔴 ...and the label NAMES the moneyline, which is what it counts",
       "⛔ `n_books` is `len(vigs)` off the moneyline de-vig. A bare "
       "'Books' is the reading that put 0 beside a price. Got: %s"
       % text(_z)[:200])
    # ⚠️ ON THE NORMALISED TEXT, not the raw HTML. The sentence is a
    #    template literal, so it carries newlines and indentation that a
    #    browser collapses and a substring match does not — a check that
    #    fails on how the source is WRAPPED is a check that reddens on
    #    correct code.
    _ztxt = text(_z)
    # [Sam, 2026-10-01] ~~"✅ ...and the zero is explained in words a reader
    #    can use" — "That zero is about the moneyline only ... the total and
    #    spread above are real prices a book is showing", under the count~~.
    #    A warning line under a number is the explanation box Sam removed
    #    from every tab, so it is now REQUIRED ABSENT. ✅ The zero still
    #    reads right through what still renders: the label names the
    #    moneyline and the 0 is shown, not suppressed (the checks above).
    ck(bool(_z) and "moneyline only" not in _ztxt
       and "real prices" not in _ztxt and "&#9888;" not in _z,
       "   ⛔ ...and NO sentence explains the zero: the label carries it "
       "[Sam, 2026-10-01]",
       "🔴 a warning sentence under the count is the explanation box Sam "
       "removed from every tab. Got: %s" % _ztxt[:240])
    ck("moneyline" in _p and not _PRICED0.search(_p),
       "   ⚠️ ...and a NON-zero count is labelled the same way",
       "🔴 one label, both cases — a special case for zero would be two "
       "descriptions of one field. Got: %s" % text(_p)[:200])
    ck("real prices" not in text(_p),
       "   ⛔ ...without the zero explanation attached to it",
       "🔴 a sentence about a missing moneyline under a count of 4 is "
       "noise, and noise is what the clean-look rule is about. Got: %s"
       % text(_p)[:200])
note("⛔ WHAT THIS FILE DOES NOT CLAIM: that the panel is well designed, "
     "or that a reader finds it useful. It claims the eight signals "
     "REACH A READER, every section is shown whether or not it could "
     "answer, the join is exact, and every word on it is the builder's "
     "own and passes the MLB card's jargon bar. ➡️ Whether it reads well "
     "is Sam's call, and it is the one thing no test can make.")
