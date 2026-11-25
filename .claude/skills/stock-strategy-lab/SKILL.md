---
name: stock-strategy-lab
description: Investigación completa y honesta de estrategias de trading para UNA acción (TSLA, NVDA, AAPL, cualquier ticker de EE. UU.) con datos diarios. Consigue y valida datos, audita el motor de backtest, lanza agentes en paralelo por familias de estrategias (volatilidad, opciones/VIX, resultados trimestrales y eventos, régimen de mercado, gestión de posición, patrones, machine learning), cada una con un validador independiente; combina lo que sobrevive, la somete a un panel escéptico, la implementa y verifica en LEAN, y termina explicando al usuario en lenguaje sencillo cuándo comprar, cuándo vender, la rentabilidad media por operación y qué hacer hoy. Úsala siempre que el usuario pida analizar una acción para encontrar una estrategia ganadora, "busca una estrategia para X", "cuándo entrar y cuándo salir de X", backtest de reglas sobre una acción, o repetir para otro ticker el estudio que se hizo con Tesla, aunque no mencione agentes, LEAN ni la palabra skill.
---

# Laboratorio de estrategias para una acción

Esta skill reproduce, para cualquier acción, el proceso con el que se estudió TSLA en noviembre de 2026. El resultado
fue una estrategia de tres módulos con un Sharpe fuera de muestra de 1,56 frente a 0,89 de comprar y mantener, verificada
sesión a sesión en LEAN (ver `references/tsla_case.md`). El valor del proceso no está en una fórmula concreta sino en su
disciplina:

- datos contrastados;
- un motor auditado antes de usarlo;
- parámetros elegidos solo con datos "de entrenamiento" (IS);
- cada hallazgo reproducido e intentado refutar por otro agente;
- expectativas recortadas con honestidad;
- una explicación final que el usuario pueda seguir sin leer código.

`<skill_dir>` es la carpeta que contiene este archivo. Scripts en `<skill_dir>/scripts/`, workflows en
`<skill_dir>/workflows/`, guías en `<skill_dir>/references/`.

## Qué esperar antes de empezar

El modo completo dura unas 5-6 horas de reloj y usa unos 20-25 subagentes, con 4-5 millones de tokens. Los workflows
corren como mucho ~2 agentes a la vez en un contenedor de 4 CPU. Díselo al usuario en una línea al empezar y sigue: si
pidió el estudio, ya lo autorizó. Si quiere algo rápido, usa el **modo rápido**:

- solo las fases 0-2;
- en la fase 3, solo las familias `events`, `regime` y `vol`;
- se salta la fase 5 (LEAN);
- la revisión final se limita al fact-check.

Pregunta solo lo que no puedas deducir: normalmente basta con el ticker. Responde al usuario en su idioma.

## Fase 0 · Laboratorio y datos de la acción (tú, en línea)

1. Crea el laboratorio en el scratchpad (no en el repo):
   `bash <skill_dir>/scripts/new_lab.sh <TICKER> <lab> [is_end] [rec_start]`.
   - IS (donde se eligen parámetros) debe cubrir aproximadamente la primera mitad de la historia y terminar el 31 de diciembre.
   - OOS es todo lo posterior.
   - REC son los últimos ~3 años.
   - Si la acción tiene poca historia (menos de 8 años), dilo: los resultados serán menos fiables.
2. Construye `<lab>/data/main.csv` (OHLCV diario ajustado por splits) siguiendo `references/data_sources.md`. Las APIs
   financieras suelen estar bloqueadas; los espejos CSV en GitHub funcionan. Empalma una fuente larga con una que se
   actualice a diario y contrasta el solapamiento.
3. Ejecuta `python3 <skill_dir>/scripts/check_data.py <lab> <otras fuentes...>`: detecta filas corruptas (por ejemplo,
   open/high/low copiados del día anterior), splits sin ajustar y discrepancias entre fuentes. Repara solo con fuentes
   realmente independientes y anótalo en `data/DATA_NOTES.md`. También fija `is_start` en `config.json`.
