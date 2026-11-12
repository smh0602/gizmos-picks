#!/usr/bin/env python3
"""
THE WATCHER FOR THE QUOTA THAT HAS ALREADY RUN OUT ONCE.

🔴🔴 `[2026-09-09]` CFBD answered **429 on every endpoint for five days**
and the college Trends table froze. `cfbd_budget.py` was written after
that, is correct, and **no workflow has ever run it.**

⛔ SO THE FIRST QUESTION IS NOT "does the watcher work" — IT IS "IS THIS
A SECOND COPY OF `budget.py`". Sam asked it before this was built, and it
is asserted here rather than argued in a commit message, because a
duplicated fact is rule 66 and the right answer would have been to fold
it in rather than run two.
"""
import os
import re
import stat
import subprocess
import sys
import tempfile

from tcheck import ck, note, section

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfbd_watch as W  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
WF_DIR = os.path.join(ROOT, ".github/workflows")


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


SRC = read(os.path.join(ROOT, "cfbd_watch.py"))
WF = read(os.path.join(WF_DIR, "cfbd.yml"))
BUDGET = read(os.path.join(ROOT, "budget.py"))
CFBD = read(os.path.join(ROOT, "cfbd_budget.py"))


def live(text):
    return "\n".join(l for l in text.splitlines()
                     if not l.lstrip().startswith("#"))


section("1. ⛔ IS THIS A SECOND COPY OF budget.py? MEASURED, NOT ARGUED")
# 🔴 IF THESE TWO PRICED THE SAME CREDITS, A SECOND WATCHER WOULD BE A
#    SECOND COPY OF ONE FACT AND THIS WHOLE FILE WOULD BE THE WRONG
#    ANSWER. So the disjointness is a CHECK, not a claim in a PR body.
ck("🔴🔴 the workflow that runs the CFBD budget EXISTS",
   bool(WF),
   "⛔ THE DEFECT, AT ITS PLAINEST: no .github/workflows/cfbd.yml, so "
   "nothing is scheduled to ask whether the quota will run out")
_odds_plan = re.search(r"^PLAN, RESERVE, GAMES = (\d+)", BUDGET, re.M)
_cfbd_plan = re.search(r'CFBD_PLAN", "(\d+)"', CFBD)
ck("⛔ they price DIFFERENT quotas, from different env vars",
   _odds_plan and _cfbd_plan
   and _odds_plan.group(1) != _cfbd_plan.group(1),
   "🔴 one plan would mean one fact. Odds=%s (ODDS_MONTHLY_PLAN) vs "
   "CFBD=%s (CFBD_PLAN)"
   % (_odds_plan and _odds_plan.group(1), _cfbd_plan and _cfbd_plan.group(1)))
ck("⛔ ...and neither tool mentions the other's API at all",
   "CFBD" not in BUDGET and "cfbd" not in BUDGET
   and "ODDS" not in CFBD and "credits_used" not in CFBD,
   "🔴 if either read the other's numbers they would be one tool wearing "
   "two names")
# 🔴🔴 THE CLINCHER, DRIVEN AGAINST THE REAL budget.py OUTPUT: every mode
#    this prices is one budget.py reports as FREE. "Free" there means free
#    in ODDS credits — and those same modes cost 906 CFBD calls a month.
_b = subprocess.run([sys.executable, "budget.py"], cwd=ROOT,
                    capture_output=True, text=True, timeout=300)
_free = set()
if "free modes" in _b.stdout:
    _free = set(_b.stdout.split("free modes (statsapi or local compute): "
                                )[1].split("\n")[0].split(", "))
_rc, _out, _err = W.run_cfbd()
_parsed = W.parse(_out)
_cfbd_modes = {m["mode"] for m in _parsed.get("modes", [])}
ck("⚠️ budget.py's free list is readable at all",
   bool(_free),
   "⛔ a check over an empty set passes and proves nothing (rule 67). "
   "budget.py rc=%d" % _b.returncode)
ck("🔴🔴 EVERY mode this prices is one budget.py reports as FREE",
   bool(_cfbd_modes) and _cfbd_modes <= _free,
   "⛔ THIS IS THE DISJOINTNESS PROOF. If a mode appeared in BOTH tools' "
   "PAID sets, the two would be counting one spend twice and this "
   "watcher would be the wrong answer. cfbd prices %s; budget.py's free "
   "list is %s" % (sorted(_cfbd_modes), sorted(_free)))
note("⛔ WHAT THAT DOES *NOT* MEAN: that these modes are free. They cost "
     "%s CFBD calls a month against a %s plan — free in ODDS credits and "
     "expensive in CFBD calls, which is exactly why one tool cannot see "
     "what the other does."
     % (_parsed.get("month"), _parsed.get("plan")))

