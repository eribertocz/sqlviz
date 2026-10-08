# Presentación de paneles: contrato y guardado confirmado

**Estado:** implementado el 2026-10-07, cuarto incremento de la unidad 8 de E1.
Continúa el [PATCH básico del panel](sqlviz-panel-patch.md). E1 sigue abierto:
la revisión de overrides de tipo y dimensiones es la siguiente parte.

## Contrato HTTP

`PATCH /api/v1/panels/{panel_id}/view-override` requiere autorización de autor.
Recibe exactamente dos campos obligatorios:

```json
{"field": "title", "value": "Ventas por región"}
```

| Entrada | Semántica |
| --- | --- |
| `field` | Solo `title`, `x_label` o `y_label` |
| `value` con texto | String estricto, hasta 512 caracteres, codificable en UTF-8; conserva los espacios originales |
| `value: null` o `value: ""` | Restablece el valor automático; guarda NULL |
| `value` omitido | 422; no equivale a borrar |
| Texto formado solo por espacios | 422; sin escritura |
| Tipos incorrectos, campos desconocidos o texto excesivo | 422; sin escritura |

La respuesta 200 conserva `status: "ok"` y añade `field`, `value` normalizado y
`updated_at`, después del commit. GET, listado y respuestas de creación/PATCH
básico incluyen los tres campos nullable `view_title`, `view_x_label` y
`view_y_label`. Son adiciones al transporte; las columnas ya existían.

El contrato conserva 404 (`panel_not_found`, o `dashboard_not_found` para un
panel histórico huérfano al escribir) y 409 (`panel_write_conflict`) sin errores
internos de DuckDB. Los viewers pueden leer estos ajustes dentro del alcance
de su enlace, pero no modificarlos. El límite general del cuerpo HTTP también
sigue vigente. No se reparan automáticamente valores históricos inválidos.

**Compatibilidad:** anteriormente omitir `value` borraba el ajuste; los clientes
que dependían de ello deben enviar null o vacío explícito. La validación más
estricta también rechaza texto excesivo, solo espacios y campos extra. Se registra
en Breaking del changelog. El frontend existente ya enviaba ambos campos.
No cambian las versiones de `InferenceResult`, `VisualSpec` o del esquema `.sqlviz`.

## Límites de arquitectura

- [Política de core](../../packages/sqlviz-core/src/sqlviz_core/models/panel_presentation.py):
  campos admitidos, longitud, Unicode y normalización; sin HTTP ni persistencia.
- [Contrato HTTP](../../packages/sqlviz-api/src/sqlviz_api/models.py): valida
  presencia y tipos estrictos, prohíbe extras y reutiliza la política de core.
- [PanelRepository](../../packages/sqlviz-storage/src/sqlviz_storage/panel_repository.py):
  vuelve a validar llamadas directas y comparte la operación transaccional con
  el PATCH básico. El helper histórico `set_view_override` delega al repositorio.
- [Router](../../packages/sqlviz-api/src/sqlviz_api/routers/panels.py): adapta el
  panel confirmado a la respuesta, sin repetir SQL de actualización.

El repositorio lee panel y padre dentro de la transacción, escribe solo la columna
permitida y el timestamp, lee el resultado y lo devuelve después del commit.
Valores enlazados; columnas procedentes de una lista fija. Fallos de escritura,
lectura o commit revierten el ajuste y la fecha juntos. Conserva SQL, fingerprint,
inferencias, dimensiones y los otros ajustes. No modifica el timestamp del padre.

