#!/usr/bin/env python3
"""push_retry.sh lands every pass, even when two runs race on one file.

🔴🔴 `[measured 2026-09-21]` The converge loop's
`git pull --rebase --autostash && git push` (x3) left a conflicted rebase
half-done and fell through SILENTLY. Whole passes never reached `main`:
the audits' "dark crons" (they fired every day) and the "~50% unrecorded
Odds spend" (the paid snapshot never landed, so the next run bought it
again). This drives two real clones against one bare remote.

# @vacuity 🔴🔴 a conflicting pass is replayed, not lost
#   file: push_retry.sh
#   find:     git rebase --abort >/dev/null 2>&1 || true
#   with:     true
#
# @vacuity ⛔ the converge loop pushes through the helper
#   file: .github/workflows/collect.yml
#   find: bash push_retry.sh "converge pass $PASS"
#   with: true "converge pass $PASS"
#
# @vacuity 🔴🔴 a rebased pass keeps a paid snapshot the remote already holds
#   file: push_retry.sh
#   find: keep_both "$(git rev-parse FETCH_HEAD)"
#   with: true
#
# @vacuity 🔴🔴 ...and so does a replayed pass
#   file: push_retry.sh
#   find: keep_both "$tip"
#   with: true
#
# @vacuity 🔴🔴 the first run's file stays at its own name
#   file: credits.py
#   find: for rel, blob in ((free, mine), (path, theirs)):
#   with: for rel, blob in ((free, mine),):
#
# @vacuity 🔴 a third run takes the next free -n, never a taken one
#   file: credits.py
#   find: while (f"{stem}-{n}.json.gz" in taken
#   with: while False and (f"{stem}-{n}.json.gz" in taken
#
# @vacuity ⛔ only a PAID kind is kept twice
#   file: credits.py
#   find: for _path, _free in keep_both(sys.argv[2], _kinds):
#   with: for _path, _free in keep_both(sys.argv[2], _kinds + ("news",)):
#
# @vacuity 🔴🔴 [2026-10-28] a rebased pass never lands a heartbeat that vouches for nothing
#   file: push_retry.sh
#   find:     settle "$(git rev-parse FETCH_HEAD)"
#   with:     true
#
# @vacuity 🔴🔴 ...nor does a replayed pass
#   file: push_retry.sh
#   find:       settle "$tip"
#   with:       true
#
# @vacuity 🔴 the tip's heartbeat is kept when IT vouches for the file that lands
#   file: freshness.py
#   find:         if theirs is not None and _vouched(doc(theirs), name, buf, keys):
#   with:         if False:
#
# @vacuity 🔴 one that vouches for nothing, with none on the tip, is removed
#   file: freshness.py
#   find:             git("rm", "-q", "--", rel)
#   with:             pass
#
# @vacuity 🔴🔴 [2026-11-01] a rebased watchdog commit gives way
#   file: push_retry.sh
#   find:     give_way "$(git rev-parse FETCH_HEAD)"
#   with:     true
#
# @vacuity 🔴🔴 ...and so does a replayed one
#   file: push_retry.sh
#   find:       give_way "$tip"
#   with:       true
#
# @vacuity 🔴🔴 only this step's commit gives way, not a pass under it
#   file: push_retry.sh
#   find: done <<< "$(git diff --name-only --no-renames "$own^" "$own")"
#   with: done <<< "$(git diff --name-only --no-renames "$base" "$own")"
#
# @vacuity ⛔ a converge pass is not a repair
#   file: push_retry.sh
#   find: [ "$label" = "$REPAIR_LABEL" ] || return 0
#   with: true
#
# @vacuity 🔴 the rule keys on the label the commit step passes
#   file: push_retry.sh
#   find: REPAIR_LABEL="health report"
#   with: REPAIR_LABEL="health note"
#
# @vacuity 🔴 ...and the commit step passes it
#   file: .github/workflows/collect.yml
#   find: bash push_retry.sh "health report" && exit 0
#   with: bash push_retry.sh "health note" && exit 0
#
# @vacuity 🔴 the health report always lands
#   file: push_retry.sh
#   find: [ -n "$p" ] && [ "$p" != "$HEALTH_PATH" ] || continue
#   with: [ -n "$p" ] || continue
#
# @vacuity 🔴 the file that always lands is the one the watchdog writes
#   file: push_retry.sh
#   find: HEALTH_PATH="data/latest/health.json"
#   with: HEALTH_PATH="data/latest/healthz.json"
#
# @vacuity 🔴 ...from the watchdog's side too
#   file: watchdog.py
#   find: HEALTH = "data/latest/health.json"
#   with: HEALTH = "data/latest/healthz.json"
#
# @vacuity 🔴 a file nobody else moved still lands
#   file: push_retry.sh
#   find: [ -n "$unjudged" ] || ! git diff --quiet --no-renames "$base" "$tip" -- "$p" || continue
#   with: true
#
# @vacuity 🔴🔴 the tip's copy is what stands
#   file: push_retry.sh
#   find: git checkout -q "$tip" -- "$p"
#   with: true
#
# @vacuity 🔴 a path the tip holds is restored, never deleted
#   file: push_retry.sh
#   find: if git cat-file -e "$tip:$p" 2>/dev/null; then
#   with: if false; then
#
# @vacuity 🔴 a file the tip deleted stays deleted
#   file: push_retry.sh
#   find: git rm -q --ignore-unmatch -- "$p"
#   with: true
#
# @vacuity    the run's log names what gave way
#   file: push_retry.sh
#   find: echo "$label: $p $why: the remote's copy stands"
#   with: true
#
# @vacuity 🔴🔴 what gave way is folded into this run's commit
#   file: push_retry.sh
#   find: git commit -q --amend --no-edit
#   with: true
#
# @vacuity 🔴 a commit with nothing left lands nothing
#   file: push_retry.sh
#   find: git reset -q --soft 'HEAD^'
#   with: true
#
# @vacuity    a commit nothing raced is left exactly as it was
#   file: push_retry.sh
#   find: git diff --cached --quiet HEAD && return 0
#   with: true
#
# @vacuity ⛔ never an amend on HEAD == tip: that is another run's commit
#   file: push_retry.sh
#   find: [ "$(git rev-parse HEAD)" != "$tip" ] || return 0
#   with: true
#
# @vacuity ⛔ no merge base: the rule stands aside
#   file: push_retry.sh
#   find: base="$(git merge-base "$own" "$tip" 2>/dev/null)" || return 0
#   with: base="$(git merge-base "$own" "$tip" 2>/dev/null)"
#
# @vacuity 🔴🔴 the base is this commit's own, from before any rebase
#   file: push_retry.sh
#   find: own="$mine"
#   with: own=HEAD
#
# @vacuity 🔴🔴 a run with no identity gets a name
#   file: push_retry.sh
#   find: git config user.name  >/dev/null 2>&1 || git config user.name  collector
#   with: true
#
# @vacuity 🔴🔴 ...and an email
#   file: push_retry.sh
#   find: git config user.email >/dev/null 2>&1 || git config user.email collector@local
#   with: true
#
# @vacuity ⛔ a replayed commit that fails is a failure, never "pushed"
#   file: push_retry.sh
#   find: git commit -q -m "$msg" || { echo "$label: the replayed commit failed: nothing landed"; exit 1; }
#   with: git commit -q -m "$msg" || true
#
# @vacuity 🔴🔴 a run with no identity is a tree nothing judged
#   file: push_retry.sh
#   find: git config user.name >/dev/null 2>&1 && git config user.email >/dev/null 2>&1 || unjudged=1
#   with: true
#
# @vacuity 🔴🔴 ...so nothing of it lands but the report, whether the tip moved or not
#   file: push_retry.sh
#   find: [ -n "$unjudged" ] || ! git diff --quiet
#   with: ! git diff --quiet
#
# @vacuity 🔴 ...and the log says why, never "moved" for a file nobody moved
#   file: push_retry.sh
#   find: [ -z "$unjudged" ] || why="is from a tree no check judged"
#   with: true
#
# @vacuity 🔴🔴 Converge is what gives a run its identity
#   file: .github/workflows/collect.yml
#   find: git config user.name  "gizmos-collector"
#   with: true
#
# @vacuity 🔴🔴 ...nothing before the tree check does
#   file: .github/workflows/collect.yml
#   find: echo "tree clean after tests"
#   with: git config user.name x
#
# @vacuity 🔴🔴 ...and Converge never runs past a tree the check refused
#   file: .github/workflows/collect.yml
#   find:         id: collect
#   with:         if: always()
#
# @vacuity ⚠️ step 1 resolves a conflicting hunk in the rebase (this run's side), so a race on one file is no replay
#   file: push_retry.sh
#   find: git pull -q --rebase -X theirs --autostash
#   with: git pull -q --rebase --autostash
#
# @vacuity 🔴🔴 [2026-11-04] a rebased converge pass never lands an older-tree file or a splice
#   file: push_retry.sh
#   find:     stand_newer "$(git rev-parse FETCH_HEAD)"
#   with:     true
#
# @vacuity 🔴🔴 ...nor does a replayed one
#   file: push_retry.sh
#   find:       stand_newer "$tip"
#   with:       true
#
# @vacuity 🔴🔴 a copy that read its sources later lands, whole
#   file: freshness.py
#   find:         if both and all(mine[k] >= theirs[k] for k in both) and any(mine[k] > theirs[k] for k in both):
#   with:         if False:
#
# @vacuity 🔴 ...only when it read EVERY shared source at least as late
#   file: freshness.py
#   find:         if both and all(mine[k] >= theirs[k] for k in both) and any(mine[k] > theirs[k] for k in both):
#   with:         if both and any(mine[k] > theirs[k] for k in both):
#
# @vacuity 🔴 ...and one of them later: the same reading built later is not newer
#   file: freshness.py
#   find:         if both and all(mine[k] >= theirs[k] for k in both) and any(mine[k] > theirs[k] for k in both):
#   with:         if both and all(mine[k] >= theirs[k] for k in both):
#
# @vacuity 🔴🔴 the remote's copy is what stands
#   file: freshness.py
#   find:             rev = top if side == "this run" else tip
#   with:             rev = top
#
# @vacuity 🔴🔴 a file and its heartbeat are one unit
#   file: freshness.py
#   find:         return p[:-len(HEARTBEAT_SUFFIX)] if p.endswith(HEARTBEAT_SUFFIX) else p
#   with:         return p
#
# @vacuity 🔴 ...judged on the stamps its heartbeat vouches for
#   file: freshness.py
#   find:             d = dict(d, **st) if st else d
#   with:             d = d
#
# @vacuity 🔴🔴 a card under picks/ is judged too
#   file: freshness.py
#   find: LANDING_SCOPE = re.compile(r"^(data/(?:[^/]+/)*latest/|picks/)")
#   with: LANDING_SCOPE = re.compile(r"^(data/(?:[^/]+/)*latest/)")
#
# @vacuity 🔴🔴 every commit of the pass since its base, not only the last
#   file: freshness.py
#   find:     raced = {unit(p) for p in names(base, top) if LANDING_SCOPE.match(p)} \
#   with:     raced = {unit(p) for p in names(top + "^", top) if LANDING_SCOPE.match(p)} \
#
# @vacuity 🔴 a pass with nothing left lands nothing
#   file: freshness.py
#   find:             git("reset", "-q", "--soft", "HEAD^")       # nothing of this run's own is left
#   with:             pass
#
# @vacuity 🔴🔴 what stands is folded into this run's commit
#   file: freshness.py
#   find:         p = git("commit", "-q", "--amend", "--no-edit", "--only", "--", *touched)
#   with:         p = git("status")
#
# @vacuity 🔴🔴 the watchdog's commit judges only the passes under it; step 6 has its own
#   file: push_retry.sh
#   find:     "$REPAIR_LABEL") top="$own^" ;;
#   with:     "$REPAIR_LABEL") top="$own" ;;
#
# @vacuity ⛔ any other label is one writer, and step 1 decides for it
#   file: push_retry.sh
#   find:     *) return 0 ;;
#   with:     *) top="$own" ;;
#
# @vacuity 🔴 the rule keys on the label the converge loop passes
#   file: push_retry.sh
#   find: PASS_LABEL="converge pass "
#   with: PASS_LABEL="converge round "
#
# @vacuity 🔴 ...and the converge loop passes it
#   file: .github/workflows/collect.yml
#   find: bash push_retry.sh "converge pass $PASS" ||
#   with: bash push_retry.sh "converge round $PASS" ||
#
# @vacuity ⛔ a rule that cannot run says so
#   file: push_retry.sh
#   find:     echo "::warning::$label: could not judge which run's copy of a latest/ or picks/ file is newer, so step 1's stands: ${out:-no python}"
#   with:     true
#
# @vacuity 🔴🔴 keep_both goes before the rule (rebased)
#   file: push_retry.sh
#   find: keep_both "$(git rev-parse FETCH_HEAD)"
#   with: give_way "$(git rev-parse FETCH_HEAD)"; keep_both "$(git rev-parse FETCH_HEAD)"
#
# @vacuity 🔴🔴 ...and replayed
#   file: push_retry.sh
#   find: keep_both "$tip"
#   with: give_way "$tip"; keep_both "$tip"
#
# @vacuity 🔴🔴 settle goes after the rule (rebased)
#   file: push_retry.sh
#   find: give_way "$(git rev-parse FETCH_HEAD)"
#   with: settle "$(git rev-parse FETCH_HEAD)"; give_way "$(git rev-parse FETCH_HEAD)"; settle() { :; }
#
# @vacuity 🔴🔴 ...and replayed
#   file: push_retry.sh
#   find: give_way "$tip"
#   with: settle "$tip"; give_way "$tip"; settle() { :; }
"""
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import tempfile

