# Dimensiones de paneles y persistencia de overrides

**Estado:** tercera unidad de E1 implementada localmente, 2026-10-06.
Corrige BP-03 de la evaluación de arquitectura. No entrega todavía un lienzo
libre, páginas ajustadas a pantalla ni la composición tipada de BP-04.

## Contrato

El ancho manual admite **1–12 columnas** y el alto manual **120–900 px**, ambos
enteros. Son los rangos que ya ofrecía el inspector. Los mínimos y máximos de
la inferencia describen recomendaciones de legibilidad; no sustituyen este
contrato manual. Cambiar estos rangos exige revisar el renderer y el inspector.

`PATCH /api/v1/panels/{id}/override` exige `field_name` y `user_value`:

```json
{"field_name": "col_span", "user_value": "6"}
```

El transporte conserva strings numéricos por compatibilidad. Se aceptan solo
dígitos ASCII, sin signos, espacios, decimales ni notación exponencial. Números
JSON, booleanos, listas, objetos y campos desconocidos se rechazan con **422**.
Omitir `user_value` también es un error; **null explícito** restablece automático.
La validación ocurre antes de escrituras y de abrir el aprendizaje.

Cada PATCH cambia un solo campo de forma atómica y conserva los demás.
`inferred_*` contiene la última inferencia exitosa; el cambio manual modifica
solo `selected_*` y `*_user_override`. Restablecer copia la última inferencia a
la selección y elimina el override. Una ejecución posterior puede actualizar
esa inferencia. Antes de ejecutar, la selección automática puede ser null.
Restablecer dimensiones desde el inspector envía dos PATCH secuenciales;
no se promete atomicidad conjunta de ancho y alto.

## Responsabilidades y errores

- **Core:** política pura, sin DuckDB, Pydantic ni dependencias de UI.
- **HTTP:** modelo estricto, autenticación de autor y traducción a 422/404/409.
- **Storage:** vuelve a validar para que los consumidores directos tampoco
  escriban tamaños inválidos. Desde el incremento de
  [tipo de gráfico](sqlviz-chart-overrides.md), el escritor compartido del panel
  confirma el campo y su copia de respuesta en una transacción, con protección
  frente a borrado del panel/padre; después intenta el aprendizaje opcional.
- **Editor:** espera la confirmación antes de modificar el gráfico, conserva
  datos/tamaño ante rechazo y serializa los cambios de dimensiones. Los
  controles quedan deshabilitados mientras se guarda. La recomposición vuelve
  a distribuir los paneles según el ancho confirmado.

Un conflicto real de escritura devuelve **409**, sin aprendizaje ni cambios
del PATCH rechazado. No se reintenta automáticamente. El editor usa la selección
confirmada por el servidor, también al restablecer, y evita que una respuesta
de tamaños sobrescriba otra página a la que el usuario acaba de navegar.
Si el tamaño se guarda y falla la recomposición, conserva el valor confirmado
e informa que hay que volver a ejecutar el dashboard.

La caché de resultados escribe sin suscribirse a su propio estado. Una prueba
reactiva reproduce el bucle anterior y verifica que actualizar una vista
produce una sola escritura por cambio.

## Aprendizaje secundario

El proyecto es la fuente de verdad del diseño. Después de guardar se intenta
registrar la preferencia y su evento en brain, usando un cursor propio y una
transacción. Si falla el evento, también se revierte el patrón de esa operación.
Aprender el alto conserva el ancho aprendido y viceversa.

Si brain no está disponible o hay un conflicto allí, el guardado del proyecto
sigue siendo exitoso; se registra una advertencia sin SQL, datos ni rutas de
la excepción. No se expone un estado de aprendizaje en la respuesta actual ni
hay reintentos persistentes. No existe transacción entre ambos archivos.
Una futura garantía de entrega necesitaría una outbox y reintentos idempotentes.
El singleton global de brain y su dependencia de contratos de inference siguen
pendientes de la unidad de límites de módulos; este cambio no los resuelve.

Restablecer no requiere abrir brain ni elimina preferencias históricas.
Estas son sugerencias del motor, no un override activo del panel.

## Archivos anteriores y alcance pendiente

No se cambia el esquema ni se repara automáticamente un proyecto antiguo.
Los overrides históricos fuera de rango se ignoran al producir tamaños para
el renderer; tampoco fijan el ancho de la composición KPI. Se mantienen en el
archivo hasta que el autor los sustituye o restablece. Esto no valida todo el
contenido de `inference_result` enviado a `/compose`: BP-04 es la siguiente unidad.

No se añade CAS/revisión de panel para sincronizar ediciones entre pestañas,
reordenamiento SQL, filtros y todas las operaciones del editor. Tampoco se
define aquí la compatibilidad entre tipos de gráfico y columnas disponibles.
Son contratos distintos que requieren pruebas y decisiones propias.

## Verificación

Las nuevas pruebas de [storage](../../packages/sqlviz-storage/tests/test_size_override_integrity.py)
y [API](../../packages/sqlviz-api/tests/test_panel_dimensions_api.py) ejercitan
rechazos sin efectos, extremos de ambos rangos, execute/compose, conflictos
nativos, fallos de aprendizaje, rollback del patrón/evento, reapertura y reset.
Las pruebas del [editor](../../packages/sqlviz-web/src/lib/stores/dashboardDimensions.svelte.test.ts)
y [caché](../../packages/sqlviz-web/src/lib/stores/dashboardCache.svelte.test.ts)
cubren rechazo, confirmación, cola, navegación y fallo de recomposición.
Las pruebas de [controles](../../packages/sqlviz-web/src/lib/components/PanelPropertiesPanel.test.ts)
verifican deshabilitación durante el guardado y restauración del valor visible
tras un rechazo, tanto en el slider como en el campo numérico.

Validación local: **49 casos nuevos Python** y **9 frontend**. Suite completa:
**1819 aprobadas y 3 omitidas**, en **155,25 s**, con
`.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp build/size-integrity-review/pytest-full-03`.
Ruff global y mypy global (**130 archivos**) pasan. `npm run check` tiene
**0 errores/advertencias**; suite frontend **83 aprobadas** y build pasa.
Persisten los avisos previos de fixtures `derived_inert`, sourcemaps/PURE y
tamaño de bundles. La validación local no equivale a CI remoto ni a una release.

Chromium con backend real y build final: se fuerza un 409 para el alto y se
comprueba que campo/gráfico conservan el valor confirmado; se guardan 6 columnas
y 480 px, se verifican en un viewer compartido y tras recargar, y se restablecen
ambas dimensiones. **Sin errores de página**. Reporte y screenshot en
`build/size-integrity-review/`, ignorados por git.
Los proyectos y brain del ensayo son aislados; el servidor de revisión se
detuvo y la demo del usuario no se reinició ni se abrieron sus archivos.
