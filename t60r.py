#!/usr/bin/env python3
"""t60r.py — the played-games backtest, exactly as `research/t60r_spec.md`
was approved by Sam on 2026-09-22.

    python t60r.py lines     # pull CFBD closing lines (needs CFBD_API_KEY)
    python t60r.py grade     # build rows, grade them, write the report

🔴 THE RULE IS FROZEN. `[Sam, 2026-09-22]` Section 2 (which side each
signal votes for) and section 3 (the bar) are pinned by a hash in
`test_prereg_gate.py`. ⛔ Nothing in this file may soften either. A
threshold moved after seeing a result is a new test with a new id.

⛔ THE VERDICT IS THE COMBINED NUMBER (section 3a). 2025 alone and 2026
alone are reported BESIDE it and are never the verdict.

⚠️ A SIGNAL WITH NO POINT-IN-TIME DATA ABSTAINS, and the report says how
often. That is the dossier's own UNAVAILABLE rule: an absent signal is
never guessed, and it is never silently dropped either.

⛔ NO p-VALUE ON THE RAW ROW COUNT. `shadow_fb.cluster()` is the ONE
implementation of the clustered effective n and this file imports it
(rule 117) rather than carrying a second copy.
"""
import collections
import datetime
import glob
import gzip
import json
import os
import sys
import urllib.request

import shadow_fb

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "t60r")

# ── the approved bar, section 3 option B. ⛔ Do not edit. ──────────────
BAR_RATE = 0.574
BAR_P = 0.01
MIN_EFF_N = 1000
BREAK_EVEN = shadow_fb.BREAK_EVEN          # 110/210 = 52.38%

# ── the approved thresholds, section 2. ⛔ Do not edit. ────────────────
GAP_POINTS = 3.0        # §2 and §4 must be this far from the line to vote
SHARE_GAP = 0.04        # §6 clock-share gap
OUT_GAP = 2             # §7 players-out difference
VS_POS = ("QB", "RB", "WR", "TE")
PLAY_AT = 2             # |net votes| needed to play a side
H2H_DAYS = 365
SEASONS = (2025, 2026)


def log(m):
    print(m, flush=True)


def jz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════
# THE GAMES
# ══════════════════════════════════════════════════════════════════════
def schedule(lg, season):
    p = os.path.join(ROOT, "data", lg, "latest", "schedule-%d.json.gz" % season)
    return jz(p)["games"] if os.path.exists(p) else []


def kick(g):
    s = (g.get("start") or "")[:10]
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def eligible(lg, season):
    """Finished games we could grade. ⛔ FBS vs FBS only in college."""
    out = []
    for g in schedule(lg, season):
        if not g.get("final") or kick(g) is None:
            continue
        if g.get("home_score") is None or g.get("away_score") is None:
            continue
        if lg == "ncaaf" and not (g.get("home_class") == "fbs"
                                  and g.get("away_class") == "fbs"):
            continue
        out.append(g)
    return out


def history(lg):
    """Every final in every stored season, for H2H and trailing form."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", lg, "latest",
                                           "schedule-*.json.gz"))):
        for g in jz(p).get("games") or []:
            if g.get("final") and kick(g) and g.get("home_score") is not None:
                out.append(g)
    out.sort(key=kick)
    return out


# ══════════════════════════════════════════════════════════════════════
# THE PRICE — ⛔ ORIENTED BY THE MONEYLINE, NEVER BY A SIGN CONVENTION
# ══════════════════════════════════════════════════════════════════════
# 🔴 CLAUDE.md, `run_line`: "The moneyline is the authority: it is a
#    single unambiguous market and the favourite lays the runs." The same
#    reasoning holds here, and it is why this never assumes whether a
#    stored spread is the home team's or the away team's.
def market(g, cfb_lines=None):
    """Return (M, T, void_reason). M = home team's expected margin."""
    if cfb_lines is not None:
        row = cfb_lines.get(str(g.get("id")))
        spread, total = (row or {}).get("spread"), (row or {}).get("total")
        ml_h, ml_a = (row or {}).get("ml_home"), (row or {}).get("ml_away")
    else:
        spread, total = g.get("closing_spread"), g.get("closing_total")
        ml_h, ml_a = g.get("closing_ml_home"), g.get("closing_ml_away")
    if spread is None or total is None:
        return None, None, "no closing line stored"
    if ml_h is None or ml_a is None:
        return None, None, "no closing moneyline to orient the spread"
    if ml_h == ml_a or float(spread) == 0:
        # ⚠️ A PICK'EM HAS NO FAVOURITE, so there is nothing to check the
        #    sign against. Not a defect — it is simply not gradeable here.
        return None, None, "pick'em: no favourite to orient the spread"
    home_fav = float(ml_h) < float(ml_a)
    m_raw = float(spread)
    if (m_raw > 0) != home_fav:
        # ⛔ THE SPREAD AND THE MONEYLINE NAME DIFFERENT FAVOURITES.
        return None, None, "spread sign conflicts with the moneyline"
    return m_raw, float(total), None


