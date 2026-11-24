"""Descarga y une el historial diario ajustado de TSLA (2010-06-29 en adelante) en tsla.csv.

Fuentes (CSV públicos en GitHub, ajustados por splits):
  - Stonks/tickers           2010-06-29 .. 2016-11-22
  - yennanliu/finance_data   2016-11-23 .. hoy
En el tramo común ambas coinciden en +-0.04%.
"""
import io
import urllib.request

import pandas as pd

RAW = "https://raw.githubusercontent.com/"
OLD = RAW + "Stonks/tickers/HEAD/tickers/nasdaq/TSLA.csv"
NEW = RAW + "yennanliu/finance_data/HEAD/data/prices/tsla.csv"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return pd.read_csv(io.BytesIO(r.read()))


old = get(OLD).rename(columns=str.lower)
old["date"] = pd.to_datetime(old["date"])
old = old.set_index("date")[["open", "high", "low", "close", "volume"]]
old["volume"] *= 1e6  # this source stores volume in millions

new = get(NEW)
new["date"] = pd.to_datetime(new["date"])
new = new.set_index("date")[["open", "high", "low", "close", "volume"]]

df = pd.concat([old[old.index < new.index[0]], new]).sort_index()
df = df[~df.index.duplicated()]
df.to_csv("tsla.csv")
print(f"{len(df)} sesiones, {df.index[0].date()} .. {df.index[-1].date()}")
