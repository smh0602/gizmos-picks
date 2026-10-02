/* THE PAGE'S STALENESS BANNER — behaviour test.
 * 🔴 [Sam, 2026-10-01] THE PAGE HAS NONE NOW, AND THIS FILE REQUIRES THAT.
 *
 * 🔴 SELF-EXTRACTING. It reads index.html and pulls the page's own code out
 * of it, so it tests THE SHIPPED PAGE and cannot drift from a copy.
 * ⛔ An earlier version read a file that only existed in a scratch
 * directory, which meant it would have silently passed on the runner
 * while testing nothing.
 *
 * WHAT IT USED TO REQUIRE: renderStaleBanner() put a red bar over the page
 * for a late tab (named by tab), a tab never built, a card REFUSED by its
 * own checks, a card published with an ACCEPTED caveat (in a different
 * sentence from the refused one), and a freshness report that failed to
 * load or was malformed. The bar came from 2026-08-28, when the site
 * served 15-hour-old props while looking completely normal.
 *
 * WHY THAT CHANGED: Sam, 2026-10-01: "i just want what's supposed to be in
 * each tab to be in each tab. do this for all 3 leagues"; asked what
 * stays, he chose: remove everything. Staleness now reaches Sam through
 * the watchdog, health.json and the GitHub issue, not through the page.
 *
 * WHAT IT REQUIRES NOW, of the same page:
 *   1. no renderStaleBanner and no stalebar anywhere in its code;
 *   2. for EVERY state the bar used to announce, the page's own loader
 *      (loadBoard) still fetches the report (the 3-minute refresh loop
 *      reads its built_at) and touches nothing on the page;
 *   3. neither card field and neither card sentence is in the page.
 * ⛔ The DATA side is unchanged: collect.py still publishes card_blocked,
 * card_caveat and every row. card_caveat's publication is checked by
 * test_card_gate.py and the rows by test_freshness.py; card_blocked has
 * no data-side check of its own (none existed before this change either).
 *
 * ⚠️ vacuity.py reads `@vacuity` declarations from test_*.py only, so this
 * file's mutations are listed here; each was applied to a scratch copy of
 * index.html and turned this file red:
 *   - `function renderStaleBanner(){...}` back beside `let FRESH = null;` -> 1
 *   - `<div id="stalebar" class="stalebar"></div>` back in the body       -> 1
 *   - the old banner back AND called at the end of loadBoard              -> 1, 2
 *   - the freshness fetch dropped from loadBoard                          -> 2
 *   - "Today's card is published with a known caveat." back on the page  -> 3
 * test_runs_status.py and test_card_gate.py ask the same absences with
 * declarations that vacuity.py does run.
 */
const fs = require('fs');

const html = fs.readFileSync('index.html', 'utf8');
/* Comments out first: this repo strikes deleted code in a comment rather
   than removing it, so an unstripped search would find the bar inside the
   note that records its removal. */
