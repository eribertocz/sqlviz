# Identidad y reconciliación SQL: primer núcleo

**Implementado — 2026-10-08: S1.1b.1.** Política pura y contrato interno de
decisiones explícitas. El editor captura [asociaciones del borrador en S1.1b.2](sqlviz-sql-draft-identity.md);
editor y Run **todavía no consumen este núcleo como preflight de escritura**.
La asociación posicional actual sigue pendiente de reemplazo en S1.1b.3.
No hay nuevos endpoints, migraciones ni escrituras de proyectos en esta entrega.

## Problema y regla de identidad

Run actual recorre las sentencias y usa `activePanelIds[i]`. Si se inserta una
consulta antes de otra, se puede editar el SQL del panel equivocado y conservar
allí sus ajustes. El [parser nativo](sqlviz-sql-script-parsing.md) resuelve límites
de sentencias, pero sus offsets e índices no establecen identidad.

El núcleo recibe el SQL fuente, sus sentencias nativas, un snapshot de paneles
existentes del dashboard y decisiones de asociación. No deduce identidad por
posición, igualdad de SQL, nombres, campos o fingerprints. Dos paneles pueden
tener exactamente la misma consulta y ajustes diferentes.

Por ahora conserva la referencia `panel_id` existente. No crea un ID persistido
de consulta ni adelanta el modelo dataset/visual/panel de S3. La aplicación deberá
aportar decisiones del autor o procedencia comprobable de una edición; este
núcleo valida su coherencia, no demuestra cómo se obtuvieron.

## Contrato implementado

[sql_reconciliation.py](../../packages/sqlviz-core/src/sqlviz_core/models/sql_reconciliation.py)
no importa HTTP, DuckDB, almacenamiento, DOM ni un renderer. Sus dataclasses son
inmutables y el resultado copia las colecciones de entrada a tuplas.

| Decisión | Efecto en la propuesta |
| --- | --- |
| `KeepSqlPanel(statement_index, panel_id)` | Conserva el ID y registra SQL anterior/nuevo; admite editar y reordenar |
| `CreateSqlPanel(statement_index, creation_key)` | Propone un panel nuevo con una clave de borrador; no asigna un ID de base de datos |
| `RemoveSqlPanel(panel_id)` | Propone una eliminación explícita; no ejecuta el borrado |
| Sin decisión | Mantiene pendientes la sentencia o el panel existente; no los crea, reasigna ni elimina |

`statement_index` direcciona únicamente el parsing de **esa fuente**, no una
identidad persistente. `creation_key` mantiene identificada una decisión nueva
dentro del borrador; no garantiza idempotencia HTTP ni recuperación tras recarga.

La propuesta ordena las sentencias resueltas según la fuente y las eliminaciones
según el snapshot. Puede estar incompleta para alimentar una futura resolución
en UI. `complete` indica cobertura total y `require_complete()` rechaza la
admisión de propuestas pendientes. Ninguna de esas operaciones escribe datos.
`sql_changed` compara texto exacto; no diagnostica compatibilidad semántica ni
ordena descartar resultados o decisiones manuales.

Ejemplo: existen `sales = SELECT 1` y `costs = SELECT 2`. La nueva fuente contiene
`SELECT 20; SELECT 3; SELECT 1`. Conservar `costs` para la primera sentencia,
crear `draft-new` para la segunda y conservar `sales` para la tercera produce
esa misma secuencia, con ambos IDs anteriores intactos. Sin esas asociaciones,
el conjunto queda pendiente, aunque una sentencia coincida con SQL anterior.

## Validación y límites

- Una sentencia recibe una sola decisión. Un panel anterior se conserva una vez
  o se elimina una vez; no ambas. No se acepta un ID ajeno al snapshot.
- Claves de creación únicas en la propuesta; IDs opacos sin normalización,
  espacios exteriores ni controles, válidos en UTF-8 y de hasta 256 bytes.
- Fuente de hasta 1 MiB UTF-8, 256 sentencias, 256 paneles anteriores y 512
  decisiones. Índices y offsets enteros estrictos, sin coerción de booleanos.
- Offsets UTF-16 ordenados, sin solapamiento y cuyo fragmento coincide con la
  fuente exacta. Un parsing obsoleto que ya no coincide se rechaza.
- Una fuente vacía o de comentarios no elimina paneles por omisión: quedan
  pendientes hasta decidir explícitamente sus eliminaciones.

Errores de identidad usan `sql_reconciliation_invalid`,
`sql_reconciliation_limit` o `sql_reconciliation_unresolved`. La validación de
texto comparte `SqlScriptError` con el parser; no reproduce SQL en diagnósticos.

El caller debe usar el parsing nativo completo para la fuente capturada y cargar
el snapshot desde un dashboard autorizado. La comprobación de spans no demuestra
por sí sola que una lista arbitraria contenga todas las sentencias. Tampoco
autoriza recursos o comprueba concurrencia de almacenamiento. Un futuro writer
debe reconstruir/validar la propuesta en servidor y comprobar el estado esperado;
no confiar en un plan enviado por el navegador.

## Evidencia y siguientes incrementos

Se añaden **53 casos** entre política pura e integración con `SqlScriptService`.
Cubren todas las permutaciones de tres consultas editadas, inserción/reordenación,
SQL duplicado, desaparición de un bloque, borrador vacío, decisiones contradictorias,
snapshots inválidos, presupuesto, inmutabilidad, fuente obsoleta y UTF-16.
El parser real alimenta cuatro formas con comentarios, CTEs y literales con `;`.

El conjunto de reconciliación y parsing ejecutado da **82 pruebas correctas**;
Ruff y mypy pasan. No se declara roundtrip de UI o persistencia a partir de estas
pruebas: el núcleo aún no está conectado a esos flujos.

Continuación en el [plan operativo](sqlviz-studio-delivery-plan.md): S1.1b.2 ya
mantiene asociaciones en el borrador y registra ediciones con procedencia;
S1.1b.3 integra resolución de ambigüedad y preflight de Run por ID. S1.1c entrega
el guardado transaccional del conjunto. Solo después asociamos el lienzo
persistido S1.2 a esos IDs y conectamos los gestos GridStack S2.
