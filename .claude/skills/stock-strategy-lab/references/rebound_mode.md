# Modo rebote: de una captura de "las que más caen hoy" a un plan de compra y venta

Objetivo: decirle al usuario cuáles de las acciones que más han caído tienen más probabilidad de rebotar, cuánto poner
en cada una, cuándo comprar y cuándo vender, y por qué descartar el resto. Sin LEAN ni el estudio completo.

Dos variantes:
- **Profunda (por defecto)**: filtro numérico con código + un workflow de agentes (`workflows/rebound_deep.js`):
  - primero, un agente de contexto de mercado (y de noticias de la lista) y otro de tasas base de las situaciones de
    hoy;
  - después, por cada finalista, un analista (causa del movimiento, histórico de situaciones parecidas de esa acción
    y de sus comparables, catalizadores y probabilidad estimada) y un escéptico que intenta refutarlo. Las que caen
    se miran con la lente de rebote y las que suben con la de continuación;
  - un juez final que ordena todas, arma el plan y dice qué hacer si ya se tienen.

  Con 5 finalistas son ~13 agentes y 30-60 minutos; con 10, ~23 agentes y 1-1,5 horas (en una máquina de 4 CPU el
  workflow solo ejecuta 2 agentes a la vez). El usuario tiene Claude Max y prefiere esta variante; úsala siempre que
  no pida otra cosa.
- **Rápida** (solo si el usuario la pide: «rápido», «sin agentes»): filtro numérico + una búsqueda de noticias por
  finalista, hecho por ti. Minutos y pocos tokens.

## Por qué estos criterios (y su límite)
- **Tasas base** (`references/rebound_base_rates.md`, ~500 acciones del S&P 500 desde 2005, vender 3 sesiones
  después):
  - un día cualquiera gana el 52% de las veces;
  - tras caer >=10% en 5 sesiones, el 55%;
  - si además sigue por encima de su media de 200 sesiones, el 59%;
  - las caídas de 15-20% y de más del 20% rebotan peor (51% y 47%).

  La ventaja existe pero es pequeña: díselo así al usuario y no prometas porcentajes altos. Regenera la tabla de vez en
  cuando con `scripts/rebound_base_rates.py`.
- El estudio de TSLA encontró que **comprar tras una caída fuerte de 5 sesiones (12% o más) y vender 3 sesiones
  después** fue de las reglas que mejor aguantaron (p≈0,02 fuera de muestra), sobre todo cuando el mercado estaba
  nervioso, y que dependía de comprar en la apertura siguiente.
- La literatura sobre reversión a corto plazo dice lo mismo en general (las caídas bruscas de días tienden a corregirse
  en parte), pero también que **las acciones que llevan meses cayendo siguen cayendo** (momentum), que **las caídas por
  malas noticias fundamentales** (resultados, guía rebajada) no suelen revertir (en TSLA las reacciones muy negativas a
  resultados no rebotaron) y que las acciones pequeñas y poco líquidas son trampas.
- **Estos criterios son provisionales**: se validaron en una sola acción. Díselo al usuario en la respuesta y
  recomiéndale, cuando quiera poner dinero serio, el estudio de rebote en muchas acciones sin sesgo de supervivencia
  (el método del modo estudio adaptado a un universo como el S&P 500, con su lista histórica de componentes).

