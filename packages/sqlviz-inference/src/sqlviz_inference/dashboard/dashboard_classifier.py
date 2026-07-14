"""DashboardClassifier — infers dashboard_hint and dashboard_domain.

Called after each panel execution to classify the parent dashboard based
on the aggregated intent signals of all its panels.

Outputs:
  hint   — fine-grained semantic label (e.g. "user_retention", "financial_kpi")
  domain — coarse topic category     (e.g. "product", "finance", "ops")

The frontend maps these to icons (never the backend).
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

# ── Domain detection ──────────────────────────────────────────────────────────

_DOMAIN_TOKENS: dict[str, list[str]] = {
    "finance": [
        "revenue", "profit", "cost", "expense", "mrr", "arr", "ltv", "cac",
        "budget", "invoice", "payment", "billing", "margin", "gross", "net_revenue",
        "arpu", "burn", "runway", "ebitda", "capex", "opex",
    ],
    "product": [
        "dau", "mau", "wau", "session", "event", "feature", "onboarding",
        "activation", "engagement", "stickiness", "screen", "click_event",
        "install", "crash", "nps",
    ],
    "marketing": [
        "campaign", "channel", "ctr", "impression", "click", "conversion",
        "ad_spend", "roas", "email", "open_rate", "unsubscribe", "bounce",
        "lead_source", "utm",
    ],
    "hr": [
        "employee", "headcount", "salary", "hire", "attrition", "turnover",
        "department", "team", "fte", "contractor", "tenure", "payroll",
        "performance", "review",
    ],
    "ops": [
        "latency", "p99", "p95", "p50", "error_rate", "uptime", "request",
        "throughput", "spike", "incident", "sla", "availability", "deploy",
        "cpu", "memory", "queue",
    ],
    "sales": [
        "deal", "pipeline", "quota", "close_rate", "prospect", "lead",
        "opportunity", "win_rate", "sales_cycle", "account", "crm",
        "forecast", "target",
    ],
}

# ── Intent → hint (single dominant intent) ────────────────────────────────────

_INTENT_HINTS: dict[str, str] = {
    "kpi":          "kpi_overview",
    "trend":        "trend_analysis",
    "comparison":   "comparison_analysis",
    "ranking":      "ranking_analysis",
    "distribution": "distribution_analysis",
    "correlation":  "correlation_analysis",
    "funnel":       "funnel_analysis",
    "retention":    "retention_analysis",
    "cohort":       "cohort_analysis",
    "anomaly":      "anomaly_detection",
    "composition":  "composition_analysis",
    "detail":       "data_detail",
}

# ── Multi-intent combos (checked in order; first match wins) ──────────────────

_COMBO_HINTS: list[tuple[frozenset[str], str]] = [
    (frozenset({"retention", "funnel"}),   "user_lifecycle"),
    (frozenset({"retention", "cohort"}),   "user_lifecycle"),
    (frozenset({"funnel", "cohort"}),      "user_lifecycle"),
    (frozenset({"trend", "kpi"}),          "kpi_performance"),
    (frozenset({"comparison", "ranking"}), "competitive_analysis"),
    (frozenset({"anomaly", "trend"}),      "anomaly_monitoring"),
]

# ── Domain + dominant intent → more specific hint ─────────────────────────────

_DOMAIN_INTENT_HINTS: dict[tuple[str, str], str] = {
    ("finance",   "trend"):       "financial_trend",
    ("finance",   "kpi"):         "financial_kpi",
    ("finance",   "comparison"):  "financial_comparison",
    ("product",   "retention"):   "product_retention",
    ("product",   "funnel"):      "product_funnel",
    ("product",   "trend"):       "product_growth",
    ("sales",     "trend"):       "sales_performance",
    ("sales",     "kpi"):         "sales_kpi",
    ("sales",     "ranking"):     "sales_ranking",
    ("marketing", "trend"):       "marketing_performance",
    ("marketing", "comparison"):  "marketing_comparison",
    ("ops",       "trend"):       "ops_monitoring",
    ("ops",       "anomaly"):     "incident_monitoring",
    ("hr",        "kpi"):         "hr_overview",
    ("hr",        "trend"):       "hr_trend",
}

# ── Domain-level default hints ────────────────────────────────────────────────

_DOMAIN_DEFAULT_HINTS: dict[str, str] = {
    "finance":   "financial_dashboard",
    "product":   "product_analytics",
    "marketing": "marketing_analytics",
    "hr":        "hr_analytics",
    "ops":       "ops_monitoring",
    "sales":     "sales_dashboard",
}


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass
class DashboardClassification:
    hint: str
    domain: str


def classify_dashboard(
    panel_intents: list[str],
    column_names: list[str],
    sql_text: str = "",
) -> DashboardClassification:
    """Infer hint + domain from all executed panels of a dashboard.

    Args:
        panel_intents: intent_winner for each panel (may be empty for fresh
                       dashboards where no panel has been executed yet).
        column_names:  column names from the most-recently-executed panel
                       (used for domain detection; lowercase expected).
        sql_text:      concatenated SQL of all panels (supplementary keyword scan).

    Returns:
        DashboardClassification with hint and domain strings.
    """
    domain = _detect_domain(column_names, sql_text)
    hint = _build_hint(panel_intents, domain)
    return DashboardClassification(hint=hint, domain=domain)


# ── Private helpers ───────────────────────────────────────────────────────────

def _detect_domain(column_names: list[str], sql_text: str) -> str:
    tokens: set[str] = {c.lower() for c in column_names}
    tokens |= set(re.findall(r"\b[a-z_]{3,}\b", sql_text.lower()))

    scores: Counter[str] = Counter()
    for domain, keywords in _DOMAIN_TOKENS.items():
        for kw in keywords:
            if kw in tokens:
                scores[domain] += 1

    if not scores:
        return "analytics"
    return scores.most_common(1)[0][0]


def _build_hint(intents: list[str], domain: str) -> str:
    if not intents:
        return "analytics_overview"

    intent_set = set(intents)
    dominant = Counter(intents).most_common(1)[0][0]

    # 1. Special multi-intent combos
    for combo, combo_hint in _COMBO_HINTS:
        if combo.issubset(intent_set):
            return combo_hint

    # 2. Domain + dominant intent → specific hint (takes priority over generic all-KPI)
    specific = _DOMAIN_INTENT_HINTS.get((domain, dominant))
    if specific:
        return specific

    # 3. All panels are KPI with no domain-specific match
    if intent_set == {"kpi"}:
        return "kpi_overview"

    # 4. Domain-level default (only for named domains, not generic "analytics")
    domain_default = _DOMAIN_DEFAULT_HINTS.get(domain)
    if domain_default:
        return domain_default

    # 5. Intent-based fallback
    return _INTENT_HINTS.get(dominant, "analytics_overview")
