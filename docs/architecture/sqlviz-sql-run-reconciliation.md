# Run con asociaciones explícitas de panel

**Implementado — 2026-10-09: S1.1b.3.** Run y «Editar SQL» usan IDs de panel
validados, sin asignarlos por posición del SELECT ni por igualdad de SQL.
La [procedencia del borrador](sqlviz-sql-draft-identity.md) aporta asociaciones
tentativas; las decisiones ambiguas se confirman bajo demanda. El guardado
transaccional y los borrados explícitos se incorporaron después en
[S1.1c.2b](sqlviz-sql-run-atomic-commit.md). Este documento conserva el recorrido
y la evidencia de la primera entrega S1.1b.3; consultar 2b para el comportamiento actual.

## Responsabilidades y recorrido de S1.1b.3

1. El parser nativo comprueba todo el script antes de modificar paneles.
2. [sqlRunResolution.ts](../../packages/sqlviz-web/src/lib/sql/sqlRunResolution.ts)
   proyecta decisiones de conservar/crear. Solo propone automáticamente una
   creación cuando todos los IDs anteriores están asociados. Si falta alguno,
   solicita una elección explícita; una consulta idéntica no identifica un panel.
3. [SqlRunResolutionDialog.svelte](../../packages/sqlviz-web/src/lib/components/SqlRunResolutionDialog.svelte)
   muestra las consultas y un selector por consulta. El autor puede comparar el
   SQL anterior, conservar un panel, crear uno nuevo o retirar una selección para
   intercambiar asociaciones. Un ID no puede pertenecer a dos consultas.
4. `POST /api/v1/sql/reconcile` vuelve a parsear el SQL y lee los paneles del
   dashboard autorizado en un snapshot transaccional. Comprueba el conjunto de
   IDs esperado y aplica el [núcleo de reconciliación](sqlviz-sql-identity-reconciliation.md).
5. El cliente exige una respuesta completa que coincida con la fuente, las
   decisiones y los rangos. Si sigue vigente la vista y el texto, Run actualiza
   cada panel por el ID confirmado o crea uno nuevo; no usa `panelIds[i]` como
   correspondencia de consultas existentes.
6. Un Run exitoso registra el vínculo explícito de esa sesión. «Editar SQL»
   busca el rango por ID; una asociación desconocida avisa en lugar de enfocar
   una consulta que podría pertenecer a otro panel.

La política web no importa DOM ni HTTP. El diálogo adapta esa política a una
interacción accesible. El router adapta contratos estrictos al núcleo y lee
almacenamiento; no ejecuta SQL ni crea, modifica o elimina paneles.

## Contrato del preflight

[sql_script_contract.py](../../packages/sqlviz-api/src/sqlviz_api/sql_script_contract.py)
define fuente, dashboard opcional, `expected_panel_ids` y decisiones discriminadas
`keep`, `create` y `remove`. Se rechazan campos extra, coerciones e índices
fuera del presupuesto. Los límites nativos de fuente/sentencias se conservan;
el núcleo vuelve a comprobar IDs, rangos y correspondencia uno a uno.

La respuesta contiene sentencias resueltas, removals propuestos y referencias
pendientes. `complete` no significa que se haya guardado nada. El endpoint
puede evaluar una eliminación explícita, pero **no la efectúa**. Un snapshot de
IDs distinto devuelve 409; referencias ajenas al dashboard se rechazan. Usa la
autorización de autor y la política `no-store` existente.

## Interacción y protección del borrador

No se añade una barra permanente. El diálogo tiene foco inicial en el primer
selector, navegación de teclado, cierre por Escape y retorno al botón Run.
Cabecera y acciones permanecen visibles; el cuerpo desplaza el contenido en
pantallas pequeñas. El modal se monta en el workspace, independiente de que el
drawer del editor esté visible. Los atajos del workspace no interfieren dentro
de un diálogo.

Editar la fuente, restaurarla o cambiar de dashboard invalida elecciones
pendientes. Una respuesta tardía de parsing/preflight no empieza escrituras si
la fuente o la vista cambiaron. Cancelar no crea ni modifica paneles. Un fallo
de preflight conserva elecciones para reintentar; nunca se ejecuta una propuesta
incompleta. Los PATCH de panel solo envían SQL y orden, conservando ajustes
manuales ligados al ID.

## Límites que S1.1c debe resolver

- La UI exige asociar todos los paneles existentes. Quitar una consulta no borra
  su panel ni permite confirmar una propuesta parcial. El borrado explícito desde
  el script espera a la escritura atómica; el borrado individual existente es
  otro flujo.
- Run todavía usa solicitudes separadas para persistir y ejecutar cada panel.
  **Un fallo posterior al primer PATCH/POST puede dejar cambios parciales.**
  Este incremento evita emparejamientos incorrectos, pero no elimina ese riesgo.
- El preflight verifica el conjunto de IDs en el instante de lectura. No es
  una reserva, revisión optimista del SQL ni protección frente a cambios entre
  validación y escrituras posteriores. El escritor de S1.1c debe validar el estado
  esperado de nuevo dentro de la misma transacción que guarda el conjunto.
- Las asociaciones confirmadas son de sesión. Recargar SQL arbitrario guardado
  vuelve a pedir confirmación; todavía no se persistieron metadatos de identidad.
- `creation_key` correlaciona una propuesta; aún no implementa creación durable
  idempotente. Un fallo parcial que cambie el conjunto de IDs exige recargar antes
  de reintentar. No se promete un rollback de ejecución ni de resultados.

## Evidencia

Las pruebas de API usan DuckDB y autorización reales: reordenación, SQL duplicado,
creación/eliminación solo como propuestas, referencias ajenas, conflictos,
contratos estrictos, sintaxis inválida y UTF-16. Las pruebas web cubren decisiones
completas, propuestas contradictorias, teclado/foco, cancelación, reordenación
por IDs, inserciones con procedencia y cambios de fuente durante el preflight.

Validación local: **2.331 pruebas Python correctas, tres omitidas**; suite frontend
completa de **249 pruebas**, seguida de **27 pruebas de store/diálogo** tras el
ajuste final de recuperación de foco. Check sin errores/advertencias, Ruff y
mypy correctos, build de producción completado. Persisten los avisos conocidos
de teardown Svelte en pruebas y tamaño de chunks.

Chromium sobre el build de producción y un proyecto aislado confirma selección
por ID, cancelación sin escrituras, duplicados deshabilitados, ancho/alto manuales
conservados, retorno de foco y creación de una tercera consulta mediante teclado
en Monaco real. El recorrido móvil a 390 × 650 mantiene las acciones visibles,
sin errores JS ni respuestas API fallidas. En la copia de vista previa existente
se comprueba apertura/cancelación conservando sus seis paneles. Los artefactos
de revisión están en `build/sql-run-review/`, ignorados por Git; no se alteró la
instancia original de demostración.

[S1.1c.1](sqlviz-sql-atomic-writer.md) ya entrega snapshot y escritor transaccional
internos; S1.1c.2a entrega HTTP autorizado y S1.1c.2b conecta el commit único de
Run, reemplazando sus escrituras secuenciales y habilitando borrados explícitos.
La recarga y recuperación continúan en S1.1c.2c. Los límites anteriores describen
la primera entrega, no el estado actual. Ver el [plan operativo](sqlviz-studio-delivery-plan.md).
