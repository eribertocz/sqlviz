"""Rollback failures cannot be advertised as safely rolled-back conflicts."""

from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import duckdb
import pytest
from sqlviz_storage.transactions import project_transaction


def test_interrupt_rolls_back_uncommitted_metadata() -> None:
    db = duckdb.connect(":memory:")
    try:
        db.execute("CREATE TABLE values_to_keep (value INTEGER)")
        with pytest.raises(KeyboardInterrupt):
            with project_transaction(db):
                db.execute("INSERT INTO values_to_keep VALUES (1)")
                raise KeyboardInterrupt
        assert db.execute("SELECT * FROM values_to_keep").fetchall() == []
    finally:
        db.close()


def test_unexpected_rollback_failure_is_not_hidden() -> None:
    db = duckdb.connect(":memory:")
    cursor = Mock(wraps=db)
    cursor.rollback.side_effect = duckdb.ConnectionException("synthetic broken cursor")
    try:
        with pytest.raises(RuntimeError, match="rollback failed"):
            with project_transaction(cast(duckdb.DuckDBPyConnection, cursor)):
                raise duckdb.TransactionException("synthetic original conflict")
        # The caller closes the cursor; this test explicitly releases its DB.
        db.rollback()
    finally:
        db.close()
