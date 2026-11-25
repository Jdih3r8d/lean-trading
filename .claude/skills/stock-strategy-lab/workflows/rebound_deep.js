export const meta = {
  name: 'stock-lab-rebound-deep',
  description: 'Rebound analysis of beaten-down stocks: market context, one analyst and one skeptic per finalist, and a final judge that builds the buy/sell plan',
  phases: [
    { title: 'Análisis', detail: 'contexto de mercado + analista y escéptico por acción' },
    { title: 'Decisión', detail: 'juez final: qué comprar, cuánto y cuándo vender' },
  ],
}

// Modo rebote profundo de la skill stock-strategy-lab.
// args: {
//   skill_dir: '/abs/skill dir', work: '/abs/dir for outputs (scratchpad)', screen_json: '/abs/screen.json from rebound_screen.py',
//   finalists: ['SNOW', 'AMD'],   // CANDIDATA + VIGILAR del script (máx. 6) y las que pida el usuario
//   captura: 'texto con lo leído de la captura (ticker, % hoy, precio, hora)', after_close: true,
//   usuario: 'notas del usuario (dinero para rebotes, preferencias)' (opcional)
// }
const A = args
const SK = A.skill_dir
const WORK = A.work
const FIN = (A.finalists || []).slice(0, 8)

const COMMON = `Contexto: un inversor particular te ha enviado una captura de su bróker con las acciones de EE. UU. que más han caído hoy y quiere saber cuáles tienen más probabilidad de REBOTAR en los próximos días (estrategia de comprar tras una caída fuerte y vender pocos días después). Escribe en español, claro y concreto.
Captura: ${A.captura || '(ver screen_json)'} · Mercado ${A.after_close ? 'ya cerrado: cifras de hoy definitivas' : 'abierto: cifras de hoy provisionales'}.
Filtro numérico previo (JSON, léelo): ${A.screen_json}. Criterios del filtro y su límite: ${SK}/references/rebound_mode.md (son provisionales: salen de un estudio de TSLA donde "comprar tras caer >=12% en 5 sesiones y vender 3 sesiones después" funcionó, y de la literatura de reversión a corto plazo; aún no validados en muchas acciones).
Tasas base (acierto histórico de la regla en ~500 acciones del S&P 500 desde 2005, por situación; léelas): ${SK}/references/rebound_base_rates.md. Resumen: un día cualquiera acierta el 52% a 3 sesiones; tras caer >=10% en 5 sesiones, 55%; si además está por encima de su media de 200, 59%; las caídas de más del 15-20% rebotan peor (47-51%). Tienen sesgo de supervivencia (techo optimista).
Herramientas: el estudio histórico de caídas de una acción y de sus comparables se obtiene con
  python3 ${SK}/scripts/drop_event_study.py TICKER --drop 0.10 --peers P1,P2,P3
(también con --drop 0.08 / 0.15 y --lookback 1 o 3 si la caída de hoy es de uno o pocos días). Los datos vienen de espejos públicos de GitHub; Yahoo y otras APIs suelen estar bloqueadas. Para noticias usa la herramienta WebSearch (cárgala con ToolSearch "select:WebSearch"). Escribe archivos solo en ${WORK}/.
Sé honesto con la incertidumbre: pocas observaciones históricas no son una probabilidad exacta.`

