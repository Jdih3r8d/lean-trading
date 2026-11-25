export const meta = {
  name: 'stock-lab-rebound-deep',
  description: 'Rebound/movers analysis from a broker screenshot: market context and base rates first, one analyst and one skeptic per stock (fallers: rebound lens; risers: continuation lens), and a final judge that builds the plan',
  phases: [
    { title: 'Contexto', detail: 'mercado (EE. UU. y Europa) + tasas base de las situaciones de hoy' },
    { title: 'Análisis', detail: 'analista y escéptico por acción (caídas: rebote; subidas: continuación)' },
    { title: 'Decisión', detail: 'juez final: ranking, qué comprar, cuánto, cuándo vender y qué hacer si ya se tiene' },
  ],
}

// Modo rebote profundo de la skill stock-strategy-lab.
// args: {
//   skill_dir: '/abs/skill dir', work: '/abs/dir for outputs (scratchpad)', screen_json: '/abs/screen.json from rebound_screen.py',
//   finalists: ['SNOW', 'AMD'] o [{ticker: 'HBX', grupo: 'cae', notas: 'Bolsa de Madrid, sin datos en los espejos'},
//               {ticker: 'ZEAL', grupo: 'sube', notas: 'Nasdaq Copenhague'}]
//     · las CANDIDATA, VIGILAR y REVISAR del filtro (máx. 6) y las que pida el usuario; un texto suelto = grupo 'cae'.
//     · grupo 'sube' para las que suben o están planas cuando el usuario pregunta por toda la lista.
//   captura: 'lo leído de la captura (nombre → ticker, bolsa, % hoy, precio, hora)', after_close: true,
//   contexto: 'hora de la captura en Nueva York y en España, festivos y medias sesiones, datos desfasados, si la lista
//              parece la cartera del usuario...' (opcional pero muy recomendable),
//   usuario: 'dinero para rebotes, preferencias' (opcional),
//   base_rates: true (por defecto; false para no lanzar el agente de tasas base),
//   search_budget: 180 (búsquedas web para todo el workflow; el cupo de la sesión es ~200 y lo comparten todos los agentes)
// }
const A = args
const SK = A.skill_dir
const WORK = A.work
const RAW = (A.finalists || [])
  .map((f) => (typeof f === 'string' ? { ticker: f } : (f || {})))
  .map((f) => ({ t: String(f.ticker || f.t || '').trim().toUpperCase(), g: String(f.grupo || '').toLowerCase() === 'sube' ? 'sube' : 'cae', notas: f.notas || '' }))
  .filter((s) => s.t)
if (RAW.length > 10) log(`Solo se analizan 10 acciones; quedan fuera: ${RAW.slice(10).map((s) => s.t).join(', ')}`)
const STOCKS = RAW.slice(0, 10)
const N = Math.max(STOCKS.length, 1)
const BUDGET = (A.search_budget === undefined || A.search_budget === null) ? 180 : Math.max(0, A.search_budget)
const B_MARKET = Math.min(20, Math.floor(BUDGET * 0.12))
const B_JUDGE = Math.min(8, Math.floor(BUDGET * 0.05))
const perStock = Math.max(0, Math.floor((BUDGET - B_MARKET - B_JUDGE) / N))
const B_ANALYST = Math.ceil(perStock * 0.6)
const B_SKEPTIC = perStock - B_ANALYST
if (perStock < 4) log(`search_budget=${BUDGET}: solo ${perStock} búsquedas por acción; conviene reducir finalistas`)
const hasRisers = STOCKS.some((s) => s.g === 'sube')
const searchRule = (n) => n <= 0 ? 'PRESUPUESTO DE BÚSQUEDAS: ninguno. No uses búsquedas web; trabaja con los datos locales y lo que te den, y marca como NO VERIFICADO lo que no puedas comprobar.' : `PRESUPUESTO DE BÚSQUEDAS: como mucho ${n} búsquedas web. El cupo (~200 por sesión) lo comparten todos los agentes: si lo gastas, los demás se quedan sin datos (el 25-nov-2026 se agotó y cuatro analistas no pudieron verificar nada; uno no vio que su acción tenía una OPA firmada). Prioriza las noticias propias de la acción y su precio reciente; no repitas lo que ya da el contexto de mercado. Si una búsqueda falla o se agota el cupo, dilo y marca el dato como NO VERIFICADO; no lo inventes.`

