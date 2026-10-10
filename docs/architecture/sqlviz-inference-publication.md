# Publicación de inferencia compatible con la consulta ejecutada

**Implementado — 2026-10-09: S1.1c.2c.1a.** Primer incremento de protección de
ejecución. Una consulta puede terminar después de que otro autor cambie su SQL.
Su inferencia no debe escribirse sobre esa nueva definición ni responder como
si la publicación hubiera sido exitosa.

Este incremento protege la publicación de una consulta ejecutada por el autor.
Por sí solo no vincula todo Run con una revisión esperada; esa integración está
entregada en [1b](sqlviz-sql-execution-definition.md). El registro condicionado
sigue pendiente en el [plan operativo](sqlviz-studio-delivery-plan.md).

## Contrato y límite de la transacción

`POST /api/v1/panels/{id}/execute` conserva su cuerpo opcional de variables y su
respuesta habitual de datos/inferencia. Para una ejecución real del autor:

1. Lee el panel autorizado y captura su SQL exacto y elección manual de gráfico.
2. Prepara filtros, ejecuta en el catálogo analítico aislado e infiere, sin
   mantener abierta una transacción de metadata.
3. Abre una transacción breve en el cursor de proyecto de esa solicitud.
4. Relee panel y padre; rechaza si desaparecieron o si cambió alguno de los dos
   inputs capturados. No compara el SQL reescrito con parámetros ni un fingerprint
   semántico. La igualdad del SQL comprueba compatibilidad; nunca asigna identidad.
5. Modifica realmente la fila del padre para establecer conflicto con commit de
   script, creación y eliminación del agregado.
6. Guarda inferencia y clasificación del dashboard en esa misma transacción.
   Construye el contrato visual con tamaños y textos manuales actuales.
7. Modifica realmente la fila del panel con una condición de SQL/elección de
   gráfico, estableciendo conflicto con PATCH y borrado legacy. Solo confirma
   después de que todas las operaciones terminen correctamente.

Cambiar o retirar la elección manual de gráfico requiere reintentar: esa elección
participó en la inferencia y sus encodings. Cambios compatibles de tamaño y título
se conservan y aparecen en la respuesta. Los valores seleccionados mantienen
precedencia de los overrides sobre la inferencia.

Si los inputs cambiaron, desaparecieron o DuckDB detectó una escritura en
competencia, devuelve **409** con `code: inference_publication_conflict` y mensaje
seguro, sin SQL, valores privados ni datos de la consulta obsoleta. Revierte
inferencia, clasificación y timestamps propios; no revierte cambios confirmados
por otro editor. No reintenta automáticamente con otra definición.

El fallo del cálculo puro de clasificación sigue siendo opcional: puede guardar
la inferencia del panel sin cambiar el icono del dashboard. Los fallos de lectura,
escritura o COMMIT de metadata no se ocultan como éxito; abortan la publicación.

## Responsabilidades

- **API:** autorización, preparación/ejecución/inferencia, cálculo de
  clasificación y construcción de respuesta.
- **Almacenamiento:** `inference_publication` valida inputs y posee la transacción
  y sus barreras de escritura. No importa FastAPI ni ejecuta SQL del usuario.
- **Primitiva de inferencia:** `store_inference` conserva su API interna y
  precedencia de overrides. No posee una transacción; el endpoint la invoca dentro
  de la protección anterior, junto con las operaciones relacionadas.
- **Motor analítico:** conserva su catálogo aislado, presupuestos y parámetros.
  No se prolonga la transacción de proyecto durante el cálculo analítico.

No cambia el esquema del archivo ni requiere migración. Las operaciones se
prueban en proyectos sintéticos y cursores independientes, sin tocar el proyecto
o la base de aprendizaje reales del usuario.

## Evidencia

Pruebas de almacenamiento y HTTP verifican SQL cambiado o eliminado, padre
eliminado, cambio/reset de gráfico, tamaño/título compatibles, variables,
escritura competidora confirmada después de la lectura inicial, escritura retenida,
rollback completo, fallos de clasificación/COMMIT, conexión reutilizable y
reapertura. También verifican que otro dashboard pueda seguir escribiendo y que
viewer/solicitudes anónimas no publiquen inferencia.

La validación del endpoint se realiza además sobre el recorrido de Run con el
frontend de producción, en una copia aislada. Artefactos de revisión en
`build/inference-publication-review/`, ignorados por Git.

Validación del incremento: **2.473 pruebas Python aprobadas y 3 omitidas**;
Ruff y mypy sin errores (149 archivos fuente). Chromium verifica cinco commits
atómicos de Run, conservación de overrides, reintentos, cancelación y eliminación
explícita, también en móvil; ninguna escritura individual de paneles desde Run
y ningún error JavaScript. No hay cambios de frontend en este incremento.

## Alcance de 1a y trabajo posterior

**1b entregado:** [referencia de definición de Run](sqlviz-sql-execution-definition.md)
cubre ejecución/composición y fallback ligados al commit; amplía la barrera de
escritura a los paneles vecinos del script. Los siguientes límites describen
1a usado por sí solo, sin esa referencia, y los caminos legacy.

Esto no entrega aislamiento de un lote de consultas. Cada solicitud todavía
empieza leyendo la definición actual: si cambia entre el commit de Run y esa
lectura, puede ejecutar SQL distinto del que el navegador esperaba. La protección
entregada comprueba los inputs capturados por el servidor para esa consulta.

Tampoco protege aún composición, caché, respuestas sin ejecución efectiva
(fallback de sintaxis/filtros), resultados de lectores ni el PATCH legacy de
`last_run_at`/`last_run_sql`. Las modificaciones posteriores al COMMIT de
publicación pueden volver obsoleto un resultado ya enviado. No hay snapshot común
de los datos para todo el dashboard, ni una revisión publicada del viewer.

La clasificación se calcula con las filas visibles en su transacción; no congela
las definiciones de otros paneles ante todos los PATCH legacy. La condición de
inputs no pretende detectar toda transición SQL A → B → A ni sustituye una
referencia de definición del script.

La referencia futura debe distinguir definiciones de metadata derivada. El token
de snapshot actual incluye timestamps e inferencia: cambia tras una publicación
normal y no puede reutilizarse sin más como referencia esperada del lote.

**Siguiente: S1.1c.2c.1c**, registro de éxito condicionado del lado servidor antes
de continuar con recarga y recuperación.
