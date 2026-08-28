# T38 — IS THE MEAN THE WRONG CENTRAL ESTIMATE FOR A RIGHT-SKEWED HITTER MARKET?
Pre-registered 2026-08-28, BEFORE any fit. Triggered by a real build failure.

## WHAT HAPPENED
Scheduled card run #183 (2026-08-28T02:22Z) failed its own verifier on ONE row:
  Amed Rosario, batter_total_bases, UNDER 1.5, confidence 75, projection 1.6.
Both numbers are correct and they disagree, and the disagreement is not noise:

  n = 41 games (pa >= 3, point-in-time)
  TB distribution: 0 x12 · 1 x18 · 2 x4 · 4 x4 · 5 x1 · 8 x1 · 10 x1
  MEAN   1.585      MEDIAN 1      under 1.5 in 30/41 = 73.2%
  mean without his four biggest games: 1.027

⛔ THE PICK IS WELL FOUNDED AND THE PROJECTION IS ARITHMETICALLY RIGHT. They
disagree because a MEAN is a poor summary of a right-skewed count: 30 of his 41
games are 0 or 1 total base, and a 10-TB game drags the average over the line.
🔴 THIS IS THE SAME SKEW T34 FOUND when three distributions failed to reproduce
total bases at the tail. It is a known weakness surfacing in a new place.

## THE QUESTION
For the skewed hitter markets, does a MEDIAN (or a trimmed mean) serve the reader
better than the mean -- i.e. contradict the row it sits beside far less often --
without giving up the properties the mean was chosen for?

## WHAT THE MEAN BUYS, AND MUST NOT BE LOST
1. LINE-INDEPENDENCE. One number per player per market (ledger rule 66).
2. It reproduces the player's own per-game average EXACTLY, which is what T34
   asked for and nothing else could do.
3. It is recomputable from the raw log by verify_card.py.
⚠️ A median keeps (1) and (3) and GIVES UP (2). That is the trade being tested.

## CANDIDATES
  A. MEDIAN of his point-in-time per-game values.
  B. 10% TRIMMED MEAN (drop the top and bottom decile).
  C. Keep the MEAN (the null).

## THE BAR, FIXED NOW, BEFORE ANY MEASUREMENT
Over a POOLED set of at least 200 priced hitter rows at >= 70% confidence,
gathered across published cards:
  - the candidate must contradict its own row in <= 2% of rows;
  - AND it must not increase contradictions on ANY individual market versus the
    mean; a candidate that fixes total bases by breaking RBIs FAILS.
  - AND it must stay within 0.35 units of the mean on median absolute difference,
    so "better agreement" cannot be bought by simply projecting near zero.
All three must hold. ⛔ If no candidate clears all three, the MEAN STAYS.

## PREDICTION, WRITTEN BEFORE RUNNING
The median will cut total-bases contradictions to near zero and will do the same
for H+R+RBI, which has the same shape. I expect it to FAIL the third condition on
home runs, where the median is 0 for almost every hitter and the mean is ~0.15 --
a median of 0 is useless beside a 0.5 line. So I expect the answer to be a
PER-MARKET choice rather than one estimator for all five, and I expect the trimmed
mean to be the compromise that clears all three.

## WHAT IS NOT BEING DONE TONIGHT
⛔ THE ESTIMATOR IS NOT CHANGED. Swapping it on the strength of one row is exactly
the move this project does not make. Rosario stays as he is, mean and all, until
this test is run on a real sample.
