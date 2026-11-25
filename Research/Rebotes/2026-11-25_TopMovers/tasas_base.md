# Tasas base para las situaciones de hoy (25-nov-2026)

Generado por `tasas_base_hoy.py`. Universo: 499 acciones (componentes ACTUALES del S&P 500; 4 sin datos: FDXF, HONA, Q, VYLR), señales desde 2005-01-01 hasta 2026-11-24 (las ventanas de 10 sesiones terminan ~2 semanas antes). Operación: señal al cierre; comprar en la apertura siguiente; vender en la apertura 3, 5 o 10 sesiones después; 0,10% de costes. Eventos sin solaparse por acción (11 sesiones de separación).

**Cómo leer:** "gana" = % de operaciones con beneficio; media y mediana después de costes; "pierde >10% (10s)" = % de operaciones que a 10 sesiones pierden más de un 10%; "exceso SPY" = rentabilidad media menos la del SPY en la misma ventana (si es ~0, el rebote fue del mercado, no de la acción); "IC 90% gana 3s" = intervalo por bootstrap de SEMANAS (los eventos se concentran en pocas semanas de crisis, así que la n real es mucho menor). "Semanas" = nº de semanas distintas con eventos.

**Sesgo de supervivencia (fuerte en B, C y E):** solo están las empresas que HOY siguen en el S&P 500. Las que se hundieron tras caídas así (y salieron del índice o quebraron) no aparecen; además, muchas acciones entraron al índice DESPUÉS de subir mucho, así que su historia previa está seleccionada por haber salido bien. Estas cifras son un TECHO optimista. Y son acciones grandes de EE. UU.: HBX (Madrid), ZEAL, NANO y ABVX son otro mercado y otro tamaño.

## Lectura rápida para el juez (añadida a mano tras la ejecución)

Comprar en la apertura siguiente y vender 3 sesiones después, con 0,10% de costes. "Gana" es el % de operaciones con beneficio.

- **Referencia.** Un día cualquiera gana el 51% de las veces, con una media de +0,0% a 3 sesiones. Con el mercado en "pánico", como hoy, gana el 55% (+0,3%), con un IC 90% de 50% a 59%. El mercado en pánico rebota algo, pero el riesgo se duplica: el 8% de las operaciones pierde más de un 10% a 10 sesiones, frente al 4% en un día normal.
- **B. Caídas tipo ALAB, TTMI, NVTS y PENG.** La señal es: día de -5% o peor, 5 sesiones de -10% o peor, 3 meses de -30% o peor y bajo la media de 200.
  - En todo el universo gana el 58%, con media +2,0% y mediana +1,9%. Su IC 90% va del 51% al 65%. Supera al SPY en +1,0 puntos.
  - Solo en tecnología (IT) gana el 60% (+2,6%).
  - Con el mercado en pánico gana el 57% (+2,3%), con un IC de 48% a 66%. Es positivo, pero estadísticamente no se distingue de la moneda al aire.
  - La versión extrema, tipo TTMI (5 sesiones de -15% o peor y 3 meses de -40% o peor), gana el 61% (+3,8%).
  - Lo contrario: entre el 15% y el 21% de estas operaciones pierde más de un 10% a 10 sesiones, frente al 4% de un día normal. Además, todo se concentra en 2008, 2020 y 2022.
  - Al restringir a los eventos en que la acción ya estaba en el índice, las cifras se mantienen (57% a 61%). Pero las quiebras y exclusiones siguen fuera, así que es un techo.
- **Semiconductores en concreto (ALAB y NVTS son chips).**
  - En general rebotan peor: B1 en semiconductores gana el 56% (+1,6%, mediana +0,9%).
  - Con el SMH hundido, la caída de -5% en un día y -10% en 5 sesiones (B0) da 49% / +0,9%, con mediana -0,3% (E4). Desde 2001 da 50% / +0,5% (X5). Es una moneda al aire.
  - TTMI (componentes) y PENG (hardware) encajan mejor en "IT", que da 55% a 60%.
