#!/usr/bin/env python3
"""THE WATCHER MUST MEASURE WHAT THE REPOSITORY PAYS, NOT WHAT IT WRITES.

🔴🔴 THE TRAP THIS FILE EXISTS FOR. Git deltas plain text extremely well
and **cannot delta a gzip at all**. So there are two very different
numbers for "how much did the repo grow", and on this repo they differ by
**2.84x** — 15.15 MB/day of raw blob bytes against 5.34 MB/day actually
stored. ⛔ A watcher summing raw sizes cries wolf; one reading the working
tree sleeps through everything.

➡️ SO THE DISCRIMINATION IS DRIVEN, NOT ASSERTED. It is not enough that
the figure is *a* number: this file recomputes the packed sum
independently from `objectsize:disk`, requires the watcher to match it,
and requires it to **NOT** match the raw sum. A check that passed for both
would be asking nothing (rule 67).

⚠️ AND THE SERIES MUST RECONCILE WITH THE TOTAL. The first version of
`_series` used `rev-list --objects --no-walk`, which lists every object
REACHABLE from a commit rather than the ones it introduced: it reported
31-41 MB per day against a 37 MB window total — 8x out, every day, in a
shape that looked entirely plausible. Reconciliation is what catches that;
a reader glancing at the numbers did not.

⛔ AND A CLONE THAT CANNOT ANSWER MUST SAY SO. `actions/checkout` defaults
to `fetch-depth: 1`, where `git count-objects` reports the size of the one
fetched commit — 43.39 MiB against a real 105.14 MiB — and there is no
history to measure at all. A watcher reporting that would be reassuring,
constant and false.

⚠️ No network, no credits. It asks git about this checkout and builds two
throwaway repositories.
"""
import datetime
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section

import repo_watch as R


# ══════════════════════════════════════════════════════════════════════
# @vacuity the watcher must read objectsize:disk, not the raw blob size
#   file: repo_watch.py
#   find: "%(objectsize:disk)"],
#   with: "%(objectsize)"],
# ══════════════════════════════════════════════════════════════════════


def _g(*a, **kw):
    return subprocess.run(("git",) + a, cwd=kw.get("cwd", ROOT),
                          capture_output=True, text=True, check=True).stdout


def _commit(d, files, days_ago):
    for path, body in files.items():
        p = os.path.join(d, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        io.open(p, "wb").write(body)
    _g("-C", d, "add", "-A")
    when = (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=days_ago)).strftime(
                "%Y-%m-%dT%H:%M:%S+00:00")
    subprocess.run(["git", "-C", d, "commit", "-q", "-m", "c"], check=True,
                   capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_DATE=when,
                            GIT_COMMITTER_DATE=when))


def _bench():
    """A repository shaped like this one: text git deltas, gzip it cannot.

    🔴🔴 EVERY ASSERTION BELOW RUNS HERE, NOT ON THE LIVE TREE, AND THAT
    IS NOT A CONVENIENCE. `collect.yml` checks out with `actions/checkout`
    defaults — **a shallow clone** — so `repo_watch.py` correctly refuses
    to read the live repository in CI. A suite that asserted on the live
    tree would pass on a developer's full clone and go red on every CI
    run, or be quietly skipped there, which is the permanent-no-op class.
    ⚠️ The live tree is still checked, as a BONUS, whenever the clone can
    answer — see the end of section 1.
    """
    d = tempfile.mkdtemp(prefix="repowatch-bench-")
    _g("init", "-q", d, cwd="/")
    _g("-C", d, "config", "user.email", "t@t")
    _g("-C", d, "config", "user.name", "t")
    day = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    # ⛔ THE FIRST COMMIT MUST PREDATE THE WINDOW or `window_base` finds
    #    nothing and everything below is measured on an UNREADABLE report.
    _commit(d, {"README": b"anchor"}, R.WINDOW_DAYS + 13)
    for n in range(4):
        files = {
            # a large plain JSON changing slightly — git deltas this well
            "data/latest/big.json": json.dumps(
                [{"k": i, "v": "row-%d" % i} for i in range(8000 + n)]
            ).encode(),
            # a gzip REWRITTEN IN PLACE — git cannot delta this at all
            "data/latest/board.json.gz": gzip.compress(os.urandom(60000)),
        }
        if n == 0:
            # a dated archive, written ONCE: the correct design (rule 285)
            files["data/%s/k/0100.json.gz" % day] = gzip.compress(
                os.urandom(60000))
        _commit(d, files, max(1, 5 - n))
    _g("-C", d, "gc", "-q", "--prune=now")
    return d, day


_BENCH, _BDAY = _bench()
_B = R.judge(R.measure(root=_BENCH))