const code = html.replace(/<!--[\s\S]*?-->|\/\*[\s\S]*?\*\//g, '')
  .split('\n').filter(l => !l.trim().startsWith('//')).join('\n');
const a = code.indexOf('let FRESH = null;');
const b = code.indexOf('function freshness(iso){');
const load = (code.match(/\nasync function loadBoard\(\)\s*\{[\s\S]*?\n\}/) || [])[0];
if (a < 0 || b < 0 || b <= a || !load) {
  console.error('COULD NOT FIND THE FRESHNESS CODE IN index.html.');
  console.error('Either the page changed shape or its freshness fetch was removed —');
  console.error('both are things this test exists to notice (the 3-minute refresh');
  console.error('loop reads FRESH.built_at).');
  process.exit(1);
}

const ok = [];
function absent(label, re) {
  const m = code.match(re);
  console.log(`  [${m ? 'WRONG' : 'OK  '}] ${label}`);
  if (m) console.log(`            found: "${m[0]}"`);
  ok.push(!m);
}

/* The page's own loader, run with the page's own declarations from where
   the banner used to live, against a document that records every touch.
   ⛔ The old file handed the banner a fake bar and read what it wrote;
   with no bar, the question is whether ANYTHING on the page is touched. */
function runLoad(doc) {
  const touched = [];
  const sink = new Proxy({}, {
    get: (_, k) => { touched.push('.' + String(k)); return undefined; },
    set: (_, k, v) => { touched.push('.' + String(k) + ' = ' + String(v).slice(0, 160)); return true; },
  });
  const document = new Proxy({}, {
    get: (_, k) => { touched.push(String(k)); return () => sink; },
    set: (_, k, v) => { touched.push(String(k) + ' = ' + String(v).slice(0, 160)); return true; },
  });
  const jget = async url => {
    if (url !== 'data/latest/freshness.json') return { games: [] };
    if (doc instanceof Error) throw doc;
    return doc;
  };
  const page = new Function('document', 'jget',
    'let BOARD = null;\n' + code.slice(a, b) + '\n' + load
    + '\nreturn { loadBoard, fresh: () => FRESH };')(document, jget);
  return page.loadBoard().then(() => ({ touched, fresh: page.fresh() }));
}

const CASES = [
  ['everything built on schedule',
    { built_at: 'B1', artifacts: [{ mode: 'card', stale: false }, { mode: 'gamelines', stale: false }] }],
  ['several tabs late (the bar named them by tab)', { built_at: 'B2', artifacts: [
    { mode: 'props-pitcher', stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'props-batter',  stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'gamelines',     stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'record',        stale: true, late_min: 468, due_et: '6:00',       missing: false },
    { mode: 'card',          stale: false }] }],
  ['a tab never built at all', { built_at: 'B3',
    artifacts: [{ mode: 'results', stale: true, late_min: null, due_et: '6:00', missing: true }] }],
  ['🔴 the card was REFUSED by its own checks', { built_at: 'B4',
    artifacts: [{ mode: 'card', stale: true, late_min: 300, due_et: '10:00', missing: false }],
    card_blocked: 'T37: hitter projections contradict <= 5.0%' }],
  ['🔴 the card is PUBLISHED WITH AN ACCEPTED CAVEAT', { built_at: 'B5',
    artifacts: [{ mode: 'card', stale: false }],
    card_caveat: 'T37: a mean-vs-frequency artifact, both numbers correct' }],
  ['the freshness report is malformed', { artifacts: 'oops' }],
  ['the freshness report failed to load', new Error('HTTP 404 for data/latest/freshness.json')],
];

(async () => {
  console.log('1. NO BANNER ON THE PAGE\n');
  absent('renderStaleBanner() is gone — not defined, not called', /\brenderStaleBanner\b/);
  absent('the #stalebar element and its styles are gone', /stalebar/);

  console.log('\n2. THE PAGE SHOWS NOTHING FOR ANY STATE THE BAR USED TO ANNOUNCE\n');
  for (const [label, doc] of CASES) {
    let r = null, err = null;
    try { r = await runLoad(doc); } catch (e) { err = e; }
    const quiet = !err && r.touched.length === 0;
    /* ⛔ AND THE FETCH STAYS: the refresh loop reads FRESH.built_at, so the
       report must still land in FRESH -- or be null when it failed to load. */
    const held = !err && (doc instanceof Error ? r.fresh === null : r.fresh === doc);
    console.log(`  [${quiet && held ? 'OK  ' : 'WRONG'}] ${err ? 'THREW ' : quiet ? 'hidden' : 'SHOWN '}  ${label}`);
    if (err) console.log(`            loadBoard threw: ${err && err.message}`);
    else if (!quiet) console.log(`            touched: ${r.touched.slice(0, 6).join(' | ')}`);
    if (!err && !held) console.log('            FRESH is not the report loadBoard fetched');
    ok.push(quiet && held);
  }

  /* ~~THE THREE CARD STATES MUST READ AS THREE DIFFERENT THINGS~~ -- until
     2026-10-01 a refused card ("showing an earlier version") and a caveated
     one ("published with a known caveat") had to be two sentences. Neither
     is on the page now; the fields stay in freshness.json. */
  console.log('\n3. NEITHER CARD STATE IS ON THE PAGE\n');
  absent('neither card field is read (card_caveat, card_blocked)', /card_caveat|card_blocked/);
  absent("neither card sentence is there ('showing an earlier version', 'known caveat')",
         /showing an earlier version|known caveat/);

  const passed = ok.every(Boolean);
  console.log('\n' + (passed ? `ALL ${ok.length} CORRECT` : 'FAILED: ' + JSON.stringify(ok)));
  process.exit(passed ? 0 : 1);
})().catch(e => { console.error('test_banner.js crashed:', e); process.exit(1); });