- **E. Semiconductores hundidos (SMH 30% o más bajo su máximo).**
  - Lo más parecido a hoy es B1 en IT con el SMH hundido y el SPY en pánico: gana el 58% (+2,8%), con un IC de 46% a 69%. Son solo 35 semanas, casi todas de 2008.
  - Por episodio, la caída de -5% en un día y -10% en 5 sesiones en IT (E3) da resultados muy distintos: en 2008, 51% / 0,0%; en 2022, 40% / -0,3%; en 2020, 68%; en 2001-2002, 55% a 59%.
  - Un día cualquiera de IT con el SMH hundido da 48% / -0,2% a 3 sesiones.
- **Episodio actual (octubre y noviembre de 2026).** Las caídas de -5% en un día y -10% en 5 sesiones del propio desplome han dado rebotes cortos que se desvanecen:
  - Todas: 59% a 3 sesiones (+1,3%), pero solo 36% a 10 sesiones (-3,2%).
  - Solo IT: 54% (+0,3%) a 3 sesiones y 27% (-5,4%) a 10 sesiones.
  - Las señales de la semana del 16 al 22 de noviembre ganaron solo el 8% a 3 sesiones (n=12, -5,7%) y el 11% a 1 sesión (-3,9%, n=72).
  - Conclusión: si se compra, que sea a 3 sesiones y no a 10, y con tamaño pequeño.
- **C. Caída de un día de -15% o peor (tipo HBX).**
  - Gana el 51% (+0,8%), con mediana +0,2%, es decir, una moneda al aire. El 17% de las operaciones pierde más de un 10% a 10 sesiones.
  - Si la acción estaba por encima de su media de 200, gana el 58% (+1,9%), pero con n=124 y un IC de 46% a 69%.
  - Si estaba por debajo, gana el 51%, con mediana +0,1%.
  - A 10 sesiones la media es +3,6%, pero la mediana es +2,3% y gana el 57%: unos pocos rebotes enormes tiran de la media.
  - HBX además es de Madrid, salió a bolsa hace poco y la caída probablemente se debe a resultados o previsiones (deriva post-resultados), así que la referencia es aún más débil.
- **D. Subidas.**
  - Un día de +5% no da ventaja: gana el 50% (-0,1%). En salud gana el 50% (+0,2%) y en biotecnología el 49% (mediana -0,1%). Con el mercado en pánico la media es -0,8%.
  - La única fila positiva es salud de +5% en el día que venía de -30% o peor en 3 meses (tipo NANO): 58% (+2,3%), IC de 51% a 65%, n=203 y 65% a 10 sesiones. Es útil para NANO o ABVX si se confirma su caída de 3 meses, aunque son pequeñas europeas fuera del S&P 500.
  - **5 sesiones de +20% (INSM) tienden a REVERTIR:**
    - En general gana el 39% (-1,4%).
    - Con el mercado en pánico, el 31% (-3,0%).
    - Por encima de la media de 200 y con el mercado en pánico, como INSM, el 36% (-2,3%), con un IC de 28% a 44%.
    - En salud con el día de la señal plano, el 46% (-0,5%).
    - A 10 sesiones queda en torno al 54% / 0%.
  - No conviene perseguir a INSM.

## Tabla completa

