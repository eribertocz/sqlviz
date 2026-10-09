# Changelog

All notable changes to SQLviz are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Breaking

- Run del workspace analiza todo el script antes de crear/editar paneles y ahora
  rechaza sintaxis inválida sin escrituras de panel. Requiere el backend con
  `POST /api/v1/sql/parse`; no vuelve al splitter por delimitadores si falla.

- `PATCH /panels/{id}/override` para `chart_type` acepta únicamente los ocho
  identificadores soportados actualmente. Tipos desconocidos o con espacios/casing
  distinto ahora devuelven 422; `user_value: null` mantiene el retorno a automático.
- `PATCH /panels/{id}/view-override` exige `value` explícito: solicitudes que
  enviaban solo `field` ahora reciben 422. Para borrar, enviar `value: null` o
  `value: ""`. Texto de más de 512 caracteres, solo espacios o campos extra
  también se rechazan; los clientes deben corregir esas entradas.

### Added

- Dependencias web fijadas: GridStack 14.0.0, Drawflow 0.0.60 y tipos Drawflow
  0.0.12. Adaptadores internos con dieciséis pruebas sobre las bibliotecas reales:
  geometría por IDs/píxeles, colisiones sin empuje y mapa de lectura con inputs
  nombrados, etiquetas como texto y cancelación/desmontaje. Todavía no conecta
  drag/resize ni mapa al Studio, ni modifica proyectos `.sqlviz`.

- S1.1a: análisis nativo DuckDB de scripts, slices de fuente y offsets UTF-16;
  contrato HTTP estricto solo para autores, sin ejecución ni conexión de proyecto.
  Presupuestos de bytes/sentencias y admisión por aplicación.

- Núcleo interno de geometría manual del dashboard: doce columnas, posiciones y
  alturas exactas, operaciones inmutables, colisiones y evaluación de espacio
  pantalla/scroll con mínimos suministrados por el renderer. Incluye 54 casos;
  todavía no integra UI, persistencia ni endpoints del nuevo lienzo.

- El logo de navegación muestra el icono de abrir/cerrar al pasar el mouse o
  recibir foco de teclado; en táctil el icono permanece visible. Conserva un
  único botón, su tamaño y la preferencia de movimiento reducido; ambos iconos
  comparten el color índigo del logo.
- Contrato HTTP tipado de composición, adaptación explícita a dataclasses y
  esquema OpenAPI; conserva resultados originales y etiquetas de ejes.
- Cabecera compacta de Preview y viewers: selector del título, filtros bajo
  demanda y apariencia/acciones secundarias en opciones, sin búsqueda duplicada.
- Control de marca/navegación directo en la esquina superior izquierda de editor,
  Preview y workspace. El mismo botón abre/cierra sin moverse en escritorio;
  la biblioteca móvil enfoca búsqueda y devuelve foco al cerrar. Se retira
  navegación de opciones y la marca repetida del sidebar.
- Navegación simplificada a un solo logo/control visual (36 px en escritorio,
  44 px en móvil). El sidebar de escritorio ya no repite el botón de cierre;
  el modal móvil conserva su cierre interior y recuperación de foco.
- Panel de filtros con borrador, Aplicar/Cancelar, resumen confirmado y presets
  locales; runtime compartido que confirma el conjunto de paneles afectados,
  conserva datos ante fallos y descarta respuestas de una vista abandonada.
- Selector compacto en cabecera del viewer de workspace: búsqueda por
  dashboard/carpeta y Ctrl/Cmd+K sin abrir sidebar; la variante con flechas queda
  disponible en el componente para recorridos explícitos futuros.
- Contrato de dimensiones manuales en core (1–12 columnas y 120–900 px),
  validación estricta de PATCH y 49 casos nuevos Python más 9 frontend.
- Política de jerarquía en core, repositorio de carpetas y revisión interna
  transaccional del árbol, compartida con la ubicación de dashboards; 93 casos
  nuevos de política, repositorio, transacciones y API.
- Repositorio transaccional para borrado de dashboards y servicio de limpieza
  de sesiones después del commit; 25 casos nuevos de integridad y concurrencia.
- Contrato de parámetros en core y servicio de preparación por aplicación:
  valores simples/listas tipadas y acotadas, sin coerción del transporte.
- Límites de cuerpos API antes de JSON, incluyendo solicitudes chunked.
- QueryService por aplicación: catálogo analítico aislado, adaptación de tablas
  locales y límites de tiempo, filas, bytes, memoria y concurrencia.
- Servicio de autorización por aplicación, principal de autor/lector y sesiones
  administrativas y de lector separadas, con expiración y revocación.
- Credenciales con alcance en cada solicitud de ambos viewers; los enlaces con
  contraseña emiten una sesión temporal ligada a ese enlace y aplicación.
- Arranque Quack opcional mediante `--quack`, con credencial propia en
  `SQLVIZ_QUACK_TOKEN`, parámetros enlazados y extensión previamente instalada.
- Navegación de workspace totalmente ocultable: recupera los 260 px del
  explorador; acceso directo en la cabecera de editor, Preview y viewer.
- Panel modal de navegación hasta 900 px, con cierre por Escape/clic exterior,
  foco contenido y cierre al seleccionar un dashboard.
- Búsqueda local por dashboard/carpeta y acceso visible a búsqueda/comandos en
  la cabecera; preferencias privadas de visibilidad para editor y viewer.
- Acceso visible al modo de concentración: oculta también editor e inspectores,
  conserva sus estados y restaura el foco al salir.

