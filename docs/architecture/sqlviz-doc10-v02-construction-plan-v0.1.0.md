# SQLviz — V0.2 Construction Plan: Cognitive Dashboard Compiler
**Version:** v0.1.0
**Status:** FROZEN — Plan oficial de V0.2
**Last Updated:** 2026-07-04
**Prerequisites:** DOC 1–8 (todos los documentos de V0.1), código real de V0.1 (`594/601` tests, ruff/mypy limpios)

---

## 0. Document Status — Frozen for V0.2

> Este documento es el resultado de una auditoría fusionada sobre el
> código real de V0.1 (`sqlviz.zip`): inspección directa del repositorio
> más revisión cruzada independiente (confirmó `306/306` tests de
> `sqlviz-inference` de forma separada). Donde las dos auditorías
> coincidían, se fusionaron. Donde diferían, la diferencia se resolvió
> explícitamente (sección 2). El resultado es el plan que las dos
> auditorías juntas revelan — ninguna de las dos sola era suficiente.
>
> **Este no es un documento de visión. Es un plan de trabajo.**
> El status FROZEN significa: no se empieza a construir V0.2 revisando
> este documento — se empieza a construir contra él.

```
Documento                                    Status         Frozen para
──────────────────────────────────────────────────────────────────────
DOC  1 — Vision & Philosophy                 Stable         V0.1 / V0.2
DOC  2 — Modes & CLI                         Stable         V0.1
DOC  3 — Technical Stack                     Stable         V0.1
DOC  4 — Mathematical Foundations            Stable         V0.1
DOC  5 — Inference Engine Architecture       Stable         V0.1
DOC  6 — UI Design System                    Stable         V0.1
DOC  7 — Security & Roles                    Stable         V0.1
DOC  8 — V0.1 Construction Plan              Stable         V0.1
DOC  9 — Cognitive BI Vision                 Stable         V0.3+
DOC 10 — V0.2 Construction Plan (este doc)   FROZEN         V0.2
```

```
Qué significa FROZEN aquí:
    DOC 10 es la única fuente de verdad para qué se construye en V0.2
    y en qué orden. Cambios durante V0.2 deben ser RAROS y deben
    registrarse como correcciones explícitas en la sección 0.1, nunca
    como una reescritura silenciosa.

    FROZEN no significa perfecto — cada fase tiene sus propios deferred
    explícitos. El freeze significa: ninguna gap nueva aparece
    silenciosamente una vez que Fase 0 comienza.
```

### 0.1 Historial de revisiones

```
Auditoría A (código real, autor):
    Inspección directa del ZIP del repositorio V0.1.
    594/601 tests pasan (7 fallos son DuckDB postgres sandbox sin red —
    no aplica en desarrollo local). ruff/mypy: 0 findings. Benchmark gold
    30 casos → 100%. Benchmark adversarial 42 casos → 100%.
    Veredicto: 70% mantener / 30% rehacer (medido en paquetes/archivos).

Auditoría B (revisión cruzada independiente):
    Misma fuente (ZIP). Confirmó 306/306 tests de sqlviz-inference
    de forma independiente. Veredicto: 45% mantener / 25% reescribir /
    30% construir desde cero (medido en lógica de decisión).

Fusión (este documento):
    Las dos métricas no se contradicen — miden dimensiones distintas.
    Resolución explícita en sección 2.3. Resultado: este plan.
```

---

## 1. Propósito de este documento

Este documento responde una sola pregunta:

> "En qué orden exacto se convierte `sqlviz-inference` en el
>  Cognitive Dashboard Compiler, y qué pertenece a V0.2?"

DOC 8 respondió esa pregunta para V0.1. Este documento la responde
para V0.2. El alcance es deliberadamente delimitado:

```
DOC 8  → plan de construcción V0.1  (el motor de reglas que funciona)
DOC 10 → plan de construcción V0.2  (convertir ese motor en un
                                      Cognitive Dashboard Compiler)

No reconstruir SQLviz.
No tocar sqlviz-core, sqlviz-storage, sqlviz-api base, sqlviz-cli.
Convertir sqlviz-inference — empezando por los dos contratos.
```

---

## 2. Diagnóstico del estado de V0.1

### 2.1 Verificado por código, no por documentación

```
594/601 tests pasan
  (7 fallos: DuckDB postgres extension sin red — no aplica en desarrollo)
306/306 tests de sqlviz-inference
  (confirmado independientemente por dos auditorías distintas)
ruff check .          →  0 findings
mypy (5 paquetes)     →  0 errores, 73 archivos
Benchmark gold        →  30/30 casos, 100% intent accuracy, 100% chart accuracy
Benchmark adversarial →  42/42 casos, 100% pass
```

### 2.2 Por qué esto es "un motor de reglas V0 bien construido", no un sistema cognitivo

```
Genera un único score por chart y toma el máximo —
    no un conjunto de candidatos que compiten con razones explícitas.

Mezcla restricciones duras ("esto es imposible") con preferencias
    blandas ("esto es preferible") en el mismo mecanismo de resta de
    penalización — no hay separación entre eliminar y ordenar.

Decide layout por tabla fija chart_type → tamaño, sin mirar
    cardinalidad real, longitud de labels, ni cantidad de series.

Decide cada panel aislado —
    no hay noción de "el dashboard como conjunto".

brain.duckdb existe pero está vacío a propósito
    ("deferred to V0.3" dice el propio código) — cero aprendizaje.

Explica con score_trace técnico (affinity_score, penalty_total) —
    útil para debug, no es explicación para el usuario final.
```

### 2.3 Reconciliación de los dos verdíctos cuantitativos

Las dos auditorías dieron números distintos. No se contradicen:

```
70% mantener / 30% rehacer
    Mide cuántos PAQUETES/ARCHIVOS se tocan en absoluto.
    sqlviz-core, storage, api, cli no se tocan → 70% "sano".

45% mantener / 25% reescribir / 30% construir
    Mide cuánta LÓGICA DE DECISIÓN sobrevive dentro de los archivos
    que sí se tocan. chart_engine.py, layout_engine.py,
    dashboard_engine.py cambian tan profundamente que "reescribir"
    es más preciso que "extender".
```

