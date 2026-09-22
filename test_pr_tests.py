#!/usr/bin/env python3
"""Every pull request runs the SAME suite the collector runs, before merge.

🔴 `[2026-09-22]` Until pr-tests.yml the suite ran only inside collect.yml,
i.e. after a change was already live on `main`. Sam, on moving work to
Claude Code: "it did end up causing alot of failed recurring runs".

# @vacuity 🔴 the PR workflow triggers on pull requests
#   file: .github/workflows/pr-tests.yml
#   find:   pull_request:
#   with:   push:
#
# @vacuity 🔴🔴 the PR loop is the collector's loop, not a weaker copy
#   file: .github/workflows/pr-tests.yml
#   find:               test_vacuity.py) echo 2400 ;;
#   with:               test_vacuity.py) echo 1 ;;
"""
import os
import re

from tcheck import ck

ROOT = os.path.dirname(os.path.abspath(__file__))
WF = os.path.join(ROOT, ".github", "workflows")
PR = open(os.path.join(WF, "pr-tests.yml"), encoding="utf-8").read()
CO = open(os.path.join(WF, "collect.yml"), encoding="utf-8").read()


def loop(src):
    """The Tests step's run body, comments and GITHUB_OUTPUT redirects dropped."""
    lines = src.splitlines()
    i = next(k for k, l in enumerate(lines) if l.strip() == "- name: Tests")
    j = next(k for k in range(i, len(lines)) if lines[k].strip() == "run: |")
    out = []
    for l in lines[j + 1:]:
        if l.startswith("      - "):
            break
        s = l.strip()
        if not s or s.startswith("#"):
            continue
        out.append(s.replace(' >> "$GITHUB_OUTPUT"', ""))
    return out


ck("🔴 pr-tests.yml runs on pull requests to main",
   re.search(r"^on:\n  pull_request:\n    branches: \[main\]", PR, re.M) is not None,
   "a PR check that does not fire on a PR checks nothing")
ck("⛔ pr-tests.yml has NO schedule block",
   "schedule:" not in PR and "cron:" not in PR,
   "scheduled runs are attributed to whoever last edited a cron block; "
   "a cron-free file is the one an agent may edit safely")
ck("⛔ pr-tests.yml is read-only",
   re.search(r"^permissions:\n  contents: read\s*$", PR, re.M) is not None
   and "contents: write" not in PR and "git push" not in PR,
   "the check that decides whether to merge must not be able to change the repo")
a, b = loop(PR), loop(CO)
ck("🔴🔴 the PR test loop is the collector's loop, line for line",
   a == b and len(a) > 20,
   "a weaker copy would pass PRs the collector then fails on main — the "
   "exact failure this file exists to prevent. Differing lines: %s"
   % ([x for x in a if x not in b][:3] + [x for x in b if x not in a][:3]))
ck("✅ ...and it still refuses a tree the tests modified",
   "The tests must not have modified the tree" in PR and "git status --porcelain" in PR,
   "same guard as collect.yml")
