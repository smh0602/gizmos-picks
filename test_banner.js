/* THE PAGE'S STALENESS BANNER — behaviour test.
 *
 * 🔴 SELF-EXTRACTING. It reads index.html and pulls the banner code out
 * of it, so it tests THE SHIPPED PAGE and cannot drift from a copy.
 * ⛔ An earlier version read a file that only existed in a scratch
 * directory, which meant it would have silently passed on the runner
 * while testing nothing.
 *
 * The case that matters most is the last one: when the page CANNOT tell
 * whether it is current, it must say so rather than render silently.
 * That exact silence is what let the site serve 15-hour-old props on
 * 2026-08-28 while looking completely normal.
 */
const fs = require('fs');

const html = fs.readFileSync('index.html', 'utf8');
const a = html.indexOf('let FRESH = null;');
const b = html.indexOf('function freshness(iso){');
if (a < 0 || b < 0 || b <= a) {
  console.error('COULD NOT FIND THE BANNER CODE IN index.html.');
  console.error('Either the page changed shape or the banner was removed —');
  console.error('both are things this test exists to notice.');
  process.exit(1);
}
const bar = { className: '', innerHTML: '' };
global.document = { getElementById: id => (id === 'stalebar' ? bar : null) };
eval(html.slice(a, b) + '\nglobalThis.__set = d => { FRESH = d; };'
   + '\nglobalThis.__fn = typeof renderStaleBanner;');
if (__fn !== 'function') {
  console.error('renderStaleBanner() IS NOT DEFINED IN index.html.');
  console.error('The page has no way to tell a reader it is out of date —');
  console.error('which is the exact failure of 2026-08-28.');
  process.exit(1);
}

function run(label, doc, expectVisible) {
  __set(doc);
  bar.className = ''; bar.innerHTML = '';
  renderStaleBanner();
  const visible = bar.className.includes('warn');
  const text = bar.innerHTML.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  const ok = visible === expectVisible;
  console.log(`  [${ok ? 'OK  ' : 'WRONG'}] ${visible ? 'SHOWN ' : 'hidden'}  ${label}`);
  if (visible) console.log(`            "${text.slice(0, 200)}"`);
  return ok;
}

console.log('BANNER BEHAVIOUR\n');
const ok = [];

ok.push(run('everything built on schedule -> stays out of the way',
  { artifacts: [{ mode: 'card', stale: false }, { mode: 'gamelines', stale: false }] }, false));

ok.push(run('several tabs late -> named by TAB, not by mode', {
  artifacts: [
    { mode: 'props-pitcher', stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'props-batter',  stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'gamelines',     stale: true, late_min: 408, due_et: '7:00/16:00', missing: false },
    { mode: 'record',        stale: true, late_min: 468, due_et: '6:00',       missing: false },
    { mode: 'card',          stale: false }] }, true));

ok.push(run('a tab never built at all', {
  artifacts: [{ mode: 'results', stale: true, late_min: null, due_et: '6:00', missing: true }] }, true));

ok.push(run('the freshness report failed to load', null, true));
ok.push(run('the freshness report is malformed', { artifacts: 'oops' }, true));

const passed = ok.every(Boolean);
console.log('\n' + (passed ? `ALL ${ok.length} CORRECT` : 'FAILED: ' + JSON.stringify(ok)));
process.exit(passed ? 0 : 1);
