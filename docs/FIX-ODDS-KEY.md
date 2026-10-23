# When the Odds API refuses our key

**What it looks like:** the watchdog's GitHub issue says *"the Odds API is
refusing our key, so no new odds or props are coming in"*. Odds, props and
the picks built from them stop updating. Scores, news and the models keep
going.

**Why it happens:** the key saved in GitHub is no longer one The Odds API
accepts. On 2026-10-22 the plan was cancelled by accident and bought again,
and every call was refused (HTTP 401) for about 19½ hours, until the key in
GitHub was replaced. Running out of credits can look the same: the API's own
reason is printed in the issue.

**Only Sam can fix it.** No code change helps, and Claude must never see,
ask for or store the key.

<!-- steps -->
1. Find the API key The Odds API gave you for the plan you have now: the email it sent when you subscribed, or your account page at the-odds-api.com. If the reason in the issue says the usage quota is used up, check the plan there instead; the key may be fine.
2. On your computer, open github.com/smh0602/gizmos-picks/settings/secrets/actions. The left menu shows Secrets and variables, then Actions; the page heading reads Actions secrets and variables.
3. Under Repository secrets, click the pencil next to ODDS_API_KEY.
4. Paste the key into Value and click Update secret. Never paste it anywhere else.
5. That is all. The next collect run uses it, and the issue clears itself on the first paid pull that works.
<!-- /steps -->

`watchdog.py` quotes the steps between the two markers above into the issue,
so edit them here and nowhere else.

## Changelog

- 2026-10-23: written after the 10-22 → 10-23 outage (PR "a refused Odds API
  key is BROKEN"). `collect.py` now records each refusal in
  `data/latest/odds-refused.json`, and the watchdog reports it.