section("2. 🔴 THE PARSER, DRIVEN AGAINST THE REAL cfbd_budget.py")
ck("⚠️ cfbd_budget.py runs at all from here",
   _rc is not None,
   "⛔ rc=%s err=%s" % (_rc, (_err or "")[-300:]))
ck("🔴🔴 the parser reads the REAL cfbd_budget.py output",
   _parsed.get("state") == "READ",
   "⛔ THIS IS THE FORMAT-DRIFT ALARM. cfbd_budget.py's output moved and "
   "this parser did not: %s" % _parsed.get("why"))
ck("✅ ...and the figures agree with each other",
   _parsed.get("state") == "READ"
   and abs(100.0 * _parsed["month"] / _parsed["plan"] - _parsed["pct"]) < 1.0
   and sum(m["calls_wk"] for m in _parsed["modes"]) > 0,
   "🔴 the cross-check is what makes a prose parser safe. Got %s"
   % {k: v for k, v in _parsed.items() if k != "modes"})
# ⛔ cfbd_budget.py EXITS 1 WHEN IT IS OVER PLAN. That is a VERDICT, not a
#    crash, and treating it as "could not look" would silence the very
#    finding this watcher exists for.
ck("🔴 an over-plan exit from cfbd_budget.py is a VERDICT, not a failure",
   "rc is None" in SRC and "not a crash" in SRC,
   "⛔ if rc=1 were read as unreadable, the watcher would go quiet at "
   "exactly the moment the quota is blowing")
note("live CFBD figure: %s calls/month against a %s plan — %.0f%%"
     % (_parsed.get("month"), _parsed.get("plan"), _parsed.get("pct", 0)))

section("3. 🔴🔴 THE ALARM, DRIVEN BOTH WAYS")


def mline(used_pct=40, plan=1000, pace=None):
    """`[2026-11-11]` cfbd_budget.py's `measured pace:` line, for a period
    that will have used `used_pct` of `plan` by the reset. ⚠️ Printed by the
    SAME formatter the tool uses (`pace_line`), so the parser is driven
    against the real line, never a copy of its shape."""
    import datetime as _dt
    import cfbd_budget as _B
    at_reset = plan - used_pct * plan / 100.0
    pace = pace if pace is not None else plan / 30.0
    return _B.pace_line({
        "state": "READ", "pace": pace, "left": int(at_reset + pace * 10),
        "at": _dt.datetime(2026, 11, 21, 16, 33, tzinfo=_dt.timezone.utc),
        "at_reset": at_reset,
        "reset": _dt.datetime(2026, 12, 1, tzinfo=_dt.timezone.utc),
        "pct": used_pct, "plan": plan})


def report(month, plan=1000, measured=None):
    """A synthetic cfbd_budget.py report at a chosen volume. `[2026-11-11]`
    with the key's measured pace, inside the bar unless told otherwise."""
    pct = round(100.0 * month / plan)
    measured = mline(40, plan) if measured is None else measured
    return ("CFBD CALL BUDGET — derived\n"
            "  assuming 3 played week(s); build_pace early-stop: ON (32 -> 15 calls)\n\n"
            "  mode          calls/build  builds/wk   calls/wk\n"
            "  cfb-probe              15          8        120\n"
            "  fb-scores               2         44         88\n"
            "                                              209  = %d/month\n\n"
            "  Free                 %d/mo      %d%%  ⚠️\n\n"
            "%s\n\n"
            "⚠️ %d/month against a %d plan — %d%%. tail\n"
            % (month, plan, pct, measured, month, plan, pct))


_over = W.judge(W.parse(report(900)))
ck("🔴🔴 a schedule past the bar ALARMS",
   _over["state"] == "OVER",
   "⛔ 900 calls against a 1,000 plan is 90%%. If this is silent the "
   "whole file is decorative. Got %s" % _over["state"])
ck("✅ ...and the message carries the numbers, not an adjective",
   all(s in _over["why"] for s in ("900", "1,000", "90")),
   "🔴 'CFBD usage is high' tells Sam nothing he can act on. Got %r"
   % _over["why"])
_fine = W.judge(W.parse(report(500)))
ck("✅ a schedule inside the bar is SILENT",
   _fine["state"] == "OK",
   "⛔ a guard that fires on correct code is the other failure, not a "
   "safe one — CLAUDE.md. 500 of 1,000 is 50%%. Got %s" % _fine["state"])
ck("🔴 exactly at the bar alarms, one call under does not",
   W.judge(W.parse(report(800)))["state"] == "OVER"
   and W.judge(W.parse(report(799)))["state"] == "OK",
   "⛔ 80%% of 1,000 is 800. Got %s / %s"
   % (W.judge(W.parse(report(800)))["state"],
      W.judge(W.parse(report(799)))["state"]))

