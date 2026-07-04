"""FastAPI dependency: DuckDB connection from app.state."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import Depends, Request


def get_db(request: Request) -> duckdb.DuckDBPyConnection:
    conn: duckdb.DuckDBPyConnection = request.app.state.db_conn
    return conn


DbDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]
