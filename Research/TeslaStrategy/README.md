# TSLA: tendencia con filtro de mercado + capitulación + continuación tras resultados

Investigación con datos diarios de TSLA del 29-jun-2010 al 23-nov-2026 (4.127 sesiones). El algoritmo LEAN está en
`Algorithm.Python/TeslaTrendRegimeEarningsAlgorithm.py`. Se ejecutó en el motor LEAN de este repositorio y reproduce
la investigación sesión a sesión.

## Reglas exactas

Son tres módulos y todos solo compran. Cada señal se calcula con el **cierre** del día *t* y se ejecuta con una orden
*market-on-open* en la **apertura de *t+1***.

| Módulo | Entrada | Salida |
|---|---|---|
| **A·G: tendencia con filtro de mercado** | SMA10 > SMA30 del cierre de TSLA **y** SMA10 > SMA30 del cierre de QQQ (ajustado por dividendos) | Cuando cualquiera de las dos condiciones deja de cumplirse |
| **B: capitulación** | El cierre está al menos un **12% por debajo** del cierre de 5 sesiones antes | En la apertura de la **3.ª sesión** después de entrar (compra en *t+1*, venta en *t+4*) |
| **P: continuación tras resultados** | En la sesión que reacciona a los resultados trimestrales, el cierre está al menos un **+3% por encima** del último cierre previo al anuncio | En la apertura de la **10.ª sesión** después de entrar |

- **Peso objetivo en TSLA:** `min(1, 0,5·A·G + 0,5·B + 0,5·P)`, es decir 0%, 50% o 100% del capital. Sin apalancamiento ni cortos; el resto queda en efectivo.
- **Rebalanceo:** se rebalancea cuando cambia el objetivo, o cuando el peso real se desvía más de 5 puntos del objetivo. Son unas 25 órdenes al año.
- **Señales ignoradas:** las señales de B y P que llegan mientras el módulo ya está comprado, o el día en que se decide su salida, se ignoran.
- **Calendario de resultados:** la sesión de reacción es la primera cuya apertura refleja la publicación. Tesla publica tras el cierre (65 de 66 veces), así que suele ser la sesión siguiente al anuncio; la excepción fue el 2012-11-05, antes de la apertura. Hay que añadir la nueva fecha **cada trimestre**; Tesla la anuncia 2-3 semanas antes.
- **Cuenta:** se necesita una cuenta de margen. El objetivo del 100% se calcula con el cierre de la decisión, así que tras una apertura con subida se financia brevemente un poco de margen (como mucho un 104% invertido en el backtest). Con una cuenta de efectivo se rechazan órdenes.

## Resultados

Las cifras de la estrategia son netas de 5 pb por lado, con ejecución en la apertura siguiente y reajuste diario al peso objetivo; con la banda de 5 puntos de LEAN, el Sharpe es 1,16 / 1,55 / 1,52 (IS / OOS / 2023+). Buy & hold se mide de cierre a cierre, sin costos. En la columna de 2026, las rentabilidades son acumuladas en el año, no anualizadas.

### Por periodo

| | 2010-2018 (IS) | 2019-2026 (OOS) | 2023-2026 | 2026 hasta 23-nov | Todo |
|---|---|---|---|---|---|
| **Estrategia: Sharpe** | **1,18** | **1,56** | **1,53** | 0,74 | **1,37** |
| Estrategia: rentabilidad anual | 26,1% | 49,5% | 40,0% | +8,1% | 36,9% |
| Estrategia: caída máxima | −23% | −23% | −22% | −9% | −23% |
| Referencia del estudio 1: Sharpe | 0,93 | 1,26 | 1,05 | 0,69 | 1,10 |
| Buy & hold: Sharpe | 0,86 | 0,89 | 0,80 | −0,12 | 0,87 |
| Buy & hold: rentabilidad anual | 36,4% | 43,7% | 34,2% | −14,3% | 39,9% |
| Buy & hold: caída máxima | −50% | −74% | −54% | −34% | −74% |

### Robustez

