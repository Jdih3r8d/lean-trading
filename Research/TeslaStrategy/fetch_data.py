"""Descarga los datos diarios que usa la investigación y los guarda en data/.

* data/tsla.csv     TSLA OHLCV ajustado por splits, 2010-06-29 en adelante.
                    Stonks/tickers hasta 2016-11-22 + yennanliu/finance_data desde 2016-11-23 (coinciden en +-0.04%).
                    La fila de Yahoo del 2018-03-13 repite el open/high/low del día anterior; se reemplaza por los valores
                    en que coinciden otras dos fuentes independientes (Stonks/tickers y willhjw/big_movers).
* data/qqq_adj.csv  QQQ con precios ajustados por dividendos (retorno total) y la columna adj_factor
                    (precio ajustado = precio bruto * adj_factor). Fuente: alm0421/alm0421 (espejo de Yahoo con dividendos).

Uso: python3 fetch_data.py   (desde esta carpeta)
"""
import io
import os
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
RAW = "https://raw.githubusercontent.com/"
TSLA_OLD = RAW + "Stonks/tickers/HEAD/tickers/nasdaq/TSLA.csv"
TSLA_NEW = RAW + "yennanliu/finance_data/HEAD/data/prices/tsla.csv"
QQQ = RAW + "alm0421/alm0421/HEAD/data/prices/QQQ.csv"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return pd.read_csv(io.BytesIO(r.read()))


def tsla():
    old = get(TSLA_OLD).rename(columns=str.lower)
    old["date"] = pd.to_datetime(old["date"])
    old = old.set_index("date")[["open", "high", "low", "close", "volume"]]
    old["volume"] *= 1e6  # esta fuente guarda el volumen en millones
    new = get(TSLA_NEW)
    new["date"] = pd.to_datetime(new["date"])
    new = new.set_index("date")[["open", "high", "low", "close", "volume"]]
    df = pd.concat([old[old.index < new.index[0]], new]).sort_index()
    df = df[~df.index.duplicated()]
    df.loc["2018-03-13", ["open", "high", "low"]] = [22.9947, 23.0080, 22.4176]
    df.to_csv(os.path.join(DATA, "tsla.csv"))
    print(f"TSLA: {len(df)} sesiones, {df.index[0].date()} .. {df.index[-1].date()}")


def qqq():
    q = get(QQQ)
    q["date"] = pd.to_datetime(q["date"])
    q = q.set_index("date").sort_index()
    div = q["dividend"].fillna(0.0)
    f = (1 - div / q["close"].shift(1)).fillna(1.0)          # factor de cada fecha ex-dividendo
    adj_factor = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)  # producto de los factores de fechas posteriores
    out = q[["open", "high", "low", "close"]].mul(adj_factor, axis=0)
    out["volume"] = q["volume"]
    out["div"] = div
    out["adj_factor"] = adj_factor
    out.round(6).to_csv(os.path.join(DATA, "qqq_adj.csv"), float_format="%.6g")
    print(f"QQQ: {len(out)} sesiones, {out.index[0].date()} .. {out.index[-1].date()}")


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    tsla()
    qqq()
