export const meta = {
  name: 'stock-lab-challenge',
  description: 'Try to beat the lead candidate with richer constructions, and attack it with three independent skeptics (statistics, implementation, regime)',
  phases: [
    { title: 'Challenge', detail: 'optimizer tries to beat the candidate robustly; three skeptics try to refute it' },
  ],
}

// args: {
//   lab: '/abs/lab', ticker: 'NVDA',
//   brief: 'history (study 1 + families, trial counts recomputed from configs_tested), validator verdicts per component,
//           exact component and candidate definitions, the lead's reproduction file (e.g. lead/components.py) and weights
//           CSVs, the lead's numbers for baseline / fallback / candidate / buy & hold incl. stress cost and one-day delay',
//   lean_work: '/abs/work dir with py311 + leandata' (optional), repo: '/abs/lean repo' (optional)
// }
const LAB = args.lab
const T = args.ticker
const BRIEF = `${T} strategy lab at ${LAB}. Read ${LAB}/PROTOCOL.md, ${LAB}/harness.py, ${LAB}/config.json and ${LAB}/data/DATA_NOTES.md first.

${args.brief}

Write only under ${LAB}/final_<your_label>/.`
const LEAN_NOTE = args.lean_work
  ? `A LEAN toolchain is ready: repo ${args.repo}, Python 3.11 venv ${args.lean_work}/py311, LEAN data folder ${args.lean_work}/leandata. You may write a LEAN Python algorithm under ${LAB}/final_impl/lean/ and run it by copying it to ${args.repo}/Algorithm.Python/<Class>.py (delete the copy afterwards and leave git status clean) with: bash <skill>/scripts/run_lean.sh ${args.repo} ${args.lean_work} <Class> <log>.`
  : 'No LEAN toolchain is set up; specify the implementation precisely and simulate share-level execution in Python.'

const VERDICT = {
  type: 'object',
  properties: {
    verdict_on_candidate: { type: 'string', enum: ['adopt', 'adopt_with_changes', 'prefer_alternative', 'reject'] },
    recommended_strategy: { type: 'string', description: 'exact rules of the strategy you recommend for production' },
    key_findings: { type: 'array', items: { type: 'string' } },
    numbers: { type: 'string' },
    expected_live_performance: { type: 'string', description: 'honest forward-looking expectation after haircuts: Sharpe, CAGR, MDD, average trade per module' },
    risks_and_caveats: { type: 'array', items: { type: 'string' } },
    files: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict_on_candidate', 'recommended_strategy', 'key_findings', 'numbers', 'expected_live_performance', 'risks_and_caveats', 'files'],
}

const TASKS = [
  { label: 'optimizer', prompt: `${BRIEF}

YOUR ROLE: challenger-optimizer. Do not stop at the lead's candidate: try hard to find a construction that beats it ROBUSTLY using all components the families produced (weights CSVs in ${LAB}/<family>/cand_*.csv). Ideas: sleeve weights and caps (chosen on IS only), adding the weak modules, gating other modules, ensembles of gates, walk-forward-weighted allocation (re-estimated each January from past data), smoothed/ensemble versions of fragile modules, risk scaling to equal volatility. Pre-register your candidate list and the decision rule in ${LAB}/final_optimizer/PLAN.md BEFORE evaluating, count the trials, select on IS and walk-forward only, then report OOS / recent / YTD, stress costs, one-day delay, paired block-bootstrap Sharpe differences vs the candidate and vs the baseline, and incremental permutation tests. If nothing beats the candidate robustly, say so and recommend it (or a simplification).` },
  { label: 'skeptic-stats', prompt: `${BRIEF}

YOUR ROLE: skeptic, statistics and overfitting lens. Try to refute the candidate. Quantify selection bias honestly (recompute the total trial count from the families' trials.csv / configs_tested; note any choice made with OOS knowledge). Compute: paired stationary block-bootstrap Sharpe differences candidate-baseline, candidate-fallback and candidate-buy&hold for IS, OOS and recent; deflated Sharpe with realistic trial counts and measured trial-Sharpe std; incremental permutation tests shifting one component at a time; a search-adjusted reality check for each selected parameter (e.g. the chosen gate against its whole grid, event thresholds against placebo dates); probability of backtest overfitting (CSCV/PBO) over a reasonable candidate set; walk-forward over that set; a Monte-Carlo block bootstrap of 3-year outcomes (also with the stock's drift reset to a lower value); dependency on the top 5 trades and the best year. Conclude with the haircut you would apply to Sharpe and CAGR and whether the candidate is statistically distinguishable from the baseline and from the fallback.` },
  { label: 'skeptic-impl', prompt: `${BRIEF}

YOUR ROLE: skeptic, implementation, data and look-ahead lens. Independently re-implement the candidate from the rule text with your OWN bar-by-bar loop (no pandas rolling shortcuts) and verify the weights match the lead's CSV on every session; hunt for bugs or look-ahead in the lead's code (event reaction-session mapping, the reference close for event reactions, adjusted vs raw ETF closes, calendars, warm-up, caps and overlapping sleeves, ignore rules). Think like a live trader: are event dates known in time; does market-on-open match the harness open; what about half days, holidays, splits and dividends during a position; slippage. Quantify daily re-targeting vs band rebalancing (0.05 / 0.10) vs fixed-share sleeves with share-level simulation including per-share fees (IBKR ~$0.005/share, min $1) on RAW prices. ${LEAN_NOTE} Specify precisely, step by step, how to implement the candidate in a LEAN daily-resolution Python algorithm so that it reproduces the backtest (follow the structure of the skill's assets/reference_lean_algorithm_tsla.py if available: RAW subscriptions, own windows rescaled on corporate actions, history replay, close and morning modes, band rebalancing). Report any discrepancy or bug.` },
  { label: 'skeptic-regime', prompt: `${BRIEF}

YOUR ROLE: skeptic, regime and economic-robustness lens. Try to refute the candidate by looking at WHEN it works: year-by-year and quarter-by-quarter vs baseline and buy & hold, rolling 2-year Sharpe, performance by market regime (market bull/bear, VIX high/low, stock high/low vol), behaviour in the main crashes and melt-ups of ${T}'s history and the current year, time under water and the longest flat periods, opportunity cost vs buy & hold (share of rolling 3-year windows, monthly AND daily starts, where it beats buy & hold on return, Sharpe and drawdown; note the windows overlap), decay checks (split the sample into thirds per module), the economic rationale of each module and whether it can persist. Stress all parameters jointly (random +-30% perturbations, ~500 draws: distribution of OOS and recent Sharpe vs the baseline, and the percentile of the nominal parameters inside the cloud). Conclude whether the edge looks structural or an artefact of a few years.` },
]

phase('Challenge')
const results = await parallel(TASKS.map((t) => () => agent(t.prompt, { label: t.label, phase: 'Challenge', schema: VERDICT })))
return TASKS.map((t, i) => ({ role: t.label, result: results[i] }))