section("4. ⚠️ THE RETRY FIGURE IS REPORTED, NEVER ALARMED ON")
# 🔴 cfbd_budget.py PRICES A FLOOR — one attempt per scheduled build. The
#    retries are what actually blew the quota, and at 7/day the SAME
#    schedule is 634% of the free tier. ⛔ Alarming on that would fire
#    every single day on a working system (rule 238).
# 🔴🔴 ~~THIS SECTION ASSERTED THE BAR AND DID NOT.~~ `[found by Sam,
#    2026-09-15, by MUTATION — the only way these are ever found.]` The
#    first version of section 3 hardcoded 800/799 and never read
#    `pct >= 80` out of `cfbd_budget.py`. **Change that line to 95 and
#    the whole suite stayed green with `WARN_FRAC` still 0.80** — the two
#    bars silently disagreeing, which is the exact "cost tool that
#    contradicts itself on one page" failure this file claims to prevent.
# ⛔ AND THE COMMIT MESSAGE SAID THE CHECK EXISTED. A message asserting a
#    check that is not there is worse than no message: it is what the next
#    reader trusts instead of looking.
# ✅ SO READ THE LINE. Same shape as `RETRY_N` below, which was always
#    driven correctly.
# ⚠️ Scoped to the WARN bar by its own text — `cfbd_budget.py` has two
#    (`>= 100` is the OVER bar), and matching the wrong one would pin
#    this to a number it does not use.
# ⚠️ `finditer` + a SLICE, not `findall` with `.{0,240}`. The greedy form
#    consumed 240 characters past the first bar — swallowing the second —
#    and reported only `>= 100`. ⛔ Caught on the first run by the
#    vacuity check immediately below, which is the whole reason it is
#    there.
_BARS = [(int(m.group(1)), CFBD[m.end():m.end() + 240])
         for m in re.finditer(r"if pct >= (\d+):", CFBD)]
_WARN_BARS = [n for n, blk in _BARS if "Little headroom" in blk]
ck("⚠️ both of cfbd_budget.py's bars are findable at all",
   len(_BARS) >= 2 and len(_WARN_BARS) == 1,
   "⛔ if this regex stops matching, the check below is vacuous — it "
   "would be comparing WARN_FRAC against an empty list (rule 67). Found "
   "bars=%s warn=%s" % ([n for n, _ in _BARS], _WARN_BARS))
# @vacuity the bar must be READ from cfbd_budget.py, never hardcoded here
#   file: cfbd_budget.py
#   find: if pct >= 80:
#   with: if pct >= 95:
# ⚠️ THIS EXACT MUTATION LEFT THE WHOLE SUITE GREEN on 2026-09-15, with
#    WARN_FRAC still 0.80 and cfbd_budget.py warning at 95 — two bars
#    silently disagreeing. Sam found it by hand. `vacuity.py` applies it
#    nightly now so the next one is not found by hand.
ck("🔴🔴 WARN_FRAC IS cfbd_budget.py's OWN BAR, read out of its source",
   bool(_WARN_BARS) and abs(W.WARN_FRAC * 100 - _WARN_BARS[0]) < 1e-9,
   "⛔ THE TWO MUST NOT DRIFT. cfbd_budget.py warns at `pct >= %s` and "
   "this file judges at %s%%. The day they differ, the issue body and "
   "the tool it quotes say opposite things about the same number — and "
   "nothing else in this repo would notice."
   % (_WARN_BARS[0] if _WARN_BARS else "<not found>", W.WARN_FRAC * 100))
ck("⚠️ the retry rate is the one cfbd_budget.py's own header names",
   W.RETRY_N == 7 and "~7 / day" in CFBD,
   "⛔ a number invented here would be a bar nobody agreed to. "
   "cfbd_budget.py measured ~7/day from backfill-report.txt's commit "
   "history, 09-06..09-08. Got %d" % W.RETRY_N)
_body = W.render(_over, retry_month=6342)
ck("✅ the retry figure appears in the BODY",
   "6,342" in _body and "FLOOR" in _body.upper(),
   "🔴 the floor is the optimistic half; hiding the retry number would "
   "make the issue read better than the truth")
ck("⛔ ...and it does NOT change the verdict",
   W.judge(W.parse(report(500)))["state"] == "OK",
   "🔴 a 634%% context figure must never turn a healthy floor into an "
   "alarm, or the channel is filtered inside a week")