| Situación | n | semanas | gana 3s | IC 90% gana 3s | media 3s | mediana 3s | gana 5s | media 5s | gana 10s | media 10s | pierde >10% (10s) | exceso SPY 3s | exceso SPY 10s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A. Cualquier día (todas) | 226763 | 1134 | 51% | 50%–53% | +0.0% | +0.1% | 53% | +0.2% | 54% | +0.5% | 4% | -0.0% | +0.1% |
| A. Cualquier día con SPY bajo su media de 200 y media 10 < media 30 ("pánico", como hoy) | 42837 | 118 | 55% | 50%–59% | +0.3% | +0.4% | 54% | +0.3% | 57% | +0.8% | 8% | -0.1% | +0.1% |
| A. Cualquier día, solo Information Technology | 32452 | 1069 | 51% | 50%–53% | +0.1% | +0.1% | 54% | +0.4% | 54% | +0.7% | 6% | +0.0% | +0.3% |
| A. Cualquier día, solo IT, con SPY en "pánico" | 6070 | 100 | 54% | 48%–59% | +0.4% | +0.4% | 53% | +0.5% | 57% | +1.3% | 9% | +0.1% | +0.6% |
| A. Cualquier día, solo Health Care | 27816 | 1036 | 51% | 49%–53% | +0.0% | +0.1% | 54% | +0.2% | 55% | +0.5% | 4% | -0.0% | +0.1% |
| A. Cualquier día, SPY en "pánico" y SMH >=30% bajo su máximo de 52 semanas | 14217 | 38 | 51% | 43%–58% | +0.2% | +0.1% | 54% | +0.5% | 53% | +0.9% | 11% | +0.1% | +0.6% |
| B. Día <=-5% tras 5 sesiones <=-10% (sin más filtros) | 8941 | 920 | 55% | 51%–60% | +0.9% | +0.8% | 54% | +0.9% | 54% | +1.0% | 16% | +0.5% | +0.9% |
| B. Igual que B0, solo IT | 2026 | 588 | 54% | 50%–57% | +0.7% | +0.5% | 56% | +1.3% | 54% | +1.7% | 14% | +0.5% | +1.7% |
| B. Día <=-5%, 5 ses. <=-10%, 3 meses <=-30%, bajo su media de 200 (todas) | 2463 | 371 | 58% | 51%–65% | +2.0% | +1.9% | 56% | +2.3% | 59% | +3.4% | 19% | +1.0% | +2.2% |
| B. Igual que B1, solo IT | 468 | 161 | 60% | 53%–67% | +2.6% | +2.6% | 61% | +3.3% | 59% | +3.7% | 15% | +2.1% | +3.0% |
| B. B1 con SPY bajo su media de 200 | 2145 | 195 | 57% | 50%–65% | +2.0% | +1.9% | 56% | +2.3% | 60% | +3.7% | 20% | +0.8% | +2.2% |
| B. B1 solo IT con SPY bajo su media de 200 | 370 | 102 | 59% | 51%–67% | +2.3% | +2.5% | 60% | +3.1% | 60% | +3.7% | 16% | +1.7% | +2.9% |
| B. B1 con SPY en "pánico" (bajo 200 y 10<30, como hoy) | 1890 | 142 | 57% | 48%–66% | +2.3% | +2.0% | 57% | +2.6% | 59% | +3.0% | 21% | +1.1% | +1.6% |
| B. B1 con SPY POR ENCIMA de su media de 200 (contraste) | 339 | 193 | 60% | 56%–65% | +2.1% | +1.6% | 55% | +2.5% | 52% | +1.2% | 17% | +1.9% | +1.2% |
| B. B1 solo semiconductores (sub-industria GICS) | 160 | 77 | 56% | 47%–64% | +1.6% | +0.9% | 59% | +2.2% | 53% | +2.0% | 20% | +1.7% | +1.7% |
| B. Día <=-5%, 5 ses. <=-15%, 3 meses <=-40%, bajo media 200 (más extremo, como TTMI) | 1137 | 190 | 61% | 51%–71% | +3.8% | +4.3% | 59% | +5.1% | 63% | +6.1% | 19% | +2.3% | +3.9% |
| C. Caída de un día >=15% (todas) | 1354 | 446 | 51% | 44%–58% | +0.8% | +0.2% | 51% | +1.3% | 57% | +3.6% | 17% | +0.8% | +2.8% |
| C. >=15% con la acción POR ENCIMA de su media de 200 | 124 | 91 | 58% | 46%–69% | +1.9% | +1.2% | 65% | +2.7% | 67% | +5.2% | 8% | +1.4% | +4.7% |
| C. >=15% con la acción POR DEBAJO de su media de 200 | 1234 | 404 | 51% | 43%–58% | +0.8% | +0.1% | 50% | +1.2% | 56% | +3.4% | 18% | +0.8% | +2.7% |
| C. >=15% con SPY POR ENCIMA de su media de 200 | 496 | 297 | 53% | 49%–58% | +0.7% | +0.4% | 53% | +1.0% | 53% | +1.2% | 10% | +0.5% | +1.1% |
| C. >=15% con SPY bajo su media de 200 | 861 | 155 | 50% | 40%–60% | +0.8% | +0.0% | 50% | +1.5% | 59% | +4.9% | 21% | +0.9% | +3.7% |
| C. Caída de un día >=20% | 487 | 233 | 53% | 46%–61% | +2.0% | +0.8% | 57% | +3.0% | 58% | +4.8% | 17% | +2.2% | +4.2% |
| C. >=15% en una acción que NO venía cayendo (5 ses. previas > -5%, "sorpresa") | 892 | 393 | 51% | 46%–57% | +0.8% | +0.2% | 54% | +2.0% | 57% | +2.9% | 15% | +0.5% | +1.9% |
| D. Subida de un día >=+5% (todas) | 27278 | 1137 | 50% | 48%–52% | -0.1% | +0.0% | 51% | -0.1% | 53% | +0.5% | 11% | +0.0% | +0.4% |
| D. >=+5% con la acción POR ENCIMA de su media de 200 | 15016 | 1128 | 50% | 49%–52% | +0.0% | +0.0% | 51% | +0.1% | 52% | +0.3% | 9% | -0.0% | +0.3% |
| D. >=+5% con la acción POR DEBAJO de su media de 200 | 13170 | 992 | 50% | 46%–53% | -0.1% | -0.1% | 50% | -0.2% | 53% | +0.6% | 15% | +0.1% | +0.5% |
| D. >=+5% con SPY en "pánico" | 8699 | 200 | 49% | 43%–54% | -0.8% | -0.2% | 49% | -1.1% | 53% | -0.0% | 17% | -0.2% | +0.3% |
| D. >=+5% con SPY sin pánico | 19539 | 1005 | 51% | 49%–52% | +0.2% | +0.1% | 51% | +0.2% | 53% | +0.6% | 9% | +0.1% | +0.5% |
| D. >=+5% solo Health Care | 3023 | 876 | 50% | 47%–52% | +0.2% | -0.0% | 51% | +0.2% | 52% | +0.3% | 10% | +0.2% | +0.4% |
| D. >=+5% Health Care, POR ENCIMA de su media de 200 | 1821 | 743 | 49% | 47%–51% | +0.1% | -0.1% | 51% | +0.2% | 51% | +0.1% | 8% | +0.1% | +0.2% |
| D. >=+5% Health Care, POR DEBAJO de su media de 200 | 1308 | 446 | 50% | 46%–54% | +0.2% | +0.1% | 51% | +0.1% | 54% | +0.7% | 13% | +0.4% | +0.6% |
| D. >=+5% Health Care con SPY en "pánico" | 856 | 147 | 52% | 45%–58% | -0.1% | +0.2% | 50% | -0.4% | 54% | +0.5% | 15% | +0.3% | +0.6% |
| D. >=+5% Health Care que llevaba <=-30% en 3 meses (como NANO) | 203 | 102 | 58% | 51%–65% | +2.3% | +2.0% | 59% | +1.5% | 65% | +4.1% | 15% | +1.5% | +3.1% |
| D. >=+5% solo biotecnología (sub-industria GICS; ZEAL, NANO) | 628 | 433 | 49% | 45%–52% | +0.3% | -0.1% | 50% | +0.8% | 52% | +1.0% | 13% | +0.2% | +0.7% |
| D. >=+5% Health Care en un día en que el SPY baja (subida propia, probable noticia) | 848 | 464 | 50% | 46%–53% | +0.5% | -0.0% | 54% | +0.8% | 53% | +1.0% | 8% | +0.2% | +0.6% |
| D. >=+5% Health Care con SPY en "pánico" y la acción bajo su media de 200 | 632 | 122 | 51% | 43%–57% | -0.1% | +0.1% | 49% | -0.5% | 54% | +0.7% | 17% | +0.3% | +0.7% |
| D. Subida de 5 sesiones >=+20% (todas) | 3431 | 683 | 39% | 35%–44% | -1.4% | -1.7% | 46% | -1.1% | 53% | +0.8% | 18% | -0.9% | +0.2% |
| D. 5 ses. >=+20% POR ENCIMA de su media de 200 | 1567 | 597 | 46% | 43%–49% | -0.3% | -0.5% | 51% | +0.2% | 55% | +1.5% | 12% | -0.2% | +1.1% |
| D. 5 ses. >=+20% POR DEBAJO de su media de 200 | 1954 | 287 | 34% | 28%–41% | -2.5% | -3.1% | 41% | -2.2% | 51% | +0.2% | 23% | -1.6% | -0.6% |
| D. 5 ses. >=+20% con SPY en "pánico" | 1477 | 121 | 31% | 25%–40% | -3.0% | -3.5% | 41% | -2.5% | 53% | -0.0% | 22% | -1.9% | -1.1% |
| D. 5 ses. >=+20% con SPY sin pánico | 2078 | 590 | 45% | 42%–49% | -0.3% | -0.6% | 49% | -0.2% | 53% | +1.6% | 15% | -0.3% | +1.2% |
| D. 5 ses. >=+20%, POR ENCIMA de su media de 200 y SPY en "pánico" (como INSM) | 237 | 90 | 36% | 28%–44% | -2.3% | -2.2% | 42% | -2.0% | 54% | +0.0% | 16% | -1.1% | -0.0% |
| D. 5 ses. >=+20% solo Health Care | 324 | 215 | 40% | 35%–45% | -1.1% | -1.2% | 49% | -0.5% | 53% | +1.0% | 11% | -0.5% | +0.5% |
| D. 5 ses. >=+20% Health Care, día de la señal plano (-2% a +2%, como INSM hoy) | 177 | 146 | 46% | 40%–51% | -0.5% | -0.7% | 54% | +0.7% | 56% | +2.0% | 7% | -0.5% | +1.5% |
| E. Cualquier día IT con SMH >=30% bajo su máximo (referencia) | 2844 | 46 | 48% | 40%–56% | -0.2% | -0.3% | 53% | +0.2% | 55% | +1.4% | 11% | +0.4% | +1.2% |
| E. Cualquier día semiconductores con SMH >=30% bajo su máximo (referencia) | 812 | 46 | 49% | 40%–58% | -0.0% | -0.3% | 55% | +0.7% | 56% | +2.0% | 11% | +0.5% | +1.9% |
| E. B1 (todas) con SMH >=30% bajo su máximo | 1564 | 78 | 57% | 50%–65% | +2.3% | +1.9% | 54% | +2.8% | 62% | +4.7% | 18% | +0.9% | +2.5% |
| E. B1 solo IT con SMH >=30% bajo su máximo | 264 | 46 | 60% | 50%–70% | +3.3% | +3.0% | 59% | +3.7% | 57% | +3.6% | 17% | +2.5% | +2.8% |
| E. B0 (día <=-5% y 5 ses. <=-10%) solo IT con SMH >=30% bajo su máximo | 558 | 71 | 55% | 45%–64% | +1.5% | +1.3% | 58% | +2.4% | 57% | +2.7% | 16% | +1.4% | +2.4% |
| E. B0 solo semiconductores con SMH >=30% bajo su máximo | 188 | 45 | 49% | 39%–61% | +0.9% | -0.3% | 55% | +1.7% | 52% | +2.2% | 18% | +1.6% | +2.6% |
| E. B1 IT con SMH >=30% bajo su máximo Y SPY en "pánico" (lo más parecido a hoy) | 229 | 35 | 58% | 46%–69% | +2.8% | +2.4% | 58% | +3.6% | 59% | +4.0% | 18% | +2.1% | +3.0% |
| X. B1 (todas) DESDE 2001 (incluye la crisis puntocom) | 3223 | 494 | 56% | 51%–61% | +1.6% | +1.6% | 56% | +2.2% | 58% | +3.5% | 20% | +0.7% | +2.2% |
| X. B1 solo IT DESDE 2001 | 762 | 237 | 58% | 53%–63% | +2.1% | +2.1% | 57% | +2.9% | 55% | +3.3% | 20% | +1.7% | +2.6% |
| X. E2: B1 IT con SMH hundido, DESDE 2001 | 521 | 106 | 57% | 51%–64% | +2.3% | +2.3% | 56% | +3.3% | 54% | +3.0% | 23% | +1.7% | +2.2% |
| X. E3: B0 IT con SMH hundido, DESDE 2001 | 1132 | 161 | 56% | 50%–61% | +1.6% | +1.3% | 59% | +2.7% | 55% | +2.8% | 20% | +1.3% | +2.4% |
| X. E4: B0 semiconductores con SMH hundido, DESDE 2001 | 404 | 107 | 50% | 43%–57% | +0.5% | -0.0% | 55% | +1.6% | 50% | +1.8% | 22% | +0.8% | +2.1% |
| X. Cualquier día IT con SMH hundido, DESDE 2001 (referencia) | 5538 | 104 | 50% | 44%–55% | +0.0% | -0.1% | 53% | +0.7% | 54% | +1.3% | 14% | +0.2% | +1.3% |
| Y. B1 (todas), solo si YA estaba en el S&P 500 ese día | 1542 | 266 | 57% | 49%–66% | +2.3% | +2.0% | 57% | +2.5% | 61% | +4.0% | 18% | +1.3% | +2.6% |
| Y. B1 solo IT, solo si YA estaba en el índice | 223 | 93 | 61% | 55%–68% | +3.4% | +2.7% | 65% | +4.2% | 61% | +4.5% | 14% | +3.0% | +4.0% |
| Y. E2 (B1 IT, SMH hundido), solo si YA estaba en el índice | 127 | 29 | 67% | 55%–78% | +5.0% | +5.1% | 65% | +5.1% | 59% | +4.5% | 14% | +4.0% | +3.7% |
| Y. B8 (más extremo), solo si YA estaba en el índice | 687 | 120 | 60% | 50%–72% | +3.7% | +4.0% | 58% | +4.9% | 65% | +6.8% | 18% | +2.3% | +4.4% |
| Y. C1 (día <=-15%), solo si YA estaba en el índice | 853 | 292 | 50% | 43%–58% | +0.4% | +0.1% | 49% | +0.2% | 57% | +2.9% | 18% | +0.5% | +2.1% |
| Y. C3 (día <=-15%, bajo su media de 200), solo si YA estaba en el índice | 796 | 271 | 50% | 42%–58% | +0.4% | -0.1% | 48% | +0.1% | 56% | +2.8% | 18% | +0.5% | +2.0% |
| Y. D11 (5 ses. >=+20%), solo si YA estaba en el índice | 1924 | 393 | 36% | 31%–41% | -2.1% | -2.2% | 45% | -1.7% | 54% | +0.4% | 18% | -1.6% | -0.6% |
| Y. D6 (día >=+5% Health Care), solo si YA estaba en el índice | 1899 | 658 | 48% | 45%–52% | -0.2% | -0.1% | 48% | -0.2% | 50% | -0.3% | 9% | -0.2% | -0.3% |
| Y. Cualquier día, solo si YA estaba en el índice (referencia) | 170524 | 1128 | 51% | 50%–52% | +0.0% | +0.1% | 53% | +0.1% | 54% | +0.4% | 4% | -0.1% | -0.0% |

