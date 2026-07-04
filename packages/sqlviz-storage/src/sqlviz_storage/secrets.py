"""DuckDB Secrets wrapper for external database credentials.

External database credentials (PostgreSQL, MySQL) are stored as DuckDB
Secrets.  Passwords are never logged, never returned by list_secrets(),
and never stored in the `connections` table — only the secret name is
cross-referenced.  DuckDB redacts passwords in duckdb_secrets() output
automatically (shown as "password=redacted" in the secret_string column).

Usage pattern:
    create_secret(conn, "analytics_pg", "postgres", host, port, db, user, pw)
    attach_via_secret(conn, "analytics", "analytics_pg", "postgres")
    # SQL can now reference analytics.table_name
"""

from __future__ import annotations

import re

import duckdb

# ── Validation ────────────────────────────────────────────────────────────────

_VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_ALLOWED_TYPES: frozenset[str] = frozenset({"postgres", "mysql"})


def _require_safe_identifier(value: str, label: str) -> None:
    if not _VALID_IDENTIFIER.match(value):
        raise ValueError(
            f"Invalid {label} {value!r}: must match [A-Za-z_][A-Za-z0-9_]*"
        )


def _require_safe_type(secret_type: str) -> None:
    if secret_type.lower() not in _ALLOWED_TYPES:
        raise ValueError(
            f"Unsupported secret type {secret_type!r}. "
            f"Supported: {sorted(_ALLOWED_TYPES)}"
        )


def _esc(value: str) -> str:
    """Escape a value for embedding in a SQL string literal."""
    return value.replace("'", "''")


# ── Public API ────────────────────────────────────────────────────────────────

def create_secret(
    conn: duckdb.DuckDBPyConnection,
    name: str,
    secret_type: str,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
) -> None:
    """Create (or replace) a DuckDB Secret for an external database connection.

    The password is embedded via SQL string escaping and is never logged
    or included in exception messages raised from this function.

    Args:
        conn: Open connection to the .sqlviz project file.
        name: Secret name — identifier characters only ([A-Za-z_][A-Za-z0-9_]*).
        secret_type: Database type ('postgres' or 'mysql').
        host: Database host name or IP address.
        port: Database port (1–65535).
        database: Database name on the remote server.
        user: Database user name.
        password: Database password (never logged).
    """
    _require_safe_identifier(name, "secret name")
    _require_safe_type(secret_type)
    if not (1 <= port <= 65535):
        raise ValueError(f"Port must be 1–65535, got {port}")

    sql = (
        f"CREATE OR REPLACE SECRET {name} ("
        f"  TYPE {secret_type.upper()},"
        f"  HOST '{_esc(host)}',"
        f"  PORT {port},"
        f"  DATABASE '{_esc(database)}',"
        f"  USER '{_esc(user)}',"
        f"  PASSWORD '{_esc(password)}'"
        f")"
    )
    try:
        conn.execute(sql)
    except Exception as exc:
        # Re-raise without the password in the message.
        raise RuntimeError(
            f"Failed to create secret {name!r} ({secret_type}) — check credentials"
        ) from exc


def attach_via_secret(
    conn: duckdb.DuckDBPyConnection,
    alias: str,
    secret_name: str,
    secret_type: str,
) -> None:
    """ATTACH an external database using a previously created named secret.

    Requires the matching DuckDB extension to be installed
    (e.g. the 'postgres' extension for secret_type='postgres').

    Args:
        conn: Open connection to the .sqlviz project file.
        alias: The alias to use in SQL (e.g. ``analytics`` →
               ``SELECT * FROM analytics.table``).
        secret_name: Name of an existing secret created by create_secret().
        secret_type: Must match the type used when the secret was created.
    """
    _require_safe_identifier(alias, "alias")
    _require_safe_identifier(secret_name, "secret name")
    _require_safe_type(secret_type)

    sql = (
        f"ATTACH '' AS {alias} "
        f"(TYPE {secret_type.upper()}, SECRET {secret_name})"
    )
    try:
        conn.execute(sql)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to attach {alias!r} via secret {secret_name!r}"
        ) from exc


def list_secrets(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """Return the names of all secrets registered in this connection.

    Passwords are never included — DuckDB redacts them in duckdb_secrets()
    output (shown as "password=redacted" in the secret_string column).
    """
    rows = conn.execute("SELECT name FROM duckdb_secrets()").fetchall()
    return [row[0] for row in rows]


def delete_secret(conn: duckdb.DuckDBPyConnection, name: str) -> None:
    """Delete a named secret from this connection.

    Args:
        conn: Open connection to the .sqlviz project file.
        name: Name of the secret to delete.

    Raises:
        ValueError: If the name contains unsafe characters.
        RuntimeError: If DuckDB reports an error (e.g. secret not found).
    """
    _require_safe_identifier(name, "secret name")
    try:
        conn.execute(f"DROP SECRET {name}")
    except Exception as exc:
        raise RuntimeError(f"Failed to delete secret {name!r}") from exc