El número que importa para planear el trabajo es el segundo, porque
el 70% intacto no es donde se va a pasar el tiempo — se va a pasar
el tiempo en el 25%+30% que sí cambia.

---

## 3. El principio estratégico que ordena todo lo demás

Antes del veredicto por componente, esto es lo más importante de V0.2:

> **Lo primero que hay que fijar no es "qué tan inteligente es la
> decisión". Es el contrato de entrada y el contrato de salida del
> cerebro.**

```
Contrato de entrada:  DataProfile   (qué sabemos de los datos, siempre
                       igual de rico, sin importar qué lógica de decisión
                       corra después)

Contrato de salida:   VisualSpec    (qué recibe el frontend, siempre
                       igual de completo, sin importar si lo generó una
                       regla simple o un optimizador multicriterio)
```

Mientras esos dos contratos no existan, cada mejora al "cerebro" de
en medio es un parche pegado a la implementación actual de `ChartEngine`
y `EChartsRenderer`. Si primero se fijan los contratos, el cerebro se
puede reemplazar en fases sin romper nada arriba ni abajo.

**Consecuencia directa para el roadmap:** `VisualSpec` + `DataProfile`
se construyen en Fase 0, antes que `ConstraintEngine`, antes que
`ScoringModel`, antes que cualquier otra cosa. El `ChartEngine` de V0.1
sigue siendo el que llena el `VisualSpec` temporalmente mientras el
resto del cerebro se construye al lado.

---

## 4. Fundamentos de investigación

Cada módulo nuevo de V0.2 traduce una línea de investigación existente
a algo construible por una sola persona. Las fuentes fundamentan por qué
las reglas son las que son — no son arbitrarias:

```
CompassQL / Voyager  (Wongsuphasawat et al., 2016 — UW/Tableau Research)
    Especificación parcial de visualización + enumeración de candidatos
    con ranking perceptual.
    → Fundamenta: VisualizationCandidateGenerator + ScoringModel
      (dimensión perceptual_accuracy).

Draco  (Moritz et al., 2019 — UW/Tableau Research)
    Reglas de diseño visual formalizadas como restricciones
    (Answer Set Programming).
    → Fundamenta: ConstraintEngine — traducido de ASP a YAML explícito,
      ejecutable sin un solver externo.

GraphScape  (Chen et al.)
    El espacio de visualizaciones como grafo de transformaciones.
    → Fundamenta: cómo DashboardLayoutOptimizer explora combinaciones
      de layout sin fuerza bruta.

VizML  (Hu et al., 2019 — MIT)
    Aprendizaje de decisiones de visualización desde corpus reales.
    → Fundamenta: FeedbackEngine — a escala de una sola instalación
      (brain.duckdb) en vez de un corpus masivo. El mecanismo de
      aprendizaje por corrección es el mismo principio.

Cleveland & McGill (1984), Heer & Bostock (2010)
    Jerarquía de precisión perceptual: posición > longitud > ángulo
    > área > color.
    → Base cuantitativa de ReadabilityModel y de la dimensión
      perceptual_accuracy en ScoringModel.

Sweller (1988) — Cognitive Load Theory; Miller (1956) — 7±2
    → Base de la dimensión cognitive_load en ScoringModel y del
      presupuesto de "chunks" por dashboard en DashboardObjective.
```

Estos fundamentos delimitan el alcance: no hace falta implementar un
solver ASP (Draco completo) ni un corpus de entrenamiento (VizML
completo). La versión "una persona, sostenible" de cada idea alcanza.

---

## 5. Veredicto por componente

### 5.1 Mantener sin modificar

| Componente | Justificación |
|---|---|
| `sqlviz-core` | No conoce nada de inferencia. No cambia. |
| `sqlviz-storage` | Extensión de superficie (campos nuevos en sección 8.1). No cambia de paradigma. |
| `sqlviz-api` (rutas base) | Las rutas de CRUD y auth no cambian. La ruta de ejecución de paneles se extiende para pasar `DataProfile` y recibir `VisualSpec` — no se reescribe. |
| `sqlviz-cli` | No conoce nada de inferencia. |
| Monorepo de 6 paquetes | La separación de responsabilidades es correcta para la arquitectura avanzada. No fusionar ni reestructurar. |
| Filosofía SQL-first | Es la ventaja competitiva del proyecto. No se introduce drag-and-drop ni field picker. |
| DuckDB como motor único | No cambiar a SQLite, no sumar motores extra. |
| FastAPI + SvelteKit + ECharts | El problema no está en el stack, está en el cerebro visual. |
| `.sqlviz` → Project → Dashboard → Panel → SQL | Extender el modelo (sección 8), no reestructurar la jerarquía. |
| `RuntimeContext` (field-owned mutation) | Patrón correcto para que el pipeline crezca sin que los módulos se pisen. Se le agregan campos, no se reescribe. |
| `yaml_loader` singleton | El mismo mecanismo sirve para las 6+ YAML nuevas. |
| `SQLParser` / `ast_helpers.py` / `fingerprint.py` | La extracción de AST es correcta. Su salida se consolida en un `SQLProfile` explícito (sección 6.1), no se reescribe la extracción. |
| Gold dataset + benchmark adversarial (infraestructura) | Se extiende con casos nuevos por fase (Fase G). La infraestructura de medición es la única fuente de verdad de si un cambio mejora algo. |

### 5.2 Reescribir profundamente — archivo por archivo

#### `chart/chart_engine.py`

```
Hoy:    un solo método hace afinidad + penalización + clamp +
        selección de ganador + alternativas, todo junto.

V0.2:   se achica a solo generación de candidatos + semantic_fit
        (la afinidad actual es una señal válida — se reutiliza).
        Penalización, clamp y selección de ganador se eliminan de aquí
        y pasan a ConstraintEngine + ScoringModel.
        chart_affinity_matrix.yaml sobrevive como fuente de semantic_fit.
        La lista de charts soportados se amplía.
```

#### `layout/layout_engine.py`

```
Hoy:    lookup fijo chart_type → (col_span, row_span).

V0.2:   eliminado como motor de decisión final. Su tabla de valores
        por defecto se conserva como fallback de último recurso dentro
        del nuevo LayoutOptimizer (graceful degradation — principio
        ya establecido en DOC 1).
```