import credits as K
import freshness as F
import watchdog as W
import wfparse
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
HELPER = os.path.join(ROOT, "push_retry.sh")


def sh(cwd, *cmd, check=True, env=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       env=dict(os.environ, **(env or {})))
    if check and p.returncode:
        raise RuntimeError("%s: %s" % (cmd, p.stderr))
    return p


def clone(bare, where):
    sh(os.path.dirname(where), "git", "clone", "-q", bare, where)
    sh(where, "git", "config", "user.name", "t")
    sh(where, "git", "config", "user.email", "t@t")
    return where


def write(repo, rel, data):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(p, mode) as fh:
        fh.write(data)


def run_helper(repo, label, env=None):
    return subprocess.run(["bash", HELPER, label], cwd=repo,
                          capture_output=True, text=True,
                          env=dict(os.environ, PUSH_BACKOFF="0", **(env or {})))


def gz(text):
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode="wb", mtime=0) as fh:
        fh.write(text.encode())
    return b.getvalue()


section("1. 🔴🔴 TWO RUNS REWRITE THE SAME latest/ FILES — BOTH PASSES LAND")
tmp = tempfile.mkdtemp(prefix="pushretry-")
try:
    bare = os.path.join(tmp, "remote.git")
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", bare)
    seed = clone(bare, os.path.join(tmp, "seed"))
    write(seed, "data/nfl/latest/freshness.json", '{"v": 0}\n')
    write(seed, "data/nfl/latest/board.json.gz", gz("v0"))
    sh(seed, "git", "add", "-A"); sh(seed, "git", "commit", "-qm", "seed")
    sh(seed, "git", "push", "-q", "origin", "HEAD:main")

    a = clone(bare, os.path.join(tmp, "a"))
    b = clone(bare, os.path.join(tmp, "b"))
    for repo, tag in ((a, "a"), (b, "b")):
        write(repo, "data/nfl/latest/freshness.json", '{"v": "%s"}\n' % tag)
        write(repo, "data/nfl/latest/board.json.gz", gz("v-" + tag))
        write(repo, "data/nfl/2026-09-22/props/%s.json" % tag, "{}\n")
        sh(repo, "git", "add", "-A")
        sh(repo, "git", "commit", "-qm", "collect[nfl]: pass by " + tag)
    ra = run_helper(a, "pass a")
    rb = run_helper(b, "pass b")
    ck(ra.returncode == 0 and rb.returncode == 0,
       "🔴🔴 both racing passes push (rc %s / %s)" % (ra.returncode, rb.returncode),
       "⛔ the old loop left the second one's rebase half-done and exited "
       "clean. a=%r b=%r" % (ra.stdout[-200:], rb.stdout[-200:] + rb.stderr[-200:]))
    chk = clone(bare, os.path.join(tmp, "check"))
    got = sorted(os.listdir(os.path.join(chk, "data/nfl/2026-09-22/props")))
    ck(got == ["a.json", "b.json"],
       "🔴🔴 ...and BOTH runs' dated snapshots are on the remote",
       "⛔ a dated snapshot is a paid pull; losing one means buying it "
       "again. Found %s" % got)
    fr = open(os.path.join(chk, "data/nfl/latest/freshness.json")).read()
    ck('"b"' in fr,
       "   ...and under a label step 7 does not judge, the LATER pass's latest/ file wins, text "
       "and binary (a converge pass: §7)",
       "got %r" % fr)
    ck(gzip.decompress(open(os.path.join(chk, "data/nfl/latest/board.json.gz"), "rb").read()) == b"v-b",
       "   ...including a gzip, which a line merge cannot resolve")
    st = sh(b, "git", "status", "--porcelain=v1", check=False).stdout
    ck(not os.path.exists(os.path.join(b, ".git", "rebase-merge"))
       and not os.path.exists(os.path.join(b, ".git", "rebase-apply")),
       "⛔ ...and no rebase is ever left half-done",
       "status=%r" % st)

    # 1b. a conflict `-X theirs` cannot resolve: one run DELETES a file
    #     the other rewrites. Only the abort-and-replay path lands this.
    d = clone(bare, os.path.join(tmp, "d"))
    e = clone(bare, os.path.join(tmp, "e"))
    sh(d, "git", "rm", "-q", "data/nfl/latest/freshness.json")
    write(d, "data/nfl/2026-09-22/props/d.json", "{}\n")
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "pass d")
    write(e, "data/nfl/latest/freshness.json", '{"v": "e"}\n')
    write(e, "data/nfl/2026-09-22/props/e.json", "{}\n")
    sh(e, "git", "add", "-A"); sh(e, "git", "commit", "-qm", "pass e")
    rd, re_ = run_helper(d, "pass d"), run_helper(e, "pass e")
    chk2 = clone(bare, os.path.join(tmp, "check2"))
    got2 = sorted(os.listdir(os.path.join(chk2, "data/nfl/2026-09-22/props")))
    ck(rd.returncode == 0 and re_.returncode == 0
       and {"d.json", "e.json"} <= set(got2)
       and not os.path.exists(os.path.join(e, ".git", "rebase-merge")),
       "🔴🔴 a modify/delete conflict is ABORTED and REPLAYED, not lost",
       "⛔ a strategy option cannot resolve this one; only the replay can. "
       "rc %s/%s, props %s, out %r" % (rd.returncode, re_.returncode, got2,
                                       re_.stdout[-200:]))

    # 2. a push that cannot land exits NON-zero
    section("2. ⛔ A PUSH THAT CANNOT LAND IS A FAILURE, NEVER A SILENT PASS")
    c = clone(bare, os.path.join(tmp, "c"))
    write(c, "x.txt", "x\n"); sh(c, "git", "add", "-A"); sh(c, "git", "commit", "-qm", "x")
    sh(c, "git", "remote", "set-url", "origin", os.path.join(tmp, "nowhere.git"))
    rc = run_helper(c, "doomed")
    ck(rc.returncode == 1 and "could not push" in rc.stdout,
       "⛔ an unreachable remote exits 1 and says so",
       "rc=%s out=%r" % (rc.returncode, rc.stdout[-200:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("3. 🔴 EVERY PUSH IN THE WORKFLOWS GOES THROUGH THE HELPER")
# ⚠️ DERIVED from the files, not listed. self-repair.yml is EXEMPT by its
#    own standing rule: an agent must never modify it (GitHub attributes a
#    scheduled run to whoever last changed the cron). Reported, not hidden.
bad = []
for f in sorted(os.listdir(os.path.join(ROOT, ".github", "workflows"))):
    if not f.endswith(".yml") or f == "self-repair.yml":
        continue
    for n, line in enumerate(open(os.path.join(ROOT, ".github", "workflows", f)), 1):
        s = line.strip()
        if s.startswith("#"):
            continue
        if re.search(r"\bgit (push|pull --rebase)\b", s):
            bad.append("%s:%d %s" % (f, n, s[:70]))
ck(not bad,
   "🔴 no workflow runs its own pull/push loop (self-repair.yml exempt)",
   "⛔ a hand-rolled loop is the defect this file exists for: %s" % bad)
wf = open(os.path.join(ROOT, ".github", "workflows", "collect.yml")).read()
ck('bash push_retry.sh "converge pass $PASS"' in wf,
   "🔴 the converge loop calls the helper")
ck(re.search(r'push_retry\.sh "converge pass \$PASS"[^\n]*\n[^\n]*rc=1', wf) is not None
   or re.search(r'push_retry\.sh "converge pass \$PASS" \|\| \{[^}]*rc=1', wf) is not None,
   "⛔ ...and a failed push turns the run red")
# ⚠️ STEP 6 READS A MISSING GIT IDENTITY AS "NOTHING JUDGED THIS TREE". That is only true while
#    Converge alone sets it, after the tree check, with no `if:` to run it past a refusal. A
#    name set any earlier would switch the rule off in silence: no run would ever lack one.
TREE3, CONV3 = "The tests must not have modified the tree", "Converge and hold"
job3 = wfparse.steps(os.path.join(ROOT, ".github", "workflows", "collect.yml"), "collect")
ck([s.name for s in job3 if "git config user.name" in (s.run or "")] == [CONV3]
   and [s.name for s in job3 if s.name in (TREE3, CONV3)] == [TREE3, CONV3]
   and [s.cond for s in job3 if s.name == CONV3] == [None],
   "🔴🔴 only Converge gives a run its identity, after the tree check and never past a refusal, "
   "so a run with none is a run nothing judged",
   "⛔ push_retry.sh step 6 reads no identity as an unjudged tree: this moved and the rule went "
   "off in silence, or fires on a judged run. %s"
   % [(s.name, s.cond) for s in job3 if s.name == CONV3 or "git config user.name" in (s.run or "")])

section("4. 🔴🔴 TWO RUNS BUY THE SAME PAID MINUTE — BOTH RECEIPTS LAND")
# `[measured 2026-10-23]` Runs 39960254704 and 39954846803 both bought NFL
#    gamelines (6) + props (144) at 17:28Z and both wrote `.../1728.json.gz`.
#    Step 1's `-X theirs` kept the second run's file: one receipt and its
#    150 credits left main (the watchdog reported them unrecorded). Main's
#    history holds two more: 10-11 19:19Z ncaaf gamelines, 08-23 01:15Z
#    props-batter. This replays it: the clones are the two runs.
DAY = "data/nfl/2026-10-23"


def snap(at, used, left):
    return gz(json.dumps({"pulled_at": at, "credits_used": used,
                          "credits_remaining": left, "games": []}))


tmp = tempfile.mkdtemp(prefix="pushretry-paid-")
try:
    bare = os.path.join(tmp, "remote.git")
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", bare)
    seed = clone(bare, os.path.join(tmp, "seed"))
    write(seed, "data/nfl/latest/board.json", '{"v": 0}\n')
    write(seed, "data/nfl/latest/odds.json", '{"v": 0}\n')
    sh(seed, "git", "add", "-A"); sh(seed, "git", "commit", "-qm", "seed")
    sh(seed, "git", "push", "-q", "origin", "HEAD:main")

    # three runs, all started from the same tip, all buying the 17:28 minute
    runs = {"a": (snap("2026-10-23T17:28:01Z", 6, 19941), snap("2026-10-23T17:28:04Z", 144, 19797)),
            "b": (snap("2026-10-23T17:28:10Z", 6, 19791), snap("2026-10-23T17:28:14Z", 144, 19647)),
            "g": (snap("2026-10-23T17:28:40Z", 6, 19641), None)}
    clones = {}
    for tag, (gl, pp) in runs.items():
        r = clones[tag] = clone(bare, os.path.join(tmp, tag))
        write(r, DAY + "/gamelines/1728.json.gz", gl)
        if pp:
            write(r, DAY + "/props-player/1728.json.gz", pp)
        # ⚠️ a dated file that is NOT a paid kind: the later run still wins
        write(r, DAY + "/news/1728.json.gz", gz("news-" + tag))
        write(r, "data/nfl/latest/board.json", '{"v": "%s"}\n' % tag)
        sh(r, "git", "add", "-A")
        sh(r, "git", "commit", "-qm", "collect[nfl]: converge pass 1 by " + tag)
    out = {t: run_helper(clones[t], "pass " + t) for t in ("a", "b", "g")}
    ck(all(p.returncode == 0 for p in out.values()),
       "   all three racing runs push",
       "rc %s" % {t: p.returncode for t, p in out.items()})
    chk = clone(bare, os.path.join(tmp, "check4"))

    def blob(rel):
        p = os.path.join(chk, rel)
        return open(p, "rb").read() if os.path.exists(p) else None

    gl_dir = sorted(os.listdir(os.path.join(chk, DAY, "gamelines")))
    ck(gl_dir == ["1728-1.json.gz", "1728-2.json.gz", "1728.json.gz"]
       and blob(DAY + "/gamelines/1728.json.gz") == runs["a"][0]
       and blob(DAY + "/gamelines/1728-1.json.gz") == runs["b"][0]
       and blob(DAY + "/gamelines/1728-2.json.gz") == runs["g"][0],
       "🔴🔴 every run's paid gamelines snapshot is on the remote: the first "
       "keeps 1728, the later ones land beside it as 1728-1, 1728-2",
       "⛔ 10-23 17:28Z: the second run's file replaced the first's and its "
       "credits left the record. Found %s" % gl_dir)
    ck(blob(DAY + "/props-player/1728.json.gz") == runs["a"][1]
       and blob(DAY + "/props-player/1728-1.json.gz") == runs["b"][1],
       "🔴🔴 ...and both 144-credit props receipts",
       "found %s" % sorted(os.listdir(os.path.join(chk, DAY, "props-player"))))
    rows = K.readings(os.path.join(chk, "data"), ("gamelines", "props-player"))
    used = sum(json.loads(gzip.decompress(open(p, "rb").read()))["credits_used"]
               for _a, _l, p in rows)
    ck(len(rows) == 5 and used == 306
       and K.newest(rows)[1] == 19641,
       "   ...so the balance chain reads all 306 credits and the newest balance",
       "readings=%d used=%d newest=%s" % (len(rows), used, K.newest(rows)))
    ck(sorted(os.listdir(os.path.join(chk, DAY, "news"))) == ["1728.json.gz"]
       and gzip.decompress(blob(DAY + "/news/1728.json.gz")) == b"news-g",
       "⛔ only a PAID snapshot is kept twice: any other file, dated or "
       "latest/, still takes the later run's copy",
       "news=%s" % sorted(os.listdir(os.path.join(chk, DAY, "news"))))
    ck("kept beside it as 1728-1.json.gz" in out["b"].stdout,
       "   ...and the run's log says which file it kept beside which",
       "b said %r" % out["b"].stdout[-300:])
    ck(sh(clones["b"], "git", "status", "--porcelain").stdout == ""
       and sh(clones["b"], "git", "rev-parse", "HEAD").stdout.strip()
       == sh(clones["b"], "git", "rev-parse", "origin/main").stdout.strip(),
       "   ...and the run's own tree matches what landed, so its next pass "
       "cannot stage its copy back over the first",
       "status %r" % sh(clones["b"], "git", "status", "--porcelain").stdout)

    # 4b. the REPLAY path (step 2): a modify/delete conflict aborts the
    #     rebase, and the replay re-applies this run's files onto the tip.
    e = clone(bare, os.path.join(tmp, "e"))
    f = clone(bare, os.path.join(tmp, "f"))
    sh(e, "git", "rm", "-q", "data/nfl/latest/odds.json")
    write(e, DAY + "/gamelines/1900.json.gz", snap("2026-10-23T19:00:02Z", 6, 19600))
    sh(e, "git", "add", "-A"); sh(e, "git", "commit", "-qm", "pass e")
    write(f, "data/nfl/latest/odds.json", '{"v": "f"}\n')
    write(f, DAY + "/gamelines/1900.json.gz", snap("2026-10-23T19:00:09Z", 6, 19594))
    sh(f, "git", "add", "-A"); sh(f, "git", "commit", "-qm", "pass f")
    re_, rf = run_helper(e, "pass e"), run_helper(f, "pass f")
    chk2 = clone(bare, os.path.join(tmp, "check4b"))
    g2 = sorted(os.listdir(os.path.join(chk2, DAY, "gamelines")))
    ck(re_.returncode == 0 and rf.returncode == 0
       and "replayed" in rf.stdout
       and {"1900.json.gz", "1900-1.json.gz"} <= set(g2)
       and open(os.path.join(chk2, DAY, "gamelines", "1900.json.gz"), "rb").read()
       == snap("2026-10-23T19:00:02Z", 6, 19600),
       "🔴🔴 the REPLAY path keeps both receipts too",
       "⛔ a replay re-applies this run's files over the tip. rc %s/%s, "
       "gamelines %s, out %r" % (re_.returncode, rf.returncode, g2, rf.stdout[-300:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("5. 🔴🔴 A HEARTBEAT LANDS ONLY BESIDE THE BYTES IT VOUCHES FOR")
# `[2026-10-28, review; two real clones, never seen in production]` A football
#    run's MLB `record` repair (watchdog) writes the heartbeat for the
#    record-detail ITS older checkout holds. Step 1's `-X theirs` would keep that
#    heartbeat over the MLB run's, beside the MLB run's newer gzip: it would vouch
#    for nothing, the gzip's own 09:55 stamp would be read, and the next MLB pass
#    would go red at 10:00Z.
#    Step 5 (`freshness.settle_beats`): the tip's heartbeat stays when IT
#    vouches for the file that lands, else the stale one is removed.
REC = "data/latest/record-detail.json.gz"


def gzdoc(built, rows):
    return gz(json.dumps({"built_at": built, "rows": rows}))


def beat(repo, built, rows):
    """A stamp-only write of record-detail in `repo`: the heartbeat, as collect.write makes it."""
    return F.keep_with_heartbeat(os.path.join(repo, REC), {"built_at": built, "rows": rows})


def landed(tag):
    chk = clone(bare, os.path.join(tmp, "check-" + tag))
    beats = sorted(os.path.relpath(os.path.join(d, n), chk).replace(os.sep, "/")
                   for d, _s, fs in os.walk(chk) if ".git" not in d
                   for n in fs if n.endswith(F.HEARTBEAT_SUFFIX))
    void = [b for b in beats if not F._bound_stamps(os.path.join(chk, b[:-len(F.HEARTBEAT_SUFFIX)]),
                                                     {"built_at": None})]
    return F.stamp_of(os.path.join(chk, REC)), beats, void


def seed_repo(tag, extra=None):
    global bare
    bare = os.path.join(tmp, tag + ".git")
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", bare)
    sd = clone(bare, os.path.join(tmp, tag + "-seed"))
    write(sd, REC, gzdoc("2026-11-10T10:05:00Z", "v0"))
    write(sd, "data/latest/record.json", '{"v": 0}\n')
    for rel, data in (extra or {}).items():
        write(sd, rel, data)
    sh(sd, "git", "add", "-A"); sh(sd, "git", "commit", "-qm", "seed")
    sh(sd, "git", "push", "-q", "origin", "HEAD:main")


def commit(repo, msg):
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-qm", msg)


tmp = tempfile.mkdtemp(prefix="pr5-")
try:
    # 5a. THE REBASE PATH: the MLB run changes record-detail at 09:55Z and sees it
    #     unchanged at 10:05Z (a heartbeat); the football repair, on the older
    #     base, heartbeats the OLD bytes at 10:06Z and lands last.
    seed_repo("a")
    u = clone(bare, os.path.join(tmp, "a-mlb"))
    fb = clone(bare, os.path.join(tmp, "a-fb"))
    write(u, REC, gzdoc("2026-11-11T09:55:00Z", "v1"))
    commit(u, "collect[mlb]: record 09:55")
    run_helper(u, "mlb 1")
    ck(beat(u, "2026-11-11T10:05:00Z", "v1"), "(the MLB run's 10:05Z pull is stamp-only: a heartbeat)")
    commit(u, "collect[mlb]: record 10:05")
    ru = run_helper(u, "mlb 2")
    ck(beat(fb, "2026-11-11T10:06:00Z", "v0"), "(the football repair's pull is stamp-only on ITS older bytes)")
    write(fb, "data/latest/record.json", '{"v": "fb"}\n')
    commit(fb, "collect[ncaaf]: repair record")
    rf = run_helper(fb, "fb repair")
    st, beats, void = landed("a")
    ck(ru.returncode == 0 and rf.returncode == 0 and "replayed" not in rf.stdout
       and st == F._parse("2026-11-11T10:05:00Z") and beats == [REC + F.HEARTBEAT_SUFFIX] and not void,
       "🔴🔴 a rebased pass keeps the tip's heartbeat when its own vouches for older bytes: "
       "record-detail is aged 10:05Z (the MLB run's pull), never 09:55Z (stale at 10:00Z)",
       "⛔ -X theirs kept the repair's heartbeat beside the MLB run's gzip. stamp_of %s, "
       "beats %s, void %s, rc %s/%s, out %r" % (st, beats, void, ru.returncode, rf.returncode,
                                                 rf.stdout[-300:]))
    ck("the remote's heartbeat is kept" in rf.stdout,
       "   ...and the run's log says which heartbeat it gave way to", repr(rf.stdout[-300:]))

    # 5b. THE REPLAY PATH (step 2): the same race, with a modify/delete conflict
    #     on another file, so the rebase aborts and this run's files are replayed.
    seed_repo("b", {"data/latest/odds.json": '{"v": 0}\n'})
    u = clone(bare, os.path.join(tmp, "b-mlb"))
    fb = clone(bare, os.path.join(tmp, "b-fb"))
    write(u, REC, gzdoc("2026-11-11T09:55:00Z", "v1"))
    commit(u, "collect[mlb]: record 09:55")
    run_helper(u, "mlb 1")
    beat(u, "2026-11-11T10:05:00Z", "v1")
    sh(u, "git", "rm", "-q", "data/latest/odds.json")
    commit(u, "collect[mlb]: record 10:05")
    ru = run_helper(u, "mlb 2")
    beat(fb, "2026-11-11T10:06:00Z", "v0")
    write(fb, "data/latest/odds.json", '{"v": "fb"}\n')
    commit(fb, "collect[ncaaf]: repair record")
    rf = run_helper(fb, "fb repair")
    st, beats, void = landed("b")
    ck(ru.returncode == 0 and rf.returncode == 0 and "replayed" in rf.stdout
       and st == F._parse("2026-11-11T10:05:00Z") and not void,
       "🔴🔴 ...and so does a REPLAYED pass",
       "stamp_of %s, beats %s, void %s, rc %s/%s, out %r"
       % (st, beats, void, ru.returncode, rf.returncode, rf.stdout[-300:]))

    # 5c. NO HEARTBEAT ON THE TIP: the MLB run's 09:55Z write was a full one and
    #     nothing vouched since; the repair's heartbeat for the old bytes is
    #     removed, so the file's own stamp stands and no void file lands.
    seed_repo("c")
    u = clone(bare, os.path.join(tmp, "c-mlb"))
    fb = clone(bare, os.path.join(tmp, "c-fb"))
    write(u, REC, gzdoc("2026-11-11T09:55:00Z", "v1"))
    commit(u, "collect[mlb]: record 09:55")
    run_helper(u, "mlb 1")
    beat(fb, "2026-11-11T10:06:00Z", "v0")
    commit(fb, "collect[ncaaf]: repair record")
    rf = run_helper(fb, "fb repair")
    st, beats, void = landed("c")
    ck(rf.returncode == 0 and st == F._parse("2026-11-11T09:55:00Z") and beats == []
       and sh(fb, "git", "status", "--porcelain").stdout == "",
       "🔴 a heartbeat that vouches for nothing, with none on the tip, is removed before it lands "
       "(the file's own stamp stands) and the run's tree is clean",
       "stamp_of %s, beats %s, void %s, status %r, out %r"
       % (st, beats, void, sh(fb, "git", "status", "--porcelain").stdout, rf.stdout[-300:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("6. 🔴🔴 THE WATCHDOG'S COMMIT NEVER REPLACES WHAT ANOTHER RUN LANDED AFTER ITS BASE")
# `[2026-11-01, review; two real clones, never seen in production]` A run's repair rebuilds
#    on the tree this run last pulled and lands through step 1, whose `-X theirs` keeps THIS
#    run's file. So a football run's MLB `record` repair WOULD put a graded day back out of
#    record.json, with a LATER built_at, and verify_record would go red. Same exposure:
#    `card`, `card-fb` in any run (watchdog.REBUILDS), and whatever the step's
#    `git add data picks` sweeps. No record.json version has ever lost a graded day.
# ⚠️ WHAT THIS GUARDS: every path the watchdog's commit changed that another run also moved.
#    NOT a new dated archive (`winner-picks`, `model-picks`) from a run that reached Converge:
#    a new path never counts as moved, so a stale repair's save still lands. ~~NOT a converge
#    pass (6b, 6b2): two overlapping football runs can still roll a card back for minutes, or
#    splice it, and that is a separate fix.~~ `[2026-11-04]` A converge pass is step 7's (§7;
#    6b, 6b2, 6d here keep step 6 to its own commit). A run that never reached Converge is
#    stricter than all of this (6n): nothing judged its tree, so only its report lands.
LABEL = "health report"     # what collect.yml's commit step passes; pinned below
HEALTH6 = W.HEALTH
REC6 = "data/latest/record.json"
OTHER6 = "data/nfl/latest/record.json"
CARD6 = "picks/fb-nfl-latest.json"
PAID6 = "data/nfl/2026-11-11/gamelines/1728.json.gz"


def rec6(built, n):
    """ONE line, as the real MLB record.json is: a conflict takes the whole file."""
    return json.dumps({"built_at": built, "overall": {"n": n}}, separators=(",", ":"))


def n6(repo):
    """The landed record's graded count. None if it did not land: a check fails, the file runs on."""
    p = os.path.join(repo, REC6)
    return json.load(open(p))["overall"]["n"] if os.path.exists(p) else None


def card6(built, rows):
    """Pretty-printed, as a football card is: a merge can splice two builds."""
    return json.dumps({"generated_at": built, "note": "x", "picks": rows}, indent=1) + "\n"


def seed6(tag, extra=None):
    bare6 = os.path.join(tmp, tag + ".git")
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", bare6)
    sd = clone(bare6, os.path.join(tmp, tag + "-seed"))
    write(sd, REC6, rec6("2026-11-10T10:05:00Z", 100))
    write(sd, HEALTH6, '{"checked_at": "seed"}')
    write(sd, OTHER6, '{"v": 0}\n')
    write(sd, CARD6, card6("2026-11-10T10:05:00Z", ["a -110", "b -115", "c -120", "d -105"]))
    for rel, data in (extra or {}).items():
        write(sd, rel, data)
    sh(sd, "git", "add", "-A"); sh(sd, "git", "commit", "-qm", "seed")
    sh(sd, "git", "push", "-q", "origin", "HEAD:main")
    return bare6, clone(bare6, os.path.join(tmp, tag + "-mlb")), clone(bare6, os.path.join(tmp, tag + "-fb"))


def wd_commit(repo, env=None):
    """The step's own commit, on the checkout this run last pulled."""
    sh(repo, "git", "add", "data", "picks")
    sh(repo, "git", "-c", "user.name=collector", "-c", "user.email=collector@local",
       "commit", "-qm", "watchdog: health report 2026-11-11T10:06Z", env=env)


def land_first(repo, msg="collect[mlb]: converge pass 3"):
    """The other run: its pass lands before this run's commit does."""
    commit(repo, msg)
    run_helper(repo, "converge pass 3")


def remote_head(repo):
    return sh(repo, "git", "ls-remote", "origin", "main").stdout


def hook(repo, name, body):
    p = os.path.join(repo, ".git", "hooks", name)
    with open(p, "w", newline="\n") as fh:
        fh.write("#!/bin/sh\n" + body)
    os.chmod(p, 0o755)


def no_identity(repo):
    """This clone as a run that never reached the workflow's `git config`; -> that run's env.

    ⚠️ Blanking the global config also drops a Windows machine's core.autocrlf, which reads
    the whole checkout as dirty, so the clone keeps that one setting for itself."""
    eol = sh(repo, "git", "config", "core.autocrlf", check=False).stdout.strip()
    if eol:
        sh(repo, "git", "config", "core.autocrlf", eol)
    sh(repo, "git", "config", "--unset", "user.name")
    sh(repo, "git", "config", "--unset", "user.email")
    sh(repo, "git", "config", "user.useConfigOnly", "true")
    return {"GIT_CONFIG_GLOBAL": os.path.join(tmp, "no-such-config"), "GIT_CONFIG_NOSYSTEM": "1"}


tmp = tempfile.mkdtemp(prefix="pr6-")
try:
    # 6a. THE REBASE PATH. The MLB run grades a new day and lands; the football run,
    #     still on the older base, repairs from its older picks, one minute LATER.
    bare6, u, fb = seed6("a")
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    write(u, CARD6, card6("2026-11-11T10:05:00Z", ["a -105", "b -115", "c -120", "d -105"]))
    write(u, HEALTH6, '{"checked_at": "mlb"}')
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100))
    write(fb, CARD6, card6("2026-11-11T10:06:00Z", ["a -110", "b -115", "c -120", "d -105"]))
    write(fb, OTHER6, '{"v": "repaired"}\n')
    write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb)
    rf = run_helper(fb, LABEL)
    chk = clone(bare6, os.path.join(tmp, "a-check"))
    ck(rf.returncode == 0 and n6(chk) == 112,
       "🔴🔴 a stale repair never rolls the record back: the graded day another run "
       "landed stays, though the repair's built_at is later",
       "⛔ rebase -X theirs kept the repair's file. n=%s rc=%s out=%r"
       % (n6(chk), rf.returncode, rf.stdout[-300:]))
    ck(open(os.path.join(chk, CARD6)).read()
       == card6("2026-11-11T10:05:00Z", ["a -105", "b -115", "c -120", "d -105"]),
       "🔴🔴 ...and a pretty-printed card is the tip's, byte for byte, never a splice of two builds",
       repr(open(os.path.join(chk, CARD6)).read()[:200]))
    ck(open(os.path.join(chk, OTHER6)).read() == '{"v": "repaired"}\n'
       and open(os.path.join(chk, HEALTH6)).read() == '{"checked_at": "fb"}',
       "   ...while a file nobody else moved lands, and so does the health report",
       repr(open(os.path.join(chk, OTHER6)).read()))
    ck("the remote's copy stands" in rf.stdout,
       "   ...and the run's log names what it gave way on", repr(rf.stdout[-300:]))
    ck(sh(fb, "git", "status", "--porcelain").stdout == ""
       and sh(fb, "git", "rev-parse", "HEAD").stdout == sh(fb, "git", "rev-parse", "origin/main").stdout,
       "   ...and the run's own tree matches what landed")

    # 6b. A CONVERGE PASS IS NOT A REPAIR: step 7 decides for it, never step 6. ~~step 1 still
    #     decides for it~~ `[2026-11-04]` Its board read LATER than the other run's, so step 7
    #     lands it, where step 6 gives way to anything moved; its older record still gives way.
    bare6, u, fb = seed6("b", {"data/nfl/latest/board.json": '{"pulled_at": "2026-11-10T10:00:00Z"}\n'})
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    write(u, "data/nfl/latest/board.json", '{"pulled_at": "2026-11-11T10:05:00Z"}\n')
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100))
    write(fb, "data/nfl/latest/board.json", '{"pulled_at": "2026-11-11T10:06:00Z"}\n')
    commit(fb, "pass fb")
    rf = run_helper(fb, "converge pass 1")
    chk = clone(bare6, os.path.join(tmp, "b-check"))
    ck(rf.returncode == 0 and n6(chk) == 112
       and open(os.path.join(chk, "data/nfl/latest/board.json")).read() == '{"pulled_at": "2026-11-11T10:06:00Z"}\n',
       "⛔ only the watchdog's commit gives way to everything moved: a converge pass that read "
       "later still lands its own copy (step 7)",
       "the rule grew past its label. n %s board %r"
       % (n6(chk), open(os.path.join(chk, "data/nfl/latest/board.json")).read()))

    # 6b2. WHAT A CONVERGE PASS DOES TO A PRETTY-PRINTED FILE. ~~⚠️ This pins the behaviour the
    #      header describes, not one anyone wants: `-X theirs` decides conflicting hunks only, so
    #      the later lander's stamp lands over the other run's price. A fix for the football
    #      rollbacks turns this red, and must correct step 1's words in the same change.~~
    #      `[2026-11-04]` It turned red with step 7, and step 1's words were corrected with it:
    #      the card is the other run's, whole (§7 has the rest of the class).
    bare6, u, fb = seed6("b2")
    write(u, CARD6, card6("2026-11-11T10:05:00Z", ["a -105", "b -115", "c -120", "d -105"]))
    land_first(u)
    write(fb, CARD6, card6("2026-11-11T10:06:00Z", ["a -110", "b -115", "c -120", "d -105"]))
    commit(fb, "pass fb")
    rf = run_helper(fb, "converge pass 1")
    chk = clone(bare6, os.path.join(tmp, "b2-check"))
    ck(rf.returncode == 0 and open(os.path.join(chk, CARD6)).read()
       == card6("2026-11-11T10:05:00Z", ["a -105", "b -115", "c -120", "d -105"]),
       "🔴🔴 a converge pass never splices a pretty-printed card: the other run's stamp and price, "
       "whole, where step 1 alone put this run's stamp over the other run's price",
       "⛔ a splice of two builds landed. %r" % open(os.path.join(chk, CARD6)).read()[:200])

    # 6c. THE REPLAY PATH: the tip deleted a file the repair rewrote, so the rebase aborts.
    bare6, u, fb = seed6("c", {"data/latest/odds.json": '{"v": 0}\n'})
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    sh(u, "git", "rm", "-q", "data/latest/odds.json")
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100))
    write(fb, "data/latest/odds.json", '{"v": "fb"}\n')
    write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb)
    rf = run_helper(fb, LABEL)
    chk = clone(bare6, os.path.join(tmp, "c-check"))
    ck(rf.returncode == 0 and "replayed" in rf.stdout
       and n6(chk) == 112
       and not os.path.exists(os.path.join(chk, "data/latest/odds.json"))
       and open(os.path.join(chk, HEALTH6)).read() == '{"checked_at": "fb"}',
       "🔴🔴 a REPLAYED landing gives way too, and a file the tip deleted stays deleted",
       "rc %s, n %s, out %r" % (rf.returncode, n6(chk), rf.stdout[-300:]))

    # 6d. ONLY THE WATCHDOG'S OWN COMMIT: a pass that could not push sits under it.
    #     `[2026-11-04]` That pass is judged by step 7: its paid pull read LATER, so it lands.
    bare6, u, fb = seed6("d", {"data/nfl/latest/board.json": '{"pulled_at": "2026-11-10T10:00:00Z", "v": 0}\n'})
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    write(u, "data/nfl/latest/board.json", '{"pulled_at": "2026-11-11T10:05:00Z", "v": "u"}\n')
    land_first(u, "collect[nfl]: converge pass 3")
    write(fb, "data/nfl/latest/board.json", '{"pulled_at": "2026-11-11T10:06:00Z", "v": "paid pass"}\n')
    commit(fb, "collect[nfl]: converge pass 1")
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100)); write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb)
    rf = run_helper(fb, LABEL)
    chk = clone(bare6, os.path.join(tmp, "d-check"))
    ck(rf.returncode == 0
       and open(os.path.join(chk, "data/nfl/latest/board.json")).read()
       == '{"pulled_at": "2026-11-11T10:06:00Z", "v": "paid pass"}\n'
       and n6(chk) == 112,
       "⛔ a converge pass under the watchdog's commit is judged as a pass (its later pull lands); "
       "only the commit this step made gives way to everything moved",
       "board %r, n %s" % (open(os.path.join(chk, "data/nfl/latest/board.json")).read(),
                           n6(chk)))

    # 6e. NOTHING LEFT: the repair was all the commit held.
    bare6, u, fb = seed6("e")
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100)); wd_commit(fb)
    before = remote_head(u)
    rf = run_helper(fb, LABEL)
    ck(rf.returncode == 0 and remote_head(u) == before
       and sh(fb, "git", "status", "--porcelain").stdout == "",
       "   a commit with nothing left lands nothing: no empty commit on the remote",
       "out %r" % rf.stdout[-300:])

    # 6f. NO IDENTITY. A run cancelled in Tests never reached the workflow's `git config`.
    #     `[run 41215684625]` "fatal: empty ident name", then "pushed on attempt 1
    #     (replayed onto the new tip)", and nothing on main: 8 of the 10 such runs.
    bare6, u, fb = seed6("f")
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    land_first(u)
    tip6 = sh(u, "git", "rev-parse", "HEAD").stdout.strip()
    run_env = no_identity(fb)
    write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb)
    rf = run_helper(fb, LABEL, run_env)
    chk = clone(bare6, os.path.join(tmp, "f-check"))
    ck(rf.returncode == 0 and open(os.path.join(chk, HEALTH6)).read() == '{"checked_at": "fb"}',
       "🔴🔴 a run with no git identity lands its report on a moved tip",
       "⛔ it said pushed and landed nothing. rc %s out %r err %r"
       % (rf.returncode, rf.stdout[-300:], rf.stderr[-300:]))
    ck(sh(chk, "git", "merge-base", "--is-ancestor", tip6, "HEAD", check=False).returncode == 0,
       "   ...on top of the other run's commit, which nothing amended",
       sh(chk, "git", "log", "--format=%h %s", "-3").stdout)
    ck("empty ident" not in rf.stderr and "Author identity" not in rf.stderr,
       "   ...and git never complained about who it is", repr(rf.stderr[-300:]))

    # 6g. A REPLAYED COMMIT THAT FAILS LANDED NOTHING, AND THE RUN SAYS SO. The hook stands
    #     in for any reason a commit can fail, now that the identity is not one of them.
    bare6, u, fb = seed6("g", {"data/latest/odds.json": '{"v": 0}\n'})
    sh(u, "git", "rm", "-q", "data/latest/odds.json")
    land_first(u)
    write(fb, "data/latest/odds.json", '{"v": "fb"}\n'); commit(fb, "collect[nfl]: converge pass 1")
    hook(fb, "pre-commit", "exit 1\n")
    before = remote_head(u)
    rf = run_helper(fb, "converge pass 1")
    ck(rf.returncode == 1 and "nothing landed" in rf.stdout and "pushed" not in rf.stdout
       and remote_head(u) == before,
       "⛔ a replayed commit that fails exits 1 and says nothing landed, never \"pushed\"",
       "rc %s out %r" % (rf.returncode, rf.stdout[-300:]))

    # 6h. THE TIP ALREADY HOLDS THIS COMMIT: the rebase drops it, and HEAD IS the other run's
    #     commit. The stray staged file (what --autostash hands back) is how a test reaches
    #     a dirty index on HEAD == tip: amending there would rewrite a commit that landed.
    bare6, u, fb = seed6("h")
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:05:00Z", 112)); wd_commit(fb)
    write(fb, "stray.txt", "x\n"); sh(fb, "git", "add", "stray.txt")
    before = remote_head(u)
    rf = run_helper(fb, LABEL)
    ck(rf.returncode == 0 and "pushed on attempt 1" in rf.stdout and remote_head(u) == before,
       "⛔ on HEAD == tip nothing is amended: another run's commit stays as it landed",
       "rc %s out %r" % (rf.returncode, rf.stdout[-300:]))

    # 6i. keep_both GOES FIRST: a paid receipt the commit swept (a cancelled run's pass) is
    #     renamed before the rule looks, in both paths, or the rule would drop it.
    for tag, path, conflict in (("i", "rebased", False), ("i2", "replayed", True)):
        bare6, u, fb = seed6(tag, {"data/latest/odds.json": '{"v": 0}\n'})
        first, second = snap("2026-11-11T17:28:01Z", 6, 19941), snap("2026-11-11T17:28:10Z", 6, 19935)
        write(u, PAID6, first)
        if conflict:
            sh(u, "git", "rm", "-q", "data/latest/odds.json")
            write(fb, "data/latest/odds.json", '{"v": "fb"}\n')
        land_first(u, "collect[nfl]: converge pass 3")
        write(fb, PAID6, second); wd_commit(fb)
        rf = run_helper(fb, LABEL)
        chk = clone(bare6, os.path.join(tmp, tag + "-check"))
        ck(rf.returncode == 0 and ("replayed" in rf.stdout) == conflict
           and blob(PAID6) == first and blob(PAID6.replace("1728", "1728-1")) == second,
           "🔴🔴 a %s commit keeps a paid receipt it swept: it lands beside the tip's" % path,
           "⛔ the rule looked first and the credits left the record. rc %s, gamelines %s, out %r"
           % (rf.returncode, sorted(os.listdir(os.path.dirname(os.path.join(chk, PAID6)))), rf.stdout[-300:]))

    # 6j. settle GOES LAST: a heartbeat the rule gave back to the tip is judged against the
    #     bytes that land. This commit's full write of the gzip lands (nobody moved it), the
    #     tip's newer heartbeat came back and vouches for the old bytes: it must go.
    t1, t2, t3 = "2026-11-11T09:00:00Z", "2026-11-11T10:05:00Z", "2026-11-11T10:06:00Z"
    for tag, path, replayed in (("j", "replayed", True), ("j2", "rebased", False)):
        seed_repo(tag)
        sd = clone(bare, os.path.join(tmp, tag + "-first"))
        beat(sd, t1, "v0")
        commit(sd, "collect[mlb]: record 09:00")
        run_helper(sd, "mlb 1")
        u = clone(bare, os.path.join(tmp, tag + "-mlb"))
        fb = clone(bare, os.path.join(tmp, tag + "-fb"))
        beat(u, t2, "v0")
        commit(u, "collect[mlb]: record 10:05")
        run_helper(u, "mlb 2")
        write(fb, REC, gzdoc(t3, "v1"))
        F.drop_heartbeat(os.path.join(fb, REC))    # a full write, as collect.write does
        if not replayed:
            beat(fb, t3.replace("10:06", "10:07"), "v1")    # ...then a pull that saw it unchanged
        commit(fb, "watchdog: health report 2026-11-11T10:07Z")
        rf = run_helper(fb, LABEL)
        st, beats, void = landed(tag)
        ck(rf.returncode == 0 and ("replayed" in rf.stdout) == replayed
           and st == F._parse(t3) and beats == [] and not void,
           "🔴🔴 a heartbeat the %s commit gave back to the tip never lands beside bytes it does "
           "not vouch for" % path,
           "⛔ settle ran before the rule did. stamp_of %s, beats %s, void %s, rc %s, out %r"
           % (st, beats, void, rf.returncode, rf.stdout[-300:]))

    # 6k. A THIRD RUN LANDS WHILE THIS ONE PUSHES: the first push fails and attempt 2 is
    #     judged against the newer tip, by the same base (`own` outlives the rebases).
    bare6, u, fb = seed6("k")
    third = clone(bare6, os.path.join(tmp, "k-third"))
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    land_first(u)
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100))
    write(fb, OTHER6, '{"v": "repaired"}\n')
    write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb)
    flag = os.path.join(tmp, "k.flag").replace(os.sep, "/")
    hook(fb, "pre-push",
         'if [ ! -f "%(flag)s" ]; then\n'
         '  touch "%(flag)s"\n'
         '  cd "%(third)s" && unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE &&\n'
         "  git pull -q origin main && printf '{\"v\": \"third\"}\\n' > %(other)s &&\n"
         '  git add -A && git commit -qm third && git push -q origin HEAD:main\n'
         '  exit 1\n'
         'fi\n' % {"flag": flag, "third": third.replace(os.sep, "/"), "other": OTHER6})
    rf = run_helper(fb, LABEL)
    chk = clone(bare6, os.path.join(tmp, "k-check"))
    ck(rf.returncode == 0 and "pushed on attempt 2" in rf.stdout
       and open(os.path.join(chk, OTHER6)).read() == '{"v": "third"}\n'
       and n6(chk) == 112
       and open(os.path.join(chk, HEALTH6)).read() == '{"checked_at": "fb"}',
       "🔴🔴 a run that lands during the push is not replaced either: attempt 2 gives way to it too",
       "rc %s other %r out %r" % (rf.returncode, open(os.path.join(chk, OTHER6)).read(), rf.stdout[-300:]))

    # 6l. THE EVERYDAY CASE: a health-only commit nothing raced. The committer date is in the
    #     past so that an amend, which stamps now, cannot make the same commit by accident.
    bare6, u, fb = seed6("l")
    write(fb, HEALTH6, '{"checked_at": "fb"}')
    wd_commit(fb, {"GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z"})
    own6 = sh(fb, "git", "rev-parse", "HEAD").stdout.strip()
    rf = run_helper(fb, LABEL)
    ck(rf.returncode == 0 and remote_head(u).split()[0] == own6,
       "   a commit nothing raced lands as the very commit it was: the rule only reads",
       "own %s remote %s out %r" % (own6, remote_head(u), rf.stdout[-300:]))

    # 6m. NO SHARED HISTORY WITH THE TIP: nothing is known to have moved, so step 1 decides.
    bare6, u, fb = seed6("m")
    sh(u, "git", "checkout", "-q", "--orphan", "fresh")
    write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
    sh(u, "git", "add", "-A"); sh(u, "git", "commit", "-qm", "a new root")
    sh(u, "git", "push", "-qf", "origin", "HEAD:main")
    write(fb, REC6, rec6("2026-11-11T10:06:00Z", 100)); wd_commit(fb)
    rf = run_helper(fb, LABEL)
    chk = clone(bare6, os.path.join(tmp, "m-check"))
    ck(rf.returncode == 0 and n6(chk) == 100,
       "⛔ with no merge base the rule stands aside rather than judge on nothing",
       "rc %s n %s out %r" % (rf.returncode, n6(chk),
                              rf.stdout[-300:]))

    # 6n. A TREE NOTHING JUDGED. No identity means the run never reached Converge: cancelled in
    #     Tests, refused by the tree check, or red in Tests on a push. The commit step still
    #     sweeps `data picks`, and that can hold what a killed test left: test_tcheck_guard.py
    #     rewrites a tracked file and adds one in the real tree. The missing identity used to
    #     stop that landing, by accident and only on a moved tip. So: the report, and nothing
    #     else, on every path. (Reproduced on two clones; no such file has ever landed.)
    PROBE6 = "data/ncaaf/latest/teams.json"
    DROP6 = "data/ncaaf/latest/_tcheck_probe_delete_me.json"
    GONE6 = "data/latest/odds.json"
    for tag, how in (("n", "a moved tip"), ("n2", "a tip nobody moved"), ("n3", "a replay")):
        bare6, u, fb = seed6(tag, {PROBE6: '{"teams": 1}\n', GONE6: '{"v": 0}\n'})
        if how == "a moved tip":
            write(u, REC6, rec6("2026-11-11T10:05:00Z", 112))
            land_first(u)
        elif how == "a replay":
            sh(u, "git", "rm", "-q", GONE6)
            land_first(u)
            write(fb, GONE6, '{"v": "fb"}\n')
        tip6 = remote_head(u).split()[0]
        run_env = no_identity(fb)
        write(fb, PROBE6, '{"teams": 1, "_tcheck_probe": 1}\n')
        write(fb, DROP6, "{}\n")
        write(fb, HEALTH6, '{"checked_at": "fb"}')
        wd_commit(fb)
        rf = run_helper(fb, LABEL, run_env)
        chk = clone(bare6, os.path.join(tmp, tag + "-check"))
        got6 = sh(chk, "git", "diff", "--name-only", "--no-renames", tip6, "HEAD").stdout.split()
        ck(rf.returncode == 0 and ("replayed" in rf.stdout) == (how == "a replay")
           and got6 == [HEALTH6]
           and open(os.path.join(chk, HEALTH6)).read() == '{"checked_at": "fb"}',
           "🔴🔴 a run nothing judged lands its health report and nothing else, on %s" % how,
           "⛔ what a killed test left reached the remote. landed %s rc %s out %r"
           % (got6, rf.returncode, rf.stdout[-300:]))
        ck("no check judged" in rf.stdout and "moved on the remote" not in rf.stdout,
           "   ...and the log says why, never that a file nobody moved had moved",
           repr(rf.stdout[-300:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

section("7. 🔴🔴 A CONVERGE PASS NEVER REPLACES A NEWER latest/ OR picks/ FILE WITH ONE BUILT FROM AN OLDER TREE")
# `[measured 2026-09-20 -> 11-04, main's own history]` Two football runs overlap and each
#    builds both leagues' cards from the tree its pass pulled. Step 1 let the second lander
#    win: 25 NFL and 13 college cards landed with an older build than the card they replaced
#    (median 14 and 18 minutes back, worst 54; 10-17 put Bills -230 back to -225 for 42), and a
#    pretty-printed card could land as a splice of the two builds (6b2 pinned it). A later
#    pull is newer whatever tree joined it (1 of the other 24 races' second cards was priced
#    from one), so "the remote always wins" would hide paid prices. Step 7
#    (`freshness.stand_newer`): the remote's copy, whole, unless this run's copy read its
#    sources later. `u` is the run that lands first; `fb` the run whose pass began before.
T0, TU, TF, TL = ("2026-11-11T10:00:00Z", "2026-11-11T10:05:00Z", "2026-11-11T10:06:00Z",
                  "2026-11-11T10:07:00Z")
T2, TB = "2026-11-11T10:02:00Z", "2026-11-11T10:04:00Z"
CARD7, REC7, BOARD7 = "picks/fb-nfl-latest.json", "data/nfl/latest/record.json", "data/nfl/latest/board.json"
PROPS7, MIX7 = "data/nfl/latest/props.json.gz", "data/nfl/latest/fb-props-model.json"
SAME7, LOGS7 = "data/nfl/latest/vs-position-2026.json.gz", "data/nfl/latest/players-2026.json.gz"
ONLY7, GONE7 = "data/nfl/latest/news-flags.json", "data/nfl/latest/odds-probe.json"
PASS7 = "converge pass 1"      # what collect.yml passes: PASS_LABEL + the pass number, pinned below


def card7(built, odds, first, note="x"):
    """Pretty-printed, as card_fb.py writes it: step 1 merges it hunk by hunk."""
    return json.dumps({"generated_at": built, "note": note, "odds_pulled_at": odds, "rule": "y",
                       "picks": [first, "b -115", "c -120", "d -105"]}, indent=1) + "\n"


def one7(**kw):
    """ONE line, as most latest/ files are: a conflict takes the whole file."""
    return json.dumps(kw, separators=(",", ":"))


def seed7(tag):
    bare7 = os.path.join(tmp, tag + ".git")
    sh(tmp, "git", "init", "-q", "--bare", "-b", "main", bare7)
    sd = clone(bare7, os.path.join(tmp, tag + "-seed"))
    for rel, data in {CARD7: card7(T0, T0, "a -110"), REC7: one7(built_at=T0, n=100),
                      BOARD7: one7(pulled_at=T0, v=0), PROPS7: gz(one7(pulled_at=T0, v=0)),
                      MIX7: one7(built_at=T0, board_pulled_at=T0, logs_pulled_at=T0),
                      SAME7: gz(one7(pulled_at=T0, v=0)), LOGS7: gz(one7(pulled_at=T0, rows="v0")),
                      ONLY7: one7(built_at=T0, v=0), GONE7: one7(built_at=T0, v=0)}.items():
        write(sd, rel, data)
    sh(sd, "git", "add", "-A"); sh(sd, "git", "commit", "-qm", "seed")
    sh(sd, "git", "push", "-q", "origin", "HEAD:main")
    return bare7, clone(bare7, os.path.join(tmp, tag + "-u")), clone(bare7, os.path.join(tmp, tag + "-fb"))


def read7(repo, rel):
    """What landed at `rel`, as text (a gzip decompressed); None if nothing did."""
    p = os.path.join(repo, rel)
    if not os.path.exists(p):
        return None
    return gzip.decompress(open(p, "rb").read()).decode() if rel.endswith(".gz") else open(p).read()


def n7(repo):
    return json.loads(read7(repo, REC7) or "{}").get("n")


def beat7(repo, at):
    """A stamp-only pull of LOGS7 in `repo`: the heartbeat, as collect.write makes it."""
    return F.keep_with_heartbeat(os.path.join(repo, LOGS7), {"pulled_at": at, "rows": "v0"})


def clean7(repo):
    return (sh(repo, "git", "status", "--porcelain").stdout == ""
            and sh(repo, "git", "rev-parse", "HEAD").stdout == sh(repo, "git", "rev-parse", "origin/main").stdout)


tmp = tempfile.mkdtemp(prefix="pr7-")
try:
    # 7a. THE REBASE PATH, AS IT RACES TODAY. The other run lands a new price and a graded
    #     day; this run built LATER from the older tree, and read the board EARLIER.
    bare7, u, fb = seed7("a")
    write(u, CARD7, card7(TU, T0, "a -105"))
    write(u, REC7, one7(built_at=TU, n=112))
    write(u, BOARD7, one7(pulled_at=T2, v="u"))
    write(u, MIX7, one7(built_at=TU, board_pulled_at=T2, logs_pulled_at=T0))
    ck(beat7(u, TB), "(the other run's 10:04 logs pull is stamp-only: a heartbeat)")
    land_first(u)
    write(fb, CARD7, card7(TF, T0, "a -110"))
    write(fb, REC7, one7(built_at=TF, n=100))
    write(fb, BOARD7, one7(pulled_at="2026-11-11T10:01:00Z", v="fb"))
    write(fb, MIX7, one7(built_at=TF, board_pulled_at=TL, logs_pulled_at="2026-11-11T09:00:00Z"))
    write(fb, LOGS7, gz(one7(pulled_at="2026-11-11T10:03:00Z", rows="v1")))
    write(fb, ONLY7, one7(built_at=TF, v="fb"))
    commit(fb, "collect[ncaaf nfl]: converge pass 1")
    rf = run_helper(fb, PASS7)
    chk = clone(bare7, os.path.join(tmp, "a-check"))
    ck(rf.returncode == 0 and read7(chk, CARD7) == card7(TU, T0, "a -105"),
       "🔴🔴 a pretty-printed card is the other run's, byte for byte, never a splice of two builds",
       "⛔ step 1 put this run's stamp over the other run's price. rc %s card %r out %r"
       % (rf.returncode, (read7(chk, CARD7) or "")[:160], rf.stdout[-300:]))
    ck(n7(chk) == 112,
       "🔴🔴 a pass built from an older tree never rolls a file back, though its built_at is later",
       "⛔ the graded day another run landed left main. n=%s" % n7(chk))
    ck(read7(chk, BOARD7) == one7(pulled_at=T2, v="u"),
       "🔴 a pass that read its source EARLIER gives way too", repr(read7(chk, BOARD7)))
    ck(F.stamp_of(os.path.join(chk, LOGS7)) == F._parse(TB)
       and json.loads(read7(chk, LOGS7))["rows"] == "v0",
       "🔴🔴 a file and its heartbeat are one: the other run's later reading stands, read "
       "through the heartbeat that vouches for it",
       "stamp_of %s rows %r" % (F.stamp_of(os.path.join(chk, LOGS7)), read7(chk, LOGS7)))
    ck(read7(chk, MIX7) == one7(built_at=TU, board_pulled_at=T2, logs_pulled_at=T0),
       "🔴 a copy that read one source later and another earlier is not newer: the remote's stands",
       repr(read7(chk, MIX7)))
    ck(read7(chk, ONLY7) == one7(built_at=TF, v="fb"),
       "   ...while a file nobody else moved lands", repr(read7(chk, ONLY7)))
    ck("the remote's copy stands" in rf.stdout and clean7(fb),
       "   ...the run's log names what gave way, and its tree matches what landed",
       repr(rf.stdout[-400:]))

    # 7b. THIS RUN READ LATER: it bought the odds after the other run did, so its board, its
    #     props join and the card priced from them land whole (the other run's note included).
    bare7, u, fb = seed7("b")
    write(u, BOARD7, one7(pulled_at=T2, v="u"))
    write(u, PROPS7, gz(one7(pulled_at=T2, v="u")))
    write(u, CARD7, card7(TU, T2, "a -105", note="u"))
    write(u, REC7, one7(built_at=TU, n=112))
    write(u, SAME7, gz(one7(pulled_at=T2, v="u")))
    beat7(u, TB)
    land_first(u)
    write(fb, BOARD7, one7(pulled_at=TL, v="fb"))
    write(fb, PROPS7, gz(one7(pulled_at=TL, v="fb")))
    write(fb, CARD7, card7(TL, TL, "a -125"))
    write(fb, REC7, one7(built_at=TF, n=100))
    write(fb, SAME7, gz(one7(pulled_at=T2, v="fb")))
    write(fb, LOGS7, gz(one7(pulled_at=TL, rows="v1")))
    commit(fb, "collect[nfl]: converge pass 1")
    rf = run_helper(fb, PASS7)
    chk = clone(bare7, os.path.join(tmp, "b-check"))
    ck(rf.returncode == 0 and read7(chk, BOARD7) == one7(pulled_at=TL, v="fb")
       and read7(chk, PROPS7) == one7(pulled_at=TL, v="fb")
       and read7(chk, CARD7) == card7(TL, TL, "a -125"),
       "🔴🔴 a pass that read its odds LATER lands its own copy, whole: the board, the props join "
       "and the card priced from them",
       "⛔ a newer paid pull was hidden behind the other run's older one. board %r card %r out %r"
       % (read7(chk, BOARD7), (read7(chk, CARD7) or "")[:160], rf.stdout[-300:]))
    ck(read7(chk, SAME7) == one7(pulled_at=T2, v="u"),
       "🔴 the same reading built later is not newer: the remote's copy stands", repr(read7(chk, SAME7)))
    ck(n7(chk) == 112, "   ...and in the same pass a file with no reading still gives way", "n=%s" % n7(chk))
    ck(F.stamp_of(os.path.join(chk, LOGS7)) == F._parse(TL)
       and not os.path.exists(os.path.join(chk, LOGS7 + F.HEARTBEAT_SUFFIX)),
       "🔴 a later full write takes its heartbeat with it: none is left beside bytes it never saw",
       "stamp_of %s" % F.stamp_of(os.path.join(chk, LOGS7)))
    ck("this run's copy lands whole" in rf.stdout and clean7(fb),
       "   ...and the log says which of this run's copies read later", repr(rf.stdout[-400:]))

    # 7c. THE REPLAY PATH: the other run deleted a file this pass rewrote, so the rebase aborts
    #     and this run's files are replayed onto the tip, then judged the same way.
    bare7, u, fb = seed7("c")
    write(u, CARD7, card7(TU, T0, "a -105"))
    write(u, REC7, one7(built_at=TU, n=112))
    write(u, BOARD7, one7(pulled_at=T2, v="u"))
    sh(u, "git", "rm", "-q", GONE7)
    land_first(u)
    write(fb, CARD7, card7(TF, T0, "a -110"))
    write(fb, REC7, one7(built_at=TF, n=100))
    write(fb, BOARD7, one7(pulled_at=TL, v="fb"))
    write(fb, GONE7, one7(built_at=TF, v="fb"))
    commit(fb, "collect[nfl]: converge pass 1")
    rf = run_helper(fb, PASS7)
    chk = clone(bare7, os.path.join(tmp, "c-check"))
    ck(rf.returncode == 0 and "replayed" in rf.stdout
       and read7(chk, CARD7) == card7(TU, T0, "a -105") and n7(chk) == 112,
       "🔴🔴 a REPLAYED pass never lands its older-tree card or record over the other run's",
       "⛔ the replay checked out every file this run changed. rc %s n %s out %r"
       % (rf.returncode, n7(chk), rf.stdout[-300:]))
    ck(read7(chk, BOARD7) == one7(pulled_at=TL, v="fb") and read7(chk, GONE7) is None and clean7(fb),
       "   ...its later read still lands, and a file the other run deleted stays deleted",
       "board %r gone %r" % (read7(chk, BOARD7), read7(chk, GONE7)))

    # 7d. AN EARLIER PASS THAT COULD NOT PUSH sits under this one: it is this run's too.
    bare7, u, fb = seed7("d")
    write(u, REC7, one7(built_at=TU, n=112))
    write(u, CARD7, card7(TU, T0, "a -105"))
    land_first(u)
    write(fb, REC7, one7(built_at=TF, n=100)); commit(fb, "collect[nfl]: converge pass 1")
    write(fb, CARD7, card7(TL, T0, "a -110")); write(fb, ONLY7, one7(built_at=TL, v="fb"))
    commit(fb, "collect[nfl]: converge pass 2")
    rf = run_helper(fb, "converge pass 2")
    chk = clone(bare7, os.path.join(tmp, "d-check"))
    ck(rf.returncode == 0 and n7(chk) == 112 and read7(chk, CARD7) == card7(TU, T0, "a -105")
       and read7(chk, ONLY7) == one7(built_at=TL, v="fb"),
       "🔴🔴 every commit of this run since its base is judged, not only the last: an earlier "
       "pass's older record gives way too",
       "n %s out %r" % (n7(chk), rf.stdout[-300:]))

    # 7e. NOTHING LEFT: every file the pass changed gave way.
    bare7, u, fb = seed7("e")
    write(u, REC7, one7(built_at=TU, n=112)); land_first(u)
    write(fb, REC7, one7(built_at=TF, n=100)); commit(fb, "collect[nfl]: converge pass 1")
    before = remote_head(u)
    rf = run_helper(fb, PASS7)
    ck(rf.returncode == 0 and remote_head(u) == before and clean7(fb)
       and "the remote's copy stands" in rf.stdout,
       "   a pass whose every file gave way lands nothing (no empty commit), and its log says why",
       "out %r" % rf.stdout[-300:])

    # 7f. A THIRD RUN LANDS WHILE THIS ONE PUSHES: attempt 2 is judged against the newer tip.
    bare7, u, fb = seed7("f")
    third = clone(bare7, os.path.join(tmp, "f-third"))
    write(u, REC7, one7(built_at=TU, n=112)); land_first(u)
    write(fb, REC7, one7(built_at=TF, n=100)); write(fb, ONLY7, one7(built_at=TF, v="fb"))
    commit(fb, "collect[nfl]: converge pass 1")
    flag = os.path.join(tmp, "f.flag").replace(os.sep, "/")
    hook(fb, "pre-push",
         'if [ ! -f "%(flag)s" ]; then\n'
         '  touch "%(flag)s"\n'
         '  cd "%(third)s" && unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE &&\n'
         "  git pull -q origin main && printf '%%s' '%(rec)s' > %(path)s &&\n"
         '  git add -A && git commit -qm third && git push -q origin HEAD:main\n'
         '  exit 1\n'
         'fi\n' % {"flag": flag, "third": third.replace(os.sep, "/"), "path": REC7,
                   "rec": one7(built_at="2026-11-11T10:08:00Z", n=120)})
    rf = run_helper(fb, PASS7)
    chk = clone(bare7, os.path.join(tmp, "f-check"))
    ck(rf.returncode == 0 and "pushed on attempt 2" in rf.stdout and n7(chk) == 120
       and read7(chk, ONLY7) == one7(built_at=TF, v="fb"),
       "🔴🔴 a run that lands during the push is not replaced either: attempt 2 gives way to it too",
       "rc %s n %s out %r" % (rf.returncode, n7(chk), rf.stdout[-300:]))

    # 7g. ANOTHER LABEL. A refit, the run list and a self-repair record are each the one writer
    #     of their files: step 7 judges a converge pass (and the passes under the watchdog's).
    bare7, u, fb = seed7("g")
    write(u, REC7, one7(built_at=TU, n=112)); land_first(u)
    write(fb, REC7, one7(built_at=TF, n=100)); commit(fb, "runs: run status")
    rf = run_helper(fb, "run status")
    chk = clone(bare7, os.path.join(tmp, "g-check"))
    ck(rf.returncode == 0 and n7(chk) == 100,
       "⛔ only a converge pass is judged: under another label step 1 still decides",
       "n %s out %r" % (n7(chk), rf.stdout[-300:]))

    # 7h. THE RULE CANNOT RUN (a broken freshness.py beside the script): the run says so and
    #     lands step 1's result. Losing the pass, and the paid receipts in it, would be worse.
    bare7, u, fb = seed7("h")
    write(u, REC7, one7(built_at=TU, n=112)); land_first(u)
    write(fb, REC7, one7(built_at=TF, n=100)); commit(fb, "collect[nfl]: converge pass 1")
    alone = os.path.join(tmp, "h-helper")
    os.makedirs(alone)
    shutil.copy(HELPER, alone)
    with open(os.path.join(alone, "freshness.py"), "w") as fh:
        fh.write("import sys\nsys.exit('boom')\n")
    rf = subprocess.run(["bash", os.path.join(alone, "push_retry.sh"), PASS7], cwd=fb,
                        capture_output=True, text=True, env=dict(os.environ, PUSH_BACKOFF="0"))
    chk = clone(bare7, os.path.join(tmp, "h-check"))
    ck(rf.returncode == 0 and "::warning::converge pass 1: could not judge" in rf.stdout
       and n7(chk) == 100,
       "⛔ a rule that cannot run warns and lands the pass: never silent, and never a pass lost",
       "rc %s n %s out %r" % (rf.returncode, n7(chk), rf.stdout[-300:]))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

helper_text = open(HELPER, encoding="utf-8").read()
m7 = re.search(r'^PASS_LABEL="([^"]+)"', helper_text, re.M)
for wf7 in (".github/workflows/collect.yml", "docs/upload/collect.yml"):
    if os.path.exists(os.path.join(ROOT, wf7)):
        ck(m7 is not None and m7.group(1) + "1" == PASS7
           and 'bash push_retry.sh "%s$PASS"' % m7.group(1) in open(os.path.join(ROOT, wf7), encoding="utf-8").read(),
           "🔴 %s's converge loop passes the label step 7 keys on" % wf7,
           "⛔ a label that drifts is a rule that stops in silence, and collect.yml changes only by "
           "Sam's upload")
m6 = re.search(r'^REPAIR_LABEL="([^"]+)"', helper_text, re.M)
ck(m6 is not None and m6.group(1) == LABEL and 'bash push_retry.sh "%s"' % m6.group(1) in wf,
   "🔴 the workflow's commit step passes the label the rule keys on, so renaming one "
   "cannot switch the rule off in silence",
   "⛔ collect.yml cannot change without Sam's upload: a label that drifts is a rule that stops")
h6 = re.search(r'^HEALTH_PATH="([^"]+)"', helper_text, re.M)
ck(h6 is not None and h6.group(1) == W.HEALTH,
   "🔴 the one file that always lands is the file the watchdog writes (watchdog.HEALTH)",
   "⛔ a moved health report would start giving way: the report that says a run went wrong")
