"""Modo rebote: filtra acciones que han caído mucho y ordena las que tienen más probabilidad de rebote.

usage: python3 rebound_screen.py ITEM [ITEM ...] [--after-close] [--hold 3] [--out file.json]
  ITEM = TICKER            (usa el último cierre disponible)
       | TICKER:-12.5      (variación de HOY en %, leída de la captura del bróker)
       | TICKER@41.20      (precio actual de HOY, leído de la captura)
       | TICKER:-12.5@41.20  (ambos: lo recomendable; permite detectar si los datos ya incluyen el movimiento de hoy)
  --after-close  la captura es posterior al cierre (la cifra de hoy es definitiva); si no, se trata como provisional.

Para cada ticker descarga el historial diario ajustado por splits (espejos públicos de GitHub: alm0421, con
jorgencarbajal/sp500_uptrend_scanner de respaldo) y calcula:
  caída de hoy y de 5 sesiones, rentabilidad de 3 meses, distancia a la media de 200 sesiones, caída desde el máximo de
  52 semanas, volumen medio en dólares, y la EVIDENCIA PROPIA: qué pasó en el pasado con esa misma acción tras caídas de
  5 sesiones de al menos un 10% (comprar en la apertura siguiente, vender en la apertura `hold` sesiones después, con
  0,10% de costes), comparado con cualquier periodo de `hold` sesiones (la deriva).
También mira el mercado (SPY y QQQ: tendencia 10/30 y media de 200 sesiones).

DATOS DESFASADOS: los espejos no se actualizan todos a la vez (el 25-nov-2026 unos llegaban al 24-nov y otros al
17-nov). Si a un ticker le falta la última sesión de Nueva York, el script NO pega el % de hoy sobre un cierre viejo
(daría una caída de 5 sesiones falsa): lo marca como REVISAR, con `datos_desfasados` y `sesiones_que_faltan`, y sus
cifras son solo orientativas hasta reconstruir los cierres recientes (búsqueda web). Si la captura da el precio
(TICKER@precio), lo usa como dato de hoy, pero sigue marcándolo.

Criterios (PROVISIONALES: salen del estudio de TSLA y de la literatura sobre reversión a corto plazo; aún no se han
validado en muchas acciones; ver references/rebound_mode.md):
  DESCARTAR: precio < 5 $, volumen medio < 20 M$/día, menos de 250 sesiones de historia, rentabilidad de 3 meses
             <= -40% (hundimiento prolongado), o caída de 5 sesiones < 8% (no es una caída fuerte).
  PREFERIR:  caída de 5 sesiones entre 10% y 15% (en el S&P 500 desde 2005 las de 15-20% y más de 20% rebotaron PEOR:
             51% y 47% de aciertos a 3 sesiones; ver references/rebound_base_rates.md), precio por encima (o cerca, -5%)
             de su media de 200 sesiones (59% de aciertos frente a 53% por debajo), evidencia propia positiva.
             Penalizar si está más de un 10% por debajo de su media de 200 (cuchillo cayendo).
  REVISAR:   datos desfasados (ver arriba), salvo que la descarten la liquidez o la historia corta, que no dependen
             de los últimos días.
  La noticia que causó la caída (resultados malos, guía rebajada, fraude, quiebra, ampliación de capital, rechazo
  regulatorio) NO la ve este script: hay que comprobarla para las finalistas y descartarlas si la hay.
"""
import argparse
import io
import json
import sys
import urllib.request

import numpy as np
import pandas as pd

RAW = 'https://raw.githubusercontent.com/'
MIRRORS = [RAW + 'alm0421/alm0421/HEAD/data/prices/{t}.csv',
           RAW + 'jorgencarbajal/sp500_uptrend_scanner/HEAD/scanner/data/prices/raw/{t}.csv']
COST = 0.001  # ida y vuelta
ORDER = {'CANDIDATA': 0, 'VIGILAR': 1, 'REVISAR': 2, 'DESCARTAR': 3, 'SIN DATOS': 4}