- **Costos:** con 15 pb por lado, el Sharpe es 1,51 OOS y 1,32 en todo el periodo.
- **Retraso de ejecución:** con un día de retraso, el Sharpe es 1,30 OOS y 1,09 desde 2023.
- **LEAN:** con comisiones IBKR por acción y 5 pb de deslizamiento, los pesos son idénticos a los de la investigación en las 4.127 sesiones, tanto en el modo "cierre" como en el modo "mañana". Medido con el método de la investigación sobre la curva diaria de LEAN: Sharpe 1,16 / 1,55 / 1,52 (IS / OOS / 2023+), rentabilidad anual 36,9% (LEAN informa 36,7%), caída máxima −23,2% y 402 órdenes.

### Rentabilidad por operación

Las filas de módulos están por unidad de capital asignado al módulo, netas de costos. Como cada módulo usa el 50% de la cuenta, el efecto en la cuenta es aproximadamente la mitad. La fila Combinado está por unidad de exposición media del tramo (entre 0,5 y 0,875 de la cuenta); en la cuenta equivale a **+4,1%** de media por tramo (mediana +0,7%; IS +3,3% / OOS +4,9% / 2023+ +3,8%).

| Módulo | Operaciones | Media | Mediana | Ganadoras | Ganancia media | Pérdida media | Duración | Media IS / OOS / 2023+ |
|---|---|---|---|---|---|---|---|---|
| A·G tendencia | 83 | **+9,6%** | +0,1% | 52% | +24,0% | −5,9% | 23 sesiones | +5,9% / +14,5% / +6,8% |
| B capitulación | 83 | **+2,55%** | +2,6% | 65% | +6,6% | −5,0% | 3 sesiones | +2,4% / +2,6% / +3,8% |
| P resultados | 24 | **+10,85%** | +10,8% | 79% | +15,4% | −6,4% | 10 sesiones | +8,6% / +14,6% / +15,7% |
| Combinado (tramos con posición) | 151 | **+7,1%** | +1,2% | 57% | +16,5% | −5,4% | 15 sesiones | +5,3% / +8,7% / +6,9% |

## Expectativa realista

Al backtest hay que aplicarle un descuento:

- **Cuántas pruebas se hicieron:** unas 9.800 configuraciones probadas en total entre los dos estudios.
- **Información fuera de muestra:** el filtro QQQ se identificó viendo datos fuera de muestra.
- **Parámetros afortunados:** los parámetros nominales caen en el percentil 89-92 de su nube de perturbaciones de ±30%.
- **Ejecución:** un día de retraso cuesta 0,26 de Sharpe OOS y 0,44 desde 2023.

Los cuatro revisores del panel final dan expectativas parecidas (rangos combinados):

| | Backtest | Esperado en vivo |
|---|---|---|
| Sharpe | 1,37 (todo el periodo) | **≈ 0,9-1,05** (rango 0,7-1,2) |
| Rentabilidad anual | 36,9% | **≈ 15-25%** (central ~18%; rango 12-25%) |
| Caída máxima | −23% | **−25% a −40%** en algún momento de 3-10 años |
| Rentabilidad por operación A·G | +9,6% | ≈ +3-7% (central +4-5%) |
| Rentabilidad por operación B | +2,55% | ≈ +1-1,5% (el optimizador, hasta +2,5%; solo si se ejecuta en la apertura siguiente) |
| Rentabilidad por operación P | +10,85% | ≈ +5-9% (central ~+5%) |

Esto es protección contra caídas con exposición a TSLA, no un sustituto de mantener la acción. En rachas fuertes de
TSLA captura solo el 29-64% de la subida en términos logarítmicos: en 2020 ganó +254% frente a +743%. En las caídas
cede muy poco: en 2022 perdió −1,3% frente a −65%. En 161 ventanas de 3 años (inicio mensual) supera a buy & hold en
rentabilidad el 49% de las veces, en Sharpe el 86% y en caída máxima el 100%, y nunca perdió dinero (peor +4,9%). Con
inicio diario, la peor ventana de 3 años perdió −0,5% (abr-2016 a abr-2019). Las ventanas se solapan: equivalen a unos 5
bloques independientes.

## Cómo se llegó aquí

### Estudio 1 (`study1/`)

