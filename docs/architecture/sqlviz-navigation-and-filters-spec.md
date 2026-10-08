# Navegación y contexto de filtros del dashboard

**Diseño inicial:** 2026-10-06; actualizado: 2026-10-07. **Estado:** especificación
con un [primer incremento de lectura implementado](sqlviz-reader-context.md).
Cabecera compacta, borradores y confirmación del conjunto están entregados
localmente; prioridades/defaults publicados y los demás contratos siguen pendientes.
La navegación que existe se describe en [su contrato actual](sqlviz-navigation.md).
Este documento complementa [Dashboard Studio](sqlviz-dashboard-studio-spec.md)
y respeta el [orden de entregas](sqlviz-product-roadmap.md).

## 1. Diagnóstico inicial — 2026-10-06

El selector del viewer resuelve cambiar de dashboard sin desplegar el sidebar.
Todavía no resuelve la composición de navegación, filtros y acciones. La revisión
del código encuentra estos límites:

| Observado | Consecuencia | Referencia |
| --- | --- | --- |
| El viewer de workspace coloca todos los filtros y `Views` entre el selector y las acciones | La densidad crece con el número de filtros; compiten por el ancho | `routes/view/workspace/[token]/+page.svelte`, cabecera |
| `.viewer-filters` tiene scroll horizontal con scrollbar oculta; en móvil se permite otra fila | Los filtros pueden quedar fuera de vista y consumir una altura variable | Mismo archivo, estilos |
| Título y botón de búsqueda abren el mismo selector; sidebar ofrece otra lista | Existen accesos equivalentes sin una jerarquía suficientemente clara | Cabecera y `openNavigationSearch` |
| Cada cambio modifica `viewerFilterValues` antes de ejecutar; algunos errores de ejecución se capturan sin mostrarlos | Criterios nuevos pueden acompañar datos anteriores o un conjunto parcialmente actualizado | `handleFilterChange` y `executeFilteredPanels` |
| El debounce conserva solamente la última variable cambiada; un preset llama al mismo manejador por cada entrada | Paneles que dependen exclusivamente de otra variable del preset pueden quedar sin actualizar | `FilterViews.onApply` y selección de paneles por `changedVar` |
| Los controles identifican rangos mediante una cadena de variables; convierten las opciones del dominio a texto y usan truthiness para algunos valores | Riesgo de perder tipos y confundir `false`/`0` con ausencia; un rango no tiene identidad explícita | `FilterControl.svelte` |
| Los presets se guardan en localStorage | Son preferencias de ese navegador; no configuración publicada ni compartida | `FilterViews.svelte` y su store |

Estos hallazgos describen el código anterior al incremento de lectura. Proceden
de lectura de código; el primer incremento documental no
añade ensayos que reproduzcan cada fallo. Las comprobaciones del selector de la
entrega anterior no prueban la corrección del sistema completo de filtros.
También queda pendiente la legibilidad móvil de los gráficos: adaptar la
cabecera no convierte por sí solo un grid de escritorio en un dashboard móvil.

## 2. Decisión: conservar una cabecera pequeña y estable

La cabecera debe contestar **dónde estoy**, **qué contexto tienen estos datos** y
**cómo cambio ese contexto**. El espacio principal corresponde al dashboard.

No se elimina la cabecera en la lectura habitual. Se reduce su contenido y se
establece una jerarquía: selector de dashboard, filtro prioritario cuando cabe,
acceso al resto de filtros y menú de acciones secundarias. No habrá una segunda
barra permanente que replique esos controles ni un dock flotante sobre gráficos.

