from __future__ import annotations

import time

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

        context = self.parser.run(context)
        context = self.result_profiler.run(context)
        context = self.column_role_detector.run(context)
        context = self.features.run(context)
        context = self.semantic.run(context)
        context = self.intent.run(context)
        context = self.chart.run(context)
        context = self.constraint.run(context)
        context = self.feedback.run_consult(context)   # Fase E: step 6.5
        context = self.readability.run(context)
        context = self.scoring.run(context)
        context = self.feedback.run_apply(context)     # Fase E: apply override
        context = self.visual_spec_builder.run(context)
        context = self.layout.run(context)
        context = self.layout_declaration_builder.run(context)
        context = self.dashboard_role_classifier.run(context)
        context = self.filters.run(context)
        context.filter_controls = pair_range_filters(context.filter_controls)
        context = self.title.run(context)
        context = self.explanation_engine.run(context)  # Fase F: step 15
        context = self.feedback.run_persist(context)   # Fase E: step 16

        elapsed_ms = (time.time() - start_time) * 1000
        context.score_trace["pipeline"] = {
            "elapsed_ms": round(elapsed_ms, 2),
            "errors": context.errors,
            "modules_run": [
                "parser", "result_profiler", "column_role_detector",
                "features", "semantic", "intent", "chart", "constraint",
                "feedback_consult", "readability", "scoring",
                "feedback_apply", "visual_spec_builder", "layout",
                "layout_declaration_builder", "dashboard_role_classifier",
                "filters", "title", "explanation_engine", "feedback_persist",
            ],
        }

        return context