#### `dashboard/dashboard_engine.py`

```
Hoy:    orden narrativo fijo + packing secuencial de filas de 12 cols.

V0.2:   el orden narrativo básico (KPIs arriba) se mantiene como
        restricción dura dentro del optimizador nuevo.
        El packing deja de ser secuencial y pasa a ser el resultado de
        DashboardLayoutOptimizer evaluando todos los paneles a la vez,
        calificado por DashboardObjective.
```

#### `EChartsRenderer.svelte`

```
Hoy:    patrón "primera columna = x, última columna = y" — el renderer
        infiere columnas desde los datos.

V0.2:   el renderer no infiere nada. Recibe VisualSpec completo y
        solo dibuja. Este es, junto con DataProfile, uno de los dos
        contratos prioritarios (sección 3).
```

#### `result.py` (`InferenceResult`)

```
Hoy:    estructura plana.

V0.2:   estructura por capas: perfil de datos, candidatos con desglose
        de score, spec visual, declaración de layout, explicación
        estructurada.
        chart_winner se mantiene por compatibilidad hacia atrás, deja
        de ser el campo principal.
        Nuevo esquema completo en sección 8.2.
```

### 5.3 Construir desde cero — 16 módulos nuevos

Ver sección 6. Construidos en el orden de dependencia real de la
sección 7 (pipeline de 16 pasos).

### 5.4 Diferir explícitamente — no en V0.2

```
Knowledge Graph completo con razonamiento sobre el grafo
    (entidades de negocio + relaciones + inferencia) →  V0.3/V1.0
    Para V0.2 alcanza con un mapa de relaciones en YAML (sección 6.3).

brain.duckdb aprendizaje bayesiano / Thompson sampling          →  V0.3
    DOC 5 sección 16.4. En V0.2 FeedbackEngine guarda y aplica
    correcciones directas; el aprendizaje estadístico completo es V0.3.

Insight Engine / Narrative Engine / Semantic Engine V1          →  V0.3
    DOC 5 sección 16.4. No en V0.2.

Cross-filtering entre paneles                                   →  V0.2 final / V0.3
    DOC 5 sección 15.7. Depende de que DashboardObjective esté estable.
```

---

## 6. Los 16 módulos nuevos — Cognitive Dashboard Compiler

Cada módulo: responsabilidad, entrada, salida, fundamento de
investigación, y qué de V0.1 reutiliza.

### 6.1 `SQLProfile` + `ResultProfiler` / `DataProfile` — el más urgente

```
Dos objetos distintos, y la distinción importa:

SQLProfile   →  qué DICE el SQL (agregaciones, GROUP BY, ORDER BY,
                window functions, CTEs) — se construye del AST,
                antes de ejecutar.

DataProfile  →  qué MUESTRAN los datos reales (row_count, cardinalidad
                real, longitud de labels, nulls, single-row,
                wide-table) — se construye del resultado, después de
                ejecutar.

El SQL puede sugerir una cosa y los datos reales contradecirla.
Por eso son dos perfiles separados, no uno solo.

Urgencia: sin DataProfile confiable, todos los módulos que se
construyan encima heredan la fragilidad de inferir solo desde el SQL.

Reutiliza: data_statistics.py ya calcula buena parte de esto —
se consolida y enriquece en un objeto explícito en vez de vivir
disperso en el vector de 39 dims.
```

### 6.2 `ColumnRoleDetector`

```
Responsabilidad: clasifica cada columna por rol estructural
    (metric, dimension, time, id, percentage, rank, category)
    usando nombre + estadísticas + posición en el AST.
    No solo tipo físico — cliente_id INTEGER no es una métrica.

Reutiliza: semantic_dictionary.yaml + ast_helpers.py
    (detectar si la columna viene de RANK()/SUM()/etc.)
```

### 6.3 `SemanticProfile` (Business Ontology — versión ligera V0.2)

```
Responsabilidad: conecta columnas con conceptos de negocio y sus
    relaciones (cobrado <= facturado,
    recuperación = cobrado / facturado).

Alcance V0.2: mapa de relaciones en YAML.
    Un Knowledge Graph completo con razonamiento es V0.3.

Reutiliza: semantic_dictionary.yaml como base.
```

### 6.4 `AnalyticalIntentModel`

```
Responsabilidad: reemplaza al IntentEngine como motor de decisión
    final. El IntentEngine actual se mantiene como generador de
    señales de evidencia — AnalyticalIntentModel los consume.

Salida: intent primario, intents secundarios, evidencia a favor y
    en contra, propiedades visuales que requiere ese intent.
    No solo una etiqueta con un score.
```

### 6.5 `VisualizationCandidateGenerator`

```
Responsabilidad: genera el conjunto de candidatos posibles a partir
    de DataProfile + SemanticProfile + AnalyticalIntentModel.
    No decide — propone.

Fundamento: CompassQL/Voyager (sección 4).
```

### 6.6 `ConstraintEngine`

```
Responsabilidad:
    Reglas DURAS (eliminan candidatos):
        pie con > N categorías
        line sin eje temporal confirmado en DataProfile
        scatter sin dos columnas numéricas
        kpi con más de una fila

    Reglas BLANDAS (penalizan sin eliminar):
        preferencias de legibilidad, alineación semántica

    Separación explícita de los dos tipos — es lo que V0.1 no tiene.

Fundamento: Draco (sección 4) — restricciones formales sin solver ASP.
```

### 6.7 `ReadabilityModel`

```
Responsabilidad: traduce cardinalidad, longitud de labels, cantidad
    de series y puntos en un ancho mínimo/preferido/máximo de
    columnas y una altura recomendada.

Orden de ejecución: corre ANTES que ScoringModel (sección 7, paso 8),
    porque ScoringModel consume readability como una de sus
    dimensiones de entrada.

Fundamento: Cleveland & McGill, Heer & Bostock (sección 4).
```

### 6.8 `ScoringModel`

