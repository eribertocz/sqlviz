# Cobertura visual: ECharts, datos y niveles de autoría

**Revisión:** 2026-10-08. **Estado:** objetivo y matriz de trabajo; no declara
nuevas familias implementadas. Complementa la
[arquitectura de inferencia](sqlviz-semantic-inference-architecture.md) y la
[decisión de autoría](sqlviz-visual-authoring-decision.md).

## Inventario revisado y alcance real

Se revisó la [galería oficial](https://echarts.apache.org/examples/en/index.html)
con JavaScript, el [índice oficial](https://echarts.apache.org/en/llms.txt) y los
exports de ECharts **6.1.0 instalado**. El núcleo exporta las 23 familias de
series enumeradas abajo, incluida `chord`. El runtime actual de SQLviz acepta
ocho identificadores legacy: `kpi`, `line`, `bar`, `bar_horizontal`, `pie`,
`scatter`, `histogram`, `table`. KPI/tabla son visuales de producto; horizontal
es una variante de barras e histograma requiere una política de bins.
No equivalen a ocho familias nativas independientes.

Que una biblioteca esté instalada no implica que SQLviz soporte todos sus tipos.
Ampliar un enum sin bindings, adaptación, persistencia y renderizado no entrega
cobertura. Esta matriz no amplía el PATCH legacy ni sustituye `VisualSpec` v1.

## Tres niveles sobre la misma visualización

| Nivel | Alcance objetivo |
| --- | --- |
| **Básico — Inferencia automática** | Proponer solo cuando datos, semántica y recursos ofrecen evidencia suficiente; mostrar alternativas, faltantes o abstención. No inferir siempre todas las familias |
| **Intermedio — Visual Builder** | Seleccionar familia, asignar roles a inputs/campos, validar forma y ajustar opciones frecuentes. Controles específicos revelados bajo demanda; no duplicar toda la API del motor |
| **Experto — ECharts native options** | Configuración JSON nativa amplia, componentes y combinaciones, con referencias a datos/recursos autorizados y opciones preservadas fuera del builder. `custom` mediante renderizadores registrados; extensiones con capacidades explícitas |

El objetivo del experto cubre las **23 familias del núcleo**, con sus requisitos.
GL y plugins amplían ese objetivo cuando están instalados y verificados. JSON
serializable no representa una función JavaScript arbitraria. No prometer
ejecutar cualquier ejemplo copiado de la galería con solo pegar su configuración.

## Familias del núcleo y contratos de datos necesarios

Todas las filas son **pendientes de cobertura completa en SQLviz**. Los roles,
adaptadores y comprobaciones son diseño propuesto. Una recomendación automática
es además una capacidad independiente, que requiere evidencia del propósito.

| Serie ECharts | Roles o estructura | Comprobación de SQLviz prevista |
| --- | --- | --- |
| `line` | X temporal/numérica/categórica + una o más medidas; agrupación opcional | Orden, huecos, granularidad, unidades y estabilidad de series |
| `bar` | Categoría + medidas o categoría/serie/valor | Agregación explícita, negativos, stacking coherente y cardinalidad |
| `pie` | Categoría + magnitud | Valores admisibles, parte/total y categorías; no convertir cualquier ratio en participación |
| `scatter` | X/Y numéricas; tamaño/color/serie opcionales | Pares completos, unidades, tamaño no negativo y precisión |
| `effectScatter` | Puntos + efecto | Requisitos de scatter, movimiento reducido y coste de animación |
| `radar` | Indicadores + valores por entidad + límites declarados | Escalas/unidades comparables, faltantes y normalización explícita |
| `map` | Clave territorial + medidas + mapa registrado | Correspondencia de claves, recurso/versionado y regiones sin dato |
| `tree` | ID/padre o caminos de niveles | IDs únicos, raíces, ciclos, huérfanos y profundidad |
| `treemap` | Jerarquía + tamaño/color | Validaciones de árbol y política de valores internos/hojas |
| `sunburst` | Jerarquía + magnitud | Totales coherentes y profundidad legible, sin sumar padre e hijos dos veces |
| `graph` | Nodos + enlaces; posiciones/categorías opcionales | Extremos válidos, IDs, duplicados, nodos aislados y límites de layout |
| `chord` | Nodos + enlaces ponderados | Referencias, pesos, dirección y significado de flujos |
| `sankey` | Nodos + enlaces de flujo | Pesos admisibles, ciclos, dirección y balance cuando el dominio lo requiera |
| `gauge` | Valor + rango; objetivo/umbrales opcionales | Unidad y límites declarados; no inventar un máximo de negocio |
| `funnel` | Etapa + valor + orden | Semántica de etapas y orden declarado; no reordenar silenciosamente por magnitud |
| `parallel` | Dimensiones + valores por entidad | Tipos/ejes, escalas, faltantes y límites de dimensiones |
| `boxplot` | Grupo + cinco estadísticos, o observaciones con cálculo explícito | Orden de cuantiles, algoritmo, bigotes y outliers; no cambiar distribución |
| `candlestick` | Tiempo + apertura/cierre/mínimo/máximo | Roles OHLC, orden temporal, rangos y precisión; volumen es otra serie |
| `lines` | Rutas o segmentos de coordenadas | Secuencia, sistema de coordenadas y continuidad; cartografía si procede |
| `heatmap` | X/Y + intensidad, o fecha + intensidad | Celdas duplicadas, escala de color, faltantes y agregación declarada |
| `pictorialBar` | Categoría + medida + símbolo | Capacidad de símbolos/recursos, escala y unidades |
| `themeRiver` | Tiempo + serie + valor | Orden y series alineadas; tratamiento explícito de tiempos sin observaciones |
| `custom` | Forma definida por un renderer registrado | Roles y parámetros declarados por la extensión, recursos y versión compatible |

## Variantes y componentes, no nuevos IDs de familia

Área, donut, barras horizontales/apiladas, waterfall, bubble, mixtos, sparklines,
small multiples y bandas de confianza son variantes/composiciones. Beeswarm y
jitter amplían scatter. Histograma, regresión y correlación necesitan un cálculo
declarado; que haya una demo no demuestra que el motor de inferencia ya lo haga.

`calendar`, `matrix`, `polar`, `geo`, `grid`, `singleAxis`, `timeline`, `dataZoom`,
`visualMap`, `graphic` y texto enriquecido son coordenadas o componentes. La matriz
interna de ECharts no reemplaza el lienzo de doce columnas del dashboard.
Cada componente también necesita cobertura y límites de edición. El experto
permitirá varias series/coordenadas dentro de una visualización; no asumir
«una consulta = una serie = un gráfico».

Gantt, violin, intervalos, contornos y otras formas custom tendrán templates
registrados cuando sus adaptadores estén disponibles. ECharts 6 admite
`renderItem` por nombre mediante `registerCustomSeries`: ver
[documentación de custom](https://github.com/apache/echarts-doc/blob/master/en/option/series/custom.md?plain=1)
y [capacidades de ECharts 6](https://echarts.apache.org/handbook/en/basics/release-note/v6-feature/).
SQLviz aún no registra esos templates. Su contrato debe declarar roles, opciones,
versión, recursos y presupuesto; el documento del autor solo referencia el nombre.
No evaluar texto como función ni cargar npm/URLs arbitrarias desde un dashboard.

## GL y extensiones: capacidad separada

La galería incluye GL. Los
[exports de ECharts GL](https://github.com/ecomfe/echarts-gl/blob/master/src/export/charts.js)
declaran once familias; no forman parte del paquete ECharts instalado en SQLviz.

| Grupo de series GL | Datos y dependencias previstos |
| --- | --- |
| `bar3D`, `scatter3D`, `line3D` | XYZ y valores/series; ejes/coordenadas 3D y presupuesto GPU |
| `lines3D`, `linesGL` | Rutas y coordenadas; geo/globe cuando corresponda |
| `map3D`, `polygons3D` | Geometrías/regiones, alturas/valores y cartografía |
| `surface` | Malla ordenada XYZ; UV en variantes paramétricas; topología explícita |
| `scatterGL` | Puntos y canales visuales con datos acotados |
| `graphGL` | Nodos/enlaces, layout y límites de ejecución GPU |
| `flowGL` | Campo de vectores y coordenadas, muestreo y parámetros explícitos |

`globe`, `geo3D`, `grid3D` y proveedores de mapas son componentes/coordenadas,
con assets, recursos externos y requisitos propios. La
[release GL 2.1.0](https://github.com/ecomfe/echarts-gl/releases/tag/2.1.0)
declara correcciones para ECharts 6, pero existe un
[reporte de imports ESM con 6.1.0](https://github.com/ecomfe/echarts-gl/issues/574).
Antes de incorporar GL, verificar la versión efectiva con Vite, SSR/build,
editor/viewer, drivers, límites y liberación de contextos; la release no sustituye
esa prueba. No instalar GL ni degradar ECharts en esta revisión documental.

Word cloud, liquid fill y otros plugins externos requieren inventario propio de
licencia, mantenimiento, formatos, compatibilidad y recursos. Su presencia en
el ecosistema no los convierte en una familia core ni en soporte universal.

## Qué significa entregar una familia

El futuro registro de capacidades distingue `available`, `requires_binding`,
`requires_resource`, `requires_extension` y `unsupported`. Debe declarar versión
de motor, roles, adaptación, capacidades automáticas/builder/experto, mínimos de
contenido, límites y requisitos de interacción. Estos estados son propuesta,
no un nuevo contrato HTTP ya publicado.

Para declarar una familia entregada: datos válidos e inválidos en corpus;
propuesta y alternativas cuando corresponda; selección/asignación desde builder;
JSON nativo conservado; IDs estables; guardado/reapertura; refresh/filtros;
viewer y recursos resueltos; nulos/precisión sin cambios ocultos; rendimiento y
accesibilidad comprobados. Una familia puede ser representable en experto sin
ser todavía inferible automáticamente, y la matriz debe mostrarlo.

Orden previsto: primer flujo completo en S4; ampliación S5 por paquetes
cartesiano/composición, distribución/finanzas, jerarquías/redes, geografía,
indicadores/multidimensional/custom; después spike e integración GL/plugins
verificados. Cada paquete se subdivide antes de iniciar. La amplitud objetivo
no justifica entregar primero una larga lista de controles sin runtime fiable.
