# Matriz analítica: contrato, cálculo y experiencia

**Revisión:** 2026-10-08. **Estado:** diseño pendiente de implementación.
La matriz es un módulo central de SQLviz con entregas propias. Su primer flujo
entra en S4, antes de ampliar todas las familias de gráficos en S5. El siguiente
incremento de código sigue siendo S1.1b; las dependencias de identidad y datasets
se conservan en el [plan operativo](sqlviz-studio-delivery-plan.md).

## Estado observado y referencia de producto

`TableRenderer.svelte` muestra filas planas, deriva columnas de la primera fila,
formatea números y mantiene cabecera sticky. No pivota ni calcula jerarquías,
medidas, subtotales, expansión o virtualización. Una mejora cosmética de esa
tabla no entrega una matriz analítica.

El objetivo es cubrir tareas comparables a una matriz BI profesional. La
[referencia Power BI](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-matrix-visual)
incluye ejes jerárquicos, expansión, tamaños y totales; su
[configuración](https://learn.microsoft.com/en-us/power-bi/visuals/power-bi-visualization-matrix-visual-format-settings)
añade modos de presentación y formato. La paridad es un objetivo a demostrar
por capacidad y tareas observadas, no una función ya entregada ni equivalencia
con todo Power BI/DAX.

La coordenada `matrix` de ECharts organiza gráficos/componentes. **La matriz BI
es un visual de producto con renderer de grilla dedicado**, dentro del mismo
panel, dataset y flujo de autoría. No se implementa dibujando todas las celdas
en ECharts ni añadiendo `matrix` al enum legacy sin migración y runtime.

## Capacidad objetivo

| Área | Comportamiento previsto |
| --- | --- |
| Ejes | Varias dimensiones en filas y columnas; niveles ordenados, jerarquías y valores en filas o columnas |
| Medidas | Varias medidas, tipos/unidades/formatos propios y semántica de total explícita |
| Exploración | Expandir nodo, expandir nivel, colapsar, drill por contexto; filas y columnas independientes |
| Totales | Subtotales por nivel y totales generales; etiquetas/posición configurables; cálculo separado de visibilidad |
| Presentación | Compacta, niveles en columnas y tabular; cabeceras multinivel, freeze, ajuste por contenido/fijo/espacio y tamaños manuales |
| Formato | Precisión, monedas, porcentajes, negativos, nulos y reglas condicionales; barras, iconos y sparklines cuando corresponda |
| Navegación | Teclado, selección/copia de rangos y foco estable; menús de contexto bajo demanda, alternativa táctil |
| Escala | Virtualización de ambos ejes y carga acotada; expandir no descarga todo el árbol ni genera el producto cartesiano completo |
| Interacción | Selección con contexto de ejes/medida; filtros y drill autorizados; limpiar sin perder formato |
| Publicación | Definición y defaults versionados; editor/viewer coherentes, exportación autorizada y estado de lectura separado |

Los consejos de legibilidad no alteran datos. Mostrar unidades, nivel, contexto y
completitud; evitar cifras ambiguas, headers truncados sin acceso al texto completo
y colores como única señal. No confundir «ocultar total» con «dejar de calcularlo».

## Modelo y límites entre capas

Separar cinco responsabilidades internas, con contratos tipados/versionados:

1. **Definición:** dataset/revisión, dimensiones de filas/columnas, medidas por ID,
   políticas de totales, orden, formato, interacción y defaults publicados.
2. **Plan analítico:** agrupaciones necesarias, contexto de filtros y caminos,
   expresiones de medida y presupuestos. Solo referencias autorizadas.
3. **Resultado:** jerarquías de ejes, celdas dispersas, medidas/totales, tipos,
   completitud, snapshot/revisión y cursores ligados al contexto.
4. **Estado de lectura:** expansión, selección, scroll y tamaños privados del
   viewer. No modifica la definición publicada ni la SQL del autor.
5. **Renderer:** ventana visible, cabeceras, accesibilidad, formato y gestos;
   no decide cómo agregar una medida ni qué filas está autorizado a consultar.

Los nombres son diseño interno; no un nuevo contrato HTTP ya publicado. El
discriminador de renderer diferencia gráfico ECharts, matriz/grilla y KPI.
Compartir identidad, revisiones, permisos, publicación y borradores sin forzar
las opciones de una matriz a tener forma de `EChartsOption`.

Core define invariantes de ejes, medidas, caminos y operaciones puras. Inference
propone roles con evidencia. Aplicación/API coordina consultas y confirma el
contexto; el adaptador DuckDB compila el plan. Storage conserva definición y
revisiones. Web mantiene interacción y rendering. No crear otro servicio de
autorización ni un monolito de lógica de cálculo dentro de Svelte.

Las claves de nodo/celda usan campo, nivel, valor tipado, camino y medida; no
índice visual ni texto formateado. NULL, el string "NULL" y una etiqueta "Total"
son valores distintos. Reordenar, filtrar o ampliar un eje conserva asociación
de anchos, formato, selección y medidas por identidad; referencias obsoletas
se diagnostican. El cursor se invalida al cambiar revisión/filtros/orden.

La elección de biblioteca de grilla se resuelve con un spike antes de M4: ejes
multinivel, freeze, virtualización bidimensional, acceso asíncrono, foco/lectores,
Svelte/SSR/build, export y licencia compatible con la distribución del producto.
Comparar reutilización con implementación propia por coste medido; no adoptar
una dependencia solo por una demo de pivot. El contrato analítico debe poder
cambiar de renderer sin trasladar a la biblioteca las reglas de medidas/permisos.

## Motor de medidas mínimo: necesario antes de la matriz

SQL sigue definiendo la relación de datos. El builder asigna campos a Filas,
Columnas y Valores y declara la operación; no exige SQL PIVOT manual ni DAX.
La consulta original y su granularidad son la autoridad: no volver a tablas
previas al dataset ni reescribir su negocio para conseguir un total.

| Clase | Regla de cálculo |
| --- | --- |
| Aditiva | SUM válida sobre el grano declarado; no sumar cantidades duplicadas por joins |
| Promedio | Calcular sobre el contexto de fuente o combinar suma/conteo válidos; no promediar promedios sin ponderación |
| Distintos | Evaluar DISTINCT en cada contexto; los conteos de grupos no son sumables |
| Ratio/derivada | Reevaluar numerador/denominador en el contexto del total; política explícita ante denominador cero |
| Semiaditiva | Balance/inventario puede agregarse por entidad pero requerir último estado por tiempo; regla temporal declarada y probada |
| No resoluble | Si el dataset solo trae ratios o estadísticos insuficientes, rechazar ese rollup o pedir sus componentes; no inventar un total |

Ejemplo: A tiene ingresos 100 y coste 50, margen 50%; B tiene ingresos 900 y
coste 810, margen 10%. El margen total es **14%**: `(1000 - 860) / 1000`.
No es 60% al sumar filas ni 30% al promediar porcentajes. Esta comprobación entra
en el corpus inicial, aunque el primer incremento soporte un subconjunto.

El total predeterminado evalúa la medida en su contexto completo y autorizado.
Un «total de elementos mostrados» es otra política, explícita en definición y UI.
Top-N, paginación, colapso o virtualización no cambian silenciosamente el total.
Las expresiones avanzadas utilizan SQL agregado validado y referencias a campos/
medidas; ciclos, funciones no soportadas y agregaciones incompatibles se rechazan.
No introducir un lenguaje público de cálculo propio para este primer alcance.

DuckDB puede ejecutar las agrupaciones necesarias con
[GROUPING SETS y GROUPING_ID](https://duckdb.org/docs/current/sql/query_syntax/grouping_sets).
El adaptador solicita solo los niveles requeridos, con parámetros y campos
resueltos; no genera siempre todas las combinaciones CUBE. La metadata de
agrupación distingue los NULL reales de los subtotales. El resultado conserva
DECIMAL y otros tipos hasta un formato comprobado, sin convertir ausencia a cero.

Esta semántica local mínima entra en S3/S4. Gobernanza de métricas entre equipos,
relaciones de modelos, lenguaje equivalente a DAX y motor multidimensional general
siguen siendo capacidades posteriores; no son requisitos para la primera matriz.

## Ejecución, escala y seguridad

La matriz no se calcula únicamente sobre las filas truncadas de la respuesta
actual del gráfico. Se necesita una lectura de la relación autorizada completa,
con presupuestos, y un resultado acotado por ventana. Un resultado incompleto no
presenta totales como completos. El acceso pasa por el aislamiento analítico
vigente; el frontend no puede enviar nombres de tabla/SQL arbitrarios como drill.

Filas/columnas expandidas, totales y ventanas comparten generación, filtros y
revisión de datos. Si la fuente admite snapshot consistente, mantenerlo; si no,
registrar frescura y no mezclar generaciones. Confirmar resultados conjuntamente,
conservar el último conjunto ante fallo y descartar respuestas tardías. La futura
cancelación debe detener trabajo del motor, no solo ignorar la respuesta HTTP.

Acotar profundidad, fan-out, miembros de cada eje, celdas, bytes, tiempo, memoria
y concurrencia. Carga progresiva de nodos y ventanas, caché ligada a autorización
y revisión, invalidación ante revocación. Un producto filas × columnas grande
exige limitar/filtrar/paginar, incluso con virtualización DOM. No revelar miembros,
totales, tooltips, exportaciones o dominios excluidos por permisos.

Distinguir dato nulo, combinación sin observación y celda pendiente de carga;
no inventar miembros ni colapsarlos bajo la misma etiqueta. Las reglas de formato
declaran si su dominio es el contexto completo o la ventana, para que el color
no cambie accidentalmente al hacer scroll.

En modo dashboard `screen`, la matriz ocupa la altura disponible y conserva sus
cabeceras; puede tener scroll interno sin scroll de página. Si el autor necesita
evitar también scroll interno, ofrecer paginación o menor detalle con preview.
No esconder filas mediante overflow para simular una matriz que cabe entera.

## UX de autoría y gestos

Al seleccionar la matriz aparecen Filas, Columnas y Valores. Campos con búsqueda,
tipo y rol visible; chips compactos muestran jerarquía y operación. Arrastrar un
campo ofrece destino, posición y preview; un destino incompatible explica por
qué. Un menú «Añadir a…» y botones para reordenar hacen la misma operación sin
arrastre. La consulta se confirma tras validar el cambio, no por cada movimiento.

Separar los gestos para que no compitan:

| Gesto | Zona y efecto | Entrega |
| --- | --- | --- |
| Mover/redimensionar panel del dashboard | Cabecera/tiradores del panel; grid de doce columnas, preview y geometría | S2 |
| Arrastrar campos a roles o reordenar niveles | Catálogo/chips del builder; cambia definición analítica, con undo | M5 / S4 |
| Ajustar columnas o reordenar medidas | Cabeceras de la matriz; cambia presentación o posición de medida por ID, sin cambiar jerarquía por accidente | M5–M6 |
| Reubicar paneles de herramientas del editor | Docks y zonas explícitas, fuera del lienzo BI; preferencias privadas y restauración | Evolución de workspace posterior al primer flujo S4 |

Docking no es prerrequisito de matriz ni debe mover el editor SQL al arrastrar
una columna. El redimensionado existente del editor conserva sus garantías; si
se amplía a docks, medir mínimos y mantener siempre accesibles los tiradores.

Un gesto crea una sola operación reversible, con Escape/cancelación, validación
al confirmar y borrador recuperable ante fallo. Mover un panel o ajustar ancho no
recalcula medidas; solicitar otra ventana de un resultado es distinto de volver
a ejecutar todo el análisis. No guardar en cada pointermove. El viewer puede
expandir, seleccionar y ajustar tamaños privados sin obtener permisos de autoría.

La grilla requiere navegación/foco, selección y lectura coherentes con
[treegrid](https://www.w3.org/WAI/ARIA/apg/patterns/treegrid/), además de alternativas
de puntero al arrastre según
[WCAG 2.2](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html).
Virtualizar exige conservar índices lógicos, relaciones de cabecera y foco al
entrar/salir de la ventana. Probar teclado, touch, zoom y lectores de pantalla;
añadir atributos ARIA no demuestra por sí solo accesibilidad.

## Los tres niveles también cubren la matriz

**Básico:** proponer ejes, medidas y una presentación cuando exista evidencia;
no asumir que todo número es sumable. El autor confirma operaciones ambiguas.
**Intermedio:** builder de roles, jerarquías, totales, formatos y reglas.
**Experto:** SQL de medidas y configuración JSON tipada de la grilla. ECharts
native options se conserva para gráficos ECharts; no sustituye el contrato de
matriz ni introduce otro nivel. Preview, precedencia, guardado/reset y viewer
son comunes. La matriz no interpreta callbacks JavaScript de ECharts.

## Entregas del módulo

Todas están pendientes. Cada parte se subdivide antes de implementarla.

| Parte | Etapa | Cierre previsto |
| --- | --- | --- |
| M1.1–M1.3 | S3 | Contrato de ejes/medidas y grano; claves tipadas/roles de celda; corpus y operaciones puras |
| M2.1–M2.3 | S4 | Agregaciones seguras; ratios/promedios/distintos por contexto cuando soportados; planes de agrupación y rechazos explícitos |
| M3.1–M3.3 | S4 | Persistencia/revisiones y migración; API de lectura acotada/permisos; filtros, snapshots y errores coherentes |
| M4.1–M4.3 | S4 | Grilla con ejes multinivel; expansión/colapso; medidas/subtotales/totales y teclado básico |
| M5.1–M5.3 | S4 | Builder de roles con drag y alternativa por clic; reordenar/tamaños y undo; guardar → reabrir → viewer + opciones expertas |
| M6.1–M6.3 | S5 | Formatos/unidades/layouts, reglas condicionales y semántica avanzada por medidas, sin pérdida de precisión |
| M7.1–M7.3 | S5 | Virtualización de ambos ejes, carga progresiva/caché y benchmarks con hardware, tamaño y límites declarados |
| M8.1–M8.3 | S7 | Selección/crossfilter/drill, rangos/copia y estados privados; cambios de contexto y permisos sin fugas |
| M9.1–M9.3 | S8 | Revisión publicada/defaults; export visible/completa autorizada y acotada; validación de tareas de referencia, accesibilidad y rendimiento |

El primer flujo M1–M5 no se cierra con una demo local ni una lista de controles.
Debe producir valores comprobados y la misma configuración en editor/viewer.
M7 escala a volúmenes mayores; M4 ya debe tener límites, estados y comportamiento
usable en su volumen declarado. La dependencia de S7 no pospone permisos ni los
filtros existentes; añade interacción avanzada sobre la matriz.

El corpus incluye promedio ponderado, distintos solapados, ratio 14%, inventario
semiaditivo, NULL real frente a subtotal, etiquetas idénticas/IDs distintos,
ordenación estable, granularidad perdida, top-N, ventanas/expansiones tardías,
cambios de esquema, decimales y permisos. Comparar con consultas de referencia
independientes; nunca certificar totales a partir de los mismos reducers del UI.

**Validación de esta revisión de arquitectura:** ejemplos SQL ejecutados en un
catálogo DuckDB aislado en RAM verificaron margen total 14%, un cliente distinto
presente en dos grupos contado una vez en el total, y separación entre miembro
NULL, subtotal y miembro con etiqueta "Total" mediante metadata de agrupación.
Es evidencia de las reglas propuestas, no de un motor de matriz implementado.
