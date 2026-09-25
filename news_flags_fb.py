#!/usr/bin/env python3
"""news_flags_fb.py — the free news-flag reviewer (Sam, 2026-09-25). It
FLAGS; it never picks.

    LEAGUE=nfl python news_flags_fb.py

Once a day, for every player and team on the football board — props rows,
the card's parlay legs, the Game Lines games — it looks for:

  1. NFL injury-report status (OUT, DOUBTFUL, QUESTIONABLE, IR), from the
     nflverse injury rows signal 7 already downloads (`injury_report` in
     `players-<season>.json.gz`). ⛔ COLLEGE HAS NONE: the conferences'
     terms forbid scraping their reports, so college is headlines only.
  2. Headlines already stored (today's `news.json` and the dated archive)
     that name the player with a status word.

⛔ A FLAG IS DESCRIPTIVE. It never removes, hides, re-ranks or re-prices a
row, and never feeds any model.
⛔ NAMES MATCH ON THE EXACT FULL NAME, as a whole phrase — never a substring
("Josh Allen" never matches "Josh Allenby"). A headline name shared by two
players in the league's logs attaches only when the headline also names
that player's team; an injury row attaches only when its team is one of the
two teams in that player's game.
⛔ FROZEN AND GRADED ONCE. Every flag is archived with its time (daystore);
after the game a player flag is graded — did he play? — once, and never
recomputed. ⚠️ STDLIB ONLY. Rides the existing news run; no new cron.
"""
import datetime
import glob
import gzip
import hashlib
import html
import json
import os
import re
import sys

import daystore                     # the ONE dated, write-once writer
import dossier_fb as D              # team_codes — the board-to-files join
import fb_props_model as M          # load_logs, name_index, game_row, league
import freshness
import record_fb                    # _played — the card's own "did he play"
import signal9                      # week_of — a card's own week

ROOT = os.path.dirname(os.path.abspath(__file__))
LEAGUE = os.environ.get("LEAGUE", "nfl")
NEWS_DAYS = 3
STATUS_WORDS = ("ruled out", "questionable", "doubtful", "inactive", "limited", "suspended",
                "traded", "released", "benched", "illness")          # ⛔ Sam's list, 2026-09-25
INJ_STATUS = {"out": "OUT", "doubtful": "DOUBTFUL", "questionable": "QUESTIONABLE",
              "injured reserve": "IR", "reserve/injured": "IR"}
# a flag that says he should not play, against one that says he might not
ABSENCE = {"OUT", "DOUBTFUL", "IR", "ruled out", "inactive", "suspended", "traded", "released",
           "benched"}
COLLEGE_NOTE = ("College football has no public injury reports we may use — the conferences' "
                "terms forbid scraping them — so college flags come from headlines only.")


def log(m):
    print(m, flush=True)


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _gz(path):
    try:
        return json.load(gzip.open(path, "rt", encoding="utf-8"))
    except (OSError, ValueError, EOFError):
        return None


def _json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _data(lg, root=None):
    return os.path.join(root or ROOT, "data", lg)


def clean(text):
    """HTML entities out, curly quotes straight — nothing else changes."""
    return html.unescape(text or "").replace("’", "'").replace("‘", "'")


def names_in(name, text):
    """Is `name` in `text` as the EXACT full name — a whole phrase, case as
    written, never inside a longer word or name?"""
    if not name or not text:
        return False
    return re.search(r"(?<![\w'])" + re.escape(clean(name)) + r"(?![\w])", clean(text)) is not None


def status_in(text):
    """The first of Sam's status words in the text, whole words only."""
    low = clean(text).lower()
    for w in STATUS_WORDS:
        if re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", low):
            return w
    return None


