#!/usr/bin/env python3
"""
🔴 AN OPEN FOOTBALL TAB FOLLOWS THE DATA, IN BOTH FOOTBALL LEAGUES.

THE DEFECT, VERIFIED 2026-11-13 IN THE SOURCE: every football file the page
reads (FBCARD, FBBOARD, FBPROPS, FBREC, FBDETAIL, WINNERS, ...) was memoised
the first time a tab asked for it and never let go, and the page's timed
refreshes (the 180 s check and the 60 s kickoff redraw at the foot of the
page) are MLB's. So a football Gizmo's Picks, Odds, Player Props, Parlays,
Game Lines or Track Record tab left open drew its first card and prices
until a reload, a league switch drew that league's first files again, and a
play whose game had kicked off stayed on Gizmo's Picks until a click.

✅ THE FIX (index.html, `fbRefreshTick` / `fbKickTick`): every 3 minutes each
football league the page holds files for is asked for its freshness.json
`built_at`; when it moved, that league's files are dropped (a league not on
screen) or read again and the tab drawn again when one changed (the league
on screen). Every minute a tab that hides started games is drawn again once
a game in its file has started since it was drawn.

WHAT THIS FILE ASKS, OF THE PAGE'S OWN CODE (node, no browser):
  1. THE CLASS, read from the page: every top-level football memo is cleared
     by the refresh or named in ALLOW below with its reason, and ALLOW is
     exact (a name in it is a memo on the page, and one the refresh keeps).
  2. The WHOLE page script runs in node (`vm`) with a small DOM, a fetch that
     serves planted files (nothing leaves this machine) and a virtual clock:
     the page's own `setInterval` timers fire when the clock is advanced,
     never the wall clock. In BOTH football leagues: card A on Gizmo's Picks,
     then card B with a new stamp, the clock 3 minutes on: B's rows and top
     plays, without a click, the reader's scroll kept; then card C later.
  3. Nothing moved: only the stamp is fetched and nothing is drawn. The stamp
     moved and no file changed: nothing is drawn.
  4. The reader is not moved: the Player props / Game lines choice and the
     state are kept; a box score open holds the redraw (drawn at the next
     check once it is closed, and within a minute of it closing when the new
     files had already arrived); a card that does not arrive keeps the one on
     screen.
  5. A league not on screen whose stamp moved is never drawn from its old
     files when the reader switches to it.
  6. A kickoff: the play leaves Gizmo's Picks and the top plays within a
     minute, by the page's own started rule, drawn once (not every minute).
  7. THE CLASS, driven: a key planted in every memo the scan found, for a
     league not on screen, is gone after its stamp moves, except ALLOW's.
  8. Every request the refresh made went through a no-cache fetch.
⚠️ The same thing on the real current data, in Chromium, is measured by hand
for the pull request (a note, never asserted here: it would be a fact about
the day's files).

⛔ IT ASKS THE CODE, NEVER PRODUCTION: planted files, a pinned clock.

# @vacuity 🔴 an open football tab is drawn from the new files after the stamp moves (the files are let go)
#   file: index.html
#   find:       held.forEach(([n, k]) => { delete memos[n][0][k]; });
#   with:       void held;
#
# @vacuity 🔴 THE CLASS: a memo left out of the refresh is caught (the Track Record's record.json)
#   file: index.html
#   find:     FBREC: [FBREC, () => fbRecordLoad()],
#   with:     /* FBREC left out */
#
# @vacuity 🔴 THE CLASS: a NEW football memo added without a refresh is caught
#   file: index.html
#   find: const FBNEWS = {};
#   with: const FBNEWS = {}; const FBFUTURE = {};
#
# @vacuity 🔴 the 3-minute football check runs on the page's own timer
#   file: index.html
#   find: setInterval(fbRefreshTick, FB_REFRESH_MS);
#   with: void FB_REFRESH_MS;
#
# @vacuity 🔴 a kicked-off play leaves Gizmo's Picks on the page's own 60 s timer
#   file: index.html
#   find: setInterval(fbKickTick, FB_KICK_MS);
#   with: void FB_KICK_MS;
#
# @vacuity 🔴 each league is asked for ITS OWN stamp (a league not on screen is not judged by the one on screen)
#   file: index.html
#   find:       try { built = String((await jget(`${LG_DATA[lg]}/latest/freshness.json`)).built_at || ''); }
#   with:       try { built = String((await jget(`${LG_DATA[LEAGUE]}/latest/freshness.json`)).built_at || ''); }
#
# @vacuity 🔴 the league on screen is the one read again and drawn (not the other)
#   file: index.html
#   find:       if (lg !== LEAGUE){ fbStampSeen[lg] = built; continue; }   // read when it is drawn
#   with:       if (lg === LEAGUE){ fbStampSeen[lg] = built; continue; }   // read when it is drawn
#
# @vacuity nothing is fetched when the stamp did not move
#   file: index.html
#   find:       if (built === fbStampSeen[lg]) continue;       // ⛔ nothing moved: nothing fetched, nothing drawn
#   with:       void 0;
#
# @vacuity nothing is drawn when no file changed
#   file: index.html
#   find:         if (JSON.stringify(M[k]) !== JSON.stringify(v)) fbOwed = lg;
#   with:         fbOwed = lg;
#
# @vacuity a box score open holds the redraw
#   file: index.html
#   find:   return !!document.querySelector('.ovl, #fbview tr.open, #fbview details[open]');
#   with:   return false;
#
# @vacuity a held redraw is drawn within a minute of the box closing
#   file: index.html
#   find:   if (fbOwed === LEAGUE) return fbDrawOwed();      // new files a held redraw still owes
#   with:   void 0;
#
# @vacuity a card that does not arrive keeps the one on screen
#   file: index.html
#   find:         if (got[i] === 'lost' || (M[k] == null && v != null)){ M[k] = v; lost = true; return; }
#   with:         if (got[i] === 'lost'){ M[k] = v; lost = true; return; }
#
# @vacuity the reader's scroll is kept across a timed redraw
#   file: index.html
#   find:   try { await fbKeepScroll(renderFootball); }   // new files
#   with:   try { await renderFootball(); }   // new files
#
# @vacuity a kickoff is judged by the page's own started rule
#   file: index.html
#   find:   let n = typeof x.commence === 'string' && hasStarted(x) ? 1 : 0;
#   with:   let n = 0;
#
# @vacuity a kickoff is drawn once, not every minute (each draw records what it showed)
#   file: index.html
#   find:   fbKickDrawn = fbKickSig();   // `[2026-11-18]` what this draw shows, for fbKickTick
#   with:   void 0;
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from tcheck import ck, note, section  # noqa: E402

import jsblock  # noqa: E402

PAGE = os.path.join(ROOT, "index.html")
SRC = open(PAGE, encoding="utf-8").read()

# ══════════════════════════════════════════════════════════════════════
# THE MEMOS THE REFRESH DOES NOT CLEAR, EACH WITH ITS REASON. ⛔ A new
# football memo goes in the refresh (index.html `fbMemos`) or here; section 1
# and 7 fail on one in neither, and on a name here that is not (or no longer)
# kept by the refresh.
# ══════════════════════════════════════════════════════════════════════
ALLOW = {
    "FBTEAMS": "the team directory: the NFL's is written into the page, and college "
               "teams.json changed in 0 of its 107 rebuilds 2026-10-01 to 11-18 (only "
               "built_at moves); a reload picks up a new season's schools",
    "FB_TNORM": "names normalised from FBTEAMS, which is kept",
    "FB_TCACHE": "board names resolved against FBTEAMS, which is kept",
    "FB_NEWSIDX": "the headline-crest index built from FBTEAMS, which is kept",
    "FBHAVE": "which Trends seasons have a file: a HEAD probe whose answer changes once a "
              "year, when a season's first table is written",
    "FBSCHEDHAVE": "which seasons have a schedule file: the same, once a year",
    "FBBOX": "ESPN's box score of one game, not our file; an open box of a live game "
             "re-reads its own (fbBoxFetch's `force`)",
    "FB_LIVE": "ESPN's live scoreboard, re-read every 45 s by the Scores tab's own poll (fbTick)",
    "FB_DAY": "ESPN's scores for the days of the week chosen on Scores, read when the "
              "week is chosen",
    "FB_DAY_KEY": "the week FB_DAY was read for",
    "FBPROJ": "set from the card at every Player Props draw, so it follows FBCARD",
    "fbStampSeen": "the refresh's own record of the stamp each league was checked against",
}

# ══════════════════════════════════════════════════════════════════════
# THE CLASS, READ FROM THE PAGE: every declaration in its code (comments
# removed), wherever it stands on its line, of a binding named FB* or WINNERS
# that starts as an empty table ({}, a Map) or as null (a cache), and of any
# fb* binding that starts as an empty table (a table is a memo whatever its
# case). A Set is a choice the reader made, not a memo. ⚠️ Which of them are
# TOP-LEVEL is asked of the running page (section 1: `typeof` in its global
# scope), never guessed from indentation: a column-0 scan missed a second
# declaration on one line, and its own mutation found that.
# ══════════════════════════════════════════════════════════════════════
CODE = jsblock.script_code(PAGE)
_DECL = re.compile(r"(?<![\w$.])(?:const|let|var)\s+([^;\n]*)")
_ONE = re.compile(r"([A-Za-z_$][\w$]*)\s*=\s*(\{\s*\}|new (?:Weak)?Map\(\s*\)|Object\.create\(null\)|null)\s*(?=,|$)")
CAND = {}
for m in _DECL.finditer(CODE):
    for name, init in _ONE.findall(m.group(1).strip()):
        football = name.startswith("FB") or name == "WINNERS"
        if init == "null" and football:
            CAND[name] = "null"
        elif init != "null" and (football or name.startswith("fb")):
            CAND[name] = "table"

# ══════════════════════════════════════════════════════════════════════
# THE PLANTED FILES. ⛔ The clock is pinned (T0); nothing is read from data/.
# ══════════════════════════════════════════════════════════════════════
T0 = "2026-11-19T15:00:00Z"
SOON = "2026-11-19T15:20:00Z"          # 20 minutes after T0
LATER = "2026-11-21T18:00:00Z"
TAG = {"nfl": "NFL", "ncaaf": "CFB"}


def prop(name, commence, conf):
    return dict(kind="fb-prop", player=name, market="receptions", market_label="Receptions",
                side="over", line=4.5, game="Away Team @ Home Team", away="Away Team",
                home="Home Team", game_id="g-" + name, commence=commence, price=-120,
                book="draftkings", confidence_basis="MODEL", confidence=conf,
                break_even=54.5, edge=round(conf - 54.5, 1))


def top(name, commence, conf):
    return dict(player=name, side="over", line=4.5, market_label="Receptions", confidence=conf,
                price=-120, away="Away Team", home="Home Team", game="Away Team @ Home Team",
                commence=commence)


def gline(team, commence):
    return dict(kind="fb-line", player=team, market="spreads", market_label="Spread", side="over",
                line=-3.5, game="Away Team @ Home Team", away="Away Team", home="Home Team",
                game_id="gl-" + team, commence=commence, price=-110, book="fanduel",
                confidence_basis="MODEL", confidence=57, break_even=52.4, edge=4.6)


def card(lg, tag, soon=None):
    """Two plays, two top plays and one game line, every name carrying `tag`."""
    one, two = "%s %s One" % (TAG[lg], tag), "%s %s Two" % (TAG[lg], tag)
    picks = [prop(one, soon or LATER, 64), prop(two, LATER, 58)]
    gl = [gline("%s %s Line" % (TAG[lg], tag), LATER)]
    return {"date": "2026-11-21", "league": lg, "generated_at": "2026-11-19T14:00:00Z",
            "odds_pulled_at": "2026-11-19T13:50:00Z", "picks": picks, "liked": picks,
            "game_lines": gl, "game_lines_liked": gl, "game_lines_meta": {"slate": "2026-11-21"},
            "top_plays": [top(one, soon or LATER, 64), top(two, LATER, 58)]}


def files(*lgs, tag="Alpha", stamp="2026-11-19T14:00:00Z"):
    out = {}
    for lg in lgs:
        out["picks/fb-%s-latest.json" % lg] = card(lg, tag)
        out["data/%s/latest/freshness.json" % lg] = {"built_at": stamp}
        out["data/%s/latest/board.json" % lg] = {"pulled_at": "2026-11-19T13:50:00Z", "games": []}
    return out


# ══════════════════════════════════════════════════════════════════════
# THE DRIVER: the page's whole script in a vm context. ⚠️ The DOM is only
# what the football tabs touch; an element's innerHTML is a string, its
# children are kept in order, and #fbview counts its writes. Replacing
# #fbview scrolls the page to the top (the worst case), so a kept scroll is
# one the page put back.
# ══════════════════════════════════════════════════════════════════════
DRIVER = r"""
'use strict';
const vm = require('vm'), fs = require('fs');
const S = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const UNHANDLED = [];
process.on('unhandledRejection', e => UNHANDLED.push(String((e && e.stack) || e)));
const turn = () => new Promise(r => setImmediate(r));
const outer = n => n.raw !== undefined ? n.raw
  : '<' + n.tagName.toLowerCase() + ' class="' + n.className + '">' + n.innerHTML + '</' + n.tagName.toLowerCase() + '>';