| Alternativa | Evaluación para SQLviz |
| --- | --- |
| Sidebar siempre visible | Útil al explorar una biblioteca, pero obliga a todos los lectores a ceder ancho |
| Eliminar cabecera y revelar controles con hover | Recupera altura, pero perjudica orientación, descubrimiento y uso táctil |
| Dock flotante de navegación y filtros | Puede cubrir datos, leyendas o tooltips; complica el modo pantalla |
| Cabecera con todos los filtros | Directa para un dashboard sencillo; no escala con filtros y títulos largos |
| Cabecera estable con contexto compacto y detalle bajo demanda | Dirección elegida; requiere pruebas de descubrimiento y del resumen de condiciones |

Una altura inicial de 48–56 px en escritorio es un objetivo de diseño, no un
contrato rígido. Texto ampliado, traducciones y necesidades de accesibilidad
tienen prioridad sobre sostener una sola fila. El número de filtros no debe
añadir filas automáticamente.

Esquema conceptual, no captura de funcionalidad implementada:

```text
Escritorio
Logo   Ventas ▾   Periodo: oct 2026 ▾   Filtros · 3   ⋯
────────────────────────────────────────────────────────────
                         Dashboard

Móvil
Logo   Ventas ▾       Oct · 3 filtros   ⋯
────────────────────────────────────────────────────────────
                         Dashboard
```

`3` significa tres definiciones de filtro con una restricción efectiva, no tres
parámetros SQL. Un rango cuenta como un filtro. El resumen completo de condiciones
siempre se puede abrir desde `Filtros`; en móvil el disparador conserva una
síntesis del periodo aplicado, con año cuando haga falta para desambiguar, si el
dashboard tiene ese filtro prioritario. No usar un número sin etiqueta ni mostrar cero como si
significara necesariamente «todos los datos».

## 3. Navegar sin abrir y cerrar un panel

- El **nombre del dashboard** es el acceso principal al selector. Al abrirlo,
  aparecen búsqueda, dashboard actual y destinos autorizados con su carpeta.
  Ctrl/Cmd+K abre el mismo acceso; no es la única manera de descubrirlo.
- Elegir un destino cierra el selector. No reserva ancho ni requiere cerrar el
  sidebar después. Nombres duplicados se distinguen por carpeta y siempre por ID.
- Con un único dashboard autorizado, el título es texto y no ofrece un selector
  vacío. Un enlace individual conserva su alcance; no descubre el workspace.
- El **explorador** se ofrece como opción de biblioteca. Se puede fijar por
  preferencia; no está abierto por defecto ni es requisito para navegar.
  Tiene acceso directo desde el control de marca/navegación en la esquina
  superior izquierda. No se duplica dentro del menú de acciones secundarias.
  El logo es el único elemento visible del botón; tooltip/nombre accesible y
  estado expandido describen su acción. El cierre interno existe solo en móvil,
  donde el modal cubre la cabecera; escritorio usa el mismo botón para cerrar.
- La búsqueda separada de la cabecera se retira cuando el selector ya tenga
  descubrimiento y acceso por teclado comprobados. Las acciones de paleta/tema
  pasan al menú secundario del lector; el tema publicado sigue siendo la base.
- Anterior/siguiente queda como acceso opcional para recorridos ordenados,
  especialmente en escritorio. `sort_order` no prueba que exista una narrativa.
  En móvil prima título + filtros; las flechas pueden quedar dentro del selector.
- No introducir pestañas permanentes para cualquier número de dashboards.
  Favoritos o recientes se incorporarán si hay uso que los justifique, con alcance
  y persistencia definidos; no inventar recomendaciones automáticas.

La entrega actual conserva búsqueda separada y flechas también en móvil. Cambiar
esa distribución exige implementar y verificar esta especificación; no basta
con reinterpretar lo ya entregado.

Un futuro historial de navegación debe soportar Atrás/Adelante y destinos
autorizados. No sustituirlo por las flechas de orden, persistir credenciales en
URLs ni restaurar sin validar criterios de otro dashboard.

## 4. Filtros: acceso rápido y edición completa

### En la cabecera