# ══════════════════════════════════════════════════════════════════════
# WHO IS ON THE BOARD
# ══════════════════════════════════════════════════════════════════════
def board(lg, root=None):
    """-> (players, teams): [{name, game_id, commence, home, away}] each."""
    latest = os.path.join(_data(lg, root), "latest")
    players, teams, seen = [], [], set()

    def addp(name, gid, commence, home, away):
        k = (name, gid)
        if name and gid and k not in seen:
            seen.add(k)
            players.append({"name": name, "game_id": gid, "commence": commence, "home": home, "away": away})
    for g in (_gz(os.path.join(latest, "props.json.gz")) or {}).get("games") or []:
        for p in g.get("props") or []:
            addp(p.get("player"), g.get("id"), g.get("commence"), g.get("home"), g.get("away"))
    card = _json(os.path.join(root or ROOT, "picks", "fb-%s-latest.json" % lg)) or {}
    for r in card.get("picks") or []:
        addp(r.get("player"), r.get("game_id"), r.get("commence"), r.get("home"), r.get("away"))
    gl = _gz(os.path.join(latest, "game-lines.json.gz")) or {}
    tseen = set()
    for g in gl.get("games") or []:
        for t in (g.get("home"), g.get("away")):
            if t and (t, g.get("id")) not in tseen:
                tseen.add((t, g.get("id")))
                teams.append({"name": t, "game_id": g.get("id"), "commence": g.get("commence"),
                              "home": g.get("home"), "away": g.get("away")})
    return players, teams


def headlines(lg, root=None, now=None, days=NEWS_DAYS):
    """Every stored headline of the last `days` days, once each (by link)."""
    now = now or _now()
    out, seen = [], set()
    docs = [_json(os.path.join(_data(lg, root), "latest", "news.json")) or {}]
    for back in range(days, -1, -1):
        day = (now - datetime.timedelta(days=back)).strftime("%Y-%m-%d")
        for p in sorted(glob.glob(os.path.join(_data(lg, root), day, "news", "*.json.gz"))):
            docs.append(_gz(p) or {})
    for d in docs:
        for it in d.get("items") or []:
            k = it.get("link") or it.get("title")
            if k and k not in seen and it.get("title"):
                seen.add(k)
                out.append(it)
    return out


def shared_names(lg, root=None, logs=None):
    """{name: number of players} for names more than one player carries."""
    logs = logs if logs is not None else M.load_logs(lg, root)
    idx = M.name_index(logs)
    return {k: len(v) for k, v in idx.items() if len(v) > 1}, idx


def injury_rows(lg, root=None, now=None):
    if lg != "nfl":
        return []
    season = freshness.current_football_season(now)
    doc = _gz(os.path.join(_data(lg, root), "latest", "players-%d.json.gz" % season)) or {}
    return doc.get("injury_report") or []


# ══════════════════════════════════════════════════════════════════════
# THE FLAGS
# ══════════════════════════════════════════════════════════════════════
def _flag(kind, subj, source, status, headline=None, link=None, published=None, team=None):
    key = "|".join(str(x) for x in (kind, subj["name"], subj["game_id"], source, status, link or ""))
    return {"key": key, "kind": kind, "subject": subj["name"], "game_id": subj["game_id"],
            "commence": subj["commence"], "team": team, "source": source, "status": status,
            "headline": headline, "link": link, "published": published, "basis": "DESCRIPTIVE"}


def flags(lg, players, teams, news, inj, shared, idx, resolve, week_of):
    """-> (flags, report). Pure: every input is passed in."""
    out, rep = [], {"headlines": len(news), "players": len(players), "teams": len(teams),
                    "injury_rows": len(inj), "ambiguous_skipped": 0}
    import card_fb
    for s in players:
        home_c, away_c = resolve(s["home"]), resolve(s["away"])
        # 1. the injury report: exact full name, and his team must be in this game
        if inj:
            wk = week_of(s["commence"])
            for r in inj:
                if str(r.get("week")) != str(wk) or r.get("team") not in (home_c, away_c):
                    continue
                if r.get("full_name") != s["name"] and card_fb.norm(r.get("full_name") or "") != card_fb.norm(s["name"]):
                    continue
                st = INJ_STATUS.get((r.get("report_status") or "").strip().lower())
                if st:
                    out.append(_flag("player", s, "injury report", st, team=r.get("team")))
        # 2. headlines: the exact full name AND one of Sam's status words
        n_shared = shared.get(card_fb.norm(s["name"]), 0)
        for it in news:
            title = it.get("title")
            if not names_in(s["name"], title):
                continue
            w = status_in(title)
            if not w:
                continue
            if n_shared > 1 and not (names_in(s["home"], title) or names_in(s["away"], title)):
                rep["ambiguous_skipped"] += 1
                continue
            out.append(_flag("player", s, "headline", w, clean(title), it.get("link"), it.get("published")))
    for t in teams:
        code = resolve(t["name"])
        if inj and code:
            wk = week_of(t["commence"])
            for r in inj:
                st = INJ_STATUS.get((r.get("report_status") or "").strip().lower())
                if st and r.get("team") == code and str(r.get("week")) == str(wk):
                    out.append(_flag("team", t, "injury report", st,
                                     headline=r.get("full_name"), team=code))
        for it in news:
            title = it.get("title")
            w = status_in(title) if names_in(t["name"], title) else None
            if w:
                out.append(_flag("team", t, "headline", w, clean(title), it.get("link"), it.get("published")))
    uniq = {}
    for f in out:
        uniq.setdefault(f["key"], f)
    return list(uniq.values()), rep


