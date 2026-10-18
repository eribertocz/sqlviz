# Parámetros y controles de calidad — cuarta unidad de E0

**Implementado en el árbol de trabajo: 2026-10-06.** Completa el contrato inicial
de valores de filtros y los controles de tipos/frontend de E0. La evidencia
local no reemplaza ejecutar CI ni acredita un despliegue público.

## Contrato de parámetros

Autor y lector envían `{ "variables": { "region": "North" } }` al ejecutar un
panel. `ParameterService` aplica el mismo contrato a ambos. El lector ejecuta
solo SQL guardado; enviar `sql_content` u otros campos de ejecución desconocidos
ahora retorna 422, en lugar de ignorarlos. No modifica el SQL ni el proyecto.

| Valor | Regla |
| --- | --- |
| Texto | String Unicode válido, sin conversión automática del transporte |
| Número | Entero en rango signed 128-bit o flotante finito; booleano no cuenta como número |
| Booleano | `true` / `false`, preservando su tipo |
| Lista | Plana, sin NULL y con una sola clase de elementos: texto, números o booleanos |
| Ausente, NULL, `""`, `[]` | «Todos»: neutraliza su predicado de negocio si puede hacerlo con seguridad |
| `0`, `false`, `" "`, `[""]` | Selecciones reales; no significan «Todos» |

Los nombres son identificadores ASCII `$name`, sin el `$` en JSON, y se
normalizan a minúsculas como parámetros DuckDB. Dos claves que difieren solo en
mayúsculas se rechazan para evitar valores contradictorios. `$1` y `?` no tienen
contrato de filtro y se rechazan. Las etiquetas y los valores pueden usar Unicode.

Se validan **todos** los valores enviados antes de descartar los que no pertenecen
al panel; esto permite mapas globales de filtros sin que sus campos extra evadan
presupuestos. Los campos de nivel superior del cuerpo sí se rechazan.