```
Responsabilidad: reemplaza afinidad-menos-penalización por un score
    multicriterio explícito con dimensiones separadas.

Score = semantic_fit
      + task_fit
      + perceptual_accuracy
      + readability          ← resultado de 6.7
      + information_density
      + business_relevance
      − cognitive_load
      − visual_clutter
      − ambiguity
      − interaction_cost

Cada dimensión debe poder mostrarse por separado en el desglose.

Fundamento: Sweller/Miller para cognitive_load (sección 4).
Reutiliza: semantic_fit de chart_affinity_matrix.yaml (señal válida
    que no se descarta — se incorpora como una de las 10 dims).
```

### 6.9 `VisualSpecBuilder`

```
Responsabilidad: construye el contrato exacto que el frontend
    renderiza sin adivinar nada.

Contiene: campo en x, campos en y, stacking, orientación, sort,
    formato de ejes, tooltip, paleta.

Este es, junto con DataProfile, uno de los dos contratos prioritarios
    (sección 3). Se puede construir en Fase 0 usando chart_winner de
    V0.1 como decisión interina mientras el resto del cerebro se
    construye al lado.

Corresponde a la reescritura de EChartsRenderer (sección 5.2).
```

### 6.10 `LayoutDeclarationBuilder` + `DashboardRoleClassifier`

```
LayoutDeclarationBuilder:
    Cada panel declara ancho/alto mínimo-preferido-máximo basado en
    ReadabilityModel + tipo de chart.

DashboardRoleClassifier:
    Asigna a cada panel un rol narrativo:
        resumen_ejecutivo, historia_principal, explicacion_secundaria,
        diagnostico, tabla_de_detalle, control.
    El rol influye en la prioridad de posición en el optimizador.
```

### 6.11 `DashboardLayoutOptimizer`

```
Responsabilidad: reemplaza layout_engine.py + la lógica de packing
    de dashboard_engine.py. Recibe todos los paneles con sus
    declaraciones de layout y roles, y decide fila, posición, ancho
    y alto como un problema conjunto — no uno por uno.

Fundamento: GraphScape para exploración del espacio de combinaciones
    sin fuerza bruta (sección 4).
```

### 6.12 `DashboardObjective`

```
Responsabilidad: evalúa si el dashboard COMPLETO es bueno —
    no solo si cada panel individual está bien.

Utilidad = comprensión
          + fidelidad_semántica
          + legibilidad
          + coherencia_narrativa
          + cobertura_de_información
          + prioridad_de_negocio
          − carga_cognitiva
          − clutter
          − redundancia
          − espacio_desperdiciado
```

### 6.13 `InformationGainEngine`

```
Responsabilidad: detecta paneles redundantes (¿el panel B dice lo
    mismo que A con otro corte?) y sugiere bajar prioridad,
    mover abajo, o convertir a tabla secundaria.
```

### 6.14 `FeedbackEngine`

```
Responsabilidad: guarda cada corrección del usuario (chart, ancho,
    alto) con fingerprint de SQL/datos/semántica, y ajusta
    inferencias futuras sobre patrones similares.

brain.duckdb ya existe vacío, preparado exactamente para esto.
Fundamento: VizML a escala de una instalación (sección 4).

Nota de alcance: aprendizaje estadístico completo (bayesiano /
    Thompson sampling) es V0.3. V0.2 implementa la capa de
    almacenamiento y aplicación directa de correcciones.
```

### 6.15 `OverrideSystem`

```
Responsabilidad: capa de storage + API que separa siempre los tres
    estados de cada decisión:
        inferred_*     →  lo que el motor decidió
        selected_*     →  lo que está activo ahora
        user_override  →  lo que el usuario corrigió explícitamente

    Para chart, ancho y alto de cada panel.

Nota de posición en el pipeline: OverrideSystem no es parte del
    pipeline de inferencia (sección 7) — vive en storage/API, se
    activa cuando el usuario corrige algo DESPUÉS de que el
    pipeline ya corrió.
```

### 6.16 `ExplanationEngine` V2

```
Responsabilidad: convierte razones de ConstraintEngine + ScoringModel
    en explicación de analista:
        "Elegí barra horizontal porque las 14 categorías hacen que
         las etiquetas del eje X se solapen en orientación vertical,
         y la longitud de los valores sugiere comparación, no parte
         de un todo."

    No el score_trace técnico crudo — lenguaje natural sobre las
    razones que ya generan ConstraintEngine y ScoringModel.
```

---

## 7. El pipeline correcto de 16 pasos

El orden está determinado por dependencia real de datos: qué módulo
necesita la salida de cuál. No es un orden arbitrario.

```
Paso  Módulo                            Entrada                 Salida
──────────────────────────────────────────────────────────────────────
 1    SQLProfile                        AST (pre-ejecución)     SQLProfile
 2    DataProfile / ResultProfiler      Resultado real          DataProfile
 3    ColumnRoleDetector                SQLProfile + DataProfile ColumnRoles
 4    SemanticProfile                   ColumnRoles +           SemanticProfile
                                        semantic_dict.yaml
 5    AnalyticalIntentModel             SQLProfile +            IntentResult
                                        DataProfile +
                                        SemanticProfile
 6    VisualizationCandidateGenerator   DataProfile +           [ChartCandidate]
                                        SemanticProfile +
                                        IntentResult
 7    ConstraintEngine                  [ChartCandidate] +      [ChartCandidate]
                                        DataProfile             (filtrados)
 8    ReadabilityModel                  [ChartCandidate]        ReadabilityResult
                                        post-filtrado +         por candidato
                                        DataProfile
 9    ScoringModel                      [ChartCandidate] +      [ChartCandidate]
                                        ReadabilityResult +     (rankeados,
                                        IntentResult            con score desglosado)
10    VisualSpecBuilder                 Candidato ganador       VisualSpec
                                        (top-1 de paso 9)
11    LayoutDeclarationBuilder +        VisualSpec +            LayoutDeclaration
      DashboardRoleClassifier           DataProfile +           + DashboardRole
                                        chart_scores
12    DashboardLayoutOptimizer          [LayoutDeclaration]     DashboardPlan
                                        (todos los paneles
                                        juntos)
13    DashboardObjective                DashboardPlan +         utility_score
                                        [VisualSpec]            + ajustes
14    InformationGainEngine             [VisualSpec] +          RedundancyReport
                                        DashboardPlan
15    ExplanationEngine V2              ConstraintReport +      Explanation
                                        ChartScores +           (lenguaje natural)
                                        AnalyticalIntentModel
16    FeedbackEngine                    VisualSpec +            (persiste en
      (post-ejecución)                  DashboardPlan +         brain.duckdb)
                                        fingerprints
──────────────────────────────────────────────────────────────────────

OverrideSystem: no es parte de este pipeline.
    Vive en storage/API. Se activa cuando el usuario corrige algo
    después de que el pipeline ya corrió.
```

