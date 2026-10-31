#!/usr/bin/env python3
"""offseason.py — THE TREE AS IT LOOKS WHEN NO LEAGUE HAS A GAME.

🔴 WHY `[Sam, 2026-10-30: "we need to fix it for the long term as well"]`.
Tests that lean on today's live board pass all season and go red the day a
league goes dark: #298 and #301 when the MLB season wound down, #329 when
board.json finally emptied (every collect run red for two days). Football goes
dark in February and nothing would have said so until then.

✅ pr-tests' `offseason` job runs this on its own throwaway checkout, then the
`tests` job's own loop: a test that needs a game on a live file fails at the
PR, in season or not. `test_offseason.py`.

⛔ ONLY WHAT A REAL OFF-SEASON EMPTIES. Published cards and graded records
stay: nothing rewrites them when a season ends. Never run on the real tree;
it refuses a tree that is not told it may (`--yes`, or `blank()` from a test).
"""
import gzip
import json
import os
import sys

LATEST = ("data/latest", "data/nfl/latest", "data/ncaaf/latest")
# file -> the lists a league with no games leaves empty
DARK = {
    "board.json": ("games",),
    "props.json.gz": ("games",),
    "game-lines.json.gz": ("games", "parlays"),
    "dossiers.json.gz": ("dossiers",),
    "fb-model.json": ("picks", "win_chances"),
    "fb-props-model.json": ("picks",),
    "winners.json": ("week",),
    "mlb-game-model.json": ("games",),
}


def _open(path, mode):
    if path.endswith(".gz"):
        return gzip.open(path, mode + "t", encoding="utf-8")
    return open(path, mode, encoding="utf-8")


def blank(root):
    """Empty every DARK list under `root`. -> ["<dir>/<file>:<key>"] emptied."""
    done = []
    for lg in LATEST:
        for name, keys in DARK.items():
            path = os.path.join(root, lg, name)
            if not os.path.exists(path):
                continue
            with _open(path, "r") as fh:
                doc = json.load(fh)
            for k in keys:
                if k in doc:
                    doc[k] = []
                    done.append("%s/%s:%s" % (lg, name, k))
            with _open(path, "w") as fh:
                json.dump(doc, fh)
    return done


if __name__ == "__main__":
    if sys.argv[1:] != ["--yes"]:
        print("usage: offseason.py --yes  (empties live files: a throwaway checkout only)")
        sys.exit(2)
    got = blank(".")
    print("off-season tree: %d list(s) emptied" % len(got))
    sys.exit(0 if got else 1)