# ══════════════════════════════════════════════════════════════════════
# THE EIGHT SIGNALS — section 2, verbatim
# ══════════════════════════════════════════════════════════════════════
def sgn(x, gap):
    return 1 if x >= gap else (-1 if x <= -gap else 0)


def s2_h2h(g, past):
    """Prior meetings inside 365 days, from THIS game's home side.

    ⛔ `past` IS ALREADY CUT AT KICKOFF BY `rows_for`, AND THAT CUT LIVES
    IN EXACTLY ONE PLACE. It used to be made here as well; two copies of
    a filter mean no single edit can break it, so `test_t60r.py` could
    declare a lookahead mutation that changed nothing and still passed —
    a guard that cannot fail (CLAUDE.md, rules 67/244/249).
    """
    k = kick(g)
    home, away = g.get("home"), g.get("away")
    met = [x for x in past
           if {x.get("home"), x.get("away")} == {home, away}
           and (k - kick(x)).days <= H2H_DAYS]
    if not met:
        return None, None
    margins, totals = [], []
    for x in met:
        hs, as_ = float(x["home_score"]), float(x["away_score"])
        margins.append(hs - as_ if x.get("home") == home else as_ - hs)
        totals.append(hs + as_)
    return (sum(margins) / len(margins)), (sum(totals) / len(totals))


def last4(team, k, past):
    # ⛔ `past` is already cut at kickoff by `rows_for`. One cut, one place.
    rows = [x for x in past
            if team in (x.get("home"), x.get("away"))][-4:]
    if len(rows) < 2:
        return None
    pf = pa = 0.0
    for x in rows:
        hs, as_ = float(x["home_score"]), float(x["away_score"])
        f, a = (hs, as_) if x.get("home") == team else (as_, hs)
        pf += f
        pa += a
    return pf / len(rows), pa / len(rows)


def s4_this_season(g, past):
    k = kick(g)
    h, a = last4(g.get("home"), k, past), last4(g.get("away"), k, past)
    if not h or not a:
        return None, None
    return ((h[0] - h[1]) - (a[0] - a[1])) / 2.0, (h[0] + h[1] + a[0] + a[1]) / 2.0


class Allowed:
    """§5, REBUILT PER GAME — yards each defence has allowed by position,
    counting only games that had already been played.

    ⛔ The stored `allowed-by-position-<season>.json.gz` is a WHOLE-SEASON
    aggregate. Using it on a game inside that season would be lookahead —
    the exact defect the spec's filter list names. So this accumulates
    the player logs date by date instead.
    """

    def __init__(self, lg):
        self.rows = collections.defaultdict(list)   # date -> [(def, pos, yds)]
        self.positions = set()
        for p in sorted(glob.glob(os.path.join(ROOT, "data", lg, "latest",
                                               "players-*.json.gz"))):
            j = jz(p)
            for _pid, v in (j.get("players") or {}).items():
                for r in (v.get("g") or []):
                    pos = (r.get("pos") or v.get("pos") or "").upper()
                    opp, d = r.get("o"), (r.get("d") or "")[:10]
                    if pos not in VS_POS or not opp or not d:
                        continue
                    yds = sum(float(r.get(k) or 0) for k in
                              ("rec_yds", "rush_yds", "pass_yds"))
                    self.rows[d].append((opp, pos, yds))
                    self.positions.add(pos)
        self.dates = sorted(self.rows)
        self._at = None
        self._tot = collections.defaultdict(lambda: collections.defaultdict(float))
        self._i = 0

    def upto(self, k):
        """Totals as of the day before `k`. ⛔ Forward-only, never rewound."""
        cut = k.strftime("%Y-%m-%d")
        while self._i < len(self.dates) and self.dates[self._i] < cut:
            for team, pos, yds in self.rows[self.dates[self._i]]:
                self._tot[team][pos] += yds
            self._i += 1
        return self._tot

    def fraction(self, g):
        """Mean rank-fraction over both defences x 4 positions, or None.

        rank 1 = ALLOWS THE MOST, so a SMALL fraction means both defences
        have been scored on heavily -> over.
        """
        tot = self.upto(kick(g))
        if len(self.positions) < len(VS_POS):
            return None                      # a position this league never logs
        fracs = []
        for team in (g.get("home"), g.get("away")):
            for pos in VS_POS:
                league = sorted((v.get(pos, 0.0) for v in tot.values()),
                                reverse=True)
                if len(league) < 10 or team not in tot or pos not in tot[team]:
                    return None
                mine = tot[team][pos]
                rank = sum(1 for x in league if x > mine) + 1
                fracs.append(rank / float(len(league)))
        return sum(fracs) / len(fracs)