### Changed

- Mínimos y bloques de texto especificados: 2 px se rechaza actualmente en
  gráficos, y títulos/subtítulos/encabezados/párrafos tendrán tipo, mínimo y
  persistencia propios, sin SQL. S1.3a–c añade su recorrido al plan; todavía sin UI.
  Se concreta la recomendación de columnas horizontales y píxeles verticales para
  el primer Studio; precisión horizontal libre deja de ser requisito S1.2a.

- Guías y precisión del lienzo especificadas: alineación, tamaños/separaciones,
  cotas durante el gesto, inspector exacto y magnetismo controlable. S1.2a debe
  concretar precisión horizontal compatible con doce columnas; S0 solo ofrece
  píxeles exactos en alto/Y. Desglose de guías/resize en S2, todavía sin UI entregada.

- Composición asimétrica aclarada como requisito S1/S2: un panel de seis columnas
  puede abarcar la altura de dos gráficos apilados en las otras seis. Cuatro casos
  core cubren ambas orientaciones y modos pantalla/scroll; la UI/persistencia siguen
  pendientes. No se confunde este caso con secciones/áreas semánticas de S6.

- Experiencia de paneles y áreas documentada: acabado de estructura/acciones/estados
  desde S1/S2, gestos del gráfico preservados y revisión visual obligatoria para
  cerrar ese flujo. CSS Grid se separa de áreas del producto; S6 se desglosa en
  medición, modos pantalla/scroll, grupos, plantillas y responsive. Diseño pendiente,
  sin cambios de UI ni formato `.sqlviz` en este incremento.

- Política de actualización de consultas compartidas documentada: conservar
  paneles y ajustes, diagnosticar impacto por consumidor, reparar y adoptar
  revisiones explícitamente; incluye variante de un panel, conflictos y resultados
  previos identificados. S3.4 se divide en persistencia, impacto y adopción atómica;
  todavía no implementa datasets compartidos ni estos controles.

- Mapa vivo del dashboard definido como vista bajo demanda de referencias reales,
  con contexto/edición mediante Studio, regreso al mapa y estados draft/confirmado.
  Distingue ajustes de instancia, visual compartida y dataset. F1–F3 entran en S3/S4;
  linaje detallado y publicación en S5/S8. Es diseño pendiente, no nueva UI.

- Autoría multiconsulta precisada: bloques SQL con identidad → datasets y esquema
  → preview/campos → varios visuales. S3.5 añade selector de consulta/dataset y
  promoción/reutilización; S4.2 explicita el builder contextual. Guardar definición
  no importa filas ni crea vistas físicas. Flujo documentado pendiente de entrega.

- Matriz analítica BI incorporada al alcance central, con módulo M1–M9:
  jerarquías, medidas/totales por contexto, renderer de grilla y drag de campos.
  Primer flujo en S3/S4, ampliación de formato/escala en S5 y lectura/publicación
  en S7/S8. S2 se divide en seis partes para drag/resize de paneles. Es diseño
  documentado pendiente; la tabla plana y los contratos legacy no cambian.

- Diseño de inferencia y cobertura visual ampliado: AST por ámbitos, linaje,
  evidencias/abstención, inputs SQL nombrados y adaptadores de forma; matriz de
  23 familias ECharts core y dependencias GL/custom. S3–S5 ahora tiene partes
  pequeñas con criterios de cierre. Es documentación de arquitectura pendiente,
  no nuevas familias soportadas; S1.1b sigue siendo el próximo incremento.

- Prioridad del Studio: geometría y lienzo persistido → drag/resize → dataset y
  visual → primer recorrido Automático/Visual Builder/ECharts nativo. Los tres
  niveles son parte del núcleo; el editor experto no se pospone al acabado.

- Documentación de la decisión aceptada para el Studio: inferencia automática,
  Visual Builder y ECharts native options; separación dataset/visual/panel y
  dataset mínimo antes de la autoría completa en los tres niveles. Define precedencia, persistencia y reset de
  ajustes expertos. Es diseño pendiente de implementación, no una función nueva.

### Fixed

- Run, contador y foco respetan `;` dentro de strings, identificadores, dollar
  quotes y comentarios. Comentarios/separadores vacíos no crean paneles;
  sintaxis inválida y NUL se rechazan antes de mutar paneles. El contador no
  publica resultados de otro draft y el foco usa posiciones confirmadas.
- Reconstrucción de SQL desde paneles separa consultas en líneas independientes
  para preservar comentarios `--` finales. `last_run_sql` conserva el snapshot
  ejecutado y respuestas tardías del preflight no cambian otro dashboard.

- Cambio manual de gráfico se guarda transaccionalmente antes del aprendizaje,
  con respuesta confirmada y conflictos de borrado/edición predecibles. La UI
  conserva el gráfico ante rechazo o fallo de refresh y ofrece reintento específico
  sin repetir aprendizaje. Reset borra el ajuste; reejecutar conserva el ganador
  automático separado del manual, incluso si ambos coinciden.
- El panel SQL respeta el alto disponible del workspace y mantiene visible su
  separador, incluso al restaurar una altura mayor o reducir la ventana.
  Arrastrar hacia abajo o usar el teclado reduce desde el tamaño visible,
  sin un recorrido muerto después de llegar al límite superior.
- El área de escritura SQL se ajusta al ampliar/reducir el panel y al cambiar
  el ancho disponible; Monaco observa su contenedor sin recrear el editor.
