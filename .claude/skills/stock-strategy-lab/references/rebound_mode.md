# Modo rebote: de una captura de "las que más caen hoy" a un plan de compra y venta

Objetivo: en pocos minutos y con pocos tokens, decirle al usuario cuáles de las acciones que más han caído tienen más
probabilidad de rebotar, cuánto poner en cada una, cuándo comprar y cuándo vender, y por qué descartar el resto. Sin
agentes, sin LEAN, sin el estudio completo. Coste orientativo: unos céntimos o decenas de céntimos de dólar por uso.

## Por qué estos criterios (y su límite)
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

## Procedimiento
1. **Lee la captura.** Extrae para cada fila: ticker (o nombre), variación de hoy en %, precio si aparece, y la hora o
   si el mercado está cerrado. Si el bróker muestra nombres y no tickers, tradúcelos al ticker de EE. UU. y, si hay
   duda, pregunta antes de seguir. Ignora valores no estadounidenses, ETFs apalancados, warrants y acciones de menos de
   5 $ (dilo en una línea). Si la captura es ilegible o cortada, pide otra.
2. **Ejecuta el script** con todo lo extraído, cada acción como `TICKER:%hoy@precio` (es barato: segundos y sin tokens
   de razonamiento):
   `pip install -q pandas_market_calendars 2>/dev/null; python3 <skill_dir>/scripts/rebound_screen.py MU:-11.01@629.79 AMD:-8.86@413.27 ... [--after-close]`
   Con precio y % juntos el script detecta si sus datos ya incluyen el movimiento de la captura (fuente ya
   actualizada o captura antigua) y no lo cuenta dos veces; si el precio y el % no cuadran, lo avisa.
   Usa `--after-close` si la captura es posterior a las 16:00 de Nueva York (22:00 en España peninsular); si no, el
   dato de hoy es provisional y el plan será "si al cierre sigue así, compra mañana en la apertura".
3. **Comprueba la noticia solo de las finalistas** (las CANDIDATA mejor puntuadas, como mucho 5): una búsqueda web por
   acción, "<ticker> stock falls why <fecha>". Descarta la acción si la caída se debe a: resultados o previsiones
   peores de lo esperado, recorte de dividendo, fraude o investigación, quiebra o reestructuración, ampliación de
   capital, rechazo regulatorio, pérdida de un cliente clave o rebaja de rating de crédito. Mantenla si la caída es
   por el mercado general, rotación sectorial, un comentario de un analista, una noticia de un competidor o pánico sin
   noticia concreta. Si no encuentras el motivo, dilo y baja su prioridad.
4. **Decide**: como mucho 3-5 compras, priorizando el score del script, que sigan cerca o por encima de su media de 200
   sesiones y con evidencia propia positiva (sus caídas pasadas rebotaron más que su deriva normal). Si el script dice
   `mercado_en_panico=True`, los rebotes suelen ser mayores pero más arriesgados: mismas reglas con la mitad de tamaño.
5. **Responde** con la plantilla de abajo, en el idioma del usuario, sin jerga.

## Plantilla de respuesta
1. **Veredicto en una frase**: cuántas comprarías de la lista y la advertencia de que los criterios son provisionales.
2. **Compraría** (una línea por acción): ticker y nombre, por qué (caída de X% en 5 días, sigue por encima de su
   tendencia, sin mala noticia: motivo de la caída), y qué pasó en el pasado tras caídas parecidas de esa misma acción
   ("de N veces, subió en X; media +Y% en 3 días").
3. **Cuánto**: divide el dinero que el usuario dedica a rebotes entre las elegidas, a partes iguales, sin pasar de un
   20-25% de ese dinero por acción (la mitad si el mercado está en pánico). Ejemplo con 1.000 €.
4. **Cuándo comprar**: en la apertura de la próxima sesión (indica la fecha, la hora de Nueva York y la de España), con
   orden a mercado en la apertura. Si la captura es de antes del cierre: "si al cierre sigue cayendo al menos lo mismo".
5. **Cuándo vender**: en la apertura de la 3.ª sesión después de comprar, con la fecha exacta del plan del script, pase
   lo que pase (en TSLA los stops y los objetivos de beneficio no mejoraban la regla).
6. **Descartadas**: una línea por acción con el motivo (cuchillo cayendo, mala noticia, poco líquida, caída pequeña).
7. **Qué esperar**: la mayoría de rebotes son pequeños; alguna vez una sigue cayendo; no meter más dinero del que se
   está dispuesto a perder en una operación.
8. Una línea: no es asesoramiento financiero.

## Para gastar pocos tokens
- Manda la captura después del cierre de Nueva York (datos definitivos, sin "si al cierre...").
- Basta una captura legible con ticker y % del día; no hace falta abrir cada acción.
- No hagas más de una búsqueda web por finalista ni análisis adicionales salvo que el usuario los pida.
