"""Transaction ownership and rollback for project metadata writes."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import duckdb


@contextmanager
def project_transaction(db: duckdb.DuckDBPyConnection) -> Iterator[None]:
    """Own one transaction on a request cursor; nested transactions are not supported."""
    db.begin()
    committing = False
    try:
        yield
        committing = True
        db.commit()
    except BaseException as exc:
        try:
            db.rollback()
        except duckdb.Error as rollback_error:
            # A real failed COMMIT can already have aborted its transaction.
            # Preserve that original error; do not disguise it as a rollback failure.
            already_aborted = (
                committing
                and isinstance(exc, duckdb.TransactionException)
                and isinstance(rollback_error, duckdb.TransactionException)
                and "cannot rollback - no transaction is active" in str(rollback_error)
            )
            if not already_aborted:
                raise RuntimeError("Project transaction rollback failed") from rollback_error
        raise
