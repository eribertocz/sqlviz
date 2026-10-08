# Plan de entregas vigente

**Actualizado:** 2026-10-08. Reemplaza el orden de trabajo del
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

**Foco según los requisitos del usuario:** trabajar sin prisa por capacidades
completas y criterios de cierre. Tras E0 y la base de E1, concentrar el desarrollo
en el Dashboard Studio. El [plan operativo](sqlviz-studio-delivery-plan.md)
adelanta composición manual y drag/resize, y entrega temprano el primer recorrido
Automático → Visual Builder → ECharts native options. No ampliar la plataforma
mientras ese recorrido esté incompleto. La
[especificación del Studio](sqlviz-dashboard-studio-spec.md) conserva el detalle
funcional y la [decisión de autoría](sqlviz-visual-authoring-decision.md) define
motor, contratos y precedencia.

## Plan operativo: Dashboard Studio

El [plan operativo del Studio](sqlviz-studio-delivery-plan.md) es la única
secuencia de trabajo actual. Reemplaza el orden inmediato anterior, que dejaba
el lienzo y el nivel experto demasiado lejos del recorrido central.

**S0 entregado:** [geometría manual](sqlviz-canvas-contract.md), todavía sin UI,
almacenamiento o endpoints. **S1 en curso:**
[S1.1a parsing](sqlviz-sql-script-parsing.md) implementado; **siguiente S1.1b**,
identidad segura de paneles. Después se integra reconciliación transaccional,
documento de layout persistido y controles de posición/tamaño. S2 añade
drag/resize sobre ese mismo contrato. La revisión de dimensiones de E1 se
incorpora a S1; no es una línea independiente de mantenimiento.

S3 separa dataset/visual/panel; S4 verifica el primer recorrido de los tres niveles
y S5 amplía inferencia/renderizado. S6–S8 completan pantalla/scroll, áreas,
interacciones y publicación. La mayor inversión será el núcleo visual S3–S5.
Migraciones y correcciones de dependencias se entregan según las necesidades de
cada incremento; no se declara todo E1 cerrado para empezar una interfaz.

Cabecera, selector, control de marca y filtros confirmados ya existen, pero no
cierran el Studio. Presets compartidos, favoritos y URLs/historial conservan su
alcance futuro. La cancelación efectiva de consultas sigue pendiente:
descartar respuestas tardías en UI no equivale a detener SQL en el motor.

Los apartados E0–E5 siguientes son mapa técnico e historial de dependencias, no
una segunda lista de prioridades. ETL general, modelado avanzado y ampliación de
conectores se mantienen posteriores al recorrido central del Studio.

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
  **Campos básicos del panel entregados localmente:** [PATCH y coordinación con borrado](sqlviz-panel-patch.md).
  **Presentación entregada localmente:** [contrato, guardado confirmado y reintento](sqlviz-panel-presentation.md).
  **Tipo de gráfico entregado:** [contrato, confirmación y reset real](sqlviz-chart-overrides.md).
  **Foco siguiente:** dimensiones y guardado integrado en S1 del lienzo manual;
  identidad estable y recuperación visible de borradores son requisitos de ese flujo.
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
El contrato mínimo de dataset reutilizable se entrega en S3 antes de la autoría
completa en los tres niveles. La geometría manual se integra primero sobre IDs
estables en S1–S2. Esta fase amplía catálogo y autoría de consultas mediante UI;
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

## Historial de primeras unidades y pendientes técnicos

Esta tabla registra E0/E1 y los primeros incrementos de lectura. No determina
el orden inmediato: sus pendientes se integran según S1–S8 del plan operativo.

| Orden | Unidad revisable | Evidencia de cierre |
| --- | --- | --- |
| 1 — Entregado | Inicio local y Quack opt-in | 28 pruebas; ensayo HTTP real con un listener loopback; Quack real iniciado/detenido |
| 2 — Entregado | Autorización de autor y viewer por solicitud | Matriz negativa + flujos legítimos de compartir; ver límites de SQL en el documento de autorización |
| 3 — Entregado | Contexto analítico separado y consultas limitadas | No acceso a metadatos/DDL; cancelación y límites probados |
| 4 — Entregado localmente | Parámetros, tipado y configuración de build | Checks locales limpios; configuración y lockfiles verificados; CI remoto pendiente |
| 5 — Entregado localmente | Borrado atómico del dashboard y sus elementos (BP-01) | 25 casos nuevos: rollback, reapertura, concurrencia y sesiones |
| 6 — Entregado localmente | Jerarquía y PATCH/null de ubicación (BP-02/BP-05 parcial) | 93 casos nuevos, promociones atómicas y reapertura; UI a raíz/delete conserva gráficos y acceso |
| 7 — Entregado localmente | Dimensiones y overrides válidos (BP-03) | 49 casos Python y 9 frontend nuevos; rechazo/reapertura; navegador comprueba guardado, viewer y reset |
| 8 — Parcial | Composición tipada (BP-04) y PATCH de campos restantes | Composición, PATCH de dashboards, campos básicos, presentación y tipo de gráfico entregados; revisión de dimensiones pendiente |
| 9 | Migraciones y límites de dependencias | Fallo explícito, rollback y ensayo sobre copias; storage independiente de inference |
| 10 — Por incrementos | Dataset mínimo, revisión de visualizaciones/paneles y configuración visual persistida | Reutilizar una definición sin duplicar SQL; revisiones fijadas y opciones expertas previstas; reabrir, reordenar, filtrar y compartir sin perder ajustes |
| 11 — Parcial | Definiciones y runtime compartido de filtros | Runtime compatible entregado; definiciones/tipos/defaults publicados pendientes |
| 12 — Parcial | Cabecera de lectura y panel de filtros (E2) | Cabecera/panel entregados; prioridad publicada, ensayos de usuarios y modo pantalla pendientes |

Estas unidades son divisiones de E0/E1 para implementación. Solo las señaladas
como entregadas tienen implementación y evidencia; la base local E0 está implementada.
Ver límites de cada unidad antes de atribuir garantías de operación pública.
Actualizar la auditoría con commit y pruebas al cerrar cada riesgo.
