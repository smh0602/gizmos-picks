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

from tcheck import ck, eq, note, section

import repo_watch as R


# ══════════════════════════════════════════════════════════════════════
# @vacuity the watcher must read objectsize:disk, not the raw blob size
#   file: repo_watch.py
#   find: "%(objectsize:disk)"],
#   with: "%(objectsize)"],
#
# @vacuity a bar within reach of the dated healthy baseline is caught
#   file: repo_watch.py
#   find: PACK_WARN_MIB = 500.0        # ~5x the 105.14 MiB measured 2026-09-19
#   with: PACK_WARN_MIB = 150.0        # ~5x the 105.14 MiB measured 2026-09-19
#
# @vacuity the judge says OK at the healthy baseline, driven not read
#   file: repo_watch.py
#   find:     if rep["disk_mb_day"] > GROWTH_WARN_MB_DAY:
#   with:     if rep["disk_mb_day"] > 5.0:
#
# @vacuity only a gzip stored more than once is flagged (bench + live paths)
#   file: repo_watch.py
#   find:     return path.endswith(".gz") and versions > 1
#   with:     return versions > 1
#
# @vacuity [2026-11-17] the series walks main's own commits: a branch authored before the base is not a day
#   file: repo_watch.py
#   find:         log = _git("log", "--first-parent", "--format=%H %cd", "--date=short",
#   with:         log = _git("log", "--format=%H %ad", "--date=short",
#
# @vacuity [2026-11-17] each day counts only what it introduced, so the days sum to the window
#   file: repo_watch.py
#   find:         rng = (end, "^" + prev, "^" + base)
#   with:         rng = (end, "^" + base)
#
# @vacuity [2026-11-17] the working tree is the files' bytes, from git ls-tree
#   file: repo_watch.py
#   find:             tot += int(f[3])
#   with:             tot += 1
#
# @vacuity [2026-11-17] the working tree's growth is HEAD's tree against the base's
#   file: repo_watch.py
#   find:         rep["tree_mb_day"] = (rep["tree_bytes"] - b0) / 1e6 / days
#   with:         rep["tree_mb_day"] = rep["tree_bytes"] / 1e6 / days
#
# @vacuity [2026-11-17] the report prints the working tree's size
#   file: repo_watch.py
#   find:         o.append("| working tree (the Pages site is built from it) | **%.1f MB** "
#   with:         o.append("| working tree (the Pages site is built from it) | **%.0f kB** "
#
# @vacuity [2026-11-17] the pack's 1 GiB is called a recommendation
#   file: repo_watch.py
#   find:                  "not a forecast. GitHub Pages' *recommended* size for a site's source "
#   with:                  "not a forecast. GitHub Pages' size limit for a site's source "
#
# @vacuity [2026-11-17] the working tree's 1 GB is called a hard limit
#   file: repo_watch.py
#   find:                      "larger than 1 GB: a hard limit** |"
#   with:                      "larger than 1 GB** |"
#
# @vacuity [2026-11-17] a tree that cannot be read is said on the report
#   file: repo_watch.py
#   find:         o.append("| working tree | ⚠️ could not be read: %s |" % rep["tree_error"])
#   with:         pass
#
# @vacuity [2026-11-17] measure() keeps a tree it could not read on the report
#   file: repo_watch.py
#   find:         rep["tree_error"] = "%s: %s" % (type(e).__name__, e)
#   with:         pass
#
# @vacuity [2026-11-17] the window's base is main's own commit, never a PR branch's
#   file: repo_watch.py
#   find:     out = _git("rev-list", "-1", "--first-parent", "--before=%d days ago" % days, "HEAD",
#   with:     out = _git("rev-list", "-1", "--before=%d days ago" % days, "HEAD",
#
# @vacuity [2026-11-17] the days to GitHub's 10 GB repository recommendation are that projection
#   file: repo_watch.py
#   find:         rep["days_to_repo_rec"] = ((REPO_REC_GB * 1e9 - rep["pack_mib"] * 1048576.0)
#   with:         rep["days_to_repo_rec"] = ((REPO_REC_GB * 1e6 - rep["pack_mib"] * 1048576.0)
#
# @vacuity [2026-11-17] the report names the size that reaches its line first
#   file: repo_watch.py
#   find:                    % ("working tree" if rep["tree_days_to_limit"] <= rep["days_to_limit"]
#   with:                    % ("working tree" if rep["tree_days_to_limit"] > rep["days_to_limit"]
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


