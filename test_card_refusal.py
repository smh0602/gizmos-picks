#!/usr/bin/env python3
"""A REFUSED CARD IS A KNOWN STATE — BUT NOT FOREVER.

🔴 THE STATE THIS EXISTS TO CATCH, AND IT IS THE ONE WE WERE IN.
`[2026-09-04]` Sam accepted T37, `card_gate` kept the run green, and
**every card rebuild was still reverted** — so Gizmo's Picks stopped
updating entirely. **Green build, frozen product, no alarm.** That is the
same failure this repo keeps learning about, pointing the other way: on
2026-08-28 the page looked fresh and was stale; here the BUILD looks
healthy while the board has stopped moving.

⛔ THE DOWNGRADE IS RIGHT AND MUST STAY. An alarm firing every fifteen
minutes for a settled decision gets ignored, and ignoring red is how the
original staleness survived a whole day.
✅ **IT IS THE UNBOUNDEDNESS THAT WAS WRONG.** An accepted failure buys
quiet for a DECISION, not permanent silence about a frozen board.

⚠️ THE SIGNAL IS THE CARD'S OWN AGE, not the failure file's.
`card-verify-failure.txt` is rewritten on every pass, so it can only say
when the LAST refusal happened and never when the FIRST one did. The
card's age is exactly "how long since a card published".

🔒 The 48-hour grace was chosen with Sam before it had ever fired.
"""
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import datetime

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
import freshness as F                                   # noqa: E402

UTC = datetime.timezone.utc
fails = []


def ck(cond, label, detail=""):
    print(f"  {'ok  ' if cond else '🔴 FAIL'} {label:<58} {detail}")
    if not cond:
        fails.append(label)


def build(tmp, card_age_h, refused, now=None):
    """A tree where EVERYTHING is fresh except the card, whose stamp is
    `card_age_h` hours old. ⚠️ Stamps are written INTO the files: this
    project bans `getmtime` for freshness, and so does its fixture."""
    now = now or datetime.datetime.now(UTC)
    fresh = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    old = (now - datetime.timedelta(hours=card_age_h)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    for m, (kind, path), _t, _p, _w in F.contract(data="data", picks="picks",
                                                  now=now):
        full = os.path.join(tmp, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        stamp = old if m == "card" else fresh
        body = {"built_at": stamp, "generated_at": stamp, "pulled_at": stamp,
                "written_at": stamp, "kind": "MARKET"}
        if kind == "dir":
            os.makedirs(full, exist_ok=True)
            with open(os.path.join(full, "us.json"), "w") as fh:
                json.dump(body, fh)
        elif path.endswith(".gz"):
            with gzip.open(full, "wt") as fh:
                json.dump(body, fh)
        else:
            with open(full, "w") as fh:
                json.dump(body, fh)
    if refused:
        with open(os.path.join(tmp, "data/latest/card-verify-failure.txt"),
                  "w") as fh:
            fh.write("verify_card FAILED\nFAILURES: T37: the artifact\n")


def run(card_age_h, refused):
    t = tempfile.mkdtemp()
    try:
        build(t, card_age_h, refused)
        for f in ("verify_freshness.py", "freshness.py"):
            shutil.copy(os.path.join(REPO, f), t)
        p = subprocess.run([sys.executable, "verify_freshness.py"], cwd=t,
                           capture_output=True, text=True,
                           env={**os.environ, "LEAGUE": "mlb"})
        return p.returncode, p.stdout + p.stderr
    finally:
        shutil.rmtree(t, ignore_errors=True)


print("\n1. THE GRACE IS REAL — a fresh refusal does NOT fail the run")
print("   ⛔ This is the behaviour that must survive. Removing it brings")
print("   back the 22 consecutive red runs of 2026-08-29.")
# ⚠️ 30 hours, not 6: the card is due DAILY, so a 6-hour-old card is not
# stale at all and never reaches the warning path. The state worth pinning
# is STALE **and** REFUSED **and** inside the grace.
rc, out = run(30, refused=True)
ck(rc == 0, "stale 30 hours and refused -> run stays green", f"rc={rc}")
ck("REFUSED for" in out, "  and the warning states how long it has been")
ck("grace left" in out,
   "🔴 and how much grace is left — visible BEFORE it bites")
rc0, out0 = run(6, refused=True)
ck(rc0 == 0, "and a refusal on a card that is not even due yet is quiet",
   f"rc={rc0}")

print("\n2. 🔴 PAST THE GRACE IT IS A FROZEN BOARD, AND THAT FAILS")
rc2, out2 = run(50, refused=True)
ck(rc2 == 1, "refused for 50 hours -> the run goes red", f"rc={rc2}")
ck("THE CARD IS FROZEN" in out2, "  and it says the board has stopped moving")
ck("buys quiet for a DECISION" in out2,
   "  and why an acceptance does not cover this")
ck("48-hour grace" in out2, "  naming the bound it crossed")

print("\n3. THE BOUNDARY IS WHERE IT SAYS IT IS")
rc3, _ = run(47, refused=True)
ck(rc3 == 0, "47 hours -> still inside the grace", f"rc={rc3}")
rc4, _ = run(49, refused=True)
ck(rc4 == 1, "49 hours -> outside it", f"rc={rc4}")
ck(F.CARD_REFUSED_GRACE_MIN == 48 * 60,
   "⛔ the constant is 48h and is not tuned to fit a run",
   f"{F.CARD_REFUSED_GRACE_MIN}m")

print("\n4. ⛔ NO REFUSAL FILE -> A STALE CARD IS HARD, EXACTLY AS BEFORE")
print("   The downgrade must apply ONLY to a card that was REFUSED.")
rc5, out5 = run(50, refused=False)
ck(rc5 == 1, "a 50h-old card with no refusal still fails", f"rc={rc5}")
ck("FROZEN" not in out5,
   "  and it is reported as ordinary staleness, not as a freeze")

print("\n5. A HEALTHY DAY IS STILL A PASS")
rc6, out6 = run(2, refused=False)
ck(rc6 == 0, "everything current -> green", f"rc={rc6}")
ck("PASS" in out6, "  and says so")

print()
if fails:
    print(f"🔴 {len(fails)} FAILURE(S)")
    for f in fails:
        print(f"   - {f}")
    sys.exit(1)
print("✅ a refused card is quiet while somebody is acting, loud once nobody is")
