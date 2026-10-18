"""Explicit lifecycle for the optional, local Quack service."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import duckdb

QUACK_TOKEN_ENV = "SQLVIZ_QUACK_TOKEN"
_QUACK_URI = "quack:127.0.0.1:9494"


class QuackStartupError(RuntimeError):
    """An explicitly requested Quack service could not start."""


def validate_quack_token(token: str) -> None:
    """Reject absent or trivially short credentials without disclosing them."""
    if len(token.strip()) < 32:
        raise QuackStartupError(
            f"Quack requires {QUACK_TOKEN_ENV} with at least 32 non-padding characters."
        )


@contextmanager
def quack_session(conn: duckdb.DuckDBPyConnection, token: str | None) -> Iterator[None]:
    """Start only on explicit opt-in; never install extensions or print credentials.

    Quack grants database access independently of SQLviz HTTP authorization.
    Keep it on loopback and stop it before its owning connection is closed.
    """
    if token is None:
        yield
        return

    validate_quack_token(token)
    try:
        conn.load_extension("quack")
        conn.execute("CALL quack_serve(?, token = ?)", [_QUACK_URI, token]).fetchone()
    except duckdb.Error:
        # DuckDB errors may contain SQL/parameters. Do not disclose them or
        # silently continue after an explicitly requested service fails.
        raise QuackStartupError(
            "Could not start local Quack. Check that a compatible quack extension "
            "is already installed and port 9494 is available. No extension was installed."
        ) from None

    print(f"  Quack:    {_QUACK_URI} (separate database credential)")
    try:
        yield
    finally:
        try:
            conn.execute("CALL quack_stop(?)", [_QUACK_URI]).fetchone()
        except duckdb.Error:
            print("  [warn] Could not stop Quack; its owning connection will be closed.")
