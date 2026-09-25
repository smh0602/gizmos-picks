const fs=require('fs');
const html=fs.readFileSync('index.html','utf8');
// Pull the real implementation out of the page -- never a copy of it.
// `[2026-09-25]` boardFor now reads the ET date through the page's own
// etDate(), so that is lifted too -- a stand-in would be a second copy.
const src=html.match(/const BOARD_MATCH_WINDOW_MS[\s\S]*?\n}/)[0];
const etSrc=html.match(/const etDate = [\s\S]*?\n};/)[0];
const BOARD=JSON.parse(fs.readFileSync('data/latest/board.json','utf8'));
const [boardFor, etDate]=new Function('BOARD', etSrc+'\n'+src+'; return [boardFor, etDate];')(BOARD);

const dupes={};
BOARD.games.forEach(g=>{const k=g.away+'|'+g.home; (dupes[k]||=[]).push(g);});
const affected=Object.entries(dupes).filter(([,v])=>v.length>1);
console.log(`${affected.length} team-pairs appear twice in this board pull\n`);

let fail=0;
for (const [k,v] of affected){
  const sorted=v.slice().sort((a,b)=>a.commence<b.commence?-1:1);
  const night=sorted[0], today=sorted[sorted.length-1];
  // The card for TODAY'S game passes today's first pitch.
  const got=boardFor(today.away, today.home, today.commence);
  const ok = got && got.commence===today.commence;
  if(!ok) fail++;
  console.log(`  ${ok?'✅':'❌'} ${k.split('|')[0].slice(0,12)} @ ${k.split('|')[1].slice(0,12)}  ` +
    `asked for ${today.commence}  got ${got?got.commence:'null'}  ` +
    `(the trap: ${night.commence}, total ${night.total})`);
  // And the card for LAST NIGHT'S game must get last night's, not today's.
  const got2=boardFor(night.away, night.home, night.commence);
  if(!(got2 && got2.commence===night.commence)){ fail++; console.log(`     ❌ reverse: got ${got2&&got2.commence}`); }
}

// ══════════════════════════════════════════════════════════════════════
// 🔴🔴 EVERY PROBE TIMESTAMP BELOW IS DERIVED FROM THE BOARD. NONE IS
// WRITTEN DOWN. `[rule 166 for the third time, red on 2026-09-14]`
//
// ⛔ THIS BLOCK USED TO ASK `boardFor(..., '2026-09-15T20:00:00Z')` and
// call it "20 days from any record". It WAS 20 days away -- when it was
// written, against an 08-26 board. Today the board covers 09-14..09-16,
// so the literal landed INSIDE the window, `boardFor` correctly returned
// the 09-15 record, and the check failed a page that was right.
// ⚠️ THE PRODUCT WAS CORRECT AND THE CHECK HAD AN EXPIRY DATE NOTHING
// EXPIRED -- rule 166, after `test_record_reset` and `test_box_live`.
//
// ✅ AND THE REPLACEMENT IS STRICTLY HARDER, not merely date-proof. The
// old form probed ONE point far outside the window, which any function
// returning null often enough would pass. This probes BOTH EDGES of
// `BOARD_MATCH_WINDOW_MS` itself -- just inside must MATCH, just outside
// must be NULL -- so it now fails a window that is too wide, too narrow,
// or ignored, none of which the old form could detect.
const WINDOW=Number(html.match(/const BOARD_MATCH_WINDOW_MS\s*=\s*([^;]+);/)[1]
                     .replace(/[^0-9*\s]/g,'').split('*').reduce((a,b)=>a*Number(b),1));
if(!Number.isFinite(WINDOW)||WINDOW<=0){
  console.log(`  ❌ could not read BOARD_MATCH_WINDOW_MS from the page -> ${WINDOW}`);
  fail++;
}

// Fails closed: a game with no board record at all returns null, not a guess.
const anchor=BOARD.games[0];
const none=boardFor('Nonexistent Team','Other Team',anchor.commence);
console.log(`\n  ${none===null?'✅':'❌'} unknown matchup -> ${none}`);
if(none!==null) fail++;

// ⛔⛔ THE EDGE PROBES I FIRST WROTE HERE WERE A TAUTOLOGY AND I CAUGHT
// IT BY DRIVING THEM. They read `BOARD_MATCH_WINDOW_MS` off the page and
// then probed at `WINDOW ± 60s` -- so when I widened the real window to
// 8h and narrowed it to 1h, the probes MOVED WITH IT and both runs stayed
// green. ⚠️ A check that derives its expectation from the thing it is
// checking cannot fail. That is rule 67 wearing rule 207's clothes, and
// it is the second fake guard I have written this week.
//
// ✅ SO THE INVARIANT IS TAKEN FROM THE DATA INSTEAD. The window exists
// to separate a doubleheader from the SAME PAIR's next-day game -- a
// 9:40pm ET first pitch is 01:40Z tomorrow, which is how six games' live
// odds reached the following day's cards. ⛔ So the window MUST be
// narrower than the smallest gap between two records of one pair, or the
// trap is unsolvable no matter how good the matcher is.
const gaps=[];
for(const [,v] of affected){
  const ts=v.map(g=>Date.parse(g.commence)).sort((a,b)=>a-b);
  for(let n=1;n<ts.length;n++) gaps.push(ts[n]-ts[n-1]);
}
if(!gaps.length){
  console.log('  ⚠️ NOT EXERCISED: no pair appears twice on this board, so '
    +'the window cannot be bounded from data today');
}else{
  const minGap=Math.min(...gaps);
  const ok = WINDOW < minGap;
  if(!ok) fail++;
  console.log(`  ${ok?'✅':'❌'} the ${WINDOW/3600000}h window is narrower than the `
    +`closest same-pair gap (${(minGap/3600000).toFixed(1)}h)`);
}

