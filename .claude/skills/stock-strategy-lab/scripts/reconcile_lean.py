"""Reconcile a LEAN run with the research weights, session by session.

usage: python3 reconcile_lean.py <lab_dir> <research_weights.csv> <lean_weights.csv> [lean_equity.csv]

research_weights.csv: columns date,weight (the target decided at each close, as used with harness.run_weights).
lean_weights.csv:     columns date,...,<weight column> written by the LEAN algorithm (last numeric column is used
                      unless a column named 'weight' or 'target' exists).
lean_equity.csv:      columns date,tpv (portfolio value at each session close) -> per-period Sharpe/CAGR/MDD with
                      the harness method, so LEAN and research numbers are comparable (LEAN's own Sharpe subtracts a
                      risk-free rate and its CAGR uses calendar days).
The goal is 0 weight mismatches. In the TSLA study the only acceptable residual was a component flip on a near-tie day
that did not change the final weight.
"""
import os
import sys

import pandas as pd

lab = os.path.abspath(sys.argv[1])
sys.path.insert(0, lab)
import harness as H  # noqa: E402

rw = pd.read_csv(sys.argv[2], parse_dates=['date']).set_index('date')['weight']
lw_df = pd.read_csv(sys.argv[3], parse_dates=['date']).set_index('date')
col = next((c for c in ('weight', 'target') if c in lw_df), lw_df.select_dtypes('number').columns[-1])
lw = lw_df[col]
common = rw.index.intersection(lw.index)
diff = (rw.loc[common] - lw.loc[common]).abs()
bad = diff[diff > 1e-9]
print(f'research sessions {len(rw)}, LEAN sessions {len(lw)}, common {len(common)}, '
      f'missing in LEAN {len(rw.index.difference(lw.index))}, weight mismatches {len(bad)}')
if len(bad):
    print(pd.DataFrame({'research': rw.loc[bad.index], 'lean': lw.loc[bad.index]}).head(20).to_string())
if len(sys.argv) > 4:
    eq = pd.read_csv(sys.argv[4], parse_dates=['date']).set_index('date')['tpv']
    r = eq.pct_change().dropna()
    for p, (lo, hi) in H.PERIODS.items():
        print(p, {k: round(v, 3) for k, v in H.perf(r, lo, hi).items()})