const ANALYST = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    causa_caida: { type: 'string', description: 'qué provocó la caída, con fecha y fuente' },
    tipo_causa: { type: 'string', enum: ['fundamental_grave', 'resultados_o_prevision', 'sector_o_mercado', 'analista_rumor_o_flujo', 'desconocida'] },
    causa_temporal: { type: 'boolean', description: 'true si la causa parece pasajera y no cambia el valor del negocio' },
    acierto_historico_accion: { type: ['number', 'null'], description: 'fracción de caídas pasadas parecidas de ESTA acción (el subconjunto más parecido a hoy, o todas si hay pocas) tras las que la operación ganó al horizonte recomendado' },
    n_historico_accion: { type: ['integer', 'null'], description: 'número de esas caídas pasadas' },
    acierto_historico_regla: { type: 'number', description: 'acierto de la regla en el S&P 500 en la situación más parecida (de rebound_base_rates.md)' },
    evidencia_historica: { type: 'string', description: 'números del estudio de caídas: n, media, mediana y % ganadoras a 3, 5 y 10 sesiones, en el contexto más parecido al de hoy, frente a la deriva; y qué causó las caídas pasadas más parecidas' },
    comparables: { type: 'string', description: 'cómo se comportan comparables del sector hoy y tras caídas parecidas' },
    catalizadores: { type: 'string', description: 'qué podría hacerla subir o bajar en los próximos días: resultados (fecha), eventos, recompras, cambios de índice, macro' },
    riesgos: { type: 'array', items: { type: 'string' } },
    prob_subida_3s: { type: 'number', description: 'probabilidad estimada (0-1) de que la operación (compra en la apertura siguiente, venta 3 sesiones después) gane' },
    prob_subida_10s: { type: 'number' },
    horizonte_recomendado: { type: 'integer', enum: [3, 5, 10] },
    veredicto: { type: 'string', enum: ['comprar', 'vigilar', 'descartar'] },
    tesis: { type: 'string', description: '3-5 frases: por qué rebotaría o no' },
    fuentes: { type: 'array', items: { type: 'string' } },
  },
  required: ['ticker', 'causa_caida', 'tipo_causa', 'causa_temporal', 'evidencia_historica', 'comparables', 'catalizadores', 'riesgos', 'prob_subida_3s', 'prob_subida_10s', 'horizonte_recomendado', 'veredicto', 'tesis', 'fuentes'],
}
const SKEPTIC = {
  type: 'object',
  properties: {
    ticker: { type: 'string' },
    refuta: { type: 'boolean' },
    argumentos: { type: 'array', items: { type: 'string' } },
    errores_del_analista: { type: 'string', description: 'datos o razonamientos equivocados que encontraste, o "ninguno"' },
    veredicto_final: { type: 'string', enum: ['comprar', 'vigilar', 'descartar'] },
    prob_ajustada_3s: { type: 'number' },
    confianza: { type: 'string', enum: ['baja', 'media', 'alta'] },
  },
  required: ['ticker', 'refuta', 'argumentos', 'errores_del_analista', 'veredicto_final', 'prob_ajustada_3s', 'confianza'],
}
const MARKET = {
  type: 'object',
  properties: {
    resumen: { type: 'string', description: 'qué ha pasado hoy y esta semana en el mercado de EE. UU. y por qué' },
    regimen: { type: 'string', description: 'calma, corrección o pánico, con datos (SPY/QQQ frente a sus medias, VIX si lo encuentras)' },
    sectores_castigados: { type: 'string' },
    eventos_proximos: { type: 'string', description: 'eventos de los próximos 5-10 días que pueden mover el mercado (Fed, IPC, empleo, festivos, vencimientos)' },
    implicacion_para_rebotes: { type: 'string' },
  },
  required: ['resumen', 'regimen', 'sectores_castigados', 'eventos_proximos', 'implicacion_para_rebotes'],
}
const JUDGE = {
  type: 'object',
  properties: {
    veredicto: { type: 'string', description: 'una frase: cuántas comprar y la advertencia principal' },
    compras: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          ticker: { type: 'string' }, nombre: { type: 'string' },
          peso: { type: 'number', description: 'fracción del dinero que el usuario dedica a rebotes (suma <= 1, máx. 0.25 por acción; la mitad si el mercado está en pánico)' },
          por_que: { type: 'string' }, historico: { type: 'string' },
          fecha_compra: { type: 'string' }, fecha_venta: { type: 'string' }, horizonte_sesiones: { type: 'integer' },
          prob_estimada: { type: 'number', description: 'probabilidad estimada de que ESTA operación gane (0-1)' },
          acierto_historico_regla: { type: 'string', description: 'p. ej. "59% en 2.350 caídas parecidas del S&P 500 desde 2005 (techo optimista)"' },
          acierto_historico_accion: { type: 'string', description: 'p. ej. "de 17 caídas parecidas de esta acción, ganó en 15 (88%)"' },
          riesgo_principal: { type: 'string' },
        },
        required: ['ticker', 'nombre', 'peso', 'por_que', 'historico', 'fecha_compra', 'fecha_venta', 'horizonte_sesiones', 'prob_estimada', 'riesgo_principal'],
      },
    },
    vigilar: { type: 'array', items: { type: 'object', properties: { ticker: { type: 'string' }, que_esperar: { type: 'string' } }, required: ['ticker', 'que_esperar'] } },
    descartadas: { type: 'array', items: { type: 'object', properties: { ticker: { type: 'string' }, motivo: { type: 'string' } }, required: ['ticker', 'motivo'] } },
    contexto_mercado: { type: 'string' },
    advertencias: { type: 'array', items: { type: 'string' } },
  },
  required: ['veredicto', 'compras', 'vigilar', 'descartadas', 'contexto_mercado', 'advertencias'],
}

phase('Análisis')
const marketP = agent(`${COMMON}

TU PAPEL: analista de mercado. Explica el contexto general de hoy para alguien que va a comprar acciones castigadas: qué ha pasado en el mercado de EE. UU. hoy y esta semana y por qué (busca noticias), si estamos en calma, corrección o pánico (usa el campo "mercado" del JSON del filtro y busca el VIX), qué sectores han caído más, qué eventos próximos (5-10 días) pueden moverlo todo, y qué implica para una estrategia de rebote a pocos días.`, { label: 'mercado', phase: 'Análisis', schema: MARKET })

