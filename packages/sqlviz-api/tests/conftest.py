"""Shared fixtures for sqlviz-api tests.

The client fixture creates a fresh .sqlviz project in a temp directory,
wires it into the FastAPI app via create_app(), and yields a TestClient.
No real files outside tmp_path are touched.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlviz_api.main import create_app
from sqlviz_storage.project_db import create_project


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    conn = create_project(str(tmp_path / "test.sqlviz"))
    app = create_app(conn)
    with TestClient(app) as c:
        yield c
    conn.close()
