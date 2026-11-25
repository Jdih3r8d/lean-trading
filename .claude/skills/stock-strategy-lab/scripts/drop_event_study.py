"""Estudio de eventos: qué pasó históricamente con una acción después de caídas parecidas a la de hoy.

usage: python3 drop_event_study.py TICKER [--drop 0.10] [--lookback 5] [--horizons 1,3,5,10,20] [--asof AAAA-MM-DD]
                                   [--peers T1,T2,...] [--last 20]

Eventos: cierres en los que la acción cae al menos `drop` en `lookback` sesiones (sin solaparse: tras un evento se salta
el horizonte más largo). Para cada evento se mide la rentabilidad de comprar en la APERTURA siguiente y vender en la
apertura h sesiones después (h en `horizons`), con 0,10% de costes, y se compara con la de cualquier día (la deriva).
Se desglosa por régimen de mercado (SPY por encima o por debajo de su media de 200 sesiones), por si la acción estaba
por encima o por debajo de su propia media de 200, y por tamaño de la caída. Lista los últimos eventos con fecha para
poder buscar qué los causó (resultados, noticias) y cómo acabaron. Con --peers repite el resumen para acciones del mismo
sector. Usa los mismos espejos de datos que rebound_screen.py.

Lectura honesta: son pocas observaciones de UNA acción; trátalo como evidencia orientativa, no como probabilidad
exacta. Desconfía de medias con n < 10 y mira siempre la mediana y el % de ganadoras junto con la media.
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebound_screen import fetch  # noqa: E402

COST = 0.001


def events(d, drop, lookback, horizons, spy_c=None):
    c, o = d['close'].values, d['open'].values
    n = len(c)
    sma200 = d['close'].rolling(200).mean().values
    hmax = max(horizons)
    rows = []
    i = lookback
    while i < n - 1:
        r = c[i] / c[i - lookback] - 1
        if r <= -drop:
            row = {'date': d.index[i], 'drop': r, 'above_own_sma200': bool(c[i] > sma200[i]) if not np.isnan(sma200[i]) else None}
            if spy_c is not None:
                s = spy_c.loc[:d.index[i]]
                row['spy_above_sma200'] = bool(s.iloc[-1] > s.rolling(200).mean().iloc[-1]) if len(s) > 200 else None
            for h in horizons:
                row[f'r{h}'] = (o[i + 1 + h] / o[i + 1] - 1 - COST) if i + 1 + h < n else np.nan
            rows.append(row)
            i += hmax + 1
        else:
            i += 1
    return pd.DataFrame(rows)


def summarize(ev, d, horizons, label):
    o = d['open'].values
    base = {h: np.nanmean(o[1 + h:] / o[1:len(o) - h] - 1) - COST for h in horizons}
    print(f'\n{label}: {len(ev)} eventos')
    if not len(ev):
        return
    print(f"{'horizonte':>10s} {'n':>4s} {'media':>8s} {'mediana':>8s} {'ganadoras':>9s} {'deriva':>8s}")
    for h in horizons:
        x = ev[f'r{h}'].dropna()
        if len(x):
            print(f'{h:>7d} s. {len(x):4d} {x.mean():8.2%} {x.median():8.2%} {(x > 0).mean():9.0%} {base[h]:8.2%}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('ticker')
    ap.add_argument('--drop', type=float, default=0.10)
    ap.add_argument('--lookback', type=int, default=5)
    ap.add_argument('--horizons', default='1,3,5,10,20')
    ap.add_argument('--asof', default=None)
    ap.add_argument('--peers', default='')
    ap.add_argument('--last', type=int, default=20)
    a = ap.parse_args()
    hz = [int(h) for h in a.horizons.split(',')]
    spy, _ = fetch('SPY')
    spy_c = spy['close'] if spy is not None else None
    d, src = fetch(a.ticker.upper())
    if d is None:
        raise SystemExit(f'sin datos para {a.ticker}')
    if a.asof:
        d = d.loc[:a.asof]
    print(f'{a.ticker.upper()}: {len(d)} sesiones {d.index[0].date()}..{d.index[-1].date()} (fuente {src}); '
          f'evento = caída >= {a.drop:.0%} en {a.lookback} sesiones; compra en la apertura siguiente')
    ev = events(d, a.drop, a.lookback, hz, spy_c)
    summarize(ev, d, hz, 'Todos los eventos')
    if len(ev):
        if 'spy_above_sma200' in ev:
            for v, lab in ((True, 'Mercado (SPY) por ENCIMA de su media de 200'), (False, 'Mercado (SPY) por DEBAJO de su media de 200')):
                summarize(ev[ev.spy_above_sma200 == v], d, hz, lab)
        for v, lab in ((True, 'Acción por ENCIMA de su propia media de 200'), (False, 'Acción por DEBAJO de su propia media de 200')):
            summarize(ev[ev.above_own_sma200 == v], d, hz, lab)
        big = ev[ev['drop'] <= -max(0.15, a.drop + 0.05)]
        summarize(big, d, hz, f'Caídas de {max(0.15, a.drop + 0.05):.0%} o más')
        cols = ['date', 'drop'] + [f'r{h}' for h in hz] + ['above_own_sma200'] + (['spy_above_sma200'] if 'spy_above_sma200' in ev else [])
        print(f'\nÚltimos {a.last} eventos (busca qué los causó para compararlos con el de hoy):')
        t = ev[cols].tail(a.last).copy()
        t['date'] = t['date'].dt.date
        for col in ['drop'] + [f'r{h}' for h in hz]:
            t[col] = t[col].map(lambda v: '' if pd.isna(v) else f'{v:+.1%}')
        print(t.to_string(index=False))
    for p in [x.strip().upper() for x in a.peers.split(',') if x.strip()]:
        dp, _ = fetch(p)
        if dp is None:
            print(f'\n{p}: sin datos')
            continue
        if a.asof:
            dp = dp.loc[:a.asof]
        summarize(events(dp, a.drop, a.lookback, hz), dp, hz, f'Comparable {p}')


if __name__ == '__main__':
    main()
