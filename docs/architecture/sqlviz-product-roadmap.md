# Plan de entregas vigente

**Actualizado:** 2026-10-07. Reemplaza el orden de trabajo del
[roadmap histórico](sqlviz-roadmap.md), no el historial de releases.
**Estado:** base local E0 implementada; E1 en curso, E2–E5 pendientes. Las cuatro
unidades E0, integridad y composición tipada de E1, y navegación parcial de E2
están registradas en `feat/sqlviz-foundations`; ver el
[registro de Git](sqlviz-git-workflow.md). Validación local documentada y CI
verificado en [2731418](https://github.com/eribertocz/sqlviz/actions/runs/37711347859);
ese resultado no acredita las capacidades futuras ni la operación pública.

No asignar fechas ni versiones antes de dimensionar cada entrega. Los números de
entrega indican dependencias, no promesas de calendario. Cada entrega debe poder
revisarse y probarse como incremento, con migraciones explícitas cuando proceda.

**Foco según los requisitos del usuario:** trabajar sin prisa por
capacidades completas y criterios de cierre. Tras E0 y la base de E1, concentrar
el desarrollo en el [Dashboard Studio](sqlviz-dashboard-studio-spec.md): contrato
visual → lienzo/navegación → inferencia y renderizado → acabado. No ampliar la
plataforma mientras ese recorrido esté incompleto. Esa especificación precisa
los criterios de E1/E2 y adelanta la calidad de inferencia al núcleo del producto.
La [decisión aceptada de autoría](sqlviz-visual-authoring-decision.md) incorpora
Automático → Visual Builder → ECharts native options y adelanta el dataset mínimo
a la unidad 10. El catálogo completo y las transformaciones siguen posteriores.

## Plan inmediato después de navegación

La cabecera, selector, control de marca/navegación, filtros con borrador y runtime
confirmado están implementados localmente. Eso no cierra E1 ni entrega el Studio.
La navegación directa solicitada no introduce un nuevo formato persistido.
Los pendientes del incremento anterior se trabajan en este orden, en unidades
pequeñas con su propia evidencia antes de pasar a la siguiente:

| Orden | Capacidad pendiente | Qué debe demostrar el cierre |
| --- | --- | --- |
| 1 — En curso, unidad 8 | Completar PATCH de paneles | Composición tipada (BP-04) y PATCH de dashboards entregados localmente; completar tipos, límites, omisión/null y atomicidad de paneles |
| 2 — Unidad 9 | Migraciones y dependencias | Cambios de esquema probados sobre copias, rollback/fallo explícitos; storage no depende de inference ni de su memoria global |
| 3 — Unidad 10, por incrementos | Dataset mínimo, identidad y configuración visual persistida | Dataset/visual/panel separados; varias visualizaciones reutilizan una definición; reordenar/editar SQL no transfiere ajustes; revisiones, campos y layout sobreviven a reapertura y compartir; contrato preparado para opciones expertas |
| 4 — Completar unidad 11 | Definiciones de filtros versionadas | ID, tipos, defaults del autor, rangos con bindings explícitos y alcance por panel; reset restaura defaults reales; la inferencia no pisa decisiones publicadas |
| 5 — Unidad pequeña de dominios/valores | Estados y semántica de filtros | Distinguir carga/error/vacío, ofrecer reintento y preservar el contexto; NULL seleccionable y contratos de zona horaria/fechas relativas definidos sin equivalencias ambiguas |
| 6 — Completar contexto de lectura de unidad 12 | Prioridades y accesibilidad observada | Periodo/resumen compacto en móvil y filtros rápidos elegidos por el autor; tareas reales de navegación/filtros, teclado, zoom y nombres largos verificadas con usuarios |
| 7 — Studio E2, lienzo | Pantalla/scroll y edición reversible | Modos persistidos por dashboard; pantalla sin scroll solo cuando el layout es viable, con explicación de falta de espacio; drag/resize, alineación, undo/redo y gráficos legibles en móvil |
| 8 — Studio E2, inferencia/renderizado | Recomendaciones y gráficos completos | Elegir campos, series, unidades y formatos; comparar alternativas con un corpus independiente; soportar multiserie y mantener overrides del autor al filtrar/ejecutar |
| 9 — Studio E2, nivel experto | Editor ECharts native options | JSON nativo validado, preview, precedencia visible sobre el builder, IDs estables, diagnóstico de incompatibilidades y reset/undo; ajustes conservados en refresh y viewer |
| 10 — Cierre de E2 | Publicación y acabado | Preview/publicación versionados, plantillas coherentes, estados vacíos/error/carga, alternativa tabular y exportaciones autorizadas; revisión integral de autor a viewer en los tres niveles |

La inferencia puede preparar su corpus y contrato durante el lienzo, pero se
entrega por incrementos revisables; no se pospone su calidad hasta después de
plantillas decorativas. **La mayor inversión será Studio e inferencia/renderizado**:
combinan modelo persistido, geometría, interacción y significado de los datos.
No se prometen fechas ni «perfección» por completar checks técnicos.

Los presets actuales son privados de navegador. Presets compartidos, favoritos
y URLs/historial de dashboards quedan como extensiones posteriores de lectura,
con alcance, permisos y persistencia definidos. No bloquean la unidad 8 ni se
introducen antes de consolidar los contratos anteriores. La cancelación efectiva
en el motor de consultas iniciadas debe diseñarse aparte: descartar respuestas
tardías en la UI no equivale a detener SQL.

E3 (datasets y constructor visual sin SQL), E4 (métricas, modelado y roles de
equipo) y E5 (refresh/integraciones) conservan sus dependencias. ETL general y
expansión de conectores no se adelantan al recorrido central del Studio.

## E0 — Cerrar exposición y recuperar una base verificable

**Resultado:** acceso denegado por defecto, compartir con alcance efectivo y
ejecución sin acceso a datos internos. Atiende SEC-01–04 y los fallos de calidad.

Orden de implementación:

1. Cambiar bind por defecto a `127.0.0.1`; compartir en LAN requiere configuración
   explícita. Hacer Quack opt-in, quitar credencial literal e instalación nightly
   automática. Aplicar la misma política a demo.
   **Entregado el 2026-10-06:** ver [comportamiento y pruebas](sqlviz-local-startup.md).
2. Definir principal admin/viewer y dependencias de autorización. Proteger CRUD,
   listados, composición, ejecución y dominios de filtros; revisar todas las rutas.
3. Incorporar credencial de viewer con alcance en cada solicitud; actualizar
   ambos viewers. Verificar revocación, password y ámbito dashboard/workspace.
   **Puntos 2/3 entregados el 2026-10-06:** ver
   [política, pruebas y límites](sqlviz-authorization.md).
4. Separar conexión analítica y metadatos; ejecución permitida de datasets
   guardados para viewers, parámetros tipados y valores enlazados. Política de
   sentencias y acceso externo; presupuesto mínimo de consultas.
   **Separación y presupuestos HTTP entregados el 2026-10-06:** ver
   [implementación y límites](sqlviz-analytical-execution.md). Contrato de valores
   y preparación de filtros entregados en la [cuarta unidad](sqlviz-parameters-and-quality.md).
   Declaraciones por dataset, adaptadores externos y límites duros de proceso pendientes.
5. Aislar sesiones por aplicación y cerrar recursos por operación. Añadir matriz
   de pruebas negativas antes de declarar segura la compartición.
   **Sesiones y cierre de cursores implementados** en la segunda unidad; no
   implica por sí solo aislamiento; este se implementa en la tercera unidad.
6. Resolver errores de mypy, revisar las advertencias Svelte y alinear
   versiones de build. Mantener lockfiles y CI reproducibles.
   **Entregado en la cuarta unidad:** mypy global sin errores, svelte-check sin
   errores/advertencias; Node compartido por CI/revisión, matriz Python ampliada,
   versión instalada común para API/meta/creación e instalación con lockfiles.

**Aceptación:** cliente sin sesión recibe 401 en rutas de autor; enlace del
dashboard A no accede a paneles/dominios/resultados del B; viewer no modifica
datos ni SQL; password incorrecta no habilita ejecución; revocación funciona
también tras acceder o cachear; proyecto protegido y demo prueban sus respectivos
límites. Probar acceso a metadatos internos, DDL y recursos externos sin usar
datos reales. Inicio normal no abre servicio Quack ni escucha fuera de loopback.
Pruebas de compartir legítimo deben seguir pasando.

**Cierre local:** estas garantías se verifican en las cuatro unidades. No implica
publicación lista para redes no confiables ni CI remoto aprobado. Mantener acceso
local controlado hasta completar operación, publicación y políticas de fuentes.

## E1 — Persistencia y ejecución confiables

**Depende de:** E0. **Resultado:** editar, ejecutar, recargar y compartir conserva
el mismo significado y la configuración guardada.

- Extraer QueryService y repositorios desde routers; adoptar el adaptador DuckDB
  detrás de un contrato que incluya dialecto, presupuestos y cancelación.
- Corregir BP-01–05 de la [revisión de buenas prácticas](sqlviz-engineering-practices-review.md):
  paneles huérfanos al borrar dashboards, ciclos de carpetas, dimensiones fuera
  de rango, composición inválida que devuelve 500 y semántica de PATCH/null.
  **BP-01 entregado:** [borrado atómico y creación concurrente](sqlviz-dashboard-integrity.md).
  **BP-02 y ubicación de BP-05 entregados:** [jerarquía y PATCH](sqlviz-folder-integrity.md).
  **BP-03 entregado:** [dimensiones y overrides](sqlviz-panel-dimensions.md).
  **BP-04 entregado localmente:** [composición tipada](sqlviz-composition-contract.md).
  **PATCH de dashboards entregado localmente:** [tipos, omisión/null y atomicidad](sqlviz-dashboard-patch.md).
  **Foco siguiente:** contratos PATCH de paneles.
- Verificar dirección de imports e instalación independiente de paquetes;
  eliminar la dependencia no declarada storage → inference. Definir resultado
  del guardado de overrides cuando falle el aprendizaje secundario.
- Parsear sentencias en backend y dar IDs estables a paneles. Reconciliación
  transaccional de revisiones; no asociar identidad exclusivamente por posición.
- Migraciones con transacción, versión requerida, copia de seguridad y fallo
  explícito. Importar proyectos anteriores sin modificar el original durante ensayo.
- Límites de filas/bytes/tiempo y concurrencia; paginación o agregación para
  resultados grandes. Exponer truncamiento, duración y frescura.
- Un runtime compartido entre editor y viewers; requests identificadas y estados
  por panel para evitar resultados antiguos tras cambios rápidos de filtros.
  La [especificación de navegación y filtros](sqlviz-navigation-and-filters-spec.md)
  concreta borrador/aplicado/pendiente, presets como conjunto y publicación
  coherente. El [incremento compatible de lectura](sqlviz-reader-context.md)
  implementa ese runtime y el panel sobre el transporte actual; las definiciones
  publicadas/versionadas y la identidad persistida siguen pendientes.
- Persistir campos X/Y, formato, tema y layout del autor. Separar preferencias
  privadas del lector. Inferencia no pisa overrides explícitos.
- Incorporar por incrementos el dataset mínimo reutilizable, visualización con
  revisión e instancia de panel; distinguir definición y resultado de ejecución.
  Conservar exploración SQL directa y migrar explícitamente proyectos existentes.
- Versionar contrato visual y generar/verificar tipos frontend desde schemas;
  conservar golden tests de compatibilidad.
  Declarar procedencia de ajustes y compatibilidad del renderer; preparar el
  contrato de opciones expertas según la [decisión de autoría](sqlviz-visual-authoring-decision.md).

**Aceptación:** consultas con punto y coma en strings/comentarios se conservan;
reordenar paneles no transfiere overrides; un fallo parcial no publica un estado
mezclado; recargar/reabrir mantiene configuración; error de filtro muestra el
estado real; una ejecución cancelada termina en el motor; fallos de migración
no dejan el proyecto operando silenciosamente con esquema incompleto.
Además, borrar un dashboard respeta su política de dependencias de forma atómica;
carpetas con ciclos y dimensiones inválidas se rechazan; composición inválida
devuelve 4xx; omitir un campo y borrarlo explícitamente tienen semánticas distintas.
Los casos de uso nuevos se prueban sin HTTP y con fallos entre escrituras.

## E2 — Experiencia de dashboards premium

**Depende de:** E1. Diseño de componentes y plantillas puede prepararse antes.
**Resultado:** un autor entrega un dashboard presentable con pocos ajustes.

- Canvas, inspector consistente, alineación/resize, secciones, títulos y texto.
- Autoría progresiva: inferencia automática, Visual Builder y editor experto de
  opciones nativas ECharts JSON. Validación/preview, overrides con precedencia,
  conflictos de propiedades/listas explícitos y reset/undo; ningún refresh elimina
  ajustes. Las opciones no representables mantienen su valor y explicación en UI.
- Modo pantalla sin scroll para layouts viables y modo scroll, persistidos por
  dashboard; tratamiento explícito de falta de espacio, móvil y zoom.
- Sidebar ocultable por completo (0 px), botón permanente para recuperar
  navegación y overlay accesible; aplicar a editor y viewer de workspace.
  **Entregado el 2026-10-06 para el alcance de
  [navegación](sqlviz-navigation.md)**; no cierra el resto de E2 ni E0/E1.
- Inferencia de especificaciones completas y renderer multiserie: campos,
  unidades, fechas/nulos, orden y alternativas. Corregir la asignación por
  primera/última columna y medir con un corpus independiente de casos reales.
- Refinar KPI/líneas/barras/tablas con formatos, accesibilidad y estados completos.
- Temas y plantillas iniciales de ventas, finanzas y operaciones, usando datos
  de ejemplo y definiciones de métricas visibles.
- Edición reversible; separar borrador y revisión publicada. Preview representa
  exactamente la revisión que se va a compartir.
- Viewer responsive, navegación por teclado, alternativa tabular y exportación
  ligada a la revisión y al permiso del usuario.

**Aceptación:** revisión visual en 1440, 1024 y 390 px, sin solapamientos ni datos
ilegibles; flujo por teclado; configuración idéntica tras reabrir; lector no ve
borradores; pruebas de screenshot en escenarios fijos y E2E de autor a viewer.
Cumplir además la matriz de pantalla/scroll, navegación e inferencia de la
[especificación del Studio](sqlviz-dashboard-studio-spec.md). Pasar el benchmark
actual de tipos de gráfico no basta para cerrar esta entrega.

**Objetivo inicial a medir, no resultado actual:** al menos 4 de 5 usuarios piloto
publican un dashboard de 4 paneles desde un dataset preparado en menos de 10 min,
sin ayuda del desarrollador. Registrar puntos de abandono y correcciones de
inferencia. No activar telemetría externa sin decisión explícita.

## E3 — Datasets reutilizables y autoría sin SQL

**Depende de:** E1; el canvas de E2 consume estos contratos al incorporarlos.
**Resultado:** quien no escribe SQL crea gráficos usando datos preparados.
El contrato mínimo de dataset reutilizable se entrega antes del lienzo, en la
unidad 10 de E1. Esta fase amplía su catálogo y autoría de consultas mediante UI;
el Visual Builder de gráficos de E2 no implica todavía un query builder completo.

- Dataset guardado y versionado: fuente, SQL o consulta visual, campos, parámetros,
  granularidad, descripción, formatos y permisos.
- Catálogo con vista previa y selección de dimensiones/métricas; agregación,
  filtros y orden de consulta visual compilados en backend.
- Flujo inicial sobre una fuente/dataset, sin joins arbitrarios. SQL avanzado
  permanece disponible para el autor técnico.
- CSV/Parquet y un conector prioritario (hipótesis inicial: PostgreSQL), con
  descubrimiento de esquema, credenciales mínimas y política de refresh.

**Aceptación:** crear cuatro paneles sin SQL sobre un dataset compartido; cambiar
el esquema avisa de dependencias; reutilizar el dataset no duplica definición;
SQL generado usa parámetros; permisos se respetan en preview y filtros.
Una consulta SQL avanzada no se degrada silenciosamente al abrir el editor visual.

## E4 — Métricas confiables y colaboración

**Depende de:** E3 y publicación de E2. **Resultado:** los equipos comparten
definiciones y acceso, además de gráficos.

- Métricas/dimensiones explícitas: unidades, granularidad, agregación, tiempo,
  relaciones y cardinalidad. Linaje y validación de cambios incompatibles.
- Reglas para joins, métricas no aditivas y comparaciones temporales; fórmulas
  derivadas pequeñas y tipadas antes de un lenguaje de modelado extenso.
- Usuarios, owner/admin/editor/viewer y permisos a datasets/dashboards/fuentes.
  RLS/permisos de columna aplicados en ejecución, dominios, caché y exportaciones.
- Auditoría de cambios y accesos; sesiones revocables; backups/restauración;
  estrategia de metadatos de equipo seleccionada con pruebas de carga.

**Aceptación:** mismos valores de métricas en SQL y constructor visual; tests
contra doble conteo por joins y promedios incorrectos; matriz de permisos de
usuarios y ámbitos sin fugas; restauración probada; ninguna métrica se certifica
solo porque su nombre parece conocido al motor.

## E5 — Operación ampliada e integraciones según demanda

**Depende de:** uso real que confirme prioridades y límites medidos.

Refresh programado, materializaciones, alertas por condiciones verificables,
exports programados, embedding con permisos, conectores adicionales e integración
con modelado/transformaciones externas. Añadir trabajos persistentes e historial
de reintentos cuando el proceso interactivo deje de ser suficiente.

SaaS multiempresa exige diseño y pruebas propios de aislamiento, cuotas,
observabilidad y operación. No es consecuencia automática de añadir roles.

## Fuera de la prioridad actual

ETL general/CDC, orquestador propio, microservicios, knowledge graph universal,
gemelo cognitivo, SDK de veinte motores y decisiones autónomas sobre negocio.
Se pueden experimentar si existe una pregunta medible y una alternativa simple
con la que comparar resultados.

## Primeras unidades de trabajo

| Orden | Unidad revisable | Evidencia de cierre |
| --- | --- | --- |
| 1 — Entregado | Inicio local y Quack opt-in | 28 pruebas; ensayo HTTP real con un listener loopback; Quack real iniciado/detenido |
| 2 — Entregado | Autorización de autor y viewer por solicitud | Matriz negativa + flujos legítimos de compartir; ver límites de SQL en el documento de autorización |
| 3 — Entregado | Contexto analítico separado y consultas limitadas | No acceso a metadatos/DDL; cancelación y límites probados |
| 4 — Entregado localmente | Parámetros, tipado y configuración de build | Checks locales limpios; configuración y lockfiles verificados; CI remoto pendiente |
| 5 — Entregado localmente | Borrado atómico del dashboard y sus elementos (BP-01) | 25 casos nuevos: rollback, reapertura, concurrencia y sesiones |
| 6 — Entregado localmente | Jerarquía y PATCH/null de ubicación (BP-02/BP-05 parcial) | 93 casos nuevos, promociones atómicas y reapertura; UI a raíz/delete conserva gráficos y acceso |
| 7 — Entregado localmente | Dimensiones y overrides válidos (BP-03) | 49 casos Python y 9 frontend nuevos; rechazo/reapertura; navegador comprueba guardado, viewer y reset |
| 8 — Parcial | Composición tipada (BP-04) y PATCH de campos restantes | Composición y PATCH de dashboards entregados localmente; tipos, límites y atomicidad de PATCH de paneles pendientes |
| 9 | Migraciones y límites de dependencias | Fallo explícito, rollback y ensayo sobre copias; storage independiente de inference |
| 10 — Por incrementos | Dataset mínimo, revisión de visualizaciones/paneles y configuración visual persistida | Reutilizar una definición sin duplicar SQL; revisiones fijadas y opciones expertas previstas; reabrir, reordenar, filtrar y compartir sin perder ajustes |
| 11 — Parcial | Definiciones y runtime compartido de filtros | Runtime compatible entregado; definiciones/tipos/defaults publicados pendientes |
| 12 — Parcial | Cabecera de lectura y panel de filtros (E2) | Cabecera/panel entregados; prioridad publicada, ensayos de usuarios y modo pantalla pendientes |

Estas unidades son divisiones de E0/E1 para implementación. Solo las señaladas
como entregadas tienen implementación y evidencia; la base local E0 está implementada.
Ver límites de cada unidad antes de atribuir garantías de operación pública.
Actualizar la auditoría con commit y pruebas al cerrar cada riesgo.