Se reutiliza la [coordinación con borrado](sqlviz-panel-patch.md#coordinación-con-borrado)
del panel y del dashboard. Las pruebas ejercitan estas carreras también desde
presentación. Las garantías requieren usar las operaciones del repositorio;
una escritura SQL directa externa no participa en ese protocolo.

## Experiencia del editor

El [store](../../packages/sqlviz-web/src/lib/stores/dashboardStore.svelte.ts)
serializa los cambios de presentación y actualiza resultados y layout después
de la respuesta confirmada. Un rechazo conserva el gráfico anterior. Invalida
la caché del dashboard afectado también ante errores de transporte ambiguos y
descarta la publicación de una respuesta de una vista abandonada.

El [control compartido](../../packages/sqlviz-web/src/lib/components/PanelPresentationInput.svelte)
se usa en el inspector y en la edición de etiquetas sobre el gráfico. Mantiene
el borrador al fallar, muestra el motivo y ofrece Retry; deshabilita el campo
mientras guarda y evita duplicar Enter/blur. Las etiquetas y errores tienen
nombres y relaciones accesibles. La edición sobre el gráfico enfoca el campo,
permite cancelar con Escape y mantiene el editor abierto si falla. El editor
del eje Y y sus errores se muestran horizontalmente para poder leerlos.
Al confirmar o cancelar esa edición se devuelve el foco a su etiqueta; el blur
producido por ese cierre no guarda un borrador cancelado ni repite la escritura.
La confirmación captura la sesión de edición que inició el guardado: si el usuario
abre otra etiqueta mientras espera, la respuesta anterior no cierra su nuevo
borrador ni le roba el foco.
Los campos
usan el color de texto del tema para conservar contraste en claro y oscuro.

El transporte convierte los errores de validación HTTP en mensajes legibles,
en lugar de mostrar objetos JSON como texto. No se recorta el título o etiqueta
antes de enviarlo. El borrador permanece mientras exista ese control; cerrar
el inspector o navegar no constituye un guardado de borradores pendientes.

Cambiar un título no vacío o una etiqueta no ejecuta SQL ni recompone el dashboard.
Restablecer una etiqueta usa su campo automático como fallback del renderer.
Restablecer el título requiere volver a ejecutar ese panel y componer: el resultado
anterior ya contiene el título personalizado y no persiste una copia de la
inferencia original. La consulta conserva los filtros confirmados y usa los
presupuestos analíticos existentes. Resultado y layout se publican juntos.

Si el borrado del título se guarda pero falla la consulta/composición posterior,
la UI lo indica como **guardado con fallo al actualizar**; conserva el gráfico
anterior y permite reintentar o ejecutar de nuevo. No presenta ese caso como
rollback de una escritura que ya se confirmó.

## Límites y siguiente incremento

No incorpora revisiones/ETag, undo, coordinación entre pestañas ni publicación
versionada. Tampoco resuelve todas las carreras entre ejecución, filtros y
controles de metadatos distintos. El autoguardado general de SQL y otros campos
requiere su propia recuperación visible. Los selectores de campos X/Y siguen
siendo ajustes de sesión; persistirlos corresponde al contrato visual posterior.

La siguiente parte revisa las rutas de override de tipo y dimensiones, su
confirmación transaccional y la separación del aprendizaje opcional. Después
siguen migraciones/dependencias y dataset mínimo según el
[plan vigente](sqlviz-product-roadmap.md). Este incremento no entrega el Studio.

## Evidencia

- [Core](../../packages/sqlviz-core/tests/test_panel_presentation_policy.py),
  [repositorio](../../packages/sqlviz-storage/tests/test_panel_presentation.py) y
  [API](../../packages/sqlviz-api/tests/test_panel_presentation_api.py): 64 casos
  nuevos; límites, Unicode, preservación, rollback, reapertura, borrado concurrente,
  transporte, autorización y presentación en viewers.
- [Store](../../packages/sqlviz-web/src/lib/stores/dashboardPresentation.svelte.test.ts),
  [control](../../packages/sqlviz-web/src/lib/components/PanelPresentationInput.test.ts) y
  [errores HTTP](../../packages/sqlviz-web/src/lib/api.test.ts): confirmación,
  rechazo/reintento, serialización, cambio de vista y restauración automática.

Logs, temporales y revisión de navegador se guardan bajo
`build/presentation-review/`, ignorado por Git. Los proyectos y el catálogo de
aprendizaje de revisión son sintéticos y están aislados de los datos reales.

Validación local del 2026-10-07:

- Suite Python completa: **2106 pasan y 3 se omiten**, en 210,40 s.
- **112 pruebas enfocadas** de presentación y PATCH básico pasan.
- **150 pruebas frontend** pasan; 17 nuevas de este incremento y su corrección de sesión.
- Ruff y mypy estricto pasan, con 136 archivos de código revisados por mypy.
- Svelte-check sin errores ni advertencias; build de producción generado.
- Navegador Chromium, escritorio 1600×1000: guardado exacto sin consultas,
  validación 422 real, conflicto 409 simulado con reintento en inspector y gráfico,
  foco al reintentar/cerrar, Escape sin escritura, viewer con recarga y título
  automático real. Cambiar de eje durante un guardado conserva el nuevo borrador
  y su foco. Color del texto verificado en claro/oscuro; sin errores JS.
- 129 enlaces Markdown locales verificados y `git diff --check` sin errores.

Persisten las advertencias conocidas de teardown `derived_inert` y tamaño de
chunks de Vite. No se presenta este ensayo de escritorio como validación móvil,
estudio con usuarios o certificación completa de accesibilidad.

CI se comprueba sobre el commit enviado; estas pruebas no certifican E1 completo.
