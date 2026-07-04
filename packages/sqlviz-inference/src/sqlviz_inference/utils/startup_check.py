from __future__ import annotations

from .yaml_loader import yaml_loader

REQUIRED_FILES = [
    "feature_vector_v0.yaml",
    "intent_rules.yaml",
    "chart_affinity_matrix.yaml",
    "chart_penalties.yaml",
    "fallback_rules.yaml",
    "thresholds.yaml",
    "semantic_dictionary.yaml",
]


def validate_rules_on_startup() -> list[str]:
    """
    Load and validate all rule files exist and parse correctly.
    Called once when sqlviz-inference is imported.
    Returns list of errors (empty if all valid).
    """
    errors: list[str] = []
    for filename in REQUIRED_FILES:
        try:
            data = yaml_loader.load(filename)
            if not data:
                errors.append(f"{filename}: file is empty")
        except FileNotFoundError as e:
            errors.append(f"{filename}: not found — {e}")
        except Exception as e:
            errors.append(f"{filename}: parse error — {e}")

    # Validate intent weights sum approximately to 1.0
    try:
        intent_rules = yaml_loader.load("intent_rules.yaml")
        for intent_name, config in intent_rules.items():
            weights = config.get("weights", {})
            total = sum(weights.values())
            # Allow up to 1.80: intents may include additive derived signals
            # (e.g., has_percentile in distribution, §16.33) that stack on top
            # of the base 1.0 to ensure the signal overcomes penalties in D0.
            # The engine clamps final scores at 1.0, so excess weight is safe.
            if not (0.95 <= total <= 1.80):
                errors.append(
                    f"intent_rules.yaml: '{intent_name}' weights sum to "
                    f"{total:.2f}, expected ~1.0"
                )
    except Exception as e:
        errors.append(f"intent_rules.yaml weight validation failed: {e}")

    return errors
