---
name: stock-strategy-lab
description: Dos modos para acciones de EE. UU. con datos diarios. (1) Modo rebote, en el que el usuario envía una captura de su bróker con las acciones que más caen hoy (o una lista de tickers); un filtro con código y agentes por acción (causa de la caída, histórico de caídas parecidas, escéptico y juez) deciden qué comprar, cuánto, cuándo vender y por qué se descarta el resto. (2) Modo estudio, de varias horas con subagentes, que busca una estrategia robusta para UNA acción con datos contrastados, motor auditado, 7 familias con validadores, panel escéptico y verificación en LEAN, explicada en lenguaje sencillo. Úsala para «analiza NVDA y dime cuándo comprar», «busca una estrategia para X», «¿cuáles de estas que han caído van a rebotar?», capturas de las que más bajan hoy, «find me a trading strategy for AAPL». NO para cotizaciones, noticias sueltas, explicar indicadores, un backtest ya definido, cripto, forex, futuros o intradía.
---

# Laboratorio de estrategias para una acción

## Elige el modo primero
- **Modo rebote**: el usuario manda una captura o lista de acciones que han caído mucho (o su lista de "Top Movers",
  con las que suben y las que bajan), o pregunta cuáles rebotarán o cuáles van a subir. Sigue SOLO `references/rebound_mode.md` y no sigas leyendo este archivo. Por defecto es la variante
  profunda: filtro con código + agentes de mercado, analista y escéptico por acción y un juez, en ~30-60 min. La
  variante rápida, sin agentes, solo si el usuario la pide.
- **Modo estudio** (varias horas, ~25 agentes): el usuario quiere una estrategia para una acción concreta. Es todo lo
  que sigue.

Esta skill reproduce, para cualquier acción, el proceso con el que se estudió TSLA en noviembre de 2026. El resultado
fue una estrategia de tres módulos con un Sharpe fuera de muestra de 1,56 frente a 0,89 de comprar y mantener,
verificada sesión a sesión en LEAN (ver `references/tsla_case.md`). El valor no está en una fórmula sino en la
disciplina:

- datos contrastados;
- un motor auditado antes de usarlo;
- parámetros elegidos solo con datos de entrenamiento (IS);
- cada hallazgo reproducido e intentado refutar por otro agente;
- expectativas recortadas con honestidad;
- una explicación final que el usuario pueda seguir sin leer código.

## Mapa

| Fase | Qué | Quién | Workflow | Tiempo en TSLA |
|---|---|---|---|---|
| 0 | Laboratorio y datos de la acción | tú | — | ~30 min |
| 1 | Auditoría del motor + datos auxiliares ∥ estudio clásico y referencia | 2 agentes ∥ tú | `phase1_audit_data.js` | ~30 min |
| 2 | Familias de estrategias + validadores | 7 + 7 agentes | `phase2_families.js` | ~85 min |
| 3 | Combinación + panel de desafío | tú + 4 agentes | `phase3_challenge.js` | ~15 + 32 min |
| 4 | Implementación y verificación en LEAN | tú | — | ~10 min + 3-5 min/ejecución |
| 5 | Entregable, revisión final y respuesta | tú + 2 agentes | `phase5_deliverable_review.js` | ~30 min |

Marcadores (usa siempre rutas absolutas, porque se incrustan en los prompts de los agentes):

- `<skill_dir>`: la carpeta de este archivo (scripts en `scripts/`, workflows en `workflows/`, guías en `references/`).
- `<T>`: el ticker.
- `<lab>`: `<scratchpad>/lab_<t>`. El scratchpad puede limpiarse; lo que valga se copia al repo en la fase 5.
- `<repo>`: raíz del repositorio LEAN, la carpeta con `QuantConnect.Lean.sln` y `Algorithm.Python/`. Si la sesión no
  tiene uno y el usuario quiere LEAN, clónalo con `git clone --depth 1 https://github.com/QuantConnect/Lean`; si no,
  sáltate la fase 4 y dilo.
- `<work>`: `/opt/lean_work` si ya existe `/opt/lean_work/py311` (lo prepara el script del entorno de nube del
  repo: LEAN compilado, venv y carpeta de datos; entonces no ejecutes `setup_lean.sh`). Si no existe,
  `<scratchpad>/lean_work`. Contiene el venv, los datos LEAN, las salidas y las revisiones. Nunca dentro del repo.
- `<Clase>`: nombre del algoritmo y de su archivo, p. ej. `NvdaTrendRegimeAlgorithm`.
- `<X>`: `<Ticker>Strategy`, la carpeta del entregable dentro de `Research/`.

