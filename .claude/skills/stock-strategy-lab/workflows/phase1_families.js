export const meta = {
  name: 'stock-lab-families',
  description: 'Strategy families for one stock researched in parallel, each pipelined into an independent validator that reproduces and tries to refute the claims',
  phases: [
    { title: 'Research', detail: 'one quant researcher per strategy family' },
    { title: 'Validate', detail: 'independent re-implementation, code audit and refutation tests per family' },
  ],
}

// args: {
//   lab: '/abs/lab', ticker: 'NVDA',
//   context: 'what study 1 found, the baseline rules and numbers, buy & hold numbers (plain text)',
//   families: [{key, title, scope}] (optional: replaces the defaults), skip: ['ml'] (optional),
//   extra_scope: {vol: 'extra notes for this family', ...} (optional)
// }
const LAB = args.lab
const T = args.ticker
const CONTEXT = args.context || '(no context given: read data/BASELINE.md)'

const DEFAULT_FAMILIES = [
  { key: 'vol', title: 'Volatility signals', scope: `Volatility as a SIGNAL (sizing is another agent's job): realized-volatility regimes (20/60-day RV and its causal trailing percentile), volatility compression then breakout (NR7, Bollinger bandwidth squeeze, ATR contraction followed by range expansion in the trend direction), volatility spikes and their mean reversion once price stabilizes, downside vs upside semivariance, range-based vol (Parkinson / Garman-Klass), VIX/VXN levels, changes and spikes as a regime for ${T} (data/vix.csv; the VIX close is at 16:15 ET so only exec='open' is legal). Measure whether the baseline's modules behave differently by volatility regime and whether a regime switch helps.` },
  { key: 'implied', title: 'Implied volatility & options', scope: `Implied volatility and options-market information. If data has ${T} implied vol, use it with an explicit early/late split (and say a LEAN version needs an IV feed). Hypotheses: variance risk premium (IV - RV) regimes, IV rank extremes, IV term-structure inversion, IV spike-and-reverse as capitulation signals. Use the long-history market proxies in data/vix.csv: VIX term-structure backwardation (VIX/VIX3M > 1, VIX9D/VIX > 1), VXN-VIX spread, VIX percentile, VIX spike-and-reverse, stock realized vol / VXN. Option-expiration effects with data/opex.csv: returns in monthly/quarterly opex weeks vs the following week, the Monday after opex, opex day. VIX-family closes are struck at 16:15 ET: exec='open' only.` },
  { key: 'events', title: 'Earnings & scheduled events', scope: `Earnings and other scheduled events (data/earnings.csv and any data/events_*.csv; read their timing/confidence columns and use first_trading_session_reacting to place the reaction). Hypotheses: pre-earnings run-up, post-earnings-announcement drift (does the reaction session's sign/size predict the next 5-60 sessions? test positive and negative reactions separately: for TSLA only big POSITIVE reactions continued), earnings-gap fade vs continuation, the same for other events, and EVENT-AVOIDANCE overlays (flatten the baseline over the event gap; for TSLA this HURT because the gaps carry a premium). Event counts are small: use random_entry_test and bootstrap, do not over-slice; event dates must be known in advance.` },
  { key: 'regime', title: 'Market regime', scope: `Market regime with the market/sector ETFs in data/ (use the *_adj.csv total-return closes for signals). Hypotheses: market trend gates (ETF > SMA200, ETF SMA crosses, ETF drawdown from its high) gating ${T} long exposure or the baseline's modules (prefer gates that reuse the baseline's own parameters: they add no new degree of freedom); ${T} relative strength vs the market (ratio momentum); idiosyncratic mean reversion (residual return vs market beta, z-score -> reversal); buying ${T} after market capitulation (ETF drop >= X% in k days); rolling beta/correlation regimes. Show robustness in IS and OOS separately, not only in one bear market, and report a one-day-delayed execution.` },
  { key: 'sizing', title: 'Position management & sizing', scope: `Position management applied to the baseline's modules, to buy & hold and to simple signals: stops (fixed %, ATR initial, ATR trailing/chandelier, time stops), profit targets, break-even stops (use engine.sim for gap-aware intraday fills), volatility-targeted sizing (target 20-60% annual vol from EWMA or rolling RV, weight = min(cap, target/RV), caps 1.0 and 1.5; the harness charges rebalancing and 6%/yr financing above 1x), scaling by trend or signal strength, fractional Kelly, drawdown de-risking, pyramiding, module re-weighting, and the rebalancing policy for LEAN (daily re-targeting vs a band of 0.025-0.25 vs fixed shares). Key question: does volatility targeting of buy & hold or of the baseline beat the baseline on Sharpe AND drawdown OOS? (For TSLA it did not: its best risk-adjusted days are the volatile ones.)` },
  { key: 'patterns', title: 'Price/volume patterns & trend ensembles', scope: `Price/volume patterns and trend construction not covered by study 1: multi-horizon trend ensembles (continuous weight = average of many binary trend signals over lookbacks 10-250), weekly-bar signals, 52-week-high proximity and breakouts, opening gaps (follow-through or fill; a rule acting at the same open needs care), volume spikes with price direction (log-volume z-score), dip-in-uptrend, streak momentum/reversal, calendar effects (turn of month, pre-holiday, month of year, day of week) with an explicit multiple-testing correction, and the overnight/intraday decomposition (check its stability by year: for TSLA it died in the last year).` },
  { key: 'ml', title: 'Walk-forward machine learning benchmark', scope: `Can a model using many causal features beat the simple rules out of sample? Features at the close of t: returns over 1-250 sessions, distance to SMAs, RSI, realized vol and its trailing percentile, volume z-score, gap statistics, day of week, VIX/VXN/term-structure and market-ETF features (VIX[t] only for decisions executed at open t+1), sessions until the next scheduled event (dates known in advance). Target: sign or value of the next k-session return from the open of t+1 (k = 1, 5, 20). Models: L2 logistic regression, sklearn HistGradientBoosting (small depth), optionally random forest (pip install scikit-learn if missing). STRICT walk-forward: retrain every January on prior data only (expanding or rolling 5 years), tune only inside the training window (purged nested time-series CV), labels fully realized before each cut-off. Convert predictions to weights; report OOS through the harness, feature importances, and whether it beats the baseline and buy & hold. Keep model variants few and counted.` },
]