section("5. 🔴🔴 FAIL CLOSED: A BROKEN PARSE IS NEVER 'FINE'")
_good = report(900)
for _name, _txt in [
        ("empty output", ""),
        ("no verdict line", _good.replace("against a", "vs a")),
        ("no per-mode table", re.sub(r"^  (cfb-probe|fb-scores).*$", "", _good,
                                     flags=re.M)),
        ("printed % disagrees with the plan",
         _good.replace("— 90%. tail", "— 12%. tail")),
        ("a zero plan", _good.replace("against a 1000 plan", "against a 0 plan")),
        # `[2026-11-11]` the key's own counter is cross-checked the same way
        ("no measured-pace line", "\n".join(
            l for l in _good.splitlines() if "measured pace:" not in l)),
        ("a measured % that disagrees with its own figures",
         re.sub(r"(\d+)% of a 1000 plan", "3% of a 1000 plan", _good)),
        ("a measured pace against another plan",
         report(900, measured=mline(40, plan=3000))),
]:
    _v = W.judge(W.parse(_txt))
    ck("⛔ %s -> UNREADABLE" % _name,
       _v["state"] == "UNREADABLE",
       "🔴 a partial parse that still answers OK is the shape that "
       "reports a confident wrong number. Got %s" % _v["state"])
ck("⛔ ...and judge() never raises on rubbish",
   W.judge(None)["state"] == "UNREADABLE"
   and W.judge({})["state"] == "UNREADABLE"
   and W.judge("nonsense")["state"] == "UNREADABLE",
   "🔴 a watcher that dies before it looks reports nothing, which is "
   "indistinguishable from all-clear")

section("6. ⛔ 'I COULD NOT LOOK' IS NOT 'THE QUOTA IS FINE'")


def drive_watch(stdout, rc=0):
    """Run the REAL cfbd_watch.py against a fake cfbd_budget.py."""
    d = tempfile.mkdtemp(prefix="cfbdwatch-")
    import shutil
    shutil.copy(os.path.join(ROOT, "cfbd_watch.py"), d)
    open(os.path.join(d, "cfbd_budget.py"), "w", encoding="utf-8").write(
        "import sys\nsys.stdout.write(%r)\nsys.exit(%d)\n" % (stdout, rc))
    p = subprocess.run([sys.executable, os.path.join(d, "cfbd_watch.py")],
                       capture_output=True, text=True, timeout=120)
    return p.returncode


for _label, _stdout, _brc, _want in [
        ("a schedule inside the bar", report(500), 0, 0),
        ("a schedule past the bar", report(900), 0, 1),
        ("cfbd_budget.py over plan (its own exit 1)", report(1500), 1, 1),
        ("output this parser cannot read", "nothing like a budget", 0, 2),
        # 🔴🔴 `[2026-11-11]` THE DEFECT: a floor inside the bar while the
        #    key's own counter runs it dry. ~~exit 0~~, which CLOSED the issue.
        ("a schedule inside the bar, a measured pace past it",
         report(500, measured=mline(103)), 1, 1),
        ("a schedule inside the bar, the counter with no pace",
         report(500, measured="  measured pace: UNKNOWN — no CFBD quota "
                              "reading on disk"), 0, 2),
]:
    _got = drive_watch(_stdout, _brc)
    ck("⛔ %s -> exit %d" % (_label, _want), _got == _want,
       "🔴 the workflow branches on this number and nothing else: 0 "
       "CLOSES an open issue, 1 opens one, 2 leaves it exactly as it is. "
       "Got %d" % _got)

section("7. ⚠️ THE WORKFLOW'S OWN SHAPE")
_LIVE = live(WF)
ck("⚠️ it is daily, off :00 and :30",
   re.search(r'- cron: "(\d+) 14 \* \* \*"', WF)
   and re.search(r'- cron: "(\d+) ', WF).group(1) not in ("0", "00", "30"),
   "⛔ a number that moves only when code moves, asked hourly, is 24 "
   "identical answers a day; :00 and :30 slots get dropped")
_mins = {c.split()[0] for c in re.findall(r'- cron: "([^"]+)"', WF)}
_others = set()
for _p in os.listdir(WF_DIR):
    if _p == "cfbd.yml" or not _p.endswith(".yml"):
        continue
    for _c in re.findall(r'- cron: "([^"]+)"', read(os.path.join(WF_DIR, _p))):
        _f = _c.split()
        if _f[1] in ("14", "*"):
            _others.add(_f[0])
ck("⚠️ ...and its minute collides with nothing already in that hour",
   not (_mins & _others),
   "🔴 GitHub drops runs in congested slots. Taken in hour 14: %s, "
   "ours: %s" % (sorted(_others), sorted(_mins)))
ck("⛔ the judgement is in Python, not in the shell step",
   "cfbd_watch.py" in _LIVE and "0.8" not in _LIVE and "1000" not in _LIVE,
   "🔴 rule 66 — a shell step that decides what counts as over-quota is "
   "a second copy of the judgement, and the copy no test reaches")