const COMMON = `Contexto: un inversor particular ha enviado una captura de su bróker con acciones que se mueven mucho hoy y quiere saber cuáles tienen más probabilidad de SUBIR en los próximos días (para las que caen, la estrategia es comprar tras una caída fuerte y vender pocos días después). Nadie puede saberlo con certeza: estima PROBABILIDADES con honestidad. Escribe en español, claro y concreto.
Captura: ${A.captura || '(ver screen_json)'} · Mercado ${A.after_close ? 'ya cerrado: cifras de hoy definitivas' : 'abierto o sin abrir: cifras de hoy provisionales'}.
${A.contexto ? `Contexto adicional (hora, festivos, datos): ${A.contexto}\n` : ''}Filtro numérico previo (JSON, léelo): ${A.screen_json}. Si una acción sale como REVISAR o con datos_desfasados=true, sus cifras de 5 sesiones y precio NO son fiables (a los espejos les faltan sesiones): reconstruye los cierres recientes antes de concluir. Las acciones no estadounidenses no están en los espejos (SIN DATOS): usa búsquedas web y comparables de EE. UU. Yahoo, Stooq, Google Finance y la API de Nasdaq suelen estar bloqueados desde este entorno; no intentes saltarte el bloqueo.
Criterios del modo rebote y su límite: ${SK}/references/rebound_mode.md (provisionales: salen de un estudio de TSLA donde "comprar tras caer >=12% en 5 sesiones y vender 3 sesiones después" funcionó, y de la literatura de reversión a corto plazo; aún no validados en muchas acciones). Tasas base de caídas en ~500 acciones del S&P 500 desde 2005: ${SK}/references/rebound_base_rates.md. Resumen: un día cualquiera acierta el 52% a 3 sesiones; tras caer >=10% en 5 sesiones, 55%; por encima de su media de 200, 59%; las caídas de 15-20% y >20% rebotan peor (51% y 47%). Tienen sesgo de supervivencia (techo optimista). La literatura añade: las caídas por resultados o previsiones peores tienden a seguir (deriva post-resultados), el momentum de meses negativo tiende a seguir, las subidas por noticias fundamentales nuevas tienden a continuar algo y las subidas sin noticia revierten en parte en una semana.
Herramientas: estudio histórico de caídas de una acción y sus comparables (solo EE. UU.):
  python3 ${SK}/scripts/drop_event_study.py TICKER --drop 0.10 --peers P1,P2,P3
(también --drop 0.05/0.08/0.15/0.20 y --lookback 1 o 3). Para otros estudios (p. ej. qué pasa tras SUBIDAS de un día >=5%) escribe un script corto en ${WORK}/ que importe la descarga: import sys; sys.path.insert(0, '${SK}/scripts'); from rebound_screen import fetch; d, src = fetch('TICKER'). Para noticias usa WebSearch (cárgala con ToolSearch "select:WebSearch"). Calendarios de bolsa: pip install -q pandas_market_calendars (NYSE, XMAD, XPAR, XCSE...). Escribe archivos solo en ${WORK}/.
Sé honesto con la incertidumbre: pocas observaciones no son una probabilidad exacta.`

