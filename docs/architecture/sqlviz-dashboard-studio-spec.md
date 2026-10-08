# Dashboard Studio: alcance, edición e inferencia

**Fecha:** 2026-10-05; actualización de navegación: 2026-10-06. **Estado:**
especificación para implementar, con navegación entregada según
[su documento de implementación](sqlviz-navigation.md). Los contratos visuales,
modos pantalla/scroll e inferencia descritos aquí siguen pendientes.
La [composición de navegación y filtros](sqlviz-navigation-and-filters-spec.md)
precisa la cabecera de lectura, los estados de contexto aplicado y los límites
del runtime. Su [primer incremento](sqlviz-reader-context.md) está implementado
localmente; configuración publicada y contratos completos siguen pendientes.
Incorpora la petición de libertad visual equilibrada, pantalla sin
scroll o con scroll y sidebar completamente ocultable. Las capturas aportadas
por el usuario son referencia para los estados abierto/oculto, no para copiar
el estilo de otra aplicación ni inferir comportamientos que no muestran.

## 1. Orden de trabajo y criterio de cierre

Trabajar una capacidad completa a la vez, cruzando las capas estrictamente
necesarias. Un inspector no está terminado hasta que valida, guarda, reabre y
renderiza sus cambios también en el viewer. La separación arquitectónica sigue
vigente; la unidad de entrega es una experiencia verificable.

| Orden | Foco | Cuándo podemos pasar al siguiente |
| --- | --- | --- |
| 1 | Aplicación y dominio: seguridad, integridad y persistencia | P0 cerrados; BP-01–05 corregidos; permisos, atomicidad y persistencia cubiertos por regresiones |
| 2 | Contrato visual y de página | IDs estables; recomendación y overrides separados; propiedades versionadas y restaurables; mismos valores en editor/viewer |
| 3 | Lienzo y navegación | Ocultar sidebar recupera todo su ancho; modos pantalla/scroll; drag/resize y undo/redo; ajustes sobreviven a recarga |
| 4 | Inferencia y renderizado completos | Campos/series/unidades correctos, evaluación independiente y recomendaciones comparables; cambios manuales respetados |
| 5 | Acabado de la experiencia | Plantillas, formatos, accesibilidad, rendimiento y pruebas visuales/E2E en la matriz soportada |

La recopilación de casos de inferencia y el diseño del contrato empiezan desde
ahora para orientar las etapas 2–4. No se amplía a ETL general, más conectores o
modelado avanzado mientras este recorrido esté incompleto.

«Impecable» se traduce en criterios comprobables para el alcance soportado:
sin defectos críticos conocidos, sin pérdida de ajustes, sin datos incorrectos
silenciosos y con limitaciones visibles. No promete perfección universal ni
prohíbe revisar una capa cuando nuevos casos aporten evidencia.

## 2. Libertad visual con límites comprensibles

Principio: **SQL aporta datos; la inferencia propone; el autor decide.**
El usuario puede aceptar un dashboard automático y después personalizar solo
lo que necesita. SQLviz conserva ambos caminos sin exigir configurar todo.

| Ámbito | Controles del autor | Restricción útil |
| --- | --- | --- |
| Página | Pantalla/scroll, fondo, espaciado, tema, secciones y disposición | Legibilidad y reglas responsive explícitas |
| Panel | Posición, ancho/alto, título, descripción, borde y fondo | Alineación a grid, dimensiones mínimas y ausencia de solapamientos accidentales |
| Datos del gráfico | Dimensión, métricas, series, orden y agrupación | Compatibilidad de tipos, unidades y granularidad; cambios de consulta son explícitos |
| Presentación | Paleta, colores por serie, leyenda, etiquetas, ejes y formatos | No convertir unidades ni alterar la interpretación de datos silenciosamente |
| Interacción | Filtros, tooltips y navegación contextual | Siempre dentro del alcance autorizado de datasets y campos |

Inspector por secciones: Datos, Visual, Formato y Posición. Mostrar primero las
propiedades habituales y permitir desplegar opciones avanzadas. Cada propiedad
admite «Automático» o un valor explícito; restablecer es distinto de guardar una
copia del valor que hoy recomendó el motor.

No exponer el objeto bruto de ECharts ni permitir JavaScript/HTML arbitrario como
atajo de personalización. La amplitud del editor crece sobre un contrato propio.
Las opciones existentes de selección X/Y deben persistirse y aplicarse de verdad
en todos los renderers antes de añadir más controles.

## 3. Pantalla completa, modo pantalla y modo scroll

Son decisiones independientes:

- **Página en modo pantalla:** ocupa el área disponible de la aplicación y
  distribuye sus paneles sin scroll vertical del dashboard.
- **Página en modo scroll:** usa el ancho disponible y crece verticalmente.
- **Modo presentación:** oculta editor/inspectores y reduce controles. Solicitar
  fullscreen del navegador es una acción adicional; no se presupone permiso.

