# Documentación de SQLviz

Actualizada: **2026-10-07**.

## Orden de lectura

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
visualización, con precedencia, persistencia y restauración. Adelanta el contrato
mínimo de dataset reutilizable a E1 antes del lienzo; estas capacidades siguen
pendientes de implementación.

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
Su orden está en el [plan inmediato después de navegación](architecture/sqlviz-product-roadmap.md#plan-inmediato-después-de-navegación).

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
siguiente foco es PATCH de otros campos, antes del contrato visual.
La evidencia local no reemplaza CI.

El [flujo de Git](architecture/sqlviz-git-workflow.md) recoge la autorización
permanente de gestión habitual: avisar cuándo corresponden commit/push/tag,
registrar incrementos verificados y preservar trabajo ajeno e historial compartido.

## Qué documento tiene autoridad

El código y las pruebas describen lo implementado; una especificación por sí sola
no demuestra que una capacidad exista. La auditoría tiene fecha y commit de
referencia: hay que actualizar sus estados cuando se corrijan los hallazgos.

La arquitectura objetivo y el nuevo plan de entregas establecen la dirección
recomendada a partir de esta revisión. **No indican funcionalidades ya entregadas.**
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
- DOC11: catálogo de posibles capacidades; sus veinte motores y su prioridad
  anterior no constituyen un compromiso de implementación.

Todo cambio nuevo debe distinguir **observado**, **decidido para implementar**,
**hipótesis por validar** y **entregado con pruebas**.