let FAMILIES = (args.families && args.families.length) ? args.families : DEFAULT_FAMILIES
if (args.skip && args.skip.length) FAMILIES = FAMILIES.filter((f) => !args.skip.includes(f.key))
if (args.extra_scope) FAMILIES = FAMILIES.map((f) => (args.extra_scope[f.key] ? { ...f, scope: f.scope + ' ' + args.extra_scope[f.key] } : f))
log(`Families: ${FAMILIES.map((f) => f.key).join(', ')}`)

const COMMON = (key) => `You are a quantitative researcher in a team searching for a ROBUST ${T} trading strategy on daily bars. Lab root: ${LAB}.
First read ${LAB}/PROTOCOL.md (mandatory evaluation rules), ${LAB}/harness.py (audited evaluation engine), ${LAB}/config.json (periods) and ${LAB}/data/DATA_NOTES.md.

Context established so far (build on it, do not redo it):
${CONTEXT}

Method (follow it):
1. Before testing, write 4-8 hypotheses with an economic rationale to ${LAB}/${key}/HYPOTHESES.md.
2. Define each parameter grid up front and COUNT every configuration you evaluate (honest trial count).
3. Choose parameters on IS only. If a dataset starts later, use an explicit early/late split that keeps at least the last 3 years untouched, and say so.
4. For your best 1-4 candidates: harness.report at base and stress cost; walk_forward_weights over your grid; shift_permutation_test on OOS (n_perm >= 1000) or random_entry_test for fixed-hold event trades; bootstrap_ci of the average trade; deflated_sharpe with your trial count and measured trial-Sharpe std; a parameter-neighbourhood table; year-by-year returns; exec='close' vs 'open'; one-session-delayed execution; result without the 3 best trades.
5. Test each candidate (a) standalone, (b) as an overlay or filter on the baseline's modules, (c) as an additional module next to the baseline. Report which use helps.
6. Rules must be unambiguous and implementable in LEAN with daily bars: exact formulas, lookbacks, thresholds, data needed, signal at the close of t and order at the open of t+1.
7. Write ALL code and outputs under ${LAB}/${key}/ only. Save each candidate's target weights as ${LAB}/${key}/cand_<name>.csv (date,weight). Never modify harness.py, engine.py or data/.
8. Negative results are valuable. Do not inflate. Be efficient with compute (CPUs are shared with another agent).`

