"""Admin password hashing and verification (DOC7 Section 3.1).

bcrypt with cost factor 12 — ~250ms per hash on commodity hardware.
Deliberately slow to resist brute force; fast enough for the one admin.

NEVER: plaintext password in logs, error messages, or return values.
"""

from __future__ import annotations

from datetime import datetime, timezone

import bcrypt
import duckdb


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Malformed or empty hash — fail closed, no information leak
        return False


def get_stored_password_hash(conn: duckdb.DuckDBPyConnection) -> str:
    row = conn.execute("SELECT password_hash FROM _sqlviz_auth").fetchone()
    if row is None:
        return ""
    return str(row[0])


def set_admin_password(conn: duckdb.DuckDBPyConnection, plain_password: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hashed = hash_password(plain_password)
    conn.execute(
        "UPDATE _sqlviz_auth SET password_hash = ?, updated_at = ?",
        [hashed, now],
    )