function boot(planted){
  let NOW = Date.parse(S.t0);
  const FILES = Object.assign({}, planted);
  const timers = []; let tid = 0;
  const CALLS = [], PRESENT = new Set(), HOOKS = {};
  const view = {writes: 0, draws: 0};
  const sb = {};
  function el(tag, id){
    return {
      tagName: String(tag || 'div').toUpperCase(), id: id || '', className: '', kids: [], _h: '',
      style: {}, dataset: {}, attrs: {}, on: {}, hidden: false, value: '', title: '', href: '',
      classList: {add(){}, remove(){}, toggle(){}, contains(){ return false; }},
      get innerHTML(){ return this._h + this.kids.map(outer).join(''); },
      set innerHTML(h){
        this._h = String(h); this.kids = [];
        if (this.id === 'fbview'){
          view.writes++;
          if (/class="msg"[^>]*>Loading/.test(this._h)) view.draws++;
          sb.scrollY = 0;
        }
      },
      get textContent(){ return this.innerHTML.replace(/<[^>]*>/g, ''); },
      set textContent(t){ this._h = String(t); this.kids = []; },
      get outerHTML(){ return outer(this); },
      get children(){ return this.kids; },
      append(...n){ n.forEach(x => this.kids.push(typeof x === 'string' ? {raw: x} : x)); },
      appendChild(n){ this.kids.push(n); return n; },
      prepend(...n){ this.kids.unshift(...n.map(x => typeof x === 'string' ? {raw: x} : x)); },
      insertAdjacentHTML(pos, h){
        if (pos === 'afterbegin') this.kids.unshift({raw: String(h)}); else this.kids.push({raw: String(h)});
      },
      addEventListener(t, f){ (this.on[t] = this.on[t] || []).push(f); },
      removeEventListener(){}, setAttribute(k, v){ this.attrs[k] = String(v); },
      getAttribute(k){ return k in this.attrs ? this.attrs[k] : null; },
      removeAttribute(k){ delete this.attrs[k]; },
      querySelector(){ return null; }, querySelectorAll(){ return []; }, closest(){ return null; },
      focus(){}, blur(){}, scrollIntoView(){}, remove(){}, click(){},
      scrollWidth: 6000, offsetHeight: 0, offsetWidth: 0,
    };
  }
  const ids = {}, statics = {};
  const STATIC = new Set(['.subnav', '.subnav ul', '.tools']);
  const LGNAV = ['mlb', 'nfl', 'ncaaf'].map(lg => { const a = el('a'); a.dataset.lg = lg; return a; });
  const document = {
    createElement: t => el(t),
    querySelector(sel){
      for (const s of String(sel).split(',').map(x => x.trim())){
        if (PRESENT.has(s)) return el('div');
        const m = /^#([\w-]+)$/.exec(s);
        if (m) return ids[m[1]] || (ids[m[1]] = el('div', m[1]));
        if (STATIC.has(s)) return statics[s] || (statics[s] = el('div'));
      }
      return null;
    },
    querySelectorAll(sel){ return sel === '.lgnav a[data-lg]' ? LGNAV : []; },
    documentElement: {scrollHeight: 20000, clientHeight: 900, style: {}},
    body: el('body'), head: el('head'), activeElement: null, hidden: false, visibilityState: 'visible',
    addEventListener(){}, removeEventListener(){},
  };
  const store = new Map();
  let ctxParse = null;
  async function fetch(u, init){
    u = String(u);
    CALLS.push({u, cache: init && init.cache ? init.cache : null, at: NOW});
    if (HOOKS[u]) HOOKS[u]();
    if (/^[a-z][a-z0-9+.-]*:/i.test(u)) throw new TypeError('Failed to fetch');  // nothing leaves this machine
    const f = FILES[u.split('?')[0]];
    if (f == null) return {ok: false, status: 404, json: async () => ({}),
                           arrayBuffer: async () => new ArrayBuffer(0)};
    const text = JSON.stringify(f);
    return {ok: true, status: 200, json: async () => ctxParse(text), text: async () => text};
  }
  const add = (fn, ms, repeat, args) => {
    const d = Math.max(0, +ms || 0);
    timers.push({id: ++tid, fn, ms: d, at: NOW + d, repeat, args}); return tid;
  };
  const clear = id => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); };
  Object.assign(sb, {
    document, fetch, console: {log(){}, info(){}, warn(){}, error(){}, debug(){}},
    scrollY: 0, innerHeight: 900, innerWidth: 1280,
    scrollTo(x, y){ sb.scrollY = typeof x === 'object' ? (x.top || 0) : y; },
    matchMedia: () => ({matches: false, addEventListener(){}, addListener(){}}),
    addEventListener(){}, removeEventListener(){},
    location: {hash: '', href: 'http://127.0.0.1/index.html', pathname: '/index.html', search: ''},
    history: {replaceState(){}, pushState(){}},
    localStorage: {getItem: k => store.has(k) ? store.get(k) : null,
                   setItem: (k, v) => { store.set(k, String(v)); }, removeItem: k => { store.delete(k); }},
    requestAnimationFrame: cb => { setImmediate(() => cb(NOW)); return 1; },
    setInterval: (fn, ms, ...a) => add(fn, ms, true, a),
    setTimeout: (fn, ms, ...a) => add(fn, ms, false, a),
    clearInterval: clear, clearTimeout: clear,
    TextDecoder, TextEncoder, __now: () => NOW,
  });
  sb.window = sb;
  const ctx = vm.createContext(sb);
  vm.runInContext(`(() => { const D = Date;
    class PinnedDate extends D { constructor(...a){ if (a.length) super(...a); else super(__now()); }
                                 static now(){ return __now(); } }
    globalThis.Date = PinnedDate; })();`, ctx);
  ctxParse = vm.runInContext('JSON.parse', ctx);
  vm.runInContext(S.script, ctx, {filename: 'index.html'});
  async function settle(){ for (let i = 0; i < 40; i++) await turn(); }
  async function advance(ms){
    const end = NOW + ms;
    for (;;){
      const due = timers.filter(t => t.at <= end).sort((a, b) => a.at - b.at || a.id - b.id)[0];
      if (!due) break;
      NOW = Math.max(NOW, due.at);
      if (due.repeat) due.at += Math.max(1, due.ms); else clear(due.id);
      try { due.fn(...(due.args || [])); } catch (e) { UNHANDLED.push('timer: ' + ((e && e.stack) || e)); }
      await settle();
    }
    NOW = end;
    await settle();
  }
  const html = () => ids.fbview ? ids.fbview.innerHTML : '';
  const TICK = () => vm.runInContext('TICK_SRC.map(x => x[1])', ctx);
  return {
    run: code => vm.runInContext(code, ctx), advance, settle, html, view, CALLS, PRESENT, HOOKS, sb,
    put: (p, v) => { FILES[p] = v; },
    league: async lg => { LGNAV.find(a => a.dataset.lg === lg).on.click[0](); await settle(); },
    tab: async t => { statics['.subnav'].on.click[0]({target: {closest: () => ({dataset: {tab: t}})}}); await settle(); },
    rows: () => [...html().matchAll(/<span class="pn">([^<]*)<\/span>/g)].map(m => m[1]),
    tops: () => [...html().matchAll(/<div class="w"><b>([^<]*)<\/b><\/div>/g)].map(m => m[1]),
    // ⚠️ the headline ticker's own 10-minute read of every league's news.json (TICK_SRC) is not the refresh's
    fb: since => CALLS.slice(since).filter(c => /^(picks\/fb-|data\/(nfl|ncaaf)\/)/.test(c.u)
                                          && !TICK().includes(c.u)),
  };
}