**Corrección de orden documentada aquí explícitamente:**
`ReadabilityModel` (paso 8) corre **antes** que `ScoringModel`
(paso 9), porque `ScoringModel` consume `readability` como una de
sus 10 dimensiones de entrada. El orden inverso es un bug
arquitectónico — `ScoringModel` no puede calificar legibilidad de
lo que no ha sido medido aún.

---

## 8. Fases de construcción — V0.2

Cada fase produce algo ejecutable y testeable. Ninguna fase comienza
hasta que pasen los exit criteria de la anterior.

### Fase 0 — Contratos de entrada y salida (PRIMERA — antes que todo)

```
Goal:    DataProfile y VisualSpec existen como contratos.
         EChartsRenderer ya no adivina columnas.
         El pipeline de V0.1 sigue siendo el cerebro —
         pero ahora habla en VisualSpec.

Tareas:
1. Implementar DataProfile (módulo 6.1 — solo el objeto de datos
   post-ejecución, no el AnalyticalIntentModel que lo consume).
   ResultProfiler calcula row_count, cardinalidad por columna,
   longitud de labels, nulls, single-row, wide-table.

2. Implementar VisualSpec: el contrato completo de lo que necesita
   EChartsRenderer para dibujar sin inferir nada.
   Campos mínimos: chart_type, x_field, y_fields, orientation,
   sort_order, color_field, stack, number_format, tooltip_fields.

3. Implementar VisualSpecBuilder (módulo 6.9) conectado al
   chart_winner de V0.1 como decisión interina — el builder
   construye el VisualSpec usando la decisión actual del ChartEngine.
   Esto NO cambia qué chart se elige; cambia cómo se comunica
   esa decisión al frontend.

4. Reescribir EChartsRenderer.svelte para consumir VisualSpec en
   vez de inferir columnas del resultado crudo.

5. Extender RuntimeContext con DataProfile como campo de primera
   clase (field-owned mutation — mismo patrón de DOC 5, sección 3).

Exit criteria:
✓ EChartsRenderer no contiene ninguna lógica de inferencia de
  columnas — cero lógica de "primera columna = x" en el componente
✓ 100% de los 8 chart types de V0.1 renderizan correctamente
  desde VisualSpec (verificación visual + test de integración)
✓ DataProfile se construye correctamente para los 30 casos del
  benchmark gold
✓ Ningún test existente falla — el cerebro de V0.1 sigue siendo
  el que decide, solo cambia el contrato de salida
```

### Fase A — Contratos internos restantes (tipos sin implementación)

```
Goal:    Todos los tipos de datos de V0.2 existen como dataclasses
         tipadas. Sin lógica de implementación todavía — solo los
         contratos que los módulos de las fases siguientes
         van a producir y consumir.

Tareas:
1. SQLProfile              — salida del parser enriquecido
2. ColumnRoles             — salida de ColumnRoleDetector
3. SemanticProfile         — salida de SemanticProfile
4. IntentResult V2         — salida de AnalyticalIntentModel
5. ChartCandidate V2       — candidato con score desglosado
6. ConstraintReport        — informe de reglas duras y blandas aplicadas
7. ReadabilityResult       — ancho mín/pref/máx + altura por candidato
8. LayoutDeclaration       — ancho/alto mín/pref/máx por panel
9. DashboardRole           — rol narrativo del panel
10. DashboardPlan          — salida del DashboardLayoutOptimizer
11. FeedbackEvent          — evento a persistir en brain.duckdb

Exit criteria:
✓ from sqlviz_inference.contracts import (todos los tipos) funciona
✓ mypy pasa con 0 errores sobre los tipos nuevos
✓ Ningún módulo de V0.1 se rompe al importar los tipos nuevos
```

### Fase B — ColumnRoleDetector + ConstraintEngine

```
Goal:    Las restricciones duras eliminan exactamente lo que deben.
         Ningún caso del benchmark pierde accuracy.

Tareas:
1. ColumnRoleDetector (módulo 6.2):
   - Clasificar metric / dimension / time / id / percentage /
     rank / category por nombre + tipo físico + posición en AST
   - cliente_id INTEGER → id, no metric
   - Integrar con semantic_dictionary.yaml + ast_helpers.py

2. ConstraintEngine (módulo 6.6):
   Reglas duras mínimas para V0.2:
   - pie: eliminar si cardinalidad > 7 O si columna numérica
     no tiene evidencia de porcentaje/composición
   - line: eliminar si no hay eje temporal confirmado en DataProfile
   - scatter: eliminar si < 2 columnas numéricas con roles distintos
   - kpi: eliminar si row_count > 1
   - histogram: eliminar si no hay evidencia de variable continua
     pre-binning (SQL ya agrupó valores exactos → bucketed, no histograma)
   - funnel: eliminar si no hay evidencia de etapas ordenadas de
     proceso (step/stage/etapa/fase/conversion/dropoff en semántica)
   Reglas blandas: configuradas en nueva YAML constraint_rules.yaml

3. Casos de prueba para cada regla dura — al menos 2 positivos
   (se aplica correctamente) y 2 negativos (no se aplica cuando
   no debe) por regla.

Exit criteria:
✓ Benchmark adversarial (42 casos) mantiene 100% pass
✓ Los 9 patrones de la sección 5.3 ("Descartar") están cubiertos
  como reglas en ConstraintEngine
✓ ColumnRoleDetector clasifica correctamente los 30 casos del
  benchmark gold (validación por inspección manual del campo roles)
✓ ruff check + mypy: 0 findings/errores
```

### Fase C — ReadabilityModel + ScoringModel (en ese orden)