## Procedimiento (los pasos 1-2 son comunes; la variante profunda sigue en el paso 3P)
1. **Lee la captura.** Extrae para cada fila: ticker (o nombre), bolsa, variación de hoy en %, precio si aparece, y la
   hora o si el mercado está cerrado. Si el bróker muestra nombres y no tickers, tradúcelos al ticker y, si hay duda,
   pregunta antes de seguir. Ignora ETFs apalancados, warrants y acciones de menos de 5 $ (dilo en una línea). Si la
   captura es ilegible o cortada, pide otra. Fíjate en cuatro cosas (las cuatro pasaron el 25-nov-2026):
   - **¿Es la lista del propio usuario?** Si entre las "mejores" hay subidas pequeñas o un 0,00%, el universo es
     pequeño: es su cartera o su lista de seguimiento. Entonces pregunta por TODAS ("¿cuáles van a subir?"): analiza
     también las que suben (grupo `sube`) y di en cada una qué hacer si ya la tiene.
   - **¿A qué hora es?** Con una captura en horario europeo antes de las 15:30 de España, los % de las acciones de
     EE. UU. son de LS Exchange/Tradegate frente al cierre de ayer: preapertura, provisionales. Mira también festivos y
     medias sesiones de Nueva York (Acción de Gracias, Navidad) y pásalo todo en `contexto`.
   - **¿Hay valores no estadounidenses?** No están en los espejos de datos (el filtro dirá SIN DATOS), pero en la
     variante profunda se analizan con búsquedas web y comparables de EE. UU. si el usuario pregunta por ellos. En la
     rápida, ignóralos y dilo.
   - Un 0,00% exacto en un valor volátil suele ser un fallo de la línea del bróker (Abivax cotizaba en París +2-4%).
2. **Ejecuta el script** con todo lo extraído, cada acción como `TICKER:%hoy@precio` (es barato: segundos y sin tokens
   de razonamiento):
   `pip install -q pandas_market_calendars 2>/dev/null; python3 <skill_dir>/scripts/rebound_screen.py MU:-11.01@629.79 AMD:-8.86@413.27 ... [--after-close]`
   Con precio y % juntos el script detecta si sus datos ya incluyen el movimiento de la captura (fuente ya
   actualizada o captura antigua) y no lo cuenta dos veces; si el precio y el % no cuadran, lo avisa.
   Usa `--after-close` si la captura es posterior a las 16:00 de Nueva York (22:00 en España peninsular); si no, el
   dato de hoy es provisional y el plan será "si al cierre sigue así, compra mañana en la apertura".
   **Datos desfasados:** los espejos no se actualizan a la vez. Si a un ticker le falta la sesión anterior, el script
   no pega el % de hoy sobre un cierre viejo y lo marca `REVISAR` (`datos_desfasados`, `sesiones_que_faltan`): sus
   cifras de 5 sesiones y precio son solo orientativas y hay que reconstruir los cierres recientes con búsquedas web
   antes de decidir. Pasar el precio (`TICKER:%@precio`) ayuda, pero no arregla las sesiones que faltan.
3P. **Variante profunda**:
   - Ejecuta el filtro con `--out <scratchpad>/rebote/screen.json`.
   - Elige finalistas: las CANDIDATA, VIGILAR y REVISAR del filtro, máximo 6 por puntuación, más las que el usuario
     pida expresamente (si pregunta por toda la lista, todas, hasta 10). Las que suben van con `grupo: "sube"`.
   - Lanza el workflow:
     `Workflow({scriptPath: "<skill_dir>/workflows/rebound_deep.js", args: {skill_dir: "<skill_dir>",
     work: "<scratchpad>/rebote", screen_json: "<scratchpad>/rebote/screen.json",
     finalists: ["SNOW", {ticker: "HBX", grupo: "cae", notas: "Bolsa de Madrid, sin datos en los espejos"},
                 {ticker: "ZEAL", grupo: "sube", notas: "Nasdaq Copenhague"}],
     captura: "<lo leído>", after_close: false,
     contexto: "<hora de la captura en Nueva York y España, festivos, qué datos están desfasados, si parece su cartera>",
     usuario: "<dinero para rebotes u otras notas, si las dio>"}})`
   - **Búsquedas web:** el cupo es de ~200 por sesión y lo comparten todos los agentes. El workflow reparte
     `search_budget` (180 por defecto) entre mercado, analistas, escépticos y juez, y pasa a los analistas las
     noticias que ya encontró el agente de mercado. No lances otro workflow con búsquedas en la misma sesión sin
     bajar `search_budget`.
   - Avisa al usuario de cuánto tardará (30-60 minutos con 5 finalistas; 1-1,5 horas con 10).
   - **Si se corta** (límite de uso de la cuenta, agentes con error): mira el journal, espera a que se restablezca el
     límite y reanuda con `Workflow({scriptPath, resumeFromRunId})`: los agentes terminados salen de caché. Si hace
     falta cambiar algo, cambia solo el prompt del juez (lo último), para no invalidar la caché de los demás.
   - Al terminar, comprueba tú las fechas del plan con `pandas_market_calendars` y que el juez no se contradiga con
     los escépticos, y responde con la plantilla usando el resultado del juez (y los argumentos del analista y del
     escéptico cuando ayuden a explicar). Salta al paso 5.

   Si la herramienta Workflow no existe en la sesión, lanza los mismos prompts con la herramienta Agent, como mucho 2
   a la vez y en este orden: primero el agente de mercado (y, si quieres, el de tasas base); después, por cada
   finalista, un analista con el JSON del mercado (sobre todo `noticias_de_la_lista`) y su presupuesto de búsquedas,
   y luego su escéptico; al final, un juez (o haz tú de juez). Reparte las búsquedas como `searchRule` del workflow:
   ~20 para el mercado, ~8 para el juez y el resto a partes iguales entre las acciones (60% analista, 40% escéptico).