const card = (lg, tag, soon) => JSON.parse(JSON.stringify(S.cards[lg + '|' + tag + '|' + (soon ? 'soon' : 'later')]));
const fresh = s => ({built_at: s});

async function openPicks(lg, planted){
  const P = boot(planted);
  await P.settle();
  await P.league(lg);
  await P.tab('picks');
  return P;
}

async function refresh(lg){
  const P = await openPicks(lg, S.files[lg]);
  const out = {a: P.rows(), aTop: P.tops()};
  P.run("setBetState('NJ')");
  P.sb.scrollY = 640;
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Bravo'));
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:01:00Z'));
  await P.advance(181000);
  Object.assign(out, {b: P.rows(), bTop: P.tops(), scrollY: P.sb.scrollY,
                      tab: P.run('FBTAB'), league: P.run('LEAGUE'), state: P.run('betState()')});
  // nothing moved: one stamp request a tick, nothing drawn
  let c0 = P.CALLS.length, w0 = P.view.writes;
  await P.advance(2 * 180000 + 1000);
  out.idle = {fetched: P.fb(c0).map(c => c.u), writes: P.view.writes - w0};
  // the stamp moved and no file changed: the files are read again, nothing is drawn
  c0 = P.CALLS.length; w0 = P.view.writes;
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:20:00Z'));
  await P.advance(181000);
  out.same = {fetched: P.fb(c0).map(c => c.u), writes: P.view.writes - w0};
  // and again later: card C
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Charlie'));
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:40:00Z'));
  await P.advance(181000);
  out.c = P.rows();
  out.caches = P.CALLS.filter(c => /^(picks\/fb-|data\/(nfl|ncaaf)\/)/.test(c.u)).map(c => c.cache);
  return out;
}

