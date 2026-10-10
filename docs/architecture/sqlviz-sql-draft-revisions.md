# Revisiones y escritura condicionada del borrador SQL

**Implementado — 2026-10-09: S1.1c.2c.3a.** Se entrega la revisión durable del
borrador y su escritor transaccional interno. La API específica y la integración
del autoguardado todavía están pendientes en 3b/3c. El PATCH actual continúa
guardando sin revisión esperada; este incremento no lo convierte en guardado
condicionado ni resuelve por sí solo la edición simultánea en la UI.

## Separar borrador de definición y presentación

El SQL editable conserva una única autoridad: `dashboards.sql_content`. La
migración aditiva `0023_dashboard_sql_draft_generation` incorpora un contador
BIGINT `sql_draft_generation`, con cero inicial y sin copiar consultas ni filas.
La apertura de un proyecto no cuenta como guardado.

[SqlDraftSnapshot](../../packages/sqlviz-storage/src/sqlviz_storage/sql_draft_revision.py)
contiene dashboard, fuente exacta y generación. Su propiedad `revision` produce
`sql-draft-v1:` más un hash SHA-256 de esos tres valores. Es una precondición de
estado, no una credencial ni una firma de resultados. El almacenamiento no
decide autorización: la aplicación deberá exigir acceso de autor en 3b.

| Operación confirmada | Generación del borrador | Definición del visual |
| --- | --- | --- |
| Guardado condicionado del borrador | Avanza, incluso con texto idéntico | No cambia |
| PATCH legacy que incluye `sql_content` | Avanza, incluso con texto idéntico | No cambia |
| Commit del script de Run | Avanza en la misma transacción | Confirma sus asociaciones y revisión |
| Nombre, descripción, clasificación, inferencia o última ejecución | No cambia | Conserva su contrato existente |
| Abrir/leer el proyecto | No cambia | No crea asociaciones |

Así, volver de A a B y después a A no reutiliza una revisión de borrador anterior
mediante los escritores admitidos. Un Run con el mismo SQL también invalida un
guardado capturado antes de ese commit. La revisión completa del script incluye
la generación; la referencia de definición continúa excluyendo borradores.

No se usa `updated_at` como revisión del borrador: lo modifican otras operaciones
del dashboard. La generación no representa tampoco frescura de datos, revisión
global de presentación ni publicación del viewer.

## Escritura atómica

[SqlDraftRepository](../../packages/sqlviz-storage/src/sqlviz_storage/sql_draft_repository.py)
ofrece `read(dashboard_id)` y `write(dashboard_id, expected_revision, source)`.
Ambas operaciones poseen su transacción; no deben llamarse dentro de otra.

1. Validar formato de revisión y texto/UTF-8, NUL y presupuesto de 1 MiB.
   No analizar SQL: un borrador vacío, incompleto o con sintaxis inválida es válido.
2. Usar el bloqueo transaccional existente `dashboard_write` sobre el padre.
3. Leer fuente/generación y exigir la revisión esperada exacta.
4. Avanzar la generación y actualizar solo el borrador; el timestamp pertenece
   al bloqueo del agregado. Comprobar también generación/fuente en el UPDATE.
5. Leer el resultado dentro de la misma transacción y devolverlo tras COMMIT.

Una actualización con WHERE/RETURNING por sí sola no cubrió todos los cruces de
escritura probados con DuckDB. El bloqueo compartido del padre evita sustituirlo
por una segunda política de concurrencia y protege frente a guardados, Run,
eliminación y cambios del mismo agregado. Durante la transacción, una modificación
de presentación puede producir conflicto por competir por la misma fila; esto
es distinto de invalidar permanentemente el token del borrador. Otros dashboards
continúan pudiendo escribirse independientemente.

Ante revisión obsoleta o competencia, `SqlDraftWriteConflict` conserva fuente,
generación y estado previo. Fallos de lectura o COMMIT revierten también el
timestamp. No cambia paneles, bindings, inferencias, overrides, última ejecución
ni aprendizaje; no ejecuta SQL del autor.

## Estado legacy e integridad

`initialized` es verdadero cuando hay una generación positiva o fuente existente
no vacía. Guardar explícitamente vacío por primera vez lo distingue de un editor
nunca guardado. Un vacío histórico de generación cero sigue siendo ambiguo:
la migración no inventa su intención ni asociaciones Monaco. La UI usará esta
distinción al integrar el nuevo transporte; la recarga actual conserva todavía
su política legacy de 2c.2.

El contador no se reinicia ante valores inválidos ni desborda al llegar a
`2**63 - 1`. Los escritores legacy y Run avanzan el mismo contador dentro de su
transacción. Metadata inválida devuelve un error HTTP seguro `500` con código
`sql_draft_metadata_invalid`; capacidad agotada devuelve `413` con código
`sql_draft_revision_limit`, sin guardado parcial ni SQL privado en el error.
Cambios de nombre sin SQL siguen permitidos si la capacidad se agotó.

La migración agrega la columna y exige NOT NULL. Se ensaya sobre una copia,
verificando datos, autenticación y overrides, reapertura e invariancia del
original. No modifica archivos reales del usuario. Si una migración falla,
el runner existente no la registra y reintenta al abrir; las operaciones que
requieren una columna ausente o metadata inválida fallan, sin asumir generación cero.

## Lo que sigue pendiente

- **3b:** contrato HTTP de borrador/revisión y errores, permisos y exposición de
  su estado en el snapshot. Transportar el token opaco y la marca de inicialización,
  sin convertir el BIGINT interno en un número JavaScript. El token nunca sustituye
  la sesión de autor.
- **3c:** cola de autoguardado con revisión confirmada, estado de conflicto y
  preservación del borrador; Run, navegación y cierre de pestaña coherentes.
  No resolver conflictos recuperando una revisión nueva y sobrescribiendo sin aviso.
- **3d:** recuperación explícita de respuesta perdida de guardado/commit,
  sin duplicar creaciones, con persistencia de operaciones cuando sea necesaria.

No hay todavía endpoint público del escritor, ledger idempotente, guardado
durable de procedencia Monaco ni UI de comparación de borradores. Un reintento
con la revisión anterior después de un guardado confirmado produce conflicto;
no se trata como éxito por igualdad de texto. Escrituras SQL directas que eviten
estos repositorios pueden eludir el contador; no se garantiza detectar ciclos
A→B→A de escritores externos o binarios anteriores a esta migración.

Ver el [plan operativo](sqlviz-studio-delivery-plan.md).

## Evidencia

Pruebas con cursores independientes cubren ganadores de borrador/PATCH/Run,
renombre y borrado antes de escribir; el bloqueo retenido hasta COMMIT; escritura
independiente en otro dashboard; tokens obsoletos/ajenos; A→B→A; texto idéntico;
Unicode, vacío/incompleto y límites; rollback tras lectura/COMMIT fallidos y
reapertura. La migración se prueba en copia, sin cambiar el archivo original.
Pruebas HTTP verifican escritores existentes y errores seguros de integridad.
Artefactos locales en `build/sql-draft-revision-review/`, ignorados por Git.

Validación final: **2583 pruebas Python pasadas, 3 omitidas**, Ruff correcto y
mypy sin errores en 154 archivos de fuente. Chromium verifica ambos recorridos
previos de Run y recarga, desktop/móvil, con los mismos IDs y cero errores
JavaScript. La preview se actualiza tras cierre ordenado y respaldo previo a
migrar; conserva los tres dashboards y su metadata original. No se cambia ni
recompila el frontend en este incremento, ni se usa el proyecto o aprendizaje
reales del usuario.