```
Goal:    El benchmark gold (30 casos) se mantiene en 100% usando
         el scoring multicriterio nuevo en vez de
         afinidad-menos-penalización.

IMPORTANTE — ORDEN FIJO:
    ReadabilityModel ANTES que ScoringModel.
    ScoringModel consume readability como dimensión de entrada.
    Invertir el orden es un bug arquitectónico (sección 7).

Tareas:
1. ReadabilityModel (módulo 6.7):
   - Inputs: cardinalidad, longitud de labels, cantidad de series,
     row_count, chart_type del candidato
   - Outputs: col_span_min, col_span_preferred, col_span_max,
     height_px_recommended, legibility_score (0–1)
   - Fundamento: Cleveland & McGill, Heer & Bostock (sección 4)

2. ScoringModel (módulo 6.8):
   - 10 dimensiones: semantic_fit + task_fit + perceptual_accuracy +
     readability + information_density + business_relevance
     − cognitive_load − visual_clutter − ambiguity − interaction_cost
   - semantic_fit reutiliza chart_affinity_matrix.yaml de V0.1
   - Cada dimensión configurable en scoring_weights.yaml (nueva YAML)
   - Score desglosado visible en InferenceResult.chart_candidates

3. Integrar en el pipeline: pasos 8 y 9 de la sección 7.

4. Extender el benchmark gold: anotar cada uno de los 30 casos con
   el candidato ganador esperado y las top-3 dimensiones que deben
   dominarlo — esto hace la comparación verificable, no solo "¿ganó
   el chart correcto?" sino "¿por las razones correctas?"

Exit criteria:
✓ Benchmark gold: 100% chart accuracy usando ScoringModel nuevo
  (no regresión respecto a V0.1)
✓ Para cada caso del benchmark gold: top dimensión del score
  del ganador coincide con la anotación esperada
✓ Benchmark adversarial: 100% pass (no regresión)
✓ ruff check + mypy: 0 findings/errores
```

### Fase D — Layout Optimizer + Dashboard Objective

```
Goal:    Dashboards de 4+ paneles muestran jerarquía narrativa real,
         no solo KPIs arriba + packing secuencial.

Tareas:
1. LayoutDeclarationBuilder + DashboardRoleClassifier (módulo 6.10):
   - Cada panel declara col_span_min/preferred/max basado en
     ReadabilityModel + tipo de chart
   - Roles: resumen_ejecutivo, historia_principal,
     explicacion_secundaria, diagnostico, tabla_de_detalle, control

2. DashboardLayoutOptimizer (módulo 6.11):
   - Recibe todos los paneles con sus LayoutDeclarations
   - Decide fila, posición, col_span y height_px para el conjunto
   - Respeta restricciones duras: KPIs antes que charts (DOC 5
     sección 15 — el orden narrativo no se descarta, se formaliza
     como restricción)
   - Fundamento: GraphScape (sección 4)

3. DashboardObjective (módulo 6.12):
   - 10 dimensiones: comprensión + fidelidad_semántica +
     legibilidad + coherencia_narrativa + cobertura_de_información +
     prioridad_de_negocio − carga_cognitiva − clutter −
     redundancia − espacio_desperdiciado

4. InformationGainEngine (módulo 6.13):
   - Detecta paneles redundantes por fingerprint de SQL + resultado
   - Reporta en InferenceResult — no actúa automáticamente

5. Nuevos casos de benchmark: mínimo 10 casos de dashboards
   multi-panel (3-6 paneles) con anotación del layout narrativo
   esperado.

Exit criteria:
✓ El dashboard de ejemplo V0.1 (4 paneles: KPI, Line, Bar,
  Bar Horizontal) produce el mismo layout que producía antes
  (no regresión en el caso conocido)
✓ Un dashboard de 6 paneles (2 KPIs + 4 charts) muestra KPIs
  en fila superior, charts ordenados por DashboardRole
✓ DashboardObjective produce utility_score > 0 para el dashboard
  de ejemplo (prueba de que la función es evaluable)
✓ InformationGainEngine detecta un caso de redundancia real
  (test con dos paneles de COUNT(*) con misma tabla)
✓ ruff check + mypy: 0 findings/errores
```

### Fase E — OverrideSystem + FeedbackEngine

```
Goal:    Una corrección del usuario en la sesión 1 cambia el
         resultado automático en la sesión 2 para el mismo
         patrón de SQL.

Tareas:
1. OverrideSystem (módulo 6.15):
   Schema en .sqlviz (sección 8.1):
   - panel: inferred_chart_type, selected_chart_type,
     chart_user_override, inferred_col_span, selected_col_span,
     layout_user_override, inferred_height_px, selected_height_px,
     height_user_override
   API: PATCH /panels/{id}/override con campo y valor
   Siempre separar inferred_* / selected_* / user_override

2. FeedbackEngine (módulo 6.14):
   - Tablas nuevas en brain.duckdb (sección 8.3):
       feedback_patterns (fingerprint → chart_override)
       layout_patterns   (fingerprint → col_span_override)
       feedback_events   (timestamp, fingerprint, campo, valor)
   - Paso 16 del pipeline: persistir FeedbackEvent
   - Al inicio del pipeline (paso 6, candidatos): consultar
     brain.duckdb — si hay patrón conocido para el fingerprint,
     elevar ese candidato antes del scoring

3. Migration en sqlviz-storage para los campos nuevos de Panel.

Exit criteria:
✓ PATCH /panels/{id}/override persiste correctamente en .sqlviz
✓ inferred_* nunca se sobreescribe — selected_* refleja el override
✓ Prueba de regresión de sesión a sesión:
    1. Ejecutar SQL X → sistema elige chart A
    2. Usuario hace override a chart B → guardado en brain.duckdb
    3. Ejecutar SQL X de nuevo (misma sesión o nueva) →
       sistema elige chart B
✓ ruff check + mypy: 0 findings/errores
```

### Fase F — InformationGainEngine V2 + ExplanationEngine V2