const ANALYST = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    nombre: { type: 'string' },
    bolsa: { type: 'string' },
    precio_reciente: { type: 'string', description: 'últimos cierres verificados con fecha y fuente, y el precio de hoy si lo encontraste; marca NO VERIFICADO lo que no hayas podido comprobar' },
    movimientos: { type: 'string', description: 'variación de hoy, de 5 sesiones, de 3 meses, distancia a la media de 200 y al máximo de 52 semanas, con datos actualizados' },
    causa_caida: { type: 'string', description: 'qué provocó el movimiento de hoy y de los últimos días (caída o subida), con fecha y fuente' },
    tipo_causa: { type: 'string', enum: ['fundamental_grave', 'resultados_o_prevision', 'resultados_o_noticia_positiva', 'ensayo_clinico_o_regulatorio', 'opa_o_fusion', 'sector_o_mercado', 'analista_rumor_o_flujo', 'desconocida'] },
    causa_temporal: { type: 'boolean', description: 'true si la causa parece pasajera y no cambia el valor del negocio' },
    acierto_historico_accion: { type: ['number', 'null'], description: 'fracción de situaciones pasadas parecidas de ESTA acción tras las que la operación ganó al horizonte recomendado' },
    n_historico_accion: { type: ['integer', 'null'], description: 'número de esas situaciones pasadas' },
    acierto_historico_regla: { type: 'string', description: 'acierto de la regla o situación general más parecida (rebound_base_rates.md, tasas base de hoy o literatura), con n' },
    evidencia_historica: { type: 'string', description: 'números del estudio histórico: n, media, mediana y % ganadoras a 3, 5 y 10 sesiones en el contexto más parecido a hoy, frente a la deriva; y qué causó los episodios pasados más parecidos' },
    comparables: { type: 'string', description: 'cómo se comportan comparables del sector hoy y tras situaciones parecidas' },
    catalizadores: { type: 'string', description: 'qué podría moverla en los próximos 3-10 sesiones, con fechas: resultados, datos clínicos, FDA/EMA, juntas, OPAs, ampliaciones, macro' },
    riesgos: { type: 'array', items: { type: 'string' } },
    prob_subida_3s: { type: 'number', description: 'probabilidad estimada (0-1) de que la operación (compra en la apertura siguiente, venta 3 sesiones después) gane' },
    prob_subida_10s: { type: 'number' },
    horizonte_recomendado: { type: 'integer', enum: [3, 5, 10] },
    veredicto: { type: 'string', enum: ['comprar', 'vigilar', 'descartar'] },
    si_ya_la_tiene: { type: 'string', description: 'qué haría quien ya la tiene en cartera: mantener, reducir o vender, con niveles concretos' },
    tesis: { type: 'string', description: '3-5 frases: por qué subiría o no' },
    fuentes: { type: 'array', items: { type: 'string' } },
  },
  required: ['ticker', 'precio_reciente', 'movimientos', 'causa_caida', 'tipo_causa', 'causa_temporal', 'evidencia_historica', 'comparables', 'catalizadores', 'riesgos', 'prob_subida_3s', 'prob_subida_10s', 'horizonte_recomendado', 'veredicto', 'si_ya_la_tiene', 'tesis', 'fuentes'],
}
const SKEPTIC = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    refuta: { type: 'boolean' },
    argumentos: { type: 'array', items: { type: 'string' } },
    errores_del_analista: { type: 'string', description: 'datos o razonamientos equivocados que encontraste, o "ninguno"' },
    datos_corregidos: { type: 'string', description: 'cifras o hechos corregidos o añadidos, con fuente' },
    veredicto_final: { type: 'string', enum: ['comprar', 'vigilar', 'descartar'] },
    prob_ajustada_3s: { type: 'number' },
    prob_ajustada_10s: { type: 'number' },
    si_ya_la_tiene: { type: 'string' },
    confianza: { type: 'string', enum: ['baja', 'media', 'alta'] },
  },
  required: ['ticker', 'refuta', 'argumentos', 'errores_del_analista', 'veredicto_final', 'prob_ajustada_3s', 'confianza'],
}
const MARKET = {
  type: 'object',
  properties: {
    resumen: { type: 'string', description: 'qué ha pasado hoy y estas dos semanas en el mercado de EE. UU. y por qué' },
    regimen: { type: 'string', description: 'calma, corrección o pánico, con datos (SPY/QQQ frente a sus medias, VIX si lo encuentras)' },
    sectores_castigados: { type: 'string' },
    europa: { type: 'string', description: 'si hay acciones europeas en la lista: cómo van hoy sus índices y sectores' },
    noticias_de_la_lista: { type: 'string', description: 'noticias importantes que hayas visto sobre CUALQUIERA de las acciones de la lista (OPAs, resultados, informes bajistas, aprobaciones), con fecha y fuente: los analistas las recibirán' },
    eventos_proximos: { type: 'string', description: 'eventos de los próximos 5-10 días que pueden mover el mercado (Fed, IPC, empleo, festivos y medias sesiones, resultados del sector, vencimientos)' },
    implicacion_para_rebotes: { type: 'string' },
  },
  required: ['resumen', 'regimen', 'sectores_castigados', 'noticias_de_la_lista', 'eventos_proximos', 'implicacion_para_rebotes'],
}
const BASE = {
  type: 'object',
  properties: {
    universo: { type: 'string' },
    tablas: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          situacion: { type: 'string' }, n: { type: 'integer' },
          gana_3s: { type: 'number' }, media_3s: { type: 'number' }, gana_10s: { type: 'number' }, media_10s: { type: 'number' },
          pct_perdida_mayor_10_10s: { type: 'number' },
        },
        required: ['situacion', 'n', 'gana_3s', 'media_3s', 'gana_10s', 'media_10s'],
      },
    },
    conclusiones: { type: 'string', description: 'qué situaciones de hoy tienen ventaja y cuáles no, en lenguaje sencillo' },
    archivo: { type: 'string' },
  },
  required: ['universo', 'tablas', 'conclusiones', 'archivo'],
}
const JUDGE = {
  type: 'object',
  properties: {
    veredicto: { type: 'string', description: 'una frase: cuántas comprar y la advertencia principal' },
    ranking: {
      type: 'array', description: 'TODAS las acciones analizadas, de más a menos probabilidad de subir en los próximos días',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' }, nombre: { type: 'string' },
          prob_subida_3s: { type: 'number' }, prob_subida_10s: { type: 'number' },
          accion: { type: 'string', enum: ['comprar', 'vigilar', 'descartar'] },
          si_ya_la_tiene: { type: 'string' }, motivo: { type: 'string' },
        },
        required: ['ticker', 'prob_subida_3s', 'prob_subida_10s', 'accion', 'si_ya_la_tiene', 'motivo'],
      },
    },
    compras: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' }, nombre: { type: 'string' },
          peso: { type: 'number', description: 'fracción del dinero que el usuario dedica a rebotes (suma <= 1, máx. 0.25 por acción; la mitad si el mercado está en pánico)' },
          condicion_entrada: { type: 'string' },
          por_que: { type: 'string' }, historico: { type: 'string' },
          fecha_compra: { type: 'string' }, fecha_venta: { type: 'string' }, horizonte_sesiones: { type: 'integer' },
          prob_estimada: { type: 'number', description: 'probabilidad estimada de que ESTA operación gane (0-1)' },
          acierto_historico_regla: { type: 'string', description: 'p. ej. "59% en 2.350 caídas parecidas del S&P 500 desde 2005 (techo optimista)"' },
          acierto_historico_accion: { type: 'string', description: 'p. ej. "de 17 caídas parecidas de esta acción, ganó en 15 (88%)"' },
          riesgo_principal: { type: 'string' },
        },
        required: ['ticker', 'nombre', 'peso', 'condicion_entrada', 'por_que', 'historico', 'fecha_compra', 'fecha_venta', 'horizonte_sesiones', 'prob_estimada', 'acierto_historico_regla', 'acierto_historico_accion', 'riesgo_principal'],
      },
    },
    vigilar: { type: 'array', items: { type: 'object', properties: { ticker: { type: 'string' }, que_esperar: { type: 'string' } }, required: ['ticker', 'que_esperar'] } },
    descartadas: { type: 'array', items: { type: 'object', properties: { ticker: { type: 'string' }, motivo: { type: 'string' } }, required: ['ticker', 'motivo'] } },
    contexto_mercado: { type: 'string' },
    discrepancias_resueltas: { type: 'string', description: 'dónde discreparon analista y escéptico y cómo lo resolviste' },
    advertencias: { type: 'array', items: { type: 'string' } },
  },
  required: ['veredicto', 'ranking', 'compras', 'vigilar', 'descartadas', 'contexto_mercado', 'advertencias'],
}

