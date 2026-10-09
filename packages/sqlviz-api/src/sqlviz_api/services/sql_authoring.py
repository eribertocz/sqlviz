"""Application admission for definition commits; storage never executes author SQL."""

from collections.abc import Sequence

import duckdb
from sqlviz_core.models.sql_reconciliation import SqlIdentityDecision
from sqlviz_core.models.sql_script import SqlStatement
from sqlviz_storage.sql_script_repository import (
    SqlScriptCommit,
    SqlScriptRepository,
    SqlScriptSnapshot,
)

from sqlviz_api.services.queries import QueryFailure, QueryService
from sqlviz_api.services.sql_scripts import SqlScriptService


class SqlAuthoringService:
    def __init__(
        self, repository: SqlScriptRepository, scripts: SqlScriptService, queries: QueryService
    ) -> None:
        self._repository = repository
        self._scripts = scripts
        self._queries = queries

    def read(self, dashboard_id: str) -> SqlScriptSnapshot:
        return self._repository.read(dashboard_id)

    def _parse_for_commit(self, source: str) -> tuple[SqlStatement, ...]:
        statements = self._scripts.parse(source)
        for statement in statements:
            try:
                # Use the same app-local read policy and SQL size budget as
                # execution. This is syntax/eligibility only, without binding
                # tables, resolving schemas, running queries or inferring charts.
                self._queries.validate(statement.sql)
            except duckdb.ParserException:
                raise QueryFailure(
                    422,
                    "sql_commit_query_invalid",
                    "Query cannot be validated for analytical execution.",
                ) from None
        return statements

    def commit(
        self,
        dashboard_id: str,
        expected_revision: str,
        source: str,
        decisions: Sequence[SqlIdentityDecision],
    ) -> SqlScriptCommit:
        return self._repository.write(
            dashboard_id, expected_revision, source, decisions, parse=self._parse_for_commit
        )