**Herramienta Workflow.** Las fases 1, 2, 3 y 5 lanzan los scripts de `workflows/` con la herramienta `Workflow`. Si
no está entre tus herramientas, búscala con `ToolSearch` (`select:Workflow`). Si no existe, ejecuta los mismos prompts
con subagentes (herramienta Agent):

- copia el texto de cada `agent(...)` del `.js` y sustituye `${LAB}`, `${T}` y el resto de variables por sus valores;
- pide la salida con la forma del `schema` correspondiente;
- respeta el orden: `parallel` significa a la vez; en `pipeline`, el validador de cada familia empieza cuando termina
  su investigador. Como mucho 2 agentes a la vez.

## Antes de empezar

El modo completo dura unas 5-6 horas de reloj y usa unos 20-25 subagentes, con 4-5 millones de tokens. Si el usuario
pidió expresamente un estudio completo o a fondo, díselo en una línea y empieza. Si no (p. ej. «analiza NVDA y dime
cuándo comprar»), pregunta UNA vez y espera: «¿Estudio completo (~5-6 h, ~25 agentes, con verificación en LEAN) o
rápido (~2-3 h, sin LEAN)?».

**Modo rápido:**

- Fases 0 y 1 completas, sin `setup_lean.sh`.
- Fase 2 solo con `events`, `regime` y `vol`: `skip: ["implied", "sizing", "patterns", "ml"]`.
- Fase 3 completa (el panel es la principal defensa contra el sobreajuste), sin `repo` ni `lean_work` en los args.
- Sin fase 4.
- Fase 5: README sin la sección LEAN, revisión con `skip_code_review: true` y respuesta final normal.

Pregunta solo lo que no puedas deducir. Responde al usuario en su idioma y cuéntale lo esencial al terminar cada fase,
en una o dos frases.

## Fase 0 · Laboratorio y datos de la acción (tú)

1. Ejecuta `bash <skill_dir>/scripts/new_lab.sh <T> <lab> [is_end]`.
   - IS debe cubrir aproximadamente la primera mitad de la historia y terminar el 31 de diciembre; OOS es todo lo
     posterior y REC son los últimos ~3 años.
   - Si aún no conoces la historia, créalo sin `is_end`, construye `main.csv` y vuelve a ejecutarlo con el `is_end` que
     sugiere `check_data.py`. No sobrescribe el harness.
2. Construye `<lab>/data/main.csv` (date,open,high,low,close,volume) siguiendo `references/data_sources.md`.
   - Las APIs financieras suelen estar bloqueadas; los espejos CSV de GitHub funcionan.
   - Contrasta al menos dos fuentes independientes.
   - Si la acción paga dividendos relevantes (más de ~0,5% al año), haz `main.csv` ajustado también por dividendos,
     con una columna `adj_factor` (ver esa guía).
3. Ejecuta `python3 <skill_dir>/scripts/check_data.py <lab> <otras fuentes...>`.
   - Detecta filas corruptas (p. ej. open/high/low copiados del día anterior), splits sin ajustar y discrepancias.
   - Las líneas "scale-free" sirven para fuentes con otro ajuste.
   - Fija `is_start` y avisa si IS u OOS quedan cortos.
   - Repara solo con fuentes realmente independientes.
4. Escribe en `<lab>/data/splits.txt` **todas** las fechas de split, con el formato `AAAA-MM-DD:ratio,...`: la primera
   sesión que ya cotiza dividida, confirmada con precios sin ajustar. NVDA tiene 6. Documenta `main.csv`, sus fuentes,
   las reparaciones y los splits en `<lab>/data/DATA_NOTES.md`.
5. Haz 2-3 búsquedas web de contexto: últimos resultados, noticias y fecha del próximo informe.

## Fase 1 · Auditoría y datos auxiliares (agentes) ∥ estudio clásico (tú)

```
Workflow({scriptPath: "<skill_dir>/workflows/phase1_audit_data.js",
          args: {lab: "<lab>", ticker: "<T>", skill_dir: "<skill_dir>",
                 market_etfs: ["QQQ", "SPY", "<ETF sectorial si aplica, p. ej. SMH o XLE>"],
                 extra_data_goals: "<opcional: eventos propios de la empresa>"}})
```

- Un agente audita `harness.py`/`engine.py` con tests sintéticos. En TSLA encontró 5 errores reales, ya corregidos;
  audita igualmente, porque el código y los datos cambian.
