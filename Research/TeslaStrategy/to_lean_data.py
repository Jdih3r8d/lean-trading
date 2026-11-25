"""Convierte un CSV diario ajustado por splits (date,open,high,low,close,volume) al formato de LEAN.

LEAN guarda precios SIN ajustar y aplica los splits mediante un factor file. Este script deshace el ajuste
con el calendario de splits indicado, escribe Data/equity/usa/daily/<ticker>.zip (precios x10000), el factor
file y el map file. Así las comisiones por acción y los tamaños de orden son realistas.

Si el CSV trae una columna adj_factor (precios del CSV ajustados por dividendos = precio bruto * adj_factor), los
precios se convierten a brutos y adj_factor se usa como price factor del factor file, igual que los datos de LEAN
para ETFs como QQQ.

Uso: python3 to_lean_data.py tsla.csv TSLA /ruta/a/lean-trading/Data [fecha_inicio]
"""
import os
import sys
import zipfile

import pandas as pd

# split efectivo (primer día ajustado) -> ratio
SPLITS = {'TSLA': [('2020-08-31', 5.0), ('2022-08-25', 3.0)]}


def main(csv_path, ticker, data_root, start=None):
    t = ticker.lower()
    df = pd.read_csv(csv_path, parse_dates=['date']).sort_values('date').reset_index(drop=True)
    if start:
        df = df[df.date >= pd.Timestamp(start)].reset_index(drop=True)
    splits = [(pd.Timestamp(d), r) for d, r in SPLITS.get(ticker.upper(), [])]
    # factor por el que hay que multiplicar el precio ajustado para obtener el precio negociado ese día
    mult = pd.Series(1.0, index=df.index)
    for d, r in splits:
        mult[df.date < d] *= r
    div = 1 / df['adj_factor'] if 'adj_factor' in df else 1.0   # el volumen no se ajusta por dividendos
    raw = df.copy()
    for col in ('open', 'high', 'low', 'close'):
        raw[col] = df[col] * mult * div
    raw['volume'] = df['volume'] / mult
    lines = [
        f"{d:%Y%m%d} 00:00,{round(o * 10000)},{round(h * 10000)},{round(l * 10000)},{round(c * 10000)},{int(round(v))}"
        for d, o, h, l, c, v in zip(raw.date, raw.open, raw.high, raw.low, raw.close, raw.volume)
    ]
    usa = os.path.join(data_root, 'equity', 'usa')
    for sub in ('daily', 'factor_files', 'map_files'):
        os.makedirs(os.path.join(usa, sub), exist_ok=True)
    with zipfile.ZipFile(os.path.join(usa, 'daily', f'{t}.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'{t}.csv', '\n'.join(lines) + '\n')
    # factor file: cada fila da el price factor y el split factor aplicables a las fechas <= fecha de la fila
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
            f.write(f"{d:%Y%m%d},{float(p_)!r},{float(s_)!r},{ref:.4f}\n")
        f.write("20501231,1,1,0\n")
    first = df.date.iloc[0]
    with open(os.path.join(usa, 'map_files', f'{t}.csv'), 'w') as f:
        f.write(f"{first:%Y%m%d},{t},Q\n20501231,{t},Q\n")
    print(f"{ticker}: {len(lines)} barras {df.date.iloc[0].date()} .. {df.date.iloc[-1].date()}")


if __name__ == '__main__':
    main(*sys.argv[1:5])
