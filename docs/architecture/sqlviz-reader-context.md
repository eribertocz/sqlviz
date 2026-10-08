# Cabecera de lectura y aplicación de filtros

**Actualizada:** 2026-10-07. **Estado:** implementación local en Preview, editor
y ambos viewers. Es un incremento compatible de la
[especificación de navegación/filtros](sqlviz-navigation-and-filters-spec.md),
no el cierre del Studio ni del contrato persistido de filtros de E1.

## Experiencia entregada

Preview y el viewer de workspace muestran el título como selector con búsqueda
por nombre/carpeta. Ctrl/Cmd+K abre ese mismo selector. El enlace individual
conserva un título sin ofrecer navegación fuera de su alcance. Se retiran de la
cabecera de lectura la búsqueda duplicada y anterior/siguiente; el componente
conserva su variante con flechas para futuros recorridos explícitos.

La cabecera presenta un único acceso **Filters**. Muestra la cantidad de controles
con restricciones efectivas y, cuando hay espacio de escritorio, una síntesis de
la primera condición aplicada. Esa síntesis no declara que el filtro tenga
prioridad semántica. El detalle completo está disponible al abrir el panel y en
el nombre accesible del botón. En móvil se conserva botón y cantidad; no se
reproduce una fila ilimitada de chips ni se elige un periodo prioritario por
heurística.

El logo es el único elemento visible de un botón en la esquina superior izquierda
de editor, Preview y workspace: 36 × 36 px en escritorio y 44 × 44 px en móvil.
Abre/cierra la biblioteca; nombre accesible, tooltip y `aria-expanded` anuncian
acción/estado. Su posición no cambia al abrir el panel de escritorio. El sidebar
acoplado no duplica un botón de cierre. En móvil,
la biblioteca enfoca su buscador, ofrece cierre dentro del diálogo y devuelve el
foco al control de cabecera. El cierre dentro del panel solo aparece en el modal,
donde el control original está cubierto. No se añade un segundo icono junto al logo.

**View options** reúne colores y apariencia; Preview añade edición y concentración.
La biblioteca tiene acceso directo y no se duplica en ese menú. Sigue siendo
opcional: 0 px oculta, 260 px fijada en escritorio y diálogo en pantallas estrechas.
El editor conserva sus acciones de autoría, pero reutiliza el panel de filtros compacto.

El panel de filtros se abre sobre el contenido, sin cambiar las dimensiones del
canvas. Contiene condiciones confirmadas, controles de borrador y **Apply filters /
Cancel**. Sus campos desplazan internamente; las acciones quedan fuera de ese
scroll. Escape/cierre descartan ediciones sin aplicar y recuperan el foco; cerrar
un panel no debe robarlo a otro control ya abierto.

**Saved filters** conserva los presets del navegador. Elegir uno modifica el
borrador; Aplicar confirma el conjunto completo. Una clave antigua que ya no
existe produce un rechazo visible antes de ejecutar. Las claves omitidas del
preset eliminan restricciones previas, según el contrato actual. **Clear all**
vacía el borrador; requiere Aplicar y no simula defaults publicados inexistentes.

Mientras se aplican cambios, el botón indica actualización y los gráficos
continúan mostrando el contexto anterior. Un fallo conserva todos los datos y
criterios confirmados; el panel mantiene el borrador para reintentar. Se anuncia
el estado por región accesible. Un conjunto sin filas se confirma como vacío.

## Responsabilidades e integridad

| Pieza | Ownership |
| --- | --- |
| [FilterContext.svelte](../../packages/sqlviz-web/src/lib/components/FilterContext.svelte) | Borrador, apertura/cierre, edición, presets y foco; recibe estado por props y emite una intención de aplicar |
| [filterContext.ts](../../packages/sqlviz-web/src/lib/filters/filterContext.ts) | Copia de valores, bindings actuales, comparación, resumen y validación básica compatible |
| [filterRuntime.svelte.ts](../../packages/sqlviz-web/src/lib/filters/filterRuntime.svelte.ts) | Solicitud vigente, estado pendiente/error y buffer completo antes de confirmar |
| [filterDomains.ts](../../packages/sqlviz-web/src/lib/filters/filterDomains.ts) | Carga secuencial y deduplicada de dominios, con descarte al abandonar la vista |
| Páginas viewer | Credenciales de su enlace, carga inicial, autorización y adaptación del runtime hacia su estado local |
| dashboardStore | Adaptación del mismo runtime hacia Preview/editor y caché de resultados confirmados |
| ViewerOptions / ViewerDashboardSwitcher | Opciones y navegación mediante props/callbacks; sin ejecución SQL ni credenciales |

Cada instancia del runtime recibe adaptadores; no importa el store de autor ni
comparte sesiones entre lectores. Captura identidad de vista, referencia del
conjunto de resultados y revisión de solicitud. Navegar, volver a ejecutar o
desmontar invalida solicitudes pendientes. Cambios concurrentes del conjunto
también impiden confirmar una respuesta sobre una base sustituida.

La aplicación compara **todas** las variables del objetivo con el contexto
confirmado. Ejecuta una vez cada panel afectado, con todos sus bindings, incluidos
los vacíos que neutralizan filtros según el contrato vigente. Los resultados se
acumulan sin publicarse parcialmente. Únicamente la solicitud vigente confirma
datos y valores juntos. El layout conserva filas, columnas y altura de paneles;
filtrar no recompone el dashboard.

