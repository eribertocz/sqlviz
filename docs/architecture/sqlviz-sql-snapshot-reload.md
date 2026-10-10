# Recarga de SQL y asociaciones confirmadas

**Implementado — 2026-10-09: S1.1c.2c.2.** El workspace carga el snapshot de
autor antes de adoptar definiciones o reutilizar resultados en memoria. Recupera
asociaciones explícitas comprobadas con parsing nativo, sin ejecutar consultas
al abrir o recargar el dashboard. No entrega todavía recuperación de respuestas
perdidas ni autoguardado con revisión; corresponden a 2c.3.

## Una lectura coherente

`GET /api/v1/dashboards/{id}/sql-script` incorpora `last_run_at`, `last_run_sql`
y `publication_status` al contrato v1. Borrador, paneles, publicación y última
ejecución salen de la misma transacción de lectura. El endpoint sigue siendo de
autor, con `Cache-Control: no-store`; no analiza SQL ni escribe metadata.

| Estado | Significado | Recuperación |
| --- | --- | --- |
| `confirmed` | La publicación explícita sigue siendo compatible con los paneles | Comprobar fuente, IDs y rangos con el parser nativo antes de adoptar |
| `absent` | No existe registro del script | Preservar el borrador; solo reconstruir el caso legacy sin borrador ni historial |
| `incompatible` | Existe registro, pero una operación legacy cambió los paneles o su SQL | Preservar el borrador, incluso vacío; no inventar asociaciones |

Metadata corrupta sigue fallando explícitamente; no se transforma en ausencia.
La referencia de definición conserva su significado y no incluye los campos de
última ejecución. No se añade una migración: todos los valores ya estaban guardados.

## Recuperación de identidad

[sqlSnapshot.ts](../../packages/sqlviz-web/src/lib/sql/sqlSnapshot.ts) valida
versión, propietario, revisión, estados, IDs únicos, límite de 256 paneles y
metadata. Para una publicación confirmada, solicita el parsing de su fuente
exacta y exige cobertura completa: índice, rangos UTF-16, ID y SQL actual del
panel deben coincidir. Dos consultas idénticas conservan sus IDs declarados;
no se emparejan por texto ni por posición en la lista de paneles.

Si `draft_source` coincide exactamente con `publication.source`, recupera sus
asociaciones. Si el autor tiene un borrador posterior, lo muestra tal cual,
incluso vacío o con sintaxis inválida, sin asignarle los IDs de la publicación.
La validación analiza la fuente confirmada, no obliga a que el borrador sea válido.

`last_run_sql` se conserva por separado. La acción existente de restaurar la
última ejecución recupera identidad solo cuando ese SQL coincide exactamente
con la publicación verificada. Una última ejecución más antigua puede restaurar
texto, pero necesita resolución explícita antes de Run. Guardar definiciones y
registrar éxito continúan siendo operaciones distintas.

Para proyectos legacy sin registro, borrador ni historial, el editor construye
la fuente directamente a partir de pares ID/SQL de los paneles. Esa construcción
aporta procedencia; una cadena guardada arbitraria no. Hay una ambigüedad legacy:
un vacío sin registro ni historial no permite distinguir un editor nunca
inicializado de uno vaciado intencionalmente. La procedencia durable de borrador
se aborda en 2c.3; no atribuir esa garantía a este incremento.

## Navegación y caché

[dashboardStore.svelte.ts](../../packages/sqlviz-web/src/lib/stores/dashboardStore.svelte.ts)
usa la misma adopción para bootstrap y cambios de dashboard. Desaparecen las
lecturas independientes de dashboard/paneles que podían mezclar estados. No
adopta un snapshot hasta terminar todas las comprobaciones. Un error conserva
la vista y el borrador anteriores, muestra el fallo y no vuelve al contrato legacy.

La generación de navegación descarta respuestas tardías; si el texto cambia
mientras carga, no se sobrescribe. Las actualizaciones diferidas de Monaco
comprueban generación, dashboard y fuente. Run permanece deshabilitado durante
la carga; crear un dashboard invalida una carga anterior pendiente.

La caché no suministra IDs ni borrador. Antes de recuperar gráficos exige fuente
exacta, misma referencia de definición, mismos IDs/SQL y cobertura única de todos
los paneles en resultados y layout. Las entradas incompatibles se descartan.
Los nombres y la última ejecución vienen siempre del snapshot actual.

Esto verifica compatibilidad de definición, no frescura de datos analíticos ni
todos los cambios de presentación. Las filas siguen siendo las de la ejecución
previa; no existe una revisión global de datos, un snapshot publicado del viewer
ni protección completa frente a ciclos de cambios legacy A→B→A. Una recarga de
página inicia la caché vacía y exige Run para obtener resultados.

## Límites y siguiente incremento

- Autoguardado mantiene su contrato anterior; no resuelve edición simultánea ni
  hace durable la procedencia de las ediciones Monaco.
- Un commit confirmado cuya respuesta se pierde no se adopta automáticamente.
  Este incremento recupera el estado al cargar; no añade un ledger idempotente.
- La igualdad de fuente con la publicación solo restaura asociaciones declaradas
  y verificadas. No transfiere identidad entre revisiones arbitrarias.
- El contrato nuevo requiere frontend/backend compatibles. Snapshot inválido,
  parser indisponible o respuesta de backend antiguo fallan explícitamente.
- Viewer compartido, filtros legacy, layout persistido y drag/resize conservan
  sus contratos actuales; no quedan completados por esta recarga.

**3a entregada:** [revisión durable y escritor interno](sqlviz-sql-draft-revisions.md).
Sigue **3b**, su API; 3c integra autoguardado y conflicto, 3d recupera respuestas
perdidas. La UI mantiene todavía su contrato legacy. Después continúa
S1.2, persistencia del lienzo. Ver el [plan operativo](sqlviz-studio-delivery-plan.md).

## Evidencia

Pruebas HTTP verifican lectura sin escrituras, estados de publicación y una
actualización concurrente de metadata durante la lectura. Las pruebas web cubren
Unicode/rangos, SQL duplicado, fuentes vacías/invalidas, bindings incompatibles,
cachés obsoletas, carga fallida, navegación tardía y recarga → Run con los mismos
IDs. El recorrido de Chromium usa una copia aislada del proyecto y una base de
aprendizaje en memoria; sus fixtures se eliminan por ID. Los artefactos de
verificación están en `build/sql-snapshot-review/`, ignorados por Git.

Validación: **2546 pruebas Python pasadas, 3 omitidas; 342 pruebas web pasadas**,
Ruff/mypy correctos, check Svelte sin errores/advertencias y build de producción
correcto. Chromium comprueba consultas idénticas con IDs invertidos, Unicode,
recarga sin escrituras/ejecución, edición Monaco y Run sin diálogo, restauración
desde borrador inválido, vacío preservado y resolución tras cambios legacy.
También pasa el recorrido previo de cinco commits, fallos/reintentos y eliminación
explícita en desktop/móvil. Sin errores JavaScript; persisten los avisos conocidos
de teardown Svelte en tests y tamaño de chunks en el build.