async function linesView(lg){
  const P = await openPicks(lg, S.files[lg]);
  P.run("FBPICKKIND = 'lines'; fbPicks()");
  await P.settle();
  const a = P.html();
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Bravo'));
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:01:00Z'));
  await P.advance(181000);
  return {a: a.includes(S.tag[lg] + ' Alpha Line'), b: P.html().includes(S.tag[lg] + ' Bravo Line'),
          aGone: !P.html().includes(S.tag[lg] + ' Alpha Line'), kind: P.run('FBPICKKIND')};
}

async function held(lg){
  const P = await openPicks(lg, S.files[lg]);
  const out = {};
  // a box score open the whole time: nothing drawn
  P.PRESENT.add('.ovl');
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Bravo'));
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:01:00Z'));
  let w0 = P.view.writes;
  await P.advance(181000);
  out.open = {rows: P.rows(), writes: P.view.writes - w0};
  P.PRESENT.delete('.ovl');
  await P.advance(181000);
  out.closed = P.rows();
  // a box opened while the new files were in flight: drawn within a minute of it closing
  P.HOOKS[`picks/fb-${lg}-latest.json`] = () => P.PRESENT.add('.ovl');
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Charlie'));
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T15:40:00Z'));
  await P.advance(180000);
  out.mid = P.rows();
  delete P.HOOKS[`picks/fb-${lg}-latest.json`];
  P.PRESENT.delete('.ovl');
  await P.advance(61000);
  out.after = P.rows();
  // a card that does not arrive keeps the one on screen, and is read once it is back
  P.put(`picks/fb-${lg}-latest.json`, null);
  P.put(`data/${lg}/latest/freshness.json`, fresh('2026-11-19T16:20:00Z'));
  await P.advance(180000);
  out.missing = P.rows();
  P.put(`picks/fb-${lg}-latest.json`, card(lg, 'Delta'));
  await P.advance(180000);
  out.back = P.rows();
  return out;
}

