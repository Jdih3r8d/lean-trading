# Implementing and verifying the final strategy in LEAN

## Toolchain (once per container)
`scripts/setup_lean.sh <repo> <work>`: .NET 10 from the Ubuntu archive, `dotnet build QuantConnect.Lean.sln`, a Python
3.11 venv with pandas<3 for pythonnet, and `<work>/leandata` with market-hours, symbol-properties and the interest-rate
file. Convert every symbol the algorithm uses with `scripts/to_lean_data.py` (raw prices + factor files; pass
`--splits $(cat <lab>/data/splits.txt)` for the stock, and keep its adj_factor column if main.csv is dividend-adjusted; use the `*_adj.csv` with adj_factor for ETFs, start ETFs a year earlier than the stock so
indicators are warm). Keep converted data OUT of the repo's tracked `Data/` folder (git shows modified qqq/spy files
otherwise). Run with `scripts/run_lean.sh <repo> <work> <Class> <log>`; LEAN reads the class from
`Algorithm.Python/<Class>.py`.

## Algorithm design (copy the structure of assets/reference_lean_algorithm_tsla.py)
That file is the production version of the TSLA strategy after two independent reviews; reuse its infrastructure and
replace only the strategy-specific parts.

Generic parts to keep:
- `add_equity(..., Resolution.DAILY, fill_forward=False, data_normalization_mode=DataNormalizationMode.RAW)` for the
  stock and every signal ETF; IB brokerage model on a MARGIN account; `settings.seed_initial_prices = True`.
- A plain-Python state class that owns the signal windows (adjusted closes) and the event-module counters, with
  `rescale_*` on splits (x split_factor) and dividends (x (1 - distribution/reference_price)), and a `step(session,
  close)` that returns the module flags and the target weight. Unit-testable without LEAN.
- `_replay(upto_exclusive)`: rebuilds the state from SCALED_RAW daily history on the first bar, after a restart, after a
  missing session (continuity guard), merging ETF bars by date.
- Two modes: 'close' (decide on the daily bar at 16:00, market-on-open for the next open) and 'morning' (stateless:
  30 min before the open, rebuild from history, require history to end exactly at the previous session, size with
  the decision close).
- Orders: cancel open orders, then MOO for `int(target * equity * (1 - cash_buffer) / price) - held`, only when the
  target changes or the held weight drifts more than the band (0.05) from it.
- Live only: a market-order fallback 15 min after the open, re-sized from the target after the MOO cancel is confirmed.
- Event calendars hard-coded as a list of reaction sessions + an `extra_*` parameter; warn with `self.error` when the
  list is stale (shorter than the shortest historical gap between events).
- `_param()`: LEAN `get_parameter` first; environment variables (e.g. `STRAT_OUT`, `STRAT_SLIPPAGE`, `STRAT_MODE`)
  only when not live. Optional CSV export of weights, fills and equity in `on_end_of_algorithm` for reconciliation.

Strategy-specific parts to replace when copying the template: the environment prefix `F3_` -> `STRAT_` (must equal the
`env_prefix` passed to the Fase 5 review), `set_start_date`/`set_end_date` (first and last session of main.csv),
symbols and `set_benchmark`, `REACTION_SESSIONS` (column `first_trading_session_reacting` of data/earnings.csv), the
state class (module rules in `step()` and constants; `HISTORY_BARS` >= longest window + margin), `EARNINGS_WARN_DAYS`
(about the shortest historical gap between releases minus 10 days) and the header documentation.

Commands (close mode, then repeat with STRAT_MODE=morning):
```
STRAT_MODE=close STRAT_SLIPPAGE=0.0005 STRAT_OUT=<work>/lean_out \
  bash <skill_dir>/scripts/run_lean.sh <repo> <work> <Clase> <work>/lean_close.log
python3 <skill_dir>/scripts/reconcile_lean.py <lab> <lab>/lead/w_<final>.csv \
  <work>/lean_out/lean_weights_close_band0.05_slip0.0005.csv <work>/lean_out/lean_equity_close_band0.05_slip0.0005.csv <weight column>
```

## Verification standard (do not skip)
1. Run 'close' mode with the CSV export and slippage = the research base cost (0.0005), then
   `scripts/reconcile_lean.py <lab> <research weights.csv> <lean weights.csv> <lean equity.csv>`: target 0 weight
   mismatches on every session and per-period Sharpe/CAGR/MDD within ~0.02 of the research.
2. Run 'morning' mode: identical weights and orders.
3. Start the backtest mid-history (around splits, inside an event hold, inside a capitulation chain): weights from the
   start date onward must match.
4. Check fills: every MOO submitted at the decision close fills at the next session's open; no invalid/cancelled orders.
5. Then the independent code review (`workflows/phase5_deliverable_review.js`) for live hazards.
LEAN's own STATISTICS (Sharpe with a risk-free rate, CAGR on calendar days) differ slightly from the harness; when
quoting LEAN numbers, say which method produced them.
