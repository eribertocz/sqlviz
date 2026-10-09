# Asociaciones del borrador SQL

**Implementado — 2026-10-08: S1.1b.2.** El editor registra procedencia de
ediciones y mantiene asociaciones tentativas con IDs de panel. La proyección
queda disponible en `dashboardStore.sqlIdentity`. La continuación
[S1.1b.3](sqlviz-sql-run-reconciliation.md) ya integra resolución y Run/foco por ID.
La persistencia de asociaciones pertenece a S1.1c.

## Responsabilidades

[sqlIdentityDraft.ts](../../packages/sqlviz-web/src/lib/sql/sqlIdentityDraft.ts)
es una política pura del borrador: fuente capturada, IDs anteriores y rangos
UTF-16. No importa Monaco, transporte, almacenamiento o un renderer. No parsea
SQL ni busca consultas por igualdad, nombres, posición o fingerprints.

[SQLEditor.svelte](../../packages/sqlviz-web/src/lib/components/SQLEditor.svelte)
adapta `onDidChangeModelContent` a fuente anterior/nueva, offsets, longitudes,
texto de sustitución e indicador `isFlush`. Comunica el evento antes de actualizar
`bind:value`. Las actualizaciones externas y el handle `setContent` se protegen
para no aparecer como ediciones del autor. También se verifica la actualización
reactiva de contenido y `readOnly` después de cargar Monaco.

[dashboardStore.svelte.ts](../../packages/sqlviz-web/src/lib/stores/dashboardStore.svelte.ts)
conserva el snapshot inmutable del borrador y usa el
[parser nativo](sqlviz-sql-script-parsing.md) existente para comprobar que cada
rango con identidad contiene una sola sentencia completa. El snapshot, la vista,
el dashboard y la fuente deben seguir vigentes al terminar la solicitud; respuestas
tardías no invalidan asociaciones de una edición posterior.

Esta proyección informa al preflight de S1.1b.3. No es autorización ni un plan de
escritura aceptable desde el navegador: el servidor valida decisiones
con el [núcleo de reconciliación](sqlviz-sql-identity-reconciliation.md) y el
snapshot de almacenamiento autorizado.

## Qué constituye evidencia

| Operación | Asociación resultante |
| --- | --- |
| Construir texto desde pares `panel_id`/SQL persistidos | Cada bloque conoce el panel desde el que se construyó; el parser debe confirmar los límites |
| Run exitoso de la sesión | Se registra qué ID ejecutó efectivamente cada fragmento; S1.1b.3 exige correspondencia explícita antes de escribir |
| Editar dentro de un bloque mediante rangos precisos | Conserva su ID y ajusta la extensión; el parser vuelve a comprobar la correspondencia |
| Insertar SQL antes de un bloque o eliminar otro bloque | Desplaza offsets; el bloque intacto mantiene su ID. Lo nuevo queda sin asignar y lo eliminado requiere decisión |
| Reemplazar un bloque completo o cruzar sus límites | Retira la evidencia de los bloques afectados |
| Reordenación opaca mediante cortar/pegar o reemplazo del script | Queda pendiente; no se deduce la nueva identidad a partir del contenido |
| Cargar SQL guardado sin metadatos de asociación | Queda pendiente, incluso si coincide con SQL conocido |
| Restaurar el último Run confirmado en la misma vista | Recupera su snapshot explícito; tras recarga/navegación no se inventa esa evidencia |

Los edits simultáneos se interpretan sobre los offsets de la fuente anterior,
independientemente del orden en que Monaco los entregue. Se comprueba que el
resultado de aplicarlos sea exactamente la fuente nueva. Eventos incoherentes,
superpuestos, `isFlush` o lotes de más de 1024 cambios retiran la evidencia;
no la convierten en una asociación arbitraria. Snapshots acotados a 256 paneles.

Las inserciones justo en un límite están fuera del bloque. Es deliberadamente
conservador: añadir una cláusula al final puede necesitar confirmar el panel,
mientras que insertar una consulta antes de otra no roba su identidad. Una
futura edición de consulta con destino explícito podrá aportar esa intención;
no se simula todavía a partir de la posición del cursor.

Si el parsing válido divide un rango en varias sentencias o fusiona bloques,
sus asociaciones quedan pendientes y se retiran del snapshot. La vuelta a un
texto conocido no las resucita por igualdad. Un fallo de sintaxis no destruye
por sí solo los rangos: una corrección interior puede conservar la procedencia.
No hay historial de identidad para undo/redo de reemplazos opacos en esta parte.

## Estado visible y persistido

Se conecta la captura al editor actual, sin nuevos controles ni cambio de formato
del proyecto. No se modifican gráficos, ajustes manuales o geometría durante una
edición. El autoguardado existente continúa guardando texto del borrador, no estas
asociaciones. No se promete conservación de identidad después de recargar.

La proyección distingue sentencias con `panel_id`, sentencias sin asignar y paneles
anteriores sin correspondencia. No crea ni elimina paneles. Cuando falta parsing
para la fuente exacta, el store devuelve `null` en lugar de una resolución obsoleta.

## Validación y continuación

- 29 pruebas nuevas: política de rangos, multicursor, inserción, borrado, SQL
  duplicado, split/merge, UTF-16, snapshots inmutables, eventos inválidos,
  actualización del componente, cargas y cambios de dashboard/respuestas tardías.
- Chromium con **SQLEditor y Monaco reales**, usando posiciones obtenidas de
  `SqlScriptService`: editar un literal con emoji conserva `a`/`b`; insertar otra
  consulta produce `a`/sin asignar/`b`; `setContent` no emite una edición del autor.
  Sin errores JavaScript y sin abrir una base de proyecto.
- Check con cero errores/advertencias, **226 pruebas frontend correctas** y build
  de producción completado. Las pruebas del store conservan el comportamiento
  previo de Run. Persisten las advertencias conocidas de teardown Svelte en
  pruebas y tamaño de chunks; no hubo errores nuevos en el navegador.

[S1.1b.3](sqlviz-sql-run-reconciliation.md) continúa este incremento con resolución
accesible y preflight de Run por ID, incluido el foco de edición. **S1.1c** debe guardar el
conjunto de forma transaccional y comprobar conflictos; una proyección de borrador
válida no sustituye esos controles. Ver el [plan operativo](sqlviz-studio-delivery-plan.md).
