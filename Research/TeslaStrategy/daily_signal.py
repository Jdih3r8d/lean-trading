"""Aviso diario de la estrategia de Tesla (F3), en español y en lenguaje sencillo.

Descarga los cierres más recientes de TSLA y QQQ, recalcula la estrategia exactamente como la investigación
(f3_strategy.py) y escribe qué hacer en la próxima apertura de Nueva York: comprar, vender, mantener o nada, con qué
parte del dinero, la fecha de venta prevista y los precios que activarían cada regla en el siguiente cierre.

Uso:
  python3 daily_signal.py [--reaction AAAA-MM-DD ...] [--next-earnings AAAA-MM-DD] [--asof AAAA-MM-DD]
    --reaction       sesión de reacción a unos resultados que aún no está en data/tsla_earnings.csv (la primera sesión
                     cuya apertura refleja el anuncio: el día siguiente si Tesla publica tras el cierre)
    --next-earnings  sesión de reacción de los PRÓXIMOS resultados, solo para avisar con antelación
    --asof           calcula la señal como si el último dato fuera esa fecha (para pruebas)
Si la lista de resultados lleva más de 60 días sin fechas nuevas y no se pasa ninguna, imprime COMPROBAR_RESULTADOS.
"""
import argparse
import io
import os
import sys
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import f3_strategy as F  # noqa: E402

RAW = 'https://raw.githubusercontent.com/'
SOURCES = {   # principal (se actualiza de madrugada) y alternativa
    'TSLA': [RAW + 'alm0421/alm0421/HEAD/data/prices/TSLA.csv', RAW + 'yennanliu/finance_data/HEAD/data/prices/tsla.csv'],
    'QQQ': [RAW + 'alm0421/alm0421/HEAD/data/prices/QQQ.csv', RAW + 'yennanliu/finance_data/HEAD/data/prices/qqq.csv'],
}
DIAS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom']
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


def fecha(d):
    d = pd.Timestamp(d)
    return f'{DIAS[d.dayofweek]} {d.day}-{MESES[d.month - 1]}-{d.year}'


def dinero(x):
    return f'{x:,.2f} $'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fetch(symbol):
    """Devuelve (DataFrame diario, fuente) con la fuente cuyo último dato sea más reciente."""
    best = None
    for url in SOURCES[symbol]:
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = pd.read_csv(io.BytesIO(r.read()))
            d['date'] = pd.to_datetime(d['date'])
            d = d.set_index('date').sort_index()
            d = d[~d.index.duplicated()]
            if best is None or d.index[-1] > best[0].index[-1]:
                best = (d, url.split('/')[3])
        except Exception as exc:  # noqa: BLE001
            print(f'(aviso: no se pudo leer {url}: {exc})', file=sys.stderr)
    if best is None:
        raise SystemExit(f'ERROR_DATOS: no se pudo descargar {symbol}')
    return best


def qqq_adjusted(q):
    """Cierres de QQQ ajustados por dividendos (igual que fetch_data.py)."""
    if 'dividend' not in q:
        return q['close']
    div = q['dividend'].fillna(0.0)
    f = (1 - div / q['close'].shift(1)).fillna(1.0)
    adj = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    return q['close'] * adj


def calendario(desde, n=40):
    """Próximas sesiones de la bolsa de Nueva York a partir de 'desde' (exclusive)."""
    try:
        import pandas_market_calendars as mcal
        s = mcal.get_calendar('NYSE').valid_days(desde + pd.Timedelta(days=1), desde + pd.Timedelta(days=90))
        return [pd.Timestamp(d).tz_localize(None).normalize() for d in s][:n], True
    except Exception:  # noqa: BLE001
        d = pd.bdate_range(desde + pd.Timedelta(days=1), periods=n)
        return list(d), False