## Reparto por años de las filas con pocas semanas (concentración)

- **B1** (2463 eventos): 2005: 16, 2006: 20, 2007: 28, 2008: 876, 2009: 287, 2010: 13, 2011: 134, 2012: 24, 2013: 3, 2014: 15, 2015: 38, 2016: 49, 2017: 7, 2018: 44, 2019: 22, 2020: 448, 2021: 18, 2022: 185, 2023: 27, 2024: 26, 2025: 100, 2026: 83
- **B2** (468 eventos): 2005: 2, 2006: 9, 2007: 4, 2008: 155, 2009: 19, 2010: 6, 2011: 39, 2012: 13, 2013: 1, 2014: 1, 2015: 5, 2016: 13, 2017: 3, 2018: 17, 2019: 4, 2020: 45, 2021: 4, 2022: 39, 2023: 1, 2024: 8, 2025: 34, 2026: 46
- **B5** (1890 eventos): 2005: 6, 2006: 9, 2007: 15, 2008: 840, 2009: 215, 2010: 6, 2011: 104, 2012: 2, 2014: 1, 2015: 22, 2016: 41, 2018: 35, 2019: 3, 2020: 373, 2022: 134, 2023: 9, 2025: 68, 2026: 7
- **B7** (160 eventos): 2005: 1, 2006: 5, 2007: 1, 2008: 56, 2009: 5, 2010: 1, 2011: 18, 2012: 8, 2014: 1, 2015: 3, 2016: 2, 2018: 7, 2019: 1, 2020: 18, 2022: 9, 2023: 1, 2024: 3, 2025: 12, 2026: 8
- **C1** (1354 eventos): 2005: 28, 2006: 20, 2007: 25, 2008: 324, 2009: 135, 2010: 10, 2011: 29, 2012: 28, 2013: 16, 2014: 9, 2015: 27, 2016: 35, 2017: 18, 2018: 25, 2019: 34, 2020: 257, 2021: 8, 2022: 50, 2023: 33, 2024: 49, 2025: 112, 2026: 82
- **E1** (1564 eventos): 2008: 813, 2009: 281, 2020: 289, 2022: 106, 2025: 54, 2026: 21
- **E2** (264 eventos): 2008: 145, 2009: 18, 2020: 36, 2022: 27, 2025: 22, 2026: 16
- **E3** (558 eventos): 2005: 4, 2008: 202, 2009: 87, 2020: 63, 2022: 109, 2025: 50, 2026: 43
- **E4** (188 eventos): 2005: 2, 2008: 73, 2009: 28, 2020: 19, 2022: 32, 2025: 19, 2026: 15
- **E5** (229 eventos): 2008: 141, 2009: 12, 2020: 36, 2022: 18, 2025: 22
- **D16** (237 eventos): 2005: 5, 2006: 3, 2007: 8, 2008: 61, 2009: 8, 2010: 2, 2011: 14, 2014: 1, 2015: 3, 2016: 10, 2018: 8, 2019: 1, 2020: 40, 2022: 33, 2023: 11, 2025: 16, 2026: 13
- **D18** (177 eventos): 2005: 10, 2006: 7, 2007: 6, 2008: 26, 2009: 20, 2010: 5, 2011: 6, 2012: 5, 2013: 6, 2014: 3, 2015: 3, 2016: 3, 2017: 5, 2018: 3, 2019: 8, 2020: 21, 2021: 3, 2022: 6, 2023: 2, 2024: 4, 2025: 12, 2026: 13
- **X3** (521 eventos): 2001: 128, 2002: 120, 2003: 1, 2004: 8, 2008: 145, 2009: 18, 2020: 36, 2022: 27, 2025: 22, 2026: 16
- **X4** (1132 eventos): 2001: 305, 2002: 212, 2003: 32, 2004: 25, 2005: 4, 2008: 202, 2009: 87, 2020: 63, 2022: 109, 2025: 50, 2026: 43
- **X5** (404 eventos): 2001: 110, 2002: 85, 2003: 11, 2004: 10, 2005: 2, 2008: 73, 2009: 28, 2020: 19, 2022: 32, 2025: 19, 2026: 15