- Otro agente consigue: ETFs de mercado con versión ajustada por dividendos, familia VIX, calendario de resultados con
  horas de la SEC, otros eventos, volatilidad implícita y vencimientos de opciones. Añade sus secciones a
  `DATA_NOTES.md`.

Mientras tanto, tú:

- Ejecuta `python3 <skill_dir>/scripts/classic_sweep.py <lab>`: unas 6.000 reglas clásicas en segundos. Léelo con las
  pautas de su docstring; la pregunta clave es si las reglas superan la simple deriva alcista de la acción.
- Elige la **referencia** solo con IS. Un buen punto de partida es un módulo de tendencia y otro de
  reversión/capitulación poco correlacionados, al 50/50 (`harness.trend_capitulation_weights`, re-ajustado en IS
  buscando una meseta, no un pico).
- Guarda `data/baseline_weights.csv` (date,weight) y `data/BASELINE.md`, con las reglas, las cifras de IS/OOS/REC/año
  actual, las de comprar y mantener (`perf(buy_and_hold(df), lo, hi)`) y lo que no funcionó.
- Si habrá LEAN y no existe `/opt/lean_work/py311`, ejecuta en segundo plano
  `bash <skill_dir>/scripts/setup_lean.sh <repo> <work>` (unos 5 minutos de compilación, casi sin tokens).

Al terminar el workflow:

1. Corrige `<lab>/harness.py`/`engine.py` con tests en `<lab>/audit/`.
2. Si cambian, vuelve a ejecutar el estudio clásico y regenera la referencia ANTES de las familias.
3. Mueve los archivos con errores conocidos a `data/superseded/`.
4. Añade a `PROTOCOL.md` el momento de publicación de cada dato (p. ej. el VIX cierra a las 16:15 ET: solo se puede
   ejecutar en la apertura siguiente).
5. Anota las correcciones del harness para proponer al final llevarlas a `<skill_dir>/scripts/`.

## Fase 2 · Familias de estrategias, cada una con validador

```
Workflow({scriptPath: "<skill_dir>/workflows/phase2_families.js",
          args: {lab: "<lab>", ticker: "<T>",
                 context: "<resumen del estudio clásico; reglas y cifras de la referencia; comprar y mantener>",
                 skip: [], extra_scope: {}}})
```

Hay 7 familias por defecto (`vol`, `implied`, `events`, `regime`, `sizing`, `patterns`, `ml`). Cada una pasa por un
validador que la reimplementa desde el texto, busca *look-ahead* e intenta refutarla.

- Quita las que no apliquen con `skip`: p. ej. `implied` si no hay datos de opciones ni un índice de volatilidad
  relevante.
- Adapta los alcances con `extra_scope`: p. ej. tipos de interés para un banco.

## Fase 3 · Combinar (tú) y panel de desafío

1. Reconstruye tú mismo los componentes con evidencia en `<lab>/lead/components.py`, comprueba que coinciden con los
   `cand_*.csv` de los agentes (diferencia 0) y guarda `lead/w_<nombre>.csv` para cada componente y combinación.
2. Orden de preferencia:
   1. componentes **confirmados** por su validador;
   2. **débiles pero robustos** a un día de retraso y a perturbaciones, sobre todo si no añaden parámetros (p. ej.
      reutilizar los 10/30 de la tendencia en el ETF de mercado);
   3. nunca los frágiles: dependen de 3 episodios o mueren con un día de retraso.

   Combinar muchos débiles sube el Sharpe IS y baja el OOS.
3. Evalúa pocas combinaciones: referencia, referencia + confirmados, y referencia + confirmados + el mejor robusto. Mira
   IS/OOS/REC/año actual, estrés de 15 pb, un día de retraso, caída máxima y operaciones por módulo. Elige una candidata
   y una alternativa más sencilla (*fallback*).
4. Escribe `<lab>/lead/BRIEF.md`, autosuficiente:
   - la historia y el número total de configuraciones, **recalculado sumando los `configs_tested` de cada familia** (en
     TSLA un brief sumó mal y el panel heredó el error);
   - los veredictos de los validadores;
   - las definiciones exactas de componentes, candidata y fallback;
   - las rutas de `lead/`;
   - tus cifras de referencia, fallback, candidata y comprar y mantener, con estrés y retraso.
5. Lanza el panel. Omite `repo` y `lean_work` si no ejecutaste `setup_lean.sh`:

```
Workflow({scriptPath: "<skill_dir>/workflows/phase3_challenge.js",
          args: {lab: "<lab>", ticker: "<T>", skill_dir: "<skill_dir>", brief_file: "<lab>/lead/BRIEF.md",
                 repo: "<repo>", lean_work: "<work>"}})
```