ck("⛔ ...and `unknown` leaves any open issue alone",
   "leaving any open issue alone" in _LIVE,
   "🔴 closing a quota alert because the check itself broke is how a "
   "real outage goes quiet")
ck("⚠️ the run carries its cron so runs_report can attribute it",
   "event.schedule" in WF and "[cron " in WF,
   "⛔ ledger rule 271 — unstamped, it is seen but not attributable")
ck("⚠️ it has its own concurrency group",
   re.search(r"concurrency:\s*\n\s*group: cfbd", WF),
   "⛔ CLAUDE.md — a shared group silently cancels queued scheduled runs")
ck("💰 it spends nothing: no API key, no Claude action",
   "API_KEY" not in WF and "anthropics/claude-code-action" not in WF,
   "🔴 reporting a quota must not consume the quota")
ck("⛔ and it never reads MLB product state",
   "picks/" not in _LIVE and "record.json" not in _LIVE
   and "card.py" not in _LIVE,
   "⚠️ cfbd_budget.py reads the workflow and cfb.py — a COLLEGE FOOTBALL "
   "call count, never a pick, a card or a record")

section("7b. ⛔ ONE ISSUE, UPDATED IN PLACE — DRIVEN, NOT GREPPED")
# 🔴🔴 ~~THIS WAS NOT GUARDED AT ALL.~~ `[found by Sam, 2026-09-15, by
#    MUTATION]` Section 7 checks that the `unknown` path leaves an open
#    issue alone. **It never checked that the OVER path EDITS rather than
#    CREATES** — so replacing `gh issue edit` with a fresh `gh issue
#    create` left the suite green, and the deployed watcher would have
#    opened a NEW quota issue every single day.
# ⛔ THAT IS RULE 238 EXACTLY: a workflow that opens a fresh issue daily
#    is one whose notifications get filtered, and a filtered alert is no
#    alert — on the one channel that would warn about a quota which has
#    already run out once.
# ⚠️ AND IT IS DRIVEN, NOT GREPPED. A check for the STRING `issue edit`
#    passes on a step that prints it and then creates anyway (rule 249).


def _steps(text):
    """(step name, shell body) for every `run: |` block."""
    out, lines, name = [], text.splitlines(), "?"
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*- name:\s*(.+)$", ln)
        if m:
            name = m.group(1).strip()
        m = re.match(r"^(\s*)run:\s*\|", ln)
        if not m:
            continue
        ind, body = len(m.group(1)), []
        for nxt in lines[i + 1:]:
            if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= ind:
                break
            body.append(nxt)
        out.append((name, "\n".join(body)))
    return out


def _drive(state, open_issue):
    """Run the REAL 'Tell Sam' shell with a fake `gh`. -> the argv log."""
    body = [b for _n, b in _steps(WF) if "gh issue create" in b]
    if not body:
        return ""
    d = tempfile.mkdtemp(prefix="cfbdtell-")
    log = os.path.join(d, "gh.log")
    gh = os.path.join(d, "gh")
    open(gh, "w", encoding="utf-8").write(
        '#!/bin/bash\nprintf "%s\\n" "$*" >> "$GH_LOG"\n'
        'if [ "$1 $2" = "issue list" ]; then echo "$FAKE_NUM"; fi\nexit 0\n')
    os.chmod(gh, os.stat(gh).st_mode | stat.S_IEXEC)
    src = re.sub(r"\$\{\{\s*steps\.look\.outputs\.state\s*\}\}",
                 state, body[-1])
    # ⚠️ `[2026-11-01]` The report the look step would have left: the step
    # writes no issue without one (test_budget_watch.py §2).
    src = re.sub(r"\$\{\{[^}]*\}\}", "x", src).replace("/tmp/", d.replace(os.sep, "/") + "/")
    open(os.path.join(d, "cfbd.md"), "w", encoding="utf-8").write("a report\n")
    sh = os.path.join(d, "step.sh")
    open(sh, "w", encoding="utf-8").write(src)
    subprocess.run(["bash", sh], cwd=d, timeout=60, capture_output=True,
                   text=True,
                   env=dict(os.environ,
                            PATH=d + os.pathsep + os.environ["PATH"],
                            GH_LOG=log, FAKE_NUM=(open_issue or "")))
    return open(log, encoding="utf-8").read() if os.path.exists(log) else ""


# 🔴 THE HARNESS IS PROVEN ABLE TO SEE A CREATE BEFORE IT IS TRUSTED TO
#    REPORT THE ABSENCE OF ONE. ⛔ Otherwise "it did not create" is true
#    of a step that never ran at all (rule 67).
_no_open = _drive("bad", "")
ck("🔴 the harness CAN observe a create — proven with no issue open first",
   "issue create" in _no_open and "cannot see a full" not in _no_open,
   "⛔ if the fake `gh` never runs, every assertion below is vacuous. "
   "Got %r" % _no_open)
