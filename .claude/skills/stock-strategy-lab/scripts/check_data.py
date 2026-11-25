"""Sanity checks for a lab's daily OHLCV file, plus optional cross-source comparison.

usage: python3 check_data.py <lab_dir> [other_source.csv ...]

Checks main.csv for: duplicated/unsorted dates, NaN, non-positive prices, high<low, open/close outside [low,high],
weekend rows, zero volume, gaps > 5 calendar days, the largest daily moves (unadjusted split jumps show up here as
-50%/-67%/-80% days), and STALE rows whose open/high/low equal the previous row's (a Yahoo artefact: TSLA 2018-03-13
had the previous day's O/H/L). Each extra CSV (columns date,open,high,low,close[,volume], any case) is compared on the
overlap: share of days where O/H/L/C differ by more than 0.5%. Only trust a repair when two INDEPENDENT sources agree
(mirrors of the same Yahoo feed are not independent).
Sources adjusted on another basis (a snapshot taken before a later split, dividend-adjusted OHLC) fail the level check
on every row: read the scale-free lines (returns and open/high/low-to-close ratios) instead.
It also fills config.json is_start with the first date of main.csv if it is still the placeholder, and warns if the IS
or OOS period is too short or IS is far from ~half of the history.
"""
import json
import os
import sys

import pandas as pd


def load(path):
    d = pd.read_csv(path)
    d.columns = [c.strip().lower().split('. ', 1)[-1] for c in d.columns]   # also strips Alpha Vantage '1. open'
    dcol = next((c for c in d.columns if c in ('date', 'datetime', 'timestamp', 'time', 'dt')), d.columns[0])
    d[dcol] = pd.to_datetime(d[dcol], format='mixed', utc=True).dt.tz_localize(None).dt.normalize()
    d = d.rename(columns={dcol: 'date'}).set_index('date').sort_index()
    return d[~d.index.duplicated()]


def main(lab, others):
    path = os.path.join(lab, 'data', 'main.csv')
    raw = pd.read_csv(path)
    df = load(path)
    print(f'{path}: {len(df)} rows {df.index[0].date()} .. {df.index[-1].date()}')
    problems = []
    if raw.iloc[:, 0].duplicated().any():
        problems.append('duplicated dates')
    if not df.index.is_monotonic_increasing:
        problems.append('unsorted dates')
    o, h, l, c = df.open, df.high, df.low, df.close
    checks = {
        'NaN values': df[['open', 'high', 'low', 'close']].isna().any(axis=1),
        'non-positive prices': (df[['open', 'high', 'low', 'close']] <= 0).any(axis=1),
        'high < low': h < l,
        'open/close outside [low, high]': (o > h + 1e-9) | (o < l - 1e-9) | (c > h + 1e-9) | (c < l - 1e-9),
        'weekend rows': pd.Series(df.index.dayofweek >= 5, index=df.index),
        'zero volume': (df.get('volume', pd.Series(1, index=df.index)) == 0),
        'stale O/H/L (equal to previous row)': (o == o.shift()) & (h == h.shift()) & (l == l.shift()),
    }
    for name, mask in checks.items():
        n = int(mask.sum())
        if n:
            problems.append(f'{name}: {n} rows, e.g. {[d.date().isoformat() for d in df.index[mask][:5]]}')
    gaps = df.index.to_series().diff().dt.days
    if (gaps > 5).any():
        problems.append(f'calendar gaps > 5 days: {[(d.date().isoformat(), int(g)) for d, g in gaps[gaps > 5].items()][:5]}')
    r = c.pct_change()
    print('largest |daily return| (check for unadjusted splits):')
    for d, v in r.abs().nlargest(6).items():
        print(f'   {d.date()} {r[d]:+.1%}')
    print('PROBLEMS:' if problems else 'no structural problems found')
    for p in problems:
        print('  -', p)
    for other in others:
        x = load(other)
        ix = df.index.intersection(x.index)
        print(f'vs {other}: overlap {len(ix)} days')
        for col in ('open', 'high', 'low', 'close'):
            if col in x:
                diff = (df.loc[ix, col] / x.loc[ix, col] - 1).abs()
                bad = diff[diff > 0.005]
                print(f'   {col}: max rel diff {diff.max():.4%}, days > 0.5%: {len(bad)} {[d.date().isoformat() for d in bad.index[:6]]}')
        a_, b_ = df.loc[ix], x.loc[ix]
        if 'close' in b_:
            ratio = b_.close / a_.close
            print(f'   close ratio other/main: first {ratio.iloc[0]:.4f} last {ratio.iloc[-1]:.4f} '
                  '(a constant or stepped ratio means only the adjustment basis differs: use the scale-free lines)')
            dr = (a_.close.pct_change() - b_.close.pct_change()).abs()
            print(f'   scale-free: close-to-close return diff > 0.5pp: {int((dr > 0.005).sum())} {[d.date().isoformat() for d in dr[dr > 0.005].index[:6]]}')
            for col in ('open', 'high', 'low'):
                if col in b_:
                    q = ((a_[col] / a_.close) / (b_[col] / b_.close) - 1).abs()
                    print(f'   scale-free: {col}/close diff > 0.5%: {int((q > 0.005).sum())} {[d.date().isoformat() for d in q[q > 0.005].index[:6]]}')
    cfg_path = os.path.join(lab, 'config.json')
    if os.path.exists(cfg_path):
        cfg = json.load(open(cfg_path))
        if cfg.get('is_start', '1990-01-01') == '1990-01-01':
            cfg['is_start'] = df.index[0].date().isoformat()
            json.dump(cfg, open(cfg_path, 'w'), indent=1)
            print('config.json is_start ->', cfg['is_start'])
        s, e = pd.Timestamp(cfg['is_start']), pd.Timestamp(cfg['is_end'])
        span = df.index[-1] - df.index[0]
        frac = (e - df.index[0]) / span if span.days > 0 else 0
        mid = (df.index[0] + span / 2).year
        print(f"IS {cfg['is_start']}..{cfg['is_end']} covers {frac:.0%} of the history (target ~50%; to change: "
              f"new_lab.sh <T> <lab> {mid}-12-31)")
        if (e - s).days < 5 * 365:
            print('WARNING: IS is shorter than 5 years or empty: fix is_end in config.json before any research')
        if (df.index[-1] - pd.Timestamp(cfg['oos_start'])).days < 3 * 365:
            print('WARNING: OOS is shorter than 3 years')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])
