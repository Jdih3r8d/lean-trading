import numpy as np, pandas as pd
from numba import njit

COST = 0.0005  # per side (commission + slippage), 0.10% round trip

def load(path):
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    return df

@njit(cache=True)
def sim(O, H, L, C, entry, exitsig, side, max_hold, stop, tp, mode, cost):
    """mode 0: signal at close t -> fill at open t+1 ; mode 1: fill at close t (MOC).
    side +1 long, -1 short. stop/tp as fraction (0 = off). Returns trades array and daily returns."""
    n = len(C)
    daily = np.zeros(n)
    pos = np.zeros(n)
    tr = np.zeros((n, 4))  # entry_idx, exit_idx, ret, hold
    k = 0
    t = 0
    while t < n - 1:
        if not entry[t]:
            t += 1
            continue
        if mode == 0:
            e = t + 1; px = O[e]; mark = px
        else:
            e = t; px = C[t]; mark = px
        sp = px * (1 - side * stop) if stop > 0 else 0.0
        tpp = px * (1 + side * tp) if tp > 0 else 0.0
        daily[e] -= cost
        d = e
        exited = False
        xpx = 0.0
        xi = 0
        start = e if mode == 0 else e + 1
        d = start
        held = 0
        while d < n:
            # gap through the take-profit at the open fills at the open (checked before intraday stops)
            if tp > 0:
                if side == 1 and O[d] >= tpp:
                    xpx = O[d]; exited = True
                elif side == -1 and O[d] <= tpp:
                    xpx = O[d]; exited = True
            # intraday stop / tp checks
            if (not exited) and stop > 0:
                if side == 1:
                    if O[d] <= sp:
                        xpx = O[d]; exited = True
                    elif L[d] <= sp:
                        xpx = sp; exited = True
                else:
                    if O[d] >= sp:
                        xpx = O[d]; exited = True
                    elif H[d] >= sp:
                        xpx = sp; exited = True
            if (not exited) and tp > 0:
                if side == 1:
                    if O[d] >= tpp:
                        xpx = O[d]; exited = True
                    elif H[d] >= tpp:
                        xpx = tpp; exited = True
                else:
                    if O[d] <= tpp:
                        xpx = O[d]; exited = True
                    elif L[d] <= tpp:
                        xpx = tpp; exited = True
            if exited:
                daily[d] += side * (xpx / mark - 1) - cost
                pos[d] = side
                xi = d
                break
            daily[d] += side * (C[d] / mark - 1)
            pos[d] = side
            mark = C[d]
            held = d - e + (1 if mode == 0 else 0)
            if exitsig[d] or held >= max_hold:
                if mode == 0:
                    if d + 1 < n:
                        daily[d + 1] += side * (O[d + 1] / mark - 1) - cost
                        xpx = O[d + 1]; xi = d + 1
                    else:
                        xpx = C[d]; xi = d
                else:
                    daily[d] -= cost
                    xpx = C[d]; xi = d
                exited = True
                break
            d += 1
        if not exited:
            xpx = C[n - 1]; xi = n - 1
            daily[n - 1] -= cost   # mark-to-market exit cost, consistent with the trade ledger
        r = side * (xpx / px - 1) - 2 * cost
        tr[k, 0] = t; tr[k, 1] = xi; tr[k, 2] = r; tr[k, 3] = xi - e
        k += 1
        # next possible entry signal: the day of exit (mode1) or exit day (mode0 exit at open -> signal at that close)
        t = xi if mode == 0 else xi + 1
        if mode == 0 and xi == d + 1:
            t = xi
    return tr[:k], daily, pos

def stats(tr, daily, idx, lo=None, hi=None):
    """Stats over trades whose signal date in [lo,hi)."""
    dates = idx
    m = np.ones(len(tr), bool)
    dm = np.ones(len(daily), bool)
    if lo is not None:
        m &= dates[tr[:, 0].astype(int)] >= lo; dm &= dates >= lo
    if hi is not None:
        m &= dates[tr[:, 0].astype(int)] < hi; dm &= dates < hi
    r = tr[m, 2]
    d = daily[dm]
    n = len(r)
    if n == 0:
        return dict(n=0)
    eq = np.cumprod(1 + d)
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    yrs = len(d) / 252
    wins = r[r > 0].sum(); losses = -r[r < 0].sum()
    sd = r.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, avg=r.mean(), med=np.median(r), win=(r > 0).mean(),
                pf=wins / losses if losses > 0 else np.inf,
                t=r.mean() / sd * np.sqrt(n) if n > 1 and sd > 0 else np.nan,
                hold=tr[m, 3].mean(), expo=(d != 0).mean(),
                cagr=eq[-1] ** (1 / yrs) - 1, mdd=dd,
                sharpe=d.mean() / d.std() * np.sqrt(252) if d.std() > 0 else np.nan,
                tot=eq[-1] - 1)

# ---------- indicators ----------
def rsi(c, n):
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)

def atr(df, n):
    pc = df.close.shift()
    tr = pd.concat([df.high - df.low, (df.high - pc).abs(), (df.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()