def _independent(root, days=R.WINDOW_DAYS, base=None):
    """Recompute raw and on-disk sums here, without asking the module.

    `base`: the commit the window starts at, when the bench knows it by construction
    (§6b), so the window itself is not the module's answer either."""
    base = base or R.window_base(days, root)
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
# 🔴 `[2026-09-28]` ~~both bars sit well above what the LIVE repo measures
#    today~~ asked whether PRODUCTION stays under half of repo_watch's own
#    bars — another guard's silence on live data, with margin. It would
#    have gone red on correct code within days (measured 2026-09-28 in
#    budget run 36478004911: growth 9.89 against a 10.0 trip, pack 179 of
#    250 MiB) while repo_watch itself still said OK. ✅ The DESIGN question
#    — "is a bar within reach of the HEALTHY BASELINE?" — is now asked of
#    the dated baseline the bars were set against (repo_watch.py cites it
#    beside each constant, and this file's docstring quotes it), with the
#    same factor of two, and the judge is driven on that baseline. The
#    live numbers are printed as a note: Sam moves a bar, not this file.
BASELINE = {"measured": "2026-09-19", "pack_mib": 105.14, "disk_mb_day": 5.34}
ck("⛔ both bars sit at least TWICE the dated healthy baseline",
   R.PACK_WARN_MIB >= 2 * BASELINE["pack_mib"]
   and R.GROWTH_WARN_MB_DAY >= 2 * BASELINE["disk_mb_day"],
   "🔴 a bar within reach of the healthy baseline fires on correct code. "
   "pack bar %.0f vs %.2f MiB · growth bar %.1f vs %.2f MB/day (measured %s)"
   % (R.PACK_WARN_MIB, BASELINE["pack_mib"], R.GROWTH_WARN_MB_DAY,
      BASELINE["disk_mb_day"], BASELINE["measured"]))
_at_base = R.judge(dict(_B, state=None, why="", complete_clone=True,
                        pack_mib=BASELINE["pack_mib"],
                        disk_mb_day=BASELINE["disk_mb_day"]))
_over = R.judge(dict(_B, state=None, why="", complete_clone=True,
                     pack_mib=R.PACK_WARN_MIB + 1,
                     disk_mb_day=R.GROWTH_WARN_MB_DAY + 1))
ck("   ...and the judge says OK at that baseline, BAD just past both bars",
   _at_base["state"] == "OK" and _over["state"] == "BAD"
   and "MiB bar" in _over["why"] and "MB/day bar" in _over["why"],
   "baseline -> %s %r · over -> %s %r"
   % (_at_base["state"], _at_base["why"], _over["state"], _over["why"][:120]))
if _LIVE:
    note("live headroom: pack %.1f of %.0f MiB · packed growth %.2f of %.0f "
         "MB/day (%s)"
         % (_LIVE["pack_mib"], R.PACK_WARN_MIB, _LIVE["disk_mb_day"],
            R.GROWTH_WARN_MB_DAY, _LIVE["state"]))

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

# 🔴 `[2026-09-28]` ~~`bool(_h) and ...`~~ required PRODUCTION to still
#    hold the defect the watcher flags — a gzip rewritten in place. Moving
#    those writers to dated archives (the design repo_watch recommends,
#    rule 285), or a quiet week, would have turned it red on correct code.
#    ✅ The planted case is the bench above (its board.json.gz is flagged,
#    every run). On the live repo the PROPERTY is still checked on every
#    path it flags; an empty list is reported, never asserted.
if _LIVE:
    _h = [t for t in _LIVE["top"] if t["hostile"]]
    ck("⚠️ and on the LIVE repo every path it flags is a gzip with several "
       "versions — a real path, not a number",
       all(p["path"].endswith(".gz") and p["versions"] > 1 for p in _h),
       "⛔ a number with no cause is a number nobody can act on. "
       "flagged: %s" % [(p["path"], p["versions"]) for p in _h][:3])
    note("live: %d path(s) flagged as rewritten in place%s"
         % (len(_h), (" — e.g. %s" % [p["path"] for p in _h][:3]) if _h else
            " — none this window (the bench above is the planted case)"))

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


# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 `[2026-11-17]` A BRANCH AUTHORED BEFORE THE WINDOW AND MERGED IN IT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ Issue #330's per-day series summed 122.24 MB against an 84.7 MB window: a
#    side-branch commit authored before the base (the HC champion branch) became
#    a day of its own, and the next day's range reached back past the base. The
#    first bench (§1) is one straight line, so it never had this shape.
def _merge(d, branch, days_ago):
    when = (datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    subprocess.run(["git", "-C", d, "merge", "-q", "--no-ff", "-m", "merge", branch],
                   check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when))


def _bench_merge():
    d = tempfile.mkdtemp(prefix="repowatch-merge-")
    _g("init", "-q", d, cwd="/")
    _g("-C", d, "config", "user.email", "t@t")
    _g("-C", d, "config", "user.name", "t")
    _g("-C", d, "config", "core.autocrlf", "false")
    W = R.WINDOW_DAYS
    _commit(d, {"README": b"anchor"}, W + 13)
    main = _g("-C", d, "rev-parse", "--abbrev-ref", "HEAD").strip()
    _g("-C", d, "branch", "side")
    # main, before the window: stored already, so never part of it
    _commit(d, {"data/latest/old.json.gz": gzip.compress(os.urandom(200000))}, W + 5)
    _commit(d, {"README": b"the base"}, W + 2)
    # the branch: authored BEFORE the base, merged inside the window
    _g("-C", d, "checkout", "-q", "side")
    _commit(d, {"data/side/feature.json.gz": gzip.compress(os.urandom(30000))}, W + 8)
    _g("-C", d, "checkout", "-q", main)
    for n in range(3):
        _commit(d, {"data/latest/board.json.gz": gzip.compress(os.urandom(40000)),
                    "data/2026-01-0%d/k/0100.json.gz" % (n + 1): gzip.compress(os.urandom(20000))},
                5 - n)
    _merge(d, "side", 2)
    _commit(d, {"data/latest/board.json.gz": gzip.compress(os.urandom(40000))}, 1)
    _g("-C", d, "gc", "-q", "--prune=now")
    return d


_MB = _bench_merge()
_M = R.judge(R.measure(root=_MB))
_MRAW, _MDISK = _independent(_MB)
_mser = _M.get("series", [])
ck("⚠️ the merge bench produced a readable report, its window based on main's own commit",
   _M["state"] in ("OK", "BAD")
   and _g("-C", _MB, "show", "%s:README" % R.window_base(root=_MB)) == "the base"
   and abs(_M.get("disk_mb", -1) - _MDISK / 1e6) < 1e-6,
   "⛔ rule 67: every check below is asked of this report. state=%s why=%s"
   % (_M["state"], _M.get("why", "")[:120]))
ck("🔴🔴 the per-day series SUMS TO THE WINDOW TOTAL with a merged branch in it",
   abs(sum(d["disk_mb"] for d in _mser) - _MDISK / 1e6) < 1e-6,
   "⛔ #330: 122.24 MB of days against an 84.7 MB window. series=%.6f window=%.6f MB, days %s"
   % (sum(d["disk_mb"] for d in _mser), _MDISK / 1e6,
      [(d["day"], round(d["disk_mb"], 4)) for d in _mser]))
ck("🔴 ...and no day in it is older than the window's base",
   bool(_mser) and min(d["day"] for d in _mser) >= _M.get("base_date", "9999"),
   "⛔ a day before the base is the branch's author date, and the day after it counts "
   "what the base already stored. base %s, days %s"
   % (_M.get("base_date"), [d["day"] for d in _mser]))
_count = int(_g("-C", _MB, "rev-list", "--count",
                "%s..HEAD" % R.window_base(root=_MB)).strip())
