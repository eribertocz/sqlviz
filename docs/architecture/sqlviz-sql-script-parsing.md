# S1.1a — Análisis de sentencias SQL

**Fecha:** 2026-10-08. **Alcance:** parsing del script, contador y foco del editor.
No entrega identidad estable, reconciliación transaccional o lienzo persistido.
Es la primera parte pequeña de S1 en el
[plan operativo](sqlviz-studio-delivery-plan.md).

## Problema y comportamiento

El editor dividía SQL con `split(';')` y contaba cada `;` para enfocar una consulta.
`SELECT 'a;b'; SELECT 2` se interpretaba como tres partes y podía crear o modificar
paneles antes de descubrir el error. Los comentarios producían paneles ficticios.

Ahora el backend analiza el script completo con el parser nativo de DuckDB antes
de que Run cree o modifique paneles. Strings escapados, identificadores entre
comillas, dollar-quoted strings y comentarios de línea, bloque y anidados
conservan sus límites reales. SQL vacío, comentarios solos y separadores vacíos
no generan paneles.

Se utiliza [extract_statements de DuckDB](https://duckdb.org/docs/stable/clients/python/reference/),
que analiza y extrae sentencias. No se invoca `execute`, no se enlazan tablas o
funciones, y no se necesitan fuentes existentes. Los fragmentos son slices del
texto original suministrado por DuckDB, con whitespace exterior retirado; no se
regeneran desde un AST. El draft completo conserva su texto original.

El parser puede admitir comandos sintácticamente válidos, pero analizarlos no
los ejecuta ni los autoriza. La política de consultas y permisos del runtime
sigue siendo la responsable de autorizar ejecución. Un parsing correcto no
garantiza que existan tablas/columnas o que el resultado sea un gráfico válido.

## Contrato y límites entre capas

- **Core:** `SqlStatement` inmutable, presupuesto de fuente y error de dominio;
  sin DuckDB, HTTP o almacenamiento.
- **Servicio de aplicación/adaptador:** `SqlScriptService` usa DuckDB y extrae
  fragmentos. Catálogo vacío propio por operación, cerrado también ante error;
  nunca recibe la conexión del proyecto. Dos operaciones simultáneas por app.
- **HTTP:** `POST /api/v1/sql/parse`, solo autor autenticado o demo. Request
  estricto `{sql: string}`; response `{version: 1, dialect: "duckdb", statements}`.
- **Web:** transporte, borrador y cache de una fuente confirmada. No hay un
  segundo lexer SQL en JavaScript. Monaco recibe posiciones de fuente.

Cada sentencia devuelve `sql`, `start_offset` y `end_offset`. Los offsets son
unidades UTF-16, el intervalo final es exclusivo y coincide con las posiciones
de JavaScript/Monaco. Caracteres como emoji no desplazan el cursor a otra consulta.
Estos offsets identifican posiciones de texto, **no IDs de panel**.

Límites: fuente de hasta 1 MiB UTF-8 y 256 sentencias, además del límite existente
de cuerpo HTTP de 1 MiB antes de JSON. Un body con escapes puede alcanzar ese
límite antes que el texto SQL. No se amplían los presupuestos de ejecución.
Concurrencia agotada devuelve 429; presupuesto excedido, 413; sintaxis o texto
inválidos, 422. El schema HTTP también puede devolver su 422 de validación.
Los diagnósticos propios no incluyen el SQL original ni una respuesta parcial.

Se rechazan Unicode inválido y NUL: el parser nativo puede ignorar contenido
después de NUL, algo incompatible con analizar el script completo. No se cargan
extensiones ni se habilita acceso externo en el catálogo de análisis. Los límites
de memoria/configuración no constituyen aislamiento duro de proceso.

## Contador, ejecución y foco

El contador se actualiza tras 300 ms sin cambios, usando el endpoint de análisis.
Hasta confirmar el SQL actual muestra estado de comprobación, no un número
calculado desde delimitadores. Un error permite reintentar con Run. Requests de
la misma fuente en curso se comparten; respuestas antiguas no pisan checks nuevos.
Solo se conserva una fuente confirmada, sin cache ilimitado de drafts.

Run captura texto y contexto antes del análisis. Si cambia la fuente durante
el preflight o se cambia de dashboard, no ejecuta ese snapshot obsoleto. Una
falla de parsing no crea/edita paneles ni reemplaza datos/layout confirmados.
El timestamp y `last_run_sql` corresponden al texto realmente ejecutado, aunque
el draft cambie después de empezar la ejecución.

El foco de edición solicita los offsets del mismo análisis y verifica el contexto
antes de mover Monaco. La asociación del panel a una sentencia sigue siendo
posicional: S1.1b debe reemplazarla. S1.1b.1 ya entrega un
[núcleo de decisiones explícitas](sqlviz-sql-identity-reconciliation.md) y S1.1b.2
[asociaciones del borrador](sqlviz-sql-draft-identity.md). Todavía no son preflight
de Run por ID. No se atribuye identidad estable a este cambio.

Al reconstruir texto desde paneles, el separador se coloca en una línea propia
(`\n;\n\n`), para que un comentario final `-- …` no lo absorba. Separadores
redundantes no crean sentencias. La reconstrucción no reemplaza el draft original
cuando este existe.

## Compatibilidad y límites pendientes

No cambia el formato `.sqlviz`, schema persistido, composición ni PATCH existentes.
El frontend necesita el backend que expone el nuevo endpoint. Si el servicio no
está disponible, Run muestra el fallo y conserva el estado confirmado; no vuelve
al splitter anterior como fallback.

La API de ejecución individual conserva su política y sus fallbacks existentes.
El Run del workspace ahora rechaza un script sintácticamente inválido antes de
mutar paneles. Un fallo posterior de ejecución o guardado todavía puede dejar
escrituras parciales: reconciliación, borrado y atomicidad del conjunto pertenecen
a S1.1b/S1.1c. No se declara S1 completa.

## Validación

- Casos de fuente: strings, comillas escapadas, identificadores, dollar quotes,
  CTE, comentarios anidados, CRLF, separadores vacíos y Unicode/UTF-16.
- Sintaxis inválida en una sentencia posterior rechaza todo el análisis; NUL,
  surrogates, presupuesto y concurrencia tienen respuestas predecibles.
- El análisis no usa proyecto ni ejecución; conexión cerrada en éxito/error;
  autor/anon/viewer y schema HTTP verificados.
- Web cubre deduplicación, respuesta tardía, retry, snapshot ejecutado, foco
  por offset y ausencia de escrituras ante fallo del preflight.

Evidencia local: suite Python completa, **2 263 aprobadas y 3 omitidas**; Ruff
global y mypy sin errores en 142 fuentes. Suite frontend: 179 aprobadas en 27
archivos; después se añadieron dos casos de recuperación y los 19 casos SQL
específicos pasan con ese estado final. Svelte-check: cero errores/advertencias;
build de producción aprobado.

Navegador real: siete recorridos aprobados sin errores de página. Contador antes
de ejecutar, dos paneles con fuente exacta, foco en la línea correcta con emoji,
script posterior inválido sin escrituras/ejecuciones, comentarios solos, recarga
y viewer compartido. Monaco usa CRLF en el entorno Windows de revisión; los
fragmentos y offsets conservan esa fuente. Proyecto y brain de prueba en memoria,
servidor de revisión detenido; artefactos en `build/sql-script-review/` ignorado.

CI ejecuta nuevamente la suite frontend completa, incluida esa ampliación, y
Python 3.12/3.13 al publicar el commit. La evidencia local no sustituye su
resultado. Pasar parsing no acredita inferencia avanzada o Studio.
