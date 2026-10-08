# Autoría visual: automático, builder y ECharts nativo

**Decisión aceptada por el usuario:** 2026-10-07.
**Estado:** diseño para implementar. Este documento no entrega nuevos controles,
datasets persistidos ni un editor experto. Prevalece sobre la exclusión anterior
de opciones nativas en la especificación del Studio.

## Experiencia y alcance

SQL produce datos; la inferencia propone una visualización; el autor la ajusta.
La experiencia inicial sigue siendo ejecutar una consulta y obtener un gráfico,
sin exigir crear métricas, modelos semánticos o datasets compartidos antes.

| Nivel | Experiencia prevista |
| --- | --- |
| Básico — Automático | Recomendación completa con campos, series y explicación; aceptar o escoger una alternativa |
| Intermedio — Visual Builder | Controles para datos, visual, formato e interacción, con restauración explícita a automático |
| Experto — ECharts native options | Inspeccionar la configuración generada, editar opciones nativas JSON, validar y revisar antes de aplicar |

Los niveles trabajan sobre la misma visualización. Abrir el editor experto no
convierte automáticamente todo el gráfico ni descarta la configuración visual.
Los ajustes se guardan, reabren y representan también en el viewer. La UI revela
opciones avanzadas bajo demanda; no incorpora tres espacios de trabajo obligatorios.

## Motor y contratos

Mantener ECharts como motor inicial. Su configuración nativa puede formar parte
del contrato de renderizado; SQLviz conserva identidad, dataset/revisión,
bindings, procedencia de los ajustes, layout y publicación. El Visual Builder
modela las propiedades que sabe editar, sin duplicar toda la gramática del motor.
El contrato existente `VisualSpec` conserva su compatibilidad hasta una migración
explícita; la aceptación de este diseño no cambia su versión ni el archivo `.sqlviz`.

Vega-Lite y Vega son alternativas válidas para describir gráficos. Vega-Lite
compila a Vega; escogerlo para renderizar con ECharts añadiría una traducción que
habría que desarrollar y evaluar. No introducir esa traducción ni otro renderer
en este incremento. Referencias: [Vega-Lite](https://vega.github.io/vega-lite/),
[compilación a Vega](https://vega.github.io/vega-lite/usage/compile.html),
[Vega](https://vega.github.io/vega/).

## Identidad y reutilización

Separar cuatro responsabilidades en el modelo objetivo:

| Objeto | Responsabilidad |
| --- | --- |
| Dataset + revisión | Definición de datos: fuente, consulta, esquema, parámetros y granularidad; no confundirlo con el resultado de una ejecución |
| Visualización + revisión | Dataset/bindings, recomendación, ajustes del builder y opciones expertas |
| Panel | Instancia de la visualización dentro de un dashboard, con ID estable, posición y tamaño |
| Dashboard + revisión | Composición, filtros y referencias explícitas a revisiones de visualizaciones |

Un dataset puede alimentar varios gráficos sin duplicar su definición. Reutilizar
una visualización no permite que editarla cambie silenciosamente dashboards ya
publicados: sus referencias deben fijar revisiones. Actualizar una referencia
es una acción explícita con preview y validación de dependencias.

Se puede promover una consulta de exploración a dataset reutilizable. Incorporar
su contrato mínimo junto con identidad y persistencia visual antes del lienzo;
el catálogo completo, conectores y métricas siguen sus fases posteriores. Polars,
el DAG de transformaciones y la IA no forman parte de este primer contrato.

## Precedencia y edición reversible

La configuración efectiva combina la propuesta aceptada, las elecciones del
builder y las opciones expertas. Las opciones expertas prevalecen en las
propiedades que modifican; la UI identifica su procedencia. SQLviz no mantiene
dos valores efectivos independientes para una misma propiedad.

- Guardar por separado ajustes del builder y ajustes expertos, con versión de
  contrato y compatibilidad del motor declaradas.
- Usar IDs estables para series/componentes. Definir sustitución, eliminación y
  conflicto de listas antes de implementar; un deep merge genérico o posiciones
  de arrays no constituyen una política de edición.
- Conservar personalizaciones al ejecutar, filtrar o recibir recomendaciones.
  Un esquema incompatible produce un diagnóstico; no reasignar campos por orden
  ni restaurar valores sin decisión del autor.
- Los controles que no puedan representar una opción experta explican ese límite
  y conservan la opción. No prometer conversión completa de cualquier configuración
  ECharts a controles visuales.
- Restablecer un ajuste experto revela el valor del builder o automático que
  corresponda. Volver a automático y salir de una configuración experta completa
  son operaciones explícitas, reversibles y con preview.
- Aplicar cambios solo después de validar el conjunto. Un error conserva la
  última visualización confirmada; el borrador inválido sigue editable.

El editor experto comienza con JSON nativo serializable y asistencia de edición.
La política validada debe cubrir propiedades de presentación, encoding, series
e interacciones soportadas, sin reducir este nivel a unos pocos ajustes cosméticos.
La identificación de propiedades no representables y la política de conflictos
son requisitos del contrato que se implementará, no capacidades ya existentes.

Los datos efectivos y su autorización siguen bajo control del runtime de SQLviz;
editar opciones no autoriza otra fuente ni amplía permisos. ECharts permite separar
datos y configuración mediante [dataset y encode](https://echarts.apache.org/handbook/en/concepts/dataset/).
Un JSON válido no basta: validar estructura, capacidades y referencias antes de
guardarlo y renderizarlo. No persistir el resultado de `getOption()` como sustituto
de la intención del autor ni insertar resultados de consultas dentro del documento
de opciones expertas.

Funciones JavaScript y HTML arbitrarios quedan fuera del editor JSON inicial;
no evaluar strings como código. Su futura ejecución requiere una decisión y
aislamiento propios. Procesar opciones con HTML/URLs conforme a la
[guía de seguridad de ECharts](https://echarts.apache.org/handbook/en/best-practices/security/).

## Cierre y orden de entrega

Continuar con PATCH de dashboards y luego paneles; completar migraciones y
dependencias; entregar identidad, dataset mínimo y configuración visual;
después implementar builder/lienzo, inferencia completa y editor experto por
incrementos pequeños. Ver el [plan vigente](sqlviz-product-roadmap.md).

Para cerrar el nivel experto deben pasar: guardado/reapertura, mismos resultados
en editor/viewer, filtros y refresh sin pérdida de ajustes, precedencia visible,
series reordenadas sin transferir personalizaciones, reset/undo, cambios de esquema
incompatibles, rechazo atómico y validación negativa de contenido no soportado.
Preview y publicación usan la misma revisión y compatibilidad del renderer.

El caso inicial recorre automático → series desde el builder → opciones nativas
para una línea de referencia → guardar → filtrar → reabrir → viewer → reset/undo,
sin pérdida de datos ni configuración. Su evidencia se añadirá al implementarlo.