eq(sum(d["commits"] for d in _mser), _count,
   "   ...and its commits are every commit the window introduced, the branch's on its merge day")


# ── 6b. the window's base is MAIN's commit at the cutoff, never a branch's ──────────
# 🔴 `[2026-11-17]` `window_base` walked every parent. When a PR branch's commit was the
#    newest before the cutoff it became the base, and `base..HEAD` still held main's own
#    commits from between the fork point and the cutoff, stored BEFORE the window: the
#    window total, a series day older than the base, and the tree growth (against the
#    branch's tree) all counted them. The bench above has main's commit (W+2) newer than
#    the branch's (W+8), so it never had this shape; this one is built to.
def _bench_side_base():
    d = tempfile.mkdtemp(prefix="repowatch-sidebase-")
    _g("init", "-q", d, cwd="/")
    _g("-C", d, "config", "user.email", "t@t")
    _g("-C", d, "config", "user.name", "t")
    _g("-C", d, "config", "core.autocrlf", "false")
    W = R.WINDOW_DAYS
    _commit(d, {"README": b"anchor"}, W + 13)
    _commit(d, {"README": b"fork point"}, W + 6)
    main = _g("-C", d, "rev-parse", "--abbrev-ref", "HEAD").strip()
    _g("-C", d, "branch", "side")
    # main's last commit before the cutoff: 300 kB stored already, so never the window's
    _commit(d, {"data/latest/old.json.gz": gzip.compress(os.urandom(300000))}, W + 3)
    m2 = _g("-C", d, "rev-parse", "HEAD").strip()
    # a PR branch's commit, also before the cutoff but NEWER than main's last one there
    _g("-C", d, "checkout", "-q", "side")
    feature = b"x = 1"
    _commit(d, {"src/feature.py": feature}, W + 0.5)
    _g("-C", d, "checkout", "-q", main)
    _commit(d, {"data/latest/board.json.gz": gzip.compress(os.urandom(40000))}, 5)
    _merge(d, "side", 2)
    board = gzip.compress(os.urandom(40000))
    _commit(d, {"data/latest/board.json.gz": board}, 1)
    _g("-C", d, "gc", "-q", "--prune=now")
    # the tree main gained since m2, by construction: the branch's file and the board
    return d, m2, len(feature) + len(board)


_SB, _SB_M2, _SB_GROW = _bench_side_base()
_S = R.judge(R.measure(root=_SB))
_sfp = _g("-C", _SB, "rev-list", "--first-parent", "HEAD").split()
_sany = _g("-C", _SB, "rev-list", "-1", "--before=%d days ago" % R.WINDOW_DAYS, "HEAD").strip()
_sbase = R.window_base(root=_SB)
_SRAW, _SDISK = _independent(_SB, base=_SB_M2)
_sser = _S.get("series", [])
_stop = [t["path"] for t in _S.get("top", [])]
ck("⚠️ the side-base bench has its shape: a readable report, and the newest commit of ANY "
   "parent before the cutoff is the branch's",
   _S["state"] in ("OK", "BAD") and _sany and _sany not in _sfp,
   "⛔ rule 67: if main's commit were the newest, every check below would pass on the old "
   "code too. state=%s why=%s any-parent=%s" % (_S["state"], _S.get("why", "")[:120], _sany[:9]))
ck("🔴🔴 the window's base is MAIN's own commit at the cutoff, never the branch's",
   _sbase == _SB_M2 and _sbase in _sfp
   and _S.get("base_date") == _g("-C", _SB, "log", "-1", "--format=%cd", "--date=short",
                                 _SB_M2).strip(),
   "base %s (main's commit at the cutoff %s), base_date %s"
   % ((_sbase or "")[:9], _SB_M2[:9], _S.get("base_date")))
ck("🔴🔴 ...so the window total is only what main took in INSIDE the window",
   abs(_S.get("disk_mb", -1) - _SDISK / 1e6) < 1e-6
   and "data/latest/old.json.gz" not in _stop,
   "⛔ old.json.gz was stored before the cutoff. reported %.6f MB, main's window %.6f MB, top %s"
   % (_S.get("disk_mb", -1), _SDISK / 1e6, _stop))
