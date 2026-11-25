"""Reconcile a LEAN run with the research weights, session by session, and compare per-period performance.

usage: python3 reconcile_lean.py <lab_dir> <research_weights.csv> <lean_weights.csv> [lean_equity.csv] [lean_column]

research_weights.csv: columns date,weight (the target decided at each close, as used with harness.run_weights).
lean_weights.csv:     written by the LEAN algorithm's CSV export. The weight column is 'weight' or 'target' if present,
                      otherwise pass its name as the 5th argument (the TSLA template writes date,A,G,B,P,F3 -> 'F3').
lean_equity.csv:      columns date,tpv (portfolio value at each session close). Per-period Sharpe/CAGR/MDD are computed
                      with the harness method for both LEAN and the research weights (base cost), side by side.
                      LEAN's own STATISTICS (Sharpe net of a risk-free rate, CAGR on calendar days) differ slightly.
Goal: 0 weight mismatches, and per-period numbers within ~0.02 Sharpe. A component flip on a near-tie day that does not
change the final weight is acceptable; anything else is a bug to find.
"""
import os
import sys

import pandas as pd

lab = os.path.abspath(sys.argv[1])
sys.path.insert(0, lab)
import harness as H  # noqa: E402

rw = pd.read_csv(sys.argv[2], parse_dates=['date']).set_index('date')['weight']
lw_df = pd.read_csv(sys.argv[3], parse_dates=['date']).set_index('date')
if len(sys.argv) > 5:
    col = sys.argv[5]
else:
    col = next((c for c in ('weight', 'target') if c in lw_df), lw_df.select_dtypes('number').columns[-1])
print(f'using LEAN weight column: {col}')
lw = lw_df[col]
common = rw.index.intersection(lw.index)
diff = (rw.loc[common] - lw.loc[common]).abs()
bad = diff[diff > 1e-9]
print(f'research sessions {len(rw)}, LEAN sessions {len(lw)}, common {len(common)}, '
      f'missing in LEAN {len(rw.index.difference(lw.index))}, extra in LEAN {len(lw.index.difference(rw.index))}, '
      f'weight mismatches {len(bad)}')
if len(bad):
    print(pd.DataFrame({'research': rw.loc[bad.index], 'lean': lw.loc[bad.index]}).head(20).to_string())
if len(sys.argv) > 4 and sys.argv[4] not in ('', '-'):
    eq = pd.read_csv(sys.argv[4], parse_dates=['date']).set_index('date')['tpv']
    r = eq.pct_change().dropna()
    df = H.load_prices()
    rr = H.run_weights(df, rw.reindex(df.index).fillna(0.0)).loc[r.index[0]:r.index[-1]]
    for p, (lo, hi) in H.PERIODS.items():
        out = []
        for name, x in (('LEAN', r), ('research', rr)):
            m = H.perf(x, lo, hi)
            if p == 'Y_YTD':
                m = {'ytd_total (not annualised)': m['total'], 'sharpe': m['sharpe'], 'mdd': m['mdd']}
            else:
                m = {k: m[k] for k in ('cagr', 'sharpe', 'mdd')}
            out.append(f"{name} " + ' '.join(f'{k}={float(v):.3f}' for k, v in m.items()))
        print(f'{p:6s} | ' + ' | '.join(out))
