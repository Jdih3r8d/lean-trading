# Pitfalls found in the TSLA study (and how the skill avoids them)

Each of these actually happened. Keep the checks; they are cheap.

## Data
- **Stale Yahoo rows**: TSLA 2018-03-13 repeated the previous day's open/high/low, creating a fake -4.9% gap. Several
  "independent" GitHub CSVs were mirrors of the same feed and had the same error. `check_data.py` flags rows whose O/H/L
  equal the previous row's; repair only from sources that are truly independent.
- **Bad cross-source "corrections"**: two other sources disagreed with ours on 2021-03-01/04 highs, but they were the
  wrong ones (the value was impossible given the real price). Sanity-check against known prices before overwriting.
- **VIX prints**: Yahoo copies of VIX/VIX9D/VIX3M had dozens of bad days; CBOE-format copies agreed exactly.
- **Timing of auxiliary data**: VIX closes at 16:15 ET, earnings are released after the close, delivery reports come
  out on weekends: every signal must be placed on the first session whose open could react.

## Harness / backtest engine (found by the independent audit before research started)
- Trade ledger double-counted long<->short flip days (3 cost sides per trade instead of 2).
- Fractional weights (0.5) were silently rebalanced daily without charging turnover; leverage had no financing cost.
- MDD ignored a loss on the first day of a window.
- Permutation p-values counted NaN simulations as "worse than actual" and could report p = 0.
- Trades were assigned to periods by signal date; walk-forward stitched return streams (no switching cost, one
  overnight gap of look-ahead per year).
Lesson: ALWAYS run the harness audit (Fase 1 workflow) even when reusing this harness on new data or after edits.
- Generic-harness defaults were TSLA dates (walk-forward 2014-2026, permutation from 2010-07-01): now derived from the
  data and config.json. Check config.json periods for every new stock (check_data.py warns).

## Research
- **Drift masquerading as edge**: on a stock that rose 200x, almost every long rule "works". Compare the average trade
  with buy-and-hold drift over the same holding period, and use random-entry / shift-permutation nulls.
- **Mean reversion decays**: TSLA's RSI/Bollinger rules looked great in 2010-2018 and their edge over drift vanished OOS.
- **Selecting the best recent strategy each year** (walk-forward over families) underperformed buy & hold.
- **OOS contamination**: once OOS numbers are printed next to IS numbers, later choices are no longer blind. Validators
  caught that the "fast QQQ gate" region and the 10/30 choice were found with OOS in view. Disclose it; prefer choices
  that add no new parameter (e.g. reuse the trend module's own 10/30 on the market ETF).
- **Fragility to execution delay**: the capitulation module lost its value with a one-day delay; several VIX/ML
  overlays too. Always report a one-session delay.
- **Concentration**: 3-5 trades (2020) carried much of every OOS result. Report "without the 3 best trades".
- **Volatility targeting hurt** TSLA: its best risk-adjusted days are high-volatility days. Do not assume textbook
  sizing helps.
- **Combining modules that are individually weak** raised IS Sharpe and lowered OOS (textbook overfitting, PBO ~0.5).
  Freeze the specification once the panel agrees.
- **Arithmetic in briefs propagates**: the lead's brief summed family trial counts wrong (3,750 vs 3,401) and the
  panel reused it. Recompute counts from the families' own `configs_tested`.

## Splits and dividends (found when testing the skill on NVDA)
- NVDA had 6 splits, not the 2 recent ones; with an incomplete list LEAN's early raw prices were 12x too low, silently.
  The Yahoo split DATE can be wrong (2001-09-10 vs the real first split session 2001-09-17). Confirm in raw prices.
- Dividends: a split-only main.csv ignores dividends in research and buy & hold; for dividend payers use a
  total-return main.csv with adj_factor so research and LEAN agree.

## LEAN implementation
- Feeding split-adjusted prices as raw made share counts and per-share IBKR fees ~3x too high. Use raw prices + a split
  factor file (`to_lean_data.py --splits`) and subscribe with `DataNormalizationMode.RAW`.
- Built-in SMA indicators and RollingWindows are NOT rescaled at a live split/dividend: a 3:1 split looks like a -67%
  crash and fires capitulation signals. Keep your own windows and rescale them on corporate actions, or rebuild from
  SCALED_RAW history.
- Factor files written with 10 significant digits lost one share at a split. Write full precision.
- Fill-forward bars must not count as sessions (`fill_forward=False` + `is_fill_forward` guard).
- Morning mode skipped the first decision after a restart because the security price was 0 before the first bar
  (`settings.seed_initial_prices = True` fixes it; size orders with the decision close).
- A stale earnings calendar silently disables an event module: warn ~60 days after the last listed event (the shortest
  gap between TSLA releases was 70 days), with `self.error`, once per day.
- Live fallback (market order when an MOO did not fill) must re-size from the target after the cancel is confirmed,
  or it can double the position.
- Environment-variable overrides are fine for local backtests only; use `get_parameter` in live/cloud.
- Sizing at 100% of equity with the decision close needs a margin account (gap-ups push weight to ~1.04).
- Rebalancing policy matters: daily re-targeting (harness) vs a 5% band (LEAN) agree; fixed-share sleeves lose ~0.05
  Sharpe and 3 points of drawdown. Use the band and reproduce it.

## Communication (the user's own feedback)
- The user did not want code or files: they wanted to be told, in plain words, WHAT the strategy is, WHEN to buy, WHEN
  to sell, how much, what to expect and what to do today. Code and repo files are proof and automation, secondary.
  Lead the final answer with the plain-language playbook (references/final_answer.md).
- Write-ups overstated claims until a fact-checker compared every number with the evidence ("never lost money over 3
  years" was false with daily starts; per-unit vs account-level returns were mixed up). Always run the claims review.

## Rebound mode (25-Nov-2026 run: a 10-stock "Top Movers" screenshot, US and European)
- GitHub price mirrors end on different dates (24-Nov, 23-Nov, 20-Nov, 17-Nov the same day). The old screen pasted
  today's % on top of a stale close and produced false 5-session drops (NVTS -28% instead of -15%). The screen now
  checks the last expected NYSE session and marks stale tickers `REVISAR` without inventing today's bar.
- ~23 agents exhausted the session's ~200 web searches; four analysts could not verify anything and one missed that
  its stock (INSM) had a signed cash takeover. The workflow now runs the market agent first, passes its news to the
  analysts and gives every agent a search budget (`search_budget`).
- A small "Top Movers" list with a 0.00% among the best is the user's own portfolio/watchlist: analyse the risers too
  (continuation lens) and say what to do if they already hold each stock. A 0.00% can be a broker artefact; US % shown
  during European hours are LS Exchange/Tradegate pre-market quotes.
- A usage limit killed 5 of 23 agents mid-run; `resumeFromRunId` served the 18 finished ones from cache. Edit only the
  last call (the judge) when resuming, or the cache is invalidated.
