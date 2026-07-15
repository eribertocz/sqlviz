"""GET /api/v1/meta — version, build info, feature flags."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=["meta"])

_VERSION = "0.2.1"


class MetaResponse(BaseModel):
    version: str
    feature_flags: dict[str, bool]


@router.get("/meta", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    return MetaResponse(
        version=_VERSION,
        feature_flags={
            "feedback_engine": True,
            "dashboard_classifier": True,
            "chart_selector": True,
            "dashboard_score": True,
        },
    )
