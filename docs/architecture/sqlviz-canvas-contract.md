# Núcleo de geometría manual del dashboard

**Entregado:** S0, 2026-10-08. **Alcance:** módulo interno de dominio y pruebas.
No está conectado a HTTP, almacenamiento, composición actual ni UI. No habilita
drag/resize y no modifica el formato `.sqlviz` o los PATCH legacy.
El siguiente paso figura en el [plan operativo](sqlviz-studio-delivery-plan.md).

## Modelo y unidades

Implementación: `packages/sqlviz-core/src/sqlviz_core/models/dashboard_canvas.py`.
Usa dataclasses inmutables y biblioteca estándar, sin dependencias de inference,
DuckDB, FastAPI, ECharts o frontend.

| Tipo | Campos y responsabilidad |
| --- | --- |
| `DashboardCanvas` | `version=1`, `mode=scroll\|screen`, `gap_px`, `padding_px`, tupla de placements |
| `PanelPlacement` | `panel_id`, columna inicial `column`, `column_span`, `top_px`, `height_px` |
| `PanelMinimum` | Ancho y alto mínimos suministrados por un adaptador que mida contenido |
| `CanvasFit` | Alto requerido, problemas de espacio y recomendación de fallback |

Hay doce columnas, indexadas de 0 a 11 internamente. Coordenadas verticales,
separación y padding son píxeles CSS enteros. `top_px` comienza dentro del padding
superior. No mezclar alturas en filas abstractas y píxeles como dos autoridades.
El futuro inspector puede mostrar columnas 1–12 sin cambiar estas coordenadas.

La tupla conserva el orden del documento; mover no la reordena. El ID solo
identifica la referencia: S0 valida su unicidad local, pero no acredita que el
panel exista en almacenamiento ni lo hace estable al editar SQL. Esas garantías
pertenecen a reconciliación y casos de uso de S1.

## Invariantes y operaciones

`validate_canvas` rechaza documentos completos inválidos mediante
`CanvasValidationError`, con código estable y panel cuando procede:

- Versión conocida, modo admitido y tipos exactos para geometría; no convertir
  strings, floats o booleanos a enteros.
- ID no vacío, UTF-8 válido y máximo 256 bytes; sin duplicados.
- Ancho entre 1 y 12 columnas, origen no negativo y extremo dentro del grid.
- Altura estructural mínima 120 px. No imponer el techo legacy de 900 px.
- Sin solapamientos y con separación vertical requerida cuando los rangos de
  columnas se cruzan. Paneles contiguos horizontalmente pueden tener altos distintos.
- Presupuesto de 256 paneles y extensión de 1 000 000 px, incluidos padding y
  paneles. Son límites operativos, no tamaños visuales recomendados.

`move_panel` cambia posición; `resize_panel` cambia tamaño. Ambos validan base y
candidato, devuelven un documento nuevo y conservan identidad, orden y vecinos.
Un rechazo no modifica el original. No compactan, empujan, recortan ni ajustan
silenciosamente valores. Puede conservarse espacio en blanco intencional.

Un panel de seis columnas y 616 px de alto puede convivir con dos paneles de seis
columnas y 300 px apilados en las otras seis columnas: tops 0 y 316 px, gap 16 px.
La posición vertical es independiente por panel; no hay una fila automática cuya
altura obligue al segundo vecino a comenzar debajo del panel alto. Las dos
orientaciones están comprobadas en `screen` y `scroll` en el núcleo; su UI y
persistencia siguen pendientes en S1/S2.

La detección por pares tiene coste O(n²), acotado por el presupuesto del documento.
Una estructura espacial solo se justificará con mediciones y necesidades reales.

## Evaluación de espacio

`assess_canvas_fit` recibe ancho/alto del espacio real disponible, finitos y
positivos. Calcula el ancho físico de columnas descontando padding y once gaps;
evalúa cada mínimo suministrado con el ancho real del span y su altura exacta.
Referencias a paneles inexistentes o mínimos inválidos producen un error.

En `screen` compara el alto requerido con el disponible. En `scroll` permite
crecer verticalmente. Los problemas identifican espacio disponible/requerido y
panel cuando corresponde; no cambian el modo ni la geometría del autor.

| Resultado | Significado |
| --- | --- |
| Sin problemas | Cabe respecto a geometría y mínimos suministrados |
| Solo `canvas_height` | Sugiere `scroll` |
| `canvas_width`, `panel_width` o `panel_height` | Sugiere `reflow`; scroll vertical no arregla falta de ancho o altura interna del panel |

La sugerencia no aplica ningún fallback. Sin mínimos suministrados no garantiza
legibilidad. Tampoco llena el viewport, reparte filas, mide DOM, implementa
breakpoints o crea layouts móviles; esos adaptadores pertenecen al Studio.

## Compatibilidad y siguiente integración

El layout inferido y los overrides actuales siguen usando sus contratos. S0 no
crea una segunda vía activa de guardado. S1 deberá definir fuente única de
posición/tamaño, adapter legacy, revisión, permisos, migración y reconciliación
de referencias; todas las posiciones de un dashboard se confirman atómicamente.
La UI ofrecerá preview compatible, pero el servidor validará el conjunto.

El mínimo de 120 px se comparte con la regla estructural existente. Elevarlo para
un tipo de gráfico no debe cambiar silenciosamente proyectos: las mediciones y
perfiles de contenido explicarán sus requisitos en la siguiente integración.

## Evidencia local

`packages/sqlviz-core/tests/test_dashboard_canvas.py`: 54 casos cubren geometría,
tipos, IDs, colisiones y límites exactos; inmutabilidad y rechazo atómico; tamaños
superiores a 900 px; mínimos de contenido, pantalla/scroll y viewports inválidos,
incluidos enteros enormes que no deben producir overflow.

Cuatro casos de regresión adicionales comprueban el panel alto junto a dos
vecinos apilados, a izquierda/derecha y en ambos modos, con alineación de altura y
rechazo sin mutación si se invade el gap. Los conteos globales siguientes son la
evidencia original de S0, no un nuevo ensayo de toda la plataforma.

Validación enfocada de esa ampliación: 58 pruebas de geometría pasan y Ruff del
archivo de pruebas pasa. No cambia código de runtime ni acredita renderizado UI.

Suite core: 275 pruebas aprobadas. Ruff global y mypy en los cinco paquetes:
sin errores, 138 fuentes verificadas por mypy. No se ejecutó revisión visual
para este módulo sin UI; la evidencia del drag/resize se exigirá en S2.
El resultado local no sustituye CI ni acredita funcionalidades futuras.