- Presentación de paneles valida título/etiquetas con valor obligatorio, hasta
  512 caracteres y sin coerción; null/vacío restaura automático. Guarda ajuste
  y fecha en una transacción, con rollback y coordinación frente a borrado.
- Inspector y etiquetas sobre el gráfico comparten guardado confirmado:
  conservan el texto al fallar y ofrecen reintento con errores legibles.
  Restablecer el título consulta la inferencia real con los filtros actuales;
  distingue guardado exitoso de un fallo posterior al actualizar el gráfico.
- La confirmación de una etiqueta conserva el editor que inició la solicitud;
  no cierra ni roba el foco de una edición posterior al cambiar rápidamente de eje.
- PATCH básico de paneles valida nombre, SQL y orden sin coerción; rechaza null
  y campos desconocidos antes de escribir, conserva ajustes visuales y SQL exacto,
  y guarda en una transacción. PATCH vacío no cambia fechas. Borrados de panel y
  dashboard protegen las filas frente a edición concurrente y revierten con 409.
- PATCH de dashboards rechaza tipos, campos y límites inválidos antes de guardar;
  distingue omisión/null y conserva SQL exacto. Actualización de campos, ubicación
  y timestamp es atómica, con rollback y conflictos 409; PATCH vacío no escribe.
- Foco del buscador de dashboards/comandos rodea el campo completo con la lupa,
  evitando el marco rectangular interior; conserva el espacio exterior.
- Items de búsqueda de dashboards y comandos resaltan en índigo suave al pasar
  el mouse o navegar con teclado; el fondo anterior coincidía con el diálogo.
- CI entrega el build verificado del frontend a los jobs Python antes de probar
  login y archivos estáticos, evitando depender de artefactos locales previos.
- `/compose` rechaza con 422 resultados incompletos, tipos/rangos incorrectos,
  números no finitos, versiones incompatibles, IDs repetidos y más de 256 paneles,
  antes de ejecutar el motor; conserva autorización y dimensiones manuales.
- Opciones de filtros conservan tipos simples, incluidos cero y falso; búsquedas
  Command tienen nombre accesible de raíz y la biblioteca recupera foco al control de cabecera.
- Filtros booleanos distinguen sin restricción, verdadero y falso mediante
  Any/Yes/No, evitando confundir falso con la ausencia de filtro.
- Dominios de filtros se solicitan secuencialmente y sin duplicar variables;
  abandonar la vista detiene la carga y descarta dominios tardíos, evitando
  ráfagas de consultas que agotaban los slots analíticos.
- Navegación del viewer descarta respuestas de dashboards abandonados y
  filtros pendientes; acceso revocado retira también el selector.
- Workspace compartido vacío muestra estado explícito; un solo dashboard
  conserva su título sin controles de cambio innecesarios.
- Overrides de tamaño rechazan rangos/tipos inválidos antes de escribir; null
  explícito restablece automático y conflictos de escritura devuelven 409.
- El editor conserva gráfico y dimensiones si falla el guardado; serializa
  cambios, usa valores confirmados y recompone sin ejecutar SQL para reset.
- Guardar dimensiones no depende del aprendizaje: patrón/evento se intentan
  después, en otra transacción. Ajustar alto conserva ancho aprendido y viceversa.
- Overrides históricos inválidos no se propagan al renderer ni al ancho KPI;
  sus valores no se reparan automáticamente en el archivo.
- La caché de resultados evita suscribirse a sus propias escrituras reactivas.
- Carpetas rechazan padres inexistentes y movimientos bajo sí mismas o sus
  descendientes. Cambios simultáneos del árbol/ubicación devuelven 409 sin ciclos
  ni referencias nuevas a carpetas eliminadas.
- PATCH distingue omisión de null para parent_id/folder_id; null mueve a raíz,
  compatible con el alias anterior "". El frontend envía null al desagrupar.
- Borrar una carpeta promueve sus contenidos directos en la misma transacción,
  preservando subárboles, dashboards, paneles y accesos compartidos.
- El contexto de transacciones conserva el conflicto de COMMIT cuando DuckDB
  ya abortó la transacción; otros fallos de rollback no se ocultan.
- Borrar un dashboard elimina también paneles, enlaces y memoria de filtros
  de forma atómica. Un fallo revierte el conjunto y conserva sesiones; otros
  dashboards y enlaces de workspace se mantienen.
- Crear paneles/enlaces de dashboard verifica y modifica el padre en la misma
  transacción; colisiones con borrado devuelven 409 sin crear huérfanos.
- El diálogo de borrado informa también de filtros guardados y enlaces afectados.
- Placeholders detectados desde SQL parseado: strings/comentarios no generan
  filtros. Multiselección adapta nodos IN sin modificar literales mediante regex.
- Valores inválidos/excesivos fallan explícitamente y errores de filtros no
  repiten valores enviados. El cuerpo de ejecución rechaza SQL/campos desconocidos.
- Selector de gráficos actualiza selección y scores al cambiar panel/resultado.
- Error de mypy de neutralización corregido; retiradas las seis advertencias
  Svelte previas, incluyendo autofocus en dos formularios.
- API/meta y metadata de creación usan la versión instalada común; CI usa
  Node 24.21.0, Python 3.12/3.13 e instalación con lockfile requerido.
- SQL de gráficos, dominios y sondeos ya no se ejecuta contra metadatos. Autor y
  lector solo ejecutan consultas de lectura; archivos/red, secretos, vistas y
  catálogos adjuntos no se exponen. No se migra el archivo del proyecto.
