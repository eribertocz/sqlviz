from __future__ import annotations

import time
from typing import Callable

from .chart.chart_engine import ChartEngine
from .constraint.constraint_engine import ConstraintEngine
from .context import RuntimeContext
from .explanation.explanation_engine import ExplanationEngine
from .features.feature_engine import FeatureEngine
from .feedback.feedback_engine import FeedbackEngine
from .filters.filter_engine import FilterEngine
from .filters.range_pairing import pair_range_filters
from .intent.intent_engine import IntentEngine
from .layout.dashboard_role_classifier import DashboardRoleClassifier
from .layout.layout_declaration_builder import LayoutDeclarationBuilder
from .layout.layout_engine import LayoutEngine
from .parser.sql_parser import SQLParser
from .profile.data_profile import ResultProfiler
from .readability.readability_model import ReadabilityModel
from .roles.column_role_detector import ColumnRoleDetector
from .scoring.scoring_model import ScoringModel
from .semantic.semantic_engine import SemanticEngine
from .spec.visual_spec_builder import VisualSpecBuilder
from .title.title_engine import TitleEngine
from .utils.sqlviz_logging import get_logger

_log = get_logger("pipeline")


class RuntimePipeline:
    """
    Coordinates the execution of all inference modules in the correct order.
    This is the ONLY place that knows the module execution order.
    Modules never call each other directly.
    """

    def __init__(self) -> None:
        self.parser = SQLParser()
        self.result_profiler = ResultProfiler()
        self.column_role_detector = ColumnRoleDetector()
        self.features = FeatureEngine()
        self.semantic = SemanticEngine()
        self.intent = IntentEngine()
        self.chart = ChartEngine()
        self.constraint = ConstraintEngine()
        self.feedback = FeedbackEngine()
        self.readability = ReadabilityModel()
        self.scoring = ScoringModel()
        self.visual_spec_builder = VisualSpecBuilder()
        self.layout = LayoutEngine()
        self.layout_declaration_builder = LayoutDeclarationBuilder()
        self.dashboard_role_classifier = DashboardRoleClassifier()
        self.filters = FilterEngine()
        self.title = TitleEngine()
        self.explanation_engine = ExplanationEngine()

    def run(self, context: RuntimeContext) -> RuntimeContext:
        """
        Execute the complete pipeline.
        Each module runs even if previous modules logged errors —
        graceful degradation means we always produce a result.
        """
        start_time = time.time()
        _t: dict[str, float] = {}

        def step(
            name: str,
            fn: Callable[[RuntimeContext], RuntimeContext],
            ctx: RuntimeContext,
        ) -> RuntimeContext:
            t0 = time.perf_counter()
            ctx = fn(ctx)
            _t[name] = round((time.perf_counter() - t0) * 1000, 2)
            return ctx

        context = step("parser",                   self.parser.run,                   context)
        context = step("result_profiler",           self.result_profiler.run,           context)
        context = step("column_role_detector",      self.column_role_detector.run,      context)
        context = step("features",                  self.features.run,                  context)
        context = step("semantic",                  self.semantic.run,                  context)
        context = step("intent",                    self.intent.run,                    context)
        context = step("chart",                     self.chart.run,                     context)
        context = step("constraint",                self.constraint.run,                context)
        context = step("feedback_consult",          self.feedback.run_consult,          context)
        context = step("readability",               self.readability.run,               context)
        context = step("scoring",                   self.scoring.run,                   context)
        context = step("feedback_apply",            self.feedback.run_apply,            context)

        # V0.2.2: expose all 8 chart types with normalized pct scores
        if context.scored_candidates:
            _max = max(
                (c.total_score for c in context.scored_candidates if c.eliminated_by_rule is None),
                default=1.0,
            ) or 1.0
            context.chart_alternatives = [
                {
                    "chart": c.chart_type,
                    "raw_score": round(c.total_score, 4),
                    "pct": round(max(0.0, c.total_score) / _max, 4),
                }
                for c in context.scored_candidates
            ]

        context.chart_engine_winner = context.chart_winner  # freeze engine's choice for UI ordering
        if context.chart_override:                          # apply explicit panel override
            context.chart_winner = context.chart_override

        context = step("visual_spec_builder",       self.visual_spec_builder.run,       context)
        context = step("layout",                    self.layout.run,                    context)
        context = step("layout_declaration_builder",self.layout_declaration_builder.run,context)
        context = step("dashboard_role_classifier", self.dashboard_role_classifier.run, context)
        context = step("filters",                   self.filters.run,                   context)

        t0 = time.perf_counter()
        context.filter_controls = pair_range_filters(context.filter_controls)
        _t["range_pairing"] = round((time.perf_counter() - t0) * 1000, 2)

        context = step("title",                     self.title.run,                     context)
        context = step("explanation_engine",        self.explanation_engine.run,        context)
        context = step("feedback_persist",          self.feedback.run_persist,          context)

        # Compute lifecycle execution state
        if context.errors and context.fallback_applied:
            context.execution_state = "degraded"
        elif context.errors:
            context.execution_state = "warning"
        elif context.fallback_applied:
            context.execution_state = "degraded"
        # else: stays "success"

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        context.score_trace["pipeline"] = {
            "elapsed_ms": elapsed_ms,
            "errors": context.errors,
            "execution_state": context.execution_state,
            "modules_run": list(_t.keys()),
        }
        if context.debug:
            context.score_trace["module_timings"] = _t

        _log.info(
            "pipeline complete",
            extra={
                "trace_id": context.trace_id,
                "elapsed_ms": elapsed_ms,
                "execution_state": context.execution_state,
                "error_count": len(context.errors),
            },
        )

        return context
