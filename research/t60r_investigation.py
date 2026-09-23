#!/usr/bin/env python3
"""research/t60r_investigation.py — the numbers behind t60r_investigation.md.

    python research/t60r_investigation.py

⛔ READ-ONLY. It imports `t60r` and calls its own functions; it changes
nothing in the rule, the thresholds or the bar, and it writes nothing.
⛔ IT COMPUTES NO HIT RATE. Every number here is about which signals
COULD vote and how many rows qualify — never about whether they won.
The one outcome figure in the doc (47.3%) is read from the committed
report, not recomputed.
"""
import collections
import datetime
import gzip
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import t60r  # noqa: E402

SIGS = ("2_h2h", "4_this_season", "5_vs_position", "7_personnel")


def week(d):
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


def main():
    cfb = t60r.jz(os.path.join(ROOT, "data", "t60r", "cfbd-lines.json.gz"))["games"]
    out = {}
    for lg in ("nfl", "ncaaf"):
        past_all = t60r.history(lg)
        allowed, personnel = t60r.Allowed(lg), t60r.Personnel(lg)
        seasons_in_history = sorted({t60r.kick(g).year if t60r.kick(g).month > 6
                                     else t60r.kick(g).year - 1 for g in past_all})
        per = collections.defaultdict(lambda: collections.Counter())
        for season in t60r.SEASONS:
            for g in sorted(t60r.eligible(lg, season), key=t60r.kick):
                m, t, why = t60r.market(g, cfb if lg == "ncaaf" else None)
                if why:
                    continue
                k = t60r.kick(g)
                past = [x for x in past_all if t60r.kick(x) < k]
                sp, to = t60r.votes(g, season, m, t, past, allowed, personnel)
                key = (lg, season, week(k.date()))
                c = per[key]
                c["games"] += 1
                c["no_h2h_history"] += t60r.s2_h2h(g, past)[0] is None
                c["no_last4"] += t60r.s4_this_season(g, past)[0] is None
                for mk, v in (("spread", sp), ("total", to)):
                    net = sum(v.values())
                    c["%s_candidates" % mk] += 1
                    c["%s_played" % mk] += abs(net) >= t60r.PLAY_AT
                    c["%s_net_pm1" % mk] += abs(net) == 1
                    for s in SIGS:
                        c["%s_%s" % (mk, s)] += bool(v.get(s))
        out[lg] = {"history_seasons": seasons_in_history,
                   "by_week": {"%s|%s|%s" % k: dict(v) for k, v in sorted(per.items())}}
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
