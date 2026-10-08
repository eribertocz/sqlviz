# PATCH de campos básicos del panel

**Estado:** implementado localmente el 2026-10-07, como tercer incremento de la
unidad 8 de E1. Continúa el [PATCH de dashboards](sqlviz-dashboard-patch.md).
Los contratos de presentación y la revisión de overrides siguen pendientes;
este incremento no cierra E1 ni implementa el Studio.

## Contrato del autor

`PATCH /api/v1/panels/{panel_id}` recibe un objeto con los campos a modificar.
La autorización de autor y el alcance de las lecturas de viewers se conservan.

| Campo | Valor admitido | `null` explícito |
| --- | --- | --- |
| `name` | String con texto, hasta 256 caracteres; conserva espacios originales | Rechazado |
| `sql_content` | Texto exacto, hasta 1 MiB en UTF-8; borrador vacío `""` válido | Rechazado |
| `sort_order` | Entero estricto entre −2³¹ y 2³¹−1; cero válido | Rechazado |

Omitir un campo conserva su valor. `{}` devuelve el panel existente sin escribir
ni cambiar fechas. No convierte booleanos, floats o strings numéricos a enteros;
no convierte números a texto. Rechaza texto que no se pueda codificar en UTF-8.
Campos desconocidos, incluidos ID, padre, timestamps y overrides, se rechazan.
Un campo inválido impide guardar todos los campos de esa solicitud.

Guardar SQL conserva comentarios, Unicode, saltos de línea y puntos y coma;
no ejecuta, parsea ni recorta el borrador. El límite existente del cuerpo HTTP
completo es 1 MiB antes de JSON, incluidos escapes y envoltura: el máximo de core
no implica que un texto de ese tamaño quepa en una solicitud. El presupuesto de
guardar el borrador no sustituye los límites por sentencia al ejecutar.

| Respuesta | Condición |
| --- | --- |
| 200 | Actualización confirmada, o lectura para `{}` |
| 422 | Campos, tipos, rangos o texto inválidos; sin escritura |
| 404 | Panel inexistente (`panel_not_found`); padre ausente al intentar modificar un panel histórico huérfano (`dashboard_not_found`) |
| 409 | Colisión o restricción de escritura: `panel_write_conflict`, después de rollback |
| 413 | Cuerpo HTTP excesivo: `body_limit` |

La validación del cuerpo conserva `detail: [{type, loc, msg}]` sin valores de
entrada ni contexto de excepciones. Los conflictos no exponen errores internos
de DuckDB. La autorización tiene sus propias respuestas y no se promete una
precedencia entre errores distintos de una solicitud inválida.

## Arquitectura y atomicidad

- [Core](../../packages/sqlviz-core/src/sqlviz_core/models/panels.py) define
  `Panel`, `PanelChanges` y la política pura. No importa HTTP, Pydantic o DuckDB.
  El modelo representa la persistencia actual, no reemplaza la futura separación
  dataset/visualización/instancia de panel de la decisión de autoría.
- [Contrato HTTP](../../packages/sqlviz-api/src/sqlviz_api/models.py) prohíbe
  extras y coerción; entrega solo campos presentes y reutiliza la política de
  core. La validación posterior rechaza `null`; las anotaciones opcionales
  representan la omisión y no son una autorización para borrar esos campos.
- [PanelRepository](../../packages/sqlviz-storage/src/sqlviz_storage/panel_repository.py)
  vuelve a validar llamadas directas y concentra lectura, listado, actualización
  y borrado. El router adapta el objeto de dominio a la respuesta existente.
- El [helper de timestamps](../../packages/sqlviz-storage/src/sqlviz_storage/timestamps.py)
  comparte la política existente con dashboards: UTC, microsegundos y valor
  distinto del previo. No constituye una revisión monotónica ni un ETag.

Una actualización no vacía abre una transacción sobre el cursor de la solicitud,
lee el panel y comprueba que su dashboard existe en ese snapshot, guarda todos
los campos y el timestamp, y lee el resultado dentro de la misma transacción.
El resultado solo sale del repositorio después de un commit confirmado. Fallos
de escritura, lectura posterior o commit revierten campos y timestamp juntos.
Los nombres de columnas se interpolan después de comprobar la lista permitida;
los valores se enlazan como parámetros.

El PATCH solo escribe esos campos y `updated_at`; conserva identidad, padre,
fecha de creación, fingerprint, inferencias, dimensiones, decisiones manuales
y títulos/etiquetas de presentación. No toca la fecha del dashboard ni la revisión
de carpetas. Paneles distintos del mismo dashboard pueden editarse simultáneamente.

## Coordinación con borrado