Se probaron 6.176 variantes de reglas clásicas: RSI, Bollinger, IBS, caídas, SMA, Donchian y momentum. El resultado
fue la referencia A+B, que tiene un Sharpe OOS de 1,26.

### Estudio 2

Se armó un laboratorio con un *harness* común (`harness.py`) y un protocolo común (`PROTOCOL.md`).

**Auditoría del motor.** Un auditor independiente revisó el motor antes de usarlo. Encontró y se corrigió:

- La contabilidad de operaciones en los cambios de largo a corto.
- Costos de rebalanceo y de apalancamiento que no se cobraban.
- Errores en el test de permutaciones.
- El cálculo de la caída máxima.
- Una fila corrupta de Yahoo (13-mar-2018).

**Siete familias.** Cada familia la investigó un agente y la validó otro agente independiente, que la reimplementó
desde el texto de las reglas e intentó refutarla. En total se probaron 3.401 configuraciones.

| Familia | Configuraciones | Resultado |
|---|---|---|
| Volatilidad (régimen, compresión y ruptura, picos, VIX) | 503 | Filtro VIX sobre A: **débil**. Es un seguro anti-pánico que depende de 3 episodios y desaparece con 1 día de retraso |
| Volatilidad implícita (IV de TSLA 2020-25, estructura del VIX, vencimientos de opciones) | 988 | IV de TSLA: **refutada**. Disparadores con el VIX: débiles |
| Resultados y entregas | 235 | **P confirmado**. El resto (antes del anuncio, entregas, evitar los resultados) no funciona |
| Régimen de mercado (QQQ/SPY) | 558 | Filtro QQQ 10/30 sobre A: **débil pero el más robusto**. Sobrevive a retrasos, costos y perturbaciones |
| Gestión de posición (stops, objetivos, tamaño por volatilidad, Kelly) | 420 | Nada mejora. El tamaño por volatilidad **empeora** porque TSLA rinde más en volatilidad alta |
| Patrones (picos de volumen, máximos de 52 semanas, gaps, calendario) | 547 | Módulos V y X **débiles**: V solo aporta en IS y la ventaja OOS de X depende de unas pocas operaciones de 2020 |
| *Machine learning* con walk-forward estricto | 150 | No supera a las reglas simples |

### Combinación y panel final

**Combinación.** Se combinaron los componentes con mejor evidencia: P (confirmado) y el filtro G (débil, pero el más
robusto de su familia; no añade parámetros porque usa los mismos 10/30 que A, y no tiene apoyo en IS: p=0,21).

**Panel final.** Cuatro agentes revisaron la combinación con enfoques distintos. Los cuatro recomendaron adoptarla sin
cambiar las reglas; dos pidieron cambios en las expectativas y en la implementación LEAN.

- **Optimizador.** Pre-registró 203 alternativas; ninguna supera a F3 de forma robusta.
- **Escéptico estadístico:**
  - F3 frente a la referencia: diferencia de Sharpe +0,27, p=0,005, y gana en 13 de 17 años. Tras corregir por pruebas múltiples, la confianza en que F3 supera a la referencia es del 65-90%.
  - F3 no se distingue estadísticamente de F1 (F3 sin el filtro G).
  - P sobrevive al ajuste por búsqueda en IS (p=0,017) y en todo el periodo (p=0,021), pero no fuera de muestra (p=0,235; 0,11 desde 2023), con solo 9 operaciones OOS.
  - El filtro G concreto no sobrevive al ajuste por búsqueda; la familia de filtros sí en todo el periodo y OOS (p≈0,01), no en IS (p=0,09).
  - PBO de 0,1-0,5 según el conjunto de candidatos.
- **Escéptico de implementación.** Reimplementó F3 sesión a sesión, encontró fallos en el primer borrador de LEAN y
  escribió la versión final que reproduce la investigación exactamente.
- **Escéptico de régimen:**
  - Mejora sobre la referencia en los tres tercios de la muestra y, en todo el periodo, en 499 de 499 perturbaciones de ±30% de todos los parámetros a la vez (OOS: 496-498 de 499).
  - El módulo de tendencia por sí solo decae con el tiempo; el filtro lo amortigua (Sharpe de A·G 0,90 frente a 0,57 de A en el último tercio).