```
Goal:    El usuario ve una explicación en lenguaje de analista, no
         el score_trace técnico.

Tareas:
1. InformationGainEngine V2 (módulo 6.13 — pulir lo de Fase D):
   - Integrar resultado de redundancia en ExplanationEngine V2
   - Sugerir acción específica (bajar prioridad, convertir a tabla)
     no solo detectar

2. ExplanationEngine V2 (módulo 6.16):
   - Consumir ConstraintReport + ChartScores desglosado +
     IntentResult de AnalyticalIntentModel
   - Generar explicación en lenguaje natural:
       "Elegí {chart} porque {razón_principal}.
        {razón_secundaria}. Consideré {alternativa} pero {por_qué_no}."
   - Plantillas YAML por combinación (intent, chart, razón principal)
     — no LLM en V0.2, templates estructurados

3. Exponer explanation_v2 en InferenceResult y en la API.

4. Añadir al frontend: panel de explicación collapsable debajo de
   cada chart (ya existe ExplainPanel.svelte en V0.1 — extenderlo).

Exit criteria:
✓ Cada uno de los 30 casos del benchmark gold produce una
  explicación no vacía con al menos razón_principal y alternativa
✓ La explicación menciona correctamente el chart ganador y la
  razón principal (validación manual de 5 casos representativos)
✓ ExplainPanel.svelte muestra explanation_v2 cuando existe
✓ ruff check + mypy: 0 findings/errores
```

### Fase G — Benchmark doctoral ampliado

```
Goal:    El benchmark cubre los patrones nuevos de V0.2 y valida
         que el Cognitive Dashboard Compiler no regresiona en
         ningún caso del corpus original de V0.1.

Tareas:
1. Añadir al benchmark gold mínimo 20 casos nuevos que cubran:
   - comparison vs. composition (¿bar grouped o stacked o pie?)
   - ranking sin LIMIT (ORDER BY + RANK() como evidencia igual de
     válida que ORDER BY + LIMIT)
   - fechas como entero YYYYMM (no DATE — debe reconocerse como
     dimensión temporal)
   - porcentajes que no suman 100 (no composition → no pie)
   - histograma real vs. bucket table (SQL ya agrupó exacto →
     NOT histograma)
   - funnel real vs. count agrupado (sin semántica de etapas →
     NOT funnel)
   - scatter con IDs numéricos falsos (customer_id, order_id →
     NOT métrica, NOT scatter)
   - wide table (más columnas que filas — ¿table o heatmap?)

2. Añadir al benchmark adversarial mínimo 10 casos nuevos:
   negatives para los 7 patrones anteriores (el sistema NO debe
   elegir el chart incorrecto cuando la evidencia es ambigua).

3. Correr el benchmark completo contra el sistema V0.2 final.

Exit criteria:
✓ Benchmark gold completo (original + nuevos): 100% chart accuracy
✓ Benchmark adversarial completo (original + nuevos): 100% pass
✓ Los 20+ casos nuevos tienen anotación de razón principal
  esperada — verificada contra ExplanationEngine V2
✓ ruff check + mypy: 0 findings/errores
✓ 650+ tests en total (original + nuevos de V0.2)
```

---

## 9. Cambios en el modelo de datos

### 9.1 `Panel` (storage + migration + API)

```sql
-- Campos nuevos en la tabla panels de .sqlviz
-- (migration nueva en sqlviz-storage/migrations.py)

inferred_chart_type   TEXT,           -- lo que el motor decidió
selected_chart_type   TEXT,           -- activo ahora (inferred o override)
chart_user_override   TEXT,           -- corrección explícita del usuario (nullable)

inferred_visual_spec  JSON,           -- VisualSpec generado por VisualSpecBuilder
selected_visual_spec  JSON,           -- activo ahora

inferred_col_span     INTEGER,        -- lo que ReadabilityModel decidió
selected_col_span     INTEGER,        -- activo ahora
layout_user_override  INTEGER,        -- corrección explícita (nullable)

inferred_height_px    INTEGER,        -- lo que ReadabilityModel decidió
selected_height_px    INTEGER,        -- activo ahora
height_user_override  INTEGER,        -- corrección explícita (nullable)

dashboard_role        TEXT            -- rol narrativo del panel
```

**Invariante del OverrideSystem:** `inferred_*` nunca se sobreescribe
una vez calculado. `selected_*` refleja el estado activo. Si hay
`user_override`, `selected_*` refleja el override.

### 9.2 `InferenceResult` (result.py)

```python
# Estructura por capas — reemplaza la estructura plana de V0.1.
# chart_winner se mantiene por compatibilidad hacia atrás.

@dataclass
class InferenceResult:
    # ── Perfil de datos ──────────────────────────────────────────
    sql_profile:        SQLProfile
    data_profile:       DataProfile
    column_roles:       ColumnRoles

    # ── Semántica e intent ───────────────────────────────────────
    semantic_profile:   SemanticProfile
    intent_result:      IntentResult          # V2 — con evidencia

    # ── Candidatos y decisión ────────────────────────────────────
    chart_candidates:   list[ChartCandidate]  # con score desglosado
    constraint_report:  ConstraintReport      # qué se eliminó y por qué
    chart_scores:       list[ChartScore]      # score desglosado por candidato
    readability_result: ReadabilityResult     # por candidato ganador

    # ── Contrato de render ───────────────────────────────────────
    visual_spec:        VisualSpec            # el contrato para EChartsRenderer

    # ── Layout ───────────────────────────────────────────────────
    dashboard_role:     DashboardRole
    layout_declaration: LayoutDeclaration

    # ── Explicación ──────────────────────────────────────────────
    explanation_v2:     Explanation           # lenguaje natural

    # ── Compatibilidad V0.1 ──────────────────────────────────────
    chart_winner:       str                   # sigue existiendo, no es el campo principal
    col_span:           int                   # derivado de selected_col_span
    filter_controls:    list[FilterControl]   # sin cambios
    title:              str                   # sin cambios
    score_trace:        dict                  # V0.1 trace — deprecado, no removido
```

### 9.3 `brain.duckdb` — tablas nuevas

