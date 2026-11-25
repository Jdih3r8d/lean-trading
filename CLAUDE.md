# Notas para Claude en este repositorio

Este repositorio es un fork del motor LEAN de QuantConnect que se usa para investigar estrategias de trading sobre
acciones concretas.

## Preferencias del usuario
- Responde en español.
- Tiene Claude Max y no le preocupa el consumo de tokens: prefiere análisis a fondo con agentes. Los quiere bajo
  petición, cuando él lo pida, no como tareas automáticas diarias.
- Al final de una investigación, explica la estrategia en lenguaje sencillo: qué mirar, cuándo comprar, cuándo vender,
  cuánto dinero poner, qué esperar y qué hacer hoy. El código y los archivos son secundarios; menciónalos al final y
  en breve.

## Qué hay aquí
- `.claude/skills/stock-strategy-lab/`: la skill que repite para cualquier acción el estudio completo hecho con TSLA
  (datos contrastados, motor auditado, familias de estrategias con validadores, panel escéptico, verificación en LEAN
  y respuesta en lenguaje sencillo). Úsala cuando el usuario pida analizar una acción o buscar una estrategia. Tiene
  también un **modo rebote**: si el usuario manda una captura de su bróker con las acciones que más caen hoy (o su
  lista de "Top Movers", con las que suben y las que bajan), sigue
  `references/rebound_mode.md` de la skill. Por defecto es la variante profunda con agentes
  (`workflows/rebound_deep.js`).
- `Research/Rebotes/`: un informe por cada análisis del modo rebote (`README.md` en lenguaje sencillo y
  `detalle_agentes.md` con lo que devolvió cada agente). El primero es `2026-11-25_TopMovers/`.
- `Research/TeslaStrategy/`: el estudio de TSLA (README con resultados y riesgos, harness auditado, script de la
  estrategia final y operaciones).
- `Algorithm.Python/TeslaTrendRegimeEarningsAlgorithm.py`: la estrategia final de TSLA en LEAN, verificada sesión a
  sesión contra la investigación. Hay que añadir cada trimestre la nueva fecha de resultados de Tesla
  (`REACTION_SESSIONS`, o el parámetro `extra_reaction_sessions`).
- `Algorithm.Python/TeslaTrendCapitulationAlgorithm.py`: la primera versión (estudio 1), superada por la anterior.

## Cosas que conviene saber
- Este repositorio tiene un entorno de nube propio llamado `lean-trading`. Su script de preparación instala .NET 10,
  compila LEAN y crea `/opt/lean_work` (venv de Python 3.11 en `py311/` y carpeta de datos LEAN en `leandata/`) ANTES
  de que empiece la sesión. Si existe `/opt/lean_work/py311`, úsalo como `<work>` de la skill y NO ejecutes
  `setup_lean.sh`. Solo si no existe (sesión iniciada en otro entorno), ejecútalo:
  `bash .claude/skills/stock-strategy-lab/scripts/setup_lean.sh $PWD /opt/lean_work` (unos 5 minutos, casi sin tokens:
  es tiempo de compilación, no de razonamiento).
- No modifiques los datos versionados de `Data/`: convierte los datos propios a una carpeta aparte con
  `to_lean_data.py`.
- El `.gitignore` del repo excluye `*.sh`: añade los scripts de shell con `git add -f`.
