#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════
# push_retry.sh <label> — land this run's commits on the remote branch.
#
# 🔴🔴 WHY THIS EXISTS. `[measured 2026-09-21, runs 09-15 → 09-21]` The
#    converge loop's `git pull --rebase --autostash && git push` (x3)
#    LOST WHOLE PASSES. Three football crons (`6 12`, `6 13`, `8 12`)
#    start within minutes of each other; once the Tests step grew past
#    ~20 min they converged at the same moment and rewrote the same
#    `data/<lg>/latest/*` files. The rebase hit a content conflict, was
#    LEFT HALF-DONE, attempts 2 and 3 could not even pull ("you have
#    unmerged files"), and the loop fell through with no error.
#    ⛔ Consequences, all measured from the run logs:
#      · the audits' "dark crons" — they fired every day; their commits
#        never landed;
#      · the "~50% unrecorded Odds spend" — 1,628 of 2,750 credits on
#        09-19 were in lost passes, and because the snapshot never landed
#        the next run BOUGHT THE SAME PULL AGAIN (ncaaf props x4 on 09-19).
#
# ✅ WHAT IT DOES:
#   1. pull --rebase -X theirs: in a rebase "theirs" is THIS run's commit,
#      and it decides CONFLICTING HUNKS only: this run's side of each, the
#      tip's side of the rest. So ON ITS OWN a one-line or binary `latest/*`
#      file is the last lander's whole, whatever its build was made from, and a
#      pretty-printed one (a card, health.json) is a splice of both builds
#      under the last lander's stamp. ~~(5 and 6 are exceptions)~~ `[2026-11-04]`
#      Steps 5, 6 and 7 then correct it before every push: ⛔ a converge pass
#      never lands that splice or that last lander's whole (7). Step 1 still
#      decides alone for a dated path that is not paid, and for any label but a
#      converge pass and the watchdog's (each of those workflows is one writer).
#      ~~Dated snapshot paths are unique and never conflict.~~ (see 4)
#   2. If the rebase still cannot finish (binary or modify/delete
#      conflict), ABORT it — never leave it half-done — and REPLAY: reset
#      onto the fresh remote tip and re-apply exactly the paths this run
#      changed, with the same commit message.
#   3. Five attempts, then EXIT 1. ⛔ It never fails silently. ~~the caller
#      turns the run red.~~ What that does is the caller's: a converge pass
#      goes red; the watchdog's commit step is `continue-on-error`, so it only
#      annotates; and a cancelled run stays cancelled.
#   4. `[2026-10-23]` Dated snapshot paths are NOT always unique: two
#      runs that buy in the same minute write
#      the same `HHMM.json.gz`, and step 1 kept only the later one (10-23
#      17:28Z lost 150 paid credits' receipt). Before every push, a PAID
#      snapshot the remote already holds keeps its name and this run's copy
#      lands beside it as `HHMM-n` (`credits.keep_both`).
#   5. `[2026-10-28]` A heartbeat (`<file>.beat.json`) this run lands must
#      vouch for the file beside it on the tip it lands on; one that no
#      longer does gives way to the tip's, or is removed
#      (`freshness.settle_beats`). Reproduced on two clones, never seen in
#      production: a football run's MLB record repair would land one bound
#      to its older record-detail, and the next MLB pass would go red.
#   6. `[2026-11-01]` The watchdog's commit (REPAIR_LABEL) gives way: every
#      path it changed that another run also moved since this run's base
#      keeps the remote's copy. A repair rebuilds on the tree this run last
#      pulled, so a stale build would otherwise replace a newer file, with
#      a LATER built_at (two clones; it has never fired). The health report
#      always lands. A run with no git identity never reached Converge
#      (cancelled in Tests, refused by the tree check, or red in Tests on a
#      push), so no check judged what its sweep holds, and that can be what a
#      killed test left in data/: ALL of it gives way, tip moved or not, and
#      only its report lands. ⚠️ NOT a new dated archive (`winner-picks`,
#      `model-picks`) from a run that did reach Converge: a new path never
#      counts as moved, so a stale repair's save still lands. ~~NOT a converge
#      pass: step 1 still decides for it, so two overlapping football runs
#      can still roll a card back for minutes, or splice it.~~ (see 7)
#   7. `[2026-11-04]` A CONVERGE PASS NEVER REPLACES A NEWER FILE WITH ONE BUILT
#      FROM AN OLDER TREE (`freshness.stand_newer`). Two football runs overlap and
#      each builds both leagues' cards from the tree its pass pulled; step 1 let
#      the second lander win: 09-20 -> 11-04, 25 NFL and 13 college cards landed
#      with an older build than the one they replaced (worst 54 minutes; one with
#      other prices: 10-17, Bills -230 back to -225 for 42), and a card could land
#      spliced. Now every
#      `data/**/latest/` and `picks/` file this pass changed that another run
#      landed after this pass's base is the REMOTE's copy, whole, unless this
#      run's copy read its sources later (`pulled_at`, `odds_pulled_at`, ...):
#      then this run's, whole. A file and its heartbeat go together. The
#      watchdog's commit judges the passes under it this way, its own by 6.
#      ⚠️ It chooses, it never rebuilds: a pass that gives way loses its newer
#      build of that file until the next one (23 cards in that window, 21 with the
#      same rows and prices); a later props pull that wins carries only what its
#      own tree had of the other run's books. A failure warns and step 1 stands.
# ══════════════════════════════════════════════════════════════════════
set -u
label="${1:-push}"
# A run cancelled in Tests never reached the workflow's `git config`: a rebase, a replayed
# commit and every amend below need an identity, and a replay without one printed "pushed".
# The same absence says no check judged this run's tree (step 6), so it is read first.
# ⚠️ That holds while Converge alone sets the identity: test_push_retry.py pins it.
unjudged=""
git config user.name >/dev/null 2>&1 && git config user.email >/dev/null 2>&1 || unjudged=1
git config user.name  >/dev/null 2>&1 || git config user.name  collector
git config user.email >/dev/null 2>&1 || git config user.email collector@local
branch="$(git rev-parse --abbrev-ref HEAD)"
remote="${PUSH_REMOTE:-origin}"
mine="$(git rev-parse HEAD)"
own="$mine"                     # this commit, before any rebase: step 6. Never reassigned.
REPAIR_LABEL="health report"    # collect.yml's commit step; test_push_retry.py pins it
PASS_LABEL="converge pass "     # collect.yml's converge loop, + the pass number; pinned too
HEALTH_PATH="data/latest/health.json"    # watchdog.HEALTH; test_push_retry.py pins it
msg="$(git log -1 --format=%B "$mine")"
here="$(cd "$(dirname "$0")" && pwd)"

