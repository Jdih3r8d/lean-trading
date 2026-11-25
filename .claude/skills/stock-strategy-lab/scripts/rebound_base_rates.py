"""Tasas base del modo rebote: con qué frecuencia rebotaron en el pasado las acciones grandes tras caídas fuertes.

usage: python3 rebound_base_rates.py tickers.txt [--since 2005-01-01] [--out references/rebound_base_rates.md]

Para cada ticker (uno por línea; p. ej. los componentes actuales del S&P 500) descarga el historial diario ajustado
(espejos de rebound_screen.py), busca caídas de 5 sesiones (8%, 10%, 12%, 15%, 20% o más; eventos sin solaparse) y
mide la operación de la estrategia: comprar en la apertura siguiente y vender en la apertura 3, 5 o 10 sesiones después,
con 0,10% de costes. Calcula el % de operaciones ganadoras (el "acierto"), la media y la mediana, y lo compara con la
misma operación en un día cualquiera (la tasa de acierto "sin hacer nada especial"). Separa por los criterios del
filtro: acción por encima o por debajo de su media de 200 sesiones, mercado (SPY) por encima o por debajo de la suya, y
hundimiento previo de 3 meses. Escribe una tabla en Markdown para que el modo rebote cite el acierto histórico.

SESGO IMPORTANTE: usar los componentes ACTUALES del índice deja fuera a las empresas que se hundieron y salieron del
índice o quebraron; eso infla el acierto de comprar caídas. Las cifras son un techo optimista, no una promesa.
"""
import argparse
import concurrent.futures as cf
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rebound_screen import fetch  # noqa: E402

H = (3, 5, 10)
COST = 0.001


def stock_events(t, d, spy_above, since):
    d = d.loc[since:] if since else d
    if len(d) < 300:
        return [], []
    c, o, v = d['close'].values, d['open'].values, d['volume'].values
    sma200 = pd.Series(c).rolling(200).mean().values
    dvol = pd.Series(c * v).rolling(20).mean().shift(1).values
    n = len(c)
    ev = []
    i = 205
    while i < n - 1 - max(H):
        r5 = c[i] / c[i - 5] - 1
        if r5 <= -0.08:
            row = {'ticker': t, 'date': d.index[i], 'drop': r5, 'above200': c[i] > sma200[i],
                   'r3m': c[i] / c[i - 63] - 1, 'price': c[i], 'dvol': dvol[i],
                   'spy_above': bool(spy_above.asof(d.index[i])) if spy_above is not None else None}
            for h in H:
                row[f'r{h}'] = o[i + 1 + h] / o[i + 1] - 1 - COST
            ev.append(row)
            i += max(H) + 1
        else:
            i += 1
    # base: la misma operación empezando en días al azar (uno de cada 10 para aligerar)
    idx = np.arange(205, n - 1 - max(H), 10)
    base = [{f'r{h}': o[j + 1 + h] / o[j + 1] - 1 - COST for h in H} for j in idx]
    return ev, base


def table(df, label):
    if not len(df):
        return f'| {label} | 0 | | | | | | |'
    cells = [f'{len(df)}']
    for h in H:
        x = df[f'r{h}']
        cells.append(f'{(x > 0).mean():.0%} / {x.mean():+.1%}')
    return f"| {label} | " + ' | '.join(cells) + ' |'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tickers')
    ap.add_argument('--since', default='2005-01-01')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    tickers = [x.strip().upper() for x in open(a.tickers) if x.strip()]
    spy, _ = fetch('SPY')
    spy_above = (spy['close'] > spy['close'].rolling(200).mean()) if spy is not None else None
    events, base, missing = [], [], []
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(fetch, t): t for t in tickers}
        for f in cf.as_completed(futs):
            t = futs[f]
            d, _ = f.result()
            if d is None:
                missing.append(t)
                continue
            e, b = stock_events(t, d, spy_above, a.since)
            events += e
            base += b
    ev = pd.DataFrame(events)
    bs = pd.DataFrame(base)
    last = ev['date'].max().date() if len(ev) else None
    filt = ev[(ev.price >= 5) & (ev.dvol >= 20e6) & (ev.r3m > -0.40)]
    lines = [
        '# Tasas base del modo rebote (generado por scripts/rebound_base_rates.py)',
        '',
        f'Universo: {len(tickers) - len(missing)} acciones (componentes actuales del S&P 500), datos diarios desde {a.since} '
        f'hasta {last}. Operación: comprar en la apertura siguiente a un cierre con caída de 5 sesiones y vender en la '
        'apertura 3, 5 o 10 sesiones después, con 0,10% de costes. Cada celda: **% de operaciones ganadoras / '
        'rentabilidad media**.',
        '',
        '**Sesgo de supervivencia:** solo incluye empresas que siguen hoy en el índice; las que se hundieron y salieron no '
        'están. Por eso estas cifras son un techo optimista del acierto real. Úsalas como referencia, no como promesa.',
        '',
        f"| Situación | Operaciones | 3 sesiones | 5 sesiones | 10 sesiones |",
        '|---|---|---|---|---|',
        table(bs, 'Cualquier día (sin señal, referencia)'),
        table(ev[ev['drop'] <= -0.10], 'Caída de 5 sesiones >= 10%'),
        table(filt[filt['drop'] <= -0.10], 'Filtro del modo rebote (>=10%, precio >= 5 $, >= 20 M$/día, 3 meses > -40%)'),
        table(filt[(filt['drop'] <= -0.10) & filt.above200], '  … y por ENCIMA de su media de 200'),
        table(filt[(filt['drop'] <= -0.10) & ~filt.above200], '  … y por DEBAJO de su media de 200'),
        table(filt[(filt['drop'] <= -0.10) & (filt.spy_above == True)], '  … con el mercado (SPY) por ENCIMA de su media de 200'),  # noqa: E712
        table(filt[(filt['drop'] <= -0.10) & (filt.spy_above == False)], '  … con el mercado (SPY) por DEBAJO (corrección o pánico)'),  # noqa: E712
        table(ev[(ev['drop'] <= -0.10) & (ev.r3m <= -0.40)], 'Caída >= 10% en una acción que ya llevaba -40% o peor en 3 meses'),
    ]
    for lo, hi in ((0.08, 0.10), (0.10, 0.12), (0.12, 0.15), (0.15, 0.20), (0.20, 1.0)):
        sub = filt[(filt['drop'] <= -lo) & (filt['drop'] > -hi)]
        lab = f'Filtro con caída de {lo:.0%} a {hi:.0%}' if hi < 1 else f'Filtro con caída de {lo:.0%} o más'
        lines.append(table(sub, lab))
    lines += ['', f'Tickers sin datos: {len(missing)}.']
    txt = '\n'.join(lines) + '\n'
    print(txt)
    if a.out:
        with open(a.out, 'w') as f:
            f.write(txt)


if __name__ == '__main__':
    main()
