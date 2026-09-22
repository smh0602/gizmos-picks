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
#      so a fresher build of a `latest/*` file wins. Dated snapshot paths
#      are unique and never conflict.
#   2. If the rebase still cannot finish (binary or modify/delete
#      conflict), ABORT it — never leave it half-done — and REPLAY: reset
#      onto the fresh remote tip and re-apply exactly the paths this run
#      changed, with the same commit message.
#   3. Five attempts, then EXIT 1. ⛔ It never fails silently; the caller
#      turns the run red.
# ══════════════════════════════════════════════════════════════════════
set -u
label="${1:-push}"
branch="$(git rev-parse --abbrev-ref HEAD)"
remote="${PUSH_REMOTE:-origin}"
mine="$(git rev-parse HEAD)"
msg="$(git log -1 --format=%B "$mine")"

for i in 1 2 3 4 5; do
  if git pull -q --rebase -X theirs --autostash "$remote" "$branch" >/dev/null 2>&1; then
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
        git commit -q -m "$msg"
      fi
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
