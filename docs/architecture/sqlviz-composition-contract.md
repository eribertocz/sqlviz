# Contrato HTTP de composición

**Estado:** BP-04 implementado localmente el 2026-10-07. Es la primera parte de
la unidad 8 de E1; los PATCH restantes siguen pendientes. No modifica el archivo
`.sqlviz`, el algoritmo de inferencia ni la edición visual.

## Responsabilidad y límites

`POST /api/v1/compose` recibe un array de `{panel_id, inference_result}`. Compone
resultados existentes, sin ejecutar SQL. El array vacío devuelve `{"rows": []}`.
La forma de solicitud y respuesta permanece compatible con autor y viewers.

El contrato vive en
[compose_contract.py](../../packages/sqlviz-api/src/sqlviz_api/compose_contract.py).
Pydantic se limita a la frontera HTTP: el adaptador entrega `InferenceResult` y
sus objetos anidados como dataclasses al motor. No añade dependencias de FastAPI
o Pydantic a core, storage o inference.

| Entrada | Regla |
| --- | --- |
| Colección | Hasta 256 paneles; cada ID aparece una sola vez |
| ID de panel | String de 1–128 caracteres, no compuesto solo por espacios; no se convierte desde números ni se exige UUID |
| Resultado | Campos obligatorios de `InferenceResult`; sin campos desconocidos en los contratos estructurados |
| Ancho y alto | Enteros estrictos, 1–12 columnas y 120–900 px; los rangos son los de core |
| Filas | `row_span` entero de 1–3, según el contrato del motor actual |
| Declaración de layout | Mínimo ≤ preferido ≤ máximo, para ancho y alto |
| Números | Finitos, también dentro de diagnósticos JSON; tiempos no negativos |
| Versiones | `result_schema_version` y `visual_spec.schema_version` admiten `"1"`; omisión usa la versión actual |
| Cuerpo HTTP | Límite existente de 1 MiB antes de analizar JSON, también con envío por chunks |

Se validan `data_profile`, `visual_spec`, `layout_declaration`, `dashboard_role`
y `explanation_v2` con sus estructuras propias. Los diagnósticos y colecciones
heredadas de explicaciones, alternativas y controles conservan su contenido
JSON extensible; no se les atribuye todavía un contrato semántico completo.
Los nombres de gráfico e intención siguen siendo strings para permitir las
extensiones que soporta el motor; validar compatibilidad de campos/series es
trabajo posterior del contrato visual.

## Errores y acceso

Un campo ausente, tipo incorrecto, rango inválido, ID repetido, versión no
soportada o campo estructurado desconocido devuelve **422**. FastAPI valida la
solicitud antes de entrar en el motor o consultar los anchos fijados. El error
usa la forma existente `detail: [{type, loc, msg}]`, sin incluir valores enviados
ni contexto interno de excepciones. Un cuerpo excesivo devuelve **413**.

La autenticación y autorización no cambian: el lector necesita un enlace/sesión
vigente y acceso a cada panel; un panel fuera del alcance devuelve **404** para
una solicitud válida. Una solicitud mal formada puede devolver 422 antes de la
comprobación por panel, por lo que el cliente no debe depender de una precedencia
404/422 para entradas inválidas. Un autor conserva el uso de IDs sintéticos al
componer resultados. Este endpoint no guarda resultados ni concede acceso a SQL.

Los anchos fijados se leen del proyecto después de verificar el alcance; no se
acepta una declaración del cliente que suplante esos valores.

## Conservación del resultado y evolución

La respuesta conserva el `inference_result` recibido: no inserta defaults ni
elimina nulls o etiquetas de presentación. `x_label` y `y_label` están admitidos
en el contrato HTTP porque `/execute` los incorpora después de la inferencia;
no se pasan como campos nuevos a la dataclass `VisualSpec`.

El adaptador construye los objetos del motor a partir de datos validados y
mantiene una representación separada para la respuesta. Una prueba compara los
campos del contrato con los de `InferenceResult`, de modo que añadir un campo
al motor requiere revisar explícitamente la frontera HTTP.

Cambiar las formas estructuradas requiere actualizar contratos, productores,
consumidores y pruebas conjuntamente. Una versión futura no se acepta
silenciosamente. Los campos opcionales omitidos siguen siendo compatibles;
enviar campos desconocidos ahora produce un rechazo explícito.

## Evidencia y siguiente incremento

[Pruebas del contrato](../../packages/sqlviz-api/tests/test_compose_contract.py):
entradas negativas, números no finitos, límites, OpenAPI, adaptación a dataclasses
y conservación del JSON. Se ejercitan también resultados reales de SQL con KPI,
categorías, fechas, correlación, filas vacías y nulls. Las pruebas existentes
comprueban el alcance de viewers y la persistencia de tamaños manuales.

El siguiente incremento es PATCH de campos restantes: presencia/omisión/null,
tipos y límites antes de escribir, respuesta predecible y escritura atómica.
BP-04 no cierra E1 ni certifica calidad de inferencia, usabilidad o rendimiento.

Validación local del 2026-10-07:

- 63 casos nuevos de contrato; 183 pruebas enfocadas de composición, dimensiones,
  autorización y overrides pasan.
- Suite Python completa: **1882 pasan, 3 omitidas** (164,49 s).
- `ruff check packages/` y mypy estricto de los cinco paquetes Python pasan
  (131 archivos de código revisados por mypy).
- `git diff --check` pasa. No se modificó frontend en este incremento; su
  compatibilidad se comprueba mediante el transporte existente y las rutas API
  de autor/lector. CI remoto y una nueva revisión de navegador siguen sin ejecutarse
  para este cambio.

Los temporales de pytest se crearon dentro de `build/compose-review`, separado
del proyecto del usuario y de la base de aprendizaje real. Logs locales en
`build/compose-review/focused.log` y `build/compose-review/python-full.log`
(artefactos ignorados por Git).