class Personnel:
    """§7 — players flagged out, as of the week BEFORE the game."""

    def __init__(self, lg):
        self.have = False
        self.out = collections.defaultdict(int)     # (season, week, team) -> n
        for p in sorted(glob.glob(os.path.join(ROOT, "data", lg, "latest",
                                               "players-*.json.gz"))):
            j = jz(p)
            season = j.get("season")
            for _pid, v in (j.get("players") or {}).items():
                for r in (v.get("g") or []):
                    if r.get("inj") is None:
                        continue
                    self.have = True
                    if float(r.get("inj") or 0) > 0:
                        self.out[(season, r.get("week"), r.get("team"))] += 1

    def vote(self, g, season):
        if not self.have or not g.get("week"):
            return 0
        wk = int(g["week"]) - 1
        if wk < 1:
            return 0
        h = self.out.get((season, wk, g.get("home")), 0)
        a = self.out.get((season, wk, g.get("away")), 0)
        return sgn(a - h, OUT_GAP)      # more of THEIR players out -> us


def votes(g, season, m, t, past, allowed, personnel):
    """Section 2's table, in order. Returns (spread_votes, total_votes)."""
    sp, to = {}, {}
    sp["1_market"] = to["1_market"] = 0
    h2h_m, h2h_t = s2_h2h(g, past)
    sp["2_h2h"] = sgn(h2h_m - m, GAP_POINTS) if h2h_m is not None else 0
    to["2_h2h"] = sgn(h2h_t - t, GAP_POINTS) if h2h_t is not None else 0
    sp["3_time_of_year"] = to["3_time_of_year"] = 0
    s4_m, s4_t = s4_this_season(g, past)
    sp["4_this_season"] = sgn(s4_m - m, GAP_POINTS) if s4_m is not None else 0
    to["4_this_season"] = sgn(s4_t - t, GAP_POINTS) if s4_t is not None else 0
    sp["5_vs_position"] = 0
    f = allowed.fraction(g)
    to["5_vs_position"] = 0 if f is None else (1 if f <= 1 / 3.0
                                               else (-1 if f >= 2 / 3.0 else 0))
    # §6 possession: ⛔ NO POINT-IN-TIME SOURCE. `top-<season>.json.gz` is a
    #    season-to-date aggregate per team, not per game, so using it inside
    #    its own season is lookahead. It abstains and the report says so.
    sp["6_possession"] = to["6_possession"] = 0
    sp["7_personnel"] = personnel.vote(g, season)
    to["7_personnel"] = 0
    sp["8_venue"] = to["8_venue"] = 0
    return sp, to