const analystPrompt = (s, market) => {
  const ctx = `Contexto de mercado y noticias ya encontradas por otro agente (no lo repitas; úsalo):
${JSON.stringify(market, null, 1)}
${s.notas ? `Notas sobre ${s.t}: ${s.notas}\n` : ''}${searchRule(B_ANALYST)}`
  return s.g === 'cae'
    ? `${COMMON}

${ctx}

TU PAPEL: analista de ${s.t}, una de las acciones que CAEN. Investiga a fondo si tiene buenas probabilidades de rebotar:
1. Precio y movimientos con datos actualizados (si el filtro la marca REVISAR o SIN DATOS, reconstruye los cierres recientes con fecha y fuente).
2. Por qué ha caído (noticias de hoy y de los últimos días, con fecha y fuente). Clasifica la causa: fundamental grave (fraude, quiebra, pérdida de un cliente clave, rechazo regulatorio, ampliación de capital), resultados o previsiones peores, sector o mercado, analista/rumor/flujos (incluidos informes de bajistas), o desconocida. ¿Es pasajera?
3. Qué pasó históricamente tras caídas parecidas de ${s.t} y de 2-4 comparables: ejecuta drop_event_study.py (con otros umbrales si la caída de hoy es distinta). Fíjate en el subconjunto más parecido a hoy (régimen de mercado, por encima o por debajo de su media de 200, tamaño de la caída) y busca qué causó 2-3 de las caídas pasadas más parecidas.
4. Comparables: ¿han caído también (caída sectorial, suele rebotar mejor) o solo ${s.t} (problema propio)?
5. Catalizadores y riesgos para los próximos 3-10 sesiones, con fechas. Si hay resultados dentro del periodo, es un riesgo grande.
6. Anota tres porcentajes: el acierto histórico de la REGLA en la situación más parecida, el de ESTA ACCIÓN tras caídas parecidas (con n) y tu probabilidad estimada.
7. Estima la probabilidad de que una compra en la próxima apertura gane si se vende 3 y 10 sesiones después. Recomienda horizonte, veredicto y qué haría quien ya la tiene.`
    : `${COMMON}

${ctx}

TU PAPEL: analista de ${s.t}, una de las acciones que SUBEN o están planas. La pregunta es si seguirá subiendo en los próximos días:
1. Precio y movimientos con datos actualizados (cierres recientes con fecha y fuente). Un 0,00% exacto en la captura puede ser un fallo de la línea del bróker: compruébalo.
2. Por qué se mueve (noticias con fecha y fuente). Clasifica la causa: noticia fundamental nueva (datos clínicos, aprobación, acuerdo, resultados), OPA o fusión (si hay una oferta en efectivo firmada, el precio queda anclado a ella: calcula el diferencial y el riesgo de que se caiga), rebote técnico, sector, analista/flujos, o nada concreto.
3. Histórico: si hay datos en los espejos (o de un comparable de EE. UU.), escribe un script corto que mida qué pasó tras subidas parecidas (día >= +5%, o 5 sesiones >= +20%): n, media, mediana y % que siguió subiendo a 3, 5 y 10 sesiones, frente a la deriva. Si la acción también ha caído mucho en semanas, añade la lente de rebote (drop_event_study.py).
4. Comparables y sector hoy y esta semana.
5. Catalizadores y riesgos para los próximos 3-10 sesiones con fechas (las biotecnológicas suelen ampliar capital tras subir).
6. Anota el acierto histórico de la situación general más parecida, el de esta acción (con n) y tu probabilidad estimada de que una compra en la próxima apertura gane 3 y 10 sesiones después. Recomienda horizonte, veredicto y qué haría quien ya la tiene.`
}

