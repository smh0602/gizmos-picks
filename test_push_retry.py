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
"""
import gzip
import io
import os
import re
import shutil
import subprocess
import tempfile

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
