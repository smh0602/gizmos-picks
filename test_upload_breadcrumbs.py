#!/usr/bin/env python3
r"""EVERY PAGE AN UPLOAD FILE SENDS SAM TO COMES WITH THE BREADCRUMB IT SHOWS.

🔴 WHAT HAPPENED `[2026-11-21, review]`. UPLOAD-browser-render-once.md's undo
said "in step 2 open <the old .github/workflows/browser.yml> instead". Step 2
then has Sam check that the breadcrumb reads "gizmos-picks / docs / upload /
browser.yml", and the page that link opens reads "gizmos-picks / .github /
workflows / browser.yml". Followed literally, the check fails and Sam cannot
tell whether he is on the right page (CLAUDE.md rule 4: which page, what the
breadcrumb at the top should read, at every step). Caught by review before
merge; the undo is now its own list, with its own breadcrumb.

✅ THE CLASS, NOT THE INSTANCE: every docs/upload/*.md, two rules.
  A. A GitHub link Sam is told to OPEN ("Open", "open", "Go to" right before
     it) is followed, before the next link, by the breadcrumb that page
     shows. The 11-21 undo opened a link with no breadcrumb of its own and
     borrowed step 2's.
  B. Every breadcrumb a file states is the breadcrumb of the link it belongs
     to: the nearest link before it ("gizmos-picks / " + the link's path,
     " / " between the parts). A breadcrumb with a `<placeholder>` (runner
     image's "For each link below") must fit every link after it up to the
     next heading, and there must be one.
  ⚠️ Struck text (~~...~~) is an old instruction, not one Sam follows, and
     is read as blank. A link Sam is told to DOWNLOAD ("download <link> with
     Download raw file") is not checked by A: the button, not the page, is
     the step there.
⚠️ WHAT THIS CANNOT SEE: a link whose verb is not "open" or "go to"
("visit", "click this"), a breadcrumb not written in **bold**, and a step
that sends Sam to another step's link in words ("as in step 2").
✅ Driven on every docs/upload/*.md on the day it was written: base 85c434f01
(17 files, 44 breadcrumbs, 31 opened links) and this branch (18, 47, 34) all
agree; it fired only on the first version of UPLOAD-browser-render-once.md's
undo (1ecf4576e, its line 97). `[2026-11-22]` Tested together with the open
football relay pull request, it fired once more: that PR's
UPLOAD-collect-football-relay.md opened relay-beat.json with no breadcrumb
(fixed there in 7a2eeb1d9).

# @vacuity 🔴 the undo's link with no breadcrumb of its own is caught (the 11-21 shape)
#   file: docs/upload/UPLOAD-browser-render-once.md
#   find: Its breadcrumb reads **gizmos-picks / .github / workflows / browser.yml**
#   with: It reads **gizmos-picks / .github / workflows / browser.yml**
#
# @vacuity 🔴 ...and a breadcrumb that is not its link's (step 2's, borrowed)
#   file: docs/upload/UPLOAD-browser-render-once.md
#   find: Its breadcrumb reads **gizmos-picks / .github / workflows / browser.yml**
#   with: Its breadcrumb reads **gizmos-picks / docs / upload / browser.yml**
#
# @vacuity ⚠️ the class: any upload file's opened link that loses its breadcrumb
#   file: docs/upload/UPLOAD-runs.md
#   find: — the breadcrumb at the top reads **gizmos-picks / docs / upload / runs.yml**.
#   with: — the page at the top reads **gizmos-picks / docs / upload / runs.yml**.
#
# @vacuity ⚠️ a placeholder breadcrumb must fit every link after it
#   file: docs/upload/UPLOAD-runner-image.md
#   find: **gizmos-picks / docs / upload / <the file name>**.
#   with: **gizmos-picks / .github / workflows / <the file name>**.
"""
import glob
import os
import re

from tcheck import ck, eq, note, section

ROOT = os.path.dirname(os.path.abspath(__file__))
URL = re.compile(r"https://github\.com/smh0602/gizmos-picks/(?:blob|tree)/[\w.-]+/([^\s)*,`|]+)")
CRUMB = re.compile(r"breadcrumb[^*\n]*(?:\n[^*\n]*)?\*\*([^*]+)\*\*")
OPENED = re.compile(r"(?:\b[Oo]pen|\bGo to)\W{0,6}$")
HEADING = re.compile(r"(?m)^#{1,6} ")
STRUCK = re.compile(r"~~.*?~~", re.S)


def crumb_of(path):
    """The breadcrumb GitHub shows for a repo path."""
    return "gizmos-picks / " + " / ".join(p for p in path.rstrip(".").split("/") if p)


def problems(text):
    """[(line, what is wrong)] for one upload file's text."""
    text = STRUCK.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)
    line = lambda i: text.count("\n", 0, i) + 1
    urls = list(URL.finditer(text))
    out = []
    for k, u in enumerate(urls):                                      # rule A
        if not OPENED.search(text[max(0, u.start() - 12):u.start()].replace("\n", " ")):
            continue
        end = urls[k + 1].start() if k + 1 < len(urls) else len(text)
        if not CRUMB.search(text, u.end(), end):
            out.append((line(u.start()), "opens %s with no breadcrumb of its own" % u.group(1)))
    for c in CRUMB.finditer(text):                                    # rule B
        claim = " ".join(c.group(1).split())
        if "<" in claim:
            nxt = HEADING.search(text, c.end())
            after = URL.finditer(text, c.end(), nxt.start() if nxt else len(text))
            pat = re.compile(re.sub(r"<[^>]*>", "[^ /]+", re.escape(claim).replace(r"\<", "<")
                                    .replace(r"\>", ">")) + "$")
            paths = [u.group(1) for u in after]
            bad = [p for p in paths if not pat.match(crumb_of(p))]
            if not paths or bad:
                out.append((line(c.start()), "%r fits no link after it%s" % (
                    claim, "" if not paths else ": " + ", ".join(bad))))
            continue
        prev = [u for u in urls if u.end() <= c.start()]
        if not prev:
            out.append((line(c.start()), "%r follows no link" % claim))
        elif crumb_of(prev[-1].group(1)) != claim:
            out.append((line(c.start()), "%r, but its link %s shows %r" % (
                claim, prev[-1].group(1), crumb_of(prev[-1].group(1)))))
    return out