El autor puede elegir **hasta dos controles prioritarios** y su orden en la
configuración publicada. Se muestra únicamente lo que cabe en el ancho real,
después de reservar título, acceso a filtros y acciones. El presupuesto inicial
normal será un control, por ejemplo Periodo; cero en móvil estrecho. No se eligen
por ser las primeras variables inferidas ni por nombres supuestamente importantes.

El acceso `Filtros` conserva un resumen de restricciones aplicadas y la cantidad
efectiva. Si hay contexto obligatorio del dashboard, permanece identificable:
no puede quedar presentado como si el lector lo hubiese quitado. La ausencia de
restricciones editables no elimina el contexto publicado. Los permisos nunca
son un filtro editable ni se cuentan como una selección del usuario.

En un dashboard sin filtros editables no se muestra un botón inerte. Una selección
extensa se resume con etiqueta/cantidad y detalle accesible; no con una fila
ilimitada de chips ni con un tooltip que solo se descubre usando mouse.

### Al abrir Filtros

En escritorio se abre un panel de edición sobre el contenido, anclado al lado
derecho, con ancho acotado. En móvil se abre un diálogo con altura disponible,
scroll interno y acciones accesibles sin quedar debajo del teclado. El canvas
conserva sus dimensiones: abrir el panel no reorganiza los gráficos.

La primera sección muestra **condiciones aplicadas**; la edición distingue sus
cambios pendientes. Los controles tienen etiquetas de negocio, búsqueda en
dominios largos y estado de carga/error/vacío diferenciado. No convertir «no
pude cargar las opciones» en «no hay valores».

Para varios criterios, rangos y multiselección se ofrece **Aplicar** y **Cancelar**.
Escape y cierre exterior descartan el borrador sin ejecutar, con foco restaurado.
El estado de descarte es visible en la interacción; no se guardan cambios al cerrar
de forma implícita. Un filtro rápido puede confirmar una elección directamente,
pero una fecha parcial o un arrastre de slider no lanza cada estado intermedio.

**Restablecer** recupera los defaults publicados válidos y explica ese destino.
No equivale necesariamente a vaciar todos los valores. Los valores `false`, `0`,
ausente, vacío y selección de SQL NULL necesitan una semántica explícita y tipos
conservados; no derivar sus diferencias de truthiness o coerción a string.

Los presets se llaman **Filtros guardados** y se gestionan dentro de este panel.
Se distingue «guardado en este navegador» de una futura configuración publicada.
Aplicar un preset es una operación del conjunto completo; valida claves, tipos
y alcance. Para un preset completo, las claves omitidas regresan al default
publicado; si se desea un preset parcial, debe declararse como tal. No reutilizar
una lista de cambios independientes para simular esa operación.

## 5. Los criterios visibles deben corresponder a los datos

Esta es una condición de integridad del producto, anterior al acabado visual.

| Estado | Comportamiento visible y de ejecución |
| --- | --- |
| Estable | Resumen aplicado y gráficos corresponden a la misma revisión de filtros |
| Editando | Borrador en el panel; el resumen aplicado y los datos siguen sin cambios |
| Actualizando | Objetivo nuevo marcado como pendiente; se mantienen datos anteriores identificados como tales, sin afirmar que ya cumplen el nuevo criterio |
| Éxito | Datos afectados y contexto aplicado se publican juntos para la revisión vigente |
| Fallo | Se conserva el último conjunto confirmado y su contexto; error visible con reintento o descarte del objetivo pendiente |
| Sin filas | Estado vacío explícito bajo el contexto confirmado; no se confunde con error ni conserva números anteriores |
| Navegación o revocación | Una respuesta anterior no publica en otro dashboard; pérdida de acceso retira resultados y contexto protegido |

El runtime toma un snapshot completo de valores validados y calcula el conjunto
de paneles afectados por **todas** las diferencias con el estado aplicado.
Incluye las dos variables de un rango y todas las de un preset. Recoge respuestas
en un buffer por revisión y confirma el conjunto únicamente cuando los paneles
afectados han terminado correctamente. Un fallo no produce una publicación
parcial silenciosa.

