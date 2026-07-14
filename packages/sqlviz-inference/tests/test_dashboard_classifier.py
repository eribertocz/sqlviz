"""Tests for DashboardClassifier — infers hint + domain from panel signals."""

from __future__ import annotations

import pytest
from sqlviz_inference.dashboard.dashboard_classifier import (
    DashboardClassification,
    classify_dashboard,
)


# ── classify_dashboard: basic API ─────────────────────────────────────────────

class TestClassifyDashboardAPI:

    def test_returns_dataclass(self) -> None:
        result = classify_dashboard(["trend"], ["date", "revenue"])
        assert isinstance(result, DashboardClassification)
        assert result.hint
        assert result.domain

    def test_empty_intents_returns_analytics_overview(self) -> None:
        result = classify_dashboard([], [])
        assert result.hint == "analytics_overview"

    def test_hint_is_string(self) -> None:
        result = classify_dashboard(["kpi", "trend"], ["date", "value"])
        assert isinstance(result.hint, str) and len(result.hint) > 0

    def test_domain_is_string(self) -> None:
        result = classify_dashboard(["comparison"], ["product_id", "sales"])
        assert isinstance(result.domain, str) and len(result.domain) > 0


# ── Domain detection from column names ───────────────────────────────────────

class TestDomainDetection:

    def test_finance_columns(self) -> None:
        result = classify_dashboard(["kpi"], ["revenue", "profit", "mrr", "cost"])
        assert result.domain == "finance"

    def test_product_columns(self) -> None:
        result = classify_dashboard(["trend"], ["dau", "mau", "session", "event"])
        assert result.domain == "product"

    def test_hr_columns(self) -> None:
        result = classify_dashboard(["kpi"], ["employee", "headcount", "attrition"])
        assert result.domain == "hr"

    def test_ops_columns(self) -> None:
        result = classify_dashboard(["anomaly"], ["latency", "p99", "error_rate"])
        assert result.domain == "ops"

    def test_sales_columns(self) -> None:
        result = classify_dashboard(["ranking"], ["deal", "pipeline", "quota", "lead"])
        assert result.domain == "sales"

    def test_marketing_columns(self) -> None:
        result = classify_dashboard(["trend"], ["campaign", "ctr", "impression", "conversion"])
        assert result.domain == "marketing"

    def test_unknown_columns_return_analytics(self) -> None:
        result = classify_dashboard(["comparison"], ["col_a", "col_b", "foo"])
        assert result.domain == "analytics"

    def test_domain_from_sql_keywords(self) -> None:
        sql = "SELECT revenue, profit FROM finance_summary"
        result = classify_dashboard(["trend"], [], sql_text=sql)
        assert result.domain == "finance"


# ── Hint: multi-intent combos ─────────────────────────────────────────────────

class TestComboHints:

    def test_retention_funnel_gives_user_lifecycle(self) -> None:
        result = classify_dashboard(["retention", "funnel"], [])
        assert result.hint == "user_lifecycle"

    def test_retention_cohort_gives_user_lifecycle(self) -> None:
        result = classify_dashboard(["retention", "cohort"], [])
        assert result.hint == "user_lifecycle"

    def test_funnel_cohort_gives_user_lifecycle(self) -> None:
        result = classify_dashboard(["funnel", "cohort", "trend"], [])
        assert result.hint == "user_lifecycle"

    def test_trend_kpi_gives_kpi_performance(self) -> None:
        result = classify_dashboard(["trend", "kpi", "kpi"], [])
        assert result.hint == "kpi_performance"

    def test_comparison_ranking_gives_competitive_analysis(self) -> None:
        result = classify_dashboard(["comparison", "ranking"], [])
        assert result.hint == "competitive_analysis"

    def test_anomaly_trend_gives_anomaly_monitoring(self) -> None:
        result = classify_dashboard(["anomaly", "trend"], [])
        assert result.hint == "anomaly_monitoring"


# ── Hint: all-KPI panel ───────────────────────────────────────────────────────

