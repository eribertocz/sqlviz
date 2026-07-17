# SQLviz — Contract Stability Policy
**Version:** 1.0
**Since:** v0.2.4

---

## Contratos versionados

Los siguientes objetos son contratos con versión explícita:

| Contrato | Ubicación | Campo de versión | Versión actual |
|---|---|---|---|
| `InferenceResult` | `sqlviz_inference/result.py` | `result_schema_version` | `"1"` |
| `VisualSpec` | `sqlviz_inference/spec/visual_spec.py` | `schema_version` | `"1"` |
| `.sqlviz` (DDL) | `sqlviz_storage/schema.py` + migraciones | `_sqlviz_meta.schema_version` | `"1"` |

---

## Clasificación de cambios

### `backward-compatible`

Un cambio es backward-compatible cuando:
- Se agrega un campo **opcional** con valor default (no rompe deserialización existente).
- Se agrega un nuevo valor a un enum/string existente.
- Se agrega un endpoint nuevo a la API sin modificar los existentes.
- Se cambia la lógica interna sin tocar el contrato de salida.

**Acción requerida:** ninguna. El campo se agrega y el golden test se actualiza para registrar el nuevo campo.

### `breaking`

Un cambio es breaking cuando:
- Se **elimina** un campo que no tenía default.
- Se **renombra** un campo existente.
- Se cambia el tipo de un campo (ej. `str` → `list[str]`).
- Se elimina una tabla o columna del schema `.sqlviz`.
- Se cambia la semántica de un campo existente de forma incompatible.

**Acción requerida:**
1. Incrementar la constante de versión (`INFERENCE_RESULT_SCHEMA_VERSION`, `VISUAL_SPEC_SCHEMA_VERSION`, o `_SCHEMA_VERSION` en `project_db.py`).
2. Actualizar el golden fixture en `tests/golden/`.
3. Documentar el cambio en `CHANGELOG.md` bajo el encabezado `### Breaking`.
4. Para `.sqlviz`: agregar una migración en `migrations.py`.

### `deprecated`

Un campo está deprecated cuando:
- Sigue existiendo pero no debe usarse en código nuevo.
- Tiene un reemplazo documentado.
- Será eliminado en una versión futura (`breaking`).

**Convención de marcado en código:**
```python
# DEPRECATED — use result_xxx instead. Will be removed in v0.3.0.
old_field: str = ""
```

El campo permanece en los golden tests hasta que se elimine.

---

## Fuentes de verdad de YAML

Todos los archivos YAML de reglas viven en:
```
packages/sqlviz-inference/src/sqlviz_inference/rules/
```

Esta es la **única** fuente de verdad. No deben existir copias en otras rutas.
El `YAMLLoader` singleton carga exclusivamente desde este directorio.

Archivos de reglas actuales:
- `chart_affinity_matrix.yaml` — afinidad semántica por chart type
- `chart_penalties.yaml` — penalizaciones por chart type
- `constraint_rules.yaml` — reglas duras y blandas del ConstraintEngine
- `explanation_templates.yaml` — plantillas de ExplanationEngine V2
- `fallback_rules.yaml` — umbrales de fallback y display rules
- `feature_vector_v0.yaml` — definición del vector de features
- `intent_rules.yaml` — pesos e intents del IntentEngine
- `scoring_weights.yaml` — pesos del ScoringModel (10 dimensiones)
- `semantic_dictionary.yaml` — diccionario semántico de columnas
- `task_fit_matrix.yaml` — matriz de task fit por intent × chart
- `thresholds.yaml` — umbrales globales

---

## Proceso para cambios breaking en los contratos

1. **Abrir issue o PR** describiendo el cambio y por qué es necesario.
2. **Bumpar la versión** del contrato afectado.
3. **Actualizar el golden fixture** (`tests/golden/`).
4. **Actualizar `CHANGELOG.md`** con sección `### Breaking`.
5. **Agregar migración** si el cambio afecta `.sqlviz` (DDL).
6. **Verificar que todos los tests pasan** antes de mergear.

Un CI verde no es suficiente para justificar un cambio breaking — se requiere
revisión explícita de impacto en consumidores (frontend, CLI, API).

---

## Campos deprecated activos

| Campo | Contrato | Reemplazo | Eliminar en |
|---|---|---|---|
| `score_trace` | `InferenceResult` | `explanation_v2` | v0.3.0 |
| `chart_winner` | `InferenceResult` | `visual_spec.chart_type` | v0.3.0 |

*Nota: estos campos existen para compatibilidad con el frontend de V0.1. No se eliminan hasta que el frontend consuma `visual_spec` de forma exclusiva.*

---

*SQLviz Contract Policy — v1.0 / introduced in v0.2.4*
