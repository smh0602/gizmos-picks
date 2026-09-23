#!/usr/bin/env python3
"""test_staged_uploads.py — a cron workflow staged for Sam to upload.

`[Sam, 2026-09-23]` "Count a cron workflow staged under docs/upload as
declared, deduplicated by file name with .github/workflows, so CRON TOTAL
is correct both before and after I upload. Keep the guards just as strict:
the uploaded file must match the staged copy exactly; runs_report flags a
staged cron that still hasn't been uploaded after 48 hours."

⚠️ ITS OWN FILE, AND SMALL ON PURPOSE. The vacuity sweep runs every
declaring file twice per mutation and sits near its 2400s limit (2401s and
2400s on PR #143). Measured locally: this file 0.36s, test_runs_report.py
1.8s — so moving these out saves little. ⛔ It is NOT the fix for that
limit, which belongs to the sweep itself.

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
# @vacuity an uploaded copy that differs from its staged copy is flagged
#   file: wfparse.py
#   find:         if a != b:
#   with:         if False:
"""
import datetime
import os
import shutil
import sys
import tempfile

from tcheck import ck, section

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import runs_report as R  # noqa: E402

UTC = datetime.timezone.utc

section("21. 🔴 STAGED CRONS: COUNTED, MATCHED, AND NEVER LEFT UNUPLOADED")
# `[Sam, 2026-09-23]` "Count a cron workflow staged under docs/upload as
# declared, deduplicated by file name with .github/workflows, so CRON TOTAL
# is correct both before and after I upload. Keep the guards just as strict."
import wfparse as _W  # noqa: E402

ck(_W.staged_mismatches(ROOT) == [],
   "🔴🔴 every uploaded cron workflow matches its staged copy exactly",
   "⛔ the count dedupes by NAME, which is only honest if the two copies are "
   "the same file. Differ: %s" % _W.staged_mismatches(ROOT))


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
_t = _stree(deployed={"a.yml": _Y1}, staged={"a.yml": _Y1, "b.yml": _Y2})
ck(_W.cron_total(_t) == 3,
   "🔴 a staged cron counts BEFORE upload, and an uploaded one counts ONCE",
   "a.yml in both folders (1) + b.yml staged only (2) = 3. got %d" % _W.cron_total(_t))
_t2 = _stree(deployed={"a.yml": _Y1, "b.yml": _Y2}, staged={"a.yml": _Y1, "b.yml": _Y2})
ck(_W.cron_total(_t2) == 3,
   "   ✅ ...and the total is the SAME after b.yml is uploaded — no red window")
_t3 = _stree(deployed={"a.yml": _Y1.replace("1 1", "9 9")}, staged={"a.yml": _Y1})
ck(_W.staged_mismatches(_t3) == ["a.yml"],
   "⛔ ...an uploaded file that differs from its staged copy IS flagged")
_t4 = _stree(deployed={"a.yml": _Y1.replace("\n", "\r\n")}, staged={"a.yml": _Y1})
ck(_W.staged_mismatches(_t4) == [],
   "   ⚠️ ...while a CRLF upload from Windows is the same file, not a mismatch")

_NOW21 = datetime.datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def _fetch_merged(hours_ago):
    def f(path):
        if path.startswith("commits?path="):
            return [{"sha": "abc", "commit": {"committer": {"date": "2026-09-01T00:00:00Z"}}}]
        if path == "commits/abc/pulls":
            t = _NOW21 - datetime.timedelta(hours=hours_ago)
            return [{"merged_at": t.strftime("%Y-%m-%dT%H:%M:%SZ")}]
        raise AssertionError(path)
    return f


def _fetch_fails(path):
    raise RuntimeError("no network")


_ts = _stree(staged={"b.yml": _Y2})
ck(R.stale_uploads(_ts, _NOW21, _fetch_merged(10)) == [],
   "✅ a staged cron merged 10h ago is NOT yet flagged",
   "⛔ the clock is the MERGE, not the branch commit (2026-09-01 here)")
_s50 = R.stale_uploads(_ts, _NOW21, _fetch_merged(50))
ck([s["file"] for s in _s50] == ["b.yml"] and _s50[0]["hours"] == 50.0,
   "🔴🔴 a staged cron still not uploaded 48h after its PR merged IS flagged",
   "got %r" % _s50)
ck([s["file"] for s in R.stale_uploads(_ts, _NOW21, _fetch_fails)] == ["b.yml"],
   "⛔ ...and when GitHub cannot say when, it is REPORTED, never assumed recent")
ck(R.stale_uploads(_t2, _NOW21, _fetch_fails) == [],
   "   ✅ ...and an uploaded workflow is never flagged, whatever GitHub says")
ck("stale_uploads(" in open(os.path.join(ROOT, "runs_report.py"), encoding="utf-8").read().split("def main(")[1],
   "⚠️ ...and main() actually runs the check",
   "⛔ a finder nothing calls is a guard in name only")
for _d in (_t, _t2, _t3, _t4, _ts):
    shutil.rmtree(_d, ignore_errors=True)
