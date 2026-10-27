#!/usr/bin/env python3
"""teamkeys.py — THE ONE RESOLVER: a sportsbook's team name -> the key that league's files use.

`[2026-10-27, review 2]` Moved here, unchanged, out of `dossier_fb.py`, which re-exports it
(`dossier_fb.team_codes`, `nfl_table`, `_norm_school`, `CFB_ALIAS`), so every caller keeps
its name. ⛔ Why it moved: `card_fb.py` now needs it (a name two players share is decided by
the board game's two teams, `card_fb.match_player`), and the card must never reach the
dossier (`test_dossier_fb.py` §3 builds the card with and without `dossier_fb.py` and diffs
them, and checks `card_fb.py` never names it). A name-to-key table is not one of Sam's eight
checks; it was only kept there. ⛔ ONE COPY (rule 117): nothing else may parse NFL_TEAMS or
fold a college name. Stdlib only, reads two files, writes nothing.
"""
import ast
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))

# ⛔ VERIFIED ONE BY ONE AGAINST `teams.json`, NEVER FUZZY-MATCHED. The
# college board names a school plus its mascot ("Syracuse Orange") while
# every college artifact keys on the school alone ("Syracuse"), so the
# join is a prefix match — and three FBS schools are spelled differently
# on the two sides. ⚠️ `difflib` was tried and REFUSED: it maps "East
# Texas A&M Lions" onto "Texas A&M", "Portland State" onto "Colorado
# State" and "South Dakota" onto "North Dakota State" — different
# schools. That is `resolve()`'s rule (CLAUDE.md): refuse to guess.
CFB_ALIAS = {"appalachianstate": "App State",
             "southernmississippi": "Southern Miss",
             "umass": "Massachusetts"}


def _norm_school(s):
    """Fold case, accents and punctuation. ⚠️ `San José State` and `San
    Jose State` are one school; `Hawai'i` and `Hawaii` are one school."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def nfl_table(root=None):
    """`collect.py`'s NFL_TEAMS, READ from its source: board name -> the key
    NFL files use. ⛔ ONE PARSE (rule 117): `team_codes()` and every test
    that plants a board read this, never a retyped copy of the table.
    `[2026-09-28]` Exposed so a test can plant games the builder resolves."""
    src = open(os.path.join(root or ROOT, "collect.py"), encoding="utf-8").read()
    for n in ast.parse(src).body:
        if (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "")
                == "NFL_TEAMS"):
            return dict(ast.literal_eval(n.value))
    return {}


def team_codes(lg=None):
    """A RESOLVER: board team name -> the key that league's files use.

    ⚠️ IT RETURNS A FUNCTION, not a dict, because the two leagues join
    differently. NFL board names are exact keys of a 32-row table;
    college names need folding and a longest-prefix match.

    ⛔ NFL's TABLE IS READ OUT OF `collect.py`'s SOURCE, never retyped.
    That file's own comment says "if you edit one side, edit both", and a
    second copy of a 32-row table is a second thing to drift (rule 66).
    ⚠️ Parsed rather than imported: importing the collector runs its
    module-level league handling, and a reporting tool must not be able
    to trip that.

    ⛔ AND IT RETURNS None RATHER THAN A GUESS. 16 of the 88 college
    board sides are FCS schools absent from the FBS `teams.json` — a
    correct absence, not a failure, and naming it is the only honest
    answer.
    """
    lg = (lg or os.environ.get("LEAGUE") or "nfl").strip().lower()
    if lg == "nfl":
        return nfl_table().get
    # ── college ──────────────────────────────────────────────────────
    try:
        raw = json.load(open(os.path.join(ROOT, "data", lg, "latest",
                                          "teams.json"), encoding="utf-8"))
        schools = list((raw.get("teams") or {}))
    except Exception:
        schools = []
    idx = {}
    for t in schools:
        idx.setdefault(_norm_school(t), t)
    # ⚠️ LONGEST FIRST, so "Miami (OH) RedHawks" resolves to `Miami (OH)`
    #    and not to `Miami`.
    order = sorted(idx, key=len, reverse=True)

    def resolve(name):
        n = _norm_school(name)
        if not n:
            return None
        for a, t in CFB_ALIAS.items():
            if n.startswith(a):
                return t
        for k in order:
            if n == k or n.startswith(k):
                return idx[k]
        return None
    return resolve
