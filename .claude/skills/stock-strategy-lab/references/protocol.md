# Strategy lab: common protocol (read before any research)

Lab root: this directory. Python 3 with pandas, numpy, numba and scipy (pip works for more).
`config.json` holds the ticker and the evaluation periods; `harness.py` reads it.

## Data (`data/`)
- `main.csv`: daily OHLCV of the stock under study, split-adjusted (date,open,high,low,close,volume).
- Other files (market ETFs, VIX family, event calendars, implied vol...) are described in `data/DATA_NOTES.md`.
  Read it: every file lists its sources, how it was cross-checked and its known artefacts.
- Network: most finance APIs (Yahoo, Stooq...) are usually blocked from cloud sessions. raw.githubusercontent.com,
  pypi, `gh api -X GET search/code` (a few searches per minute) and WebSearch usually work.
- Prices of recent years may be rounded to 2 decimals: do not trust edges smaller than ~10 bp per trade.
- Index/volatility closes such as VIX are struck at 16:15 ET, after the 16:00 equity close: a signal using them at
  day t can only be traded at the open of t+1, never at the close of t.

## Evaluation rules (mandatory)
Use `harness.py` (audited; do not edit it; copy helpers into your own module for variants).
`run_weights` models fractional / leveraged / short weights as rebalanced to target every session and CHARGES that
turnover, 6%/yr financing on leverage above 1x and 0.5%/yr borrow on shorts. `trades_from_weights` handles long<->short
flips. `shift_permutation_test` returns (sharpe, p, n_valid). Use `walk_forward_weights(df, {name: weights})` for
walk-forward. `engine.sim` (numba; binary positions with gap-aware stops / take-profits / max-hold) is also available.

1. Signals use information up to the close of day t and execute at the open of t+1 (`exec='open'`).
   `exec='close'` is a robustness variant only.
2. Costs: `COST_BASE` = 5 bp per side. Every candidate must also be reported at `COST_STRESS` = 15 bp per side.
3. Choose parameters on IS ONLY (config.json is_start..is_end), then report OOS, REC (last ~3 years) and Y_YTD.
   Also run `walk_forward_weights()` over your parameter grid (annual re-selection from past data only).
   If a dataset starts later than the stock (e.g. implied vol), use an explicit early/late split that keeps at least
   the last 3 years untouched for out-of-sample, and say so.
4. Significance: `shift_permutation_test()` for timing/regime strategies, `random_entry_test()` for long, fixed-hold
   event strategies, `bootstrap_ci()` (default is a 90% interval) for the average trade, `deflated_sharpe()` with
   the TRUE number of configurations you tried and the measured std of the trial Sharpes in DAILY units
   (annualised std / sqrt(252); passing the annualised value pushes the DSR towards 0).
5. Always compare with buy & hold and with the reference strategy (`load_baseline(df)`, if
   `data/baseline_weights.csv` exists; its numbers are in `data/BASELINE.md`). For buy & hold quote
   `perf(buy_and_hold(df), lo, hi)` per period (close-to-close, no costs); `report()` with weight 1 gives the same
   Sharpe/MDD but its trade statistics are meaningless (one long trade).
6. Check parameter-neighbourhood robustness (a single isolated optimum is not a finding), year-by-year returns,
   one-day-delayed execution (weights shifted one session) and removal of the 3 best trades.
7. Report the average return per trade net of costs, median, win rate, average win and loss, holding days and number
   of trades, per period. State the basis: per unit of capital allocated to the module, or account level.
8. Write all your code and outputs in your own subdirectory `<lab>/<your_label>/`, including `trials.csv` (one row per
   configuration evaluated: config,is_sharpe,oos_sharpe). Never modify harness.py, engine.py
   or data/. Save candidate target weights as `cand_<name>.csv` (columns date,weight) so others can reproduce them.
9. Count your configurations honestly, pre-register hypotheses before testing, and report negative results.