_with_open = _drive("bad", "42")
# @vacuity the OVER path must EDIT an open issue, never open a second one
#   file: .github/workflows/cfbd.yml
#   find: gh issue edit "$NUM" --add-label gizmo-watch --body-file /tmp/cfbd.md
#   with: gh issue create --label gizmo-watch --title "$TITLE" --body-file /tmp/cfbd.md
# ⚠️ ~~`find: gh issue edit "$NUM" --body-file /tmp/cfbd.md`~~ REPOINTED
#    2026-09-19, in the same commit that put `--add-label gizmo-watch` on
#    that line. ⛔ A `find` that matches ZERO times mutates nothing, so
#    the file "passes" having been asked nothing — rule 244, and the
#    exact shape this harness exists to catch. `vacuity.py` calls it
#    MALFORMED rather than clean, which is what caught this one.
# ⚠️ THIS EXACT MUTATION LEFT THE WHOLE SUITE GREEN on 2026-09-15 — a new
#    quota issue every day, rule 238, on the one channel that would warn
#    about a quota that has already run out once.
ck("🔴🔴 with an issue ALREADY OPEN, the OVER path EDITS it",
   "issue edit 42" in _with_open,
   "⛔ THE MUTATION SAM FOUND: swap `gh issue edit` for a fresh `gh issue "
   "create` and this file used to stay green. Got %r" % _with_open)
ck("🔴🔴 ...and does NOT open a second one",
   "issue create" not in _with_open,
   "⛔ RULE 238. A new quota issue every day is a channel Sam filters, "
   "and the thing it would have warned about is a quota that has already "
   "run out once. Got %r" % _with_open)
ck("✅ ...while `ok` closes the open issue rather than editing it",
   "issue close 42" in _drive("ok", "42"),
   "🔴 one issue, updated in place, CLOSED BY ITSELF — the third leg of "
   "the contract. Got %r" % _drive("ok", "42"))

section("8. 🔴 THE CRON TOTAL MOVES WITH THE CRON THIS ADDS")
# ⛔ Drop 66's guard counts every `- cron:` line and fails if CLAUDE.md
#    disagrees. This adds exactly one, so the marker moves IN THIS COMMIT
#    — a follow-up would leave an intermediate red state on main.
# ⚠️ Deployed + staged, one per file name — the one counter (rule 117).
import wfparse as _wfp  # noqa: E402
_total = _wfp.cron_total(ROOT)
_claim = re.search(r"<!--\s*CRON TOTAL:\s*(\d+)\s*-->",
                   read(os.path.join(ROOT, "CLAUDE.md")))
ck("🔴 CLAUDE.md's stated cron total matches the crons actually scheduled",
   _claim and int(_claim.group(1)) == _total,
   "⛔ this PR adds one cron, so the marker must move with it. Stated "
   "%s, actual %d" % (_claim and _claim.group(1), _total))
note("⚠️ %d crons with this PR's one included. ⛔ PR #13 also adds a cron "
     "and also moves this marker, so whichever merges SECOND needs a "
     "recount to 53 — the guard will catch it either way, and the count "
     "must be recounted rather than incremented." % _total)

section("9. 🔴🔴 THE KEY'S OWN COUNTER: THE PACE THE SCHEDULE CANNOT SEE")
# `[2026-11-11]` THE DEFECT. Every day of October and November this watcher
# printed "OK 949/month 31% of 3000" while CFBD's own header fell ~100 calls
# a day: October ended with 173 left (94% used) and November's 1,888 on 11-11
# would run out around the 29th. It read the schedule and nothing else, and a
# schedule cannot see a cron GitHub starts 5-10 hours late re-sweeping what an
# hourly pass already built, or a rebuild priced at week 3 in week 11.
# ✅ The readings are PLANTED, by the real writer (`cfb.record_quota`), on a
# tree pinned to the clock each check uses: never the live tree.
import datetime as _dt  # noqa: E402
import cfb as _cfb  # noqa: E402
import cfbd_budget as B  # noqa: E402

_UTC = _dt.timezone.utc


def plant(readings):
    """A college data dir whose quota readings are [(datetime, remaining)]."""
    data = os.path.join(tempfile.mkdtemp(prefix="cfbdpace-"), "ncaaf")
    saved = dict(_cfb.QUOTA)
    try:
        for t, r in readings:
            _cfb.QUOTA.update({"seen": True,
                               "headers": {"X-CallLimit-Remaining": str(r)},
                               "at": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
                               "note": None})
            _cfb.record_quota(data, log=lambda *a: None, when=t)
    finally:
        _cfb.QUOTA.clear()
        _cfb.QUOTA.update(saved)
    return data