const skepticPrompt = (s, an, market) => `${COMMON}

Contexto de mercado y noticias ya encontradas (úsalo para contrastar):
${JSON.stringify(market, null, 1)}
${searchRule(B_SKEPTIC)}

TU PAPEL: escéptico. Otro analista concluyó esto sobre ${s.t} (${s.g === 'cae' ? 'acción que CAE: tesis de rebote o no' : 'acción que SUBE o está plana: tesis de continuación o no'}):
${JSON.stringify(an, null, 1)}

Intenta REFUTAR su conclusión, sea cual sea. Comprueba sus datos (precios y fechas: si marcó algo como NO VERIFICADO, intenta verificarlo; vuelve a ejecutar los scripts si hace falta), busca noticias que haya pasado por alto (¿una OPA, resultados o un evento binario en los próximos días? ¿rebajas de rating, demandas, informes de bajistas, ventas de directivos, ampliaciones?), cuestiona si el histórico es comparable (pocas observaciones, otro contexto) y si la probabilidad está inflada o es demasiado baja. Da tu veredicto final, probabilidades ajustadas y qué haría quien ya la tiene. Si la tesis aguanta, dilo.`

phase('Contexto')
const marketP = agent(`${COMMON}
${searchRule(B_MARKET)}

Acciones de la lista: ${STOCKS.map((s) => `${s.t} (${s.g})`).join(', ')}.

TU PAPEL: analista de mercado. Explica el contexto general: qué ha pasado en el mercado de EE. UU. hoy y estas dos semanas y por qué, si estamos en calma, corrección o pánico (usa el campo "mercado" del JSON del filtro y busca el VIX), qué sectores han caído más, cómo va Europa si hay acciones europeas en la lista, qué eventos próximos (5-10 días) pueden moverlo todo (festivos y medias sesiones incluidos) y qué implica para una estrategia de rebote a pocos días. Además, apunta en "noticias_de_la_lista" cualquier noticia importante que veas sobre las acciones de la lista (OPAs, resultados, informes bajistas...): los analistas la recibirán y así no gastan búsquedas en buscarla.`, { label: 'mercado', phase: 'Contexto', schema: MARKET })