# ══════════════════════════════════════════════════════════════════════
# GRADING
# ══════════════════════════════════════════════════════════════════════
def rows_for(lg, cfb_lines=None):
    """Returns (played rows, skip reasons, votes cast over EVERY candidate).

    ⚠️ THE THIRD ONE MATTERS: counting a signal's votes only on the rows
    that were PLAYED answers a different question — it cannot show a
    signal that votes often and is always outvoted, or one that never
    votes at all.
    """
    out, skipped = [], collections.Counter()
    cast = collections.Counter()
    candidates = collections.Counter()
    past_all = history(lg)
    allowed, personnel = Allowed(lg), Personnel(lg)
    for season in SEASONS:
        games = sorted(eligible(lg, season), key=kick)
        for g in games:
            m, t, why = market(g, cfb_lines if lg == "ncaaf" else None)
            if why:
                skipped[why] += 1
                continue
            k = kick(g)
            past = [x for x in past_all if kick(x) < k]
            sp, to = votes(g, season, m, t, past, allowed, personnel)
            margin = float(g["home_score"]) - float(g["away_score"])
            points = float(g["home_score"]) + float(g["away_score"])
            for mk, v, res, line in (("spread", sp, margin, m),
                                     ("total", to, points, t)):
                candidates[mk] += 1
                for sig, val in v.items():
                    if val:
                        cast["%s|%s" % (mk, sig)] += 1
                net = sum(v.values())
                if abs(net) < PLAY_AT:
                    skipped["no side (net %d)" % net] += 1
                    continue
                side = 1 if net > 0 else -1
                diff = res - line
                if diff == 0:
                    skipped["push"] += 1
                    continue
                out.append({
                    "league": lg, "season": season, "game_id": str(g.get("id")),
                    "date": (g.get("start") or "")[:10], "market": mk,
                    "home": g.get("home"), "away": g.get("away"),
                    "line": line, "result": res, "net_votes": net,
                    "side": ("home" if side > 0 else "away") if mk == "spread"
                            else ("over" if side > 0 else "under"),
                    "votes": v,
                    "won": (diff > 0) == (side > 0),
                    "state": "graded"})
    return out, skipped, {"votes_cast": dict(cast),
                          "candidate_rows": dict(candidates)}


def verdict(rows):
    """⛔ The approved bar, applied to whatever rows are handed in."""
    c = shadow_fb.cluster(rows, key="game_id")
    p = shadow_fb.one_sided_p(c["eff_wins"], c["eff_n"], BREAK_EVEN)
    out = {**c, "p_value": p, "bar_rate": BAR_RATE, "bar_p": BAR_P,
           "min_eff_n": MIN_EFF_N, "p_value_on_raw_n": None,
           "p_basis": ("one-sided exact binomial against break-even "
                       "(%.2f%% at -110), on the CLUSTERED effective n"
                       % (100 * BREAK_EVEN))}
    if c["eff_n"] < MIN_EFF_N:
        out["verdict"] = "NOT YET MEASURABLE"
        out["why"] = ("%s effective row(s) against the pre-registered "
                      "minimum of %d. Not a pass and not a fail."
                      % (c["eff_n"], MIN_EFF_N))
        return out
    ok = (c["rate"] is not None and c["rate"] >= BAR_RATE
          and p is not None and p < BAR_P)
    out["verdict"] = "PASS" if ok else "FAIL"
    out["why"] = ("%.1f%% over %s effective row(s), one-sided p=%s against "
                  "the %.1f%% bar." % (100 * c["rate"], c["eff_n"],
                                       ("%.4g" % p) if p is not None else "n/a",
                                       100 * BAR_RATE))
    return out


def grade():
    cfb = None
    p = os.path.join(OUT, "cfbd-lines.json.gz")
    if os.path.exists(p):
        cfb = jz(p).get("games") or {}
    rows, skipped, participation = [], collections.Counter(), {}
    for lg in ("nfl", "ncaaf"):
        if lg == "ncaaf" and cfb is None:
            log("⚠️ ncaaf: no data/t60r/cfbd-lines.json.gz — run `t60r.py "
                "lines` where CFBD_API_KEY is set. College is NOT graded.")
            continue
        r, s, cast = rows_for(lg, cfb)
        rows += r
        participation[lg] = cast
        for k, v in s.items():
            skipped["%s: %s" % (lg, k)] += v
        log("%s: %d row(s) played out of %d candidate(s)"
            % (lg, len(r), sum(cast["candidate_rows"].values())))

    # ⛔ SECTION 3a: three numbers, and the VERDICT IS THE COMBINED ONE.
    rep = {"spec": "research/t60r_spec.md",
           "bar": "option B: >= %.1f%%, one-sided p < %.2f, effective n >= %d"
                  % (100 * BAR_RATE, BAR_P, MIN_EFF_N),
           "built_at": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
           "combined": verdict(rows),
           "by_season": {str(s): verdict([r for r in rows if r["season"] == s])
                         for s in SEASONS},
           "by_league": {lg: verdict([r for r in rows if r["league"] == lg])
                         for lg in ("nfl", "ncaaf")},
           "verdict_is": ("the COMBINED number only. The per-season pair is "
                          "reported beside it so the offseason can be seen, "
                          "and is never the verdict (spec 3a)."),
           "signal_participation": signal_report(rows),
           "votes_over_every_candidate": participation,
           "not_played": dict(skipped.most_common()),
           "rows": rows}
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, "report.json.gz"), "wt",
                   encoding="utf-8") as f:
        json.dump(rep, f)
    render(rep)
    return rep


