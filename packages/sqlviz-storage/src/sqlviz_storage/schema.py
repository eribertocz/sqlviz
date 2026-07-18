"""SQL DDL for the .sqlviz project file schema.

Source of truth: DOC2 Section 4. Eight application tables + one
migration-control table (schema_migrations), in creation order.
Each statement uses CREATE TABLE IF NOT EXISTS so the list is safe
to replay on an already-initialised file (idempotent).
"""

from __future__ import annotations

SCHEMA_STATEMENTS: list[str] = [
    # Project signature — validated by is_sqlviz_project()
    """
    CREATE TABLE IF NOT EXISTS _sqlviz_meta (
        key   VARCHAR PRIMARY KEY,
        value VARCHAR NOT NULL
    )
    """,
    # Admin credentials — password_hash set by CLI/API on first setup
    """
    CREATE TABLE IF NOT EXISTS _sqlviz_auth (
        password_hash  VARCHAR NOT NULL,
        session_secret VARCHAR NOT NULL,
        created_at     VARCHAR NOT NULL,
        updated_at     VARCHAR NOT NULL
    )
    """,
    # External data-source connections (credentials in DuckDB Secrets)
    """
    CREATE TABLE IF NOT EXISTS connections (
        id         VARCHAR PRIMARY KEY,
        name       VARCHAR NOT NULL,
        type       VARCHAR NOT NULL,
        config     VARCHAR NOT NULL,
        created_at VARCHAR NOT NULL
    )
    """,
    # Dashboard folders (tree via parent_id self-reference)
    """
    CREATE TABLE IF NOT EXISTS folders (
        id         VARCHAR PRIMARY KEY,
        name       VARCHAR NOT NULL,
        parent_id  VARCHAR,
        sort_order INTEGER DEFAULT 0,
        created_at VARCHAR NOT NULL
    )
    """,
    # Dashboards — each owns one SQL file and one connection
    """
    CREATE TABLE IF NOT EXISTS dashboards (
        id               VARCHAR PRIMARY KEY,
        name             VARCHAR NOT NULL,
        folder_id        VARCHAR,
        connection_id    VARCHAR,
        sql_content      VARCHAR DEFAULT '',
        sort_order       INTEGER DEFAULT 0,
        created_at       VARCHAR NOT NULL,
        updated_at       VARCHAR NOT NULL,
        dashboard_hint   VARCHAR,
        dashboard_domain VARCHAR,
        description      VARCHAR,
        last_run_at      VARCHAR
    )
    """,
    # Sharing — each share has its own nonce (DOC7 §4.1 fix, prevents
    # deterministic tokens; enables independent revocation per share)
    """
    CREATE TABLE IF NOT EXISTS shares (
        id            VARCHAR PRIMARY KEY,
        dashboard_id  VARCHAR NOT NULL,
        nonce         VARCHAR NOT NULL,
        token         VARCHAR NOT NULL,
        mode          VARCHAR NOT NULL,
        password_hash VARCHAR,
        created_at    VARCHAR NOT NULL,
        revoked       BOOLEAN DEFAULT false
    )
    """,
    # Filter memory — last-used value per dashboard variable
    """
    CREATE TABLE IF NOT EXISTS filter_memory (
        dashboard_id VARCHAR NOT NULL,
        variable     VARCHAR NOT NULL,
        value        VARCHAR,
        updated_at   VARCHAR NOT NULL,
        PRIMARY KEY (dashboard_id, variable)
    )
    """,
    # Project-wide settings (theme, locale, etc.)
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        VARCHAR PRIMARY KEY,
        value      VARCHAR NOT NULL,
        updated_at VARCHAR NOT NULL
    )
    """,
    # Panels — each belongs to one dashboard, carries the SQL content.
    # V0.2 Fase E adds inference override columns (DOC10 §6.14):
    #   fingerprint        — links to brain.duckdb patterns
    #   inferred_*         — written once on execute; never overwritten
    #   selected_*         — active value (= inferred until user overrides)
    #   *_user_override    — NULL until user explicitly corrects a field
    """
    CREATE TABLE IF NOT EXISTS panels (
        id                     VARCHAR PRIMARY KEY,
        dashboard_id           VARCHAR NOT NULL,
        name                   VARCHAR NOT NULL,
        sql_content            VARCHAR DEFAULT '',
        sort_order             INTEGER DEFAULT 0,
        created_at             VARCHAR NOT NULL,
        updated_at             VARCHAR NOT NULL,
        fingerprint            VARCHAR,
        inferred_chart_type    VARCHAR,
        selected_chart_type    VARCHAR,
        chart_user_override    VARCHAR,
        inferred_col_span      INTEGER,
        selected_col_span      INTEGER,
        col_span_user_override INTEGER,
        inferred_height_px     INTEGER,
        selected_height_px     INTEGER,
        height_user_override   INTEGER,
        inferred_intent_type   VARCHAR
    )
    """,
    # Migration control — one row per applied migration (id = migration id)
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        id         VARCHAR PRIMARY KEY,
        applied_at VARCHAR NOT NULL
    )
    """,
]