# ══════════════════════════════════════════════════════════════════════
section("1. THE RULES, ON PLANTED TEXT")
# ══════════════════════════════════════════════════════════════════════
G = "https://github.com/smh0602/gizmos-picks/"
for text, n, why in (
        ("2. Open %sblob/main/docs/upload/x.yml\n   and check the breadcrumb at the top reads "
         "**gizmos-picks / docs / upload /\n   x.yml**.\n" % G, 0,
         "an opened link and its own breadcrumb, across a line break"),
        ("1. Go to **%stree/main/.github/workflows**\n2. Check the breadcrumb reads\n"
         "   **gizmos-picks / .github / workflows**.\n" % G, 0, "   ...`Go to **link**`, breadcrumb below"),
        ("2. Open %sblob/main/docs/upload/x.yml and check the breadcrumb reads "
         "**gizmos-picks / docs / upload / x.yml**.\n\n## Undo\n\nUpload the previous file the "
         "same way: in step 2 open %sblob/85c434f01/.github/workflows/x.yml\ninstead.\n" % (G, G), 1,
         "🔴🔴 the 11-21 undo: a link opened in place of step 2's, with no breadcrumb of its own"),
        ("2. Open %sblob/abc/.github/workflows/x.yml\n   Its breadcrumb reads "
         "**gizmos-picks / docs / upload / x.yml**.\n" % G, 1,
         "🔴 a breadcrumb that is not its link's"),
        ("If you upload only this file: download %sblob/main/docs/upload/x.yml with **Download raw "
         "file**, then in %stree/main/.github/workflows\n(breadcrumb **gizmos-picks / .github / "
         "workflows**) click **Add file**.\n" % (G, G), 0,
         "a link to DOWNLOAD from is not a page to check; its breadcrumb is the folder link's"),
        ("2. Check the breadcrumb at the top reads\n   **gizmos-picks / docs / upload / <the file "
         "name>**.\n\n| 1 | %sblob/main/docs/upload/a.yml |\n| 2 | %sblob/main/docs/upload/b.yml |"
         "\n\n## Step 3\n\n1. Go to %stree/main/.github/workflows\n2. Check the breadcrumb reads "
         "**gizmos-picks / .github / workflows**.\n" % (G, G, G), 0,
         "a <placeholder> breadcrumb fits every link after it up to the next heading"),
        ("2. Check the breadcrumb at the top reads **gizmos-picks / docs / upload / <the file "
         "name>**.\n\n| 1 | %sblob/main/docs/upload/a.yml |\n| 2 | %sblob/main/.github/workflows/"
         "b.yml |\n" % (G, G), 1, "🔴 ...and one that does not fit a link after it is caught"),
        ("Check the breadcrumb reads **gizmos-picks / docs / upload / <the file name>**.\n\n## Next\n"
         "%sblob/main/docs/upload/a.yml\n" % G, 1, "🔴 ...as is one with no link after it"),
        ("Check the breadcrumb reads **gizmos-picks / .github / workflows**.\n", 1,
         "🔴 a breadcrumb that follows no link"),
        ("~~2. Open %sblob/main/docs/upload/old.yml (breadcrumb **gizmos-picks / docs**)~~\n"
         "2. Open %sblob/main/docs/upload/x.yml (breadcrumb **gizmos-picks / docs / upload / "
         "x.yml**)\n" % (G, G), 0, "⚠️ struck text is an old instruction, read as blank")):
    eq(len(problems(text)), n, why)

# ══════════════════════════════════════════════════════════════════════
section("2. 🔴🔴 EVERY UPLOAD FILE: EVERY OPENED LINK HAS ITS OWN BREADCRUMB, AND IT AGREES")
# ══════════════════════════════════════════════════════════════════════
DOCS = sorted(glob.glob(os.path.join(ROOT, "docs", "upload", "*.md")))
TEXT = {os.path.basename(p): open(p, encoding="utf-8").read() for p in DOCS}
_crumbs = sum(len(CRUMB.findall(STRUCK.sub("", t))) for t in TEXT.values())
_opened = sum(1 for t in TEXT.values() for u in URL.finditer(t)
              if OPENED.search(t[max(0, u.start() - 12):u.start()].replace("\n", " ")))
# ⚠️ rule 67: a scanner that sees nothing passes everything.
ck(len(DOCS) >= 15 and _crumbs >= 30 and _opened >= 20,
   "⚠️ the upload files, their breadcrumbs and their opened links were read",
   "%d files, %d breadcrumbs, %d opened links" % (len(DOCS), _crumbs, _opened))
BAD = [(f, ln, why) for f, t in sorted(TEXT.items()) for ln, why in problems(t)]
ck(not BAD, "🔴🔴 every breadcrumb an upload file asks Sam to check is the one its page shows",
   "\n".join("       %s:%d %s" % b for b in BAD))
_undo = TEXT.get("UPLOAD-browser-render-once.md", "")
ck("/blob/85c434f01b14146062e2fb4ac753ccbc7ef8013a/.github/workflows/browser.yml" in _undo,
   "⚠️ the render-once undo link is still there to be checked")
note("%d upload files: %d breadcrumbs, %d opened links" % (len(DOCS), _crumbs, _opened))