Cada operación se identifica por dashboard, revisión de configuración y revisión
de solicitud. Solo la vigente puede publicar. Con cambios rápidos, una respuesta
antigua no puede ganar por llegar primero ni por llegar después. Cancelar HTTP
puede ahorrar trabajo, pero no sustituye esa validación ni garantiza cancelación
del motor. Los límites de concurrencia siguen aplicándose al fan-out.

Publicar resultados juntos asegura coherencia del estado de la interfaz, **no**
un snapshot transaccional entre consultas sobre fuentes que están cambiando.
Ese nivel de consistencia requiere un contrato de ejecución/fuente adicional y
no se promete aquí. Un panel no afectado conserva su contexto de alcance
declarado; un filtro local se identifica como local, no como global.

Fechas relativas requieren zona horaria y límites resueltos para la ejecución.
Actualizar «este mes» no debe reutilizar silenciosamente límites antiguos al
cruzar un cambio de periodo. Duración de consulta, última ejecución y frescura de
la fuente son conceptos distintos; mostrar frescura solo cuando se conoce.

## 6. Lectura, edición y presentación

**Viewer y Preview:** comparten controles y runtime de lectura. El autor decide
etiquetas, prioridades, defaults y tema al editar; el lector ajusta únicamente lo
permitido. Renombrar, guardar SQL y publicar no forman parte de esa cabecera.

**Editor:** incorpora comandos de autoría en áreas propias. Preview no conserva
acciones de edición porque existan en el mismo componente de cabecera. La
configuración del autor, la preferencia privada del lector y el estado transitorio
de ejecución tienen ownership separado.

**Modo pantalla:** calcula espacio útil restando altura real de cabecera,
márgenes y cualquier contexto visible. El panel de filtros temporal no obliga a
recomponer el layout. No usar `overflow: hidden` para simular que todo cabe ni
reducir texto hasta hacerlo ilegible. Una composición inviable requiere ajustar
paneles o elegir scroll, según el contrato de Studio.

**Presentación:** futura opción explícita que puede ocultar comandos de cabecera,
con recuperación visible/táctil y teclado. El título y contexto aplicado deben
seguir identificables en el dashboard. Fullscreen del navegador es otra acción.
No activar ocultación automática por hover ni afirmar que ya existe este modo.

## 7. Límites de arquitectura

| Responsabilidad | Contrato objetivo |
| --- | --- |
| Core | Definición/ID de filtro, tipos, defaults, variables vinculadas y alcance; validación independiente de UI/HTTP |
| API | Modelos de transporte tipados, validación predecible, autorización y adaptación hacia casos de uso; compose no ejecuta SQL |
| Persistencia | Configuración publicada versionada, vinculada a identidad estable de paneles; migración explícita del formato cuando proceda |
| Inferencia | Recomienda controles y composición; no redefine defaults, prioridades o decisiones guardadas del autor |
| Runtime de lectura web | Borrador/aplicado/pendiente/error, snapshots, revisiones y publicación coherente, compartido entre Preview y ambos viewers |
| Componentes UI | Renderizan props y emiten intenciones; no deciden qué consultas ejecutar, no importan credenciales ni stores de autor |

Una definición puede vincular varios parámetros, por ejemplo límites de fecha.
Dos variables con el mismo nombre no se unifican automáticamente si tipo,
significado o alcance difieren. La API verifica bindings y autorización del lado
servidor; declaraciones del cliente no amplían permisos ni presupuestos.

No hace falta otro microservicio. Hace falta separar decisiones de dominio,
orquestación de solicitudes y presentación dentro de los módulos existentes.
El runtime se extrae por comportamiento y casos comprobables, no como una base
genérica de componentes ni un singleton que mezcle sesiones de autor y viewer.

## 8. Orden de implementación y criterios de cierre

