# Integridad del borrado de dashboards

**Actualizado:** 2026-10-07. **Estado:** primera unidad de E1 implementada,
con ampliación para edición de paneles. Corrige BP-01; el resto de E1 continúa pendiente.

## Comportamiento

`DELETE /api/v1/dashboards/{id}` requiere autor y conserva la respuesta **204**
sin cuerpo. En una sola transacción elimina:

- El dashboard y todos sus paneles, incluyendo SQL, inferencias y overrides.
- Sus enlaces compartidos, de cualquier modo y también los ya revocados.
- Su memoria de filtros en `filter_memory`.

Las carpetas, conexiones, settings, credenciales y tablas de datos del proyecto
se conservan. Los enlaces de workspace pertenecen al workspace, no al dashboard:
siguen funcionando y su listado deja de incluir el dashboard eliminado.
El diálogo de confirmación enumera paneles, filtros guardados y enlaces afectados.
El frontend limpia el dashboard activo y su caché después de recibir éxito;
ante un error conserva la vista y muestra el mensaje del servidor.

Un ID inexistente, incluido un segundo borrado, devuelve **404** con código
`dashboard_not_found`. Una colisión de escritura o restricción de integridad
devuelve **409**, `dashboard_write_conflict`, después de rollback. El detalle
HTTP no incluye SQL interno, nombres de dependencias ni tokens. Un fallo SQL
inesperado antes del commit sigue siendo un **500** y revierte la transacción.
La limpieza posterior de sesiones no comparte esa transacción; la ausencia del
enlace confirmado es la comprobación definitiva de acceso.

## Responsabilidades

- [DashboardRepository](../../packages/sqlviz-storage/src/sqlviz_storage/dashboard_repository.py)
  contiene las escrituras y es dueño de begin/commit/rollback sobre un cursor
  independiente. Devuelve tokens para limpieza únicamente después del commit;
  su resultado oculta credenciales en `repr`. No importa API, sesiones ni inference.
- [DashboardDeletionService](../../packages/sqlviz-api/src/sqlviz_api/services/dashboards.py)
  coordina el repositorio y la revocación de sesiones de lector ligadas a esos
  tokens. No importa FastAPI. Una excepción del repositorio impide la revocación.
- [Dependencias](../../packages/sqlviz-api/src/sqlviz_api/dependencies.py) construyen
  el servicio para cada solicitud con su cursor y el almacén de sesiones de la
  aplicación. El router delega; la fábrica traduce errores a HTTP.

Se usa un repositorio concreto y una operación acotada. No se introduce un CRUD
genérico, un registro global de conexiones ni una jerarquía de interfaces sin
un segundo adaptador que la necesite.

## Creación simultánea y transacciones

**Ampliación del 2026-10-07:** el [PATCH básico de paneles](sqlviz-panel-patch.md)
incorpora UPDATE de timestamps de los paneles antes del borrado del conjunto.
Protege también frente a ediciones concurrentes, sin depender de que DELETE
por sí solo provoque conflicto. Esa escritura adicional pertenece a la misma
transacción y se revierte junto con todas las filas si falla. Paneles distintos
pueden editarse simultáneamente; borrar su dashboard compite con cualquiera de ellos.

Una transacción de borrado por sí sola no evita que otro request compruebe el
padre, espere y cree un panel huérfano. `dashboard_write` establece una escritura
real de `dashboards.updated_at` antes de crear paneles, crear enlaces de dashboard
o borrar el conjunto. La comprobación del padre y la escritura dependiente
ocurren dentro de la misma transacción. La fecha usa UTC con microsegundos;
si coincide con el valor anterior se incrementa un microsegundo para asegurar
que la escritura cambie el valor. Crear un elemento modifica la fecha de su
dashboard, coherente con tratarlo como un conjunto.