En los ensayos locales con **DuckDB 1.5.4**, una carrera de UPDATE frente a DELETE
sin protección adicional devolvía un resultado de panel que no existía al terminar
la operación. También se reprodujo el borrado del padre durante una actualización.
La documentación general de [concurrencia de DuckDB](https://duckdb.org/docs/current/connect/concurrency)
describe control optimista; las garantías del producto se prueban con las
operaciones concretas del repositorio y no se deducen únicamente de esa descripción.

Para cerrar esa carrera, los borrados participan sobre la misma columna que
actualiza el editor antes de ejecutar DELETE:

- `PanelRepository.delete` lee y modifica el timestamp del panel y luego lo
  elimina, todo en una transacción. La ruta conserva 204 después del commit,
  404 para un panel ausente y 409 para conflicto/restricción.
- `DashboardRepository.delete` mantiene su protección del padre frente a nuevas
  dependencias y además modifica los timestamps de sus paneles antes de borrar
  paneles, enlaces, filtros y dashboard. Usa un UPDATE conjunto y dos timestamps
  distintos para que cada fila cambie, también si el reloj coincide con su valor.
  Un conflicto conserva todo el agregado; devuelve `dashboard_write_conflict`.

Una edición en curso impide confirmar esos borrados y viceversa. Si el borrado
se confirma entre la lectura del panel y su escritura, la actualización falla
y no devuelve un panel fantasma. Si el padre se elimina antes de empezar, la
actualización obtiene 404. La lectura en una transacción conserva su snapshot
hasta que termine; otras lecturas no reciben por este cambio un snapshot global.

Las escrituras de metadatos deben usar estas operaciones; ejecutar DELETE
directamente desde otro consumidor no adquiere estas garantías. No hay bloqueo
global ni transacciones anidadas. Un panel histórico huérfano no se repara al
editarlo, pero el borrado individual permite limpiar esa fila.

## Compatibilidad y pendientes

El editor existente guarda SQL y orden antes de ejecutar; ese transporte permanece
compatible. Lecturas y listados usan el repositorio con la misma respuesta;
SQL histórico NULL se adapta a `""` sin reparar el archivo.

Cambiar SQL no genera una nueva inferencia ni verifica la compatibilidad de las
decisiones anteriores con los nuevos campos. La identidad actual por posición,
reconciliación de visualizaciones y revisiones persistidas pertenecen a unidades
posteriores. No se cambian esquema, `PanelCreate`, aprendizaje ni formato visual.

Los ajustes de presentación y overrides tienen sus propias rutas, todavía por
completar/revisar. La recuperación visible del autoguardado en la UI también sigue
pendiente. El conflicto transaccional no evita sobrescrituras en solicitudes
sucesivas: edición condicional, revisión y coordinación entre pestañas requieren
su contrato posterior. El servidor no reintenta automáticamente un conflicto.

## Evidencia

- [Política](../../packages/sqlviz-core/tests/test_panel_policy.py): null, omisión,
  tipos estrictos, Unicode, límites exactos y conservación del texto.
- [Repositorio](../../packages/sqlviz-storage/tests/test_panel_repository.py):
  conservación de todas las columnas visuales, fallo en escritura/lectura/commit,
  reapertura sintética, snapshots, concurrencia y reloj repetido; edición frente
  a borrado individual y del padre en ambos órdenes.
- [API](../../packages/sqlviz-api/tests/test_panel_patch.py): rechazo completo,
  SQL exacto, PATCH vacío, transporte del editor seguido de ejecución, conflictos
  y rollback de actualización/borrado, con errores sin datos internos.

Las pruebas existentes de dashboards, autorización, viewers y overrides se
incluyen en la suite completa. Logs y temporales nuevos de pytest bajo
`build/panel-patch-review/`, ignorados por Git; proyectos y aprendizaje de pruebas
aislados de los datos reales.

Validación local del 2026-10-07:

- **74 casos nuevos** de política, repositorio y API pasan dentro de la suite
  completa: **2042 pruebas pasan y 3 se omiten**, en 177,57 s.
- **129 pruebas enfocadas** de campos básicos, concurrencia, dashboards y
  repositorios pasaron antes de ampliar el ensayo con el reloj del borrado conjunto.
- `ruff check packages/` y mypy estricto de los cinco paquetes Python pasan
  (135 archivos de código revisados por mypy).
- 112 enlaces locales de Markdown verificados y `git diff --check` sin errores.
  Sin cambios de frontend ni nueva prueba de navegador; las pruebas HTTP usan
  el artefacto local existente y CI genera el suyo.

CI remoto se comprueba sobre el commit enviado. Estos resultados no certifican
E1 completo ni calidad del Studio futuro.