- Consultas que exceden presupuestos fallan explícitamente sin resultados
  parciales; timeout interrumpe DuckDB y libera recursos de la operación.
- CRUD y listados de autor requieren sesión; lectura, ejecución, dominios y
  composición verifican el alcance del enlace. Revocar o rotar el secreto impide
  nuevas solicitudes, también tras desbloquear un enlace protegido.
- Ejecutar como lector no persiste inferencias, clasificación ni aprendizaje;
  se rechazan sentencias de modificación y múltiples queries guardados.
- Los viewers retiran los resultados al recibir un rechazo de acceso; las
  respuestas de datos usan `no-store` y los cursores se cierran por solicitud.
- El CLI escucha por defecto en `127.0.0.1` en demo y proyectos persistentes;
  escuchar en LAN requiere `--host` explícito.
- Se elimina la instalación automática de Quack desde nightly y el token fijo.
  Si Quack se solicita y no puede arrancar, el CLI falla con un mensaje sin
  credenciales; los recursos se cierran también durante fallos de arranque.
- Los atajos globales respetan campos de texto y las combinaciones de Monaco.
- El cierre del explorador devuelve el foco al control de navegación; una
  restricción de localStorage no interrumpe la interfaz.
- Los dashboards con igual nombre conservan IDs distintos en la búsqueda de
  comandos. El título accesible del diálogo se ubica dentro de su contenido.
- El editor no crea una instancia huérfana si se cierra durante la carga de
  Monaco. Se desactiva el resaltado de coincidencias de palabras que dependía
  del worker provisional, evitando su rechazo `Canceled` al cerrar el editor.

### Documentation

- S1 dividido en S1.1a–c y S1.2a–e; contratos y límites del parsing documentados.
  Identidad/reconciliación es el siguiente incremento, antes del layout persistido.

- Plan operativo único del Studio con entregas S0–S8, criterios de cierre,
  reglas de libertad/legibilidad y análisis del informe de producto. Contrato
  del núcleo geométrico documentado; alineados README, índice, roadmap,
  especificación del Studio y decisión de autoría.

- Plan inmediato después de navegación: composición/PATCH, migraciones,
  identidad/configuración persistida, semántica y contexto de filtros,
  Studio pantalla/scroll, inferencia y publicación, con criterios de cierre.
- Especificación conjunta de navegación y filtros y primer incremento de lectura:
  cabecera compacta, edición bajo demanda y runtime confirmado. Prioridades,
  defaults publicados y semántica persistida completa siguen pendientes.
- Contratos de dimensiones, reset, aprendizaje opcional y límites de
  concurrencia documentados; BP-03 corregido y composición tipada como siguiente unidad.
- Política de jerarquía, PATCH y creación concurrente en proyectos anteriores;
  BP-02 y BP-05 de ubicación corregidos. Explorador anidado y otros PATCH pendientes.
- Política de integridad del dashboard, ownership de dependencias, protección
  concurrente y conservación del historial de aprendizaje; BP-01 corregido.
- Política de ejecución analítica, compatibilidad y límites reales de aislamiento
  y presupuestos. Pendientes: datasets externos, cuotas de SO y declaraciones
  persistidas de tipos de parámetros. Contrato de transporte implementado.
- Política de autorización, transporte de credenciales y límites del incremento.
- Política de arranque local, ownership de conexiones y pruebas del primer
  incremento de E0, complementada por autorización y ejecución analítica.
- Documento de navegación con decisiones, responsabilidades, pruebas y límites.
- Especificación del Dashboard Studio: libertad visual equilibrada, pantalla sin
  scroll/scroll, sidebar totalmente ocultable y criterios de calidad de inferencia.
  Ensayos adicionales detectan asignación de ejes por posición y omisión de
  métricas; se registra el límite del benchmark actual de 52 casos. Navegación
  implementada; contratos visuales, modos de página e inferencia pendientes.
- Evaluación adicional de buenas prácticas de arquitectura, con cinco problemas
  reproducidos de integridad/contratos, dirección de dependencias y criterios de
  refactorización incorporados a E1. BP-01/02 y BP-05 de ubicación corregidos;
  BP-03/04 y PATCH de otros campos pendientes.
- Auditoría técnica y de producto del 2026-10-05 con evidencia de autorización
  incompleta, baseline de pruebas y prioridades de corrección. Los hallazgos de
  seguridad originales tienen seguimiento en la auditoría; el aislamiento
  analítico HTTP se implementa en la tercera unidad; E0 permanece abierto.
- Nueva dirección de autoría SQL y visual, arquitectura objetivo y plan de
  entregas con criterios de aceptación; documentos anteriores señalados como
  históricos cuando su alcance o prioridad cambió.
- README corregido: Python 3.12+, fábrica de aplicación, CLI en puerto 4000,
  instalación del workspace y limitaciones de seguridad actuales.

---

## [v0.2.11] — 2026-07-25

Objetivo: compartir dashboards en la red local de forma confiable, motor de
charts profesional y controles de filtro consistentes.

### Added
- **Motor de charts profesional** con paletas a nivel dashboard, y nuevas
  paletas seleccionables desde el Panel Properties.
- **Títulos de panel y de ejes editables**, persistidos y visibles también en
  los dashboards compartidos.
- **Selector de paleta en los viewers**: cada visitante elige su paleta, que se
  guarda por dashboard en su navegador.
- **Compartir con alcance**: `dashboard` (uno solo) o `workspace` (todos, con
  navegación), cada uno con su viewer.
