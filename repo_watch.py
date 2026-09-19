#!/usr/bin/env python3
"""
IS THIS REPOSITORY GROWING IN A WAY THAT WILL BECOME A PROBLEM, AND WHAT
IS DOING IT? NOTHING ASKED.

🔴🔴 THE FIGURE IN CIRCULATION WAS WRONG, AND THAT IS WHY THIS IS A
WATCHER AND NOT A NUMBER IN A COMMENT. "105 MB, ~3.5 MB/day" was repeated
for a week and had never been measured. `[measured 2026-09-19 on a FULL
clone of main]`:

    pack                     105.14 MiB   (25,892 objects)
    raw blob bytes added      15.15 MB/day   <- what a `du` diff suggests
    ON-DISK (packed) growth    5.34 MB/day   <- what the repo actually pays

⛔ THEY DIFFER BY 2.84x, AND MEASURING THE WRONG ONE IS THE WHOLE TRAP.
Git deltas plain text extremely well and **cannot delta a gzip at all** —
a gzip's raw and on-disk sizes are identical, so every rewrite is stored
in full. A watcher summing raw blob sizes cries wolf at 15; one reading
the working tree sleeps through everything. ✅ This reads
`objectsize:disk` over the objects introduced in the window, which is
what git actually stores.

🔴 AND THE BREAKDOWN IS THE STORY, NOT THE TOTAL:

    ext          share of RAW     share of PACKED
    .json.gz          33.1%            79.6%     <- one third written,
    .json             53.4%             8.7%        four fifths kept
    .py                8.4%             8.0%

➡️ **RULE 285 IN PRODUCTION, AT SCALE.** Plain JSON is half of what gets
written and a twelfth of what gets kept; gzip is a third of what gets
written and four fifths of what gets kept.

══════════════════════════════════════════════════════════════════════
🔴 IT NAMES THE CAUSE, BECAUSE A NUMBER WITH NO CAUSE IS A NUMBER NOBODY
   CAN ACT ON.
══════════════════════════════════════════════════════════════════════
⛔ "The repo grew 5 MB today" is not actionable. "7.13 MB of the last
week went into `data/ncaaf/latest/schedule-2026.json.gz`, which is a gzip
rewritten in place and therefore stored in full every single time" is.

⚠️ AND "REWRITTEN IN PLACE" IS MEASURED, NOT PATTERN-MATCHED. A path
convention (`/latest/`) is a guess about behaviour; the number of
DISTINCT BLOB VERSIONS the path has inside the window is the behaviour
itself. A dated archive is written once and has exactly one version — it
is the correct design and is never flagged. A file rewritten every run
has many, and if it is a gzip then git stored every one of them in full.

══════════════════════════════════════════════════════════════════════
⛔ THE THRESHOLDS ARE WELL CLEAR OF THE MEASURED BASELINE.
══════════════════════════════════════════════════════════════════════
`CLAUDE.md`: *a guard that fires on correct code is the other failure,
not a safe one.* 105 MiB and 5.34 MB/day are the HEALTHY state this was
measured from, so the bars sit far above them:

    pack   > 500 MiB          ~5x today
    growth > 20 MB/day        ~4x today, sustained across the window

⚠️ THE WINDOW IS 7 DAYS AND THE SERIES IS PRINTED, NOT JUST THE MEAN, so
a quiet day cannot clear a real trend and a reader can see the shape.

══════════════════════════════════════════════════════════════════════
🔴 IT FAILS CLOSED ON A CLONE THAT CANNOT ANSWER, AND THAT MATTERS HERE
   MORE THAN USUAL.
══════════════════════════════════════════════════════════════════════
⛔ `actions/checkout` DEFAULTS TO `fetch-depth: 1`, AND IN THAT CLONE
BOTH FIGURES ARE WRONG. `git count-objects` reports the size of the one
commit that was fetched — measured here, **43.39 MiB against a real
105.14 MiB** — and there is no history at all to compute a window over.
⚠️ A watcher reporting 43 MiB and "no growth" would be reassuring,
constant, and false. So:

    shallow clone        -> size is UNREADABLE, never OK
    history < window     -> growth is UNREADABLE, never OK

`UNREADABLE` exits 2, and the workflow leaves any open issue ALONE on a 2
— "I could not look" is not "the repo is fine".

⚠️ No network, no credits, no API. It asks git about the checkout it is
standing in.
"""
import collections
import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# ── the bars, both far above the measured baseline ────────────────────
PACK_WARN_MIB = 500.0        # ~5x the 105.14 MiB measured 2026-09-19
GROWTH_WARN_MB_DAY = 20.0    # ~4x the 5.34 MB/day measured 2026-09-19
WINDOW_DAYS = 7
# ⚠️ GitHub's soft warning for a repository. Used ONLY for the projection,
#    which is labelled a projection wherever it is printed.
LIMIT_GIB = 1.0
TOP_N = 12
GIT_TIMEOUT = 300


