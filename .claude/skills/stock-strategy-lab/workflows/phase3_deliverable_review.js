export const meta = {
  name: 'stock-lab-deliverable-review',
  description: 'Independent review of the final LEAN algorithm (bugs, live hazards, LEAN runs) and fact-check of every claim in the research write-up',
  phases: [
    { title: 'Review', detail: 'LEAN code reviewer and write-up fact-checker in parallel' },
  ],
}

// args: {
//   repo: '/abs/lean repo', work: '/abs/work dir (py311, leandata)', skill_dir: '/abs/skill dir', lab: '/abs/lab',
//   ticker: 'NVDA', algorithm_class: 'NvdaTrendRegimeAlgorithm', readme: '/abs/README.md', research_dir: '/abs/Research/<X>',
//   research_weights: '/abs/weights.csv', lean_out: '/abs/dir with lean_*.csv', lean_log: '/abs/log',
//   env_prefix: 'STRAT_', evidence_paths: ['/abs/journal.jsonl', ...]
// }
const A = args
const ALG = `${A.repo}/Algorithm.Python/${A.algorithm_class}.py`
const FINDINGS = {
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
          evidence: { type: 'string' },
          proposed_fix: { type: 'string', description: 'concrete patch text or exact replacement' },
        },
        required: ['location', 'severity', 'issue', 'evidence', 'proposed_fix'],
      },
    },
    verified_ok: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['findings', 'verified_ok', 'summary'],
}

phase('Review')
const [code, claims] = await parallel([
  () => agent(`You are a senior QuantConnect/LEAN engineer doing an adversarial code review of a trading algorithm before it is committed. Do NOT edit files in ${A.repo}; work in ${A.work}/review_lean/ and report concrete patches (also save a tested unified diff there as patch.diff).

Target: ${ALG}. Its intended rules are documented in its header and in ${A.readme}; the research reference implementation is in ${A.research_dir}; the research weights are ${A.research_weights}. Known pitfalls to check against: ${A.skill_dir}/references/pitfalls.md and ${A.skill_dir}/references/lean.md.

LEAN is runnable: bash ${A.skill_dir}/scripts/run_lean.sh ${A.repo} ${A.work} <Class> <log> runs ${A.repo}/Algorithm.Python/<Class>.py on ${A.work}/leandata. Parameters for local runs come from environment variables ${A.env_prefix}<NAME> (e.g. ${A.env_prefix}OUT=<dir> writes weights/fills/equity CSVs, ${A.env_prefix}MODE=morning, ${A.env_prefix}SLIPPAGE=0.0005). To test a variant (e.g. another start date) copy the file to a new class name in Algorithm.Python, run it and DELETE the copy afterwards; leave git status exactly as you found it.

Check with evidence (LEAN runs where possible): rule fidelity against the documented rules and event lists; 'close' mode weights equal the research weights on every session and fills happen at the next open; 'morning' mode equals 'close' mode, including the first decision after a start/restart; mid-history starts (around splits, inside event holds, inside capitulation chains, on ETF ex-dividend dates) rebuild state exactly; splits and dividends while running; order logic (band, sizing, cash/margin after gaps, cancel_open_orders, rounding, duplicate or oversized orders, the live fallback); live hazards (daily bar timing, missing or repeated bars, holidays/half days, restarts, stale event calendars and how early the warning fires, parameters from environment variables vs get_parameter, file writes in the cloud); code quality that matters. Report every real issue with severity and a concrete tested patch, and list what you verified.`, { label: 'review:lean-code', phase: 'Review', schema: FINDINGS }),

  () => agent(`You are an independent fact-checker. A research write-up must not contain numbers or claims that are not supported by evidence. Do NOT edit files in ${A.repo}; work in ${A.work}/review_claims/.

1. Copy ${A.research_dir} to ${A.work}/review_claims/ (without downloaded data and results), and follow its 'reproduce' instructions from scratch. They must work as written (paths, commands, folders that must exist).
2. Check EVERY number in ${A.readme} against: the reproduction output and the harness (compute anything else needed: stress costs, one-session-delayed weights, rolling windows with monthly AND daily starts), the LEAN outputs in ${A.lean_out} and the LEAN log ${A.lean_log}, and the research/validation/panel reports under ${A.lab} ${(A.evidence_paths || []).length ? 'and in ' + A.evidence_paths.join(', ') : ''}. Flag any number that is wrong, misrounded, mislabelled (per-unit vs account-level, CAGR vs year-to-date total, harness vs LEAN statistics) or unsupported; recompute summed counts (e.g. total configurations) yourself.
3. Check qualitative claims ('never', 'always', 'N of N', 'robust', 'survives') against the reports; flag overstatements and claims that omit an unfavourable period (IS / OOS / recent).
4. Check that expectation ranges attributed to reviewers match what each reviewer actually said.
5. Check the plain-language rules section: could a non-technical reader follow it exactly and get the same trades?
Report each problem with the exact text, the correct value/wording, and the evidence.`, { label: 'review:claims', phase: 'Review', schema: FINDINGS }),
])
return { code, claims }