4. Anota las fechas de split reales de la acción, que se necesitan para LEAN.
5. Haz 2-3 búsquedas web rápidas de contexto (últimos resultados, noticias, fecha del próximo informe) para la respuesta final.

## Fase 1 · En paralelo: auditoría, datos auxiliares y estudio clásico

Lanza el workflow de la fase 0 en segundo plano:

```
Workflow({scriptPath: "<skill_dir>/workflows/phase0_audit_data.js",
          args: {lab: "<lab>", ticker: "<T>", skill_dir: "<skill_dir>",
                 market_etfs: ["QQQ", "SPY", "<ETF sectorial si aplica, p.ej. SMH, XLE>"],
                 extra_data_goals: "<opcional: eventos propios de la empresa>"}})
```

- Un agente audita `harness.py`/`engine.py` con tests sintéticos. El de TSLA encontró 5 errores reales; ya están
  corregidos, pero audita de todas formas: el código y los datos cambian.
- Otro agente consigue los datos auxiliares: ETFs de mercado con versión ajustada por dividendos, familia VIX,
  calendario de resultados con horas de la SEC, eventos, volatilidad implícita y vencimientos de opciones.

Mientras tanto, tú:

- Ejecuta el estudio clásico: `python3 <skill_dir>/scripts/classic_sweep.py <lab>` (unas 6.000 reglas en segundos).
  Léelo con las pautas de su docstring. La pregunta clave es si las reglas superan la simple deriva alcista de la acción.
- Elige la **referencia** (baseline) solo con IS: un módulo de tendencia más uno de reversión/capitulación poco
  correlacionados, al 50/50, suele ser un buen punto de partida (`harness.trend_capitulation_weights`, re-ajustado en IS).
- Guarda `data/baseline_weights.csv` (date,weight) y `data/BASELINE.md` con:
  - las reglas;
  - las cifras IS/OOS/REC/año actual;
  - las de comprar y mantener;
  - lo que no funcionó.
- Si va a haber LEAN, prepara la cadena en segundo plano: `bash <skill_dir>/scripts/setup_lean.sh <repo> <work>`.

Cuando termine el workflow:

1. Lee los hallazgos de la auditoría y corrige el harness con tests.
2. Si cambia `engine.py` o `harness.py`, vuelve a ejecutar el estudio clásico.
3. Revisa `DATA_NOTES.md` y mueve los archivos con errores conocidos a `data/superseded/`.
4. Actualiza `PROTOCOL.md` si hace falta: el tiempo de publicación de cada dato (p. ej. el VIX cierra a las 16:15 ET),
   y el aviso de que no se debe usar `superseded/`.

## Fase 2 · Familias de estrategias, cada una con validador

```
Workflow({scriptPath: "<skill_dir>/workflows/phase1_families.js",
          args: {lab: "<lab>", ticker: "<T>",
                 context: "<resumen del estudio clásico, reglas y cifras de la referencia, comprar y mantener>",
                 skip: [], extra_scope: {}}})
```

Son 7 familias por defecto (`vol`, `implied`, `events`, `regime`, `sizing`, `patterns`, `ml`), cada una en pipeline con
un validador que reimplementa las reglas desde el texto, busca *look-ahead* e intenta refutarlas.

- Quita las que no apliquen con `skip`: por ejemplo `implied` si no hay datos de opciones ni ETF de volatilidad
  relevante, o `ml` en modo rápido.
- Adapta los alcances con `extra_scope`: por ejemplo, para un banco, eventos de tipos de interés.
- Mientras corre, lee los resultados conforme llegan (ver "Seguimiento") y cuéntale al usuario lo esencial de cada
  familia en una o dos frases.

## Fase 3 · Combinar (tú) y panel de desafío

1. Reconstruye tú mismo los componentes con evidencia en `<lab>/lead/components.py`. Comprueba que coinciden con los
   CSV de los agentes (diferencia 0). Guarda los pesos de cada componente y de cada combinación en
   `lead/w_<nombre>.csv`.
