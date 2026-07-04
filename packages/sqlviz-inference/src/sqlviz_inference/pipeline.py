from __future__ import annotations

import time

from .chart.chart_engine import ChartEngine
from .context import RuntimeContext
from .features.feature_engine import FeatureEngine
from .filters.filter_engine import FilterEngine
from .filters.range_pairing import pair_range_filters
from .intent.intent_engine import IntentEngine
from .layout.layout_engine import LayoutEngine
from .parser.sql_parser import SQLParser
from .semantic.semantic_engine import SemanticEngine
from .title.title_engine import TitleEngine


class RuntimePipeline:
    """
    Coordinates the execution of all inference modules in the correct order.
    This is the ONLY place that knows the module execution order.
    Modules never call each other directly.
    """

    def __init__(self) -> None:
        self.parser = SQLParser()
        self.features = FeatureEngine()
        self.semantic = SemanticEngine()
        self.intent = IntentEngine()
        self.chart = ChartEngine()
        self.layout = LayoutEngine()
        self.filters = FilterEngine()
        self.title = TitleEngine()

    def run(self, context: RuntimeContext) -> RuntimeContext:
        """
        Execute the complete pipeline.
        Each module runs even if previous modules logged errors —
        graceful degradation means we always produce a result.
        """
        start_time = time.time()

        context = self.parser.run(context)
        context = self.features.run(context)
        context = self.semantic.run(context)
        context = self.intent.run(context)
        context = self.chart.run(context)
        context = self.layout.run(context)
        context = self.filters.run(context)
        context.filter_controls = pair_range_filters(context.filter_controls)
        context = self.title.run(context)

        elapsed_ms = (time.time() - start_time) * 1000
        context.score_trace["pipeline"] = {
            "elapsed_ms": round(elapsed_ms, 2),
            "errors": context.errors,
            "modules_run": [
                "parser", "features", "semantic", "intent",
                "chart", "layout", "filters", "title",
            ],
        }

        return context