## E3 (IT, día <=-5% y 5 ses. <=-10%, SMH hundido) por episodio

| Año | n | gana 3s | media 3s | gana 10s | media 10s |
|---|---|---|---|---|---|
| 2005 | 4 | 50% | +0.8% | 50% | +0.4% |
| 2008 | 202 | 51% | +0.0% | 49% | -1.1% |
| 2009 | 87 | 57% | +1.3% | 55% | +3.7% |
| 2020 | 63 | 68% | +4.4% | 98% | +16.4% |
| 2022 | 109 | 40% | -0.3% | 55% | +1.9% |
| 2025 | 50 | 48% | +2.5% | 70% | +5.4% |
| 2026 | 43 | 95% | +8.3% | 33% | -2.2% |

## X4 (IT, día <=-5% y 5 ses. <=-10%, SMH hundido, desde 2001) por año

| Año | n | gana 3s | media 3s | gana 10s | media 10s |
|---|---|---|---|---|---|
| 2001 | 305 | 55% | +1.0% | 55% | +3.4% |
| 2002 | 212 | 59% | +2.6% | 49% | +2.7% |
| 2003 | 32 | 62% | +1.7% | 41% | -3.4% |
| 2004 | 25 | 44% | -0.1% | 80% | +5.8% |
| 2005 | 4 | 50% | +0.8% | 50% | +0.4% |
| 2008 | 202 | 51% | +0.0% | 49% | -1.1% |
| 2009 | 87 | 57% | +1.3% | 55% | +3.7% |
| 2020 | 63 | 68% | +4.4% | 98% | +16.4% |
| 2022 | 109 | 40% | -0.3% | 55% | +1.9% |
| 2025 | 50 | 48% | +2.5% | 70% | +5.4% |
| 2026 | 43 | 95% | +8.3% | 33% | -2.2% |

