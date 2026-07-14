from .chart import ChartCandidate, ChartScore
from .column_roles import ColumnRole, ColumnRoles
from .constraint import ConstraintReport, ConstraintViolation
from .explanation import Explanation
from .feedback import FeedbackEvent
from .intent import IntentEvidence, IntentResult
from .layout import DashboardPlan, DashboardRole, LayoutDeclaration, PanelPlacement
from .readability import CandidateReadability, ReadabilityResult
from .semantic_profile import SemanticProfile, SemanticRelation
from .sql_profile import SQLProfile

__all__ = [
    # Fase A — 11 V0.2 contracts
    "SQLProfile",
    "ColumnRole",
    "ColumnRoles",
    "SemanticRelation",
    "SemanticProfile",
    "IntentEvidence",
    "IntentResult",
    "ChartScore",
    "ChartCandidate",
    "ConstraintViolation",
    "ConstraintReport",
    "CandidateReadability",
    "ReadabilityResult",
    "LayoutDeclaration",
    "DashboardRole",
    "PanelPlacement",
    "DashboardPlan",
    "FeedbackEvent",
    # Fase F — explanation
    "Explanation",
]