- **Modo privado** = preview solo para el admin, links listos para LAN y
  generador de contraseñas fuertes (16 caracteres, sin caracteres ambiguos),
  con botón para copiarla.
- **El CLI escucha en `0.0.0.0`** por defecto, para que `sqlviz` a secas alcance
  para compartir en la red local.
- **Command palette**, sidebar tipo rail, focus mode y editor drawer.
- **Vistas de filtro guardadas** (combinaciones con nombre, en localStorage por
  dashboard), disponibles también en el viewer.
- **El dropdown de filtros ahora es un combobox con búsqueda**, igual que el
  multiselect: dominios de docenas de valores se buscan en vez de scrollearse.
- **Identidad visual**: logo oficial de SQLviz, Geist Sans para el wordmark y
  color de marca indigo `#5B5BD6`.
- `$lib/clipboard.ts`: helper de copiado con fallback para contexto inseguro.
- Polyfills de jsdom para Pointer Capture y `PointerEvent` en `vitest-setup.ts`,
  sin los cuales ningún test podía abrir un menú de bits-ui.

### Changed
- **Viewer rediseñado**: sidebar colapsable, filtros flotantes y la misma barra
  de filtros que el modo edición.
- Share pasa a botón icon-only, Preview/Edit a control segmentado y los filtros
  a pills.
- Scrollbars finas y sensibles al tema.

### Fixed
- **Copiar el link de share copiaba otra cosa**: sin contexto seguro se caía a
  `execCommand`, que seleccionaba un `<textarea>` colgado de `<body>` — fuera
  del focus trap del diálogo de bits-ui, que le robaba el foco antes de copiar.
  La selección ahora ocurre siempre dentro del diálogo.
- **Las vistas de filtro no se podían guardar desde la red local**:
  `crypto.randomUUID()` solo existe en contexto seguro, así que tiraba
  `TypeError` en `http://<LAN-IP>`. Ahora el id sale de `crypto.getRandomValues`.
- **El dropdown con muchas opciones se salía de la pantalla sin scroll**: tenía
  `overflow-y-auto` pero nada que acotara su altura, y una caja libre de crecer
  nunca produce scrollbar.
- El viewer no cargaba: se separó la navegación del fetch de datos, se sirve la
  SPA para `/view/<token>` y se dejó de devolver HTML cacheado a su fetch JSON.
- Los dominios de filtro no se cargaban en el viewer, así que los dropdowns se
  renderizaban como cajas de texto.
- Las posiciones de los paneles se mantienen estables al cambiar un filtro.
- Windows: se usa el event loop Selector para evitar el ruido de resets del
  Proactor.
- El título del eje Y se renderiza vertical (rotado 90°), también en edición.
- Propiedades de panel obsoletas al cambiar de panel.

---

## [v0.2.10] — 2026-07-21

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Creación inline estilo VSCode** en el sidebar: nombrar carpetas y
  dashboards directamente en el árbol, sin modal (Enter confirma, Escape
  cancela, nombre vacío muestra un aviso inline).
- **Selección explícita de carpeta/raíz** como destino de creación, visualmente
  distinta del dashboard activo (línea fina a la izquierda vs. resaltado).
- **Caché de resultados en memoria** por dashboard (charts, layout, dominios y
  selección de filtros): navegar entre dashboards restaura la vista al instante
  en vez de mostrar el editor vacío. Se invalida en cuanto el SQL borrador
  diverge de la query que produjo esos resultados.

### Changed
- El estado de los filtros paramétricos migró a runes de Svelte 5: el cambio de
  un filtro pasó a ser una escritura de estado pura, con un `$effect` que
  debouncea (350 ms) y re-ejecuta solo los paneles afectados.
- El botón "Run Again" se eliminó y "Last run X ago" quedó como línea
  informativa.
- El botón de limpiar del dropdown reemplaza a la opción "All".

### Fixed
- Limpiar un filtro no re-ejecutaba la query: la ejecución abortaba si alguna
  variable estaba vacía, así que el chart seguía mostrando los datos filtrados.
  Un valor vacío significa "All" y el API neutraliza ese predicado.
- La paleta elegida no se aplicaba a line/bar/scatter/histogram: solo el pie
  usaba la paleta, el resto tenía el color de serie hardcodeado.
- Cursor DuckDB por request, para que los resultados no se pisen entre threads.
- Migraciones idempotentes: se acabó el traceback al reabrir un proyecto.

---

## [v0.2.9] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Panel de Propiedades del panel** (`PanelPropertiesPanel.svelte`): panel
  lateral derecho que se abre al hacer clic en cualquier panel en modo edición y
  centraliza toda su configuración — tipo de chart (el Chart Selector ahora
  embebido), título editable, ejes X/Y, colores, dimensiones (ancho en columnas
  y alto en px, con reset a automático), SQL editable con Apply que re-ejecuta
  solo ese panel, e inferencia (intent/chart/calidad + explicación del motor).
  Reemplaza el modal flotante del Chart Selector y el popover de layout.
- **Roadmap completo** (`sqlviz-roadmap.md`): V0.2.x → V1.0 con convención de
  versiones, y **DOC11**, el plan de construcción del Filter Engine de V0.4.0
  (20 motores). Solo documentación.

---

## [v0.2.8] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Auto-guardado del borrador**: el texto exacto del editor se persiste solo,
  2 s después de dejar de tipear, al cambiar de dashboard, al perder foco la
  ventana y al cerrar la pestaña (PATCH con `keepalive`). El usuario nunca
  piensa en guardar.
