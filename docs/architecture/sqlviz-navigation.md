# Navegación del workspace

Actualizada: **2026-10-08**. Estado: implementada en el editor, Preview y viewer de
workspace; validación descrita abajo. Esta entrega no cierra E2 ni implementa
los modos de página pantalla/scroll.

La [especificación conjunta de navegación y filtros](sqlviz-navigation-and-filters-spec.md)
define la evolución completa. Su [primer incremento de lectura](sqlviz-reader-context.md)
entrega cabecera compacta, filtros bajo demanda y contexto confirmado por el
runtime; configuración publicada y otras capacidades de la especificación siguen pendientes.

## Decisión de experiencia

SQLviz combina tres accesos que se complementan:

- **Cabecera:** en el editor, navegación y comandos de autoría; en lectura,
  control de marca/navegación, selector del título, filtros y menú de opciones.
- **Búsqueda y comandos:** Ctrl/Cmd+K para saltar a un dashboard o ejecutar una
  acción en el editor. Los resultados usan IDs únicos y se buscan por nombre o
  carpeta. Preview y el viewer de workspace buscan desde el selector de título sin abrir
  el explorador; conserva también la búsqueda opcional del sidebar.
- **Explorador:** organiza carpetas y dashboards en edición; en Preview y en el
  viewer ofrece navegación. Su búsqueda local filtra por nombre o carpeta.

Ocultar la navegación deja **0 px** ocupados: el panel y sus controles se
retiran del DOM. No queda una columna de iconos ni una zona invisible que el
usuario deba descubrir. En escritorio, abrirla reserva 260 px. Hasta 900 px
de ancho, se abre como diálogo modal sobre el contenido; seleccionar un
dashboard cierra ese diálogo. En escritorio permanece abierto si el usuario
prefiere explorar con una lista visible; el editor permite también organizar.

## Navegación cotidiana del viewer

**Cabecera compacta — 2026-10-07:** Preview y el viewer de workspace usan el
nombre actual con flecha desplegable como selector principal. Al abrirlo, el
lector busca un destino por nombre/carpeta y lo selecciona sin abrir el sidebar.
No hay búsqueda duplicada ni flechas anterior/siguiente en esta cabecera.
El componente conserva una variante con flechas para recorridos explícitos,
pero las páginas de lectura usan `compact`.

El desplegable aparece sobre el contenido y se cierra al elegir, con Escape o
clic exterior. Ctrl/Cmd+K y el título abren el mismo selector.
Elegir o pulsar Escape devuelve el foco al título. Las carpetas ayudan a
distinguir nombres duplicados y los destinos se seleccionan por ID. El mismo
acceso funciona en escritorio y móvil, sin un contador fijo de dashboards.

Los destinos siguen `sort_order`, conservando el orden recibido para empates;
no representan historial del navegador. Durante la carga se puede seguir buscando; la selección de otro
destino se deshabilitan hasta finalizar. Si se cambia desde
el explorador mientras una consulta anterior sigue en curso, su respuesta
tardía no reemplaza el dashboard actual. Se descartan también filtros pendientes
al navegar y resultados de filtros de una vista abandonada. Esto no cancela
trabajo ya iniciado en el servidor ni añade caché persistente.

El sidebar tiene un acceso directo en la esquina superior izquierda: un único
botón muestra el logo en reposo y, al pasar el mouse o recibir foco visible por
teclado, lo sustituye por el icono de abrir/cerrar según `aria-expanded`.
En dispositivos sin hover o con puntero táctil, el icono funcional permanece
visible. Las dos representaciones se superponen dentro del mismo botón, con
una transición breve de opacidad y sin animación si se solicita movimiento reducido.
Su nombre accesible Mostrar/Ocultar siempre describe la acción disponible.
Ambos iconos usan siempre `--sqlviz-primary`, el mismo índigo del logo, tanto
en reposo como con hover/foco y en ambos estados de navegación.
Los items de búsqueda y comandos comparten el resaltado `bg-accent` cuando
Bits UI selecciona una opción por mouse o teclado; `bg-muted` coincidía con el
fondo del diálogo. El componente compartido conserva los items deshabilitados
sin interacción y no añade un estado de hover separado de la selección de teclado.
El buscador conserva 8 px de espacio exterior (4 px de la raíz y 4 px del
wrapper). El foco se dibuja sobre el grupo redondeado que contiene lupa y texto,
sin marco adicional en el input interior; este se ajusta al alto del grupo.
Ese botón mantiene la posición en escritorio y sirve para
abrir/cerrar. La cabecera del workspace se encuentra por encima de sidebar y
canvas; abrir el panel no desplaza el control hacia la derecha. El botón mide
36 × 36 px en escritorio y 44 × 44 px en móvil. En el sidebar se muestra
«Dashboards», sin repetir marca ni cierre en escritorio; el cierre interno
aparece solo en el diálogo móvil. `View options` conserva solo
acciones secundarias y apariencia.