## Riesgos

- **P tiene pocas operaciones:** 24 en 16 años, 9 fuera de muestra y ninguna en 2026. Si se olvida añadir una fecha de resultados, se pierde el módulo mejor confirmado.
- **G es un seguro:** gana en las caídas del Nasdaq (2020, 2022, 2023-25) y cuesta dinero en las subidas de TSLA que no acompaña el mercado (2013, 2019, 2021).
- **B depende de ejecutar en la apertura siguiente** y es sensible al umbral: con 8-10% en vez de 12%, el Sharpe OOS de A+B cae de 1,26 a ~1,02.
- Puede haber periodos largos sin ganancias: entre 2017 y 2019 estuvo 2,25 años bajo el máximo anterior.
- Los precios desde 2017 tienen 2 decimales. Los datos vienen de espejos públicos de Yahoo en GitHub, contrastados con otras fuentes.
- Rentabilidades pasadas no garantizan rentabilidades futuras. Esto no es asesoramiento financiero.

## Reproducir

```bash
cd Research/TeslaStrategy
pip install pandas numpy scipy numba
python3 fetch_data.py      # data/tsla.csv y data/qqq_adj.csv
python3 f3_strategy.py     # métricas, operaciones por módulo (results/f3_trades.csv) y estado actual
```

Para ejecutarlo en LEAN se necesita .NET 10 y Python 3.11 con pandas (accesible vía `PYTHONPATH`):

```bash
# desde Research/TeslaStrategy
python3 to_lean_data.py data/tsla.csv TSLA /ruta/datos_lean
python3 to_lean_data.py data/qqq_adj.csv QQQ /ruta/datos_lean 2009-01-02
# copiar también de Data/: market-hours/, symbol-properties/ y alternative/interest-rate/usa/interest-rate.csv
cd ../..   # raíz del repositorio
dotnet build QuantConnect.Lean.sln
cd Launcher/bin/Debug
F3_SLIPPAGE=0.0005 F3_OUT=/ruta/salida PYTHONNET_PYDLL=/usr/lib/x86_64-linux-gnu/libpython3.11.so \
  dotnet QuantConnect.Lean.Launcher.dll \
  --algorithm-type-name TeslaTrendRegimeEarningsAlgorithm --algorithm-language Python \
  --algorithm-location ../../../Algorithm.Python/TeslaTrendRegimeEarningsAlgorithm.py \
  --data-folder /ruta/datos_lean/ --close-automatically true
```

Las variables `F3_*` solo se leen en backtests locales; en vivo o en la nube se usan los parámetros de LEAN (`mode`,
`band`, `slippage`, `cash_buffer`, `extra_reaction_sessions`, `out`). Sin `F3_SLIPPAGE`, LEAN corre sin deslizamiento
(rentabilidad anual 37,5%). Las cifras por periodo de LEAN se calculan con `harness.perf` sobre
`/ruta/salida/lean_equity_close_band0.05_slip0.0005.csv`.

Estudio 1: `cd study1 && cp ../data/tsla.csv . && python3 research.py && python3 final.py`. Sus salidas guardadas se
generaron antes de reparar la fila del 2018-03-13, así que las cifras IS cambian ligeramente; el Sharpe OOS de A+B
sigue siendo 1,26.

## Archivos

| Archivo | Contenido |
|---|---|
| `harness.py`, `engine.py` | Motor de evaluación auditado (v2) |
| `PROTOCOL.md` | Reglas comunes de evaluación |
| `f3_strategy.py` | Estrategia final e informe |
| `fetch_data.py` | Descarga de datos |
| `to_lean_data.py` | Conversión a formato LEAN (precios sin ajustar + factores de split y dividendo) |
| `data/tsla_earnings.csv` | 66 publicaciones de resultados (65 con hora del 8-K de la SEC) y su sesión de reacción |
| `results/f3_trades.csv` | Todas las operaciones por módulo |
| `study1/` | Primer estudio; su algoritmo `TeslaTrendCapitulationAlgorithm.py` queda superado por el nuevo |
