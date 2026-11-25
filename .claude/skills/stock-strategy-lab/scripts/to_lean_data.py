"""Convert a split-adjusted daily CSV (date,open,high,low,close,volume[,adj_factor]) to LEAN's equity format.

LEAN stores RAW (unadjusted) prices x10000 in a zip and applies splits/dividends through a factor file. Feeding LEAN
split-adjusted prices as if they were raw makes share counts and per-share fees wrong (for TSLA in 2011 the algorithm
bought 15x too many shares and fees were ~3x too high). This script undoes the split adjustment with the split list you
give, writes <root>/equity/usa/daily/<ticker>.zip, the factor file and a map file. If the CSV has an adj_factor column
(dividend-adjusted price = raw price * adj_factor, e.g. ETFs like QQQ/SPY), prices are converted back to raw and
adj_factor becomes the price factor. Volume is only split-adjusted.

usage: python3 to_lean_data.py <csv> <TICKER> <lean_data_root> [--start YYYY-MM-DD] [--splits 2020-08-31:5,2022-08-25:3]
  --splits  first session trading split-adjusted, and the ratio (5 = 5-for-1). Find them in the data: a day whose
            close is ~1/ratio of the previous close in raw data, or from the company's investor-relations page.
The data root also needs market-hours/, symbol-properties/ and alternative/interest-rate/usa/interest-rate.csv copied
from the LEAN repository's Data/ folder.
"""
import argparse
import os
import zipfile

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('ticker')
    ap.add_argument('root')
    ap.add_argument('--start', default=None)
    ap.add_argument('--splits', default='', help='comma list of YYYY-MM-DD:ratio')
    a = ap.parse_args()
    t = a.ticker.lower()
    df = pd.read_csv(a.csv, parse_dates=['date']).sort_values('date').reset_index(drop=True)
    if a.start:
        df = df[df.date >= pd.Timestamp(a.start)].reset_index(drop=True)
    splits = []
    for item in [s for s in a.splits.split(',') if s.strip()]:
        d, r = item.split(':')
        splits.append((pd.Timestamp(d), float(r)))
    mult = pd.Series(1.0, index=df.index)          # adjusted price x mult = traded price
    for d, r in splits:
        mult[df.date < d] *= r
    div = 1 / df['adj_factor'] if 'adj_factor' in df else 1.0
    raw = df.copy()
    for col in ('open', 'high', 'low', 'close'):
        raw[col] = df[col] * mult * div
    raw['volume'] = df['volume'] / mult
    lines = [f"{d:%Y%m%d} 00:00,{round(o * 10000)},{round(h * 10000)},{round(l * 10000)},{round(c * 10000)},{int(round(v))}"
             for d, o, h, l, c, v in zip(raw.date, raw.open, raw.high, raw.low, raw.close, raw.volume)]
    print(f"first raw close {raw.close.iloc[0]:.2f} on {df.date.iloc[0].date()}: compare with the real first traded price "
          "(a missing split makes early raw prices too low by the missing ratio)")
    for d, r in splits:
        hit = df.index[df.date == d]
        if not len(hit):
            print(f'WARNING: split date {d.date()} is not a session of the CSV (use the first session trading split-adjusted)')
        elif hit[0] > 0:
            print(f'  split {d.date()} {r:g}:1  raw close {raw.close[hit[0] - 1]:.2f} -> {raw.close[hit[0]]:.2f} (should drop ~{r:g}x)')
    for sub in ('market-hours', 'symbol-properties'):
        if not os.path.isdir(os.path.join(a.root, sub)):
            print(f'WARNING: {a.root}/{sub} missing: use <work>/leandata created by setup_lean.sh as root')
    usa = os.path.join(a.root, 'equity', 'usa')
    for sub in ('daily', 'factor_files', 'map_files'):
        os.makedirs(os.path.join(usa, sub), exist_ok=True)
    with zipfile.ZipFile(os.path.join(usa, 'daily', f'{t}.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'{t}.csv', '\n'.join(lines) + '\n')
    sf = pd.Series(1.0, index=df.index)
    for d, r in splits:
        sf[df.date < d] /= r
    pf = df['adj_factor'] if 'adj_factor' in df else pd.Series(1.0, index=df.index)
    rows = []
    for i in range(len(df)):
        last = i == len(df) - 1
        if i == 0 or last or pf.iloc[i] != pf.iloc[i + 1] or sf.iloc[i] != sf.iloc[i + 1]:
            if last and pf.iloc[i] == 1 and sf.iloc[i] == 1:
                continue
            rows.append((df.date.iloc[i], pf.iloc[i], sf.iloc[i], raw.close.iloc[i]))
    with open(os.path.join(usa, 'factor_files', f'{t}.csv'), 'w') as f:
        for d, p_, s_, ref in rows:
            f.write(f"{d:%Y%m%d},{float(p_)!r},{float(s_)!r},{ref:.4f}\n")   # full precision: 10 digits lost a share
        f.write("20501231,1,1,0\n")
    first = df.date.iloc[0]
    with open(os.path.join(usa, 'map_files', f'{t}.csv'), 'w') as f:
        f.write(f"{first:%Y%m%d},{t},Q\n20501231,{t},Q\n")
    print(f"{a.ticker}: {len(lines)} bars {df.date.iloc[0].date()} .. {df.date.iloc[-1].date()}, splits {a.splits or 'none'}")


if __name__ == '__main__':
    main()