- **Indicadores de estado en el header**, discretos y nunca modales:
  ● Draft · Saving… · Saved (se desvanece) · Running · Error.
- **Restore al refrescar**: reabre el último dashboard activo, restaura el
  borrador exacto y, en vez de re-ejecutar, muestra "Last run X min ago".
- **Botón "Restore last run"**: revierte el borrador al SQL de la última
  ejecución exitosa, que ahora se persiste aparte en `dashboards.last_run_sql`
  (migración 0018). Solo aparece mientras borrador y última ejecución difieren.
- **Sidebar de dashboards colapsable y dual-mode**, con drag-and-drop, borrado
  de grupos y edición inline.

---

## [v0.2.7] — 2026-07-18

> Entrada reconstruida el 2026-07-25 a partir del historial: esta release se
> tagueó sin registrarse en el changelog.

### Added
- **Dashboard Explorer**: sidebar de navegación entre dashboards.

---

## [v0.2.6] — 2026-07-18

Objetivo: filtros paramétricos completos y controles de UI profesionales
(ver `docs/architecture/sqlviz-roadmap-v02x.md`).

### Added
- **Los 8 tipos de filtro paramétrico** funcionando end-to-end en la FilterBar:
  `dropdown`, `multiselect`, `date_picker`, `date_range_picker`, `numeric`,
  `range_slider`, `search`, `toggle`.
- **Controles ricos por dominio de columna**: nuevo endpoint
  `POST /api/v1/panels/{id}/filter-domain` (body `{column, kind}`) que devuelve
  los valores distintos (dropdown/multiselect) o el `MIN`/`MAX` (slider) de la
  columna. El dominio se calcula reescribiendo el SQL del panel con sqlglot
  (se quita el `WHERE` paramétrico y se proyecta la columna), en
  `sqlviz_inference.filters.domain.build_domain_query`.
- **Migración a shadcn-svelte** de todos los controles de filtro: Select,
  Combobox (Popover + Command), Calendar/RangeCalendar, Slider, Switch, Input.
  Nuevas dependencias: `bits-ui`, `clsx`, `tailwind-merge`, `tailwind-variants`,
  `@internationalized/date`, `@lucide/svelte`, `tw-animate-css`.
- **Tema dark/light**: los tokens de shadcn (`--background`, `--primary`,
  `--border`, `--ring`, `--radius`, …) se aliasean sobre los design tokens de
  DOC6 (`--sqlviz-*`) mediante una capa `@theme inline` en `app.css`; la
  variante `dark:` se remapea al esquema dark-por-defecto de SQLviz. Una sola
  definición maneja ambos temas.
- Tests: builder de dominio (inference), endpoint `filter-domain` (API),
  cobertura end-to-end de los 8 tipos, y tests de componente de FilterControl.

### Changed
- `FilterEngine._find_associated_column`: reconoce `col IN ($var)` (multiselect)
  y `col BETWEEN $a AND $b` (rangos de fecha/numéricos) — antes ninguno producía
  un `filter_control`.
- Dedup de `$variables` con `dict.fromkeys()` en vez de `set()`: preserva el
  orden de aparición para que el par de un rango (`desde`/`hasta`, `min`/`max`)
  no se invierta según el hash-seed del proceso.
- `execute_panel`: en el flujo sin valores prueba la query con cada `$variable`
  ligada a `NULL` para recuperar el schema real de columnas antes de correr
  `FilterEngine` (numéricos/fechas ya no caen a texto plano).

### Fixed
- `col IN ($var)` con valor de tipo lista fallaba en DuckDB (`Conversion Error`);
  `execute_panel` reescribe a `IN $var` cuando el valor ligado es una lista.
- Switch (toggle): track/thumb invisibles — las clases usaban `data-checked:` /
  `data-unchecked:` pero bits-ui 2.18 emite `data-state="checked|unchecked"`.
  Reapuntadas a `data-[state=…]`.
- Slider de rango: la barra y el rango resaltado no se veían — usaban
  `data-horizontal:` / `data-vertical:` pero bits-ui emite
  `data-orientation="…"`. Reapuntadas a `data-[orientation=…]`.
- Popover/Select/Dialog: animaciones de apertura/cierre no disparaban
  (`data-open:` / `data-closed:` → `data-[state=open]:` / `data-[state=closed]:`)
  y `tw-animate-css` no estaba cableado.

---

## [v0.2.5] — 2026-07-18

### Added
- **`sqlviz_api.routers.api.ts`**: cliente HTTP centralizado en el frontend
  para las llamadas a `/api/v1/*`, reemplazando `fetch()` dispersos por la app.
- **Stores dedicados** (`dashboardStore.svelte.ts`, `executionStore.svelte.ts`,
  `uiStore.svelte.ts`): extraen el estado y la lógica de orquestación que vivía
  en `+page.svelte` (bootstrap de dashboard, ejecución de paneles, filtros,
  overrides de layout, estado de UI) a stores de Svelte 5 (`$state`) testeables
  de forma aislada.
- **Componentes nuevos**: `AppBar.svelte`, `DashboardArea.svelte`,
  `EditorSection.svelte`, `ToastHost.svelte`, `VerticalResizer.svelte`
  (panel de editor SQL redimensionable), y `explain/*`
  (`ChartSection`, `DiagnosticsSection`, `IntentSection`, `QualitySection`,
  `ScoreBars`, `explainMeta.ts`) extraídos de `ExplainPanel.svelte`.
  `shared/ExecutionStateBadge.svelte` y `shared/StateMessage.svelte` para
  estados de carga/error reutilizados entre componentes.