def signal_report(rows):
    """How often each signal actually voted. ⚠️ A signal that never votes
    is not evidence about that signal — it is a data gap, and it is said."""
    out = {}
    for key in ("1_market", "2_h2h", "3_time_of_year", "4_this_season",
                "5_vs_position", "6_possession", "7_personnel", "8_venue"):
        voted = sum(1 for r in rows if r["votes"].get(key))
        out[key] = {"voted": voted,
                    "share": round(voted / len(rows), 4) if rows else None}
    return out


def render(rep):
    log("")
    log("══ T60R — %s" % rep["bar"])
    for name in ("2025", "2026"):
        v = rep["by_season"][name]
        log("   %s: %s — %s" % (name, v["verdict"], v["why"]))
    for lg in ("nfl", "ncaaf"):
        v = rep["by_league"][lg]
        log("   %-6s %s — %s" % (lg, v["verdict"], v["why"]))
    c = rep["combined"]
    log("🔴 COMBINED (this is the verdict): %s — %s" % (c["verdict"], c["why"]))
    log("   effective n %s over %s raw row(s) in %s game(s); basis: %s"
        % (c["eff_n"], c["n"], c["games"], c.get("eff_basis")))
    log("   signals that voted: %s"
        % ", ".join("%s %d" % (k, v["voted"])
                    for k, v in rep["signal_participation"].items() if v["voted"]))
    log("   not played: %s" % json.dumps(rep["not_played"]))


# ══════════════════════════════════════════════════════════════════════
# CFBD CLOSING LINES — the only network call in this file
# ══════════════════════════════════════════════════════════════════════
def lines():
    key = os.environ.get("CFBD_API_KEY", "").strip()
    if not key:
        log("FATAL: CFBD_API_KEY is not set. This runs in CI, where the "
            "repo secret exists.")
        return 1
    games, providers = {}, collections.Counter()
    calls = 0
    for season in SEASONS:
        url = ("https://api.collegefootballdata.com/lines?year=%d&"
               "seasonType=regular" % season)
        req = urllib.request.Request(
            url, headers={"Authorization": "Bearer %s" % key,
                          "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.load(r)
        calls += 1
        for g in data:
            for ln in (g.get("lines") or []):
                providers[ln.get("provider")] += 1
        for g in data:
            best = None
            for ln in (g.get("lines") or []):
                if ln.get("spread") is None or ln.get("overUnder") is None:
                    continue
                # ⛔ PROVIDER ORDER IS FIXED HERE, FROM THE LIST THE CALL
                #    RETURNS, and never re-picked per game to taste.
                rank = PROVIDER_ORDER.index(ln.get("provider")) \
                    if ln.get("provider") in PROVIDER_ORDER else len(PROVIDER_ORDER)
                if best is None or rank < best[0]:
                    best = (rank, ln)
            if best is None:
                continue
            ln = best[1]
            games[str(g.get("id"))] = {
                # CFBD's `spread` is the HOME team's handicap (negative when
                # home is favoured). ⛔ The sign is never trusted on its own:
                # `market()` re-orients every row against the moneyline.
                "spread": -float(ln["spread"]),
                "total": float(ln["overUnder"]),
                "ml_home": ln.get("homeMoneyline"),
                "ml_away": ln.get("awayMoneyline"),
                "provider": ln.get("provider"), "season": season}
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(OUT, "cfbd-lines.json.gz"), "wt",
                   encoding="utf-8") as f:
        json.dump({"games": games, "calls": calls,
                   "providers_seen": dict(providers.most_common()),
                   "provider_order": list(PROVIDER_ORDER),
                   "built_at": datetime.datetime.now(datetime.timezone.utc)
                               .strftime("%Y-%m-%dT%H:%M:%SZ")}, f)
    log("cfbd lines: %d game(s) from %d call(s); providers %s"
        % (len(games), calls, dict(providers.most_common())))
    return 0


# ⛔ FIXED BEFORE ANY GRADING, from CFBD's own documented provider names.
PROVIDER_ORDER = ("consensus", "DraftKings", "Bovada", "ESPN Bet",
                  "teamrankings", "numberfire")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "grade"
    if mode == "lines":
        return lines()
    if mode == "grade":
        grade()
        return 0
    log("usage: t60r.py [lines|grade]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