def fetch(ticker):
    for tmpl in MIRRORS:
        for t in dict.fromkeys([ticker, ticker.replace('.', '-'), ticker.replace('-', '.')]):
            try:
                with urllib.request.urlopen(tmpl.format(t=t), timeout=60) as r:
                    d = pd.read_csv(io.BytesIO(r.read()))
                d.columns = [c.lower() for c in d.columns]
                d['date'] = pd.to_datetime(d['date'].astype(str).str[:10])
                d = d.set_index('date').sort_index()
                d = d[~d.index.duplicated()][['open', 'high', 'low', 'close', 'volume']].dropna()
                if len(d):
                    return d, tmpl.split('/')[3]
            except Exception:  # noqa: BLE001
                continue
    return None, None


def parse_item(s):
    """Devuelve (ticker, {'pct': variación de hoy en %, 'price': precio de hoy}) con las claves presentes."""
    info = {}
    if '@' in s:
        s, v = s.split('@', 1)
        info['price'] = float(v.replace(',', '.').replace('$', ''))
    if ':' in s:
        s, v = s.split(':', 1)
        info['pct'] = float(v.replace(',', '.').replace('%', ''))
    return s.upper().strip(), info or None


def nyse_sessions(start, end):
    """Sesiones de la bolsa de Nueva York entre start y end (ambos incluidos), sin zona horaria."""
    try:
        import pandas_market_calendars as mcal
        s = mcal.get_calendar('NYSE').valid_days(start, end)
        return [pd.Timestamp(x).tz_localize(None).normalize() for x in s]
    except Exception:  # noqa: BLE001
        return list(pd.bdate_range(start, end))


def sessions_after(day, n):
    return nyse_sessions(day + pd.Timedelta(days=1), day + pd.Timedelta(days=30))[:n]


def session_context(today):
    """(hoy es sesión, última sesión que los datos YA deberían tener). Si hoy hay sesión, la anterior; si no
    (fin de semana o festivo), la última sesión hasta hoy."""
    recent = nyse_sessions(today - pd.Timedelta(days=20), today)
    is_session = bool(recent) and recent[-1] == today
    if is_session:
        prev = recent[-2] if len(recent) > 1 else today - pd.offsets.BDay(1)
    else:
        prev = recent[-1] if recent else today - pd.offsets.BDay(1)
    return is_session, pd.Timestamp(prev).normalize()


def missing_sessions(last, prev):
    """Sesiones posteriores a `last` y hasta `prev` que faltan en los datos."""
    if last >= prev:
        return 0
    return len(nyse_sessions(last + pd.Timedelta(days=1), prev))


def own_evidence(d, hold, thr=0.10):
    """Caídas pasadas de 5 sesiones >= thr en la propia acción: rentabilidad de comprar en la apertura siguiente y
    vender en la apertura `hold` sesiones después (eventos sin solaparse, excluyendo las últimas 10 sesiones)."""
    c, o = d['close'].values, d['open'].values
    n = len(c)
    out = []
    i = 5
    while i < n - hold - 2 - 10:
        if c[i] / c[i - 5] - 1 <= -thr:
            out.append(o[i + 1 + hold] / o[i + 1] - 1 - COST)
            i += hold + 1
        else:
            i += 1
    base = (o[1 + hold:n] / o[1:n - hold] - 1).mean() - COST if n > hold + 2 else np.nan
    x = np.array(out)
    return {'n': len(x), 'avg': float(x.mean()) if len(x) else None,
            'win': float((x > 0).mean()) if len(x) else None, 'drift': float(base)}