En móvil, la biblioteca enfoca su búsqueda al abrirse, tiene cierre visible dentro
del modal y restaura foco al control de cabecera al cerrarse. Su apertura no altera
el alcance del enlace ni la búsqueda del título. Abrir el selector no altera su
preferencia. Con un solo dashboard no
se ofrecen flechas ni selector innecesarios; un workspace vacío muestra un
estado explícito. Un enlace de dashboard individual mantiene su alcance y no
adquiere navegación a todo el workspace. El selector solo recibe la lista que
el backend entrega al enlace de workspace; cada consulta conserva autorización.

`ViewerDashboardSwitcher.svelte` recibe destinos, selección, carga y callback.
No importa stores ni llama a la API. La página adapta el DTO compartido y posee
la carga y su generación; `Popover`/`Command` existentes proporcionan el overlay
y la búsqueda. El patrón de teclado se apoya en
[WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/); las pruebas no
constituyen una certificación completa de accesibilidad.

La siguiente evolución puede incorporar favoritos privados si los workspaces
grandes muestran esa necesidad en uso real. Pestañas persistentes para todos
los dashboards añadirían competencia con filtros y títulos largos; requieren
un contrato de prioridad/overflow antes de introducirlas. No se ha implementado
esa evolución ni navegación mediante historial/URLs de dashboard en esta unidad.

## Modo de concentración del editor

El modo de concentración del editor oculta cabecera, explorador, editor SQL e
inspectores. Tiene salida visible y admite Escape. Conserva la preferencia de
navegación y la visibilidad del editor para recuperarlas al salir. No solicita
fullscreen al navegador ni ajusta automáticamente las filas a la altura de la
pantalla: esas capacidades tienen contratos separados en el Studio.

