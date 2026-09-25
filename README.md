# jd-play-scraper

Free, stdlib-only scanner of public ATS job boards (Greenhouse / Lever / Ashby) that
finds companies **hiring outbound-sales roles right now** — an approved-budget signal
for anyone selling into their pipeline.

Built by [Pipeline Factory](https://pipelinefactory.vercel.app). We use it daily; you can run it yourself.

## Why this signal works

A company posting an SDR/BDR/AE/RevOps role has (a) money allocated for outbound and
(b) a pipeline gap for the ~90 days until the hire ramps. That window is exactly when
they'll buy leads or outsourced pipeline.

## Run it

```bash
python jd_play.py            # full scan (~380 companies, ~4 min)
python jd_play.py 40         # first 40 companies only (quick test)
python jd_play.py --selfcheck
```

No API keys. No dependencies. Output: `jd_leads.json` —
`{company, ats, role, title, location, url, posted, fetched_at}`.

The company list (`companies.json`) comes from the MIT-licensed
[ConorsCode/open-jobs-data](https://github.com/ConorsCode/open-jobs-data) dataset (378 companies, 9 ATS platforms).

Last full run (2026-09-25): 2,662 matching roles across 214 companies, 338 boards scanned.

## Be polite

- 0.25s pause between boards, custom User-Agent, 12s timeout.
- These are the same public feeds each platform's careers widget uses — they're meant to be read.
- Don't hammer: one scan per day is plenty (postings don't churn faster).

## License

MIT.