def market(prev):
    res = {}
    for t in ('SPY', 'QQQ'):
        d, _ = fetch(t)
        if d is None:
            continue
        c = d['close']
        res[t] = {'trend_10_30': bool(c.rolling(10).mean().iloc[-1] > c.rolling(30).mean().iloc[-1]),
                  'above_sma200': bool(c.iloc[-1] > c.rolling(200).mean().iloc[-1]),
                  'last': d.index[-1].date().isoformat(),
                  'desfasado': bool(d.index[-1] < prev)}
    panic = bool(res) and all((not v['trend_10_30']) and (not v['above_sma200']) for v in res.values())
    return res, panic


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('items', nargs='+')
    ap.add_argument('--after-close', action='store_true')
    ap.add_argument('--hold', type=int, default=3)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    today = pd.Timestamp.now(tz='America/New_York').tz_localize(None).normalize()
    today_is_session, prev_session = session_context(today)
    rows = []
    for item in a.items:
        t, today_info = parse_item(item)
        d, src = fetch(t)
        if d is None:
            rows.append({'ticker': t, 'decision': 'SIN DATOS',
                         'motivo': 'no encontré su historial (¿no es de EE. UU.? Las europeas no están en los espejos: '
                                   'analízala con búsquedas web en la variante profunda)'})
            continue
        d = d.copy()
        last_date = d.index[-1]
        n_missing = missing_sessions(last_date, prev_session)
        stale = n_missing > 0
        provisional = False
        notas = []
        appended = False
        if stale:
            faltan = 'falta 1 sesión' if n_missing == 1 else f'faltan {n_missing} sesiones'
            notas.append(f'DATOS DESFASADOS: el último dato es del {last_date.date()} y {faltan}; '
                         'reconstruye los cierres recientes antes de fiarte de la caída de 5 sesiones')
        if today_info and today_info.get('pct') == 0.0:
            notas.append('0,00% exacto en la captura: comprueba que no sea un fallo de la línea del bróker '
                         '(p. ej. que cotice en otra bolsa)')
        if today_info and last_date < today and today_is_session:
            last = d['close'].iloc[-1]
            pct, price = today_info.get('pct'), today_info.get('price')
            if stale:
                if price is not None:
                    # el precio de la captura es real, pero entre medias faltan sesiones: se usa y se marca
                    d.loc[today] = [price, price, price, price, np.nan]
                    appended = True
                    provisional = not a.after_close
                # con solo el % no se pega nada: el % es frente al cierre de AYER, no frente al último dato viejo
            elif price is not None and abs(price / last - 1) < 0.005 and (pct is None or abs(pct) >= 1.0):
                # el precio de la captura ya es el último cierre de los datos: el movimiento ya está incluido
                notas.append(f'los datos ya incluyen el movimiento de la captura (último cierre {last_date.date()})')
            else:
                px = price if price is not None else last * (1 + pct / 100)
                if price is not None and pct is not None and abs(price / last - 1 - pct / 100) > 0.02:
                    notas.append('el precio y el % de la captura no cuadran con el último cierre: revisa la captura')
                d.loc[today] = [px, px, px, px, np.nan]
                appended = True
                provisional = not a.after_close
        elif today_info and not today_is_session and not stale:
            notas.append(f'hoy no hay sesión en Nueva York: los datos ya incluyen el último movimiento '
                         f'(último cierre {last_date.date()})')
        c = d['close']
        if len(c) < 250:
            rows.append({'ticker': t, 'decision': 'DESCARTAR', 'motivo': f'solo {len(c)} sesiones de historia'})
            continue
        px = float(c.iloc[-1])
        drop1 = float(c.iloc[-1] / c.iloc[-2] - 1)
        if stale and today_info and today_info.get('pct') is not None:
            drop1 = today_info['pct'] / 100     # con datos viejos, el % de la captura es el único dato fiable de hoy
        drop5 = float(c.iloc[-1] / c.iloc[-6] - 1)
        r3m = float(c.iloc[-1] / c.iloc[-64] - 1)
        sma200 = float(c.rolling(200).mean().iloc[-1])
        dist200 = px / sma200 - 1
        dd52 = float(px / c.iloc[-252:].max() - 1)
        dvol = float((d['close'] * d['volume']).iloc[-21:-1].mean())
        ev = own_evidence(d.iloc[:-1] if appended else d, a.hold)
        duros, blandos = [], []          # duros: no dependen de los últimos días; blandos: sí
        if not np.isnan(dvol) and dvol < 20e6:
            duros.append(f'poco líquida ({dvol / 1e6:.0f} M$/día)')
        if px < 5:
            blandos.append('precio < 5 $')
        if r3m <= -0.40:
            blandos.append(f'lleva meses hundiéndose ({r3m:.0%} en 3 meses)')
        if drop5 > 0:
            blandos.append(f'no ha caído: sube {drop5:.1%} en 5 sesiones (no es un rebote; ver la lente de subidas)')
        elif drop5 > -0.08:
            blandos.append(f'la caída de 5 sesiones es pequeña ({drop5:.1%})')
        score = 0.0
        if duros:
            decision = 'DESCARTAR'
        else:
            dd = -drop5                                              # caída: mejor entre 10% y 15%
            score += 1.5 if 0.10 <= dd < 0.15 else (0.5 if (0.08 <= dd < 0.10 or 0.15 <= dd < 0.20) else 0.0)
            score += 1.0 if dist200 >= -0.05 else (-1.0 if dist200 < -0.10 else 0.0)
            if ev['n'] >= 5 and ev['avg'] is not None:
                score += 1.0 if ev['avg'] > ev['drift'] and ev['win'] >= 0.55 else (-1.0 if ev['avg'] <= 0 else 0.0)
            if stale:
                decision = 'REVISAR'
                if blandos:
                    blandos = [f'(orientativo, con datos viejos) {m}' for m in blandos]
            elif blandos:
                decision = 'DESCARTAR'
            else:
                decision = 'CANDIDATA' if dist200 >= -0.10 and drop5 <= -0.10 else 'VIGILAR'
            if decision != 'DESCARTAR' and dist200 < -0.10:
                blandos.append(f'{dist200:.0%} por debajo de su media de 200 sesiones (tendencia de fondo bajista)')
        if decision == 'DESCARTAR':
            score = 0.0
        rows.append({'ticker': t, 'decision': decision, 'score': round(score, 2), 'precio': round(px, 2),
                     'caida_hoy': round(drop1, 4), 'caida_5s': round(drop5, 4), 'rent_3m': round(r3m, 4),
                     'dist_sma200': round(dist200, 4), 'desde_max_52s': round(dd52, 4),
                     'vol_medio_musd': round(dvol / 1e6, 1) if not np.isnan(dvol) else None,
                     'evidencia_propia': ev, 'dato_hoy_provisional': provisional,
                     'datos_desfasados': stale, 'sesiones_que_faltan': n_missing, 'fuente': src,
                     'ultimo_dato': d.index[-1].date().isoformat(), 'motivo': '; '.join(notas + duros + blandos)})
    mk, panic = market(prev_session)
    base_day = today if today_is_session else prev_session
    ses = sessions_after(base_day, a.hold + 1)
    plan = {'compra': ses[0].date().isoformat(), 'venta': ses[a.hold].date().isoformat()}
    rows.sort(key=lambda r: (ORDER[r['decision']], -r.get('score', 0)))
    out = {'mercado': mk, 'mercado_en_panico': panic, 'plan_si_se_compra_al_cierre_de_hoy': plan,
           'ultima_sesion_esperada_en_los_datos': prev_session.date().isoformat(),
           'criterios': 'PROVISIONALES (no validados aún en muchas acciones)', 'acciones': rows}
    print(f"Mercado: {json.dumps(mk)}  pánico={panic}")
    print(f"Los datos deberían llegar al menos al {prev_session.date()} (sesión anterior de Nueva York).")
    print(f"Si la señal se confirma al cierre de {base_day.date()}: compra en la apertura del {plan['compra']}, "
          f"venta en la apertura del {plan['venta']} ({a.hold} sesiones).")
    print(f"{'ticker':7s} {'decisión':10s} {'score':>5s} {'precio':>9s} {'hoy':>7s} {'5 ses':>7s} {'3 meses':>8s} "
          f"{'vs m200':>8s} {'M$/día':>8s}  evidencia propia (n, media, % ganadoras vs deriva)  motivo")
    for r in rows:
        if 'precio' not in r:
            print(f"{r['ticker']:7s} {r['decision']:10s}  {r['motivo']}")
            continue
        ev = r['evidencia_propia']
        evs = (f"n={ev['n']} media={ev['avg']:+.1%} gana={ev['win']:.0%} deriva={ev['drift']:+.1%}"
               if ev['n'] else 'sin caídas parecidas')
        print(f"{r['ticker']:7s} {r['decision']:10s} {r['score']:5.1f} {r['precio']:9.2f} {r['caida_hoy']:7.1%} "
              f"{r['caida_5s']:7.1%} {r['rent_3m']:8.1%} {r['dist_sma200']:8.1%} {r['vol_medio_musd'] or 0:8.0f}  "
              f"{evs}  {r['motivo']}{' [dato de hoy provisional]' if r['dato_hoy_provisional'] else ''}")
    if a.out:
        with open(a.out, 'w') as f:
            json.dump(out, f, indent=1, ensure_ascii=False, default=str)


if __name__ == '__main__':
    main()
