#!/usr/bin/env python3
"""
🔴 ONE RANKING RULE, AND BOTH LEAGUES READ IT FROM HERE.

`[measured 2026-09-11 against the live tables]` **5,613 of the college
board's 6,116 published ranks broke a tie ARBITRARILY** — 92% — and the
offense side was 91%. The code was a bare ordinal:

    for i, (o, _) in enumerate(rows):
        tbl[o][pos][f + "_rank"] = i + 1

**Equal numbers came out of `sorted()` in whatever order the dict
happened to yield them, and each was handed a different rank.**

⛔ **THE WORST CASES ARE NOT EDGE CASES. They are whole columns:**

    RB  interceptions allowed   142 defences ALL at 0.0  ->  ranked 1-142
    WR  passing TDs allowed     142 defences ALL at 0.0  ->  ranked 1-142
    TE  rushing TDs allowed     130 defences ALL at 0.0  ->  ranked 1-130

**One team was told it was best in the country and another worst at a
statistic where they are identical.** ⚠️ And it was not confined to the
junk columns — **QB rushing yards had 93 rows tied-but-differently-ranked,
RB rushing yards 53, WR receiving yards 50.** Those are columns a reader
actually reads.

✅ **THE VALUES WERE NEVER WRONG.** All **6,116** stat cells reproduce the
player log exactly, across all eleven stats. **This module changes ranks
and percentiles ONLY** — no stat value moves.

---

## THE TWO RULES

**1. TIES SHARE THE BEST RANK.** `[100, 90, 90, 80] -> 1, 2, 2, 4`
(standard competition ranking). ⛔ Not `1, 2, 3, 4`, which is the bug, and
not `1, 2, 2, 3` ("dense"), which would misreport how many teams are
genuinely ahead of you.

**2. A COLUMN WHERE EVERY VALUE IS IDENTICAL PUBLISHES NO RANK AT ALL.**
Not rank 1, not rank N, not a shared rank — **nothing**, so the page can
render a dash.

🔴 **RULE 2 IS DERIVED FROM THE DATA, NOT FROM FOOTBALL KNOWLEDGE.** The
obvious alternative was a hard-coded list of impossible combinations —
running backs do not throw, wide receivers do not intercept. ⛔ **That
list would be a second source of truth about the sport, it would be wrong
the first time a running back throws a touchdown, and it would not catch
a column that goes degenerate for a reason nobody predicted.** *"Every
value is the same, so there is nothing to rank"* needs no such list and
catches all of it.

⚠️ **A MOSTLY-ZERO COLUMN IS NOT DEGENERATE AND STILL RANKS.** RB carries
allowed is 99% zeros, and under rule 1 those 140 defences now share one
rank — which is the honest answer, because they are genuinely tied.

---

⛔ **WHAT THIS MODULE DOES NOT DO.** It does not decide WHICH rows are
eligible (that is the `min_games` floor, which stays with the caller), it
does not sort the page, and it never touches a stat value.
"""


def competition_ranks(pairs):
    """Rank `[(key, value), ...]`, highest value = rank 1, ties shared.

    Returns ``{key: (rank, pct)}`` — and **an EMPTY dict when every value
    is identical**, because a column with no spread has nothing to rank.

    ``pct`` is the share of the field at or below you, so **100 = the
    most** — matching the `rank_note` both builders already publish
    (*"rank 1 = ALLOWS THE MOST; pct 100 = softest"*). ⛔ Ties get the
    SAME pct as well as the same rank; a shared rank beside two different
    percentiles would just move the contradiction somewhere quieter.
    """
    rows = [(k, v) for k, v in pairs if v is not None]
    if not rows:
        return {}

    # 🔴 RULE 2 — NOTHING TO RANK. Checked BEFORE sorting, so the answer
    #    cannot depend on iteration order (which is what produced the bug
    #    this module exists to fix).
    first = rows[0][1]
    if all(v == first for _, v in rows):
        return {}

    n = len(rows)
    rows.sort(key=lambda kv: -kv[1])

    out = {}
    i = 0
    while i < n:
        # every row sharing this value forms one tie group
        j = i
        while j + 1 < n and rows[j + 1][1] == rows[i][1]:
            j += 1
        rank = i + 1                      # competition: the BEST position
        # ⚠️ pct is computed from the END of the group, so a tied block
        #    reports the share of the field it is genuinely at-or-above.
        pct = round(100.0 * (n - j) / n, 1)
        for k, _ in rows[i:j + 1]:
            out[k] = (rank, pct)
        i = j + 1
    return out


def apply_ranks(tbl, positions, fields, eligible):
    """Write `<field>_rank` / `<field>_pct` into a by-position table.

    `tbl` is ``{team: {pos: {field: value, ...}}}``; `eligible(cell)`
    decides which rows may be ranked at all — the caller owns that,
    because the games floor is the caller's rule.

    ⛔ **A FIELD THAT EARNS NO RANK HAS ITS KEYS REMOVED, NOT SET TO
    None.** A stale `_rank` left behind from an earlier build would be
    read by the page as a real rank; absence is the only unambiguous way
    to say *"this cannot be ranked"*. Returns the number of
    (position, field) columns that published nothing.
    """
    blank = 0
    for pos in positions:
        for f in fields:
            pairs = [(t, cell[pos][f]) for t, cell in tbl.items()
                     if pos in cell and f in cell[pos]
                     and eligible(cell[pos])]
            ranked = competition_ranks(pairs)
            if not ranked:
                blank += 1
            for t, cell in tbl.items():
                if pos not in cell:
                    continue
                got = ranked.get(t)
                if got is None:
                    cell[pos].pop(f + "_rank", None)
                    cell[pos].pop(f + "_pct", None)
                else:
                    cell[pos][f + "_rank"], cell[pos][f + "_pct"] = got
    return blank
