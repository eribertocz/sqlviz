"""Access invariants exercised without HTTP, a server or persistent files."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlviz_api.services.access import AccessDenied, AuthorizationService, Principal, SessionStore
from sqlviz_api.services.query_policy import validate_viewer_query


def test_session_expiry_is_sliding_and_uses_injected_monotonic_clock() -> None:
    now = [0.0]
    sessions = SessionStore(lifetime=10, clock=lambda: now[0])
    token = sessions.issue()
    now[0] = 8
    assert sessions.validate(token)
    now[0] = 16
    assert sessions.validate(token)
    now[0] = 27
    assert not sessions.validate(token)
    now[0] = 0
    assert not sessions.validate(token)


def test_invalid_binding_does_not_extend_a_session() -> None:
    now = [0.0]
    sessions = SessionStore(lifetime=10, clock=lambda: now[0])
    token = sessions.issue("share-A")
    now[0] = 8
    assert not sessions.validate(token, "share-B")
    now[0] = 11
    assert not sessions.validate(token, "share-A")


def test_revoking_one_binding_preserves_other_sessions() -> None:
    sessions = SessionStore()
    first = sessions.issue("A")
    second = sessions.issue("B")
    sessions.revoke_binding("A")
    assert not sessions.validate(first, "A")
    assert sessions.validate(second, "B")
    sessions.clear()
    assert not sessions.validate(second, "B")


def test_concurrent_session_creation_is_unique_and_revocation_is_visible() -> None:
    sessions = SessionStore()
    with ThreadPoolExecutor(max_workers=8) as pool:
        tokens = list(pool.map(lambda _: sessions.issue(), range(64)))
    assert len(set(tokens)) == 64
    sessions.clear()
    assert all(not sessions.validate(token) for token in tokens)


def test_app_instances_do_not_share_admin_or_viewer_sessions() -> None:
    first = AuthorizationService()
    second = AuthorizationService()
    token = first.admin_sessions.issue()
    assert first.is_admin(token)
    assert not second.is_admin(token)
    token = first.viewer_sessions.issue("share")
    assert not second.viewer_sessions.validate(token, "share")


def test_explicit_viewer_scope_never_inherits_demo_author_rights() -> None:
    access = AuthorizationService(demo_mode=True)
    assert access.require_admin(None).is_admin
    with pytest.raises(AccessDenied) as exc:
        access.require_admin(None, share_token="share")
    assert exc.value.status_code == 403


def test_dashboard_scope_is_explicit() -> None:
    Principal("viewer", "A").require_dashboard("A")
    with pytest.raises(AccessDenied):
        Principal("viewer", "A").require_dashboard("B")
    Principal("viewer", "__workspace__").require_dashboard("B")
    Principal("admin").require_dashboard("B")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1",
        "SELECT ';' AS value; -- trailing comment",
        "WITH data AS (SELECT 1 AS value) SELECT * FROM data",
        "SELECT 1 UNION ALL SELECT 2",
        "SELECT value FROM (VALUES (1), (2)) data(value) WHERE value = $value",
    ],
)
def test_read_statement_policy_accepts_supported_query_forms(sql: str) -> None:
    validate_viewer_query(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "SELECT 1; SELECT 2",
        "SELECT 1; -- comment\nDELETE FROM dashboards",
        "CREATE TABLE forbidden (id INT)",
        "SELECT 1 INTO forbidden",
        "DELETE FROM dashboards",
        "COPY dashboards TO 'output.csv'",
        "INSTALL quack",
        "WITH changed AS (DELETE FROM dashboards) SELECT * FROM changed",
    ],
)
def test_read_statement_policy_rejects_write_and_multiple_statements(sql: str) -> None:
    with pytest.raises(AccessDenied):
        validate_viewer_query(sql)