class TestAllKPI:

    def test_all_kpi_panels(self) -> None:
        result = classify_dashboard(["kpi", "kpi", "kpi"], [])
        assert result.hint == "kpi_overview"

    def test_single_kpi_panel(self) -> None:
        result = classify_dashboard(["kpi"], [])
        assert result.hint == "kpi_overview"


# ── Hint: domain + intent specific ───────────────────────────────────────────

class TestDomainIntentHints:

    def test_finance_trend(self) -> None:
        result = classify_dashboard(["trend"], ["revenue", "profit"])
        assert result.hint == "financial_trend"

    def test_finance_kpi(self) -> None:
        result = classify_dashboard(["kpi"], ["mrr", "arr", "ltv"])
        assert result.hint == "financial_kpi"

    def test_product_retention(self) -> None:
        result = classify_dashboard(["retention"], ["dau", "mau"])
        assert result.hint == "product_retention"

    def test_product_funnel(self) -> None:
        result = classify_dashboard(["funnel"], ["session", "event"])
        assert result.hint == "product_funnel"

    def test_sales_trend(self) -> None:
        result = classify_dashboard(["trend"], ["deal", "pipeline", "quota"])
        assert result.hint == "sales_performance"

    def test_ops_anomaly(self) -> None:
        result = classify_dashboard(["anomaly"], ["latency", "p99", "error_rate"])
        assert result.hint == "incident_monitoring"

    def test_hr_kpi(self) -> None:
        result = classify_dashboard(["kpi"], ["employee", "headcount", "salary"])
        assert result.hint == "hr_overview"


# ── Hint: domain default (no intent+domain specific match) ───────────────────

class TestDomainDefaultHints:

    def test_finance_domain_default(self) -> None:
        result = classify_dashboard(["distribution"], ["revenue", "cost"])
        assert result.hint == "financial_dashboard"

    def test_marketing_domain_default(self) -> None:
        result = classify_dashboard(["distribution"], ["campaign", "ctr"])
        assert result.hint == "marketing_analytics"

    def test_sales_domain_default(self) -> None:
        result = classify_dashboard(["distribution"], ["deal", "pipeline"])
        assert result.hint == "sales_dashboard"


# ── Hint: intent-based fallback ───────────────────────────────────────────────

class TestIntentFallback:

    def test_trend_fallback(self) -> None:
        result = classify_dashboard(["trend"], [])
        assert result.hint == "trend_analysis"

    def test_correlation_fallback(self) -> None:
        result = classify_dashboard(["correlation"], [])
        assert result.hint == "correlation_analysis"

    def test_funnel_fallback(self) -> None:
        result = classify_dashboard(["funnel"], [])
        assert result.hint == "funnel_analysis"

    def test_anomaly_fallback(self) -> None:
        result = classify_dashboard(["anomaly"], [])
        assert result.hint == "anomaly_detection"

    def test_unknown_intent_returns_analytics_overview(self) -> None:
        result = classify_dashboard(["unknown_intent"], [])
        assert result.hint == "analytics_overview"


# ── Multi-panel dominant selection ────────────────────────────────────────────

class TestDominantIntent:

    def test_combo_beats_dominance(self) -> None:
        # trend+kpi combo fires even when trend is more common — combos take priority.
        result = classify_dashboard(["trend", "trend", "trend", "kpi"], [])
        assert result.hint == "kpi_performance"

    def test_dominant_intent_wins_without_combo(self) -> None:
        # Pure trend panels with no combo → trend_analysis.
        result = classify_dashboard(["trend", "trend", "trend"], [])
        assert result.hint == "trend_analysis"

    def test_tie_broken_by_counter_most_common(self) -> None:
        # Counter.most_common returns first-encountered on tie — deterministic.
        result = classify_dashboard(["comparison", "distribution"], [])
        assert result.hint in ("comparison_analysis", "distribution_analysis")

    def test_many_panels_combo_still_wins(self) -> None:
        result = classify_dashboard(["trend", "retention", "funnel", "comparison"], [])
        assert result.hint == "user_lifecycle"