Son cuatro agentes:

- un optimizador que intenta superar a la candidata con alternativas pre-registradas;
- un escéptico estadístico: bootstrap, Sharpe deflactado, *reality check*, PBO y Monte Carlo;
- uno de implementación: reimplementación sesión a sesión y diseño para LEAN;
- uno de régimen: años, crisis, decaimiento y perturbaciones conjuntas.

**Regla de decisión:**

- Si 3 o 4 dicen `adopt`/`adopt_with_changes`, adopta la candidata.
- Si la mayoría dice `prefer_alternative` o `reject`, adopta el fallback (o la referencia).
- Como mucho UNA ronda de cambios de reglas: reevalúa tú y relanza solo al agente que lo pidió.
- Si solo piden cambiar expectativas, congela la especificación: más ajustes son sobreajuste.

**Resultado negativo:** si nada supera de forma robusta a la referencia y la referencia no mejora a comprar y mantener
ni en Sharpe OOS ni en caída máxima, dilo en la primera frase de la respuesta. Entrega la regla más simple que sí
aporte (o recomienda mantener la acción) y omite LEAN salvo que el usuario lo pida.

## Fase 4 · LEAN

Hazla si el repositorio es LEAN o el usuario quiere automatizar. Sigue `references/lean.md`:

1. Convierte cada símbolo con `scripts/to_lean_data.py` en `<work>/leandata`, nunca en el `Data/` versionado:
   - la acción con `--splits $(cat <lab>/data/splits.txt)`; revisa los precios sin ajustar que imprime alrededor de
     cada split;
   - los ETFs con sus `*_adj.csv`, empezando un año antes.
2. Copia `assets/reference_lean_algorithm_tsla.py` a `<repo>/Algorithm.Python/<Clase>.py` y cambia solo lo específico:
   - el prefijo `F3_` por `STRAT_`;
   - las fechas, los símbolos y el *benchmark*;
   - el calendario de eventos;
   - las reglas y constantes de la clase de estado;
   - la cabecera.

   Si el escéptico de implementación escribió un diseño, síguelo.
3. Ejecuta en modo `close` y luego en modo `morning` con los comandos de `references/lean.md`
   (`STRAT_MODE`, `STRAT_SLIPPAGE=0.0005`, `STRAT_OUT`), y concilia con `scripts/reconcile_lean.py`.
4. La meta es **0 diferencias de peso** en todas las sesiones, el mismo resultado en ambos modos, y que los arranques a
   mitad de historia reconstruyan el estado.

## Fase 5 · Entregable, revisión final y respuesta

1. Prepara `Research/<X>/` en el repo:
   - `harness.py`, `engine.py` y `PROTOCOL.md`;
   - un script de la estrategia final que imprima cifras, operaciones por módulo y estado actual;
   - un `fetch_data.py` con fecha de corte fija;
   - los calendarios de eventos;
   - `results/`;
   - un README en el idioma del usuario con: reglas exactas, resultados por periodo, robustez (estrés, retraso, LEAN),
     rentabilidad por operación indicando la base (por módulo o por cuenta), expectativa realista con los rangos del
     panel, metodología, qué no funcionó, riesgos y cómo reproducir.

   No subas datos descargados de terceros.
2. Haz commit en la rama de trabajo de la sesión, nunca en la principal sin permiso expreso, y push, si el usuario o
   las instrucciones de la sesión piden el código en el repo. Si no, deja los archivos y dilo en una línea.
3. Lanza la revisión:

```
Workflow({scriptPath: "<skill_dir>/workflows/phase5_deliverable_review.js",
          args: {repo: "<repo>", work: "<work>", skill_dir: "<skill_dir>", lab: "<lab>", ticker: "<T>",
                 algorithm_class: "<Clase>", readme: "<repo>/Research/<X>/README.md", research_dir: "<repo>/Research/<X>",
                 research_weights: "<lab>/lead/w_<final>.csv", lean_out: "<work>/lean_out", lean_log: "<work>/lean_close.log",
                 env_prefix: "STRAT_", evidence_paths: ["<journals de las fases 1-3>"]}})
```

   Sin LEAN, pasa `skip_code_review: true` y omite `work`, `algorithm_class`, `lean_out`, `lean_log` y `env_prefix`.
4. Revisa el `patch.diff` del revisor de código antes de aplicarlo, vuelve a correr LEAN y la conciliación, y corrige
   el README según el fact-check. En TSLA hubo conteos mal sumados, frases absolutas falsas y expectativas mal
   atribuidas. Haz commit y push.