El tipado de transporte no inventa un tipo de negocio a partir del gráfico. El
tipo SQL final y las conversiones se resuelven en el catálogo aislado por DuckDB,
incluyendo `CAST` explícitos del autor. Su metadata de prepared statements
[devuelve UNKNOWN para los tipos de parámetros](https://duckdb.org/docs/current/sql/meta/duckdb_table_functions#duckdb_prepared_statements),
por lo que no se presenta como un esquema tipado inferido fiable. Declaraciones
persistidas de parámetros y validación por tipo de dataset siguen siendo E1/E3.

## Preparación desde el árbol SQL

La detección de placeholders usa SQL parseado. Un `$name` dentro de un literal,
comentario, identificador entre comillas o dollar string no crea un filtro ni un
binding. El motor de controles comparte esa detección con el plan de ejecución.

`IN ($regions)` con una lista se convierte a `IN $regions` mediante el nodo de
membership; no se modifica texto SQL con regex. Un literal `'IN ($regions)'`
conserva exactamente su contenido. Los valores se enlazan, nunca se concatenan.

Tras neutralizar «Todos», se recalculan los placeholders restantes. Un rango
con un extremo vacío elimina también el binding del otro extremo si desapareció
el predicado. Variables usadas en proyecciones o límites necesitan un valor
concreto: se conserva el sondeo/inferencia sin datos cuando aún no lo tienen.

## Presupuestos y errores

| Recurso | Predeterminado |
| --- | --- |
| Variables enviadas / nombre | 64 / 64 bytes |
| Texto por valor | 4096 bytes UTF-8 |
| Elementos por lista / total | 500 / 2048 |
| JSON de parámetros validado | 64 KiB |
| Cuerpo de ejecución y dominio de filtro | 128 KiB |
| Otros cuerpos de API y enlaces compartidos | 1 MiB |
| Nombre de columna de dominio | 1–128 caracteres |

`ParameterLimits` se configura por aplicación con `create_app(parameter_limits=...)`;
la preparación y QueryService comparten esa configuración. Los clientes no pueden
ampliarla. Los límites de transporte HTTP son independientes y permanecen activos.

El middleware ASGI limita bytes **antes de parsear JSON**. Comprueba también el
flujo real de chunks: un Content-Length ausente, falso o menor no evita la cuota.
Una desconexión no entrega un JSON parcial al router. Cuerpos excesivos retornan
413 / `body_limit`. No cubre cuotas del servidor/proxy ni protege todas las rutas
de frontend de un despliegue hostil.

Valores inválidos retornan 422 / `parameter_type` o `parameter_name`; límites de
valores retornan 413 / `parameter_limit`. Las respuestas identifican el campo y
la razón, sin repetir su valor. Los errores de validación HTTP omiten `input` y
`ctx`; los errores SQL con bindings también omiten valores y mensajes crudos del
motor. Error ordinario no equivale a resultado exitoso vacío.

## Responsabilidades

| Capa | Responsabilidad |
| --- | --- |
| `core.models.parameters` | Tipos, presupuestos, validación pura y significado de valores vacíos; sin Pydantic, SQL o HTTP |
| `inference.filters.parameters` | Detección de placeholders reales desde el parser existente |
| `api.services.parameters` | Plan de filtros, neutralización, adaptación de listas y bindings restantes; sin FastAPI |
| `api.services.queries` | Validación del contrato también en llamadas directas; ejecución aislada y presupuestos |
| `api.models`, dependencias y middleware | Cuerpos estrictos, servicio por aplicación y transporte acotado |
| Routers y `main.py` | Autorizar recursos y traducir errores a HTTP |

El siguiente adaptador de datasets justificará un contrato de proveedores. No
se añade una abstracción genérica vacía ni una migración del archivo en esta unidad.

## Calidad y build

- Se corrige `Expr`/`Expression` en el recorrido de padres del neutralizador;
  el chequeo global de tipos ya no requiere ignorar ese error.
- El selector de gráficos deriva ganador, opciones, scores y selección del
  resultado vigente. Permite feedback inmediato al seleccionar y adopta el
  siguiente resultado persistido; cambiar de panel no conserva sus scores viejos.
  Usa [derived writable de Svelte](https://svelte.dev/docs/svelte/$derived#Overriding-derived-values).
- Se retira autofocus del login y del desbloqueo de dashboard, preservando el
  orden de teclado sin mover el foco automáticamente.
- API/OpenAPI, `/meta` y versión de creación de proyectos nuevos usan
  `sqlviz_core.version`. Abrir un proyecto existente mantiene su metadata original;
  `SCHEMA_VERSION` es independiente y no cambia. La versión viene del paquete
  instalado: no se inventa una release nueva ni se cambia el tag del repositorio.
- CI usa Node **24.21.0** de `.node-version`, igual que la revisión local.
  Node 20 está fuera de soporte; ver [calendario oficial](https://nodejs.org/en/about/previous-releases).
  La matriz Python conserva 3.12 y agrega 3.13. `uv sync --locked` y `npm ci`
  impiden actualizar silenciosamente los lockfiles durante instalación de CI.

## Validación y continuación

Pruebas de core, planificación SQL, API con DuckDB real y middleware ASGI cubren
valores/tipos, case collisions, Unicode inválido, listas, presupuestos agregados,
no interpolación/no eco de valores, cuerpos chunked y compatibilidad de ejecución.
Se conservan los ocho controles de filtros y las selecciones «Todos», cero y false.
El selector de gráficos tiene pruebas de cambio de resultado y selección manual.

- Suite Python completa: **1652 pasan, 3 omitidas**, en **124,99 s**; incluye
  **93 casos nuevos** de parámetros, transporte, planificación y versión.
  Comando: `.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp build/parameter-review/pytest-final-03`.
- **74 tests frontend en 12 archivos**, incluidos dos casos nuevos del selector
  de gráficos. `npm run check`: **0 errores y 0 advertencias**. `npm run build`
  genera el SPA correctamente. Los tres comandos se ejecutaron secuencialmente.
- Ruff sobre todos los paquetes correcto. Mypy global correcto en **124 archivos**.
  `uv lock --check --offline` valida el lockfile sin modificarlo.
- Chromium con backend real y build nuevo: autor requiere login, dashboard y
  workspace públicos/con contraseña renderizan gráficos, credenciales por
  solicitud y revocación efectiva. **Sin errores de página**. Reporte en
  `build/parameter-review/browser-report.json`, ignorado por git. El ensayo usa
  proyecto/aprendizaje en memoria y su servidor se cerró; no se reinició la demo
  abierta del usuario ni se modificaron sus proyectos reales.

Las advertencias previas de `derived_inert` en fixtures de componentes y las de
bundles/sourcemaps de build requieren seguimiento; cero advertencias de
svelte-check no implica ausencia de todo diagnóstico de dependencias.
Validación local Windows/Python 3.13.14/Node 24.21.0. CI Linux/Python 3.12/3.13
queda configurado; no se afirma haberlo ejecutado remotamente. `--basetemp` es
una carpeta exclusiva de ensayo: pytest puede eliminarla al reutilizarla.

**Siguiente foco: E1, integridad y persistencia.** Comenzar con dashboard/panel y
operaciones atómicas antes de IDs estables y el contrato visual del Studio.
RLS, permisos de columnas, aislamiento de proceso, publicación/versiones,
adaptadores externos y límites del aprendizaje global siguen fuera de E0 local.