ck("🔴 ...the days sum to it, and none is older than the base",
   bool(_sser) and abs(sum(d["disk_mb"] for d in _sser) - _SDISK / 1e6) < 1e-6
   and min(d["day"] for d in _sser) >= _S.get("base_date", "9999"),
   "base %s, days %s" % (_S.get("base_date"),
                         [(d["day"], round(d["disk_mb"], 4)) for d in _sser]))
ck("🔴 ...and the tree's growth is HEAD's tree against MAIN's at the cutoff",
   abs(_S.get("tree_mb_day", -1) - _SB_GROW / 1e6 / R.WINDOW_DAYS) < 1e-9,
   "⛔ against the branch's tree it counts main's pre-window files as growth. report %.6f "
   "MB/day, by construction %.6f" % (_S.get("tree_mb_day", -1), _SB_GROW / 1e6 / R.WINDOW_DAYS))
shutil.rmtree(_SB, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 `[2026-11-17]` THE WORKING TREE BESIDE THE PACK, EACH WITH ITS OWN LIMIT")
# ══════════════════════════════════════════════════════════════════════
# ⛔ #330 called 1 GiB of pack "a limit". It is GitHub Pages' RECOMMENDATION for a
#    source repository; the HARD limit is the published site's 1 GB, and the site is
#    built from the working tree (a one-commit-deep checkout), which history never
#    enters. The tree's size is asked of the files on disk here, not of git.
def _walk_bytes(d):
    tot = 0
    for dp, dns, fns in os.walk(d):
        dns[:] = [x for x in dns if x != ".git"]
        tot += sum(os.path.getsize(os.path.join(dp, f)) for f in fns if f != ".git")
    return tot


_wt = tempfile.mkdtemp(prefix="repowatch-base-")
_g("-C", _MB, "worktree", "add", "-q", "--detach", _wt + "/b", R.window_base(root=_MB))
_tree_head, _tree_base = _walk_bytes(_MB), _walk_bytes(_wt + "/b")
_g("-C", _MB, "worktree", "remove", "--force", _wt + "/b")
shutil.rmtree(_wt, ignore_errors=True)
ck("🔴 the report's working tree IS the bytes of the checked-out files",
   _M.get("tree_bytes") == _tree_head and _tree_head > 0,
   "⛔ asked of the files, not of git. report=%s on disk=%d" % (_M.get("tree_bytes"), _tree_head))
ck("🔴 ...and its growth is the HEAD tree against the base's, over the window",
   abs(_M.get("tree_mb_day", -1) - (_tree_head - _tree_base) / 1e6 / R.WINDOW_DAYS) < 1e-9
   and _M.get("tree_mb_day", 0) > 0,
   "report %.6f MB/day; files on disk: %d -> %d bytes"
   % (_M.get("tree_mb_day", -1), _tree_base, _tree_head))
# GitHub: "Published GitHub Pages sites may be no larger than 1 GB" (read as 10^9 bytes, the
#    nearer reading). Written here, not read from the module, so the module cannot move it.
ck("   ...with a projection to the site's 1 GB",
   abs(_M.get("tree_days_to_limit", -1)
       - (1e9 - _tree_head) / 1e6 / _M.get("tree_mb_day", 1)) < 1e-6,
   "got %s" % _M.get("tree_days_to_limit"))
_txt = R.render(_M)
_lines = _txt.splitlines()
_pk = [l for l in _lines if l.startswith("| pack to")]
_tr = [l for l in _lines if l.startswith("| working tree to")]
ck("🔴🔴 the report names BOTH figures: the pack and the working tree",
   ("%.2f MiB" % _M["pack_mib"]) in _txt and ("%.1f MB" % (_tree_head / 1e6)) in _txt,
   "⛔ the pack alone is the number #330 printed. %s" % _txt[:300])
ck("🔴🔴 ...the pack's 1 GiB is called a RECOMMENDATION, not a hard limit, beside GitHub's 10 GB",
   len(_pk) == 1 and "recommended" in _pk[0] and "not a hard limit" in _pk[0]
   and "10 GB" in _pk[0],
   "⛔ #330 said 'to 1 GiB' as if it were a wall. %s" % _pk)
ck("🔴🔴 ...and the working tree's 1 GB is called what it is: the Pages site's HARD limit",
   len(_tr) == 1 and "1 GB" in _tr[0] and "hard limit" in _tr[0] and "days" in _tr[0],
   "⛔ the limit that is enforced is the one #330 never printed. %s" % _tr)
_ue = R.render(dict(_M, tree_error="CalledProcessError: planted"))
ck("⛔ a tree that cannot be read is SAID, never left out",
   "could not be read: CalledProcessError: planted" in _ue and "| working tree to" not in _ue,
   _ue[:300])

# ⛔ AND measure() SAYS IT, DRIVEN: the check above plants `tree_error` in the report, so
#    measure() could swallow the error and every line above would still pass. Here git's
#    tree read fails for real inside measure(): every tree, then only the base's.
# (getattr: a module with no tree reader at all fails the checks below, rather than
#  stopping this file before them)
_real_tree_bytes = getattr(R, "tree_bytes", None)


def _all_trees_fail(rev="HEAD", root=R.ROOT):
    raise subprocess.CalledProcessError(128, ["git", "ls-tree", rev], "", "planted")


def _base_tree_fails(rev="HEAD", root=R.ROOT):
    if rev != "HEAD":
        raise subprocess.CalledProcessError(128, ["git", "ls-tree", rev], "", "planted")
    return _real_tree_bytes(rev, root)


def _render_or_why(rep):
    try:
        return R.render(rep)
    except Exception as e:  # a report that cannot be rendered is a failure, said as one
        return "render raised %s: %s" % (type(e).__name__, e)


try:
    R.tree_bytes = _all_trees_fail
    _TE = R.judge(R.measure(root=_MB))
    R.tree_bytes = _base_tree_fails
    _TB = R.judge(R.measure(root=_MB))
finally:
    R.tree_bytes = _real_tree_bytes
for _lbl, _rep in (("no tree can be read", _TE), ("the base's tree cannot be read", _TB)):
    _t = _render_or_why(_rep)
    ck("⛔ when %s, measure() keeps the error on the report and the report says it" % _lbl,
       _rep["state"] in ("OK", "BAD")
       and _rep.get("tree_error", "").startswith("CalledProcessError: ")
       and "| working tree | ⚠️ could not be read: CalledProcessError" in _t
       and "| working tree to" not in _t and "| pack to" in _t,
       "⛔ an unread tree left out is the pack-only report #330 printed. state=%s "
       "tree_error=%r %s" % (_rep["state"], _rep.get("tree_error"), _t[:300]))

# GitHub: a repository's on-disk size "10 GB", recommended (10^9 bytes). Written here, not
#    read from the module, as the site's 1 GB is above.
_rec = (10e9 - _M["pack_mib"] * 1048576.0) / 1e6 / _M["disk_mb_day"]
ck("🔴 the days to GitHub's 10 GB repository recommendation are that projection, printed",
   abs(_M.get("days_to_repo_rec", -1) - _rec) <= 1e-9 * max(1.0, _rec)
   and len(_pk) == 1 and ("~%.0f days at this rate" % _rec) in _pk[0],
   "report %s, by hand %.3f days. %s" % (_M.get("days_to_repo_rec"), _rec, _pk))
_tree_first = R.render(dict(_M, tree_days_to_limit=10.0, days_to_limit=500.0))
_pack_first = R.render(dict(_M, tree_days_to_limit=500.0, days_to_limit=10.0))
ck("🔴 ...and the report names the size that reaches its line FIRST, either way round",
   "the **working tree** reaches its line first" in _tree_first
   and "the **pack** reaches its line first" in _pack_first,
   "⛔ an inverted comparison sends Sam to the wrong size. tree nearer -> %r; pack nearer -> %r"
   % ([l for l in _tree_first.splitlines() if "reaches its line" in l][:1],
      [l for l in _pack_first.splitlines() if "reaches its line" in l][:1]))

shutil.rmtree(_MB, ignore_errors=True)
