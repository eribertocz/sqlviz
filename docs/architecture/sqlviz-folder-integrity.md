# Jerarquía de carpetas y ubicación de dashboards

**Actualizado:** 2026-10-06. **Estado:** segunda unidad de E1 implementada en el
árbol de trabajo. Corrige BP-02 y BP-05 para `parent_id` de carpetas y `folder_id`
de dashboards. Otros campos PATCH y el resto de E1 siguen pendientes.

## Comportamiento del contrato

Crear o mover una carpeta requiere un padre existente. No puede ser su propio
padre ni quedar bajo uno de sus descendientes. Crear o ubicar un dashboard
también requiere una carpeta de destino existente y una cadena de ancestros
válida. Un destino inexistente devuelve **422**, `folder_parent_not_found`;
un ciclo propuesto devuelve **422**, `folder_cycle`. El recurso que se pretende
editar/borrar y no existe devuelve **404**, `folder_not_found`.

En PATCH, la presencia del campo determina la operación:

| Campo enviado | `parent_id` de carpeta / `folder_id` de dashboard |
| --- | --- |
| Omitido | Conservar la ubicación actual |
| ID existente | Mover al destino, previa validación |
| `null` | Quitar el padre/grupo y mover a raíz |
| `""` | Alias de raíz para compatibilidad con clientes anteriores |

El frontend envía `null` al mover un dashboard a raíz desde el menú o arrastrar.
Los cuerpos de carpetas rechazan campos desconocidos y coerciones; `name` y
`sort_order` no admiten `null` explícito, porque no se pueden quitar. Nombres
vacíos o con solo espacios y órdenes fuera de un entero de 32 bits devuelven
422 antes de escribir. El texto válido del nombre conserva sus espacios.
Un PATCH `{}` de carpeta devuelve su estado sin cambiar la revisión interna.

Borrar una carpeta mantiene la política anterior: mueve sus dashboards y
subcarpetas **directos** a raíz, conserva sus descendientes bajo las subcarpetas
y elimina solo la carpeta seleccionada. SQL, paneles, overrides, filtros,
enlaces y sesiones de lector de esos dashboards se conservan. Las promociones
y la eliminación son una transacción; un fallo no deja contenidos a medio mover.

## Límites entre módulos

- [Core](../../packages/sqlviz-core/src/sqlviz_core/models/folders.py) define
  `Folder`, cambios parciales tipados y reglas puras de valores/ancestros.
  No importa DuckDB, Pydantic ni FastAPI. La validación recorre ancestros de
  forma iterativa, sin depender del límite de recursión de Python.
- [FolderRepository](../../packages/sqlviz-storage/src/sqlviz_storage/folder_repository.py)
  obtiene el snapshot del árbol y valida/escribe dentro de una transacción.
  Su contexto de ubicación permite que la escritura del dashboard pertenezca
  a esa misma transacción. No importa HTTP ni inference.
- Los [modelos HTTP](../../packages/sqlviz-api/src/sqlviz_api/models.py) distinguen
  campos omitidos de enviados; el [router](../../packages/sqlviz-api/src/sqlviz_api/routers/folders.py)
  traduce el cuerpo a cambios de dominio y delega en el repositorio inyectado.
  La fábrica mapea errores de dominio y concurrencia a 404/422/409.

No se añade un servicio que solo repita métodos del repositorio ni un repositorio
CRUD genérico. La política se prueba sin base de datos; atomicidad y concurrencia
se prueban con DuckDB real; la traducción del contrato se prueba mediante HTTP.

## Protección ante cambios simultáneos

Validar un movimiento y luego modificar solo esa carpeta permite write skew:
dos autores pueden mover A bajo B y B bajo A desde snapshots distintos. Cada
movimiento aislado sería válido, pero el conjunto formaría un ciclo. Tocar solo
la fila de cada carpeta tampoco protege ese caso.

