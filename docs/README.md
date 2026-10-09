# Documentación de SQLviz

Actualizada: **2026-10-08**.

**Qué trabajamos ahora:** [plan operativo del Dashboard Studio](architecture/sqlviz-studio-delivery-plan.md).
S0 entrega el núcleo de geometría; S1 incorporará persistencia y controles de
posición/tamaño, y S2 drag/resize. Después se completa el recorrido Automático →
Visual Builder → ECharts nativo. Este es el orden operativo vigente, con criterios
de cierre; los apartados E0–E5 conservan el mapa técnico e historial.

**Primera parte de S1 implementada:** [S1.1a, parsing SQL](architecture/sqlviz-sql-script-parsing.md).
Run, contador y foco usan análisis nativo en backend. El siguiente paso es S1.1b:
identidad y reconciliación; no se atribuye todavía esa garantía al parsing.

**Alcance de inferencia ampliado, pendiente de implementar:**
[AST, ámbitos, linaje y evidencias](architecture/sqlviz-semantic-inference-architecture.md)
y [matriz de familias ECharts](architecture/sqlviz-visual-capability-matrix.md).
Documentan los tres niveles, inputs SQL múltiples, adaptación de jerarquías/redes,
23 familias core y dependencias GL/custom. El plan desglosa S3–S5 en partes pequeñas;
el siguiente incremento de código continúa siendo S1.1b.

## Orden de lectura

La [matriz analítica BI](architecture/sqlviz-analytical-matrix-spec.md) es ahora
un módulo central pendiente, con entregas M1–M9: jerarquías de filas/columnas,
medidas, totales por contexto, builder con drag de campos y grilla dedicada.
Su primer flujo entra en S3/S4 antes de la ampliación general ECharts. El plan
también divide drag/resize de paneles S2 en seis partes. No confundir esta matriz
con la tabla plana existente ni con las coordenadas `matrix` de ECharts.

1. [Auditoría del producto y del código](architecture/sqlviz-audit-2026-10-05.md): estado observado, evidencias, riesgos y validación ejecutada.
2. [Evaluación de buenas prácticas](architecture/sqlviz-engineering-practices-review.md): SOLID, dependencias, invariantes, transacciones, concurrencia y controles de arquitectura.
3. [Dirección de producto y arquitectura objetivo](architecture/sqlviz-product-architecture.md): decisiones para continuar el desarrollo y límites entre módulos.
4. [Plan de entregas vigente](architecture/sqlviz-product-roadmap.md): prioridades, dependencias y criterios de aceptación.
5. [Contrato de inferencia](inference_contract.md) y [política de contratos](architecture/sqlviz-contract-policy.md): preservar los comportamientos compatibles durante la evolución.
6. [Changelog](../CHANGELOG.md): historial de funcionalidades entregadas.

Para la siguiente capacidad a pulir, consultar [Dashboard Studio](architecture/sqlviz-dashboard-studio-spec.md):
libertad de edición, modos pantalla/scroll, navegación sin rail y evaluación de
inferencias completas. Incluye nuevos ensayos sintéticos y criterios de cierre.
La [decisión aceptada de autoría](architecture/sqlviz-visual-authoring-decision.md)
define Automático → Visual Builder → ECharts native options sobre una misma
visualización, con precedencia, persistencia y restauración. El contrato mínimo
de dataset/visual precede la autoría completa en los tres niveles; la geometría
manual puede integrarse antes sobre referencias de panel estables. El
[núcleo del canvas](architecture/sqlviz-canvas-contract.md) ya está implementado
y probado; no habilita todavía UI de arrastre ni guardado del nuevo lienzo.

La [experiencia de paneles y áreas](architecture/sqlviz-panel-experience-spec.md)
define el acabado de cabecera, contenido, acciones y estados desde S1/S2, con
partes P1a–c y evidencia visual. Distingue CSS Grid como adaptador web de las áreas
de composición S6; sigue siendo diseño pendiente de implementación.

