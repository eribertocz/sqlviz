"""Operator-approved data folders: files inside are readable, everything else stays denied."""

from __future__ import annotations

import duckdb
import pytest
from sqlviz_api.main import create_app
from sqlviz_api.services.queries import QueryFailure, QueryService, resolve_data_directories
from sqlviz_storage.project_db import create_project


@pytest.fixture
def folders(tmp_path):
    allowed, other = tmp_path / "allowed", tmp_path / "other"
    allowed.mkdir()
    other.mkdir()
    duckdb.sql(f"COPY (SELECT 1 AS a, 'x' AS b) TO '{allowed / 'totals.parquet'}'")
    duckdb.sql(f"COPY (SELECT 2 AS a) TO '{other / 'secret.parquet'}'")
    (allowed / "rows.csv").write_text("a,b\n3,y\n", encoding="utf-8")
    return allowed, other


@pytest.fixture
def source():
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


def denied(service, source, sql):
    with pytest.raises(QueryFailure) as caught:
        service.execute(source, sql)
    assert caught.value.status_code == 403
    assert caught.value.code == "external_access"


def test_without_data_directories_files_stay_denied_with_guidance(folders, source):
    allowed, _ = folders
    service = QueryService()
    with pytest.raises(QueryFailure) as caught:
        service.execute(source, f"SELECT * FROM '{allowed / 'totals.parquet'}'")
    assert caught.value.code == "external_access"
    assert "--data-dir" in caught.value.detail


def test_files_inside_an_allowed_folder_are_readable(folders, source):
    allowed, _ = folders
    service = QueryService(data_directories=[allowed])
    assert service.execute(source, f"SELECT * FROM '{allowed / 'totals.parquet'}'").rows == [
        (1, "x")
    ]
    assert service.execute(
        source, f"SELECT * FROM read_csv('{allowed / 'rows.csv'}')"
    ).rows == [(3, "y")]
    forward = str(allowed / "totals.parquet").replace("\\", "/")
    assert service.execute(source, f"SELECT a FROM '{forward}'").rows == [(1,)]


@pytest.mark.parametrize(
    "template",
    [
        "SELECT * FROM '{other}/secret.parquet'",
        "SELECT * FROM '{allowed}/../other/secret.parquet'",
        "SELECT * FROM glob('{root}/*')",
        "SELECT * FROM read_text('{root}/allowed/rows.csv/../../other/secret.parquet')",
    ],
)
def test_paths_outside_allowed_folders_remain_denied(folders, source, template):
    allowed, other = folders
    service = QueryService(data_directories=[allowed])
    denied(service, source, template.format(allowed=allowed, other=other, root=allowed.parent))


def test_author_sql_cannot_widen_the_allowed_folders(folders, source):
    allowed, other = folders
    service = QueryService(data_directories=[allowed])
    with pytest.raises(QueryFailure) as caught:
        service.execute(source, f"SET allowed_directories = ['{other}']")
    assert caught.value.status_code == 403
    denied(service, source, f"SELECT * FROM '{other / 'secret.parquet'}'")


def test_missing_or_file_paths_fail_at_startup(folders):
    allowed, _ = folders
    with pytest.raises(ValueError, match="does not exist"):
        resolve_data_directories([allowed / "missing"])
    with pytest.raises(ValueError, match="not a folder"):
        resolve_data_directories([allowed / "totals.parquet"])
    assert resolve_data_directories([allowed, allowed]) == (str(allowed.resolve()),)


def test_panel_execution_reads_allowed_files_over_http(folders, tmp_path):
    from fastapi.testclient import TestClient

    allowed, _ = folders
    conn = create_project(str(tmp_path / "data.sqlviz"))
    app = create_app(conn, data_directories=[allowed])
    with TestClient(app) as client:
        client.cookies.set("sqlviz_session", app.state.authorization.admin_sessions.issue())
        dash = client.post("/api/v1/dashboards", json={"name": "Files"}).json()["id"]
        panel = client.post("/api/v1/panels", json={
            "dashboard_id": dash, "name": "P",
            "sql_content": f"SELECT a, b FROM '{allowed / 'totals.parquet'}'",
        }).json()["id"]
        response = client.post(f"/api/v1/panels/{panel}/execute")
        assert response.status_code == 200, response.text
        assert response.json()["data"] == [{"a": 1, "b": "x"}]
    conn.close()