const pairsP = pipeline(
  FIN,
  (t) => agent(`${COMMON}

TU PAPEL: analista de ${t}. Investiga a fondo si ${t} tiene buenas probabilidades de rebotar tras su caída:
1. Por qué ha caído (noticias de hoy y de los últimos días, con fecha y fuente). Clasifica la causa: fundamental grave (fraude, quiebra, pérdida de un cliente clave, rechazo regulatorio, ampliación de capital), resultados o previsiones peores, sector o mercado, analista/rumor/flujos, o desconocida. ¿Es pasajera?
2. Qué pasó históricamente tras caídas parecidas de ${t}: ejecuta drop_event_study.py con 2-4 comparables del sector (y con otros umbrales si la caída de hoy es distinta). Fíjate en el subconjunto más parecido a hoy (régimen de mercado, si está por encima o por debajo de su media de 200, tamaño de la caída) y busca qué causó 2-3 de las caídas pasadas más parecidas y cómo terminaron.
3. Comparables: ¿han caído también hoy (caída sectorial, suele rebotar mejor) o solo ${t} (problema propio)?
4. Catalizadores y riesgos para los próximos 3-10 sesiones: fecha de los próximos resultados (si caen dentro del periodo, es un riesgo grande), eventos, recompras, cambios de índice, macro.
5. Anota tres porcentajes: el acierto histórico de la REGLA en la situación más parecida (rebound_base_rates.md), el acierto histórico de ESTA ACCIÓN tras caídas parecidas (con n) y tu probabilidad estimada para la operación de ahora.
6. Estima con honestidad la probabilidad de que una compra en la próxima apertura gane si se vende 3 sesiones después, y 10 sesiones después, partiendo de la tasa histórica y ajustándola por la causa. Recomienda horizonte (3, 5 o 10 sesiones) y veredicto.`, { label: `analista:${t}`, phase: 'Análisis', schema: ANALYST }),
  (an, t) => an && agent(`${COMMON}

TU PAPEL: escéptico. Otro analista concluyó esto sobre ${t}:
${JSON.stringify(an, null, 1)}

Intenta REFUTAR su tesis de rebote. Comprueba sus datos (vuelve a ejecutar drop_event_study.py si hace falta), busca noticias que haya pasado por alto (¿la causa es más grave? ¿hay resultados o un evento binario en los próximos días? ¿rebajas de rating, demandas, ventas de directivos, ampliaciones?), cuestiona si el histórico es comparable (pocas observaciones, otro contexto) y si la probabilidad está inflada. Da tu veredicto final y una probabilidad ajustada. Si la tesis aguanta, dilo.`, { label: `esceptico:${t}`, phase: 'Análisis', schema: SKEPTIC }).then((sk) => ({ ticker: t, analista: an, esceptico: sk })),
)

const [market, pairs] = await Promise.all([marketP, pairsP])
const results = (pairs || []).filter(Boolean)

phase('Decisión')
const judge = await agent(`${COMMON}

TU PAPEL: juez final y gestor. Con todo lo de abajo, decide qué comprar (como mucho 3-5), cuánto (fracción del dinero dedicado a rebotes: a partes iguales salvo que la convicción justifique inclinar un poco; máximo 0,25 por acción; la mitad del tamaño si el mercado está en pánico), cuándo comprar (próxima apertura de Nueva York tras la captura; si la captura es de antes del cierre, "si al cierre sigue así") y cuándo vender (apertura N sesiones después según el horizonte elegido). Calcula las fechas con el calendario de la bolsa de Nueva York: pip install -q pandas_market_calendars; python3 -c "import pandas_market_calendars as m; print(m.get_calendar('NYSE').valid_days('AAAA-MM-DD','AAAA-MM-DD'))". Una acción va a compras solo si el escéptico no la ha refutado con argumentos sólidos. Explica cada decisión en una o dos frases sencillas. Para cada compra da SIEMPRE los tres porcentajes de acierto: el de la regla en general (de rebound_base_rates.md, en la situación más parecida), el de esta acción tras caídas parecidas (con n) y la probabilidad estimada ahora, explicando en una frase por qué la estimada sube o baja respecto a los históricos. Si n es pequeño (< 10), dilo. Lista las de vigilar (qué tendría que pasar) y las descartadas con su motivo (incluye las que el filtro numérico descartó, que están en el JSON). Notas del usuario: ${A.usuario || 'ninguna'}.

Contexto de mercado:
${JSON.stringify(market, null, 1)}

Análisis por acción (analista + escéptico):
${JSON.stringify(results, null, 1)}`, { label: 'juez', phase: 'Decisión', schema: JUDGE })

return { market, pairs: results, judge }
