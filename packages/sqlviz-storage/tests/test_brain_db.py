"""Tests for brain_db: path resolution and singleton connection.

Scenarios:
  - get_brain_path() returns a Path inside ~/.sqlviz/ named brain.duckdb.
  - get_brain_path() creates ~/.sqlviz/ when it does not exist.
  - get_brain_connection() called twice returns the same Python object (is).
  - brain.duckdb retains its _brain_meta signature after close + reopen.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
import sqlviz_storage.brain_db as brain_module
from sqlviz_storage.brain_db import get_brain_connection, get_brain_path

# ── Autouse fixture: guarantee a clean singleton state per test ───────────────

@pytest.fixture(autouse=True)
def _reset_brain_conn() -> Generator[None, None, None]:
    """Close any open brain connection and reset the module-level singleton."""
    brain_module._brain_conn = None
    yield
    if brain_module._brain_conn is not None:
        brain_module._brain_conn.close()
    brain_module._brain_conn = None


# ── get_brain_path ────────────────────────────────────────────────────────────

class TestGetBrainPath:

    def test_path_ends_with_sqlviz_brain_duckdb(self) -> None:
        path = get_brain_path()
        assert path.name == "brain.duckdb"
        assert path.parent.name == ".sqlviz"
        assert path.parent.parent == Path.home()

    def test_creates_sqlviz_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        brain_dir = tmp_path / ".sqlviz"
        assert not brain_dir.exists()
        get_brain_path()
        assert brain_dir.exists()

    def test_directory_creation_is_idempotent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        get_brain_path()
        get_brain_path()  # must not raise even though dir already exists


# ── get_brain_connection ──────────────────────────────────────────────────────

class TestGetBrainConnection:

    @pytest.fixture
    def brain_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Redirect get_brain_path() to a temp location for isolation."""
        p = tmp_path / ".sqlviz" / "brain.duckdb"
        (tmp_path / ".sqlviz").mkdir()
        monkeypatch.setattr(brain_module, "get_brain_path", lambda: p)
        return p

    def test_same_object_returned_twice(
        self, brain_path: Path  # noqa: ARG002
    ) -> None:
        conn1 = get_brain_connection()
        conn2 = get_brain_connection()
        assert conn1 is conn2

    def test_brain_meta_app_row(self, brain_path: Path) -> None:  # noqa: ARG002
        conn = get_brain_connection()
        row = conn.execute(
            "SELECT value FROM _brain_meta WHERE key = 'app'"
        ).fetchone()
        assert row is not None and row[0] == "sqlviz-brain"

    def test_brain_meta_version_row(self, brain_path: Path) -> None:  # noqa: ARG002
        conn = get_brain_connection()
        row = conn.execute(
            "SELECT value FROM _brain_meta WHERE key = 'version'"
        ).fetchone()
        assert row is not None and row[0] == "0.2.0"

    def test_brain_meta_persists_after_reopen(
        self, brain_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # First connection — creates and seeds brain.duckdb
        conn1 = get_brain_connection()
        conn1.close()
        brain_module._brain_conn = None

        # Redirect again so the second open hits the same file
        monkeypatch.setattr(brain_module, "get_brain_path", lambda: brain_path)

        # Second connection — must read existing signature, not re-seed
        conn2 = get_brain_connection()
        row = conn2.execute(
            "SELECT value FROM _brain_meta WHERE key = 'app'"
        ).fetchone()
        assert row is not None and row[0] == "sqlviz-brain"
