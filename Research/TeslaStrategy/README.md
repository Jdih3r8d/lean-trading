# TSLA: tendencia + capitulación

Investigación con datos diarios ajustados de TSLA del 29-jun-2010 al 23-nov-2026 (4.127 sesiones).
El algoritmo LEAN que la implementa está en `Algorithm.Python/TeslaTrendCapitulationAlgorithm.py`.

## Reglas

Hay dos módulos independientes, cada uno con el 50% del capital y solo en largo. Las señales se calculan
con el cierre diario y se ejecutan en la apertura de la sesión siguiente (orden *market-on-open*).

| Módulo | Entrada | Salida |
|---|---|---|
| **A: Tendencia** | SMA(10) del cierre por encima de SMA(30) | SMA(10) cruza por debajo de SMA(30) |
| **B: Capitulación** | Cierre al menos 12% por debajo del cierre de hace 5 sesiones | Apertura de la 3.ª sesión después de entrar |

## Resultados

Los resultados incluyen un costo de 0,05% por lado (0,10% ida y vuelta).
El periodo 2010-2018 es *in-sample* y 2019-2026 es *out-of-sample*.

### Por operación

| Módulo | Periodo | Operaciones | Promedio | Mediana | % ganadoras | Ganancia media | Pérdida media | Duración |
|---|---|---|---|---|---|---|---|---|
| A | 2010-2026 | 75 | **+11,0%** | −0,4% | 49% | +29,9% | −7,4% | 31 sesiones |
| A | 2019-2026 | 36 | +12,9% | 0,0% | 50% | +32,7% | −6,9% | 30 sesiones |
| A | 2023-2026 | 20 | +4,9% | −0,5% | 45% | +17,6% | −5,6% | 26 sesiones |
| B | 2010-2026 | 83 | **+2,55%** | +2,6% | 65% | +6,6% | −5,0% | 3 sesiones |
| B | 2019-2026 | 53 | +2,6% | +2,6% | 60% | +8,0% | −5,6% | 3 sesiones |
| B | 2023-2026 | 22 | +3,8% | +4,4% | 68% | +7,1% | −3,2% | 3 sesiones |

### Cartera (50% A + 50% B)

| Periodo | Sistema CAGR | Sistema Sharpe | Sistema Máx. DD | Buy&Hold CAGR | Buy&Hold Sharpe | Buy&Hold Máx. DD |
|---|---|---|---|---|---|---|
| 2010-2018 | 17,4% | 0,91 | −27% | 36,3% | 0,86 | −50% |
| 2019-2026 | 34,6% | 1,27 | −28% | 43,7% | 0,89 | −74% |
| 2023-2026 | 23,7% | 1,05 | −22% | 34,2% | 0,80 | −54% |
| 2026 (hasta 23-nov) | +9,4% | 0,69 | −11% | −14,3% | −0,12 | −34% |

El sistema **no supera a Buy&Hold en rentabilidad bruta**: TSLA subió unas 240 veces en el periodo.
Lo que mejora es el rendimiento ajustado por riesgo, con un Sharpe más alto y caídas máximas entre 2 y 3 veces menores.

## Metodología

- `research.py` evalúa 6.176 variantes: RSI, días bajistas consecutivos, caídas de N días, Bollinger,
  IBS, días de fuerte subida, cortos por sobrecompra, SMA, cruces, Donchian y momentum de serie temporal.
  Se prueban dos formas de ejecución: en la apertura siguiente y al cierre.
- Los parámetros se eligieron solo con datos de 2010-2018 y luego se comprobaron en 2019-2026.
- El vecindario de parámetros es robusto:
  - Módulo B: el promedio es positivo en el 100% de las 120 combinaciones vecinas en IS y en el 96% en OOS.
  - Módulo A: el Sharpe se mantiene entre 0,7 y 1,4 OOS para cualquier combinación rápida/lenta entre 5-20 y 20-50.
- Elegir cada año "la mejor estrategia reciente" (walk-forward) rinde **peor** que Buy&Hold. Por eso se usan
  reglas fijas y una combinación de módulos no correlacionados (correlación diaria ≈ 0,1).

### Lo que no funcionó

- Reversión a la media clásica (RSI-2, Bollinger, IBS): ganaba en 2010-2018 y se degradó fuera de muestra.
  Su ventaja sobre la simple deriva alcista de TSLA quedó en cero.
- Cualquier estrategia en corto: pierde en todos los periodos.
- Efecto nocturno (comprar al cierre y vender en la apertura siguiente tras días verdes): fuerte en 2019-2025,
  con t > 3, pero negativo en 2026.

## Riesgos

- Son 75 y 83 operaciones, una muestra pequeña. Con un 90% de confianza, el promedio por operación de B
  en 2019-2026 está entre −0,3% y +2,8% para la variante del 10%.
- El módulo A depende de tendencias fuertes; el promedio de 2020 está inflado por la subida de +743% de ese año.
- Resultados pasados no garantizan resultados futuros. Esto no es asesoramiento financiero.

## Reproducir

```bash
cd Research/TeslaStrategy
python3 fetch_data.py   # descarga y genera tsla.csv
pip install numba pandas
python3 research.py     # rejilla de 6.176 variantes -> grid.pkl
python3 final.py        # métricas del sistema final y trades.csv
```