Los patrones de referencia son la jerarquía y visibilidad de controles de
[Apple](https://developer.apple.com/design/human-interface-guidelines/sidebars)
y la separación entre navegación y área de trabajo de
[Figma](https://help.figma.com/hc/en-us/articles/360039831974-Explore-the-navigation-bar-and-left-sidebar).
La identidad, dimensiones y comportamiento anteriores son decisiones de
SQLviz; no se afirma que reproduzcan exactamente esas aplicaciones.

## Tamaño del editor SQL

El separador modifica la altura del panel mediante `uiStore`; el layout CSS
distribuye ese espacio entre barra de acciones y área de escritura. Monaco usa
`automaticLayout` para observar su contenedor, tanto en altura como en ancho.
La adaptación pertenece a `SQLEditor`, sin suscripciones del shell ni recreación
del editor durante un arrastre. Monaco libera su observador al disponer la instancia.

La altura solicitada es una preferencia privada de navegador, entre 120 y
700 px. El shell limita la altura efectiva al espacio de trabajo mediante
`max-height: 100%`; una ventana menor puede mostrar menos que la preferencia
sin sobrescribirla. Cada ajuste parte de la altura renderizada y se limita al
espacio actual antes de persistirlo. Así, el separador sigue accesible y reduce
desde el primer movimiento, aunque se haya restaurado una altura mayor.
La geometría pertenece al shell; `uiStore` conserva la preferencia y Monaco
adapta el área de escritura. No se agregan observadores o listeners globales.

Corrección del 2026-10-08: antes, ampliar el panel aumentaba el contenedor de
252 a 352 px en el ensayo de escritorio, mientras Monaco permanecía en 252 px.
Solo se recalculaba al abrirlo. La corrección permite que el área de escritura
ocupe la altura disponible; barra, separador y margen inferior conservan su espacio.

Revisión Chromium a 1600×1000: ampliación por teclado a 352 px y arrastre a
522 px; reducción a 322 px; ancho de 1600 a 1340 px al abrir navegación y a
940 px al cambiar el viewport. En todos esos casos el área interna coincide con
el contenedor. El SQL escrito permanece durante el arrastre y al cerrar/reabrir;
sin errores de página. Reporte y capturas en `build/editor-resize-review/`, con
proyecto y aprendizaje en memoria. Svelte-check sin errores/advertencias,
150 pruebas frontend pasan y build correcto. CI se verifica sobre el commit enviado.

Revisión adicional del 2026-10-08 para el límite superior: antes, en una ventana
1280×600 con 548 px de workspace, el arrastre dejaba el panel en 590 px y el
separador a 11 px, oculto por encima del área que comienza a 52 px. Ahora se
detiene en 548 px y el separador permanece accesible. Un arrastre descendente
de 80 px reduce a 468 px. Al reducir la ventana con una preferencia de 700 px,
un arrastre de 40 px reduce desde 548 a 508 px sin recorrido muerto. Restaurar
700 px en una ventana 1280×500 muestra 448 px y ArrowDown reduce a 438 px.
Cerrar/reabrir conserva esa altura y Monaco ocupa su contenedor en todos los
casos, sin errores de página. Evidencia en `build/editor-bounds-review/`, con
ambos catálogos en memoria; 150 pruebas frontend, check y build correctos.

## Responsabilidades de implementación

| Pieza | Responsabilidad |
| --- | --- |
| `NavigationToggle.svelte` | Botón compacto de logo, nombre de acción, estado y referencia al panel |
| `NavigationPanel.svelte` | Acoplamiento de escritorio o diálogo móvil, foco, Escape/clic exterior, selección y breakpoint |
| `DashboardExplorer.svelte` | Contenido, búsqueda y operaciones del explorador; no decide la geometría del shell |
| `AppBar.svelte` | Contexto, acceso a comandos, filtros y acciones del editor |
| `CommandPalette.svelte` | Buscar dashboards y ejecutar comandos; no contiene lógica de layout |
| `uiStore.svelte.ts` | Preferencias privadas del navegador y estado transitorio de interfaz |
| Viewer de workspace | Datos y navegación de lectura del workspace, reutilizando panel y opciones |
| `ViewerDashboardSwitcher.svelte` | Selector/búsqueda y anterior/siguiente sin API ni estado de autoría |
| `ViewerOptions.svelte` | Apariencia y acciones secundarias de Preview mediante callbacks; no duplica navegación |
| `FilterContext.svelte` / runtime | Borrador y confirmación del conjunto según su contrato de lectura |

El panel recibe el estado abierto y comunica cambios mediante callbacks. No
accede a la API ni al store de dashboards. Su snippet recibe callbacks de
selección/cierre e indicador de modalidad; los consumidores muestran cierre
interno solo en móvil y deciden qué dashboard cargar. Se usa
`Dialog` de bits-ui para el foco modal, cierre y bloqueo de scroll.

La preferencia del editor conserva la clave `sqlviz-sidebar-collapsed`:
`1` significa oculto y `0` abierto. El viewer usa su propia preferencia
`sqlviz-viewer-navigation-hidden`. Ambas tienen alcance de navegador, se
restauran al cargar y siguen funcionando si localStorage está bloqueado.
No se guardan en el proyecto ni alteran lo que ve otro visitante.

Los atajos globales respetan eventos ya manejados y campos de texto; el editor
Monaco conserva sus combinaciones. Ctrl/Cmd+B alterna la navegación. El cierre
devuelve el foco al control de marca/navegación de cabecera, también si se hizo con el atajo. Los
menús portaleados conservan su propia interacción. Las animaciones de apertura
respetan `prefers-reduced-motion`.

## Validación y límites

La evidencia actual de cabecera/filtros se documenta en
[el incremento de lectura](sqlviz-reader-context.md). La ampliación del control
de marca/navegación pasó 133 pruebas frontend, check Svelte sin diagnósticos,
build estático y revisión Chromium: ancla estable y 260 px recuperados en
escritorio; cabecera a 390/320 px, búsqueda enfocada y cierre/foco móvil.
La simplificación posterior a un único logo/control y cierre solo en modal pasa
28 pruebas específicas de navegación/explorador, sin diagnósticos Svelte.
El cambio posterior de logo a icono según hover/foco pasa esas mismas 28 pruebas,
check sin errores/advertencias y build estático. Chromium con API aislada en
memoria comprueba el icono correcto al abrir/cerrar, ancla estable, Enter/Espacio,
movimiento reducido y tap/foco en móvil táctil de 390 px, para workspace,
Preview y editor. Sin errores de página. Reporte/capturas en
`build/navigation-hover-review`, ignorado por Git; el servidor de ensayo se cerró.
El ajuste de color conserva el índigo exacto del logo (`#5B5BD6`) en ambos
iconos. Check y build pasan; Chromium verifica el stroke en los dos temas,
abierto/cerrado y con/sin hover, además de un dispositivo táctil. Evidencia en
`build/navigation-hover-review/color-report.json`; sin errores de página.
La corrección del resaltado de items pasa check sin diagnósticos, build y las
25 pruebas existentes del selector y filtros. Chromium comprueba dashboards y
acciones con mouse, selección por flechas, búsqueda/Enter y selector del viewer
en temas claro y oscuro; sin errores de página. Evidencia en
`build/command-hover-review`, ignorado por Git, con API de ensayo en memoria.
El ajuste de foco del buscador pasa check sin diagnósticos, build y las mismas
25 pruebas. Chromium verifica foco automático, un único marco en el grupo,
8 px de espacio lateral, input contenido, búsqueda/Enter y selección por flechas
en el diálogo claro/oscuro y el selector de workspace de escritorio/táctil;
sin overflow ni errores de página. Evidencia en `build/command-focus-review`,
ignorado por Git; la API de ensayo en memoria se cerró.
Los registros siguientes
corresponden a entregas anteriores, incluida la variante con flechas.

**Ampliación anterior del selector de viewer:** 8 casos nuevos entre componente y página,
suite completa **91 pruebas en 16 archivos**, tipos **0 errores/advertencias**
y build aprobado. Se ejecutaron secuencialmente sobre el mismo checkout.
Chromium con backend real aislado verifica anterior/siguiente, búsqueda por
nombre/carpeta, teclado, foco tras Escape/selección y cierre automático. El
lienzo mantiene **1440 px** con el selector abierto y sidebar oculto. A **390 px**
el desplegable cabe en el viewport y el shell no genera overflow horizontal.
Sin errores de página. Reporte/capturas en `build/viewer-switcher-review/`,
ignorados por git. El servidor de revisión se detuvo; la demo del usuario no
se reinició. Persisten los avisos de fixtures `derived_inert` y bundles/PURE.
Este ensayo verifica navegación, no la legibilidad de todos los gráficos en
móvil ni los modos de página pantalla/scroll todavía pendientes.

Se verifican con Vitest apertura/cierre, retorno de foco, persistencia,
almacenamiento bloqueado, búsqueda, selección desde comandos, respeto de
atajos de escritura, modo de concentración y el viewer protegido antes del
desbloqueo. Se conservan los flujos de creación inline del explorador.

La revisión en Chromium con respuestas API sintéticas mide 1440 px de área
principal con navegación oculta y 1180 px con navegación abierta, tanto en el
editor como en el viewer. A 390 px el diálogo no reduce el ancho del contenido;
se comprueban ausencia de overflow horizontal del shell, Tab dentro del modal,
Escape con retorno de foco y cierre por selección. Las capturas y el informe
local quedan en `build/navigation-review/`, excluido de Git.
Se verifica que ECharts redimensione el gráfico hasta ocupar el ancho recuperado.
También se comprueban menús portaleados de organización y un diálogo de
confirmación dentro del modal móvil: Escape cierra la confirmación, mantiene
la navegación y permite después cerrar con clic exterior.

Las pruebas de navegador usan la SPA de producción y fixtures; no demuestran
autorización del backend, calidad de inferencia ni persistencia de configuración
visual. Tampoco cubren todavía Safari/Firefox, lector de pantalla, todas las
combinaciones de gráficos/filtros ni la legibilidad de dashboards completos en
móvil. Los hallazgos de seguridad de la auditoría siguen abiertos.

Validación del 2026-10-06: **61 pruebas aprobadas en 10 archivos**, comprobación
de tipos sin errores y build de producción completado.

Comandos de verificación del frontend:

```sh
npm run check
npm test
npm run build
```

Ejecutar estos comandos secuencialmente sobre el mismo checkout: SvelteKit,
Vitest y el build comparten archivos generados en `.svelte-kit`. Ejecutarlos en
paralelo puede mezclar los identificadores de bootstrap de servidor y cliente.

La comprobación de tipos de esa primera entrega mantenía seis avisos de
componentes ajenos a navegación, corregidos después en E0. Vitest registra
avisos `derived_inert` al remontar
consumidores de stores; esta entrega no refactoriza su ciclo de vida. El build
mantiene los avisos previos de tamaño de bundles y de la anotación PURE.

La prueba ampliada encontró un rechazo `Canceled` al cerrar rápidamente
Monaco. La traza lo sitúa en `WordHighlighter.dispose` al cancelar trabajo
diferido; el worker actual de SQL, además, es provisional. Se desactiva el
resaltado automático de coincidencias; se conservan resaltado de
sintaxis, selección y búsqueda de texto. Rehabilitar coincidencias automáticas
requiere implementar el worker real. Además, la carga diferida del editor
comprueba si fue desmontado antes de crear una instancia y cancela su foco
pendiente al destruirse.
El flujo ampliado pasa tres ejecuciones consecutivas en Chromium sin errores
de página después de esta corrección.

## Siguiente alcance

Esta entrega permite evaluar la navegación con usuarios. El trabajo pendiente
del Studio incluye contratos persistentes de página/panel, modo pantalla con
reglas de viabilidad, modo scroll explícito, layout editable, undo/redo e
inferencia y renderizado multiserie. Antes de ampliarlo a ETL/modelado, siguen
vigentes las prioridades de seguridad e integridad de E0/E1.
