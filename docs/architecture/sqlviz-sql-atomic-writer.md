# Guardado atómico de definiciones SQL

**Implementado — 2026-10-09: S1.1c.1.** Se entrega un repositorio interno que
guarda fuente, paneles y asociaciones en una sola transacción. **HTTP incorporado
en [S1.1c.2a](sqlviz-sql-commit-api.md) y Run en
[S1.1c.2b](sqlviz-sql-run-atomic-commit.md)**. Se confirma el guardado atómico de
definiciones; revisión ejecutada y recarga se incorporan en
[2c.1](sqlviz-sql-execution-definition.md) y [2c.2](sqlviz-sql-snapshot-reload.md).
Autoguardado y recuperación siguen pendientes en 2c.3.

## Contrato y límites entre capas

[SqlScriptRepository](../../packages/sqlviz-storage/src/sqlviz_storage/sql_script_repository.py)
recibe un cursor independiente del proyecto. `read(dashboard_id)` devuelve un
snapshot inmutable: ID, revisión esperada, borrador, paneles y publicación de
asociaciones compatible con esos paneles, si existe.

`write` recibe ID, revisión esperada, fuente exacta y decisiones explícitas del
[núcleo de reconciliación](sqlviz-sql-identity-reconciliation.md). Exige un parser
nativo del servicio de aplicación; no acepta un plan ni slices enviados por HTTP
como autorización para escribir. El parsing completo sucede antes de iniciar la
transacción. La política de reconciliación se repite dentro de ella contra los
paneles realmente persistidos y exige una propuesta completa.

El repositorio no importa FastAPI, SQLGlot, el servicio API ni renderers. El
servicio que lo invoque deberá comprobar autorización y elegibilidad de cada
consulta. La validación sintáctica no autoriza ejecución ni convierte DDL en una
consulta analítica. El repositorio guarda definiciones; **no ejecuta SQL del autor**.

El dashboard debe existir. Este incremento no crea dashboards, persiste layout,
publica revisiones del viewer ni implementa datasets reutilizables. No hay una
transacción distribuida entre proyecto y `brain.duckdb`.

## Revisión esperada y concurrencia

La revisión es un token SHA-256 versionado del estado leído en una única
transacción: dashboard, campos de paneles —incluidos SQL, orden, presentación,
ajustes e inferencia— y metadata del script. No se usa como ID ni como evidencia
para emparejar consultas por SQL. Tampoco es credencial o reserva de escritura.

El escritor vuelve a leer y comparar ese token dentro de su transacción. Un
cambio confirmado desde la lectura produce `SqlScriptWriteConflict` antes de
mutar. Es una comprobación conservadora: incluso cambios de nombre o borrador
requieren refrescar; no existe un merge silencioso.

Después de validar, el escritor modifica la fila del dashboard y **todas** las
filas de paneles anteriores, incluidos los que mantienen el mismo SQL. Las filas
a eliminar reciben primero una actualización real. Estos writes compiten con
PATCH, overrides, creación y borrado existentes en DuckDB. Un cambio confirmado
después de la comparación, o una escritura concurrente, también puede abortar la
transacción; no basta con validar un snapshot y luego escribir sin protección.

No se usa un bloqueo global del proyecto. Otro dashboard puede guardar mientras
el primero mantiene una transacción abierta. Un lector observa el estado
completo anterior hasta COMMIT y el nuevo al iniciar su siguiente lectura.

## Qué se guarda junto

- Fuente exacta del script en `dashboards.sql_content`.
- SQL y orden de paneles conservados por ID, sin cambiar sus nombres,
  overrides manuales ni títulos/etiquetas.
- Nuevos paneles con UUID asignado por almacenamiento; la respuesta relaciona
  `creation_key` con el ID creado. La clave del borrador no se convierte en ID.
- Borrados solo para decisiones explícitas y dentro del dashboard leído.
- Documento de asociaciones por ID y offsets UTF-16, ligado a su fuente exacta.

Si cambia el SQL de un panel, se retiran fingerprint e inferencias anteriores;
los valores seleccionados conservan sus overrides manuales. Reordenar SQL sin
cambiarlo conserva la inferencia. No se marca un Run exitoso, no se modifica
`last_run_sql`/`last_run_at`, ni se ejecuta composición dentro de esta transacción.
Los resultados y la clasificación se tratarán después del commit en la integración
de aplicación. Shares, memoria de filtros, datos analíticos y credenciales quedan
fuera de esta operación.

