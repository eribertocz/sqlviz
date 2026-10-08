"""FastAPI dependency: DuckDB connection from app.state."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

import duckdb
from fastapi import Depends, Request
from sqlviz_storage.dashboard_repository import DashboardRepository
from sqlviz_storage.folder_repository import FolderRepository

from sqlviz_api.services.dashboards import DashboardDeletionService
from sqlviz_api.services.parameters import ParameterService
from sqlviz_api.services.queries import QueryService


def get_db(request: Request) -> Iterator[duckdb.DuckDBPyConnection]:
    # Endpoints are sync `def`, so FastAPI runs them in a threadpool. A single
    # shared DuckDBPyConnection has one active result set, so concurrent
    # execute()/fetch() from different request threads clobber each other's
    # cursor (symptom: IndexError on a row with the wrong column count).
    # `.cursor()` hands each request an independent execution context over the
    # same database, which is DuckDB's supported pattern for multithreading.
    conn: duckdb.DuckDBPyConnection = request.app.state.db_conn
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


DbDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db)]


def get_dashboard_deletion(request: Request, db: DbDep) -> DashboardDeletionService:
    return DashboardDeletionService(
        DashboardRepository(db), request.app.state.authorization.viewer_sessions,
    )


DashboardDeletionDep = Annotated[DashboardDeletionService, Depends(get_dashboard_deletion)]


def get_folders(db: DbDep) -> FolderRepository:
    return FolderRepository(db)


FoldersDep = Annotated[FolderRepository, Depends(get_folders)]


def get_queries(request: Request) -> QueryService:
    return request.app.state.queries  # type: ignore[no-any-return]


QueriesDep = Annotated[QueryService, Depends(get_queries)]


def get_parameters(request: Request) -> ParameterService:
    return request.app.state.parameters  # type: ignore[no-any-return]


ParametersDep = Annotated[ParameterService, Depends(get_parameters)]
