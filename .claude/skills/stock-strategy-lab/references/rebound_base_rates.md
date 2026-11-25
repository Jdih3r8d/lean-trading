# Tasas base del modo rebote (generado por scripts/rebound_base_rates.py)

Universo: 517 acciones (componentes actuales del S&P 500), datos diarios desde 2005-01-01 hasta 2026-11-06. Operación: comprar en la apertura siguiente a un cierre con caída de 5 sesiones y vender en la apertura 3, 5 o 10 sesiones después, con 0,10% de costes. Cada celda: **% de operaciones ganadoras / rentabilidad media**.

**Sesgo de supervivencia:** solo incluye empresas que siguen hoy en el índice; las que se hundieron y salieron no están. Por eso estas cifras son un techo optimista del acierto real. Úsalas como referencia, no como promesa.

| Situación | Operaciones | 3 sesiones | 5 sesiones | 10 sesiones |
|---|---|---|---|---|
| Cualquier día (sin señal, referencia) | 244812 | 52% / +0.1% | 54% / +0.2% | 54% / +0.5% |
| Caída de 5 sesiones >= 10% | 10730 | 55% / +0.7% | 54% / +0.8% | 56% / +1.4% |
| Filtro del modo rebote (>=10%, precio >= 5 $, >= 20 M$/día, 3 meses > -40%) | 8858 | 55% / +0.5% | 54% / +0.5% | 56% / +1.0% |
|   … y por ENCIMA de su media de 200 | 2350 | 59% / +1.0% | 60% / +1.5% | 58% / +1.9% |
|   … y por DEBAJO de su media de 200 | 6508 | 53% / +0.3% | 52% / +0.1% | 55% / +0.6% |
|   … con el mercado (SPY) por ENCIMA de su media de 200 | 4154 | 54% / +0.4% | 54% / +0.8% | 54% / +0.8% |
|   … con el mercado (SPY) por DEBAJO (corrección o pánico) | 4704 | 55% / +0.5% | 53% / +0.2% | 57% / +1.1% |
| Caída >= 10% en una acción que ya llevaba -40% o peor en 3 meses | 952 | 58% / +3.0% | 55% / +3.3% | 61% / +5.9% |
| Filtro con caída de 8% a 10% | 14940 | 53% / +0.3% | 54% / +0.5% | 55% / +0.7% |
| Filtro con caída de 10% a 12% | 5193 | 56% / +0.6% | 54% / +0.7% | 56% / +0.8% |
| Filtro con caída de 12% a 15% | 2373 | 54% / +0.7% | 55% / +0.7% | 56% / +1.4% |
| Filtro con caída de 15% a 20% | 941 | 51% / -0.1% | 50% / -0.5% | 55% / +0.9% |
| Filtro con caída de 20% o más | 351 | 47% / -0.8% | 48% / -1.7% | 53% / +1.7% |

Tickers sin datos: 0.