Un fallo en update, creación, borrado, documento o COMMIT restaura todo el conjunto.
El resultado solo sale del método después de COMMIT. Reintentar con el token
anterior a un commit confirmado devuelve conflicto y no duplica creaciones.
No hay caché de respuestas idempotentes; la recuperación de una respuesta perdida
deberá leer el nuevo snapshot, sin reenviar un conjunto sobre estado distinto.

## Persistencia y migración

`dashboard_sql_scripts` guarda una fila por dashboard: contador positivo de
revisión, fuente, JSON versionado de bindings y timestamp. El contador aumenta
en cada commit, incluso con igual SQL o reloj repetido; se rechaza agotamiento
del BIGINT. La revisión del documento y el token de estado tienen funciones
distintas: la primera cuenta commits del escritor; el segundo detecta también
operaciones legacy que aún no actualizan ese contador.

El [DDL](../../packages/sqlviz-storage/src/sqlviz_storage/schema.py) compartido
entre creación y [migración 0022](../../packages/sqlviz-storage/src/sqlviz_storage/migrations.py)
es aditivo e idempotente. **No fabrica bindings para proyectos antiguos**.
Abrir un proyecto conserva sus paneles/ajustes y devuelve asociación desconocida
hasta un commit explícito. La tabla se incluye en el catálogo reservado y no se
exporta al motor analítico. Borrar un dashboard elimina también esta fila en la
transacción de borrado existente.

La lectura valida versión, campos, presupuesto, claves JSON únicas, IDs y rangos.
Metadata corrupta produce error, no una asociación adivinada. Si un PATCH legacy
cambia SQL o paneles, una publicación anterior incompatible se devuelve como
ausente; permanece almacenada hasta reemplazarla o borrar el dashboard.
Cambiar presentación no invalida la identidad explícita, pero sí el token esperado.
Un borrador distinto de la fuente publicada tampoco hereda sus bindings por
igualdad parcial: la futura integración debe comprobar fuente exacta o procedencia.

El runner existente registra y reintenta migraciones fallidas; no se cambia su
política en esta parte. Si falta la nueva tabla, el repositorio no degrada a un
guardado parcial. La recuperación de schema/metadata corruptos no está automatizada.

## Evidencia y continuación

Pruebas sobre DuckDB real cubren rollback de cada etapa y COMMIT, lectura antes
del commit, dos escritores, operaciones legacy concurrentes, cambio posterior
a la validación, independencia de dashboards, revisiones obsoletas, creaciones
sin duplicar, SQL duplicado, UTF-16 y asociaciones inválidas. Se comprueba guardar
y reabrir tanto con éxito como tras un fallo. La migración se ensaya sobre una
copia de un proyecto legacy, conservando SQL, overrides y credenciales, dejando
el archivo original intacto. El parser nativo real se integra desde pruebas API,
incluida sintaxis inválida tardía y ausencia de ejecución de DDL.

Validación local: suite Python completa con **2.387 pruebas correctas y tres
omitidas**, y **57 casos focalizados** tras el endurecimiento final del documento
y del rollback de borrado. Ruff y mypy pasan. No se modifica frontend en esta
parte; su validación completa se ejecuta también en CI sobre el commit enviado.

Además se migra otra copia de la demostración archivada: tres dashboards y seis
paneles, sin ejecutar consultas. Se confirma guardar/reabrir asociaciones por
IDs construidos desde cada panel, overrides intactos y archivo de origen sin
cambios. Los artefactos están en `build/sql-atomic-review/`, ignorados por Git.
El servidor de vista previa existente no se reinicia ni cambia de comportamiento
por esta entrega interna.

**S1.1c.2a entregado:** [contrato HTTP y autorización](sqlviz-sql-commit-api.md)
para leer snapshot y guardar. **S1.1c.2b entregado:** Run con un único commit de
definiciones. **S1.1c.2c.2 entregada:** [recarga verificada](sqlviz-sql-snapshot-reload.md).
Siguiente: **S1.1c.2c.3**, autoguardado, conflictos y recuperación explícita.
Ver el [plan operativo](sqlviz-studio-delivery-plan.md).