def _git(*args, **kw):
    """-> stdout. Raises on failure; callers turn that into UNREADABLE."""
    return subprocess.run(("git",) + args, cwd=kw.get("cwd", ROOT),
                          capture_output=True, text=True, check=True,
                          timeout=GIT_TIMEOUT).stdout


def _bad(why):
    return {"state": "UNREADABLE", "why": why}


def clone_is_complete(root=ROOT):
    """⛔ A SHALLOW CLONE CANNOT BE ASKED HOW BIG THE REPOSITORY IS."""
    return not os.path.exists(os.path.join(root, ".git", "shallow"))


def pack_mib(root=ROOT):
    """size-pack, in MiB, from git's own accounting."""
    out = _git("count-objects", "-v", cwd=root)
    got = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            got[k.strip()] = v.strip()
    # ⚠️ `-v` reports KiB; `-vH` reports a human string that would have to
    #    be parsed back. The machine-readable one is the one to read.
    return int(got["size-pack"]) / 1024.0, int(got.get("in-pack", 0))


def window_base(days=WINDOW_DAYS, root=ROOT):
    """The newest commit at least `days` old, or None if history is short."""
    out = _git("rev-list", "-1", "--before=%d days ago" % days, "HEAD",
               cwd=root).strip()
    return out or None


def measure(days=WINDOW_DAYS, root=ROOT, top_n=TOP_N):
    """What the repo pays, and what is doing it. -> report dict."""
    rep = {"window_days": days}
    try:
        rep["complete_clone"] = clone_is_complete(root)
        rep["pack_mib"], rep["objects"] = pack_mib(root)
    except Exception as e:
        return _bad("git could not be asked: %s: %s" % (type(e).__name__, e))
    # ⛔ THE SHALLOW CASE IS ANSWERED FIRST, AND THE ORDER IS THE POINT.
    #    A shallow clone ALSO has no window, so the window message fired
    #    first and the reader was told "no commit is 7 days old" — true,
    #    but it names a symptom and not the fix. Both states are
    #    UNREADABLE either way; only one of them tells you to change
    #    `fetch-depth`.
    if not rep["complete_clone"]:
        return _bad("this is a SHALLOW clone, so `size-pack` is the size of "
                    "what was fetched and not of the repository — measured "
                    "as 43.39 MiB against a real 105.14 MiB — and a "
                    "`fetch-depth: 1` checkout has no history to measure a "
                    "window over. Check out with `fetch-depth: 0`.")
    try:
        base = window_base(days, root)
    except Exception as e:
        return _bad("git could not be asked: %s: %s" % (type(e).__name__, e))
    if not base:
        return _bad("no commit is %d days old in this checkout — there is no "
                    "window to measure. A `fetch-depth: 1` checkout has one "
                    "commit and cannot answer this." % days)
    rep["base"] = base[:8]
    try:
        rep["base_date"] = _git("log", "-1", "--format=%ad", "--date=short",
                                base, cwd=root).strip()
        # objects reachable from HEAD but not from the base == introduced
        # in the window, with the path each was seen at.
        paths = {}
        for line in _git("rev-list", "--objects", "%s..HEAD" % base,
                         cwd=root).splitlines():
            sha, _, path = line.partition(" ")
            if path:
                paths.setdefault(sha, path)
        if not paths:
            return _bad("no objects were introduced in the last %d days — "
                        "that is not a repository this check can read" % days)
        # ⛔ RAW **AND** ON-DISK, because the gap between them is the whole
        #    point and a report carrying only one of them cannot show it.
        proc = subprocess.run(
            ["git", "cat-file",
             "--batch-check=%(objectname) %(objecttype) %(objectsize) "
             "%(objectsize:disk)"],
            cwd=root, input="\n".join(paths) + "\n", capture_output=True,
            text=True, timeout=GIT_TIMEOUT)
    except Exception as e:
        return _bad("git could not be asked: %s: %s" % (type(e).__name__, e))

    raw = disk = 0
    by_ext_raw, by_ext_disk = collections.Counter(), collections.Counter()
    by_path = collections.Counter()
    versions = collections.Counter()
    for line in proc.stdout.splitlines():
        f = line.split()
        if len(f) != 4 or f[1] != "blob":
            continue
        r, d = int(f[2]), int(f[3])
        path = paths.get(f[0], "")
        raw += r
        disk += d
        by_ext_raw[_ext(path)] += r
        by_ext_disk[_ext(path)] += d
        by_path[path] += d
        versions[path] += 1
    if not disk:
        return _bad("no blob bytes were introduced in the last %d days" % days)

    rep["raw_mb"] = raw / 1e6
    rep["disk_mb"] = disk / 1e6
    rep["raw_mb_day"] = raw / 1e6 / days
    rep["disk_mb_day"] = disk / 1e6 / days
    rep["raw_over_disk"] = raw / float(disk)
    rep["by_ext"] = [
        {"ext": e, "raw_mb": by_ext_raw[e] / 1e6, "disk_mb": by_ext_disk[e] / 1e6,
         "raw_pct": 100.0 * by_ext_raw[e] / raw,
         "disk_pct": 100.0 * by_ext_disk[e] / disk}
        for e, _ in by_ext_disk.most_common(6)]
    rep["top"] = [
        {"path": p, "disk_mb": d / 1e6, "pct": 100.0 * d / disk,
         "versions": versions[p], "hostile": _hostile(p, versions[p])}
        for p, d in by_path.most_common(top_n)]
    rep["hostile_pct"] = sum(t["pct"] for t in rep["top"] if t["hostile"])
    # ⚠️ THE PER-DAY SERIES, so a quiet day cannot hide a trend and the
    #    reader sees the shape rather than one scalar.
    rep["series"] = _series(base, days, root)
    # ⚠️ A PROJECTION, AND IT SAYS SO WHEREVER IT IS PRINTED.
    if rep["complete_clone"] and rep["disk_mb_day"] > 0:
        left = LIMIT_GIB * 1024.0 - rep["pack_mib"]
        rep["days_to_limit"] = left * 1.048576 / rep["disk_mb_day"]
    return rep