DuckDB usa control optimista: dos escrituras simultáneas sobre esa fila entran
en conflicto. La operación rechazada revierte todo; el usuario puede actualizar
y reintentar. No hay reintento automático ni un bloqueo global que serialice
dashboards distintos. Esta propiedad y la carrera entre SELECT del padre y
UPDATE se prueban con cursores independientes. Una actualización que conserva
el mismo valor no sirve de protección; esa alternativa se descartó al fallar
las pruebas. Ver [concurrencia de DuckDB](https://duckdb.org/docs/current/connect/concurrency).

La atomicidad depende de una transacción del mismo archivo, no de compensaciones
entre varias escrituras autocommit. Un lector dentro de una transacción conserva
su snapshot completo; uno nuevo observa el borrado confirmado. Ver
[transacciones de DuckDB](https://duckdb.org/docs/current/sql/statements/transactions).
Los endpoints de lectura que realizan varias consultas autocommit no adquieren
por este cambio un snapshot único para toda su respuesta.

No se modifica el esquema ni se añade `ON DELETE CASCADE`, que DuckDB no soporta.
La eliminación de dependencias es explícita y debe revisarse cuando se añadan
nuevas tablas propiedad del dashboard. Ver
[restricciones de CREATE TABLE](https://duckdb.org/docs/current/sql/statements/create_table).
`dashboard_write` es dueño de la transacción y no admite anidarse en otra.
Los próximos caminos de creación de elementos deben participar en este mismo
protocolo; SQL directo externo puede saltarlo y no queda cubierto.

## Acceso y datos históricos

Después del commit se retiran las sesiones de los enlaces eliminados. Las de
otros dashboards, las de workspace y las del autor se conservan. Cada futura
solicitud valida además que el enlace y el dashboard existan, por lo que una
sesión emitida por un unlock que ya estaba en curso tampoco permite volver a
leer el dashboard eliminado. No se puede retirar una respuesta ya entregada
ni cancelar todas las solicitudes que fueron autorizadas antes del commit.

El historial `feedback_events` y los patrones reutilizables de `brain.duckdb`
se conservan. Son datos históricos globales, no elementos del proyecto sujetos
a este borrado, y no comparten la transacción del archivo `.sqlviz`. Esto no es
una operación de eliminación total de datos personales ni un borrado físico
seguro de páginas, backups o WAL. Una política de retención/purga de aprendizaje
requiere su propio diseño y pruebas.

No se borran automáticamente huérfanos históricos al abrir proyectos. Una
reparación necesita diagnóstico y un procedimiento explícito, fuera de esta
unidad. Tampoco se completan aquí revisión condicional de ediciones, invariantes
de carpetas/layout, migraciones ni persistencia del contrato visual.

## Validación

**25 casos nuevos** entre
[repositorio](../../packages/sqlviz-storage/tests/test_dashboard_repository.py) y
[API](../../packages/sqlviz-api/tests/test_dashboard_deletion.py):

- Limpieza exacta del conjunto y conservación de otros dashboards, workspace,
  datos, configuración, autenticación e historial de aprendizaje.
- Rollback por fallo real en cada tabla de elementos y por restricción al
  eliminar el padre; fallo de commit inyectado sobre la base real.
- Reapertura de un archivo sintético después de éxito y después de rollback.
- Visibilidad de snapshots, conflictos en ambos órdenes de creación/borrado,
  carrera entre lectura y actualización del padre, reloj coincidente y progreso
  de operaciones sobre dashboards distintos.
- API 204/404/409, creación posterior rechazada, sesiones conservadas tras
  fallo y revocadas después de éxito; lectura/ejecución/dominios del panel
  eliminado devuelven 404. Workspace sigue consultando otro dashboard.

Las pruebas usan archivos temporales y un brain aislado. No abren ni modifican
proyectos personales. La validación local no sustituye la matriz remota de CI.

Validación del incremento completo:

- **1677 pruebas Python aprobadas, 3 omitidas**, en **133,69 s**. Comando:
  `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp build/dashboard-integrity-review/pytest-final-02`.
- Ruff sobre todos los paquetes y mypy global sobre **126 archivos** pasan.
- **74 pruebas frontend** pasan. `npm run check` da **0 errores y 0 advertencias**;
  `npm run build` genera el SPA. Check, tests y build se ejecutaron en secuencia.
  Persisten avisos anteriores de fixtures `derived_inert`, sourcemaps/PURE y
  tamaño de bundles; no se han silenciado ni se consideran resueltos aquí.
- Chromium con backend y build reales: rechazo HTTP 409 inyectado conserva
  dashboard/gráfico y muestra error; reintento con DELETE real devuelve 204,
  limpia la vista y bloquea los enlaces eliminados. El workspace protegido
  mantiene su sesión y permite consultar/navegar al dashboard restante.
  **Sin errores de página**. Reporte y screenshots en
  `build/dashboard-integrity-review/`, ignorados por git. El servidor de ensayo
  usa proyecto/brain en memoria y se detuvo al finalizar; la demo del usuario
  no se reinició.

No se creó una release ni se ejecutó CI remoto. El ajuste de la prueba de
autorización toma el snapshot después de crear el enlace como autor, para medir
exclusivamente los efectos de ejecutar como lector.

**Seguimiento:** BP-02 y PATCH de ubicación de BP-05 se implementan en la
[segunda unidad de E1](sqlviz-folder-integrity.md). Esta añade un contexto
compartido de transacciones, usado también por el borrado de dashboards, que
preserva el conflicto original cuando DuckDB ya abortó un COMMIT fallido real.
Siguiente: dimensiones válidas de layout (BP-03).
