"""Shared fixtures for sqlviz-api tests.

The client fixture creates a fresh .sqlviz project in a temp directory,
wires it into the FastAPI app via create_app(), and yields a TestClient.
No real files outside tmp_path are touched.

The brain fixture patches get_brain_connection() to use an in-memory DuckDB
so that patterns stored in ~/.sqlviz/brain.duckdb from live sessions never
pollute test expectations.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import duckdb
import pytest
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage import brain_db
from sqlviz_storage.brain_db import _ensure_tables
from sqlviz_storage.project_db import create_project


@pytest.fixture(autouse=True)
def _isolated_brain(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Replace the brain singleton with a fresh in-memory DB for every test.

    This prevents ~/.sqlviz/brain.duckdb patterns from live sessions
    from causing FeedbackEngine to override test expectations.
    """
    mem_conn = duckdb.connect(":memory:")
    _ensure_tables(mem_conn)
    monkeypatch.setattr(brain_db, "_brain_conn", mem_conn)
    yield
    monkeypatch.setattr(brain_db, "_brain_conn", None)
    mem_conn.close()


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()
