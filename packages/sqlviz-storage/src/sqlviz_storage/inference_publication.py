"""Short metadata transaction for an inference computed outside the project DB."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import duckdb
from sqlviz_core.models.panels import Panel

from sqlviz_storage.dashboard_repository import DashboardNotFound, DashboardRepository
from sqlviz_storage.panel_repository import PanelNotFound, PanelRepository
from sqlviz_storage.timestamps import modification_timestamp
from sqlviz_storage.transactions import project_transaction


class InferencePublicationConflict(Exception):
    """The inputs changed or a competing writer prevented the complete publication."""


@contextmanager
def inference_publication(
    db: duckdb.DuckDBPyConnection,
    panel_id: str,
    *,
    expected_sql: str,
    expected_chart_override: str | None,
) -> Iterator[Panel]:
    """Verify captured inputs, fence metadata writes and publish all or nothing.

    Execute and infer BEFORE entering this context. Its transaction contains
    only trusted metadata reads/writes, including optional classification of
    the parent. The yielded panel carries current size and presentation choices.
    SQL equality checks input compatibility, never identity or query matching.

    The parent fence conflicts with script commits and dashboard deletion. The
    conditional panel fence conflicts with legacy edits/deletion that do not
    touch the parent. A failure during the body or COMMIT rolls back both rows.
    Do not nest this context in another project transaction.
    """
    try:
        with project_transaction(db):
            try:
                panel = PanelRepository(db).get(panel_id)
                parent = DashboardRepository(db).get(panel.dashboard_id)
            except (PanelNotFound, DashboardNotFound) as exc:
                raise InferencePublicationConflict("Execution inputs no longer exist") from exc
            if (
                panel.sql_content != expected_sql
                or panel.chart_user_override != expected_chart_override
            ):
                raise InferencePublicationConflict("Execution inputs changed")

            db.execute(
                "UPDATE dashboards SET updated_at = ? WHERE id = ?",
                [modification_timestamp(parent.updated_at), parent.id],
            )
            yield panel
            # Last write guarantees a real modification even when the inference
            # primitive used the same second-granularity timestamp as before.
            row = db.execute(
                "UPDATE panels SET updated_at = ? "
                "WHERE id = ? AND COALESCE(sql_content, '') = ? "
                "AND chart_user_override IS NOT DISTINCT FROM ? RETURNING id",
                [
                    modification_timestamp(panel.updated_at), panel.id, expected_sql,
                    expected_chart_override,
                ],
            ).fetchone()
            if row is None:
                raise InferencePublicationConflict("Execution inputs changed")
    except (duckdb.TransactionException, duckdb.ConstraintException) as exc:
        raise InferencePublicationConflict("Inference publication conflicted") from exc