```sql
-- Las 3 tablas hoy deliberadamente ausentes (DOC 5, sección 16.4)

CREATE TABLE IF NOT EXISTS feedback_patterns (
    fingerprint         TEXT PRIMARY KEY,
    -- fingerprint = hash(sql_normalized + column_types + row_count_bucket)
    chart_override      TEXT    NOT NULL,
    col_span_override   INTEGER,
    height_override     INTEGER,
    confidence          FLOAT   DEFAULT 1.0,
    observation_count   INTEGER DEFAULT 1,
    last_seen_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS layout_patterns (
    fingerprint         TEXT PRIMARY KEY,
    col_span_override   INTEGER NOT NULL,
    height_override     INTEGER,
    confidence          FLOAT   DEFAULT 1.0,
    observation_count   INTEGER DEFAULT 1,
    last_seen_at        TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS feedback_events (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint         TEXT    NOT NULL,
    field_name          TEXT    NOT NULL,   -- 'chart_type' | 'col_span' | 'height_px'
    inferred_value      TEXT    NOT NULL,
    user_value          TEXT    NOT NULL,
    occurred_at         TIMESTAMP DEFAULT now()
);
```

### 9.4 Dashboard compose — cambio de contrato en la API

```
V0.1: POST /api/v1/compose recibe paneles ya decididos (panel_id,
      chart_winner, col_span) y los empaqueta en filas.

V0.2: POST /api/v1/compose recibe contexto global:
      - Todos los paneles con sus InferenceResult completos
        (incluye VisualSpec, LayoutDeclaration, DashboardRole)
      - Feedback de brain.duckdb para el fingerprint del conjunto

      Necesario porque DashboardLayoutOptimizer y DashboardObjective
      necesitan ver el conjunto completo — no uno por uno.

Compatibilidad: el contrato V0.1 (panel_id + chart_winner +
      col_span) se mantiene como fallback mientras la Fase D
      no esté completa.
```

---

## 10. Árbol de dependencias de construcción — V0.2

```
Fase 0  (DataProfile + VisualSpec + VisualSpecBuilder)
    │  prerequisito de: todo lo demás
    ▼
Fase A  (tipos sin implementación)
    │  prerequisito de: B, C, D, E, F
    ▼
Fase B  (ColumnRoleDetector + ConstraintEngine)
    │  prerequisito de: C
    ▼
Fase C  (ReadabilityModel + ScoringModel)   ← ReadabilityModel ANTES que ScoringModel
    │  prerequisito de: D
    ▼
Fase D  (LayoutOptimizer + DashboardObjective)
    │  prerequisito de: E, F
    ▼
Fase E  (OverrideSystem + FeedbackEngine)
    │  puede correr en paralelo con F una vez que D está completa
Fase F  (ExplanationEngine V2)
    │
    ▼
Fase G  (Benchmark doctoral ampliado)
```

Fase 0 → A → B → C → D son lineales. E y F pueden solaparse.
G solo comienza cuando E y F tienen exit criteria completos.

---

## 11. Definición de Done — V0.2

SQLviz V0.2 está completo cuando, y solo cuando, todos los siguientes
son simultáneamente verdaderos:

```
[ ] EChartsRenderer no tiene ninguna lógica de inferencia de columnas
    — cero "primera columna = x" en el componente Svelte

[ ] VisualSpec existe como contrato explícito y todos los chart types
    renderizan desde él sin adivinar nada

[ ] DataProfile se calcula para cada ejecución de panel y está
    disponible en InferenceResult

[ ] ConstraintEngine elimina correctamente los 9 patrones incorrectos
    documentados en la sección 5.3

[ ] ScoringModel produce score desglosado con 10 dimensiones visibles
    para cada candidato

[ ] Benchmark gold (30 casos originales + 20 casos nuevos): 100%

[ ] Benchmark adversarial (42 casos originales + 10 casos nuevos): 100%

[ ] Un dashboard de 4+ paneles muestra jerarquía narrativa real
    (no solo KPIs arriba + packing secuencial)

[ ] Una corrección del usuario en la sesión 1 cambia el resultado
    en la sesión 2 para el mismo patrón de SQL

[ ] Cada panel muestra una explicación en lenguaje de analista,
    no el score_trace técnico

[ ] Las 3 tablas de brain.duckdb están activas y reciben datos

[ ] inferred_* / selected_* / user_override separados para chart,
    col_span y height en cada panel del .sqlviz

[ ] 650+ tests en total (pytest)

[ ] ruff check + mypy: 0 findings/errores en los 6 paquetes

[ ] La sección 11 de este documento lista con precisión todo lo
    que NO está en V0.2, para que ninguna decisión de scope
    se tome silenciosamente durante la implementación
```

---

## 12. Qué queda diferido — y cuándo vuelve

```
Feature                                    Fuente           Retorna
────────────────────────────────────────────────────────────────────
Knowledge Graph completo con razonamiento  DOC 9 / sección  V0.3 / V1.0
 (entidades de negocio + grafo + inferencia)  6.17

FeedbackEngine con aprendizaje estadístico  DOC 5 §16.4       V0.3
 (bayesiano / Thompson sampling)

Insight Engine                              DOC 5 §16.4       V0.3
Narrative Engine                            DOC 5 §16.4       V0.3
Semantic Engine V1 (embeddings)             DOC 5 §16.4       V0.3
Domain Dictionaries completos               DOC 5 §16.3       V0.3
Cross-filtering entre paneles               DOC 5 §15.7       V0.3
Dashboard Composer (missing-perspective)    DOC 5 §15.7       V0.3

Feature Registry (80-120 dims)              DOC 5 §16.3       V0.2 final
 (depende de que ColumnRoleDetector +
  DataProfile estén estables — puede
  expandirse al final de V0.2)

sqlviz-sources (ClickHouse)                 DOC 8 §6          V0.2
sqlviz-viz (Plotly)                         DOC 8 §6          V0.2
 (ambos bloqueados en V0.1 por falta de
  consumidores reales — V0.2 puede
  desbloquearlos si hay demanda)

Cloud mode                                  DOC 2 §1          V0.4
Multi-source dashboards                     DOC 8 §6          V0.3+
Auto-layout UX final mile                   DOC 8 §6          V0.2 / V0.3
 (zero "Edit SQL" modal indirection)
```

---

*SQLviz V0.2 Construction Plan — v0.1.0*
*"No reconstruir SQLviz. Convertir sqlviz-inference en el Cognitive Dashboard*
*Compiler, empezando por los dos contratos: DataProfile de entrada, VisualSpec*
*de salida. El cerebro de en medio se reemplaza en fases sin romper nada."*
