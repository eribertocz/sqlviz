from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IntentEvidence:
    signal: str
    weight: float
    direction: str   # "for" | "against"


@dataclass
class IntentResult:
    """
    Output of AnalyticalIntentModel (Fase C+).
    Replaces the label+score of IntentEngine with structured evidence.
    The V0.1 IntentEngine becomes a signal generator consumed by this.
    """

    primary_intent: str
    secondary_intents: list[str] = field(default_factory=list)
    evidence_for: list[IntentEvidence] = field(default_factory=list)
    evidence_against: list[IntentEvidence] = field(default_factory=list)
    required_visual_properties: list[str] = field(default_factory=list)
    confidence: float = 0.0
