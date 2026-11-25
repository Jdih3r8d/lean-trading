# The final answer to the user: a plain-language playbook first

The user who commissioned the TSLA study said, after receiving tables, code and files: "Yo pensaba que tú me ibas a
decir, esa estrategia funciona tal que así y así. ¿Yo para qué quiero tanto código?" They wanted to know what to DO.
Code, LEAN algorithms and research folders are evidence and automation; they come after the playbook, briefly.

Write in the user's language, no jargon (explain "media móvil de 10 días" once, avoid "Sharpe", "IS/OOS", "PBO" in the
main text, or translate them into plain words: "rentabilidad por unidad de riesgo", "datos que no se usaron para elegir").

## Template (adapt the wording; keep the order)

1. **Una frase de veredicto**: what the strategy is and whether it beats simply holding the stock (be honest: often it
   wins on risk, not on raw return).
2. **Lo que necesitas**: the charts/indicators to look at (e.g. daily chart with 10- and 30-day simple moving averages,
   any free platform), when to look (after the close), what order to place (market order at the next open), and how to
   split the money between rules.
3. **Una sección por regla**, each with:
   - **Comprar**: the exact condition, in words and numbers.
   - **Vender**: the exact exit.
   - **Qué esperar**: trades per year, win rate in "X de cada Y", typical win and loss, average return per trade,
     holding time; plus any execution caveat (e.g. "hay que comprar justo en la apertura siguiente").
4. **Ejemplo con dinero** (e.g. 10.000 € split in halves) so sizing is unambiguous; state the maximum exposure.
5. **Qué esperar de verdad**: realistic yearly return range and worst drawdown AFTER the panel's haircut, how it
   compares with holding the stock in booms and crashes (one example year of each), flat periods.
6. **Ahora mismo**: the state of every rule at the last close in the data and exactly what to watch next (price levels,
   upcoming event dates).
7. One line: not financial advice; start small.
8. Only then, briefly: where the code/algorithm/report live and what they are for (proof, automation in LEAN), offered,
   not imposed.

Keep it short enough to read on a phone. Numbers must match the reviewed write-up exactly.