const baseP = A.base_rates === false ? Promise.resolve(null) : agent(`${COMMON}

TU PAPEL: estadístico de tasas base. Calcula con datos (no con la memoria) qué pasó históricamente en las situaciones de HOY, para que el juez tenga referencias más precisas que la tabla general. Lee el JSON del filtro y la lista: ${STOCKS.map((s) => `${s.t} (${s.g})`).join(', ')}. Universo: componentes actuales del S&P 500 (si no existe ${WORK}/sp500.csv, descárgalo de https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv; columnas Symbol y GICS Sector), descargados con fetch() de rebound_screen.py en paralelo (reutiliza el código de ${SK}/scripts/rebound_base_rates.py; guarda una caché en ${WORK}/cache/ para que otros agentes la reutilicen). Desde 2005: comprar en la apertura siguiente a la señal y vender en la apertura 3, 5 y 10 sesiones después, con 0,10% de costes; eventos sin solaparse por acción. Para cada situación: n, % ganadoras, media y mediana, y % que pierde más de un 10% a 10 sesiones. Situaciones: referencia (cualquier día, y cualquier día con el régimen de mercado de hoy); las caídas de hoy por tipo (día <= -5% tras 5 sesiones <= -10%; con 3 meses <= -30% y bajo su media de 200; por sector; caída de un día >= 15%)${hasRisers ? '; y las subidas de hoy (día >= +5%, todas y por sector; 5 sesiones >= +20%)' : ''}. Avisa del sesgo de supervivencia. Guarda la tabla en ${WORK}/tasas_base_hoy.md y el script en ${WORK}/tasas_base_hoy.py. Límite: unos 25 minutos; si va lento, usa una muestra y dilo. No uses búsquedas web.`, { label: 'tasas-base', phase: 'Contexto', schema: BASE })

