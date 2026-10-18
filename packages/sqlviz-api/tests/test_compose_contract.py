"""HTTP composition validation, wire compatibility and engine isolation."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlviz_api.compose_contract import (
    MAX_COMPOSE_PANELS,
    CompositionInferenceInput,
)
from sqlviz_inference.dashboard import DashboardEngine
from sqlviz_inference.result import InferenceResult
from test_compose import _ir


@pytest.fixture
def inference(client: TestClient) -> dict[str, Any]:
    return _ir(client, "SELECT SUM(v) AS total FROM (VALUES (42)) t(v)")


def compose(client: TestClient, inference: dict[str, Any]):
    return client.post("/api/v1/compose", json=[{
        "panel_id": "p1", "inference_result": inference,
    }])


@pytest.mark.parametrize("field,value", [
    ("col_span", 0), ("col_span", 13), ("col_span", True),
    ("col_span", "6"), ("col_span", 6.5), ("col_span", None),
    ("row_span", 0), ("row_span", 4), ("row_span", False),
    ("panel_height_px", 119), ("panel_height_px", 901),
    ("panel_height_px", "360"), ("chart_winner", []),
    ("intent_winner", {}), ("fallback_applied", "false"),
    ("chart_raw_score", "0.8"), ("feature_vector", [True]),
    ("errors", [1]), ("elapsed_ms", -1), ("filter_controls", {}),
    ("data_profile", {"row_count": "1"}), ("visual_spec", []),
    ("execution_state", "other"), ("result_schema_version", "2"),
    ("unknown_field", "ignored?"),
])
def test_invalid_result_never_reaches_engine(
    client: TestClient, inference: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
    field: str, value: Any,
) -> None:
    def unexpected(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Invalid input reached the composition engine")

    monkeypatch.setattr(DashboardEngine, "compose", unexpected)
    inference[field] = value
    response = compose(client, inference)
    assert response.status_code == 422
    assert response.json()["detail"]
    # The established error shape exposes location/type/message, never raw
    # diagnostics, credentials or Python validation exception context.
    assert all(set(error) == {"type", "loc", "msg"} for error in response.json()["detail"])


def test_empty_result_returns_validation_error(client: TestClient) -> None:
    response = compose(client, {})
    assert response.status_code == 422
    assert ["body", 0, "inference_result", "col_span"] in [
        error["loc"] for error in response.json()["detail"]
    ]


@pytest.mark.parametrize("body", [
    {}, None, [None], [{"panel_id": "p1"}],
])
def test_invalid_envelope(client: TestClient, body: Any) -> None:
    response = client.post("/api/v1/compose", content=json.dumps(body), headers={
        "Content-Type": "application/json",
    })
    assert response.status_code == 422


@pytest.mark.parametrize("panel_id", ["", "   ", "x" * 129, 12, True])
def test_invalid_identity(client: TestClient, inference: dict[str, Any], panel_id: Any) -> None:
    response = client.post("/api/v1/compose", json=[{
        "panel_id": panel_id, "inference_result": inference,
    }])
    assert response.status_code == 422


def test_duplicate_ids_cannot_mix_results(client: TestClient, inference: dict[str, Any]) -> None:
    other = {**inference, "title": "A different result"}
    response = client.post("/api/v1/compose", json=[
        {"panel_id": "same", "inference_result": inference},
        {"panel_id": "same", "inference_result": other},
    ])
    assert response.status_code == 422


def test_unknown_envelope_fields_rejected(client: TestClient, inference: dict[str, Any]) -> None:
    response = client.post("/api/v1/compose", json=[{
        "panel_id": "p1", "inference_result": inference, "pinned_span": 12,
    }])
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["chart_raw_score", "score_trace", "explanation"])
@pytest.mark.parametrize("number", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_json_returns_422(
    client: TestClient, inference: dict[str, Any], field: str, number: float,
) -> None:
    value: Any = number
    if field == "score_trace":
        value = {"nested": [{"value": number}]}
    elif field == "explanation":
        value = [{"value": number}]
    inference[field] = value
    # Send explicitly: the HTTP client itself refuses non-standard JSON numbers.
    response = client.post("/api/v1/compose", content=json.dumps([{
        "panel_id": "p1", "inference_result": inference,
    }]), headers={"Content-Type": "application/json"})
    assert response.status_code == 422


@pytest.mark.parametrize("mutation", [
    {"orientation": "diagonal"}, {"y_fields": [1]},
    {"stack": "false"}, {"schema_version": "2"}, {"unknown": 1},
])
def test_nested_visual_contract(
    client: TestClient, inference: dict[str, Any], mutation: dict[str, Any],
) -> None:
    inference["visual_spec"].update(mutation)
    assert compose(client, inference).status_code == 422


@pytest.mark.parametrize("mutation", [
    {"col_span_min": 8, "col_span_preferred": 6},
    {"height_px_preferred": 120, "height_px_min": 240},
])
def test_nested_layout_ranges(
    client: TestClient, inference: dict[str, Any], mutation: dict[str, Any],
) -> None:
    inference["layout_declaration"].update(mutation)
    assert compose(client, inference).status_code == 422


def test_original_wire_result_preserved(client: TestClient, inference: dict[str, Any]) -> None:
    inference["title"] = "Facturaci\u00f3n por regi\u00f3n"
    inference["visual_spec"]["x_label"] = "Regi\u00f3n"
    inference["visual_spec"]["y_label"] = "Importe"
    # Do not replace explicit nulls or inject defaults into older wire results.
    del inference["trace_id"]
    del inference["result_schema_version"]
    del inference["visual_spec"]["tooltip_fields"]
    inference["score_trace"] = {"opaque": [None, False, 0, 0.5, "custom"]}
    response = compose(client, inference)
    assert response.status_code == 200
    returned = response.json()["rows"][0]["panels"][0]["inference_result"]
    assert json.dumps(returned, sort_keys=True) == json.dumps(inference, sort_keys=True)


def test_domain_adapter_restores_nested_dataclasses(inference: dict[str, Any]) -> None:
    result = CompositionInferenceInput.model_validate(inference).to_domain()
    assert isinstance(result, InferenceResult)
    assert result.visual_spec is not None
    assert result.visual_spec.chart_type == inference["visual_spec"]["chart_type"]
    assert result.data_profile is not None
    assert result.data_profile.column_profiles[0].name == "total"
    assert result.layout_declaration is not None
    assert result.layout_declaration.col_span_min >= 1
    assert result.dashboard_role is not None
    assert result.dashboard_role.role
    assert result.explanation_v2 is not None
    assert result.explanation_v2.full_text
    # A newly added domain field must trigger a deliberate wire-contract review.
    assert set(asdict(result)) == {field.name for field in fields(InferenceResult)}
    assert set(CompositionInferenceInput.model_fields) == set(asdict(result))


def test_panel_count_limit_and_boundary(client: TestClient, inference: dict[str, Any]) -> None:
    # Use the backwards-compatible required-only result, under the 1 MiB limit.
    required = {
        key: value for key, value in inference.items()
        if CompositionInferenceInput.model_fields[key].is_required()
    }
    required["score_trace"] = {}
    body = [{"panel_id": f"p{i}", "inference_result": required}
            for i in range(MAX_COMPOSE_PANELS)]
    accepted = client.post("/api/v1/compose", json=body)
    assert accepted.status_code == 200
    assert sum(len(row["panels"]) for row in accepted.json()["rows"]) == MAX_COMPOSE_PANELS
    body.append({"panel_id": "extra", "inference_result": required})
    rejected = client.post("/api/v1/compose", json=body)
    assert rejected.status_code == 422
    assert any(error["type"] == "too_long" for error in rejected.json()["detail"])


@pytest.mark.parametrize("sql", [
    "SELECT 1 AS n",
    "SELECT * FROM (VALUES ('North', 1), ('South', 2)) t(region, revenue)",
    "SELECT * FROM (VALUES (DATE '2025-01-01', 1), (DATE '2025-01-02', 2)) t(day, sales)",
    "SELECT i AS x, i * i AS y FROM range(30) t(i)",
    "SELECT 1 AS value WHERE FALSE",
    "SELECT NULL::INTEGER AS value",
])
def test_real_execution_results_remain_compatible(client: TestClient, sql: str) -> None:
    inference = _ir(client, sql)
    response = compose(client, inference)
    assert response.status_code == 200, response.text
    assert response.json()["rows"][0]["panels"][0]["inference_result"] == inference


def test_openapi_publishes_typed_composition(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    body_schema = schema["paths"]["/api/v1/compose"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert body_schema["$ref"].endswith("/ComposeRequest")
    contract = schema["components"]["schemas"]["ComposeRequest"]
    assert contract["type"] == "array"
    assert contract["maxItems"] == MAX_COMPOSE_PANELS