- **Infraestructura de testing frontend**: `vitest-setup.ts` + primeros tests
  (`routes/page.test.ts`, `routes/login/page.test.ts`,
  `routes/view/[token]/page.test.ts`).
- **CI**: nuevo job `frontend` en `.github/workflows/ci.yml`
  (`svelte-check` + `vitest` + `vite build`), corriendo junto al job de
  backend existente.
- **Filtros paramétricos**: soporte para `col IN ($var)` (multiselect) y
  `col BETWEEN $a AND $b` (date_range_picker / range_slider) en
  `FilterEngine._find_associated_column` — antes ninguno de los dos producía
  un `filter_control`, así que la FilterBar no mostraba ningún control para
  esos patrones de SQL.

### Changed
- `+page.svelte` reducido de ~985 a un fragmento delgado que compone los
  nuevos componentes/stores; `ExplainPanel.svelte` reducido de forma análoga
  al extraer sus secciones a `explain/*`.
- `execute_panel` (`panels.py`): en el flujo sin valores (fallback), la
  query ahora se prueba con cada `$variable` ligada a `NULL` para recuperar
  el schema real de columnas antes de correr `FilterEngine` — sin esto,
  columnas numéricas/fecha se mostraban como controles de texto plano en
  vez de `numeric`/`date_picker`.
- El dedup de `$variables` en `FilterEngine` pasó de `set()` a
  `dict.fromkeys()`: preserva el orden de aparición en el SQL, evitando que
  el hash-seed del proceso invirtiera aleatoriamente qué caja de un rango
  (`desde`/`hasta`, `min`/`max`) queda ligada a cada variable.

### Fixed
- `col IN ($var)` con un valor de tipo lista fallaba en DuckDB con
  `Conversion Error` (los paréntesis hacen que DuckDB trate el parámetro
  como escalar, no como array). `execute_panel` ahora reescribe a
  `IN $var` cuando el valor ligado es una lista.

---

## [v0.2.4] — 2026-07-16

### Added
- **Versioning de contratos**: `InferenceResult` expone `result_schema_version`
  (constante `INFERENCE_RESULT_SCHEMA_VERSION = "1"`). `VisualSpec` expone
  `schema_version` (constante `VISUAL_SPEC_SCHEMA_VERSION = "1"`). El schema
  `.sqlviz` expone `schema_version = "1"` en la tabla `_sqlviz_meta`. Los
  consumidores pueden detectar cambios breaking comparando estas versiones.
- **`APP_VERSION` y `SCHEMA_VERSION`** exportadas públicamente desde
  `sqlviz_storage.project_db` para que los tests y la API puedan referenciarlas
  sin hardcodear strings.
- **Golden tests de serialización** (`test_serialization_golden.py`): freezan
  el conjunto de campos de `InferenceResult` y `VisualSpec`. Fallan cuando
  cualquier campo es agregado, eliminado o renombrado, forzando actualización
  intencional del fixture en `tests/golden/`.
- **Política formal de contratos** (`docs/architecture/sqlviz-contract-policy.md`):
  define `backward-compatible` / `breaking` / `deprecated`, lista los contratos
  versionados, y documenta el proceso para cambios breaking.
- **Migración 0015** (`meta_set_schema_version`): backfill de `schema_version`
  en proyectos `.sqlviz` creados antes de v0.2.4.

### Changed
- `_APP_VERSION` en `project_db.py` actualizado de `"0.1.0"` a `"0.2.4"`.
- Directorio `packages/sqlviz-inference/rules/` eliminado. Era una copia stale
  de `src/sqlviz_inference/rules/` (el `YAMLLoader` ya cargaba desde `src/`).
  La fuente de verdad única es `src/sqlviz_inference/rules/`.

### Fixed
- `sqlviz_logging.py`: anotación `dict` sin argumentos de tipo → `dict[str, object]`.
- `server.py`: comentario `# type: ignore[import-not-found]` redundante eliminado
  (mypy con `--ignore-missing-imports` suprime el error nativamente).
- `result.py`: comentario `# type: ignore[arg-type]` redundante eliminado.

Suite de tests: **1325 passed, 3 skipped** (antes: 1319).

---

## [v0.2.3] — 2026-07-16

### Added
- **Structured JSON logging** (`sqlviz_logging.py`): cada módulo del pipeline
  emite líneas JSON con `ts`, `level`, `logger`, `msg` y campos opcionales
  (`trace_id`, `elapsed_ms`, `execution_state`, `error_count`). Nivel
  configurable vía variable de entorno `SQLVIZ_LOG_LEVEL` (default: `WARNING`).
- **`trace_id`** por ejecución: identificador hex de 8 caracteres generado en
  `RuntimeContext`, propagado a través de todo el pipeline y expuesto en
  `InferenceResult`. Permite correlacionar logs de una misma inferencia.
- **`execution_state`** en `InferenceResult`: `"success"` / `"warning"` /
  `"degraded"` / `"failed"`, calculado por `pipeline.py` a partir de
  `context.errors` y `context.fallback_applied`.
- **Timings por módulo** (`module_timings`): cuando se pasa `?debug=1` al
  endpoint de ejecución, `InferenceResult` incluye un dict con el tiempo en ms
  de cada uno de los 21 pasos del pipeline.