def parlay_flags(lg, fl, root=None):
    """Flags on parlay legs: a leg is its player's (or team's) when the leg's
    text BEGINS with that exact full name and a space, in that leg's game."""
    by_game = {}
    for f in fl:
        by_game.setdefault(f["game_id"], []).append(f)
    out = []
    card = _json(os.path.join(root or ROOT, "picks", "fb-%s-latest.json" % lg)) or {}
    gl = _gz(os.path.join(_data(lg, root), "latest", "game-lines.json.gz")) or {}
    for src, P in (("card", card.get("parlays") or {}), ("game_lines", gl.get("parlays") or {})):
        for size, lst in P.items():
            for i, p in enumerate(lst or []):
                for j, (leg, gid) in enumerate(zip(p.get("legs") or [], p.get("game_ids") or [])):
                    hit = [f["key"] for f in by_game.get(gid, []) if leg.startswith(f["subject"] + " ")]
                    if hit:
                        out.append({"source": src, "size": size, "index": i, "leg": j, "flags": hit})
    return out


# ══════════════════════════════════════════════════════════════════════
# FREEZE, GRADE, RECORD
# ══════════════════════════════════════════════════════════════════════
def archives(lg, root=None):
    return sorted(glob.glob(os.path.join(_data(lg, root), "20*", "news-flags", "*.json.gz")))


def first_seen(lg, root=None):
    out = {}
    for p in archives(lg, root):
        d = _gz(p) or {}
        for f in d.get("flags") or []:
            out.setdefault(f["key"], d.get("taken_at"))
    return out


def freeze(lg, fl, root=None, now=None, log=log):
    now = now or _now()
    ahead = [f for f in fl if (f.get("commence") or "") > _iso(now)]
    if not ahead:
        return None
    fp = hashlib.sha256(json.dumps(sorted(f["key"] for f in ahead)).encode("utf-8")).hexdigest()
    a = archives(lg, root)
    if a and (_gz(a[-1]) or {}).get("fingerprint") == fp:
        return None
    p, wrote = daystore.archive({"league": lg, "taken_at": _iso(now), "fingerprint": fp, "flags": ahead},
                                _data(lg, root), "news-flags", log=log, when=now)
    return p if wrote else None


def frozen_player_flags(lg, root=None):
    """Every player flag frozen before its kickoff, once each."""
    out = {}
    for p in archives(lg, root):
        d = _gz(p) or {}
        for f in d.get("flags") or []:
            if f.get("kind") == "player" and d.get("taken_at", "") < (f.get("commence") or ""):
                out.setdefault(f["key"], dict(f, taken_at=d["taken_at"]))
    return list(out.values())


def stored_grades(lg, root=None):
    out = {}
    for p in sorted(glob.glob(os.path.join(_data(lg, root), "20*", "news-flags-grades", "*.json.gz"))):
        for g in (_gz(p) or {}).get("grades") or []:
            out.setdefault(g["key"], g)                # ⛔ the FIRST stored grade stands
    return out


def logs_through(logs):
    return max((g.get("d") or "" for players in logs.values() for p in players.values()
                for g in p.get("g") or []), default="")


