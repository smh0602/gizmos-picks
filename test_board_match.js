const fs=require('fs');
const html=fs.readFileSync('index.html','utf8');
// Pull the real implementation out of the page -- never a copy of it.
const src=html.match(/const BOARD_MATCH_WINDOW_MS[\s\S]*?\n}/)[0];
const BOARD=JSON.parse(fs.readFileSync('data/latest/board.json','utf8'));
const boardFor=new Function('BOARD', src+'; return boardFor;')(BOARD);

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

// Fails closed: a game with no board record at all returns null, not a guess.
const none=boardFor('Nonexistent Team','Other Team','2026-08-26T20:00:00Z');
console.log(`\n  ${none===null?'✅':'❌'} unknown matchup -> ${none}`);
// A real matchup whose first pitch is nowhere near any record -> null.
const far=boardFor(BOARD.games[0].away, BOARD.games[0].home, '2026-09-15T20:00:00Z');
console.log(`  ${far===null?'✅':'❌'} matchup 20 days from any record -> ${far}`);
if(none!==null||far!==null) fail++;
console.log(fail? `\n❌ ${fail} FAILURES` : `\n✅ all ${affected.length*2+2} assertions passed`);
process.exit(fail?1:0);
