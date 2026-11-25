"""Estrategia final ("F3") y su informe, con el harness auditado.

w[t] = min(1, 0.5*A[t]*G[t] + 0.5*B[t] + 0.5*P[t]), decidido con el cierre de t y ejecutado en la apertura de t+1.
  A: SMA10 > SMA30 del cierre de TSLA.
  G: SMA10 > SMA30 del cierre de QQQ ajustado por dividendos.
  B: cierre al menos 12% por debajo del cierre de 5 sesiones antes -> peso 1 en los cierres t, t+1, t+2
     (compra en la apertura t+1, venta en la apertura t+4). Señales durante la tenencia y en el cierre de salida se ignoran.
  P: en una sesión de reacción a resultados R, si close[R]/close[R-1]-1 >= +3% -> peso 1 en los cierres R..R+9
     (compra en la apertura R+1, venta en la apertura R+11).

Uso: python3 fetch_data.py && python3 f3_strategy.py
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness as H  # noqa: E402


def fixed_hold(sig, hold, index):
    """Peso 1 en los cierres t..t+hold-1 tras cada señal; se ignoran señales durante la tenencia y en el cierre de salida."""
    w = np.zeros(len(sig))
    s = np.asarray(sig, bool)
    i = 0
    while i < len(s):
        if s[i]:
            w[i:i + hold] = 1.0
            i += hold + 1
        else:
            i += 1
    return pd.Series(w, index=index)


def reaction_sessions(extra=()):
    """Earnings reaction sessions (first session whose open reflects each release) plus any extra dates."""
    e = pd.read_csv(os.path.join(HERE, 'data', 'tsla_earnings.csv'), parse_dates=['first_trading_session_reacting'])
    return pd.DatetimeIndex(list(e.first_trading_session_reacting) + [pd.Timestamp(d) for d in extra]).unique()


def components(df, qqq_close=None, extra_reactions=()):
    """Module flags decided at each close. qqq_close: dividend-adjusted QQQ closes (default: data/qqq_adj.csv)."""
    c, idx = df['close'], df.index
    a = (c.rolling(10).mean() > c.rolling(30).mean()).astype(float)
    b = fixed_hold((c / c.shift(5) - 1 <= -0.12).fillna(False).values, 3, idx)
    reaction = pd.Series(idx.isin(reaction_sessions(extra_reactions)), index=idx)
    p = fixed_hold((reaction & (c / c.shift(1) - 1 >= 0.03)).values, 10, idx)
    q = qqq_close
    if q is None:
        q = pd.read_csv(os.path.join(HERE, 'data', 'qqq_adj.csv'), parse_dates=['date']).set_index('date')['close']
    g = (q.rolling(10).mean() > q.rolling(30).mean()).reindex(idx).astype(float)
    return {'A': a, 'G': g, 'B': b, 'P': p}


def f3_weights(df, qqq_close=None, extra_reactions=()):
    m = components(df, qqq_close, extra_reactions)
    return np.minimum(1.0, 0.5 * m['A'] * m['G'] + 0.5 * m['B'] + 0.5 * m['P'])


def main():
    pd.set_option('display.width', 200)
    df = H.load_tsla()
    m = components(df)
    w = f3_weights(df)
    ref = H.ref_weights(df)['AB_50_50']
    print('Sharpe / CAGR / MDD por periodo (5 pb por lado, ejecución en la apertura siguiente)')
    rows = {}
    for name, x in (('F3', w), ('Referencia A+B', ref)):
        r = H.run_weights(df, x)
        for p, (lo, hi) in H.PERIODS.items():
            rows[(name, p)] = H.perf(r, lo, hi)
    bh = H.buy_and_hold(df)
    for p, (lo, hi) in H.PERIODS.items():
        rows[('Buy&Hold', p)] = H.perf(bh, lo, hi)
    print(pd.DataFrame(rows).T[['cagr', 'sharpe', 'mdd']].unstack().round(3).to_string())
    print('\nF3 con 15 pb por lado:', {p: round(H.perf(H.run_weights(df, w, H.COST_STRESS), *H.PERIODS[p])['sharpe'], 3)
                                       for p in ('OOS', 'ALL')})
    print('\nOperaciones por módulo (cada una por unidad de capital asignado al módulo, neta de costos)')
    out = []
    for name, x in (('A*G tendencia', m['A'] * m['G']), ('B capitulación', m['B']), ('P resultados', m['P']), ('F3 combinado', w)):
        t = H.trades_from_weights(df, x)
        t.insert(0, 'modulo', name)
        out.append(t)
        for p in ('ALL', 'IS', 'OOS', 'REC'):
            s = H.trade_stats(t, *H.PERIODS[p])
            print(f"  {name:16s} {p:4s} n={s['n']:3d} media={s['avg']:+.2%} mediana={s['med']:+.2%} "
                  f"ganadoras={s['win']:.0%} ganancia media={s['avg_win']:+.2%} pérdida media={s['avg_loss']:+.2%} "
                  f"sesiones={s['days']:.1f}")
    os.makedirs(os.path.join(HERE, 'results'), exist_ok=True)
    pd.concat(out).to_csv(os.path.join(HERE, 'results', 'f3_trades.csv'), index=False)
    last = df.index[-1]
    print(f"\nEstado al cierre del {last.date()}: A={m['A'].iloc[-1]:.0f} G={m['G'].iloc[-1]:.0f} "
          f"B={m['B'].iloc[-1]:.0f} P={m['P'].iloc[-1]:.0f} -> peso objetivo {w.iloc[-1]:.2f}")


if __name__ == '__main__':
    main()
