#!/usr/bin/env python3
r"""test_staged_uploads.py — a cron workflow staged for Sam to upload.

`[Sam, 2026-09-23]` "Count a cron workflow staged under docs/upload as
declared, deduplicated by file name with .github/workflows, so CRON TOTAL
is correct both before and after I upload. Keep the guards just as strict:
the uploaded file must match the staged copy exactly; runs_report flags a
staged cron that still hasn't been uploaded after 48 hours."

🔴 `[Sam, 2026-09-23, on PR #145]` "A staged copy that differs from the
deployed one is a PENDING UPLOAD, not a failure. For those pairs, CRON
TOTAL counts the staged version, because that is what will be live.
runs_report flags a pending upload 48 hours after its PR merged, the same
clock as a new staged file. Test both directions with mutations."
⛔ ~~a differing pair failed this file immediately~~ — that is exactly what
an update to an existing cron workflow looks like before Sam uploads it, so
#145 (vacuity.yml) would have turned main red the moment it merged. The
strictness now lives on the 48-hour clock: a wrong upload stays PENDING
and is flagged there.

⚠️ ITS OWN FILE, AND SMALL ON PURPOSE. The vacuity sweep runs every
declaring file twice per mutation. Measured locally: this file 0.36s,
test_runs_report.py 1.8s — so moving these out saves little. ⛔ It is NOT
the fix for that sweep's time limit, which belongs to the sweep itself.

# @vacuity a staged cron counts only once its name is unique across both folders
#   file: wfparse.py
#   find:             e = out.setdefault(f, {"crons": n, "deployed": False, "staged": False})
#   with:             e = out.setdefault(f + where, {"crons": n, "deployed": False, "staged": False})
#
# @vacuity a staged cron older than 48 hours is flagged
#   file: runs_report.py
#   find:         if hours is None or hours >= STAGED_UPLOAD_HOURS:
#   with:         if hours is None:
#
# @vacuity a staged copy that differs from the deployed one is PENDING
#   file: wfparse.py
#   find:         e["pending"] = bool(e["deployed"] and e["staged"] and not _same(root, f))
#   with:         e["pending"] = False
#
# @vacuity a pending pair counts at its STAGED version
#   file: wfparse.py
#   find:             e["crons"] = staged_n[f]     # what WILL be live once Sam uploads
#   with:             pass
#
# @vacuity a pending update is timed like a new staged file
#   file: runs_report.py
#   find:         if not v["staged"] or (v["deployed"] and not v["pending"]):
#   with:         if not v["staged"] or v["deployed"]:
#
# @vacuity a CRLF upload from Windows is the same file, not a pending one
#   file: wfparse.py
#   find:     a, b = (open(os.path.join(root, sub, f), encoding="utf-8").read().replace("\r", "")
#   with:     a, b = (open(os.path.join(root, sub, f), encoding="utf-8", newline="").read()
"""
import datetime
import os
import shutil
import sys
import tempfile

from tcheck import ck, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as R  # noqa: E402
import wfparse as _W  # noqa: E402

UTC = datetime.timezone.utc


