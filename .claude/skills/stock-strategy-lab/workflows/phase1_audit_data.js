export const meta = {
  name: 'stock-lab-phase1-audit-data',
  description: 'Audit the shared backtest harness and acquire the auxiliary datasets for a single-stock strategy lab',
  phases: [
    { title: 'Audit & Data', detail: 'independent harness audit + auxiliary data acquisition in parallel' },
  ],
}

// Fase 1 of the stock-strategy-lab skill.
// args: { lab: '/abs/path/to/lab', ticker: 'NVDA', skill_dir: '/abs/skill dir', market_etfs: ['QQQ','SPY','SMH'], extra_data_goals: '...' }
const LAB = args.lab
const T = args.ticker
const ETFS = (args.market_etfs && args.market_etfs.length) ? args.market_etfs : ['QQQ', 'SPY']
const EXTRA = args.extra_data_goals || ''
const SKILL_REF = args.skill_dir ? `${args.skill_dir}/references/data_sources.md` : 'the skill references/data_sources.md'

const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          location: { type: 'string' },
          severity: { type: 'string', enum: ['critical', 'major', 'minor', 'note'] },
          issue: { type: 'string' },
          evidence: { type: 'string', description: 'concrete reproduction: inputs, expected vs actual numbers' },
          proposed_fix: { type: 'string' },
        },
        required: ['location', 'severity', 'issue', 'evidence', 'proposed_fix'],
      },
    },
    verified_ok: { type: 'array', items: { type: 'string' } },
    test_script: { type: 'string' },
  },
  required: ['findings', 'verified_ok', 'test_script'],
}

const DATA_SCHEMA = {
  type: 'object',
  properties: {
    files: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          content: { type: 'string', description: 'columns, date range, rows' },
          sources: { type: 'string' },
          validation: { type: 'string' },
          caveats: { type: 'string' },
        },
        required: ['path', 'content', 'sources', 'validation', 'caveats'],
      },
    },
    not_found: { type: 'array', items: { type: 'string' } },
  },
  required: ['files', 'not_found'],
}

phase('Audit & Data')
const [audit, data] = await parallel([
  () => agent(`You are an independent, skeptical auditor of a backtesting harness. Find bugs that would make backtest results wrong or optimistic.

Audit (read fully): ${LAB}/harness.py, ${LAB}/engine.py, ${LAB}/PROTOCOL.md, ${LAB}/config.json. Data: ${LAB}/data/main.csv (${T} daily split-adjusted OHLCV). Write tests only under ${LAB}/audit/; do NOT edit harness.py, engine.py or data/.

Check each item with a concrete numerical test (synthetic price series with hand-computed answers where possible):
1. Look-ahead: run_weights timing for exec='open' and exec='close'; adding a future signal must not change past returns.
2. Costs: turnover charged once per entry/exit on the right day; partial weights, leverage (financing), shorts (borrow), long<->short flips.
3. trades_from_weights: reconciles with run_weights equity (sum of log1p), entry/exit days, flips, last bar.
4. engine.sim (numba): gap-through stops and take-profits, max_hold counting, exit timing, re-entry index, daily vs trade returns, both modes.
5. perf / trade_stats / exposure: CAGR, Sharpe, MDD (including a first-day loss), period filtering by entry date.
6. walk_forward_weights: no leakage of the selection year; weight stitching timing at year boundaries; switching cost.
7. shift_permutation_test, random_entry_test, bootstrap_ci, deflated_sharpe: statistical validity, NaN handling, (1+k)/(1+n), the DSR formula (Bailey & Lopez de Prado 2014).
8. fixed_hold / trend_capitulation_weights: ignore rules and holding periods as documented.
9. Data sanity of main.csv: duplicates, non-positive prices, high<low, open/close outside [low,high], weekend rows, gaps, unadjusted split jumps, STALE rows whose open/high/low equal the previous row's (a known Yahoo artefact), 2-decimal rounding.
10. config.json periods: sensible for this stock's history (IS long enough to choose parameters, OOS and the last ~3 years untouched).
Report every real issue with severity and reproducible evidence; list what you verified as correct and how.`, { label: 'audit:harness', phase: 'Audit & Data', schema: AUDIT_SCHEMA }),

  () => agent(`You are a data-acquisition agent for a ${T} trading research lab at ${LAB}. Read ${LAB}/PROTOCOL.md and ${SKILL_REF} first (what is reachable from this sandbox and which GitHub mirrors worked before). Do not try to bypass the proxy. Load the WebSearch tool with ToolSearch ("select:WebSearch") if you need it. Sleep a few seconds between GitHub code searches.

The lead has already built ${LAB}/data/main.csv (${T}); do not modify it. Save new files in ${LAB}/data/ and APPEND one section per new file to ${LAB}/data/DATA_NOTES.md (columns, range, sources per segment, validation with overlap statistics, caveats, confidence); keep the lead's existing sections about main.csv and splits unchanged. Goals in priority order:
1. Market ETFs ${ETFS.join(', ')}: daily OHLCV from one year before main.csv starts (or from the ETF's inception if later; say so in DATA_NOTES.md) until main.csv's last date. Save raw (<etf>.csv) and a dividend-adjusted total-return version with an adj_factor column (<etf>_adj.csv: adjusted price = raw price * adj_factor), validated against a published adj_close. Calendars must match main.csv.
2. VIX family: VIX, VIX3M, VIX9D, VXN (and a sector/volatility index relevant to ${T} if one exists) daily closes, as recent as main.csv; prefer CBOE-format copies, splice and cross-check. Save data/vix.csv.
3. ${T} earnings releases for the whole history: announce date, timing (after close / before open), last session before the news, and first_trading_session_reacting (the first session whose OPEN reflects the release). Use SEC 8-K Item 2.02 acceptance timestamps (cached EDGAR submissions JSON on GitHub; data.sec.gov is usually blocked) and cross-check with at least one other source. Save data/earnings.csv with a confidence column.
4. Other scheduled company events that move ${T} (only if they exist and are relevant; e.g. delivery/sales reports, product events), with the same timing rules. Save data/events_<name>.csv.
5. ${T} implied volatility history (30-day ATM IV, IV rank) if any public source exists; record coverage honestly.
6. data/opex.csv: monthly option expirations (3rd Friday; Thursday if Friday is an exchange holiday), quarterly flag.
${EXTRA ? '7. Extra goals from the lead: ' + EXTRA : ''}
Validate everything (dates must be sessions of main.csv where relevant; no duplicates; plausible values). Be honest about confidence and list what you could not find and what you tried.`, { label: 'data:acquire', phase: 'Audit & Data', schema: DATA_SCHEMA }),
])
return { audit, data }
