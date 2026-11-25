"""Study 1: broad sweep of classic daily rules on one stock, with an honest in-sample / out-of-sample split.

usage: python3 classic_sweep.py <lab_dir>          (writes <lab_dir>/study1/grid.csv and prints a summary)

Families (about 6,000 configurations, a few seconds with numba): RSI mean reversion, consecutive down closes,
N-day drops, Bollinger, IBS, big-up-day continuation and reversal, overbought shorts, close>SMA trend and its short,
SMA crosses, Donchian breakouts (with optional stops), time-series momentum. Every rule is long-only unless named
'short'; signals at the close of t, filled at the open of t+1 (mode 0) or at the close of t (mode 1, robustness only).
Also prints the overnight/intraday decomposition and calendar effects, which were informative for TSLA.

How to read it (lessons from the TSLA study):
  * Select on IS only (IS t-stat > 2, PF > 1.3, n >= 30), then look at how the selection behaves OOS. For TSLA,
    92% of IS-selected mean-reversion rules stayed profitable OOS but only 2% stayed significant: their 'edge' was the
    stock's drift. Always compare the average trade with the drift over the same holding period (column *_exc).
  * Trend rules often match buy & hold on Sharpe while halving the drawdown; shorts usually lose on a strong stock.
  * Neighbourhood robustness matters more than the single best cell.
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

LAB = os.path.abspath(sys.argv[1])
sys.path.insert(0, LAB)
import harness as H  # noqa: E402
from engine import sim, stats, rsi  # noqa: E402

df = H.load_prices()
O, Hh, L, C = [df[k].values.astype(float) for k in ['open', 'high', 'low', 'close']]
c = df.close
idx = df.index.values
SPLIT = np.datetime64(H.PERIODS['OOS'][0])
REC = np.datetime64(H.PERIODS['REC'][0])
n = len(c)
NO = np.zeros(n, bool)
sma = {k: c.rolling(k).mean() for k in [5, 10, 20, 30, 50, 100, 150, 200]}
rs = {k: rsi(c, k) for k in [2, 3, 4, 5, 14]}
ibs = ((df.close - df.low) / (df.high - df.low)).fillna(0.5)
filters = {'none': np.ones(n, bool), 'sma200': (c > sma[200]).values, 'sma100': (c > sma[100]).values, 'sma50': (c > sma[50]).values}
rows = []


def run(fam, params, entry, exitsig=NO, side=1, max_hold=10 ** 6, stop=0., tp=0., mode=0):
    entry = np.nan_to_num(np.asarray(entry, dtype=float)).astype(bool)
    exitsig = np.nan_to_num(np.asarray(exitsig, dtype=float)).astype(bool)
    tr, daily, _ = sim(O, Hh, L, C, entry, exitsig, side, max_hold, stop, tp, mode, H.COST_BASE)
    row = dict(fam=fam, params=params, side=side, mode=mode)
    for p, (lo, hi) in (('is', (None, SPLIT)), ('oos', (SPLIT, None)), ('rec', (REC, None))):
        for k, v in stats(tr, daily, idx, lo, hi).items():
            row[f'{p}_{k}'] = v
    rows.append(row)


for mode in (0, 1):
    for rn, x, fk, ex, mh in itertools.product([2, 3, 4, 5], [5, 10, 15, 20, 25, 30], filters, ['rsi50', 'rsi65', 'rsi75', 'sma5', 'hold'], [3, 5, 10, 20]):
        exs = {'rsi50': rs[rn] > 50, 'rsi65': rs[rn] > 65, 'rsi75': rs[rn] > 75, 'sma5': c > sma[5], 'hold': pd.Series(NO, index=c.index)}[ex]
        run('RSI_MR', f'rsi{rn}<{x} f={fk} exit={ex} mh={mh}', (rs[rn] < x).values & filters[fk], np.asarray(exs), max_hold=mh, mode=mode)
    dn = (c < c.shift()).astype(int)
    for k, fk, ex, mh in itertools.product([2, 3, 4, 5], filters, ['upclose', 'sma5', 'hold'], [1, 3, 5, 10]):
        exs = {'upclose': (c > c.shift()).values, 'sma5': (c > sma[5]).values, 'hold': NO}[ex]
        run('DownDays', f'{k}down f={fk} exit={ex} mh={mh}', (dn.rolling(k).sum() == k).values & filters[fk], exs, max_hold=mh, mode=mode)
    for k, x, fk, mh in itertools.product([1, 2, 3, 5, 10], [0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25], filters, [1, 2, 3, 5, 10, 20]):
        run('Drop', f'drop{k}d>={x:.0%} f={fk} mh={mh}', (c / c.shift(k) - 1 <= -x).values & filters[fk], max_hold=mh, mode=mode)
    m20, sd20 = sma[20], c.rolling(20).std()
    for z, fk, mh in itertools.product([1.5, 2.0, 2.5], filters, [5, 10, 20]):
        run('Boll', f'z={z} f={fk} mh={mh}', (c < m20 - z * sd20).values & filters[fk], (c > m20).values, max_hold=mh, mode=mode)
    for x, fk, mh in itertools.product([0.1, 0.15, 0.2, 0.25], filters, [1, 3, 5]):
        run('IBS', f'ibs<{x} f={fk} mh={mh}', (ibs < x).values & filters[fk], (ibs > 0.7).values, max_hold=mh, mode=mode)
    r1 = c.pct_change()
    for x, mh in itertools.product([0.03, 0.05, 0.08, 0.10], [1, 3, 5, 10, 20]):
        run('BigUp_long', f'up>={x:.0%} mh={mh}', (r1 >= x).values, max_hold=mh, mode=mode)
        run('BigUp_short', f'up>={x:.0%} mh={mh}', (r1 >= x).values, side=-1, max_hold=mh, mode=mode)
    for rn, x, mh in itertools.product([2, 3, 5], [90, 95, 98], [1, 3, 5, 10]):
        run('RSI_short', f'rsi{rn}>{x} mh={mh}', (rs[rn] > x).values & (c < sma[200]).values, (rs[rn] < 50).values, side=-1, max_hold=mh, mode=mode)
    for k in [20, 30, 50, 100, 150, 200]:
        run('SMA_trend', f'c>sma{k}', (c > sma[k]).values, (c < sma[k]).values, mode=mode)
        run('SMA_trend_short', f'c<sma{k}', (c < sma[k]).values, (c > sma[k]).values, side=-1, mode=mode)
    for f_, s_ in [(5, 20), (10, 30), (10, 50), (20, 50), (20, 100), (50, 100), (50, 200), (100, 200)]:
        fa, sl = c.rolling(f_).mean(), c.rolling(s_).mean()
        run('SMA_cross', f'{f_}/{s_}', (fa > sl).values, (fa < sl).values, mode=mode)
    for N, M, st in itertools.product([10, 20, 40, 55, 100, 252], [5, 10, 20, 40], [0, 0.1, 0.15, 0.2]):
        if M < N:
            run('Donchian', f'N={N} M={M} stop={st}', (c >= c.rolling(N).max()).values, (c <= c.rolling(M).min()).values, stop=st, mode=mode)
    for lb in [21, 63, 126, 252]:
        m = c / c.shift(lb) - 1
        run('TSMOM', f'lb={lb}', (m > 0).values, (m < 0).values, mode=mode)

res = pd.DataFrame(rows)
out = os.path.join(LAB, 'study1')
os.makedirs(out, exist_ok=True)
mu_is = c[:H.PERIODS['IS'][1]].pct_change().mean()
mu_oos = c[H.PERIODS['OOS'][0]:].pct_change().mean()
res['is_exc'] = res.is_avg - res.side * res.is_hold.clip(lower=1) * mu_is
res['oos_exc'] = res.oos_avg - res.side * res.oos_hold.clip(lower=1) * mu_oos
res.to_csv(os.path.join(out, 'grid.csv'), index=False)
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 40)
print(f'{len(res)} configurations -> {out}/grid.csv')
bh = H.buy_and_hold(df)
for p in ('IS', 'OOS', 'REC'):
    print(f'buy & hold {p}:', {k: round(float(v), 3) for k, v in H.perf(bh, *H.PERIODS[p]).items()})
print(f'mean daily return IS {mu_is:.4%}  OOS {mu_oos:.4%}  (an average trade must beat drift x holding days)')
sel = res[(res.is_n >= 30) & (res.is_t > 2.0) & (res.is_pf > 1.3)]
print(f'\nIS-qualified (n>=30, t>2, PF>1.3): {len(sel)} of {len(res)}; of those OOS avg>0: {(sel.oos_avg > 0).mean():.2f}, '
      f'OOS t>2: {(sel.oos_t > 2).mean():.2f}, OOS excess over drift >0: {(sel.oos_exc > 0).mean():.2f}')
if len(sel):
    print(sel.groupby(['fam', 'mode']).agg(n=('params', 'size'), oos_pos=('oos_avg', lambda x: (x > 0).mean()),
                                           oos_t_med=('oos_t', 'median'), oos_avg_med=('oos_avg', 'median'),
                                           is_avg_med=('is_avg', 'median')).round(4).to_string())
cols = ['fam', 'params', 'mode', 'is_n', 'is_avg', 'is_win', 'is_sharpe', 'is_mdd', 'oos_n', 'oos_avg', 'oos_win', 'oos_sharpe', 'oos_cagr', 'oos_mdd', 'rec_sharpe', 'oos_expo']
trend = res[res.fam.isin(['SMA_trend', 'SMA_cross', 'TSMOM', 'Donchian']) & (res['mode'] == 0)].sort_values('is_sharpe', ascending=False)
print('\nTrend families, best 15 by IS Sharpe (mode 0):')
print(trend[cols].head(15).round(3).to_string())
print('\nTop 20 by IS t-stat (mode 0, IS n >= 30):')
print(res[(res['mode'] == 0) & (res.is_n >= 30)].sort_values('is_t', ascending=False)[cols + ['is_t', 'oos_t', 'oos_exc']].head(20).round(3).to_string())
# overnight / intraday decomposition and calendar
on = df.open / c.shift() - 1
intra = c / df.open - 1
print('\nOvernight vs intraday (mean daily, t-stat):')
for p in ('IS', 'OOS', 'REC'):
    lo, hi = H.PERIODS[p]
    a, b = on[lo:hi].dropna(), intra[lo:hi].dropna()
    print(f'  {p}: overnight {a.mean():+.4%} (t={a.mean() / a.std() * np.sqrt(len(a)):.1f})  intraday {b.mean():+.4%} (t={b.mean() / b.std() * np.sqrt(len(b)):.1f})')
print('Day-of-week mean return IS / OOS (treat as noise unless consistent and corrected for multiple tests):')
for p in ('IS', 'OOS'):
    x = c.pct_change()[H.PERIODS[p][0]:H.PERIODS[p][1]]
    print(f'  {p}:', x.groupby(x.index.dayofweek).mean().round(4).to_dict())