def grade_new(lg, frozen, stored, root=None, now=None, log=log, logs=None):
    """Did the flagged player play? Once per flag, after the game.
    ⛔ No row for that game counts as 'did not play' only once the logs run
    past the game's date; before that it is left pending."""
    todo = [f for f in frozen if f["key"] not in stored]
    if not todo:
        return []
    logs = logs if logs is not None else M.load_logs(lg, root)
    idx, through = M.name_index(logs), logs_through(logs)
    new = []
    with M.league(lg):
        for f in todo:
            day = (f.get("commence") or "")[:10]
            if not day or through < day:
                continue
            pid = M.resolve(idx, f["subject"])
            if pid is None:
                continue
            _s, g = M.game_row(logs, pid, f["commence"])
            played = bool(g) and record_fb._played(g)[0]
            new.append({"key": f["key"], "played": played, "graded_at": _iso(now or _now())})
    if new:
        daystore.archive({"league": lg, "grades": new}, _data(lg, root), "news-flags-grades",
                         log=log, when=now)
    return new


def record(frozen, grades):
    """How often the flags were right. An absence flag (OUT, IR, ruled out…)
    is right when he did not play; a caution flag (questionable, limited,
    illness) has no right answer, so only how often he played is shown."""
    out = {}
    for cls, test in (("absence", lambda s: s in ABSENCE), ("caution", lambda s: s not in ABSENCE)):
        fs = [f for f in frozen if test(f["status"]) and f["key"] in grades]
        played = sum(1 for f in fs if grades[f["key"]]["played"])
        out[cls] = {"graded": len(fs), "played": played, "did_not_play": len(fs) - played,
                    "games": len({f["game_id"] for f in fs}),
                    "right_pct": (round(100.0 * (len(fs) - played) / len(fs), 1)
                                  if (fs and cls == "absence") else None),
                    "basis": "DESCRIPTIVE"}
    return out


def build(lg=None, root=None, now=None, log=log, logs=None):
    lg = (lg or LEAGUE).lower()
    now = now or _now()
    players, teams = board(lg, root)
    logs = logs if logs is not None else M.load_logs(lg, root)
    shared, idx = shared_names(lg, root, logs)
    resolve = D.team_codes(lg)
    week_of = (lambda c: signal9.week_of(lg, (c or "")[:10], root)) if lg == "nfl" else (lambda c: None)
    fl, rep = flags(lg, players, teams, headlines(lg, root, now), injury_rows(lg, root, now),
                    shared, idx, resolve, week_of)
    fs = first_seen(lg, root)
    for f in fl:
        f["first_seen"] = fs.get(f["key"]) or _iso(now)
    frz = freeze(lg, fl, root, now, log)
    grades = stored_grades(lg, root)
    for g in grade_new(lg, frozen_player_flags(lg, root), grades, root, now, log, logs):
        grades.setdefault(g["key"], g)
    doc = {"league": lg, "kind": "DESCRIPTIVE", "built_at": _iso(now),
           "sources": (["injury report (nflverse)", "headlines"] if lg == "nfl" else ["headlines"]),
           "college_note": COLLEGE_NOTE if lg == "ncaaf" else None,
           "status_words": list(STATUS_WORDS), "flags": sorted(fl, key=lambda f: (f["commence"] or "", f["subject"])),
           "parlay_legs": parlay_flags(lg, fl, root), "report": rep,
           "record": record(frozen_player_flags(lg, root), grades),
           "note": ("A flag is a note, never a lever: it removes, hides, re-ranks and re-prices "
                    "nothing and feeds no model. Names match on the exact full name.")}
    with open(os.path.join(_data(lg, root), "latest", "news-flags.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    log("news flags %s: %d flag(s) on %d player(s) / %d team(s); %d headline(s), %d injury row(s); "
        "%d shared-name hit(s) skipped; frozen %s" % (
            lg, len(fl), len(players), len(teams), rep["headlines"], rep["injury_rows"],
            rep["ambiguous_skipped"], frz or "unchanged"))
    return doc


def due(lg, root=None, now=None):
    """Once a day: is the flag file older than today's deadline?"""
    d = _json(os.path.join(_data(lg, root), "latest", "news-flags.json")) or {}
    last = freshness.last_due(freshness.FB_TIMES[lg]["flags"], now)
    return not d.get("built_at") or (last is not None and d["built_at"] < _iso(last))


if __name__ == "__main__":
    build()
    sys.exit(0)