async function offScreen(){
  // ⚠️ Both leagues start on the SAME stamp, and each is checked once before the NFL one moves:
  //    a first check lets go of a league not on screen whatever its stamp says, so a scenario
  //    without these two steps would pass for the wrong reason (and did, under the mutation
  //    that judges the NFL by college's stamp).
  const P = await openPicks('nfl', Object.assign({}, S.files.nfl, S.files.ncaaf));
  const out = {nflA: P.rows()};
  await P.advance(181000);                  // the NFL's stamp checked, the NFL on screen
  await P.league('ncaaf');
  out.cfbA = P.rows(); out.tab = P.run('FBTAB');
  await P.advance(180000);                  // college's checked, the NFL's again (unchanged)
  P.put('picks/fb-nfl-latest.json', card('nfl', 'Bravo'));
  P.put('data/nfl/latest/freshness.json', fresh('2026-11-19T15:02:00Z'));
  const w0 = P.view.writes;
  await P.advance(180000);
  out.cfbWrites = P.view.writes - w0;
  out.cfbStill = P.rows();
  await P.league('nfl');
  out.nflAfter = P.rows();
  return out;
}

async function kickoff(lg){
  const planted = Object.assign({}, S.files[lg], {[`picks/fb-${lg}-latest.json`]: card(lg, 'Alpha', true)});
  const P = await openPicks(lg, planted);
  const out = {before: P.rows(), beforeTop: P.tops()};
  const d0 = P.view.draws;
  await P.advance(19 * 60000);              // the game has not started yet
  out.early = {rows: P.rows(), draws: P.view.draws - d0};
  await P.advance(2 * 60000 + 1000);        // it kicks off at +20 minutes
  out.after = P.rows(); out.afterTop = P.tops();
  const d1 = P.view.draws;
  await P.advance(10 * 60000);
  out.later = {rows: P.rows(), draws: P.view.draws - d1};
  out.kickDraws = d1 - d0;
  return out;
}

