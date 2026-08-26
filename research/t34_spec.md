# T34 -- does a Poisson projection fit HITTER markets?

Registered 2026-08-26, BEFORE any fit was run.

## Why
Pitcher projections invert the row's own distribution (Poisson for K,
Normal for outs) and both are the distribution the MODEL already assumes,
so the inversion is exact by construction. Hitter rows have NO model. The
displayed number is a DESCRIPTIVE rate. To turn that rate into a
projection something must supply a distribution, and the cheap assumption
is Poisson.

Poisson is almost certainly WRONG for total bases -- a home run is 4 bases,
so TB is overdispersed and Poisson will read its mean too high off an OVER
rate. The question is how wrong, in the units on the page.

## Specification
For every hitter with >= 25 games he STARTED (real batting order where the
lineup file has it; `pa >= 3` fallback, per CLAUDE.md), for every market in
{hits, total bases, home runs, RBIs, H+R+RBI} at every line the book
actually posts:

  p_hat = observed P(X > line)
  lam   = the Poisson mean that reproduces p_hat   (card.invert_poisson)
  xbar  = his observed per-game mean of that stat

Statistic: `lam - xbar`, in the market's own units.

## The bar, fixed now
Poisson SHIPS as the hitter projection if, per market:
  * |mean(lam - xbar)| < 0.10 units, AND
  * the 90th percentile of |lam - xbar| < 0.25 units.

Any market failing either half does NOT get a Poisson projection.
The fallback, to be tested at the SAME bar and only then: a negative
binomial matched to the player's own observed mean AND variance.

## Forbidden
- Moving either half of the bar after seeing a result.
- Shipping Poisson on some markets and NB on others without re-testing the
  survivors at the same bar.
- Reporting only the markets that passed.
- Labelling any hitter projection MODEL. Ledger rule 55: it is DESCRIPTIVE
  whatever distribution wins, because the rate behind it is descriptive.

## Prediction, recorded now
Hits and RBIs pass (small counts, near-Poisson). Home runs pass on the
mean but the sample is thin. **Total bases FAILS**, biased HIGH, by
roughly +0.2 to +0.4 bases. H+R+RBI fails too, same reason -- it inherits
TB's tail through the RBI leg.

---

## RESULT, 2026-08-26

| market | n | Poisson mean | p90|d| | NB mean | p90|d| | ships |
|---|---|---|---|---|---|---|
| hits | 1058 | +0.0142 | 0.202 | +0.0146 | 0.198 | **Poisson** |
| total bases | 1628 | −0.0162 | 0.673 | +0.0329 | 0.350 | **NEITHER** |
| home runs | 377 | +0.0056 | 0.022 | +0.0055 | 0.016 | **Poisson** |
| RBIs | 977 | +0.0547 | 0.299 | +0.0174 | 0.117 | **NegBin** |
| H+R+RBI | 1654 | −0.1192 | 0.696 | +0.0138 | 0.356 | **NEITHER** |

Every shipped market cleared BOTH halves of the bar under the distribution
it ships with. No bar was moved.

### My pre-registered prediction was WRONG, and wrong in a useful way.
I predicted total bases would fail **biased high by +0.2 to +0.4 bases**.
It is not biased at all — Poisson's mean error on TB is **−0.016**, the
second-smallest of the five. It fails on **SPREAD**: p90 |error| 0.673.
That is the worse failure of the two. A consistent bias can be subtracted;
an unbiased estimator that is wrong by two-thirds of a base on one row in
ten cannot be, and it would print a confidently precise wrong number.

I also predicted RBIs would pass under Poisson. It failed (p90 0.299) and
needed the negative binomial. RBI is lumpier than it looks — a three-run
homer is one swing.

## T34b -- registered NOW, before running, for the two markets with nothing

Total bases and H+R+RBI have no distribution that clears the bar. The only
remaining candidate is to stop inverting and print the player's **observed
per-game mean** directly. That reproduces the mean by construction (error
exactly 0), so the mean-accuracy bar is vacuous and CANNOT be the test.
What it risks instead is the thing inversion bought: the mean may sit on
the LOSING side of the line the row picked.

Bar, fixed now: the observed mean lands on the picked side of the line in
**>= 97%** of rows whose displayed rate is >= 60%. Below that, total bases
and H+R+RBI ship with **no projection at all**, and the page says so.

Prediction, recorded now: this FAILS on unders. A hitter who stays under
1.5 total bases in 80% of games still has a mean near 1.0 -- but the ones
topping an UNDER board are the low-power bats, so I expect the failure to
be concentrated in a few percent, landing somewhere around 93-98%. I am
genuinely unsure which side of 97% it falls on, which is the point of
fixing the number first.

### T34b RESULT
| market | on the picked side | bar 97% |
|---|---|---|
| total bases | 1318/1386 = **95.09%** | FAIL |
| H+R+RBI | 1239/1278 = **96.95%** | FAIL |

Prediction was right on shape and wrong on nothing that mattered: **every
single miss (68 + 39 = 107 of 107) is an UNDER**, as predicted, and both
landed inside the 93-98% range I named. H+R+RBI misses the bar by 0.05
points. The bar was fixed before the run and it is not moving for a near
miss -- that is the entire reason for fixing it first.

## T35 -- registered NOW, before running: compound Poisson for total bases

The one structural candidate not yet tried. TB is not a count, it is a
SUM: `TB = 1B + 2*2B + 3*3B + 4*HR`. That is why a Poisson fitted to it
has the wrong tail -- one swing moves it by four. But the count underneath
it, HITS, passed T34 cleanly (p90 0.202). So model hits as Poisson and
draw each hit's base value from the player's OWN observed extra-base mix.

Bar: THE SAME AS T34 -- |mean(implied - observed)| < 0.10 bases AND
p90 |implied - observed| < 0.25 bases. Not renegotiable, not per-line.

Prediction, recorded now: this passes on the mean and I expect p90 around
0.20-0.35 -- so roughly a coin flip against the 0.25 half of the bar. The
mechanism is right, but the extra-base mix is estimated from few events
for most hitters and that noise goes straight into the tail.

If it fails, total bases and H+R+RBI ship with NO PROJECTION and the page
says why. Three of five hitter markets carrying one is an honest state; a
fourth carrying a wrong one is not.

### T35 RESULT
`total bases, compound Poisson: n=1628  mean +0.0335  p90|d| 0.287  FAIL`

Progression on the same statistic: plain Poisson **0.673** -> negative
binomial **0.350** -> compound Poisson **0.287**, bar **0.25**. The
mechanism was right -- modelling TB as a sum over hits rather than as a
count cut the error by more than half -- and it still does not clear. My
prediction ("0.20-0.35, roughly a coin flip") was accurate, including that
the extra-base mix is the noisy part.

## FINAL DISPOSITION
| market | projection | distribution |
|---|---|---|
| hits | YES | Poisson (T34) |
| home runs | YES | Poisson (T34) |
| RBIs | YES | negative binomial, player's own mean and variance (T34) |
| total bases | **NO** | nothing cleared 0.25 (T34, T35) |
| H+R+RBI | **NO** | nothing cleared 0.25 (T34, T34b) |

⛔ Do not add a projection to total bases or H+R+RBI without a NEW
pre-registered test that clears the SAME bar. Three tries have failed;
the fourth does not get an easier one. The page states the absence.
🔴 All three shipped hitter projections are labelled **DESCRIPTIVE**, never
MODEL. The rate they invert is the player's own record, and rule 55 binds.
