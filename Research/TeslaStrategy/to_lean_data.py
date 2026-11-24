"""Convierte un CSV diario ajustado por splits (date,open,high,low,close,volume) al formato de LEAN.

LEAN guarda precios SIN ajustar y aplica los splits mediante un factor file. Este script deshace el ajuste
con el calendario de splits indicado, escribe Data/equity/usa/daily/<ticker>.zip (precios x10000), el factor
file y el map file. Así las comisiones por acción y los tamaños de orden son realistas.

Uso: python3 to_lean_data.py tsla.csv TSLA /ruta/a/lean-trading/Data
"""
import os
import sys
import zipfile

import pandas as pd

# split efectivo (primer día ajustado) -> ratio
SPLITS = {'TSLA': [('2020-08-31', 5.0), ('2022-08-25', 3.0)]}


def main(csv_path, ticker, data_root):
    t = ticker.lower()
    df = pd.read_csv(csv_path, parse_dates=['date']).sort_values('date').reset_index(drop=True)
    splits = [(pd.Timestamp(d), r) for d, r in SPLITS.get(ticker.upper(), [])]
    # factor por el que hay que multiplicar el precio ajustado para obtener el precio negociado ese día
    mult = pd.Series(1.0, index=df.index)
    for d, r in splits:
        mult[df.date < d] *= r
    raw = df.copy()
    for col in ('open', 'high', 'low', 'close'):
        raw[col] = df[col] * mult
    raw['volume'] = df['volume'] / mult
    lines = [
        f"{d:%Y%m%d} 00:00,{round(o * 10000)},{round(h * 10000)},{round(l * 10000)},{round(c * 10000)},{int(round(v))}"
        for d, o, h, l, c, v in zip(raw.date, raw.open, raw.high, raw.low, raw.close, raw.volume)
    ]
    usa = os.path.join(data_root, 'equity', 'usa')
    with zipfile.ZipFile(os.path.join(usa, 'daily', f'{t}.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(f'{t}.csv', '\n'.join(lines) + '\n')
    # factor file: cada fila da el split factor acumulado aplicable a las fechas <= fecha de la fila
    rows = []
    cum = 1.0
    for d, r in splits:
        cum /= r
    prev_cum = cum
    first = df.date.iloc[0]
    rows.append((first, prev_cum, raw.close.iloc[0]))
    for d, r in splits:
        last_before = df.date[df.date < d].iloc[-1]
        rows.append((last_before, prev_cum, float(raw.close[df.date == last_before].iloc[0])))
        prev_cum *= r
    with open(os.path.join(usa, 'factor_files', f'{t}.csv'), 'w') as f:
        for d, sf, ref in rows:
            f.write(f"{d:%Y%m%d},1,{sf:.10g},{ref:.4f}\n")
        f.write("20501231,1,1,0\n")
    with open(os.path.join(usa, 'map_files', f'{t}.csv'), 'w') as f:
        f.write(f"{first:%Y%m%d},{t},Q\n20501231,{t},Q\n")
    print(f"{ticker}: {len(lines)} barras {df.date.iloc[0].date()} .. {df.date.iloc[-1].date()}")


if __name__ == '__main__':
    main(*sys.argv[1:4])
