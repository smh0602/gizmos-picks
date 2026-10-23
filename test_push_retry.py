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
from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
HELPER = os.path.join(ROOT, "push_retry.sh")


def sh(cwd, *cmd, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
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


def run_helper(repo, label):
    return subprocess.run(["bash", HELPER, label], cwd=repo,
                          capture_output=True, text=True,
                          env=dict(os.environ, PUSH_BACKOFF="0"))


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
       "   ...and the LATER pass's latest/ file wins, text and binary",
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
