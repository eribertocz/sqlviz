"""Exit criteria for Fase A — all 11 V0.2 contracts importable and instantiable."""
from __future__ import annotations

from sqlviz_inference.contracts import (
    CandidateReadability,
    ChartCandidate,
    ChartScore,
    ColumnRole,
    ColumnRoles,
    ConstraintReport,
    ConstraintViolation,
    DashboardPlan,
    DashboardRole,
    FeedbackEvent,
    IntentEvidence,
    IntentResult,
    LayoutDeclaration,
    PanelPlacement,
    ReadabilityResult,
    SemanticProfile,
    SemanticRelation,
    SQLProfile,
)


class TestContractsImportable:
    """The primary exit criterion: every type can be imported and instantiated."""

    def test_sql_profile_default(self) -> None:
        p = SQLProfile()
        assert p.has_aggregation is False
        assert p.has_group_by is False
        assert p.group_by_columns == []
        assert p.select_columns == []

    def test_sql_profile_populated(self) -> None:
        p = SQLProfile(
            has_aggregation=True,
            has_group_by=True,
            group_by_columns=["month"],
            aggregation_functions=["SUM"],
            select_columns=["month", "revenue"],
        )
        assert p.has_aggregation is True
        assert "SUM" in p.aggregation_functions

    def test_column_role(self) -> None:
        r = ColumnRole(name="customer_id", role="id")
        assert r.name == "customer_id"
        assert r.role == "id"

    def test_column_roles_default(self) -> None:
        cr = ColumnRoles()
        assert cr.roles == []

    def test_column_roles_populated(self) -> None:
        cr = ColumnRoles(roles=[
            ColumnRole(name="month", role="time"),
            ColumnRole(name="revenue", role="metric"),
            ColumnRole(name="customer_id", role="id"),
        ])
        assert len(cr.roles) == 3
        assert cr.roles[0].role == "time"
        assert cr.roles[2].role == "id"

    def test_semantic_relation(self) -> None:
        rel = SemanticRelation(
            source_column="cobrado",
            target_column="facturado",
            relation_type="lte",
            expression="cobrado <= facturado",
        )
        assert rel.relation_type == "lte"

    def test_semantic_profile_default(self) -> None:
        sp = SemanticProfile()
        assert sp.column_concepts == {}
        assert sp.relations == []

    def test_semantic_profile_populated(self) -> None:
        sp = SemanticProfile(
            column_concepts={"revenue": "ingresos", "cost": "costos"},
            relations=[SemanticRelation("cost", "revenue", "lte", "cost <= revenue")],
        )
        assert sp.column_concepts["revenue"] == "ingresos"
        assert len(sp.relations) == 1

    def test_intent_evidence(self) -> None:
        ev = IntentEvidence(signal="has_order_by", weight=0.8, direction="for")
        assert ev.direction == "for"

    def test_intent_result_v2_default(self) -> None:
        ir = IntentResult(primary_intent="trend")
        assert ir.primary_intent == "trend"
        assert ir.secondary_intents == []
        assert ir.confidence == 0.0

    def test_intent_result_v2_populated(self) -> None:
        ir = IntentResult(
            primary_intent="trend",
            secondary_intents=["comparison"],
            evidence_for=[IntentEvidence("has_temporal_dim", 1.0, "for")],
            evidence_against=[IntentEvidence("no_group_by", 0.3, "against")],
            required_visual_properties=["temporal_axis", "continuous_y"],
            confidence=0.87,
        )
        assert len(ir.evidence_for) == 1
        assert "temporal_axis" in ir.required_visual_properties

    def test_chart_score_default(self) -> None:
        s = ChartScore()
        assert s.semantic_fit == 0.0
        assert s.cognitive_load == 0.0
        assert len(vars(s)) == 10   # exactly 10 dimensions

    def test_chart_score_all_10_dims(self) -> None:
        dims = [
            "semantic_fit", "task_fit", "perceptual_accuracy", "readability",
            "information_density", "business_relevance",
            "cognitive_load", "visual_clutter", "ambiguity", "interaction_cost",
        ]
        s = ChartScore()
        for dim in dims:
            assert hasattr(s, dim), f"Missing dimension: {dim}"

    def test_chart_candidate_v2_default(self) -> None:
        c = ChartCandidate(chart_type="bar")
        assert c.chart_type == "bar"
        assert c.rank == 0
        assert c.eliminated_by_rule is None

    def test_chart_candidate_v2_eliminated(self) -> None:
        c = ChartCandidate(
            chart_type="pie",
            eliminated_by_rule="pie_high_cardinality",
            rank=0,
        )
        assert c.eliminated_by_rule == "pie_high_cardinality"

    def test_constraint_violation(self) -> None:
        v = ConstraintViolation(
            chart_type="pie",
            rule_name="pie_high_cardinality",
            rule_type="hard",
            reason="cardinalidad > 7",
        )
        assert v.rule_type == "hard"
        assert v.penalty == 0.0

    def test_constraint_report_default(self) -> None:
        r = ConstraintReport()
        assert r.eliminated == []
        assert r.penalized == []
        assert r.rules_checked == 0

    def test_constraint_report_populated(self) -> None:
        r = ConstraintReport(
            eliminated=[ConstraintViolation("pie", "pie_high_cardinality", "hard", "14 cats")],
            penalized=[
                ConstraintViolation("bar", "low_cardinality", "soft", "only 2 cats", penalty=0.2)
            ],
            rules_checked=6,
        )
        assert len(r.eliminated) == 1
        assert r.penalized[0].penalty == 0.2

    def test_candidate_readability_default(self) -> None:
        cr = CandidateReadability(chart_type="bar")
        assert cr.col_span_min == 4
        assert cr.col_span_preferred == 6
        assert cr.col_span_max == 12
        assert 0.0 <= cr.legibility_score <= 1.0

    def test_readability_result_default(self) -> None:
        rr = ReadabilityResult()
        assert rr.by_candidate == []

    def test_readability_result_populated(self) -> None:
        rr = ReadabilityResult(by_candidate=[
            CandidateReadability("bar", col_span_preferred=8, legibility_score=0.9),
            CandidateReadability("bar_horizontal", col_span_preferred=6, legibility_score=0.95),
        ])
        assert len(rr.by_candidate) == 2

    def test_layout_declaration_default(self) -> None:
        ld = LayoutDeclaration(panel_id="p1")
        assert ld.col_span_min == 4
        assert ld.col_span_preferred == 6
        assert ld.height_px_preferred == 360

    def test_layout_declaration_populated(self) -> None:
        ld = LayoutDeclaration(
            panel_id="p1",
            col_span_min=6,
            col_span_preferred=8,
            col_span_max=12,
            height_px_min=300,
            height_px_preferred=450,
            height_px_max=600,
        )
        assert ld.col_span_preferred == 8

    def test_dashboard_role_default(self) -> None:
        dr = DashboardRole(panel_id="p1")
        assert dr.role == "historia_principal"
        assert dr.priority == 5

    def test_dashboard_role_executive(self) -> None:
        dr = DashboardRole(panel_id="kpi_1", role="resumen_ejecutivo", priority=1)
        assert dr.role == "resumen_ejecutivo"
        assert dr.priority == 1

    def test_panel_placement(self) -> None:
        pp = PanelPlacement(panel_id="p1", row=0, col_offset=0, col_span=6, height_px=360)
        assert pp.col_span == 6

    def test_dashboard_plan_default(self) -> None:
        dp = DashboardPlan()
        assert dp.placements == []
        assert dp.total_rows == 0
        assert dp.utility_score == 0.0

    def test_dashboard_plan_populated(self) -> None:
        dp = DashboardPlan(
            placements=[
                PanelPlacement("kpi_1", 0, 0, 3, 180),
                PanelPlacement("kpi_2", 0, 3, 3, 180),
                PanelPlacement("line_1", 1, 0, 12, 360),
            ],
            total_rows=2,
            utility_score=0.82,
        )
        assert len(dp.placements) == 3
        assert dp.utility_score == 0.82

    def test_feedback_event_required_fields(self) -> None:
        fe = FeedbackEvent(
            fingerprint="abc123",
            field_name="chart_type",
            inferred_value="bar",
            user_value="bar_horizontal",
        )
        assert fe.panel_id is None
        assert fe.user_value == "bar_horizontal"

    def test_feedback_event_optional_fields(self) -> None:
        fe = FeedbackEvent(
            fingerprint="abc123",
            field_name="col_span",
            inferred_value="6",
            user_value="8",
            panel_id="p1",
            dashboard_id="d1",
        )
        assert fe.dashboard_id == "d1"


class TestContractRoles:
    """Validate the allowed role and role-type values."""

    def test_valid_column_roles(self) -> None:
        from sqlviz_inference.contracts.column_roles import VALID_ROLES
        assert "metric" in VALID_ROLES
        assert "dimension" in VALID_ROLES
        assert "time" in VALID_ROLES
        assert "id" in VALID_ROLES
        assert "percentage" in VALID_ROLES
        assert "rank" in VALID_ROLES
        assert "category" in VALID_ROLES
        assert len(VALID_ROLES) == 7

    def test_valid_dashboard_roles(self) -> None:
        from sqlviz_inference.contracts.layout import DASHBOARD_ROLES
        expected = {
            "resumen_ejecutivo", "historia_principal", "explicacion_secundaria",
            "diagnostico", "tabla_de_detalle", "control",
        }
        assert DASHBOARD_ROLES == expected

    def test_constraint_rule_types(self) -> None:
        hard = ConstraintViolation("pie", "rule", "hard", "reason")
        soft = ConstraintViolation("bar", "rule", "soft", "reason", penalty=0.3)
        assert hard.rule_type == "hard"
        assert soft.rule_type == "soft"
