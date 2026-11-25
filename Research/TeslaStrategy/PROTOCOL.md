# TSLA strategy lab: common protocol

> Copy of the protocol the research agents followed in the lab. The lab-only auxiliary datasets it mentions (VIX,
> SPY, TSLA implied vol, deliveries, opex, DATA_NOTES.md) are not shipped here; `fetch_data.py` rebuilds the TSLA and
> QQQ files the final strategy needs, and `data/tsla_earnings.csv` is included.

Lab root: this directory (`lab/`). Python 3.13 with pandas, numpy, numba, scipy installed (pip works for more).

## Data (`data/`)
- `tsla.csv`: TSLA daily OHLCV, split-adjusted, 2010-06-29 .. 2026-11-23 (4,127 sessions). Closes from two
  sources agree within 0.04%. The 2020 (5:1) and 2022 (3:1) splits are already adjusted. The stale Yahoo row of
  2018-03-13 (O/H/L copied from the previous day) was repaired from two other sources. Prices since 2017 have
  2 decimals (up to ~3 bp rounding at 2017-2019 price levels), so do not trust edges below ~10 bp per trade.
- `qqq.csv` / `qqq_adj.csv` (QQQ raw / total-return adjusted, 1999-2026), `spy.csv` / `spy_adj.csv` (1993-2026).
- `vix.csv`: VIX (1990-), VIX3M (2006-), VXN (2009-), VIX9D (2011-) daily closes to 2026-11-23 (CBOE, cross-checked).
  NOTE: VIX closes are struck at 16:15 ET, after the 16:00 equity close -- a signal using VIX[t] can only be
  traded at the open of t+1 (exec='open'), never at the close of t.
- `tsla_iv.csv`: TSLA implied vol (ORATS-derived: atm_iv30, mfiv30, term points, rvol30, iv_rank_252) daily
  2020-01-02..2025-12-31 ONLY (no 2010-2019, no 2026). Single source, medium confidence.
- `tsla_earnings.csv`: all 66 earnings releases 2010Q2..2026Q3 with timing and `first_trading_session_reacting`.
- `tsla_deliveries.csv`: 49 production/delivery reports (2013, 2015Q1..2026Q3) with reaction sessions.
- `opex.csv`: monthly option expiration dates 2010-2026 (quarterly flag).
- Read `data/DATA_NOTES.md` for sources, validation and caveats of every file. `data/superseded/` holds old files
  with known bad prints: do not use them.
- Network: Yahoo, Stooq and most finance APIs are BLOCKED. raw.githubusercontent.com, pypi, `gh api -X GET search/code`
  (a few searches per minute) and WebSearch work.

## Evaluation rules (mandatory)
Use `harness.py` v2 (audited; do not edit it; copy helpers into your own module if you need variants).
Note: `run_weights` models fractional / leveraged / short weights as rebalanced to target every session and
CHARGES that turnover, charges 6%/yr financing on leverage above 1x and 0.5%/yr borrow on shorts.
`trades_from_weights` handles long<->short flips correctly. `shift_permutation_test` returns
(sharpe, p, n_valid). Prefer `walk_forward_weights(df, {name: weights})` over the legacy `walk_forward`.
`engine.sim` (numba, binary positions with gap-aware stops / take-profits / max-hold) is also available.
1. Signals use information up to the close of day t and execute at the open of t+1 (`exec='open'`).
   `exec='close'` is only a robustness variant.
2. Costs: `COST_BASE` = 5 bp per side. Every candidate must also be reported at `COST_STRESS` = 15 bp per side.
3. Choose parameters on IS = 2010-07-01..2018-12-31 ONLY, then report OOS = 2019..2026-11-23, REC = 2023+,
   and Y2026. Also run `walk_forward_weights()` over the family's parameter grid (annual re-selection from past data only).
4. Significance: `shift_permutation_test()` for timing/regime strategies, `random_entry_test()` for event
   strategies with fixed holding periods, `bootstrap_ci()` for the average trade, `deflated_sharpe()` with the
   true number of configurations you tried (count them honestly).
5. Always compare with buy & hold (`buy_and_hold`) and with the reference system `ref_weights(df)['AB_50_50']`
   (OOS Sharpe 1.26, MDD -28%, CAGR 34.4%; buy & hold OOS Sharpe 0.89, MDD -74%, CAGR 43.7%).
6. Check parameter-neighbourhood robustness. A single isolated optimum is not a finding.
7. Report the average return per trade (net of costs), median, win rate, average win and loss, holding days,
   and the number of trades, for each period.
8. Write all your code and outputs in your own subdirectory `lab/<your_family>/`. Never write elsewhere.