const market = await marketP

const pairs = await pipeline(
  STOCKS,
  (s) => agent(analystPrompt(s, market), { label: `analista:${s.t}`, phase: 'Análisis', schema: ANALYST }),
  (an, s) => an && agent(skepticPrompt(s, an, market), { label: `esceptico:${s.t}`, phase: 'Análisis', schema: SKEPTIC }).then((sk) => ({ ticker: s.t, grupo: s.g, analista: an, esceptico: sk })),
)
const base = await baseP
const results = (pairs || []).filter(Boolean)
const missing = STOCKS.map((s) => s.t).filter((t) => { const r = results.find((x) => x.ticker === t); return !r || !r.esceptico })
if (missing.length) log(`Sin análisis completo (falló el analista o el escéptico): ${missing.join(', ')}`)

phase('Decisión')
const judge = await agent(`${COMMON}
${searchRule(B_JUDGE)}

TU PAPEL: juez final y gestor. Mira la hora (date; TZ=America/New_York date): si la bolsa ya ha abierto desde la captura, busca cómo van HOY las acciones que vayas a recomendar y ajusta la condición de entrada a lo que ya ha pasado. Con todo lo de abajo:
1. Ordena TODAS las acciones analizadas de más a menos probabilidad de subir (3 y 10 sesiones), con acción (comprar / vigilar / descartar), qué hacer si ya la tiene y el motivo en una o dos frases sencillas.
2. Decide qué comprar (como mucho 3-5; puede ser ninguna: dilo sin rodeos), cuánto (fracción del dinero dedicado a rebotes: a partes iguales salvo que la convicción justifique inclinar un poco; máximo 0,25 por acción; la mitad si el mercado está en pánico), cuándo comprar (próxima apertura tras la captura; si la captura es de antes del cierre, "si al cierre sigue así") y cuándo vender (apertura N sesiones después según el horizonte). Calcula las fechas con pandas_market_calendars (NYSE y, para acciones europeas, su bolsa: XMAD, XPAR, XCSE...). Una acción va a compras solo si el escéptico no la ha refutado con argumentos sólidos. Las que se mueven por el mismo motivo (mismo sector en pánico) cuentan como UNA sola apuesta.
3. Para cada compra da SIEMPRE los tres porcentajes de acierto: el de la regla en general (situación más parecida, de rebound_base_rates.md o de las tasas base de hoy; avisa de que es un techo optimista), el de esta acción tras situaciones parecidas (con n; si n < 10, dilo) y la probabilidad estimada ahora, explicando en una frase por qué sube o baja respecto a los históricos.
4. Lista las de vigilar (qué tendría que pasar) y las descartadas con su motivo (incluye las que el filtro numérico descartó, que están en el JSON). Explica dónde discreparon analista y escéptico y cómo lo resolviste.
Notas del usuario: ${A.usuario || 'ninguna'}.
${missing.length ? `SIN ANÁLISIS COMPLETO (falló el analista o el escéptico): ${missing.join(', ')}. Inclúyelas en el ranking marcadas como "análisis incompleto" y NO las pongas en compras si su escéptico falta.
` : ''}
Contexto de mercado:
${JSON.stringify(market, null, 1)}

Tasas base calculadas hoy:
${JSON.stringify(base, null, 1)}

Análisis por acción (analista + escéptico):
${JSON.stringify(results, null, 1)}`, { label: 'juez', phase: 'Decisión', schema: JUDGE })

return { market, base, pairs: results, judge }