def series(now, per_day, left_now, days=10, step_h=6):
    """Readings every `step_h` hours, falling `per_day`, `left_now` at `now`."""
    n = int(days * 24 / step_h)
    return [(now - _dt.timedelta(hours=k * step_h),
             int(round(left_now + per_day * k * step_h / 24.0)))
            for k in range(n, -1, -1)]


def verdict(pace, month=949, plan=3000):
    """judge() on a floor at `month` beside this measured pace."""
    return W.judge(W.parse(report(month, plan, measured=B.pace_line(pace))))


# THE INCIDENT'S OWN NUMBERS: the key's readings 11-05 -> 11-11 as the
# archive holds them, judged at 11-11 21:40Z, the run that said "OK".
_INCIDENT = [("11-04T15:40:46", 2584), ("11-05T07:16:14", 2542),
             ("11-05T15:53:03", 2499), ("11-06T08:51:50", 2457),
             ("11-06T15:14:44", 2414), ("11-07T10:38:39", 2368),
             ("11-07T14:22:34", 2325), ("11-08T07:07:46", 2279),
             ("11-08T14:40:03", 2233), ("11-08T19:26:24", 2190),
             ("11-09T07:09:05", 2145), ("11-09T17:55:07", 2104),
             ("11-10T09:17:33", 2020), ("11-10T16:09:04", 1979),
             ("11-11T07:26:23", 1932), ("11-11T15:40:46", 1890),
             ("11-11T16:33:10", 1888)]
_NOW = _dt.datetime(2026, 11, 11, 21, 40, tzinfo=_UTC)
_inc = B.measured_pace(plant([(_dt.datetime.strptime("2026-" + w, "%Y-%m-%dT%H:%M:%S")
                               .replace(tzinfo=_UTC), r) for w, r in _INCIDENT]),
                       now=_NOW, plan=3000)
ck("🔴 the incident's readings give a pace: ~100 calls a day",
   _inc["state"] == "READ" and 90 <= _inc["pace"] <= 115,
   "⛔ 2,542 on 11-05 to 1,888 on 11-11 is 654 calls in 6.4 days. Got %s"
   % {k: _inc.get(k) for k in ("state", "pace", "used", "span_days", "why")})
ck("🔴 ...and the key runs out before the 12-01 reset, around 11-29/30",
   _inc.get("run_out") and _dt.datetime(2026, 11, 28, tzinfo=_UTC)
   <= _inc["run_out"] < _dt.datetime(2026, 12, 1, tzinfo=_UTC),
   "Got %s" % _inc.get("run_out"))
# @vacuity the measured pace must be what the header FELL by, never its rises
#   file: cfbd_budget.py
#   find:     used = sum(max(0, a - b) for (_t0, a), (_t1, b) in zip(win, win[1:]))
#   with:     used = sum(max(0, b - a) for (_t0, a), (_t1, b) in zip(win, win[1:]))
_iv = verdict(_inc)
# @vacuity the counter's pace must reach the verdict at the floor's own bar
#   file: cfbd_watch.py
#   find:     if m["pct"] >= 100 * WARN_FRAC:
#   with:     if m["pct"] >= 1000 * WARN_FRAC:
ck("🔴🔴 THE DEFECT: a floor at 32% beside that counter is OVER, never OK",
   _iv["state"] == "OVER" and "runs out around 2026-11-" in _iv.get("why", ""),
   "⛔ ~~'OK 949/month 31%% of 3000'~~ is what this watcher printed at 11-11 "
   "21:40Z, and OK CLOSES the issue. Got %s: %s"
   % (_iv["state"], _iv.get("why")))
ck("✅ ...and the body says both halves, the counter first",
   _iv["state"] == "OVER"
   and W.render(_iv).index("CFBD's own counter") < W.render(_iv).index("FLOOR"),
   "🔴 the issue must name the number that tripped the bar")

_ok = B.measured_pace(plant(series(_NOW, 40, 1888)), now=_NOW, plan=3000)
_okv = verdict(_ok)
ck("✅ a key at 40 a day with 1,888 left on 11-11 is OK (63% by the reset)",
   _ok["state"] == "READ" and 38 <= _ok["pace"] <= 42 and _okv["state"] == "OK"
   and not _ok["run_out"],
   "⛔ a guard that fires on correct code is the other failure. Got %s %s"
   % (_okv["state"], {k: _ok.get(k) for k in ("pace", "pct", "run_out")}))
ck("✅ ...and an OK says the counter's numbers too",
   "CFBD's own counter fell 40" in _okv.get("why", ""), _okv.get("why"))
_flo = verdict(_ok, month=2700)
ck("⛔ a floor past the bar is OVER whatever the counter says",
   _flo["state"] == "OVER", "Got %s" % _flo["state"])

