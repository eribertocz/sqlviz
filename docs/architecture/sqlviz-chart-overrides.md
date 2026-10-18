# Tipo de gráfico: decisión confirmada del autor

**Estado:** implementado el 2026-10-08, quinto incremento de la unidad 8 de E1.
Continúa [presentación de paneles](sqlviz-panel-presentation.md). La revisión
completa de dimensiones y el cierre de E1 siguen pendientes.

## Contrato y responsabilidades

`PATCH /api/v1/panels/{id}/override` conserva sus campos obligatorios
`field_name` y `user_value`. Para `chart_type`, el valor es exactamente uno de
`kpi`, `line`, `bar`, `bar_horizontal`, `pie`, `scatter`, `histogram` o `table`.
`null` borra la decisión manual. Omitir el valor, enviar un tipo desconocido,
coerciones, espacios añadidos, otro casing o campos extra devuelve 422 antes
de cualquier escritura. El catálogo pertenece a core y también alimenta
los candidatos de inferencia. Valida identificadores; no certifica que cada
tipo sea adecuado para cualquier dataset. Funnel y opciones expertas quedan
fuera de este contrato actual.

El router adapta HTTP. `PanelRepository.set_override` valida de nuevo el dominio
y utiliza la misma transacción que los otros cambios del panel: verifica panel
y padre, escribe valor seleccionado/override y timestamp, obtiene una copia del
resultado y confirma. Reset toma la inferencia de esa misma transacción. Un
conflicto devuelve 409 con `code: panel_write_conflict`; un recurso inexistente
o un padre inexistente devuelve 404. Fallos posteriores a la escritura revierten
valor y fecha. Los fences de borrado del panel/dashboard protegen estos ajustes.

El escritor compartido se usa también para dimensiones; esta consolidación
no sustituye su revisión pendiente de controles y confirmación en la interfaz.
No se cambia el esquema del proyecto ni se migra el archivo del usuario.

`apply_override` coordina el guardado y el aprendizaje: primero confirma el
proyecto, después intenta actualizar patrón y evento en otra transacción.
Si el aprendizaje falla, conserva el guardado y registra un aviso sin SQL,
rutas ni mensajes privados de la excepción. No hay una transacción distribuida
entre proyecto y memoria. La respuesta contiene la copia confirmada de la
operación, sin releerla después del aprendizaje. Reset no escribe aprendizaje.

## Automático y manual

Al ejecutar, `inferred_chart_type` recibe `chart_engine_winner`, mientras
`selected_chart_type` conserva la elección manual. Antes se persistía
`chart_winner`, que ya incluía el override y podía contaminar el valor automático.

`InferenceResult` incorpora `chart_user_override: string | null`, con valor
predeterminado `null`, también admitido por composición y expuesto al frontend.
Es una ampliación opcional compatible del contrato de resultado versión 1.
Distingue la intención del autor incluso cuando el tipo seleccionado coincide
con la recomendación. Un resultado antiguo sin ese campo usa la comparación
de ganadores como fallback en el selector.

Reset envía `user_value: null`; no fija el ganador automático de ese momento.
El ajuste desaparece del proyecto y futuras ejecuciones siguen la inferencia.
La memoria de preferencias existente no se borra al resetear un panel: retirar
una decisión local y purgar aprendizaje son operaciones distintas.

## Confirmación en la interfaz

El store serializa los cambios de tipo. Guarda, ejecuta el panel con los filtros
actuales y compone los resultados en un buffer; publica datos y layout juntos.
Ante rechazo del PATCH conserva el gráfico anterior y devuelve un error que el
selector presenta con reintento. Mientras guarda, mantiene seleccionada la
opción confirmada, muestra estado y bloquea cambios duplicados.

Si la elección ya se guardó pero falla ejecución/composición, muestra esa
distinción y ofrece `Retry refresh`: repite la lectura/composición, sin otro
PATCH ni otro evento de aprendizaje. Un reset fallido conserva su intención
`null` para reintento. Las opciones con una elección manual muestran `Manual`;
la recomendación se identifica aparte. Una elección persistida ausente de las
nuevas alternativas permanece visible sin inventar un porcentaje de score.

La generación de vista y la referencia a los resultados evitan que una respuesta
tardía reemplace otro dashboard o un cambio confirmado durante la espera.
Se invalida la caché del dashboard objetivo, incluso tras un fallo de transporte
ambiguo. El selector se identifica por panel para no transferir estado de error
o reintento al abrir otro inspector.

## Límites y siguiente parte

No añade revisiones/ETag, undo, reconciliación entre pestañas o publicación
versionada. Un fallo de transporte puede dejar ambiguo si el servidor guardó;
la interfaz ofrece reintento e invalida caché, sin afirmar que hubo rollback.
Los valores históricos inválidos y la dependencia storage → inference del
evento de aprendizaje no se migran aquí. El aprendizaje conserva su ámbito
global actual; aislamiento por workspace pertenece a una unidad posterior.

Tampoco valida compatibilidad de campos/unidades/series de todos los tipos ni
certifica calidad de inferencia. Esas capacidades corresponden al contrato visual
y al Studio. Siguiente: revisar dimensiones sobre este escritor transaccional,
antes de migraciones/dependencias y dataset mínimo del
[plan vigente](sqlviz-product-roadmap.md).

## Evidencia

- 22 casos core: catálogo, entradas inválidas y reset explícito.
- 15 casos storage: copia confirmada, rollback, fallos de aprendizaje, patrón/evento
  atómicos, borrado concurrente, reset y reapertura de proyecto sintético.
- 22 casos API: validación sin efectos, omisión/extras, 409, aprendizaje fallido,
  separación automático/manual, composición, lectores de dashboard/workspace.
- 12 casos frontend añadidos: confirmación, errores/reintentos, refresh sin PATCH,
  filtros actuales, serialización, respuestas tardías y metadatos manuales.
- Chromium 1600×1000: rechazo 409 mantiene la selección, reintento con demora
  mantiene el radio confirmado y bloquea duplicados; fallo de composición
  distingue guardado/refresh y reintenta sin otro PATCH. Reset deja `null`, la
  elección funciona con teclado y sobrevive a recarga/Run y viewer compartido.
  Los seis recorridos pasan sin errores de página. Svelte-check sin diagnósticos,
  162 pruebas frontend pasan y build correcto; Ruff y mypy pasan.
- Suite Python final: 2165 pasan y 3 omitidas. Proyectos de pruebas bajo un
  `--basetemp` nuevo dentro de la carpeta de revisión; no se abren archivos reales.

Logs y revisión en `build/chart-override-review/`, ignorado por Git. Los ensayos
usan proyectos y memoria sintéticos; el navegador usa ambos catálogos en RAM.
La CI se comprueba sobre el commit enviado. Esto no certifica E1 completo.
