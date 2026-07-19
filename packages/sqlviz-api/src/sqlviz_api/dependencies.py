"""FastAPI dependency: DuckDB connection from app.state."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import Depends, Request


def get_db(request: Request) -> duckdb.DuckDBPyConnection:
    # Endpoints are sync `def`, so FastAPI runs them in a threadpool. A single
    # shared DuckDBPyConnection has one active result set, so concurrent
    # execute()/fetch() from different request threads clobber each other's
    # cursor (symptom: IndexError on a row with the wrong column count).
    # `.cursor()` hands each request an independent execution context over the
    # same database, which is DuckDB's supported pattern for multithreading.
    conn: duckdb.DuckDBPyConnection = request.app.state.db_conn
    return conn.cursor()


DbDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]