const NUM = { type: ['number', 'null'] }
const CAND = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    rules: { type: 'string', description: 'exact, unambiguous entry/exit/sizing rules incl. formulas, lookbacks, thresholds, data needed, execution timing' },
    rationale: { type: 'string' },
    weights_csv: { type: 'string' },
    code_path: { type: 'string' },
    is_sharpe: NUM, oos_sharpe: NUM, rec_sharpe: NUM, ytd_return: NUM,
    oos_cagr: NUM, oos_mdd: NUM, oos_stress_sharpe: NUM, all_cagr: NUM, all_mdd: NUM,
    delayed_oos_sharpe: NUM, wf_sharpe: NUM,
    n_trades_all: NUM, avg_trade_all: NUM, avg_trade_is: NUM, avg_trade_oos: NUM, avg_trade_rec: NUM,
    median_trade_all: NUM, win_rate_all: NUM, avg_hold_days: NUM, exposure_all: NUM,
    perm_p_oos: NUM, dsr: NUM, avg_trade_ci90_oos: { type: 'string' },
    combo_with_baseline: { type: 'string', description: 'metrics as overlay / extra module with the baseline (IS and OOS Sharpe, MDD, CAGR) and whether it helps' },
    robustness_notes: { type: 'string' },
  },
  required: ['name', 'rules', 'rationale', 'weights_csv', 'code_path', 'is_sharpe', 'oos_sharpe', 'oos_mdd', 'oos_cagr', 'n_trades_all', 'avg_trade_all', 'avg_trade_oos', 'win_rate_all', 'combo_with_baseline', 'robustness_notes'],
}
const FAMILY_SCHEMA = {
  type: 'object',
  properties: {
    family: { type: 'string' },
    configs_tested: { type: 'integer' },
    hypotheses: { type: 'array', items: { type: 'object', properties: { hypothesis: { type: 'string' }, result: { type: 'string' } }, required: ['hypothesis', 'result'] } },
    candidates: { type: 'array', items: CAND },
    negative_results: { type: 'array', items: { type: 'string' } },
    verdict: { type: 'string' },
  },
  required: ['family', 'configs_tested', 'hypotheses', 'candidates', 'negative_results', 'verdict'],
}
const VALID_SCHEMA = {
  type: 'object',
  properties: {
    family: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          reproduced: { type: 'boolean' },
          reproduced_metrics: { type: 'string' },
          discrepancies: { type: 'string' },
          code_issues: { type: 'string' },
          refutation_tests: { type: 'array', items: { type: 'object', properties: { test: { type: 'string' }, result: { type: 'string' }, passes: { type: 'boolean' } }, required: ['test', 'result', 'passes'] } },
          adds_value_vs_baseline: { type: 'string' },
          verdict: { type: 'string', enum: ['confirmed', 'weak', 'refuted'] },
          reason: { type: 'string' },
        },
        required: ['name', 'reproduced', 'reproduced_metrics', 'discrepancies', 'code_issues', 'refutation_tests', 'adds_value_vs_baseline', 'verdict', 'reason'],
      },
    },
    family_level_issues: { type: 'string' },
    summary: { type: 'string' },
  },
  required: ['family', 'candidates', 'family_level_issues', 'summary'],
}

const results = await pipeline(
  FAMILIES,
  (f) => agent(`${COMMON(f.key)}\n\nYOUR FAMILY: ${f.title} (directory ${LAB}/${f.key}/).\nScope: ${f.scope}`, { label: `research:${f.key}`, phase: 'Research', schema: FAMILY_SCHEMA }),
  (res, f) => {
    if (!res) return null
    if (!res.candidates || res.candidates.length === 0) return { research: res, validation: null }
    return agent(`You are an independent, skeptical validator. A researcher studied the ${T} strategy family "${f.title}" and claims the candidates below. REPRODUCE each claim and try hard to REFUTE it. Lab root: ${LAB}. Read ${LAB}/PROTOCOL.md, ${LAB}/harness.py, ${LAB}/config.json and ${LAB}/data/DATA_NOTES.md first.

Context: ${CONTEXT}

Researcher's claims (JSON):
${JSON.stringify(res, null, 1)}

For each candidate (at most 4):
1. Re-implement the rules FROM THE TEXT ONLY in ${LAB}/validation_${f.key}/ (do NOT open the researcher's code or weights before finishing this step). Run harness.report at base and stress cost and compute the trade stats.
2. Compare with the claimed numbers.
3. Then read the researcher's code and weights and explain every material discrepancy. Hunt for: look-ahead (same-close fills, centred or full-sample normalisation/percentiles, future event dates, 16:15 VIX used for a 16:00 decision, revised data), off-by-one errors, costs not charged, parameters chosen with OOS data, dishonest trial counts.
4. Refutation tests: permutation / random-entry on OOS; remove the 3 best trades; exclude the single best year; costs at 25 bp per side; exec='close' vs 'open' and a one-session-delayed execution; +-20-30% perturbation of each parameter; year-by-year consistency; the latest year.
5. Judge whether it adds value versus the baseline and buy & hold, standalone and combined.
Verdict per candidate: confirmed (reproduces, survives the tests, adds value), weak (real but small or fragile), refuted (bug, look-ahead, or does not survive). Write only under ${LAB}/validation_${f.key}/.`, { label: `validate:${f.key}`, phase: 'Validate', schema: VALID_SCHEMA })
      .then((v) => ({ research: res, validation: v }))
  },
)

return results.filter(Boolean)