def _ext(path):
    base = path.rsplit("/", 1)[-1]
    if base.endswith(".json.gz"):
        return ".json.gz"
    return "." + base.rsplit(".", 1)[-1] if "." in base else "(none)"


def _hostile(path, versions):
    """⛔ MEASURED, NOT PATTERN-MATCHED.

    A gzip git had to store MORE THAN ONCE inside the window is one that
    is rewritten in place — and because git cannot delta a gzip, every one
    of those rewrites was stored in full.
    ✅ A dated archive has exactly one version and is never flagged: it is
    written once, there is nothing to delta against, and it is the correct
    design (rule 285).
    """
    return path.endswith(".gz") and versions > 1


def _series(base, days, root=ROOT):
    """Packed bytes INTRODUCED per day across the window.

    ⛔ `rev-list --objects --no-walk <day's commits>` IS THE WRONG
    QUESTION and it was the first thing written here. It lists every
    object REACHABLE from those commits — the whole tree — not the ones
    they introduced. Measured: it produced 31-41 MB per day against a
    37.38 MB window TOTAL, i.e. roughly 8x the real figure, every day,
    and the shape looked perfectly plausible.
    ✅ The right question is the same one the window itself asks, one day
    at a time: objects in `<end of previous day>..<end of this day>`.
    ⚠️ `test_repo_watch.py` asserts the series RECONCILES with the window
    total, which is what catches this class of mistake rather than a
    reader noticing the numbers look large.
    """
    out = []
    try:
        log = _git("log", "--format=%H %ad", "--date=short",
                   "%s..HEAD" % base, cwd=root).splitlines()
    except Exception:
        return out
    # oldest first; the last commit seen on a day is that day's end
    day_end, order = {}, []
    for line in reversed(log):
        sha, _, day = line.partition(" ")
        day = day.strip()
        if day not in day_end:
            order.append(day)
        day_end[day] = sha
    prev = base
    counts = collections.Counter()
    for line in log:
        counts[line.partition(" ")[2].strip()] += 1
    for day in order:
        try:
            names = [l.split(" ", 1)[0] for l in
                     _git("rev-list", "--objects",
                          "%s..%s" % (prev, day_end[day]),
                          cwd=root).splitlines()]
            if names:
                proc = subprocess.run(
                    ["git", "cat-file",
                     "--batch-check=%(objecttype) %(objectsize:disk)"],
                    cwd=root, input="\n".join(names) + "\n",
                    capture_output=True, text=True, timeout=GIT_TIMEOUT)
                tot = sum(int(f[1]) for f in
                          (l.split() for l in proc.stdout.splitlines())
                          if len(f) == 2 and f[0] == "blob")
            else:
                tot = 0
        except Exception:
            continue
        out.append({"day": day, "disk_mb": tot / 1e6,
                    "commits": counts[day]})
        prev = day_end[day]
    return out