2. Orden de preferencia para incluir componentes:
   1. **confirmados** por su validador;
   2. **débiles pero robustos** a un día de retraso y a perturbaciones, sobre todo si no añaden parámetros nuevos
      (p. ej. reutilizar los 10/30 del módulo de tendencia en el ETF de mercado);
   3. nunca los frágiles: dependen de 3 episodios o mueren con un día de retraso.

   Combinar muchos componentes débiles sube el Sharpe IS y baja el OOS.
3. Evalúa pocas combinaciones: referencia, referencia + confirmados, referencia + confirmados + el mejor robusto. Para
   cada una, mira IS/OOS/REC/año actual, costo de estrés, un día de retraso, caída máxima y operaciones por módulo.
   Elige la candidata y una alternativa más sencilla (*fallback*).
4. Lanza el panel:

```
Workflow({scriptPath: "<skill_dir>/workflows/phase2_challenge.js",
          args: {lab: "<lab>", ticker: "<T>", repo: "<repo>", lean_work: "<work>", brief: "<ver abajo>"}})
```

El `brief` debe ser autosuficiente:

- la historia;
- el número total de configuraciones, **recalculado sumando los `configs_tested` de cada familia** (en TSLA el brief
  sumó mal y el panel heredó el error);
- los veredictos de los validadores;
- las definiciones exactas de componentes y candidata;
- las rutas de `lead/`;
- tus cifras para referencia, fallback, candidata y comprar y mantener, con estrés y retraso.

Son cuatro agentes:

- un optimizador que intenta superar a la candidata con 200 alternativas pre-registradas;
- un escéptico estadístico: bootstrap, Sharpe deflactado, *reality check*, PBO y Monte Carlo;
- uno de implementación: reimplementación sesión a sesión y diseño para LEAN;
- uno de régimen: años, crisis, decaimiento y perturbaciones conjuntas.

Si el panel pide cambios de reglas con evidencia, aplícalos y repite la evaluación. Si solo pide cambiar expectativas,
congela la especificación: más ajustes son sobreajuste.

## Fase 4 · LEAN (si el repo es LEAN o el usuario quiere automatizar)

Sigue `references/lean.md`. Resumen:

1. Convierte cada símbolo con `scripts/to_lean_data.py` (precios sin ajustar + factores; `--splits` para la acción; los
   `*_adj.csv` para los ETFs, empezando un año antes) en `<work>/leandata`, nunca en el `Data/` versionado del repo.
2. Escribe el algoritmo copiando la estructura de `assets/reference_lean_algorithm_tsla.py`, versión de producción tras
   dos revisiones; cambia solo la lógica de los módulos, las constantes, los símbolos y el calendario de eventos.
   Tómalo del diseño del escéptico de implementación si escribió uno.
3. Ejecuta `scripts/run_lean.sh` en modo "close" con exportación de CSV y deslizamiento = costo base, y luego
   `scripts/reconcile_lean.py`.
4. La meta es **0 diferencias de peso** en todas las sesiones, el mismo resultado en modo "morning", y que los
   arranques a mitad de historia reconstruyan el estado.

## Fase 5 · Entregable, revisión final y respuesta

1. Crea en el repo `Research/<Ticker>Strategy/` con:
   - `harness.py`, `engine.py` y `PROTOCOL.md`;
   - el script de la estrategia final, que imprima cifras, operaciones por módulo y estado actual;
   - un `fetch_data.py` que reconstruya los datos con fecha de corte fija;
   - los calendarios de eventos necesarios;
   - `results/` con las operaciones;
   - un README en el idioma del usuario con: reglas exactas, resultados por periodo, robustez (estrés, retraso, LEAN),
     tabla de rentabilidad por operación indicando la base (por módulo o por cuenta), expectativa realista con los
     rangos del panel, metodología, qué no funcionó, riesgos y cómo reproducir.

   No subas datos descargados de terceros (ignóralos en `.gitignore`).
