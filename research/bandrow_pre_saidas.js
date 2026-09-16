/* FROZEN COPY — `bandRow` exactly as `origin/main` carried it at
   d6c5a4c, the commit before the optional `saidAs` label was added
   (2026-09-17).

   🔴 THIS FILE IS AN ORACLE, NOT CODE. Nothing on the page imports it.
   `test_fb_record.py` renders MLB's REAL calibration through this
   version and through the live one and asserts the two strings are
   byte-identical — which is the whole licence for touching a component
   MLB depends on. "I did not change the MLB call site" is not that
   proof; this is.

   ⛔ DO NOT UPDATE IT TO MATCH A NEW `bandRow`. The moment it tracks the
   live version it proves nothing, and the check is written to fail if
   the two files are identical. If MLB's rendered bands must change, that
   is a decision for Sam and for the MLB freeze, not a fixture edit. */
function bandRow(b){
  const gap = b.hit == null ? null : b.hit - b.said;
  const cls = gap == null ? 'v-none' : (gap >= 0 ? 'v-good' : 'v-bad');
  const verdict = gap == null ? 'No sample'
                : gap >= 0 ? 'Beat the claim'
                : gap > -10 ? 'Slightly hot' : 'Overconfident';
  return `<div class="band">
    <div class="bn">${b.name}<small>${b.n} pick${b.n===1?'':'s'}</small></div>
    <div class="track">
      ${b.hit != null ? `<div class="hit ${gap >= 0 ? 'good' : 'bad'}" style="width:${b.hit}%"></div>` : ''}
      <div class="said" style="left:${b.said}%" title="we said ${b.said}%"></div>
      <div class="lbl">hit ${b.hit != null ? b.hit + '%' : '—'} &nbsp;·&nbsp; claimed ${b.said}%</div>
    </div>
    <div class="verd ${cls}">${verdict}${gap != null ? `<br><span style="font-weight:600;color:var(--mut)">${
      gap > 0 ? '+' : ''}${gap.toFixed(1)} pts</span>` : ''}</div>
  </div>`;
}