for _label, _rs, _want in [
        ("no reading at all", [], "no CFBD quota reading"),
        ("a newest reading 3 days old",
         series(_NOW - _dt.timedelta(days=3), 100, 1888), "hours old"),
        ("one day of readings", series(_NOW, 100, 1888, days=1), "a pace needs"),
]:
    _u = B.measured_pace(plant(_rs), now=_NOW, plan=3000)
    _uv = verdict(_u)
    # @vacuity a counter with no pace is "could not look", never the floor's OK
    #   file: cfbd_watch.py
    #   find: return _bad("the key's own counter gave no pace (%s), so the schedule's "
    #   with: return dict(out, state="OK", why="the key's own counter gave no pace (%s), so the schedule's "
    ck("⛔ %s -> no pace, and the watcher could not look" % _label,
       _u["state"] == "UNKNOWN" and _want in _u.get("why", "")
       and _uv["state"] == "UNREADABLE",
       "🔴 no pace is not a small pace. Got %s %r / %s"
       % (_u["state"], _u.get("why"), _uv["state"]))
ck("⛔ ...while a floor past the bar still alarms without one",
   W.judge(W.parse(report(2700, 3000, measured=B.pace_line(
       B.measured_pace(plant([]), now=_NOW, plan=3000)))))["state"] == "OVER",
   "🔴 a missing counter must not silence the schedule's own alarm")

# ⚠️ A RESET INSIDE THE WEEK: 173 on 10-31 23:56Z, 2,924 on 11-01 07:13Z.
_rst = [(t, r) for t, r in series(_dt.datetime(2026, 10, 31, 23, 56, tzinfo=_UTC),
                                   100, 173, days=4)] + \
       [(t, r) for t, r in series(_dt.datetime(2026, 11, 3, 7, 13, tzinfo=_UTC),
                                   100, 2924 - 200, days=2)]
_rp = B.measured_pace(plant(_rst), now=_dt.datetime(2026, 11, 3, 8, 0, tzinfo=_UTC),
                      plan=3000)
ck("⚠️ a reset inside the week adds nothing: the pace stays ~100 a day",
   _rp["state"] == "READ" and _rp["resets"] == 1 and 85 <= _rp["pace"] <= 105,
   "⛔ counted as a rise, the reset would read as -2,700 calls; ignored, the "
   "sweep between the two readings is lost, so a little under 100. Got %s"
   % {k: _rp.get(k) for k in ("state", "pace", "resets", "used", "span_days")})

# 🔴🔴 END TO END, THE REAL WATCHER RUNNING THE REAL cfbd_budget.py, on a
#    tree pinned to NOW (the real clock both runs read). ⛔ Today's watcher
#    exited 0 here, and 0 is the exit that CLOSES the issue.
_now = _dt.datetime.now(_UTC)
_to_reset = (B.next_reset(_now) - _now).total_seconds() / 86400.0
_hot = plant(series(_now, 100, int(100 * _to_reset * 0.5)))
_e2e = subprocess.run([sys.executable, "cfbd_watch.py"], cwd=ROOT,
                      capture_output=True, text=True, timeout=300,
                      env=dict(os.environ, CFBD_DATA=_hot, CFBD_PLAN="3000"))
ck("🔴🔴 the real watcher on a key spending 100 a day, half-way to empty "
   "at the reset, exits 1",
   _e2e.returncode == 1 and "runs out around" in _e2e.stdout,
   "⛔ THE GUARD FOR 11-11: exit 0 closes the open issue. Got rc=%s %s %s"
   % (_e2e.returncode, _e2e.stdout[-300:], _e2e.stderr[-300:]))
_cold = subprocess.run([sys.executable, "cfbd_watch.py"], cwd=ROOT,
                       capture_output=True, text=True, timeout=300,
                       env=dict(os.environ, CFBD_DATA=plant([]),
                                CFBD_PLAN="3000"))
# ⚠️ The schedule's month does not depend on the plan; the bar here is 3,000's.
_floor_over = (_parsed.get("state") == "READ"
               and _parsed["month"] >= W.WARN_FRAC * 3000)
ck("⛔ ...and with no reading on disk it could not look (exit 2), unless the "
   "schedule alone is past the bar",
   _cold.returncode == (1 if _floor_over else 2),
   "🔴 no reading is not all-clear. Got rc=%s %s"
   % (_cold.returncode, _cold.stdout[-200:]))

note("⛔ WHAT THIS DOES NOT CLAIM: that 906 calls a month is safe, or "
     "that the floor is what will actually be spent. It claims the "
     "DERIVED schedule is at 91% of a quota that has already run out "
     "once, and that a human should look. ➡️ Six watchers now, six "
     "questions, and none of them replaces another.")