def judge(rep):
    """-> the same dict with `state` and `why` decided."""
    if rep.get("state") == "UNREADABLE":
        return rep
    # ⛔ A SHALLOW CLONE'S PACK SIZE IS NOT THE REPOSITORY'S SIZE, and
    #    reporting it as one is worse than reporting nothing: it is small,
    #    stable and wrong, which reads exactly like health.
    if not rep.get("complete_clone"):
        rep["state"] = "UNREADABLE"
        rep["why"] = ("this is a SHALLOW clone, so `size-pack` is the size "
                      "of what was fetched and not of the repository — "
                      "measured here as 43.39 MiB against a real 105.14 "
                      "MiB. Check out with `fetch-depth: 0` to ask this.")
        return rep
    bad = []
    if rep["pack_mib"] > PACK_WARN_MIB:
        bad.append("the pack is %.1f MiB, over the %.0f MiB bar"
                   % (rep["pack_mib"], PACK_WARN_MIB))
    if rep["disk_mb_day"] > GROWTH_WARN_MB_DAY:
        bad.append("packed growth is %.2f MB/day over %d days, over the "
                   "%.0f MB/day bar"
                   % (rep["disk_mb_day"], rep["window_days"],
                      GROWTH_WARN_MB_DAY))
    rep["state"] = "BAD" if bad else "OK"
    rep["why"] = " and ".join(bad)
    return rep


def render(rep):
    o = []
    if rep["state"] == "UNREADABLE":
        o.append("## ⚠️ The repository size could not be read")
        o.append("")
        o.append(rep["why"])
        o.append("")
        o.append("⛔ This is **not** a statement that the repository is "
                 "fine. Nothing was measured.")
        return "\n".join(o)
    o.append("## %s Repository size" % ("🔴" if rep["state"] == "BAD" else "✅"))
    o.append("")
    if rep["state"] == "BAD":
        o.append("**%s.**" % rep["why"])
        o.append("")
    o.append("| | |")
    o.append("|---|---|")
    o.append("| pack | **%.2f MiB** (%s objects) |"
             % (rep["pack_mib"], "{:,}".format(rep["objects"])))
    o.append("| packed growth | **%.2f MB/day** over %d days |"
             % (rep["disk_mb_day"], rep["window_days"]))
    o.append("| raw blob bytes | %.2f MB/day (%.2fx the packed figure) |"
             % (rep["raw_mb_day"], rep["raw_over_disk"]))
    if "days_to_limit" in rep:
        o.append("| to %.0f GiB | ~%.0f days — **a projection at today's "
                 "rate**, not a forecast |"
                 % (LIMIT_GIB, rep["days_to_limit"]))
    o.append("")
    o.append("⛔ The raw figure is what a `du` diff would show. The packed "
             "figure is what the repository pays, and they differ because "
             "git deltas text and **cannot delta a gzip at all**.")
    o.append("")
    o.append("### Per day")
    o.append("")
    o.append("```")
    for d in rep.get("series", []):
        o.append("  %s  %7.2f MB  (%d commits)"
                 % (d["day"], d["disk_mb"], d["commits"]))
    o.append("```")
    o.append("")
    o.append("### What is growing it")
    o.append("")
    o.append("| packed | share | path |")
    o.append("|---:|---:|---|")
    for t in rep.get("top", []):
        o.append("| %.2f MB | %.1f%% | `%s`%s |"
                 % (t["disk_mb"], t["pct"], t["path"],
                    " 🔴 **rewritten in place, %d versions — a gzip git "
                    "stored in full every time**" % t["versions"]
                    if t["hostile"] else ""))
    o.append("")
    if rep.get("hostile_pct"):
        o.append("🔴 **%.1f%% of the listed growth is gzip files rewritten "
                 "in place.** Git cannot delta a gzip, so each rewrite is "
                 "stored whole. ⚠️ Dated archives are written once and are "
                 "NOT flagged — those are the correct design (rule 285). "
                 "⛔ Changing a stored format is a separate, careful task."
                 % rep["hostile_pct"])
    return "\n".join(o)


def main():
    rep = judge(measure())
    print(render(rep))
    if rep["state"] == "UNREADABLE":
        sys.stderr.write("could not read the repository size: %s\n"
                         % rep.get("why", "?"))
        return 2
    if rep["state"] == "OK":
        sys.stderr.write("OK  pack %.2f MiB  growth %.2f MB/day over %dd\n"
                         % (rep["pack_mib"], rep["disk_mb_day"],
                            rep["window_days"]))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