# keep_both <tip>: step 4, against the exact commit this push lands on.
# ⚠️ A copy of this script without credits.py beside it (a test fixture)
#    has no paid kinds to protect. A failure warns and lands anyway: losing
#    the whole pass would be worse than losing one receipt.
keep_both() {
  [ -f "$here/credits.py" ] || return 0
  local py out
  py="$(command -v python || command -v python3)"
  if [ -z "$py" ] || ! out="$("$py" "$here/credits.py" keep-both "$1" 2>&1)"; then
    echo "::warning::$label: could not check for a paid snapshot another run landed under the same name: ${out:-no python}"
    return 0
  fi
  [ -z "$out" ] || while IFS= read -r line; do echo "$label: $line"; done <<< "$out"
}

# settle <tip>: step 5, against the exact commit this push lands on.
# ⚠️ Like keep_both: no freshness.py beside the script (a fixture) means no
#    heartbeats to settle, and a failure warns and lands anyway.
settle() {
  [ -f "$here/freshness.py" ] || return 0
  local py out
  py="$(command -v python || command -v python3)"
  if [ -z "$py" ] || ! out="$("$py" "$here/freshness.py" settle-beats "$1" 2>&1)"; then
    echo "::warning::$label: could not check this run's heartbeats against the remote: ${out:-no python}"
    return 0
  fi
  [ -z "$out" ] || while IFS= read -r line; do echo "$label: $line"; done <<< "$out"
}