3. **Variante rápida. Comprueba la noticia solo de las finalistas** (las CANDIDATA mejor puntuadas, como mucho 5; una REVISAR solo si al reconstruir sus cierres recientes cumple la regla): una búsqueda web por
   acción, "<ticker> stock falls why <fecha>". Descarta la acción si la caída se debe a: resultados o previsiones
   peores de lo esperado, recorte de dividendo, fraude o investigación, quiebra o reestructuración, ampliación de
   capital, rechazo regulatorio, pérdida de un cliente clave o rebaja de rating de crédito. Mantenla si la caída es
   por el mercado general, rotación sectorial, un comentario de un analista, una noticia de un competidor o pánico sin
   noticia concreta. Si no encuentras el motivo, dilo y baja su prioridad.
4. **Decide**: como mucho 3-5 compras, priorizando el score del script, que sigan cerca o por encima de su media de 200
   sesiones y con evidencia propia positiva (sus caídas pasadas rebotaron más que su deriva normal). Si el script dice
   `mercado_en_panico=True`, los rebotes suelen ser mayores pero más arriesgados: mismas reglas con la mitad de tamaño.
5. **Responde** con la plantilla de abajo, en el idioma del usuario, sin jerga.
6. **Guarda el informe en el repositorio**: el scratchpad y los journals se pierden al cerrar la sesión y el usuario
   quiere poder volver a leerlo. Crea `Research/Rebotes/AAAA-MM-DD_<nombre>/` con:
   - `README.md`: la respuesta de la plantilla, con la tabla de la captura (nombre, ticker, bolsa, %), el ranking, qué
     vigilar, el mercado, advertencias y cómo se hizo (ver `Research/Rebotes/2026-11-25_TopMovers/` como ejemplo);
   - `detalle_agentes.md`: `python3 <skill_dir>/scripts/rebound_report.py <journal.jsonl> <carpeta>/detalle_agentes.md`
     (todo lo que devolvió cada agente, sin editar);
   - `tasas_base.md` si el workflow la generó. Nunca precios descargados de terceros.

   Haz commit y push en la rama de la sesión y dile al usuario dónde verlo (la ruta en GitHub).

## Plantilla de respuesta
1. **Veredicto en una frase**: cuántas comprarías de la lista (puede ser ninguna: dilo sin rodeos) y la advertencia
   de que los criterios son provisionales. Si la lista parece la cartera del usuario, dilo.
1b. **Ranking** (si se analizaron también las que suben, o la lista es la del usuario): una tabla con todas, de más a
   menos probabilidad de subir, con la probabilidad a 3 y 10 sesiones, el porqué en una frase y qué hacer si ya la
   tiene (mantener, reducir o vender, con niveles concretos).