## Episodio actual (señales B0 desde el 1-oct-2026; horizontes medibles con datos hasta el 24-nov)

Mismo cálculo (apertura siguiente a apertura h sesiones después, 0,10% de costes), sin exigir 10 sesiones. Separación mínima entre eventos de una acción: 4 sesiones. Es UN solo episodio: muy informativo del comportamiento reciente, nada de estadística.

| Grupo / semana de la señal | n | gana 1s | media 1s | gana 3s | media 3s | gana 5s | media 5s | gana 10s | media 10s |
|---|---|---|---|---|---|---|---|---|---|
| Todas las B0 | 249 | 36% (n=237) | -1.7% | 59% (n=177) | +1.3% | 62% (n=169) | +1.1% | 36% (n=164) | -3.2% |
| Solo IT | 144 | 33% (n=137) | -2.2% | 54% (n=102) | +0.3% | 52% (n=100) | -0.5% | 27% (n=100) | -5.4% |
| Solo B1 (3 meses <=-30% y bajo media 200) | 53 | 14% (n=49) | -3.2% | 70% (n=27) | +6.6% | 88% (n=25) | +8.2% | 42% (n=24) | +3.9% |
| Semana 2026-10-05/2026-10-11 | 5 | 60% (n=5) | -0.5% | 40% (n=5) | -1.4% | 20% (n=5) | -6.7% | 20% (n=5) | -8.1% |
| Semana 2026-10-12/2026-10-18 | 36 | 50% (n=36) | -0.4% | 39% (n=36) | -1.6% | 44% (n=36) | -1.6% | 36% (n=36) | -3.3% |
| Semana 2026-10-19/2026-10-25 | 18 | 78% (n=18) | +1.0% | 89% (n=18) | +7.8% | 78% (n=18) | +3.8% | 22% (n=18) | -6.9% |
| Semana 2026-10-26/2026-11-01 | 22 | 36% (n=22) | -1.6% | 68% (n=22) | +0.3% | 41% (n=22) | -0.7% | 45% (n=22) | -1.3% |
| Semana 2026-11-02/2026-11-08 | 83 | 41% (n=83) | -1.0% | 67% (n=83) | +2.5% | 78% (n=83) | +3.3% | 37% (n=83) | -2.5% |
| Semana 2026-11-09/2026-11-15 | 1 | 100% (n=1) | +0.6% | 0% (n=1) | -2.0% | 0% (n=1) | -9.9% |  |  |
| Semana 2026-11-16/2026-11-22 | 83 | 11% (n=72) | -3.9% | 8% (n=12) | -5.7% | 0% (n=4) | -10.8% |  |  |
| Semana 2026-11-23/2026-11-29 | 1 |  |  |  |  |  |  |  |  |