Los dominios comparten el presupuesto analítico con los gráficos. Cada cargador
solicita uno a la vez, deduplica variables y deja de emitir consultas cuando su
vista se invalida. Esto evita que un dashboard con muchos filtros lance una
ráfaga que agote por sí sola los slots del servidor. No elimina la contención
entre visitantes: el servidor conserva sus límites y autoridad.

Se preserva `false` y `0` como selección efectiva. El control booleano distingue
**Any / Yes / No**: sin restricción, verdadero y falso, respectivamente.
Dropdown/multiselect mantienen
los tipos de opciones simples del dominio en lugar de convertir todo a texto.
La validación frontend es preliminar: backend sigue siendo autoridad para valores,
SQL, acceso y presupuestos. Las búsquedas Command usan una etiqueta de raíz
válida para que `aria-labelledby` no anule el nombre accesible de sus inputs.

En los viewers, 401/403/404 retiran contenido y contexto protegido. Una denegación
de una solicitud anterior conserva ese efecto aunque exista una respuesta más
reciente. Invalidar una solicitud en el navegador no cancela SQL en el motor.

La confirmación conjunta es coherencia de interfaz, no una transacción común
entre fuentes. Cada consulta puede observar un momento distinto de sus datos.
Tampoco crea una revisión de configuración persistida en el servidor.

## Límites que siguen pendientes

- Definiciones persistidas/versionadas: ID, tipos declarados, defaults, prioridad
  de controles y alcance por panel. Se conserva `variable` y pairing con coma.
- Periodo prioritario abreviado en móvil, filtros rápidos publicados por el autor
  y configuración de presentación. No hay preferencias publicadas nuevas.
- Estado diferenciado de carga/error/vacío de dominios; permanece el fallback
  actual a entrada manual cuando no se dispone del dominio.
- Valores SQL NULL seleccionables, zonas horarias/fechas relativas, presets
  compartidos, historial/URLs de dashboard y favoritos.
- Modo pantalla viable, layout responsive de gráficos y garantía de legibilidad
  móvil del dashboard completo. Cambiar la cabecera no entrega esas capacidades.
- Observación de tareas con usuarios, medición de descubrimiento y accesibilidad
  completa. Las pruebas técnicas no demuestran superioridad comercial ni UX perfecta.

E1 continúa con composición tipada y contratos PATCH restantes. Este incremento
de interacción reutiliza el transporte existente y no cambia el formato `.sqlviz`
ni sustituye migraciones o identidad estable de paneles.
Los pendientes anteriores están ordenados con criterios de aceptación en el
[plan inmediato después de navegación](sqlviz-product-roadmap.md#plan-inmediato-después-de-navegación).

## Validación

- `npm run check`: 0 errores y 0 advertencias.
- Última ejecución completa, antes de simplificar el logo:
  `npm test -- --maxWorkers=4`, 133 pruebas pasan en 21 archivos. Incluyen borrador,
  presets con varias variables, fallos parciales, respuestas tardías, revocación,
  geometría conservada, valores cero/falso y carga secuencial de dominios.
  La ampliación de navegación comprueba el mismo control de cabecera al abrir/cerrar
  y búsqueda/foco del diálogo móvil; mantiene las pruebas de alcance y revocación.
- Corrección del logo y cierre duplicado: 28 pruebas pasan en los tres archivos
  de navegación de autor, workspace y explorador; check Svelte sin diagnósticos.
  Se exige un único cierre en escritorio y se conserva el del modal móvil.
  Build estático y Chromium también pasan: botón de logo de 36 px sin SVG
  adicional, un solo cierre en escritorio, botón de 44 × 44 px en móvil y
  cierre interior del modal funcional. Reporte/capturas en `build/logo-navigation-review`.
- `npm run build`: compilación estática completada.
- Chromium con la API real en RAM: workspace a 1440 × 900 y 390/320 × 844,
  enlace individual y Preview de autor. Se comprueban búsqueda por Ctrl+K,
  aplicación/error de filtros, recuperación de foco y navegación opcional.
  Diez filtros cargan sus opciones; el panel no cambia el ancho del canvas,
  no produce overflow horizontal y mantiene Aplicar visible en móvil.
  El reporte final no registra errores de página ni consola inesperados;
  excluye el HTTP 500 provocado deliberadamente para comprobar recuperación.
- Ampliación de marca/navegación: Enter abre y Espacio cierra desde el mismo
  botón en escritorio. Sus coordenadas no cambian; ocultar recupera 260 px.
  A 390/320 px los accesos de cabecera permanecen dentro del viewport, el control
  de navegación tiene 44 px de alto y conserva espacio para el selector.
  La búsqueda móvil recibe foco; Escape/clic exterior cierran y lo devuelven
  al control de marca. Opciones no duplica navegación y el enlace individual
  mantiene su alcance. Capturas y reporte en `build/navigation-brand-review`.

Los artefactos temporales están en `build/filter-context-review` y
`build/navigation-brand-review` y `build/logo-navigation-review`, ignorados por Git.
La revisión HTTP usa un proyecto y memoria de aprendizaje en RAM; no abre archivos
del usuario. Check, tests y build se ejecutan secuencialmente en el checkout.
Vitest aún emite avisos `derived_inert` de Bits UI al desmontar fixtures; se espera
la limpieza diferida del bloqueo de scroll antes de destruir jsdom. No hay errores
no capturados en la ejecución final de pruebas.
La compilación conserva el aviso de tamaño de chunks;
su optimización no forma parte de este incremento. La comprobación a 320 px cubre
cabecera/panel, no garantiza legibilidad de todos los gráficos del layout anterior.