def _independent(root, days=R.WINDOW_DAYS):
    """Recompute raw and on-disk sums here, without asking the module."""
    base = R.window_base(days, root)
    names = [l.split(" ", 1)[0] for l in
             _g("rev-list", "--objects", "%s..HEAD" % base,
                cwd=root).splitlines()]
    p = subprocess.run(
        ["git", "cat-file",
         "--batch-check=%(objecttype) %(objectsize) %(objectsize:disk)"],
        cwd=root, input="\n".join(names) + "\n", capture_output=True,
        text=True)
    raw = disk = 0
    for l in p.stdout.splitlines():
        f = l.split()
        if len(f) == 3 and f[0] == "blob":
            raw += int(f[1])
            disk += int(f[2])
    return raw, disk


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴🔴 IT MEASURES WHAT IS STORED, NOT WHAT IS WRITTEN")
# ══════════════════════════════════════════════════════════════════════
ck("⚠️ the bench repository produced a readable report",
   _B["state"] in ("OK", "BAD"),
   "⛔ if this cannot be read, every comparison below is vacuous — rule "
   "67. state=%s why=%s" % (_B["state"], _B.get("why", "")[:120]))

_BRAW, _BDISK = _independent(_BENCH)
ck("🔴🔴 the reported growth IS the objectsize:disk sum",
   abs(_B.get("disk_mb", -1) - _BDISK / 1e6) < 1e-6,
   "⛔ this is the whole question. reported=%.6f MB independent=%.6f MB"
   % (_B.get("disk_mb", -1), _BDISK / 1e6))
ck("🔴🔴 ...and it is NOT the raw objectsize sum",
   abs(_B.get("disk_mb", -1) - _BRAW / 1e6) > 1e-6,
   "⛔ THE DISCRIMINATION. A watcher reading either number would pass a "
   "check that only asked for 'a number'. reported=%.4f raw=%.4f "
   "disk=%.4f MB" % (_B.get("disk_mb", -1), _BRAW / 1e6, _BDISK / 1e6))
ck("⚠️ ...and the two really are far apart on the bench, so that bites",
   _BDISK and _BRAW / float(_BDISK) > 1.5,
   "⛔ the bench is built to contain both kinds of file precisely so the "
   "check above discriminates. If they converged it would stop asking "
   "anything. raw/disk=%.2fx" % (_BRAW / float(_BDISK) if _BDISK else 0))

ck("🔴 the per-day series RECONCILES with the window total",
   abs(sum(d["disk_mb"] for d in _B.get("series", []))
       - _B.get("disk_mb", 0)) <= 0.05 * _B.get("disk_mb", 1),
   "⛔ the first `_series` listed every object REACHABLE from each day's "
   "commits rather than the ones they introduced, and reported ~8x the "
   "real figure in a shape that looked plausible. series=%.4f total=%.4f"
   % (sum(d["disk_mb"] for d in _B.get("series", [])), _B.get("disk_mb", 0)))

# ⚠️ AND THE LIVE TREE TOO — BUT ONLY WHERE IT CAN ANSWER.
# 🔴 `[2026-09-22]` ~~within 0.01 MB, on any full clone~~ asked a question
#    with no single answer: on a repository storing objects more than
#    once, `objectsize:disk` depends on WHICH copy git finds first. The
#    check now runs only on a single-copy repository — and there it must
#    match EXACTLY, which is harder than 0.01. ⛔ And it now RUNS: the
#    `repo` job in `budget.yml` (full history) repacks and sets
#    REPO_WATCH_LIVE_REQUIRED=1, so skipping it there is a failure.
_REQUIRED = os.environ.get("REPO_WATCH_LIVE_REQUIRED") == "1"
if R.clone_is_complete() and R.single_copy():
    _LIVE = R.judge(R.measure())
    _LRAW, _LDISK = _independent(ROOT)
    ck("✅ and the same three hold on the LIVE repository, EXACTLY",
       _LIVE["state"] in ("OK", "BAD")
       and abs(_LIVE["disk_mb"] - _LDISK / 1e6) < 1e-6
       and abs(_LIVE["disk_mb"] - _LRAW / 1e6) > 0.01,
       "⛔ real data, real mix. state=%s reported=%.6f raw=%.2f disk=%.6f MB"
       % (_LIVE["state"], _LIVE.get("disk_mb", -1), _LRAW / 1e6,
          _LDISK / 1e6))
    note("live: pack %.2f MiB · packed %.2f MB/day · raw %.2f MB/day (%.2fx)"
         % (_LIVE["pack_mib"], _LIVE["disk_mb_day"], _LIVE["raw_mb_day"],
            _LIVE["raw_over_disk"]))