## B1 (todas) por año

| Año | n | gana 3s | media 3s | gana 10s | media 10s |
|---|---|---|---|---|---|
| 2005 | 16 | 50% | +0.3% | 50% | +1.2% |
| 2006 | 20 | 75% | +2.6% | 55% | +2.8% |
| 2007 | 28 | 71% | +1.8% | 50% | +0.6% |
| 2008 | 876 | 57% | +2.1% | 54% | +1.2% |
| 2009 | 287 | 55% | +1.6% | 59% | +7.7% |
| 2010 | 13 | 69% | +1.7% | 62% | +4.2% |
| 2011 | 134 | 75% | +4.3% | 57% | +2.3% |
| 2012 | 24 | 58% | +0.4% | 46% | -0.4% |
| 2013 | 3 | 67% | +3.6% | 100% | +4.1% |
| 2014 | 15 | 47% | -0.8% | 27% | -3.6% |
| 2015 | 38 | 66% | +0.7% | 61% | +2.3% |
| 2016 | 49 | 53% | +0.4% | 67% | +3.9% |
| 2017 | 7 | 57% | +0.8% | 71% | +1.6% |
| 2018 | 44 | 50% | +0.4% | 82% | +7.3% |
| 2019 | 22 | 55% | +2.4% | 45% | -0.1% |
| 2020 | 448 | 53% | +1.0% | 66% | +5.3% |
| 2021 | 18 | 61% | +4.2% | 78% | +4.7% |
| 2022 | 185 | 54% | +2.0% | 58% | +2.7% |
| 2023 | 27 | 56% | +0.2% | 59% | +1.2% |
| 2024 | 26 | 65% | +3.8% | 77% | +9.9% |
| 2025 | 100 | 62% | +4.2% | 77% | +7.3% |
| 2026 | 83 | 70% | +4.5% | 49% | +2.3% |
