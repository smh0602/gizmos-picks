#!/usr/bin/env python3
"""champions_named.py — THE TREE AS IT LOOKS ONCE A CHAMPION SWITCH IS MERGED. `[2026-11-08]`

🔴 WHY. #339, college's first champion switch (HC), turned pr-tests red on files whose checks
were right but quietly assumed that no league names a champion (§3j of research/fb_refit_spec.md).
That class shows only on the day a switch merges, the way an off-season red shows only when a
league goes dark. So pr-tests' `champion` job runs this on its own throwaway checkout, then the
`tests` job's own loop: a test that leans on "no champion" fails at its PR, not on Sam's switch.
`test_pr_champion.py`.

✅ It names one champion in every league that names NONE, through `fb_refit.set_champion` (the
weekly job's own branch edit, so this is the change a merged switch makes). One shape per league:
NFL `SM` (the score model: its own predicted score, one input) and college `HC` (history seasons,
the switch that is waiting). ⛔ A league that already names one keeps it. Never on the real tree:
it refuses a tree it is not told it may change (`--yes`).
"""
import glob
import os
import sys

NAMED = {"nfl": "SM", "ncaaf": "HC"}


def drop_bytecode(root):
    """Remove every compiled copy of fb_model.py under `root` (-> the paths removed).
    🔴 `[2026-11-08]` PR #344's first run: this script imports fb_model (through fb_refit) BEFORE it
    rewrites it, and None -> "SM" / "HC" keeps the file's size. Rewritten in the same second, the
    cached bytecode still matched the file's (mtime, size), so every test in the job imported the OLD
    module: the job ran with no champion named and stayed green. test_pr_champion.py's bench caught
    it on the Linux runner."""
    gone = sorted(glob.glob(os.path.join(root, "__pycache__", "fb_model.*.pyc")))
    for p in gone:
        os.remove(p)
    return gone


def name(src):
    """-> (fb_model.py's text with NAMED's champion in every league that names none, [leagues named])."""
    import fb_refit
    done = []
    for lg, n in NAMED.items():
        if fb_refit.names_none(src, lg):
            src = fb_refit.set_champion(src, lg, n)
            done.append(lg)
    return src, done


if __name__ == "__main__":
    if sys.argv[1:] != ["--yes"]:
        print("usage: champions_named.py --yes  (edits fb_model.py: a throwaway checkout only)")
        sys.exit(2)
    sys.path.insert(0, os.getcwd())
    path = os.path.join(os.getcwd(), "fb_model.py")
    with open(path, encoding="utf-8") as fh:
        src, got = name(fh.read())
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    drop_bytecode(os.getcwd())          # ⛔ never let a stale compiled fb_model shadow the edit
    print("champions named: %s" % (", ".join("%s %s" % (lg, NAMED[lg]) for lg in got) or
                                   "none (every league already names one)"))
    sys.exit(0)
