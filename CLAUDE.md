# Notas para Claude en este repositorio

Este repositorio es un fork del motor LEAN de QuantConnect que se usa para investigar estrategias de trading sobre
acciones concretas.

## Preferencias del usuario
- Responde en español.
- Al final de una investigación, explica la estrategia en lenguaje sencillo: qué mirar, cuándo comprar, cuándo vender,
  cuánto dinero poner, qué esperar y qué hacer hoy. El código y los archivos son secundarios; menciónalos al final y
  en breve.

## Qué hay aquí
- `.claude/skills/stock-strategy-lab/`: la skill que repite para cualquier acción el estudio completo hecho con TSLA
  (datos contrastados, motor auditado, familias de estrategias con validadores, panel escéptico, verificación en LEAN
  y respuesta en lenguaje sencillo). Úsala cuando el usuario pida analizar una acción o buscar una estrategia.
- `Research/TeslaStrategy/`: el estudio de TSLA (README con resultados y riesgos, harness auditado, script de la
  estrategia final y operaciones).
- `Algorithm.Python/TeslaTrendRegimeEarningsAlgorithm.py`: la estrategia final de TSLA en LEAN, verificada sesión a
  sesión contra la investigación. Hay que añadir cada trimestre la nueva fecha de resultados de Tesla
  (`REACTION_SESSIONS`, o el parámetro `extra_reaction_sessions`).
- `Algorithm.Python/TeslaTrendCapitulationAlgorithm.py`: la primera versión (estudio 1), superada por la anterior.

## Cosas que conviene saber
- Los contenedores de la nube son temporales: .NET, el venv de Python 3.11 y los datos en formato LEAN hay que
  recrearlos en cada sesión (`.claude/skills/stock-strategy-lab/scripts/setup_lean.sh`, unos 10 minutos).
- No modifiques los datos versionados de `Data/`: convierte los datos propios a una carpeta aparte con
  `to_lean_data.py`.
- El `.gitignore` del repo excluye `*.sh`: añade los scripts de shell con `git add -f`.