5. **Responde con el plan en lenguaje sencillo** siguiendo `references/final_answer.md`: veredicto, qué mirar, cada
   regla con comprar/vender/qué esperar, ejemplo con dinero, expectativa realista, qué hacer hoy y, solo al final y en
   breve, dónde está el código y para qué sirve. El usuario de TSLA lo dijo claro: «¿Yo para qué quiero tanto código?».
6. Si hubo correcciones del harness o lecciones nuevas, propón llevarlas a la skill (`<skill_dir>/scripts/`,
   `references/pitfalls.md`).

## Seguimiento de los workflows

- **Dónde está el registro.** Cada workflow escribe
  `~/.claude/projects/<proyecto>/<sesión>/subagents/workflows/wf_*/journal.jsonl`. El del último lanzado es el
  directorio más reciente: `ls -td ~/.claude/projects/*/*/subagents/workflows/wf_* | head -1`.
- **Qué contiene.** Cada agente escribe una línea `started` (con `key`, `label` y `phase`) y, al terminar, una línea
  `result` con la misma `key` y el JSON de su schema. La etiqueta solo aparece en `started`.
- **Esperar.** Bash con `run_in_background` y
  `until [ "$(grep '"type":"result"' <journal> | wc -l)" -ge N ]; do sleep 60; done`. Usa `grep | wc -l`, no
  `grep -c || echo 0`, que rompe la comparación. N vale:
  - 2 en la fase 1;
  - 2 × familias en la fase 2 (una familia sin candidatos no lanza validador);
  - 4 en el panel;
  - 2 (o 1 sin LEAN) en la revisión.
- **Leer los resultados:**

```
python3 -c "import json,sys
L={}
for l in open(sys.argv[1]):
    j=json.loads(l)
    if j['type']=='started': L[j['key']]=j['label']
    elif j['type']=='result': print('==', L.get(j['key']), json.dumps(j['result'], ensure_ascii=False)[:6000])" <journal>
```

- Las rutas de estos journals son los `evidence_paths` de la fase 5.
- Si un agente devuelve `null`, mira su transcripción antes de reintentar. Para reanudar:
  `Workflow({scriptPath, resumeFromRunId})`.
- Si un hook pide hacer commit de archivos sin seguimiento, añade solo rutas concretas (`git add <rutas>`), nunca los
  temporales de los revisores. Si el `.gitignore` del repo excluye `*.sh`, usa `git add -f` para los scripts que deban
  versionarse.

## Principios (el porqué)

- **La deriva engaña.** En una acción que sube mucho, casi cualquier regla de compra "gana". Compara con comprar y
  mantener y con entradas aleatorias del mismo periodo.
- **Solo IS para elegir.** Lo que se elige viendo OOS deja de ser OOS: declara la contaminación y prefiere opciones
  sin parámetros nuevos.
- **Robustez antes que brillo:** vecindario de parámetros, un día de retraso, costos de 15-25 pb, sin las 3 mejores
  operaciones, año a año.
- **Cada hallazgo lo reproduce otro agente, y cada cifra del entregable la verifica un fact-checker.** Frases como
  "nunca", "siempre" o "N de N" deben resistir con inicio diario y en todos los periodos.
- **Recorta las expectativas** (selección, deriva, ejecución) y entrégalas como rangos.
- **Congela la especificación** cuando el panel la acepta.
- **Honestidad:** si la estrategia no supera a comprar y mantener en rentabilidad bruta, dilo en la primera frase.

## Referencias

| Archivo | Cuándo leerlo |
|---|---|
| `references/data_sources.md` | Fase 0 (incluye splits y dividendos) y antes de lanzar la fase 1 |
| `references/protocol.md` | Se copia al laboratorio: reglas de evaluación para todos los agentes |
| `references/pitfalls.md` | Antes de combinar, antes de LEAN y antes del README: todos los errores que ya ocurrieron |
| `references/lean.md` | Fase 4: diseño del algoritmo, partes a cambiar en la plantilla, comandos, verificación |
| `references/final_answer.md` | Antes de la respuesta final al usuario |
| `references/tsla_case.md` | Ejemplo completo: tiempos, costes, cifras y veredictos por familia |
| `references/rebound_mode.md` | Modo rebote: captura del bróker → lista de compras con fecha de venta |
| `references/rebound_base_rates.md` | Modo rebote: acierto histórico de la regla en ~500 acciones del S&P 500 (regenerable con `scripts/rebound_base_rates.py`) |
| `assets/reference_lean_algorithm_tsla.py` | Plantilla LEAN revisada dos veces (prefijo `F3_`, a renombrar) |