2. **Compraría** (una línea por acción): ticker y nombre, por qué (caída de X% en 5 días, sigue por encima de su
   tendencia, sin mala noticia: motivo de la caída) y SIEMPRE tres porcentajes de acierto:
   - **la regla en general** (de `rebound_base_rates.md`, en la situación más parecida, avisando de que es un techo
     optimista por sesgo de supervivencia);
   - **esta acción en el pasado** ("de N caídas parecidas, ganó en X: Y%"; si N < 10, dilo);
   - **la probabilidad estimada ahora**, explicando en una frase por qué sube o baja respecto a los históricos.
3. **Cuánto**: divide el dinero que el usuario dedica a rebotes entre las elegidas, a partes iguales, sin pasar de un
   20-25% de ese dinero por acción (la mitad si el mercado está en pánico). Ejemplo con 1.000 €.
4. **Cuándo comprar**: en la apertura de la próxima sesión (indica la fecha, la hora de Nueva York y la de España), con
   orden a mercado en la apertura. Si la captura es de antes del cierre: "si al cierre sigue cayendo al menos lo mismo".
5. **Cuándo vender**: en la apertura N sesiones después de comprar (N = el horizonte del juez; 3 en la variante
   rápida), con la fecha exacta, pase lo que pase (en TSLA los stops y los objetivos de beneficio no mejoraban la
   regla).
6. **Descartadas**: una línea por acción con el motivo (cuchillo cayendo, mala noticia, poco líquida, caída pequeña).
7. **Qué esperar**: la mayoría de rebotes son pequeños; alguna vez una sigue cayendo; no meter más dinero del que se
   está dispuesto a perder en una operación.
8. Una línea: no es asesoramiento financiero.

## Si el usuario quiere gastar pocos tokens (variante rápida)
- Manda la captura después del cierre de Nueva York (datos definitivos, sin "si al cierre...").
- Basta una captura legible con ticker y % del día; no hace falta abrir cada acción.
- No hagas más de una búsqueda web por finalista ni análisis adicionales salvo que el usuario los pida.

## Errores ya vistos (25-nov-2026: captura "Top Movers" de 10 valores, EE. UU. y Europa)
- **Datos desfasados.** Los espejos de GitHub terminaban en fechas distintas (24-nov, 23-nov, 20-nov, 18-nov y 17-nov). El
  filtro antiguo pegaba el % de hoy sobre el último cierre que tuviera y daba caídas de 5 sesiones falsas (Navitas
  −28% cuando era −15%; Penguin −9% cuando era −18%). Ahora el filtro lo marca REVISAR y no inventa la caída.
- **Cupo de búsquedas agotado.** 23 agentes gastaron las ~200 búsquedas de la sesión. Los analistas de Zealand, SES,
  Abivax e Insmed no pudieron verificar nada, y el de Insmed no vio que Sanofi la compraba a 175 $ (lo vio el agente
  de mercado; el escéptico lo corrigió). Ahora hay presupuesto por agente y el mercado va primero y comparte sus
  noticias.
- **La captura era la lista del usuario**, con valores que subían y europeos (HBX en Madrid, Zealand en Copenhague,
  SES y Nanobiotix en París). Preguntaba "cuáles van a subir": hubo que analizar también las que suben y decir qué
  hacer si ya las tiene.
- **Un 0,00% era un fallo del bróker** (Abivax subía en París) y los % de EE. UU. eran de preapertura en LS Exchange.
- **Límite de uso** a mitad del workflow: 5 agentes fallaron; se reanudó con `resumeFromRunId` y los 18 terminados
  salieron de caché.
- **El juez trabajó con el mercado ya abierto** (4 horas después de la captura): conviene que mire cómo van las
  acciones en la sesión antes de fijar la condición de entrada.
- Resultado de aquel día: ninguna compra; las diez entre 46% y 54%. En un desplome sectorial (IA y semiconductores),
  las cuatro del sector eran la misma apuesta y sus rebotes se deshacían en días.