El [recorrido de editor multiconsulta](architecture/sqlviz-visual-authoring-decision.md#del-editor-multiconsulta-a-campos-reutilizables)
precisa la evolución prevista: sentencias con identidad → datasets/esquema →
preview y catálogo de campos → varios gráficos o matrices. Guardar SQL como
definición no importa filas ni crea vistas físicas. Este flujo corresponde a
S3/S4 y aún no está implementado; hoy se ejecuta una sentencia por panel.

El [Mapa vivo del dashboard](architecture/sqlviz-dashboard-map-spec.md) añade una
vista prevista de las conexiones reales consulta → dataset → visual → panel,
actualizada durante la autoría. Acceso bajo demanda, contexto y estados de guardado,
sin reservar espacio fijo ni construir un segundo modelo de dependencias.
F1–F3 se integran en S3/S4; la vista aún no está implementada.

La [navegación del workspace](architecture/sqlviz-navigation.md) documenta la
primera capacidad visual implementada de ese alcance: ocultación completa,
diálogo móvil, búsqueda y foco. Preview y el viewer de workspace incorporan
un selector de título para navegar sin abrir el sidebar.
El control de marca/navegación en la esquina superior izquierda abre o cierra
la biblioteca directamente, sin duplicar ese acceso dentro de opciones.
No indica que el Studio completo esté entregado.

La [especificación conjunta de navegación y filtros](architecture/sqlviz-navigation-and-filters-spec.md)
establece la evolución de esa cabecera: controles prioritarios, edición bajo
demanda y publicación coherente de datos/contexto. Incluye diagnóstico del código,
límites entre capas y criterios de cierre. Su [primer incremento de lectura](architecture/sqlviz-reader-context.md)
ya implementa cabecera compacta, panel de filtros y confirmación coherente;
prioridades/defaults publicados y contratos persistidos siguen pendientes.
Su evolución se integra en el [plan operativo del Studio](architecture/sqlviz-studio-delivery-plan.md).

La base E0 se entrega por unidades. Su [primera unidad de arranque local](architecture/sqlviz-local-startup.md)
ya está implementada: loopback por defecto, Quack opt-in y ownership explícito de
recursos. La [segunda unidad de autorización](architecture/sqlviz-authorization.md)
protege autor y lectores por recurso y solicitud. La
[tercera unidad de ejecución analítica](architecture/sqlviz-analytical-execution.md)
separa el catálogo, restringe acceso externo y aplica presupuestos. La
[cuarta unidad de parámetros y calidad](architecture/sqlviz-parameters-and-quality.md)
acota los valores y cuerpos, prepara bindings desde SQL parseado y corrige tipos
y advertencias Svelte. E1 ya tiene su [primera unidad de integridad](architecture/sqlviz-dashboard-integrity.md):
borrado atómico de dashboard, paneles, enlaces y memoria de filtros, con rollback
y protección frente a creación simultánea. Su [segunda unidad](architecture/sqlviz-folder-integrity.md)
protege la jerarquía y la ubicación de dashboards, con PATCH/null explícito y
conflictos concurrentes. Su [tercera unidad](architecture/sqlviz-panel-dimensions.md)
valida dimensiones, conserva el gráfico ante rechazo y separa el aprendizaje
opcional del guardado. La [primera parte de la unidad 8](architecture/sqlviz-composition-contract.md)
valida composición en HTTP y conserva los resultados de autor/viewers. El
[segundo incremento](architecture/sqlviz-dashboard-patch.md) valida PATCH de
dashboards con omisión/null y guardado atómico. El
[tercer incremento](architecture/sqlviz-panel-patch.md) valida nombre/SQL/orden
del panel y coordina edición/borrado. El
[cuarto incremento](architecture/sqlviz-panel-presentation.md) valida títulos y
etiquetas, guarda atómicamente y conserva borradores ante rechazo en el inspector
y sobre el gráfico. El [quinto incremento](architecture/sqlviz-chart-overrides.md)
valida tipos de gráfico, guarda decisiones manuales antes del aprendizaje y
confirma el gráfico/composición con reintento; reset borra el ajuste real.
La revisión pendiente de dimensiones se incorpora a S1, el lienzo persistido.
S0 ya valida doce columnas, tamaños exactos, colisiones y viabilidad de espacio;
no reemplaza los overrides legacy ni su API.
La evidencia local no reemplaza CI.

El [flujo de Git](architecture/sqlviz-git-workflow.md) recoge la autorización
permanente de gestión habitual: avisar cuándo corresponden commit/push/tag,
registrar incrementos verificados y preservar trabajo ajeno e historial compartido.

## Qué documento tiene autoridad

El código y las pruebas describen lo implementado; una especificación por sí sola
no demuestra que una capacidad exista. La auditoría tiene fecha y commit de
referencia: hay que actualizar sus estados cuando se corrijan los hallazgos.

La arquitectura objetivo establece límites entre módulos; el plan operativo del
Studio establece el orden actual. Las especificaciones describen dirección y
criterios; **no indican por sí solas funcionalidades entregadas.**
Los contratos publicados siguen vigentes hasta que una migración explícita los
reemplace. Un documento estratégico no autoriza romper el formato `.sqlviz`.

DOC1–DOC11 y el [roadmap anterior](architecture/sqlviz-roadmap.md) conservan contexto
histórico y especificaciones útiles. Sus fechas, fases y números de versión no
son una lista fiable del estado actual. En particular:

- DOC1: la restricción «SQL como única interfaz» queda reemplazada por autoría
  mediante SQL y edición visual sobre un modelo común.
- DOC7: describe seguridad deseada; la auditoría encontró rutas sin autorización.
- DOC9: investigación opcional; las afirmaciones de originalidad comercial no
  están verificadas y no deben usarse como promesas de producto.
- DOC5: su propuesta inicial de inferir todo sin configuración se sustituye por
  evidencias, alternativas/abstención y los tres niveles de autoría. El nuevo
  diseño semántico no declara que el pipeline profundo esté ya implementado.
- DOC11: catálogo de posibles capacidades; sus veinte motores y su prioridad
  anterior no constituyen un compromiso de implementación.

Todo cambio nuevo debe distinguir **observado**, **decidido para implementar**,
**hipótesis por validar** y **entregado con pruebas**.
