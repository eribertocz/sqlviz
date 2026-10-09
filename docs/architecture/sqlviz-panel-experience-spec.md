# Experiencia de paneles y áreas del dashboard

**Fecha:** 2026-10-08. **Estado:** diseño pendiente de implementación.
Complementa el [plan operativo](sqlviz-studio-delivery-plan.md) y el
[contrato de geometría](sqlviz-canvas-contract.md). No cambia el formato `.sqlviz`
ni habilita nuevas interacciones por sí solo.

## Observación del código actual

`DashboardGrid.svelte` usa doce columnas, spans y alturas explícitas, pero coloca
paneles por flujo automático; todavía no representa las posiciones manuales S0.
`PanelRenderer.svelte` convierte la tarjeta completa en botón de selección,
incluyendo controles internos y el gráfico. El menú se posiciona sobre la esquina
superior derecha mientras la cabecera tiene sus propios badges; la tarjeta recorta
overflow. Los editores de ejes se superponen al gráfico y hay metadata técnica en
un footer permanente en edición. Estos son hallazgos del código, no un ensayo visual.

## Grid CSS, geometría y áreas del producto

CSS Grid pertenece al adaptador web del canvas. `grid-area` puede colocar un
elemento por líneas o área nombrada; `grid-template-areas` define regiones
rectangulares de una plantilla. Referencia:
[especificación CSS Grid](https://www.w3.org/TR/css-grid-2/#named-areas).

La autoridad persistida continúa siendo el contrato de layout por IDs, doce
columnas y coordenadas verticales en píxeles. El adaptador debe representar esa
geometría exactamente: no sustituir `top_px` por filas automáticas, ni dejar que
el alto de un vecino mueva otro panel. La elección entre tracks explícitos y
posicionamiento dentro del grid se valida con el recorrido S1; no obliga al autor
a escribir CSS ni introduce una segunda geometría canónica.

### Un panel alto junto a dos paneles apilados

Este es un requisito del lienzo S1/S2, no de las secciones S6:

```text
         columnas 1–6          columnas 7–12
       ┌─────────────────┬─────────────────┐
       │                 │     Panel B     │
       │     Panel A     ├─────────────────┤
       │                 │     Panel C     │
       └─────────────────┴─────────────────┘
```

El autor puede invertir los lados y elegir otros spans/altos respetando las doce
columnas, separación y mínimos. Un panel alto no obliga a dejar espacio vacío bajo
su vecino corto ni empuja automáticamente el siguiente gráfico debajo de ambos.
Los límites visuales de filas ayudan a alinear, pero no atan todos los paneles a
una misma altura. Tampoco son el orden de consultas SQL.

Con dos paneles de 300 px y gap de 16 px, A mide 616 px; B comienza en 0 y C en
316 px. El núcleo S0 admite ambas orientaciones en `screen` y `scroll`, con
coordenadas exactas. Todavía falta persistir y representar este caso en la UI.
S1.2d/S1.2e deben demostrar la composición con controles y guardado/reapertura;
S2 añade drag/resize. La altura relativa al viewport se resuelve posteriormente
en S6; no posterga la composición asimétrica básica.

Las áreas del producto —Resumen, Tendencias, Detalle— son grupos con identidad,
miembros, orden y título opcional. En S6 se concreta su contrato y conversión desde
layout plano, con preview y revisión. Una plantilla de áreas puede compilar a
`grid-template-areas` si su geometría lo permite; el string CSS no es su identidad
ni su formato de almacenamiento. No crear un grid independiente por área que
rompa la alineación de las doce columnas globales. Comenzar con un nivel de grupos;
movimientos conjuntos deben validar la composición completa sin empujar vecinos.

## Guías de dimensionado y precisión

**Requisito de producto:** combinar ayuda visual durante drag/resize con entrada
numérica exacta. No depender de que el autor acierte una medida con el mouse.
Referencias: [guías de Power BI](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-gridlines-snap-to-grid),
[cuadrícula dinámica de Visio](https://support.microsoft.com/en-us/visio/improve-shape-placement-by-using-the-dynamic-grid)
y [dimensiones/posición exactas en Visio](https://support.microsoft.com/en-us/visio/set-the-dimensions-and-position-of-a-shape-by-using-the-size-position-window).

| Ayuda | Comportamiento previsto |
| --- | --- |
| Alineación | Guías temporales de bordes y centros entre paneles; mostrar solo candidatos relevantes y válidos |
| Tamaño coincidente | Indicar cuando el borde ajustado iguala el alto/ancho de otro panel, sin modificar el vecino |
| Separación | Medidas entre paneles y márgenes; identificar gaps iguales y falta de espacio |
| Medida en vivo | Etiqueta de ancho/alto y tramo de columnas durante resize; posición durante drag, sin desplazar el gráfico |
| Inspector numérico | Campos de posición/tamaño con unidades y valores efectivos; draft, validación y confirmación sobre el mismo contrato del gesto |
| Ajuste fino | Alto/Y en pasos de 1 px; incremento mayor con modificador. Teclas solo con foco de layout, nunca dentro de un input o gesto del gráfico |
| Magnetismo | Preferencia visible para activar/desactivar ayudas; suspensión temporal durante el gesto con alternativa por clic/touch. No desactiva límites ni validación de colisiones |

Una entrada numérica exacta no se redondea al múltiplo de una cuadrícula ni al
tamaño de otro panel. Si el candidato es inválido, explicar el límite y conservar
el borrador. Las guías no autorizan solapamientos ni reducen los mínimos del visual.
Reglas y cotas adicionales se revelan bajo demanda, sin barras permanentes en el
viewer ni líneas que resten legibilidad a los datos.

### Precisión horizontal y las doce columnas

S0 representa `top_px` y `height_px` enteros, pero `column`/`column_span` son columnas,
no X/ancho en píxeles. Mostrar el ancho medido no lo vuelve un ancho editable.
La UI debe distinguir esas unidades y no mostrar un campo de precisión ficticia.

La dirección recomendada para el primer Studio es mantener X/ancho por columnas
y alto/Y por píxeles. La ampliación horizontal contemplada anteriormente deja
de ser un prerrequisito S1.2a; un lienzo completamente libre requiere una necesidad
validada y decisión separada de anclajes, viewport y colisiones. No guardar ancho
derivado del DOM como otra autoridad ni mostrarlo como un valor editable exacto.
Las medidas horizontales efectivas se muestran en el gesto como información.

Separar coordenadas del canvas de las coordenadas del puntero: incluir origen,
scroll y escala de edición. Zoom o densidad de pantalla no cambian una altura
guardada de 301 px. La tolerancia de magnetismo se mide en espacio visual y se
convierte al canvas; empates deterministas y retención del objetivo evitan saltos
entre guías. Snap se aplica al candidato antes de validar, con preview de la medida
real, no como una corrección invisible después de guardar.

El ejemplo de A alto con B/C apilados debe ofrecer alineación de bordes y mostrar
`300 + 16 + 300 = 616 px`; poder fijar A a 617 px sin ajustar B/C es igualmente
válido si cabe. Validar entrada numérica frente a gesto, magnetismo desactivado,
límites, teclado/touch y zoom/scroll antes de declarar precisión entregada.

## Mínimos y bloques de texto

### Precisión dentro de un tamaño válido

Una altura de 2 px se rechaza. La política actual de paneles y el núcleo S0 exigen
al menos 120 px; una comprobación enfocada confirma el rechazo sin cambiar la
altura anterior. Esto no garantiza que todo gráfico sea legible a 120 px.

En S1.2a–d definir mínimos estructurales por tipo y perfil, junto con los mínimos
de contenido aportados por el renderer. La UI mide cabecera, título, ejes, leyenda
y área de trazado disponible; no aplica el mismo mínimo a KPI y línea multiserie.
El servidor conserva las restricciones estructurales del tipo/perfil autorizado;
una medida suministrada por el cliente no puede rebajarlas.

Durante resize mostrar el límite y candidato válido más cercano; confirmar solo
una medida válida y visible. Si se escribe un número menor, conservar el borrador,
explicar el mínimo y ofrecer aplicarlo, sin reemplazar silenciosamente el número.
La legibilidad del formato/densidad requiere diagnóstico adicional: más alto no
arregla unidades incorrectas ni demasiadas series. No ocultar ejes o reducir la
fuente automáticamente para aceptar una altura imposible.

### Insertar títulos, subtítulos y texto

Ofrecer «Insertar → Texto» con roles Título, Subtítulo, Encabezado de sección y
Texto descriptivo. Presets de tipografía y espaciado coherentes; el autor puede
editar contenido, alineación, ancho por columnas y presentación bajo los mismos
controles del lienzo. Texto plano multilínea en la primera entrega, sin exigir
Markdown, SQL, dataset ni un renderer ECharts.

El bloque tiene ID estable y tipo propio en la composición. Comparte posición,
selección, movimiento, borrador, guardado y undo; no fabrica un panel SQL vacío.
S1.2a debe reservar el contrato discriminado de referencias visual/texto y mínimos
por tipo; S1.3 concreta contenido y persistencia. No bajar el mínimo global de
gráficos para acomodar títulos ni cambiar el contrato S0 sin adaptación/versionado.

El alto sugerido depende de líneas, tipografía, padding y ancho disponible: un
encabezado de una línea no hereda la caja de 120 px de los gráficos. Cambiar texto
o tamaño de fuente propone el ajuste de altura con preview; no solapa ni empuja
otros elementos por sorpresa. En contenido largo, explicar el espacio requerido
antes de guardar, sin cortar texto silenciosamente en el viewer.

Presentación inicial discreta, sin cabecera de tarjeta ni acciones de gráfico.
«Texto descriptivo» es párrafo; títulos/encabezados conservan una jerarquía
semántica coherente con el dashboard, sin escoger nivel solo por tamaño de fuente.
El orden de lectura y foco sigue la composición, también en móvil. El contenido
se persiste como texto, sin interpretar HTML. Edición solo con permiso de autor;
publicación/preview comparten contenido y geometría confirmados.

Los bloques sirven en `scroll` y `screen`, donde cuentan para el espacio requerido.
S6 puede asociar un encabezado a una sección, pero no exige esperar a grupos
avanzados para insertarlo. El título de una sección tendrá una fuente única:
si se vincula a un bloque, no guardar otro texto independiente en el grupo.
Cambiar una consulta conserva estos bloques y posiciones. El mapa puede mostrar
su pertenencia al dashboard, sin inventar dependencias de datasets.

Primer recorrido: insertar «Ventas» → añadir subtítulo → situar gráficos debajo
→ agregar «Detalle por región» más abajo → guardar → reabrir → viewer. Comprobar
título corto, multilínea, ancho estrecho, límite de altura, colisión al crecer,
cancelación, permisos, tema/zoom y publicación. El texto no debe ejecutar SQL.

## Panel centrado en los datos

El panel comparte estructura entre editor y viewer: cabecera, contenido y estados.
Las herramientas de edición no deben cambiar sus dimensiones al aparecer.

| Aspecto | Criterio previsto |
| --- | --- |
| Superficie | Tokens compartidos de espaciado, tipografía, borde y radio; sombra discreta solo cuando ayuda a diferenciar elevación |
| Cabecera | Título y contexto necesario; acciones con espacio reservado, sin superponerse a título o estados. Permitir ocultar la cabecera en un diseño explícito, conservando nombre accesible |
| Herramientas | Selección/hover/foco revelan acciones secundarias sin mover el gráfico; touch tiene acceso por tap. Ninguna acción depende exclusivamente de hover |
| Selección y drag | Cabecera con acceso explícito a propiedades y zona de arrastre diferenciada; el cuerpo conserva tooltip, zoom, selección y scroll |
| Contenido | Área útil medida después de cabecera/leyenda/controles; adaptar ECharts, KPI y grilla sin recortar ejes, etiquetas o errores |
| Diagnósticos | Tiempo de ejecución, SQL e inferencia bajo demanda en contexto; mantener visibles los estados relevantes de error, truncamiento y datos anteriores |
| Menú | Una entrada de opciones; capa de popover que no quede recortada por la tarjeta, con Escape, foco/restauración y navegación accesible |
| Edición de ejes | Controles fuera de la zona de trazado o contexto de formato; si hay edición directa, medir espacio y no ocultar datos ni mensajes de validación |
| Estados | Carga inicial, actualización, vacío, fallo, datos anteriores y referencia incompatible; preservar contenido confirmado cuando corresponda y explicar su frescura |
| Viewer | Sin tiradores, selección de autor ni metadata de desarrollo; acciones de lectura según capacidades y permisos |

Usar regiones y títulos semánticos; evitar representar toda una tarjeta con
controles interactivos como un único botón. Un borde de selección no cambia
medidas y el foco visible no depende solo del color. No indicar capacidad de
edición si no existe una acción autorizada. Movimiento reducido, claro/oscuro,
teclado, touch y zoom acompañan cada incremento.

El contenedor conoce selección, acciones y medidas. Los renderers reciben datos,
configuración y área disponible, sin administrar layout persistido, identidad ni
permisos. Reutilizar componentes accesibles y tokens existentes; no crear un menú
o un sistema de estilos distinto para cada familia de gráfico.

## Entregas pequeñas y cierre

| Parte | Etapa | Cierre |
| --- | --- | --- |
| P1a | S1.2d | Estructura/tokens de panel, cabecera y contenido; misma geometría en editor/viewer y títulos largos sin colisión |
| P1b | S1.2d | Selección explícita y opciones accesibles; popovers sin recorte, foco/Escape/touch y acciones sin cambios de tamaño |
| P1c | S1.2e | Estados, diagnóstico contextual y revisión visual en claro/oscuro, tamaños estrechos y alturas mínimas; guardar/reabrir/viewer |
| P2 | S2.1–S2.6 | Drag/resize sobre esa estructura, tiradores recuperables, cancelación/undo y gestos del gráfico intactos |
| P3 | S4.2/S4.5 | Builder/experto contextual, edición de títulos/ejes sin superposición y personalizaciones preservadas |
| P4 | S6 | Áreas/plantillas y pantalla/scroll sobre el mismo panel; mínimos medidos y adaptación sin sobrescribir diseño desktop |

Antes de cerrar P1, observar líneas multiserie, barras con etiquetas largas, KPI
y tabla con scroll. Incluir paneles de distinto alto junto a otros, último panel
del viewport, título largo con badges, menú cerca de bordes y gráfico interactivo.
Registrar evidencia visual y funcional a 1366×768, 1440×900 y 1920×1080, móvil y
zoom de 200 %. Pasar checks estáticos no acredita este acabado. S8 completa la
evaluación del producto; no pospone estos criterios básicos del panel.
