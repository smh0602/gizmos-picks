# CFBD `/coaches` — PROBE REPORT

**One call, 2026-09-18T03:45:32Z, `year=2026`.** Run
[35303621911](https://github.com/smh0602/gizmos-picks/actions/runs/35303621911),
artifact `data/ncaaf/latest/coaches-probe.json`.

⛔ **NOTHING IS ADOPTED.** §7 still publishes *"COACHING CHANGES HAVE NO
SOURCE IN THIS STACK"*, nothing reads the artifact, and no NFL side was
attempted — nflverse has no coaching table and inventing one is worse
than the declared gap.

---

## The five questions, answered off the response

| | |
|---|---|
| **Does it exist?** | ✅ **Yes.** HTTP 200, a list of **138** rows. |
| **What columns does it really return?** | 5 top level, 15 nested — listed below. |
| **Is there a start year?** | ✅ **Yes — `hireDate`.** ⚠️ **The probe's own verdict line says NOT COMPUTABLE and that line is WRONG.** See below. |
| **Does it cover FBS?** | ✅ **138 of 138**, zero missing, zero extra. |
| **What did it cost?** | **1 call.** CFBD returned `X-CallLimit-Remaining: 2374`. |

### Columns, counted across all 138 rows

⛔ Not `rows[0].keys()` — a feed that omits a null field would make the
schema a property of whoever sorted first. Every count below is 138/138,
so no column is ragged.

```
top level   firstName  lastName  id  hireDate  seasons
seasons[]   school  teamId  conference  year  games  wins  losses  ties
            winPercentage  srs  spOverall  spOffense  spDefense
            preseasonRank  postseasonRank
```

One real row, verbatim from the artifact:

```json
{"firstName": "Scott", "lastName": "Abell", "id": 1826,
 "hireDate": "2024-11-26T00:00:00.000Z",
 "seasons": [{"school": "Rice", "conference": "American Athletic",
              "year": 2026, "games": 0, "wins": 0, "losses": 0,
              "spOverall": -15.1, "spOffense": 16.7, "spDefense": 32.2}]}
```

---

## 🔴 THE PROBE GOT ITS OWN THIRD QUESTION WRONG, AND THAT IS THE FINDING

The artifact's `verdict` reads:

> `"New this season" is NOT COMPUTABLE from this response.`

**It is computable.** The response carries **`hireDate` on all 138 rows**.

What happened: the probe's candidate list was **year-SHAPED only**
(`year`, `season`, `startYear`, `hireYear`, …). It found `seasons[].year`,
correctly observed that it is **pinned to 2026 on every row** — because
`?year=2026` filters to that season, so the column answers nothing about
tenure — and concluded there was no usable start year. The answer was in
the next column, in a format the list could not see.

⛔ **That is a fact about MY CANDIDATE LIST published as a fact about the
feed.** It is the same error this repo has made five times in the other
direction, and it is why `CLAUDE.md` says an absence in a response is
evidence about the request.

✅ **Fixed**: `_DATE_KEYS` and an ISO-year parser now run beside the
year-shaped list, and `per_date_key` reports the spread of hire years and
how many coaches were hired **in the season asked for** — which is
literally the "new this season" count. Guarded by
`test_coaches_probe.py` §8, driven against the measured row shape above.

⚠️ **WHAT IS STILL UNMEASURED, AND IT IS NOT GUESSED AT.** The corrected
code has been driven against the stored row shape, **not against all 138
live rows** — that would be a second call and the work order allows one.
So this report states that `hireDate` EXISTS and VARIES (2024 on Rice,
against a 2026 season), and does **not** state how many of the 138 are
new this year. ⛔ That number needs one more credit and is nobody's to
invent.

---

## FBS coverage — 138 of 138

Measured against `data/ncaaf/latest/teams.json` (138 schools, `CFBD
/teams/fbs`, built 2026-09-17), **which was already on disk**. ⛔ Asking
`/teams/fbs` again to check coverage would have been a second credit for
a set this repo re-fetches weekly and stores.

```
fbs_reference_n   138        fbs_matched      138
fbs_missing       []         not_in_fbs       0
```

⚠️ Matched on the **exact** school string, and it came out clean — so the
usual "is a miss a gap or a spelling difference" caveat did not have to
be exercised. ⚠️ The schools live at `seasons[].school`, **not** at the
top level; `school_keys_found` is `[]` for exactly that reason and the
138 came from walking one level down.

📌 One row per school, 138 rows for 138 schools, is consistent with
**one head coach per FBS school and no coordinators**. ⛔ Whether CFBD
holds coordinators anywhere is NOT answered here — this probe asked
`/coaches` and nothing else.

---

## 💰 Cost, and a header nobody in this repo had read

```
calls_made                  1
X-CallLimit-Remaining    2374        ← CFBD's own header, on this response
```

🔴 **CFBD DOES send a quota header, and this is the first time one is
recorded in the repo.** `cfb.py` has kept quota-shaped headers since
2026-09-09 while noting it did not know whether CFBD sends any. **It
does.**

⚠️ **AND THE NUMBER DOES NOT FIT THE PLAN THIS REPO ASSUMES.**
`cfbd_budget.py` prices against `PLAN=1000` (the free tier) and warns at
**91%**. A remaining allowance of **2,374** cannot come from a 1,000-call
plan. ⛔ **That is an observation about one header, not a conclusion about
the account** — the header could be a rolling window, a per-day figure, or
a different meter entirely. ✅ It is worth one look at the CFBD account
page, which costs nothing.

### The Academic tier — the cheapest item on the plan, and un-actioned

`python cfbd_budget.py`, this branch, unchanged by this PR:

```
  mode          calls/build  builds/wk   calls/wk
  cfb-probe              15          8        120
  cfb-teams               1          1          1
  fb-scores               2         44         88
                                              209  = 906/month

  Free                 1000/mo      91%  ⚠️
  Academic (.edu)      3000/mo      30%  ✅
  Tier 1 ($1/mo)       5000/mo      18%  ✅
  Tier 2 ($5/mo)      30000/mo       3%  ✅
```

📌 **The free Academic tier takes the quota from 91% to 30%.** It needs a
`.edu` address and costs nothing. CFBD answered **429 on every endpoint
for four days** in September and froze the Trends tab and the stored
schedule; 91% is the headroom that produced that. ⛔ Sam's to action.

⚠️ Those tier sizes are **quoted from CFBD's pricing page**, not derived —
`cfbd_budget.py` says so itself. The 906 is the derived half.

---

## What this probe cost the schedule: nothing

`coaches-probe` has **no cron arm**. It is dispatched by hand, so
`cfbd_budget.py` prices it at **zero a month**, which is the true answer
for a mode nothing schedules. `CRON TOTAL` is unmoved and no workflow
file was touched.