`folder_tree_write` cambia una revisión compartida del árbol en
`_sqlviz_meta`, clave `folder_tree_revision`, **antes** de leer padres. Participan
todos los writes de carpetas y la creación/cambio de ubicación de dashboards.
La revisión incrementa un contador y garantiza una escritura real. Las
transacciones superpuestas compiten por esa fila; una falla con **409**,
`folder_write_conflict`, revierte sus cambios y permite actualizar/reintentar.
No se reintenta automáticamente una intención basada en un árbol anterior.
Este diseño aplica el control optimista de
[DuckDB](https://duckdb.org/docs/current/connect/concurrency).

Es una decisión conservadora para mutaciones administrativas de un workspace:
incluso cambios en ramas distintas pueden entrar en conflicto. Las lecturas,
consultas analíticas y edición de dashboards sin cambios de carpeta no adquieren
esta revisión. No es una prueba de rendimiento ni una solución de colaboración
distribuida. Si el uso exige alta concurrencia de edición del árbol, habrá que
medir y revisar este límite.

La clave se crea de forma perezosa en la primera escritura válida, dentro de
su transacción. No se añade una tabla/columna ni cambia `SCHEMA_VERSION`. En un
proyecto antiguo, dos primeros escritores pueden competir al confirmar la
inserción de esa clave; solo uno confirma, y el otro revierte también su cambio
de árbol. Esta carrera tiene una prueba con COMMIT fallido real.

El [contexto compartido de transacciones](../../packages/sqlviz-storage/src/sqlviz_storage/transactions.py)
se usa también en el borrado de dashboard. Preserva el error original si un
COMMIT fallido ya abortó la transacción y un ROLLBACK adicional indica que no hay
transacción activa. Otros fallos de rollback son explícitos; no se reportan
como conflictos revertidos con éxito. Ver la
[semántica de transacciones](https://duckdb.org/docs/current/sql/statements/transactions).
Cada operación es dueña de su transacción en un cursor independiente; no admite
anidamiento. No se introduce un lock global de Python ni estado del árbol en
memoria compartida entre aplicaciones.

## Proyectos anteriores y alcance

Una cadena de destino con un ciclo previo o un ancestro ausente devuelve **409**,
`folder_hierarchy_invalid`, en lugar de recorrer indefinidamente o aceptar
nuevas dependencias. Una revisión interna malformada también falla explícitamente.
No se resetea automáticamente ni se altera su valor ante un rechazo.

La validación comprueba la cadena del destino propuesto, no repara todas las
ramas históricas. El autor puede romper un ciclo existente quitando explícitamente
el padre de una carpeta. Mover a raíz no requiere cargar el mapa de ancestros.
El procedimiento general de diagnóstico/reparación de archivos anteriores y
las migraciones siguen fuera de esta unidad. Los writes SQL directos que eludan
el repositorio tampoco quedan protegidos por este protocolo.

La API admite jerarquía; **el explorador actual sigue mostrando grupos planos**.
No se incorpora en esta unidad un editor visual de carpetas anidadas ni una nueva
política de permisos por carpeta. No se amplía la semántica de `null` para
`connection_id`, descripciones y otros campos de dashboard; esa parte de BP-05
necesita una revisión específica.

## Validación

Las pruebas de
[política](../../packages/sqlviz-core/tests/test_folder_policy.py),
[repositorio](../../packages/sqlviz-storage/tests/test_folder_repository.py),
[transacciones](../../packages/sqlviz-storage/tests/test_project_transactions.py) y
[API](../../packages/sqlviz-api/tests/test_folder_integrity.py) cubren:

- Omisión, asignación, `null` y compatibilidad de raíz; valores inválidos sin
  escrituras parciales ni cambios de revisión.
- Ciclos propios, descendientes, ciclos históricos y ancestros ausentes;
  cadena de 5000 nodos sin recursión.
- Conflictos entre movimientos opuestos, creación de hijos/asignación de
  dashboards y borrado en ambos órdenes; primer COMMIT concurrente en un archivo
  antiguo sin revisión. El reintento valida el nuevo estado.
- Rollback entre promociones/eliminación, restricción real de base de datos,
  fallo de commit, interrupción y fallo explícito de rollback.
- Reapertura de archivos sintéticos después de éxito/fallo; dashboards, paneles,
  subárboles y accesos de lector conservados tras borrar solo una carpeta.

Validación del incremento:

- **93 casos nuevos** y suite Python completa: **1770 aprobadas, 3 omitidas**, en
  **136,39 s**. Comando:
  `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp build/folder-integrity-review/pytest-full-03`.
  Los 93 casos nuevos también pasan en la revisión final específica:
  `build/folder-integrity-review/pytest-final-focused-04` (**10,12 s**).
- Ruff global y mypy global sobre **129 archivos** pasan. `npm run check`:
  **0 errores y 0 advertencias**. **74 pruebas frontend** y build pasan;
  check, tests y build se ejecutaron secuencialmente. Persisten los avisos
  anteriores de fixtures `derived_inert`, sourcemaps/PURE y tamaño de bundles.
- Chromium, backend real y SPA nuevo: mover a Ungrouped envía `folder_id: null`
  y conserva el gráfico; mover de vuelta y borrar el grupo promueve los contenidos
  directos, conserva el subárbol y mantiene válido el acceso de viewer con
  contraseña. **Sin errores de página**. Reporte y screenshot en
  `build/folder-integrity-review/`, ignorados por git.

Los ensayos usan proyectos temporales/brain aislado; no abren proyectos del
usuario. El servidor de revisión se detuvo; la demo abierta del usuario no se
reinició. La validación local no equivale a ejecutar CI remoto ni crear una release.

**Siguiente parte de E1:** rangos válidos de ancho/alto y overrides de layout
(BP-03), antes de la composición tipada y del contrato visual del Studio.

**Seguimiento:** esa tercera unidad ya se implementó; ver
[dimensiones de paneles](sqlviz-panel-dimensions.md). El siguiente foco actual
es composición tipada y PATCH de campos restantes.