La siguiente unidad continúa siendo **E1: composición tipada y PATCH restantes**.
Debe rechazar entradas inválidas antes de componer, conservar payloads válidos
compatibles y definir omisión/null/vacío por campo. El contrato de compose no
es el futuro contrato completo de filtros o del Studio.

Por petición del usuario se adelantó un incremento compatible de la interacción
de lectura. Reutiliza los contratos actuales sin cambiar persistencia ni permisos;
su [documento de implementación](sqlviz-reader-context.md) distingue lo entregado
de la configuración publicada y semántica completa que aún requieren E1.

Después se cierran migraciones/dependencias e identidad/configuración persistida.
Con esa base, el recorrido de esta capacidad será:

1. Definiciones tipadas de filtros y semántica de defaults/presets, con contrato
   compatible y sin pérdida de tipos.
2. Runtime compartido de lectura, comenzando por presets, rangos, errores y
   concurrencia; la UI actual permite verificarlo antes de rediseñarla.
3. Cabecera y panel de filtros con ese runtime, primero viewer y Preview, después
   integración de configuración en el editor. Cada incremento preserva alcance.
4. Ajuste responsive y modo pantalla; pruebas de usabilidad antes de cerrar UX.

Criterios mínimos para cerrar esta capacidad:

- Matriz con 0/1/2/10 filtros; 0/1/50 dashboards; nombres duplicados/largos y
  valores extensos. Anchos 320/390/768/1440 y texto ampliado: sin controles
  inaccesibles, overflow horizontal ni gráficos recortados.
- Seleccionar otro dashboard sin abrir sidebar; biblioteca opcional con cero
  ancho reservado al ocultarse. No publicar datos de una vista abandonada.
- Contar restricciones por definición; `false` y `0` conservarán su valor.
  Preset de varios filtros actualiza todos los paneles afectados en una revisión.
- Cambios rápidos, respuestas fuera de orden, error de un panel, dominio fallido,
  cero filas y revocación. Nunca mostrar nuevos criterios como aplicados sobre
  un conjunto anterior o parcialmente confirmado.
- Teclado, foco visible, Escape, retorno al disparador, lectores de pantalla y
  scroll del diálogo móvil. Sin depender de hover ni de atajos exclusivamente.
- Abrir filtros no cambia las dimensiones del canvas. Modo pantalla verifica
  espacio real y viabilidad de los gráficos; no solo ausencia de scrollbar.
- Ensayo de uso: personas sin instrucción descubren cambiar dashboard, aplican
  dos filtros y explican correctamente el contexto de los números. Objetivo
  inicial por validar: al menos 4 de 5 completan el recorrido sin ayuda. Es una
  señal de iteración, no evidencia estadística ni garantía universal.

## 9. Fundamento y límites de la recomendación

Mostrar lo frecuente y abrir lo avanzado bajo demanda sigue el principio de
[revelación progresiva de NN/g](https://www.nngroup.com/articles/progressive-disclosure/).
La selección de qué conservar visible necesita observar tareas reales.

La distinción entre edición por lote y filtrado interactivo considera intención
y tiempo de respuesta, siguiendo el análisis de
[NN/g sobre aplicación de filtros](https://www.nngroup.com/articles/applying-filters/).
Su contexto es filtrado de resultados; la publicación coherente de un dashboard
es una decisión adicional de SQLviz, no una garantía que esa fuente demuestre.

Para accesibilidad, el [patrón toolbar de W3C](https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/)
requiere gestión de foco y navegación interna cuando se adopta ese rol. La
cabecera puede agrupar botones semánticos sin anunciar `role="toolbar"` de forma
decorativa. El selector y los diálogos deben conservar sus patrones propios.

Esta propuesta busca eficiencia, claridad y confianza. No afirma originalidad
mundial ni superioridad sobre productos sin un estudio comparativo y ensayos
de usuarios. Su calidad se demostrará con comportamiento, legibilidad y evidencia.
