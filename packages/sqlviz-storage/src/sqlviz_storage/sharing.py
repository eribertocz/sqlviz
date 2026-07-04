"""Share-link token generation and verification (DOC7 Section 4).

Token = SHA256(dashboard_id:nonce:session_secret)[:24 hex chars]

The nonce is per-share (not per-dashboard), which is what makes each share's
token unique and independently revocable. Two shares for the same dashboard
produce two different, independently revocable tokens. This is the design fix
described in DOC7 §4.1 and §8.1 (fourth review round).

verify_share_token() always works from a real row looked up by token in the
shares table — it never recomputes from just the dashboard_id. This is the
"lookup flow" described in DOC7 §4.2: find the row by token first, THEN verify
that the row is not revoked and that the stored token is still consistent with
the current session_secret (i.e. the secret hasn't been regenerated since this
share was created).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

import duckdb


def generate_session_secret() -> str:
    """Generate a new project-wide session secret. Called at project creation."""
    return secrets.token_urlsafe(32)


def generate_share_nonce() -> str:
    """Generate a per-share nonce. Called once per share at creation time."""
    return secrets.token_urlsafe(16)


def generate_share_token(
    dashboard_id: str,
    share_nonce: str,
    session_secret: str,
) -> str:
    """Derive a share token from three inputs.

    Depending on all three means:
    - Two shares for the same dashboard always differ (different nonces).
    - Regenerating the session_secret invalidates ALL shares at once.
    """
    payload = f"{dashboard_id}:{share_nonce}:{session_secret}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def verify_share_token(
    token: str,
    share_row: dict[str, object],
    session_secret: str,
) -> bool:
    """Verify a token against a row already looked up from the shares table.

    Returns False (not raises) if:
      - share_row["revoked"] is True
      - the token doesn't match (secret rotated, or data integrity issue)
    """
    if share_row.get("revoked"):
        return False
    expected = generate_share_token(
        str(share_row["dashboard_id"]),
        str(share_row["nonce"]),
        session_secret,
    )
    return secrets.compare_digest(token, expected)


def get_session_secret(conn: duckdb.DuckDBPyConnection) -> str:
    """Read the current session_secret from _sqlviz_auth."""
    row = conn.execute("SELECT session_secret FROM _sqlviz_auth").fetchone()
    if row is None:
        return ""
    return str(row[0])


def regenerate_session_secret(conn: duckdb.DuckDBPyConnection) -> str:
    """Generate and persist a new session_secret, invalidating all existing shares.

    All existing share tokens were derived from the old secret; verify_share_token()
    will now fail for every existing share because the expected value changes.
    Existing rows in 'shares' are kept for audit history — they simply become
    permanently unverifiable (DOC7 §4.4).
    """
    new_secret = generate_session_secret()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(
        "UPDATE _sqlviz_auth SET session_secret = ?, updated_at = ?",
        [new_secret, now],
    )
    return new_secret