def umbral_cruce(closes):
    """Precio del próximo cierre que iguala la media de 10 y la de 30 (por encima: la de 10 queda arriba)."""
    x = closes.values
    return 15 * (x[-29:].sum() / 30 - x[-9:].sum() / 10)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reaction', action='append', default=[])
    ap.add_argument('--next-earnings', default=None)
    ap.add_argument('--asof', default=None)
    a = ap.parse_args()

    t, src_t = fetch('TSLA')
    q, src_q = fetch('QQQ')
    df = t[['open', 'high', 'low', 'close']].copy()
    qc = qqq_adjusted(q)
    if a.asof:
        df = df.loc[:a.asof]
        qc = qc.loc[:a.asof]
    last = min(df.index[-1], qc.index[-1])
    df = df.loc[:last]
    qc = qc.loc[:last]
    extra = list(a.reaction)
    m = F.components(df, qc, extra)
    w = np.minimum(1.0, 0.5 * m['A'] * m['G'] + 0.5 * m['B'] + 0.5 * m['P'])
    L = len(df) - 1
    c = df['close']
    target, held = float(w.iloc[L]), float(w.iloc[L - 1])
    ag = m['A'] * m['G']
    sesiones, oficial = calendario(last)
    prox = sesiones[0]

    def sesion(k):          # fecha de la sesión que está k sesiones después de la última con datos
        if k <= 0:
            return df.index[L + k]
        return sesiones[k - 1]

    def inicio_tramo(s):     # índice de la señal que abrió el tramo activo de una regla de duración fija
        i = L
        while i > 0 and s.iloc[i - 1] == 1:
            i -= 1
        return i

    lineas = []
    lineas.append(f'TESLA · estrategia de 3 reglas · datos hasta el cierre del {fecha(last)} '
                  f'(TSLA {dinero(c.iloc[L])}, fuente {src_t})')
    hoy_ny = pd.Timestamp.now(tz='America/New_York').tz_localize(None).normalize()
    if not a.asof and last < hoy_ny - pd.Timedelta(days=4):
        lineas.append(f'⚠️ Los datos parecen antiguos (último cierre {fecha(last)}): comprueba la señal a mano.')
    cuando = f'en la apertura del {fecha(prox)} (9:30 de Nueva York; 15:30 en España peninsular)'
    parte = {0.5: 'la MITAD del dinero de la estrategia', 1.0: 'TODO el dinero de la estrategia'}

    # ---- acción
    motivos = []
    if ag.iloc[L] != ag.iloc[L - 1]:
        motivos.append('regla 1 (tendencia) ' + ('se ENCIENDE' if ag.iloc[L] else 'se APAGA'))
    if m['B'].iloc[L] != m['B'].iloc[L - 1]:
        motivos.append('regla 2 (caída fuerte) ' + ('se ACTIVA' if m['B'].iloc[L] else 'TERMINA'))
    if m['P'].iloc[L] != m['P'].iloc[L - 1]:
        motivos.append('regla 3 (resultados) ' + ('se ACTIVA' if m['P'].iloc[L] else 'TERMINA'))
    if target > held:
        accion = 'COMPRAR'
        extra_txt = 'compra ' + ('la mitad del dinero' if target - held == 0.5 else 'todo el dinero') + \
            (' (ya tenías la otra mitad: quedas con TODO invertido)' if held == 0.5 else '')
        lineas.append(f'🔔 ACCIÓN: COMPRAR {cuando}: orden de compra "a mercado en la apertura"; {extra_txt}.')
    elif target < held:
        accion = 'VENDER'
        if target == 0:
            lineas.append(f'🔔 ACCIÓN: VENDER TODO {cuando}: orden de venta "a mercado en la apertura". Quedas en efectivo.')
        else:
            lineas.append(f'🔔 ACCIÓN: VENDER LA MITAD {cuando} (orden "a mercado en la apertura"); te quedas con '
                          f'{parte.get(target, f"{target:.0%}")}.')
    elif target > 0:
        accion = 'MANTENER'
        lineas.append(f'✅ Sin cambios: MANTÉN la posición ({parte.get(target, f"{target:.0%}")} invertido).')
    else:
        accion = 'NADA'
        lineas.append('✅ Sin cambios: sigue en EFECTIVO, no hagas nada.')
    if motivos:
        lineas.append('   Motivo: ' + '; '.join(motivos) + '.')

    # ---- ventas previstas de las reglas con duración fija
    for nombre, s, hold in (('regla 2 (caída fuerte)', m['B'], 3), ('regla 3 (resultados)', m['P'], 10)):
        if s.iloc[L] == 1:
            t0 = inicio_tramo(s)
            k_venta = t0 + hold + 1 - L          # la venta es en la apertura de la sesión t0 + hold + 1
            compra = sesion(t0 + 1 - L)
            lineas.append(f'   📅 {nombre}: comprada en la apertura del {fecha(compra)}; VENTA PREVISTA en la apertura '
                          f'del {fecha(sesion(k_venta))}, pase lo que pase.')
    if not oficial:
        lineas.append('   (calendario sin festivos: si alguna fecha cae en festivo de EE. UU., pasa a la siguiente sesión)')

    # ---- qué vigilar en el próximo cierre
    lineas.append(f'Qué vigilar al cierre del {fecha(prox)}:')
    ut, uq = umbral_cruce(c), umbral_cruce(qc)
    a_on, g_on = bool(m['A'].iloc[L]), bool(m['G'].iloc[L])
    def txt_umbral(nombre, u, on, ultimo):
        if on and u <= 0.8 * ultimo:
            return f'{nombre} no puede pasar a bajista en un solo día'
        if not on and u >= 1.2 * ultimo:
            return f'{nombre} no puede pasar a alcista en un solo día (necesitaría cerrar por encima de {dinero(u)})'
        return f'{nombre} {"sigue" if on else "pasa a"} alcista si cierra por encima de {dinero(u)}'
    txt_a = txt_umbral('TSLA', ut, a_on, c.iloc[L])
    txt_g = txt_umbral('QQQ', uq, g_on, qc.iloc[-1])
    estado1 = 'ENCENDIDA' if ag.iloc[L] else 'apagada'
    lineas.append(f' • Regla 1 (tendencia, {estado1}): TSLA {"alcista" if a_on else "bajista"}, QQQ '
                  f'{"alcista" if g_on else "bajista"}. {txt_a}; {txt_g}. Hacen falta las dos.')
    if m['B'].iloc[L] == 1:
        lineas.append(' • Regla 2 (caída fuerte): ACTIVA; no se vuelve a activar hasta después de la venta.')
    else:
        u = 0.88 * c.iloc[L - 4]
        lineas.append(f' • Regla 2 (caída fuerte): se activa si TSLA cierra en {dinero(u)} o menos '
                      f'(un 12% por debajo del cierre del {fecha(df.index[L - 4])}).')
    reacciones = F.reaction_sessions(extra)
    futuras = [d for d in reacciones if d > last]
    if a.next_earnings:
        futuras.append(pd.Timestamp(a.next_earnings))
    if m['P'].iloc[L] == 1:
        lineas.append(' • Regla 3 (resultados): ACTIVA (ver venta prevista arriba).')
    elif futuras and min(futuras) == prox:
        lineas.append(f' • Regla 3 (resultados): el {fecha(prox)} es el día de reacción a los resultados de Tesla: si TSLA '
                      f'cierra en {dinero(1.03 * c.iloc[L])} o más (+3% sobre el cierre del {fecha(last)}), compra al día siguiente.')
    elif futuras:
        lineas.append(f' • Regla 3 (resultados): próximos resultados; el día de reacción será el {fecha(min(futuras))}. '
                      'Si ese día TSLA cierra un 3% o más por encima del cierre anterior, se compra al día siguiente.')
    else:
        lineas.append(' • Regla 3 (resultados): sin resultados en los próximos días.')
    ultima = reacciones.max()
    if (last - ultima).days > 60 and not a.reaction and not a.next_earnings:
        lineas.append(f'COMPROBAR_RESULTADOS: la última fecha de resultados conocida es el {ultima.date()}; '
                      'busca la fecha de los próximos (o últimos) resultados de Tesla y vuelve a ejecutar con '
                      '--next-earnings o --reaction.')
    lineas.append(f'Posición objetivo tras la próxima apertura: {target:.0%} del dinero de la estrategia '
                  f'(ahora: {held:.0%}).')
    # la acción va en la primera línea (es la que se ve en la notificación); el aviso de datos antiguos, encima
    i_acc = next(i for i, x in enumerate(lineas) if x.startswith(('🔔', '✅')))
    j = i_acc + 1
    while j < len(lineas) and lineas[j].startswith('   '):
        j += 1
    bloque = lineas[i_acc:j]
    resto = lineas[:i_acc] + lineas[j:]
    avisos = [x for x in resto if x.startswith('⚠️')]
    resto = [x for x in resto if not x.startswith('⚠️')]
    print('=== MENSAJE ===')
    print('\n'.join(avisos + bloque + resto))
    print('=== FIN ===')
    print(f'ACCION={accion}')


if __name__ == '__main__':
    main()