Power BI distingue tamaño de página y modos de visualización como ajustar a
página/ancho/tamaño real. Esa distinción resulta útil, pero SQLviz no debe
confundir escalar un lienzo fijo con redistribuir paneles al espacio disponible.
[Referencia de Microsoft](https://learn.microsoft.com/en-us/power-bi/create-reports/power-bi-report-display-settings).

### Modo pantalla

Medir el contenedor real, descontando cabecera, filtros visibles y márgenes.
Distribuir altura entre filas con pesos y mínimos según el contenido; ocupar
toda la altura útil, sin depender de alturas de panel fijas heredadas del motor.

La condición de viabilidad es:

```text
sum(altura mínima de cada fila) + espacios + padding <= altura disponible
```

Si no se cumple, no ocultar paneles con `overflow: hidden` ni reducir el texto
hasta volverlo ilegible. Mostrar al autor el conflicto y permitir reorganizar,
reducir contenido, dividir en páginas o escoger scroll. El viewer ofrece una
alternativa legible cuando el tamaño no está soportado; nunca recorta información
sin indicarlo. El modo elegido por el autor no se sobrescribe por ese fallback.

El objetivo inicial sin scroll se valida en viewport 1366×768, 1440×900 y
1920×1080, considerando el alto real del área útil de cada shell. Un dashboard
con más contenido del que físicamente cabe necesita paginación o scroll: el
producto debe explicar ese límite, no esconderlo.

En tablas, priorizar paginación para la vista pantalla. Scroll interno de una
tabla debe ser deliberado y visible, no una manera de aparentar que todo cabe.
En móvil y con zoom grande, ofrecer lectura con reflow/scroll o páginas, además
de conservar la configuración de escritorio. La [guía W3C de reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow)
explica por qué no se debe asumir que toda una página está exenta por contener
gráficos o tablas bidimensionales.

### Modo scroll

Grid adaptable al ancho, alturas por panel y un único scroll vertical principal.
Preservar orden/posiciones del autor y la posición de lectura al filtrar.
La cabecera y filtros pueden permanecer disponibles sin ocupar un espacio
desproporcionado. Cambiar a modo pantalla ofrece vista previa y conserva la
configuración previa de scroll para poder volver sin perder trabajo.

### Contratos propuestos

Separar `PageSpec` (modo, layout por breakpoint, tema), `PanelSpec` (dataset,
encoding, formato y overrides) y preferencias de interfaz del usuario. Guardar
el modo/layout en la revisión del dashboard; guardar sidebar e inspector como
preferencias privadas. Migrar proyectos actuales a modo scroll para preservar
su comportamiento, sin inferir que ya son compatibles con modo pantalla.

La UI mide el viewport y resuelve dimensiones según el contrato. Eso es layout
de presentación, no inferencia de negocio. El comentario actual de
`DashboardGrid.svelte` que prohíbe toda lógica cliente de layout debe precisarse:
el navegador necesita adaptar y permitir editar geometría.

`EChartsRenderer.svelte` ya usa `ResizeObserver` y `resize()`; conservarlo y
comprobarlo al ocultar navegación, abrir inspector y cambiar de modo. No basta
con responder al resize de la ventana. [Referencia ECharts](https://echarts.apache.org/handbook/en/concepts/chart-size/).

## 4. Navegación que recupera el ancho completo

Implementada en editor y viewer de workspace: panel de escritorio de 260 px,
oculto sin rail, diálogo modal hasta 900 px y búsqueda. Ver comportamiento,
evidencia y límites en [Navegación del workspace](sqlviz-navigation.md).
El modo de concentración oculta controles; no implementa el modo pantalla.

Estados de navegación:

| Estado | Espacio ocupado | Recuperar navegación |
| --- | --- | --- |
| Abierto, fijado en escritorio | Ancho del sidebar | Botón para ocultarlo |
| Oculto | **0 px**, sin rail de iconos | Botón visible en cabecera, accesible por teclado |
| Abierto temporalmente | Overlay, sin cambiar el canvas | Botón de cabecera; cerrar con Escape/clic exterior y devolver foco |

En pantallas estrechas usar overlay; en escritorio permitir fijarlo. El estado
oculto no depende de hover ni de descubrir una zona invisible. La cabecera
mantiene nombre/ruta del dashboard y acceso a búsqueda/cambio rápido. Los menús
portaleados dentro de la navegación deben respetar el foco y el cierre.

Al ocultarlo, retirar también sus elementos del orden de tabulación. El botón
declara nombre, `aria-expanded` y relación con el panel. Respetar movimiento
reducido; guardar preferencia y restaurar navegación con teclado/táctil.

Aplicar la misma experiencia al editor y al viewer de workspace. El viewer de
un único dashboard no necesita un árbol vacío. El modo presentación siempre
dispone de una salida descubrible y no modifica la preferencia de sidebar.

## 5. Inferencia: evidencia de la limitación actual

El pipeline tiene varias etapas, pero la calidad final depende también de cómo
se asignan campos y cómo se representa la especificación.

Reproducción con `infer(sql, schema, data)`, sin conexión brain ni ejecución SQL,
usando seis filas sintéticas (enero–junio 2026, `revenue=100*mes`, `cost=60*mes`):

| Caso | Resultado observado |
| --- | --- |
| `SELECT month, revenue FROM monthly_sales ORDER BY month`, DATE/DOUBLE | `histogram`, X=month, Y=revenue |
| Misma información con `SELECT revenue, month ... ORDER BY month`, DOUBLE/DATE | `histogram`, X=revenue, Y=month |
| `SELECT month, revenue, cost ... ORDER BY month`, DATE/DOUBLE/DOUBLE | `table` |
| Pedir explícitamente `line` al VisualSpecBuilder con month/revenue/cost | X=month, Y=cost; revenue omitido |

No hay una obligación universal de elegir línea para toda consulta temporal,
pero una serie mensual debe permitir una tendencia válida y una fecha no debe
convertirse accidentalmente en medida numérica por el orden del SELECT.

Evidencia estática: `VisualSpecBuilder.build` usa primera/última columna en
varios tipos; `EChartsRenderer` toma `y_fields[0]` en líneas/barras. Mejorar solo
el ranking de charts no corrige campos erróneos ni habilita multiserie.

El benchmark actual `tests/benchmark/run_benchmark.py` se ejecutó en esta revisión:
**52 casos; 100% intent_accuracy, chart_accuracy y quality_pass_rate**. Esto
significa que satisface esas anotaciones. La última métrica compara etiquetas
internas de calidad; no mide estética, legibilidad ni aceptación del usuario.
Los resultados anteriores demuestran un hueco de evaluación fuera de ese corpus.

## 6. Cómo mejorar la inferencia de extremo a extremo

Orden de trabajo dentro de la etapa 4:

1. Validar SQL/esquema/perfil: roles semánticos, tipos, cardinalidad, temporalidad,
   granularidad, valores nulos, unidades conocidas y distribución. El alias
   aporta evidencia, pero no sustituye el significado confirmado por el autor.
2. Generar especificaciones candidatas completas: tipo + campos + series +
   orden/formato. Priorizar corrección analítica antes de puntuar preferencias.
3. Rechazar candidatos incompatibles: fechas como medida por accidente, series
   omitidas, unidades mezcladas sin aviso, gráficos de composición con semántica
   inválida, exceso de categorías ilegibles o agregaciones inventadas.
4. Puntuar idoneidad para la pregunta y espacio disponible. Mostrar pocas
   alternativas útiles, con explicación concreta. Una tabla es alternativa
   legítima; abstenerse ante ambigüedad no cuenta como acierto de selección.
5. Renderizar fielmente la spec: varias series, fechas/orden, null frente a cero,
   moneda/porcentaje, leyendas y tooltip. Evitar que `Number(null)` convierta datos
   ausentes en ceros. El agregado o downsampling debe ser explícito y verificable.
6. Recomendar composición del dashboard respetando paneles fijados, modo de
   página y preferencias. Reordenar requiere acción explícita del autor.

Un score normalizado no es probabilidad de acierto. Calibrar confianza contra
anotaciones independientes antes de mostrar porcentajes como certeza. La IA,
si se evalúa más adelante, debe competir con esta base sobre los mismos casos;
su presencia no demuestra calidad.

## 7. Criterios para declarar pulida esta capacidad

Crear un corpus versionado con casos representativos y adversariales. Separar
desarrollo y evaluación reservada por familias de consultas/datasets, evitando
variantes casi idénticas en ambos. Anotar conjuntos de soluciones aceptables
cuando varias gráficas sean válidas y acordar casos ambiguos con revisión humana.

| Dimensión | Evidencia exigida |
| --- | --- |
| Corrección | Casos críticos de campos, series, fechas, nulos y unidades sin errores silenciosos; no perder métricas al renderizar |
| Selección | Medir acierto de especificación completa, top-3, abstención y cobertura por familia; comparar contra baseline con igual cobertura |
| Robustez | Reordenar columnas, cambiar alias o variar filas no rompe el significado; casos pequeños, vacíos y de alta cardinalidad |
| Control del autor | Ajustes persisten tras ejecutar, filtrar, recargar, publicar y abrir como viewer; restaurar automático es reversible |
| Layout | Sin scroll vertical en configuraciones pantalla viables; cero ancho reservado con sidebar oculto; sin clipping en la matriz definida |
| Responsive/accesibilidad | Teclado, zoom 200%, móvil, alternativa tabular y salida de presentación; limitaciones comunicadas |
| Rendimiento | p50/p95 y memoria medidos con hardware, filas/paneles y fases declaradas; separar SQL, inferencia y renderizado |
| Percepción | Revisión de dashboards completos y tareas con usuarios; registrar qué corrigen y por qué |

Los umbrales de selección/latencia se fijan tras medir la nueva línea base y antes
de ajustar el motor contra el conjunto reservado. No usar el 100% de los 52 casos
actuales como afirmación comercial de precisión universal.

Primeros escenarios de aceptación: dashboard ejecutivo de cuatro paneles sin
scroll; dashboard exploratorio con scroll; tendencia con dos métricas compatibles;
misma consulta con columnas reordenadas; navegación oculta/abierta; overrides
preservados tras actualizar datos. Terminar ese recorrido antes de sumar tipos
de gráfico por cantidad o capacidades de plataforma ajenas a esta etapa.