# stand_newer <tip>: step 7, against the exact commit this push lands on. A converge pass
# judges every commit it holds (an earlier pass that could not push included); the watchdog's
# commit judges the passes under it and leaves its own to step 6. After keep_both (a paid
# snapshot is a dated path, never judged here), before give_way and settle.
# ⚠️ Like settle: no freshness.py beside the script (a fixture) means no rule, and a failure
#    warns and lands step 1's result: losing the whole pass would be worse.
stand_newer() {
  local top py out
  case "$label" in
    "$PASS_LABEL"*) top="$own" ;;
    "$REPAIR_LABEL") top="$own^" ;;
    *) return 0 ;;
  esac
  [ -f "$here/freshness.py" ] || return 0
  py="$(command -v python || command -v python3)"
  if [ -z "$py" ] || ! out="$("$py" "$here/freshness.py" stand-newer "$1" "$top" 2>&1)"; then
    echo "::warning::$label: could not judge which run's copy of a latest/ or picks/ file is newer, so step 1's stands: ${out:-no python}"
    return 0
  fi
  [ -z "$out" ] || while IFS= read -r line; do echo "$label: $line"; done <<< "$out"
}

# give_way <tip>: step 6, against the exact commit this push lands on. After keep_both, so a
# paid snapshot the commit swept is renamed first; before settle, so a heartbeat is judged
# against what lands. No merge base: nothing is known to have moved, and step 1 decides.
# A run nothing judged gives way on every path but the report, whether it moved or not.
give_way() {
  [ "$label" = "$REPAIR_LABEL" ] || return 0
  local tip="$1" base p why="moved on the remote after this run's base"
  [ -z "$unjudged" ] || why="is from a tree no check judged"
  [ "$(git rev-parse HEAD)" != "$tip" ] || return 0     # no commit of this run to fold into
  base="$(git merge-base "$own" "$tip" 2>/dev/null)" || return 0
  while IFS= read -r p; do
    [ -n "$p" ] && [ "$p" != "$HEALTH_PATH" ] || continue
    [ -n "$unjudged" ] || ! git diff --quiet --no-renames "$base" "$tip" -- "$p" || continue
    if git cat-file -e "$tip:$p" 2>/dev/null; then
      git checkout -q "$tip" -- "$p"
    else
      git rm -q --ignore-unmatch -- "$p"
    fi
    echo "$label: $p $why: the remote's copy stands"
  done <<< "$(git diff --name-only --no-renames "$own^" "$own")"
  git diff --cached --quiet HEAD && return 0
  if [ "$(git write-tree)" = "$(git rev-parse 'HEAD^^{tree}')" ]; then
    git reset -q --soft 'HEAD^'
  else
    git commit -q --amend --no-edit
  fi
}

for i in 1 2 3 4 5; do
  if git pull -q --rebase -X theirs --autostash "$remote" "$branch" >/dev/null 2>&1; then
    keep_both "$(git rev-parse FETCH_HEAD)"
    stand_newer "$(git rev-parse FETCH_HEAD)"
    give_way "$(git rev-parse FETCH_HEAD)"
    settle "$(git rev-parse FETCH_HEAD)"
    if git push -q "$remote" "HEAD:$branch" >/dev/null 2>&1; then
      echo "$label: pushed on attempt $i"
      exit 0
    fi
  else
    git rebase --abort >/dev/null 2>&1 || true
    # ── REPLAY: this run's paths, onto the fresh tip ──
    if git fetch -q "$remote" "$branch" 2>/dev/null; then
      tip="$(git rev-parse FETCH_HEAD)"
      base="$(git merge-base "$mine" "$tip" 2>/dev/null || echo "$tip")"
      changes="$(git diff --name-status --no-renames "$base" "$mine")"
      git reset -q --hard "$tip"
      while IFS=$'\t' read -r st path; do
        [ -n "${path:-}" ] || continue
        case "$st" in
          D) git rm -q --ignore-unmatch -- "$path" ;;
          *) git checkout -q "$mine" -- "$path" ;;
        esac
      done <<< "$changes"
      if ! git diff --cached --quiet; then
        git commit -q -m "$msg" || { echo "$label: the replayed commit failed: nothing landed"; exit 1; }
      fi
      keep_both "$tip"
      stand_newer "$tip"
      give_way "$tip"
      settle "$tip"
      mine="$(git rev-parse HEAD)"
      if git push -q "$remote" "HEAD:$branch" >/dev/null 2>&1; then
        echo "$label: pushed on attempt $i (replayed onto the new tip)"
        exit 0
      fi
    fi
  fi
  echo "$label: push attempt $i failed, retrying"
  sleep $(( i * ${PUSH_BACKOFF:-3} ))
done
echo "$label: could not push after 5 attempts"
exit 1