- **Panel de Diagnósticos en ExplainPanel**: muestra estado de ejecución con
  badge de color, trace ID, tiempo total, fingerprint, versión del motor y
  grilla de timings por módulo (visible solo en modo debug).
- **14 nuevos tests** de observabilidad (`test_observability.py`) — suite total:
  1319 passed, 3 skipped.

### Fixed
- Todos los bloques `except Exception: pass` (17 módulos de inferencia)
  reemplazados por `_log.warning(...)` con `trace_id` en `extra`. Los errores
  silenciosos ahora son observables sin cambiar el comportamiento del pipeline.

---

## [v0.2.2] — 2026-07-15

### Fixed
- **FeedbackEngine** ya no reemplaza silenciosamente la inferencia original.
  `run_apply` es ahora un no-op; la preferencia aprendida se expone en
  `feedback_preferred_chart` pero nunca se aplica automáticamente.
- **Chart Selector orden fijo**: la lista de alternativas ya no se reordena al
  seleccionar un ítem. `engineWinner` (antes del override) ancla el orden; solo
  cambia el radio button seleccionado.
- **Item duplicado**: `ScoringModel._update_winner()` podía mover el winner a
  una posición que ya estaba en `chart_alternatives`. Corregido filtrando
  `a.chart !== engineWinner` en la construcción de la lista.
- **Item seleccionado se movía al primer lugar**: causa raíz era `Math.random()`
  como row key en `DashboardGrid`, que provocaba remount del panel y reset del
  estado local. Corregido exponiendo `chart_engine_winner` en `InferenceResult`
  e inicializando `_override` desde `result.chart_winner !== engineWinner`.
- **Chart Selector recortado por el contenedor del panel**: convertido a modal
  flotante con `position: fixed` via acción Svelte `portal` que monta el nodo
  directamente en `document.body`, escapando cualquier `overflow: hidden`.

### Added
- **Preferencia ★ en Chart Selector**: cuando `feedback_preferred_chart` coincide
  con un ítem de la lista, se muestra una estrella dorada (★) junto al nombre.
  La preferencia es una sugerencia visual, nunca se aplica automáticamente.
- **Chart Selector muestra los 8 tipos siempre**, organizados en dos grupos:
  - **Recomendados** (score ≥ 50 %): charts que el motor considera adecuados.
  - **Disponibles** (score < 50 %): el resto, accesibles pero no recomendados.
  `ScoringModel` ahora expone `total_score` en `ChartCandidateV2`; el pipeline
  reconstruye `chart_alternatives` con los 8 tipos y un campo `pct` normalizado
  (winner = 1.0) después del scoring.

---

## [v0.2.1] — 2026-07-14

### Changed
- All packages unified at version `0.2.1`

### Fixed
- 38 ruff errors (import sorting, unused imports, line length) across test files
- New Dashboard button now clears previous query on navigation
- New Dashboard state no longer carries SQL from prior dashboard

### Added
- `GET /api/v1/meta` endpoint — returns version, build hash, feature flags
- `README.md` with installation and usage instructions
- `CHANGELOG.md` (this file)

---

## [v0.2.0] — 2026-07-13

### Added — Cognitive Dashboard Compiler (DOC6 §12)

**Inference pipeline (V0.2):**
- `DataProfile` + `VisualSpec` contracts (Fase 0)
- 11 typed contracts in `sqlviz_inference.contracts` (Fase A)
- `ColumnRoleDetector` + `ConstraintEngine` with 6 hard rules (Fase B)
- `ReadabilityModel` + `ScoringModel` (Fase C)
- `LayoutDeclarationBuilder` + `DashboardRoleClassifier` + `DashboardLayoutOptimizer`
  + `DashboardObjective` + `InformationGainEngine` (Fase D)
- `OverrideSystem` + `FeedbackEngine` — learned chart preferences (Fase E)
- `ExplanationEngine` V2 (Fase F)
- Benchmark suite: 52/52 gold (100%), 48/52 adversarial (92.3%) (Fase G)

**API:**
- `PATCH /api/v1/panels/{id}/override` — apply user chart/layout override
- `PanelOverrideRequest` model

**Storage:**
- `brain_db.py` — feedback patterns, layout patterns, feedback events
- `override_system.py` — `store_inference()` + `apply_override()`
- Migrations 0002–0014 (fingerprint, override columns, dashboard classification)
- `dashboard_hint` + `dashboard_domain` on dashboards table
- `inferred_intent_type` on panels table

**Frontend:**
- `ChartSelectorPanel.svelte` — chart alternatives with scores, "Reset to auto"
- `DashboardSidebar.svelte` — dashboard-level navigation with inferred icons
- `LayoutOverrideControls.svelte` — column span + height overrides
- `DashboardScorePanel.svelte` — utility score + breakdown + suggestions
- `DashboardGrid.svelte` — panel IDs, override props
- `PanelRenderer.svelte` — 150ms fade-out / 200ms fade-in animation on chart change
- `dashboardIcons.ts` — `resolveDashboardIcon()` with 4-level fallback
- Dashboard management UI: create dashboard, navigate between dashboards,
  active dashboard name in app bar
- `lucide-svelte@1.0.1` installed

---

## [v0.1.0] — 2026-06-01 (approx.)

### Added — V0.1 Foundation

- Core inference pipeline: intent detection → chart selection
- DuckDB-backed storage for dashboards, panels, SQL content
- FastAPI REST API: dashboards + panels CRUD, panel execution
- SvelteKit frontend: SQL editor, panel grid, ECharts rendering
- `sqlviz-cli` package
- 523 passing tests across all packages