else:
    _LIVE = None
    note("⚠️ the live tree was not measured: %s. ⛔ That is exactly why "
         "every assertion above runs against the bench." %
         ("this checkout is SHALLOW" if not R.clone_is_complete() else
          "objects are stored more than once here, so an on-disk size has "
          "no single answer (repack to one pack to measure)"))
ck("⛔ where the live check is REQUIRED it actually ran",
   _LIVE is not None or not _REQUIRED,
   "REPO_WATCH_LIVE_REQUIRED=1 and the live block was skipped — a check "
   "that only runs where nobody looks runs nowhere")

# ⚠️ `if _LIVE:` AND NOT `_LIVE["state"]`. In a SHALLOW clone `_LIVE` is
#    None, and subscripting it raised a TypeError that made this file DIE
#    rather than fail — 10 checks ran and the rest never did. Caught by
#    running the suite in a `--depth 1` clone, which is what CI has.
if _LIVE:
    ck("⛔ both bars sit well above what was actually measured",
       _LIVE["pack_mib"] < R.PACK_WARN_MIB * 0.5
       and _LIVE["disk_mb_day"] < R.GROWTH_WARN_MB_DAY * 0.5,
       "🔴 a bar within reach of the healthy baseline fires on correct "
       "code. pack %.1f vs %.0f MiB · growth %.2f vs %.0f MB/day"
       % (_LIVE["pack_mib"], R.PACK_WARN_MIB, _LIVE["disk_mb_day"],
          R.GROWTH_WARN_MB_DAY))

# ══════════════════════════════════════════════════════════════════════
section("3. 🔴 A SHALLOW CLONE IS UNREADABLE, NEVER OK")
# ══════════════════════════════════════════════════════════════════════
# ⛔ `actions/checkout` DEFAULTS TO THIS, so it is the case most likely to
#    happen and the one where a wrong answer is most reassuring.
_src = tempfile.mkdtemp(prefix="repowatch-src-")
_g("init", "-q", _src, cwd="/")
_g("-C", _src, "config", "user.email", "t@t")
_g("-C", _src, "config", "user.name", "t")
for _n, _b in enumerate((b"x" * 1000, b"y" * 1000, b"z" * 1000)):
    _commit(_src, {"a.txt": _b}, R.WINDOW_DAYS + 5 - _n * 2)
_sh = tempfile.mkdtemp(prefix="repowatch-shallow-")
try:
    subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + _src,
                    _sh + "/c"], check=True, capture_output=True)
    _shallow = R.judge(R.measure(root=_sh + "/c"))
finally:
    shutil.rmtree(_src, ignore_errors=True)
    shutil.rmtree(_sh, ignore_errors=True)

ck("🔴🔴 a `--depth 1` clone reports UNREADABLE",
   _shallow["state"] == "UNREADABLE",
   "⛔ in that clone `git count-objects` reports the one fetched commit — "
   "43.39 MiB against a real 105.14 MiB here — and there is no window at "
   "all. Reporting it would be small, stable and wrong, which reads "
   "exactly like health. got %s" % _shallow["state"])
ck("⛔ ...and it is explicitly NOT OK",
   _shallow["state"] != "OK",
   "🔴 'I could not look' is not 'the repository is fine', and the "
   "workflow leaves an open issue alone on this state")
ck("⚠️ ...and it says WHY, in words a reader can act on",
   "shallow" in _shallow.get("why", "").lower()
   and "fetch-depth" in _shallow.get("why", ""),
   "⛔ an UNREADABLE with no reason is a dead end. why=%r"
   % _shallow.get("why", "")[:140])

# ══════════════════════════════════════════════════════════════════════
section("4. 🔴 IT NAMES THE CAUSE, AND 'REWRITTEN IN PLACE' IS MEASURED")
# ══════════════════════════════════════════════════════════════════════
# ⛔ A PATH CONVENTION IS A GUESS ABOUT BEHAVIOUR. The number of distinct
#    versions a path has inside the window IS the behaviour.
_top = {t["path"]: t for t in _B.get("top", [])}

ck("⚠️ the bench produced contributors to judge",
   len(_top) >= 3,
   "⛔ an empty top list would make every flag below vacuous. got %s"
   % sorted(_top))
ck("🔴🔴 a gzip REWRITTEN IN PLACE is flagged",
   _top.get("data/latest/board.json.gz", {}).get("hostile") is True,
   "⛔ git cannot delta a gzip, so each of its %s versions was stored in "
   "FULL. This is the finding the watcher exists to keep visible."
   % _top.get("data/latest/board.json.gz", {}).get("versions"))