async function classSweep(){
  const P = await openPicks('nfl', Object.assign({}, S.files.nfl, S.files.ncaaf));
  // which candidates are bindings of the page's global scope (top-level), asked of the page
  const top = {};
  for (const n of Object.keys(S.cand)) top[n] = P.run(`typeof ${n}`);
  const tables = Object.keys(S.cand).filter(n => S.cand[n] === 'table' && top[n] === 'object');
  await P.advance(181000);
  const SENT = '{sentinel: "planted"}';
  for (const n of tables) P.run(`${n}['ncaaf'] = ${SENT}; ${n}['ncaaf|probe'] = ${SENT};`);
  P.put('data/ncaaf/latest/freshness.json', fresh('2026-11-19T15:05:00Z'));
  await P.advance(180000);
  const keys = {};
  for (const n of tables)
    keys[n] = P.run(`[Object.prototype.hasOwnProperty.call(${n}, 'ncaaf'), Object.prototype.hasOwnProperty.call(${n}, 'ncaaf|probe')]`);
  return {top, keys, on: P.run('LEAGUE')};
}

(async () => {
  const R = {};
  for (const lg of ['nfl', 'ncaaf']){
    R['refresh_' + lg] = await refresh(lg);
    R['lines_' + lg] = await linesView(lg);
    R['held_' + lg] = await held(lg);
    R['kick_' + lg] = await kickoff(lg);
  }
  R.offScreen = await offScreen();
  R.classSweep = await classSweep();
  R.unhandled = UNHANDLED;
  process.stdout.write(JSON.stringify(R));
})().catch(e => { console.error(String((e && e.stack) || e)); process.exit(1); });
"""

_s = SRC.index("<script>") + len("<script>")
SCRIPT = SRC[_s:SRC.index("</script>", _s)]       # the page's one script, as a browser runs it
CARDS = {"%s|%s|%s" % (lg, tag, w): card(lg, tag, SOON if w == "soon" else None)
         for lg in TAG for tag in ("Alpha", "Bravo", "Charlie", "Delta") for w in ("soon", "later")}
PAYLOAD = {"t0": T0, "script": SCRIPT, "cards": CARDS, "tag": TAG,
           "files": {lg: files(lg) for lg in TAG}, "cand": CAND}

tmp = tempfile.mkdtemp(prefix="fbrefresh-")
try:
    open(os.path.join(tmp, "d.js"), "w", encoding="utf-8").write(DRIVER)
    json.dump(PAYLOAD, open(os.path.join(tmp, "d.json"), "w", encoding="utf-8"))
    r = subprocess.run(["node", os.path.join(tmp, "d.js"), os.path.join(tmp, "d.json")],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ck(r.returncode == 0, "the page's whole script ran in node, with the planted files and a pinned clock",
   (r.stderr or "")[-600:])
R = json.loads(r.stdout) if r.returncode == 0 else {}


def got(*path):
    x = R
    for p in path:
        x = (x or {}).get(p) if isinstance(x, dict) else None
    return x


def names(lg, tag):
    return ["%s %s One" % (TAG[lg], tag), "%s %s Two" % (TAG[lg], tag)]


# ══════════════════════════════════════════════════════════════════════
section("1. 🔴 THE CLASS: EVERY TOP-LEVEL FOOTBALL MEMO IS REFRESHED OR ALLOW-LISTED")
# ══════════════════════════════════════════════════════════════════════
_top = got("classSweep", "top") or {}
TABLES = {n for n, k in CAND.items() if k == "table" and _top.get(n) == "object"}
NULLS = {n for n, k in CAND.items() if k == "null" and _top.get(n) not in (None, "undefined")}
ck(len(TABLES) >= 12 and {"FBCARD", "FBBOARD", "FBPROPS", "WINNERS", "FBREC"} <= TABLES,
   "the page's top-level football memo tables are found (%d: %s)" % (len(TABLES), ", ".join(sorted(TABLES))),
   "⛔ a scan that finds nothing passes every check below (rule 67)")
note("   null-initialised football caches: %s; declared, not top-level: %s"
     % (", ".join(sorted(NULLS)), sorted(n for n in CAND if n not in TABLES | NULLS) or "none"))
_stale = sorted(k for k in ALLOW if k not in TABLES | NULLS)
ck(not _stale, "ALLOW names only memos that are on the page",
   "⛔ a stale allow-list entry hides nothing today and excuses something tomorrow: %s" % _stale)
ck(all(isinstance(v, str) and len(v) > 20 for v in ALLOW.values()),
   "   ...and gives each one its reason")
_null_bare = sorted(NULLS - set(ALLOW))
ck(not _null_bare,
   "🔴 every null-initialised football cache is allow-listed with its reason "
   "(the refresh lets go of a league's keys in a TABLE; a bare cache it cannot see)",
   "⛔ put the file in a table keyed by league and in fbMemos(), or say here why it never "
   "needs refreshing: %s" % _null_bare)


# ══════════════════════════════════════════════════════════════════════
section("2. 🔴 AN OPEN GIZMO'S PICKS TAB DRAWS THE NEW CARD, IN BOTH FOOTBALL LEAGUES")
# ══════════════════════════════════════════════════════════════════════
for lg in TAG:
    X = got("refresh_" + lg) or {}
    ck(X.get("a") == names(lg, "Alpha") and X.get("aTop") == names(lg, "Alpha"),
       "%s: card A's two plays and two top plays are on screen first" % TAG[lg],
       "rows %s, top plays %s" % (X.get("a"), X.get("aTop")))
    ck(X.get("b") == names(lg, "Bravo") and X.get("bTop") == names(lg, "Bravo"),
       "🔴 %s: card B with a new stamp, the page's own clock 3 minutes on: B's plays and top "
       "plays, no click (~~card A until a reload~~)" % TAG[lg],
       "rows %s, top plays %s" % (X.get("b"), X.get("bTop")))
    ck(X.get("c") == names(lg, "Charlie"),
       "🔴 %s: ...and card C at a later stamp: it keeps following, not once" % TAG[lg], str(X.get("c")))
    ck(X.get("scrollY") == 640 and X.get("tab") == "picks" and X.get("league") == lg
       and X.get("state") == "NJ",
       "%s: the reader stays where they were: scroll 640 put back, the tab, the league and the "
       "state they chose" % TAG[lg],
       "scroll %s, tab %s, league %s, state %s"
       % (X.get("scrollY"), X.get("tab"), X.get("league"), X.get("state")))

# ══════════════════════════════════════════════════════════════════════
section("3. NOTHING MOVED: NOTHING FETCHED BUT THE STAMP, NOTHING DRAWN")
# ══════════════════════════════════════════════════════════════════════
for lg in TAG:
    X = got("refresh_" + lg) or {}
    idle, same = X.get("idle") or {}, X.get("same") or {}
    _stamp = "data/%s/latest/freshness.json" % lg
    ck(idle.get("fetched") == [_stamp, _stamp] and idle.get("writes") == 0,
       "%s: two quiet ticks ask for the stamp twice and draw nothing" % TAG[lg],
       "fetched %s, #fbview written %s time(s)" % (idle.get("fetched"), idle.get("writes")))
    ck("picks/fb-%s-latest.json" % lg in (same.get("fetched") or []) and same.get("writes") == 0,
       "🔴 %s: the stamp moved and no file changed: the files are asked again and nothing is "
       "drawn" % TAG[lg],
       "fetched %s, #fbview written %s time(s)" % (same.get("fetched"), same.get("writes")))

# ══════════════════════════════════════════════════════════════════════
section("4. THE READER IS NOT MOVED")
# ══════════════════════════════════════════════════════════════════════
for lg in TAG:
    L = got("lines_" + lg) or {}
    ck(L.get("a") and L.get("b") and L.get("aGone") and L.get("kind") == "lines",
       "%s: on the Game lines view, the new card's game line is drawn and the view stays Game "
       "lines" % TAG[lg], str(L))
    H = got("held_" + lg) or {}
    ck((H.get("open") or {}).get("rows") == names(lg, "Alpha") and (H.get("open") or {}).get("writes") == 0,
       "🔴 %s: a box score open: nothing is drawn under it" % TAG[lg], str(H.get("open")))
    ck(H.get("closed") == names(lg, "Bravo"),
       "   %s: ...and the new card is drawn once it is closed" % TAG[lg], str(H.get("closed")))
    ck(H.get("mid") == names(lg, "Bravo") and H.get("after") == names(lg, "Charlie"),
       "🔴 %s: a box opened while the new files were arriving holds the draw, which comes within "
       "a minute of it closing (not the next stamp)" % TAG[lg],
       "while open %s, a minute after closing %s" % (H.get("mid"), H.get("after")))
    ck(H.get("missing") == names(lg, "Charlie") and H.get("back") == names(lg, "Delta"),
       "🔴 %s: a card that does not arrive keeps the one on screen (~~\"No picks\"~~), and is "
       "drawn once it is back" % TAG[lg],
       "missing %s, back %s" % (H.get("missing"), H.get("back")))

# ══════════════════════════════════════════════════════════════════════
section("5. 🔴 A LEAGUE NOT ON SCREEN IS NEVER DRAWN FROM ITS OLD FILES AFTER ITS STAMP MOVED")
# ══════════════════════════════════════════════════════════════════════
O = got("offScreen") or {}
ck(O.get("nflA") == names("nfl", "Alpha") and O.get("cfbA") == names("ncaaf", "Alpha")
   and O.get("tab") == "picks",
   "NFL card A, then a switch to college keeps Gizmo's Picks", str(O))
ck(O.get("cfbWrites") == 0 and O.get("cfbStill") == names("ncaaf", "Alpha"),
   "the NFL stamp moving does not redraw the college tab on screen",
   "#fbview written %s time(s), rows %s" % (O.get("cfbWrites"), O.get("cfbStill")))
ck(O.get("nflAfter") == names("nfl", "Bravo"),
   "🔴 ...and switching back to the NFL draws card B (~~the NFL card A it held~~)", str(O.get("nflAfter")))

# ══════════════════════════════════════════════════════════════════════
section("6. 🔴 A KICKOFF LEAVES GIZMO'S PICKS WITHOUT A CLICK, DRAWN ONCE")
# ══════════════════════════════════════════════════════════════════════
for lg in TAG:
    K = got("kick_" + lg) or {}
    one, two = names(lg, "Alpha")
    ck(K.get("before") == [one, two] and K.get("beforeTop") == [one, two]
       and (K.get("early") or {}).get("rows") == [one, two] and (K.get("early") or {}).get("draws") == 0,
       "%s: both plays shown, and nothing drawn in the 19 minutes before the kickoff" % TAG[lg], str(K))
    ck(K.get("after") == [two] and K.get("afterTop") == [two],
       "🔴 %s: a minute after %s kicks off it has left the plays and the top plays (the page's "
       "own started rule), no click" % (TAG[lg], one),
       "rows %s, top plays %s" % (K.get("after"), K.get("afterTop")))
    ck(K.get("kickDraws") == 1 and (K.get("later") or {}).get("draws") == 0
       and (K.get("later") or {}).get("rows") == [two],
       "   %s: ...drawn once for it, and not again in the next 10 minutes" % TAG[lg],
       "draws for the kickoff %s, in the 10 minutes after %s"
       % (K.get("kickDraws"), (K.get("later") or {}).get("draws")))

# ══════════════════════════════════════════════════════════════════════
section("7. 🔴 THE CLASS, DRIVEN: A LEAGUE'S KEYS IN EVERY MEMO GO WHEN ITS STAMP MOVES")
# ══════════════════════════════════════════════════════════════════════
C = (got("classSweep") or {}).get("keys") or {}
ck(got("classSweep", "on") == "nfl" and TABLES and all(isinstance(C.get(n), list) for n in TABLES),
   "a key for college (not on screen) was planted in each of the %d memo tables" % len(TABLES), str(C)[:300])
_kept = sorted(n for n in TABLES - set(ALLOW) if any(C.get(n) or [True]))
ck(not _kept,
   "🔴 every memo table not in ALLOW let go of college's keys when its stamp moved",
   "⛔ a football memo the refresh does not clear keeps a league's first file until a "
   "reload: put it in fbMemos() (index.html) or in ALLOW with its reason: %s" % _kept)
_dropped = sorted(n for n in TABLES & set(ALLOW) if not all(C.get(n) or [False]))
ck(not _dropped,
   "...and every one in ALLOW is one the refresh really keeps (ALLOW is exact)",
   "⛔ these are cleared now: take them out of ALLOW: %s" % _dropped)

# ══════════════════════════════════════════════════════════════════════
section("8. EVERY REQUEST THE REFRESH MADE ASKED THE SERVER (no-cache)")
# ══════════════════════════════════════════════════════════════════════
for lg in TAG:
    _c = (got("refresh_" + lg) or {}).get("caches") or []
    ck(_c and all(c in ("no-cache", "no-store", "reload") for c in _c),
       "%s: %d football request(s), each with a cache mode that goes to the server "
       "(test_fetch_fresh.py holds every fetch on the page to it)" % (TAG[lg], len(_c)),
       "modes %s" % sorted(set(map(str, _c))))
_un = R.get("unhandled") or []
_ours = [u for u in _un if re.search(r"fbRefreshTick|fbKickTick|fbDrawOwed|fbDataAgain|fbMemos", u)]
ck(not _ours, "no error was thrown by the refresh", "\n".join(_ours)[:600])
if _un:
    note("   %d other unhandled error(s) in the run (the MLB half, which has no files here): %s"
         % (len(_un), _un[0][:160]))
note("⛔ WHAT THIS FILE DOES NOT CLAIM: how a phone paints the redraw, or how GitHub Pages "
     "answers a revalidation. It claims the page's own timers draw the new files, in both "
     "football leagues, without moving the reader.")