2. Haz commit en la rama de trabajo de la sesión y push.
3. Lanza la revisión:

```
Workflow({scriptPath: "<skill_dir>/workflows/phase3_deliverable_review.js",
          args: {repo: "<repo>", work: "<work>", skill_dir: "<skill_dir>", lab: "<lab>", ticker: "<T>",
                 algorithm_class: "<Clase>", readme: "<repo>/Research/<X>/README.md", research_dir: "<repo>/Research/<X>",
                 research_weights: "<lab>/lead/w_<final>.csv", lean_out: "<dir csv LEAN>", lean_log: "<log>",
                 env_prefix: "STRAT_", evidence_paths: ["<journals de los workflows>"]}})
```

4. Revisa y aplica el parche del revisor de código: vuelve a correr LEAN y la conciliación. Corrige el README según el
   fact-check: en TSLA había conteos mal sumados, frases absolutas falsas y expectativas mal atribuidas. Haz commit y push.
5. **Responde al usuario con el plan en lenguaje sencillo**, siguiendo `references/final_answer.md`: veredicto, qué
   mirar, cada regla con comprar/vender/qué esperar, ejemplo con dinero, expectativa realista, qué hacer hoy y, solo al
   final y en breve, dónde está el código y para qué sirve.

   El usuario de TSLA lo dijo claro: "¿Yo para qué quiero tanto código?". Lo que quiere saber es qué hacer.

## Seguimiento de los workflows

- Cada workflow devuelve un *task id* y escribe un `journal.jsonl` en su carpeta de transcripción; el resultado de
  cada agente es una línea `{"type":"result",...}`.
- Para esperar sin bloquear la conversación, usa Bash con `run_in_background` y un bucle `until` que cuente esas
  líneas. Lee cada resultado con un pequeño script de Python que imprima veredicto, candidatos y cifras.
- Si un agente devuelve `null`, mira su transcripción antes de reintentar. Para reanudar:
  `Workflow({scriptPath, resumeFromRunId})`.
- Si el hook de parada pide hacer commit de archivos sin seguimiento, añade solo las rutas concretas (`git add <rutas>`),
  nunca los archivos temporales de los revisores.

## Principios (el porqué)

- **La deriva engaña.** En una acción que sube mucho, casi cualquier regla larga "gana". Compara con comprar y mantener
  y con entradas aleatorias del mismo periodo.
- **Solo IS para elegir.** Todo lo que se elige viendo OOS deja de ser OOS: decláralo y prefiere opciones sin
  parámetros nuevos.
- **Robustez antes que brillo:** vecindario de parámetros, un día de retraso, costos de 15-25 pb, sin las 3 mejores
  operaciones, año a año.
- **Cada hallazgo lo reproduce otro agente** y cada cifra del entregable la verifica un fact-checker. Las frases
  "nunca", "siempre" o "N de N" deben resistir con inicio diario y en todos los periodos.
- **Recorta las expectativas** (selección, deriva, ejecución) y entrégalas como rangos.
- **Congela la especificación** cuando el panel la acepta.
- **Honestidad con el usuario:** si la estrategia no supera a comprar y mantener en rentabilidad bruta, dilo en la
  primera frase.

## Referencias (léelas cuando toque)

| Archivo | Cuándo |
|---|---|
| `references/data_sources.md` | Fase 0 y antes de lanzar el agente de datos |
| `references/protocol.md` | Se copia al laboratorio; reglas de evaluación para todos los agentes |
| `references/pitfalls.md` | Antes de combinar, antes de LEAN y antes de escribir el README: todos los errores que ya ocurrieron |
| `references/lean.md` | Fase 4 |
| `references/final_answer.md` | Antes de la respuesta final al usuario |
| `references/tsla_case.md` | Ejemplo completo: tiempos, costos, cifras y veredictos por familia |
| `assets/reference_lean_algorithm_tsla.py` | Plantilla del algoritmo LEAN; usa el prefijo de entorno `F3_`, renómbralo |