// ⚠️ WHAT THIS DOES NOT CATCH, SAID PLAINLY: a window NARROWED below 4h.
// Narrowing only makes `boardFor` fail closed more often, and a card
// missing a line is a card missing a line -- the safe direction, per
// CLAUDE.md. The dangerous direction is widening, and widening past the
// doubleheader gap is what the assertion above fails on.

// ══════════════════════════════════════════════════════════════════════
// 🔴🔴 THE CARDS ASK WITH MLB's GAME, NOT WITH THE BOARD's OWN TIME.
// `[2026-09-25]` Every probe above passes the RECORD's commence back in,
// so it can only ever find the record it started from. The page asks with
// MLB's `gameDate` -- and MLB lists game 2 of a traditional doubleheader
// at a placeholder (BAL @ NYY: 20:10Z beside game 1's 20:05Z, odds feed
// 23:06Z). All six assertions above were green while game 2's card showed
// game 1's odds.
// ✅ So replay the newest STORED schedule -- the same statsapi payload the
// page fetches -- through the page's matcher, game object and all, and
// assert the one thing a doubleheader must never do: hand ONE board record
// to TWO games. Discovered from the data, never dated (test_frozen_dates).
const zlib=require('zlib'), path=require('path');
const snaps=[];
for (const d of fs.readdirSync('data').filter(x=>/^\d{4}-\d\d-\d\d$/.test(x)).sort().slice(-3)){
  const dir=path.join('data',d,'schedule');
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir).filter(x=>x.endsWith('.json.gz'))) snaps.push(path.join(dir,f));
}
snaps.sort();
const sched=snaps.length
  ? JSON.parse(zlib.gunzipSync(fs.readFileSync(snaps[snaps.length-1])).toString()).schedule||{}
  : {};
const mlbGames=[].concat(...(sched.dates||[]).map(x=>x.games||[]));
const owner={};
let matched=0;
const failBefore=fail;
for (const g of mlbGames){
  const a=g.teams.away.team.name, h=g.teams.home.team.name;
  const r=boardFor(a, h, g.gameDate, g);
  if (!r) continue;
  matched++;
  const sameDay = r.away===a && r.home===h && (g.officialDate||etDate(g.gameDate))===etDate(r.commence);
  if (!sameDay){ fail++; console.log(`  ❌ ${a} @ ${h} game ${g.gameNumber} got a record from another pair or day: ${r.commence}`); }
  if (owner[r.id] && owner[r.id]!==g.gamePk){
    fail++;
    console.log(`  ❌ ONE RECORD, TWO GAMES: ${a} @ ${h} -- ${r.id.slice(0,8)} (${r.commence}) `
      +`went to game ${owner[r.id]} AND game ${g.gamePk} (game ${g.gameNumber}, MLB time ${g.gameDate})`);
  }
  owner[r.id]=g.gamePk;
}
const dhs=mlbGames.filter(g=>g.doubleHeader==='S'||g.doubleHeader==='Y').length;
if (!snaps.length || !matched){
  console.log(`  ⚠️ NOT EXERCISED: ${snaps.length?'no game in the newest schedule has a board record':'no stored schedule'}`);
}else{
  console.log(`  ${fail===failBefore?'✅':'❌'} ${matched} of ${mlbGames.length} scheduled game(s) in ${snaps[snaps.length-1]} matched, `
    +`${dhs} doubleheader game(s)`+(fail===failBefore?', and no record went to two games':''));
}

// ...and far beyond it, measured from the board's OWN last record.
const last=BOARD.games.reduce((a,g)=>g.commence>a?g.commence:a,BOARD.games[0].commence);
const farISO=new Date(Date.parse(last)+20*86400000).toISOString();
const far=boardFor(anchor.away,anchor.home,farISO);
console.log(`  ${far===null?'✅':'❌'} 20 days past the board's last game (${farISO.slice(0,10)}) -> ${far}`);
if(far!==null) fail++;
console.log(fail? `\n❌ ${fail} FAILURES` : `\n✅ all ${affected.length*2+2} assertions passed`);
process.exit(fail?1:0);