def _stree(deployed=None, staged=None):
    d = tempfile.mkdtemp(prefix="staged-")
    for sub, files in ((".github/workflows", deployed or {}), ("docs/upload", staged or {})):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
        for name, text in files.items():
            with open(os.path.join(d, sub, name), "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
    return d


_Y1 = 'on:\n  schedule:\n    - cron: "1 1 * * *"\n'
_Y2 = 'on:\n  schedule:\n    - cron: "2 2 * * *"\n    - cron: "3 3 * * *"\n'
_NOW = datetime.datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def _fetch_merged(hours_ago):
    def f(path):
        if path.startswith("commits?path="):
            return [{"sha": "abc", "commit": {"committer": {"date": "2026-09-01T00:00:00Z"}}}]
        if path == "commits/abc/pulls":
            t = _NOW - datetime.timedelta(hours=hours_ago)
            return [{"merged_at": t.strftime("%Y-%m-%dT%H:%M:%SZ")}]
        raise AssertionError(path)
    return f


def _fetch_fails(path):
    raise RuntimeError("no network")


_trees = []


def T(**kw):
    d = _stree(**kw)
    _trees.append(d)
    return d


section("1. THE REAL REPO — every staged file is accounted for")
_pend = _W.pending_uploads(ROOT)
_undeployed = sorted(f for f, v in _W.cron_files(ROOT).items() if v["staged"] and not v["deployed"])
_need = _pend + _undeployed
_nodoc = [f for f in _need if not os.path.exists(os.path.join(ROOT, "docs", "upload",
                                                              "UPLOAD-%s.md" % f[:-4]))]
ck(not _nodoc,
   "🔴 every staged cron still waiting for Sam has its UPLOAD instructions",
   "⛔ Sam's rule 4: anything he must upload by hand comes with an UPLOAD .md. "
   "missing for: %s" % _nodoc)
note("⚪ waiting for upload right now — pending updates %s, never uploaded %s. ⚠️ "
     "Not a failure: `runs_report` flags either 48h after its PR merged." % (_pend, _undeployed))

section("2. COUNTING — before, during and after an upload")
_t = T(deployed={"a.yml": _Y1}, staged={"a.yml": _Y1, "b.yml": _Y2})
ck(_W.cron_total(_t) == 3,
   "🔴 a NEW staged cron counts before upload, and an uploaded one counts ONCE",
   "a.yml in both (1) + b.yml staged only (2) = 3. got %d" % _W.cron_total(_t))
_t2 = T(deployed={"a.yml": _Y1, "b.yml": _Y2}, staged={"a.yml": _Y1, "b.yml": _Y2})
ck(_W.cron_total(_t2) == 3 and _W.pending_uploads(_t2) == [],
   "   ✅ ...the total is the SAME after b.yml is uploaded, and nothing is pending")

section("3. 🔴🔴 AN UPDATE TO AN EXISTING CRON WORKFLOW IS PENDING, NOT A FAILURE")
_t3 = T(deployed={"a.yml": _Y1}, staged={"a.yml": _Y2})
ck(_W.pending_uploads(_t3) == ["a.yml"],
   "🔴 a staged copy that DIFFERS from the deployed one is a PENDING upload",
   "⛔ that is what an update looks like until Sam uploads it. got %r"
   % _W.pending_uploads(_t3))
ck(_W.cron_total(_t3) == 2,
   "🔴🔴 ...and CRON TOTAL counts the STAGED version (2), because that is "
   "what will be live",
   "⛔ counting the deployed one (1) would change the total at upload — the "
   "red window again, one level down. got %d" % _W.cron_total(_t3))
_t3u = T(deployed={"a.yml": _Y2}, staged={"a.yml": _Y2})
ck(_W.cron_total(_t3u) == _W.cron_total(_t3) and _W.pending_uploads(_t3u) == [],
   "   ✅ ...so uploading the update changes neither the total nor anything "
   "else: pending clears, total stays 2")
_t4 = T(deployed={"a.yml": _Y1.replace("\n", "\r\n")}, staged={"a.yml": _Y1})
ck(_W.pending_uploads(_t4) == [],
   "⚠️ a CRLF upload from Windows is the SAME file, not a pending one",
   "⛔ otherwise every correct Windows upload would read as a wrong one")

section("4. 🔴🔴 THE 48-HOUR CLOCK — new files AND pending updates")
_ts = T(staged={"b.yml": _Y2})
ck(R.stale_uploads(_ts, _NOW, _fetch_merged(10)) == [],
   "✅ a NEW staged cron merged 10h ago is NOT yet flagged",
   "⛔ the clock is the MERGE, not the branch commit (2026-09-01 here)")
_s50 = R.stale_uploads(_ts, _NOW, _fetch_merged(50))
ck([(s["file"], s["kind"]) for s in _s50] == [("b.yml", "new")] and _s50[0]["hours"] == 50.0,
   "🔴 a NEW staged cron still not uploaded 48h after its PR merged IS flagged",
   "got %r" % _s50)
ck(R.stale_uploads(_t3, _NOW, _fetch_merged(10)) == [],
   "✅ a PENDING update merged 10h ago is NOT yet flagged")
_p50 = R.stale_uploads(_t3, _NOW, _fetch_merged(50))
ck([(s["file"], s["kind"]) for s in _p50] == [("a.yml", "update")],
   "🔴🔴 a PENDING update still not uploaded 48h after its PR merged IS flagged",
   "⛔ the same clock as a new file — and it is also how a WRONG upload is "
   "caught: it stays pending. got %r" % _p50)
ck("update" in R.render_stale(_p50) and "differs" in R.render_stale(_p50),
   "   ⚠️ ...and the message says it is an UPDATE, not a file that never fired")
ck([s["file"] for s in R.stale_uploads(_ts, _NOW, _fetch_fails)] == ["b.yml"]
   and [s["file"] for s in R.stale_uploads(_t3, _NOW, _fetch_fails)] == ["a.yml"],
   "⛔ when GitHub cannot say when, both kinds are REPORTED, never assumed recent")
ck(R.stale_uploads(_t2, _NOW, _fetch_fails) == []
   and R.stale_uploads(_t4, _NOW, _fetch_fails) == [],
   "   ✅ ...and an uploaded, matching workflow is never flagged, whatever "
   "GitHub says")
ck("stale_uploads(" in open(os.path.join(ROOT, "runs_report.py"), encoding="utf-8").read().split("def main(")[1],
   "⚠️ ...and main() actually runs the check",
   "⛔ a finder nothing calls is a guard in name only")
for _d in _trees:
    shutil.rmtree(_d, ignore_errors=True)
