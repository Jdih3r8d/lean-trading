# Getting daily data from a locked-down cloud session

What worked in the TSLA study (Nov 2026). Hosts change; re-probe before relying on any of this.

## What is reachable
Probe quickly with `curl -s -o /dev/null -m 15 -w '%{http_code}' <url>`; `[agent-proxy]` lines in a failed command say
which host was refused. Typical result: Yahoo (query1.finance.yahoo.com), Stooq, Alpha Vantage, FMP, Polygon, Tiingo,
Nasdaq Data Link, Kaggle and Google were BLOCKED; raw.githubusercontent.com, pypi.org, registry.npmjs.org,
api.nuget.org, archive.ubuntu.com and packages.microsoft.com were OPEN, and the WebSearch tool worked.
Do not try to route around a blocked host.

## Prices: public CSV mirrors on GitHub
1. Search: `gh api -X GET search/code -f q='filename:<TICKER>.csv' -f per_page=50 --jq '.items[] | .repository.full_name + " " + .path'`.
   Also try `filename:<TICKER>.csv "<YYYY-MM>"` with the current month (finds auto-updating repos), `filename:<ticker>_daily.csv`,
   and lower-case names. Sleep a few seconds between searches (rate limit).
2. Download candidates with `curl -sL https://raw.githubusercontent.com/<owner>/<repo>/HEAD/<path>` into a fresh
   directory and look at `head -2` / `tail -2` to find the date range and whether prices are split-adjusted.
3. Build `main.csv` by splicing an old long-history source with a recent auto-updating one. Validate the overlap:
   closes should agree within ~0.05%. Then run `scripts/check_data.py <lab> <other sources...>` and repair only rows
   where two INDEPENDENT feeds agree (many repos mirror the same Yahoo feed; agreement between mirrors proves nothing).
   Known Yahoo artefact: rows whose open/high/low repeat the previous day's (TSLA 2018-03-13).
4. Note per-source quirks: volume in millions, dates like 01/02/2013, timezone-suffixed timestamps, rounding to 2
   decimals, dividend adjustment or not.
Sources that were useful for TSLA/QQQ/SPY: `yennanliu/finance_data` (data/prices/<ticker>.csv, daily updates, raw
prices with div/split columns, 2016+), `Stonks/tickers` (tickers/nasdaq/<T>.csv, long history to 2023, split-adjusted),
`alm0421/alm0421` (data/prices/<T>.csv with dividend and adj_close: good for ETFs), `flytothejy/market-data`,
`willhjw/big_movers`, `BrendaAMelo/FINS3657-group-project`. The LEAN repo's own `Data/equity/usa/daily/*.zip` has a few
tickers (SPY, QQQ, AAPL...) to ~2021: useful as an independent cross-check (prices x10000, raw + factor files).

## Market regime and volatility
- QQQ / SPY / sector ETFs: same GitHub approach; build a dividend-adjusted (total return) version with an adj_factor
  column (factor 1 - dividend/previous close on each ex-date, cumulated backwards) for signals, and check it against a
  published adj_close.
- VIX, VIX9D, VIX3M, VXN: CBOE-format history files mirrored on GitHub (search `filename:VIX_History.csv`,
  `vix_history.csv`, `vixfamily.csv`). Yahoo copies of the VIX family have bad prints; prefer CBOE copies and splice
  several, checking overlaps exactly.

## Event calendars
- Earnings dates: the reliable timing source is the SEC 8-K (Item 2.02) acceptance timestamp. data.sec.gov is usually
  blocked, but cached EDGAR submissions JSON files exist on GitHub (search the company's CIK or `submissions` +
  ticker). Cross-check with partial lists (AlphaVantage/Yahoo dumps on GitHub: search `filename:<TICKER>_earnings.csv`)
  and web search. Record for each release: announce date, timing (after close / before open), the last session
  before the news and the FIRST SESSION WHOSE OPEN REFLECTS IT. AlphaVantage's 'pre-market' flags for old years were
  wrong for TSLA; one release in 66 was pre-market.
- Other company events (deliveries, product days, index inclusion) only if relevant; same timing rules.
- Option expirations: compute them (3rd Friday; Thursday if Friday is an exchange holiday).

## Implied volatility of the stock
Rare. For TSLA only 2020-2025 ORATS-derived data was found (in a thesis repo). If found, record coverage honestly; a
signal that cannot be tested before the data starts, or in the current year, is exploratory only, and LEAN would need
an options/IV feed to trade it.

## Document everything
Write `data/DATA_NOTES.md`: for every file its columns, date range, sources per segment, how it was validated
(overlap statistics) and caveats. Research agents read it.