ck("⛔ a gzip written ONCE — a dated archive — is NOT flagged",
   _top.get("data/%s/k/0100.json.gz" % _BDAY, {}).get("hostile") is False,
   "🔴 THE HALF THAT STOPS THIS BECOMING NOISE. A dated archive is "
   "written once, has nothing to delta against, and is the CORRECT "
   "design (rule 285). Flagging it would tell Sam to undo the thing that "
   "already works. versions=%s"
   % _top.get("data/%s/k/0100.json.gz" % _BDAY, {}).get("versions"))
ck("⛔ ...and a PLAIN file rewritten in place is not flagged either",
   _top.get("data/latest/big.json", {}).get("hostile") is False,
   "🔴 it is rewritten as often as the gzip, and git deltas it — the flag "
   "is about what git can STORE, not about how often a file changes. "
   "versions=%s" % _top.get("data/latest/big.json", {}).get("versions"))

if _LIVE:
    _h = [t for t in _LIVE["top"] if t["hostile"]]
    ck("⚠️ and on the LIVE repo it names real paths rather than a number",
       bool(_h) and all(p["path"].endswith(".gz") and p["versions"] > 1
                        for p in _h),
       "⛔ a number with no cause is a number nobody can act on. "
       "flagged: %s" % [p["path"] for p in _h][:3])

shutil.rmtree(_BENCH, ignore_errors=True)

# ══════════════════════════════════════════════════════════════════════
section("5. ⛔ IT RIDES AN EXISTING ARM — NO NEW CRON")
# ══════════════════════════════════════════════════════════════════════
_WF = os.path.join(ROOT, ".github", "workflows", "budget.yml")
_Y = io.open(_WF, encoding="utf-8").read()
ck("⚠️ budget.yml carries the repo job",
   "\n  repo:\n" in _Y and "repo_watch.py" in _Y,
   "⛔ a watcher nothing runs is a feature that does not exist (rule 78)")
ck("🔴 the repo job checks out FULL history",
   "fetch-depth: 0" in _Y,
   "⛔ git cannot be asked how big a repository is from a shallow clone "
   "of it — §3 above is the same fact from the other side")
ck("⛔ budget.yml still declares exactly ONE cron",
   _Y.count("- cron:") == 1,
   "🔴 CRON TOTAL must not move. Jobs share their workflow's schedule, "
   "which is why this is a second JOB and not a second workflow. got %d"
   % _Y.count("- cron:"))
# ~~`_Y.count("gh label create gizmo-watch") == 2`~~ — **STRUCK
# 2026-09-19, LEDGER RULE 166 FOR THE FOURTH TIME.** Two literal counts,
# 2 and 4, asserting a fact about a file that was correct on the day they
# were written. ⛔ They went RED the moment the UPDATE path learned to
# label as well — a CORRECT change, adding two more `gh label create`
# lines, failed a check whose real subject was never the number.
# ✅ THE QUESTION IS PER CALL SITE, DERIVED. Every filing chain must lead
# with the label, every update must add it, and each must have the label
# ensured above it. That is strictly harder to pass than a count — a new
# unlabelled site now fails where before a matching PAIR of changes could
# have kept the totals and lost the property.
_creates = [l.strip() for l in _Y.split("\n")
            if l.strip().startswith("gh issue create")]
_edits = [l.strip() for l in _Y.split("\n")
          if l.strip().startswith("gh issue edit")]
_heads = [l for l in _creates if not l.startswith("|| gh issue create")]
ck("⚠️ every issue chain in budget.yml LEADS with the gizmo-watch label",
   _heads and all("--label gizmo-watch" in l for l in _heads),
   "⛔ self-repair triages by label, and a watcher that can file without "
   "one files into a queue nothing reads. heads=%r" % (_heads,))
ck("🔴 ...and every UPDATE adds it too — that is where 5 of 6 were lost",
   _edits and all("--add-label gizmo-watch" in l for l in _edits),
   "⛔ an issue created before the label existed stays invisible to "
   "triage forever unless the update path labels it. edits=%r" % (_edits,))
ck("⛔ ...and the label is ensured to exist as often as it is used",
   _Y.count("gh label create gizmo-watch") >= len(_edits),
   "🔴 `gh issue edit --add-label X` FAILS when X does not exist, and "
   "the `else` branch's ensure is on the CREATE path. ensures=%d "
   "edits=%d" % (_Y.count("gh label create gizmo-watch"), len(_edits)))
ck("⛔ ...and `unknown` never closes an open issue",
   _Y.count("leaving any open issue alone") == 2,
   "🔴 'I could not look' is not 'it is fine' — both watchers in this "
   "file must honour that. got %d"
   % _Y.count("leaving any open issue alone"))
