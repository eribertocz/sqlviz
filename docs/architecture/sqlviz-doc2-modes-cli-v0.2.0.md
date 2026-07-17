# SQLviz — Modes & CLI
**Version:** v0.2.0 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-08
**Changes from v0.1.0:** .sqlviz is now DuckDB. Quack server for concurrency.
Admin login with password. Viewer access via hashed link. Sharing modes.

---

## 1. Project Modes

SQLviz operates in two modes.
The code is identical across both modes — only the storage changes.

### Mode 1 — Demo Mode

```
sqlviz
```

No arguments. No files. No configuration.
SQLviz starts instantly with an in-memory DuckDB database.

```
Purpose:       Try SQLviz without creating any files
Storage:       DuckDB :memory: — disappears on exit
Persistence:   None — all data is lost when SQLviz closes
Use case:      First time users, testing, presentations
Admin login:   Not required in demo mode
```

Demo mode is the full system running in memory.
Every feature available in persistent mode works in demo mode.

### Mode 2 — Persistent Mode

```
sqlviz my_project
sqlviz path/to/my_project
```

```
Purpose:       Real work, saved projects
Storage:       DuckDB file on disk (.sqlviz extension)
Persistence:   Full — survives restarts
Admin login:   Required
Use case:      Daily analytical work, sharing dashboards
```

---

## 2. The CLI

SQLviz CLI is designed after DuckDB.
The simplest possible interface.

```bash
# Demo mode — no files, no arguments, no login
sqlviz

# Persistent mode — create or open project
sqlviz my_project              # creates my_project.sqlviz
sqlviz my_project              # opens existing my_project.sqlviz
sqlviz path/to/my_project      # explicit path
```

### CLI decision tree

```
sqlviz called
    │
    ├── No arguments
    │       └── Start in demo mode (DuckDB :memory:)
    │           → Print: "Demo mode — data will not be saved"
    │           → Open browser: http://localhost:4000
    │           → No login required
    │
    └── Has argument
            │
            ├── File exists + valid SQLviz signature
            │       └── Open existing project
            │           → Ask: "Admin password:"
            │           → Open browser: http://localhost:4000
            │
            ├── File exists + invalid signature
            │       └── Error: "Not a valid SQLviz project"
            │           → Exit cleanly
            │
            └── File does not exist
                    └── Create new project
                        → Ask: "Set admin password:"
                        → Confirm password
                        → Create my_project.sqlviz (DuckDB)
                        → Open browser: http://localhost:4000
```

### CLI output

```bash
# Demo mode
$ sqlviz
  ███████╗██████╗ ██╗    ██╗   ██╗██╗███████╗
  ...
  Demo mode — memory only, no files created
  Opening browser: http://localhost:4000

# New project
$ sqlviz my_project
  ███████╗██████╗ ██╗    ██╗   ██╗██╗███████╗
  ...
  Set admin password: ****
  Confirm password:   ****
  Project created: my_project.sqlviz
  Opening browser: http://localhost:4000

# Existing project
$ sqlviz my_project
  ███████╗██████╗ ██╗    ██╗   ██╗██╗███████╗
  ...
  Admin password: ****
  Project: my_project
  Opening browser: http://localhost:4000

# Invalid file
$ sqlviz some_database.sqlviz
  ███████╗██████╗ ██╗    ██╗   ██╗██╗███████╗
  ...
  Error: some_database.sqlviz is not a valid SQLviz project.
```

---

## 3. What Happens at Startup

When SQLviz starts, three things happen in order:

```
1. Open .sqlviz with DuckDB
   → DuckDB is the only database engine
   → All project data lives here

2. Start Quack server
   → Quack exposes DuckDB via HTTP (DuckDB core extension, v1.5.3+)
   → Handles concurrency between admin and viewers
   → Admin connects read/write
   → Viewers connect read-only
   → Multiple viewers simultaneously — no conflicts

3. Start FastAPI
   → Serves the UI on port 4000
   → Communicates with DuckDB via Quack
```

```python
# cli.py — simplified startup

conn = duckdb.connect("my_project.sqlviz")

# Start Quack — handles admin/viewer concurrency via HTTP
conn.execute("INSTALL quack FROM core_nightly")
conn.execute("LOAD quack")
conn.execute("CALL quack_serve('quack:localhost', token = 'token')")

# Start FastAPI — serves the UI
uvicorn.run(app, port=4000)
```

---

## 4. The .sqlviz File

### What is a .sqlviz file

A `.sqlviz` file is a standard DuckDB database
with a specific schema and a validation signature.

```
my_project.sqlviz
    │
    ├── DuckDB database (standard format)
    ├── SQLviz schema (dashboards, panels, connections, secrets)
    └── _sqlviz_meta table (validation signature)
```

### Why DuckDB and not SQLite

```
DuckDB advantages for .sqlviz:
✅ One engine for everything — no sqlite3 dependency
✅ DuckDB Secrets — credentials stored securely
✅ ATTACH to PostgreSQL, MySQL, SQLite natively
✅ Analytical queries on project data
✅ Same engine as the query executor
✅ DuckDB Quack for concurrency

SQLite was considered but rejected:
❌ Requires sqlite3 as separate dependency
❌ Cannot store DuckDB Secrets
❌ Cannot ATTACH to external databases natively
❌ Two engines (SQLite + DuckDB) is more complex than one
```

### The _sqlviz_meta signature

```sql
CREATE TABLE IF NOT EXISTS _sqlviz_meta (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL
);

INSERT OR IGNORE INTO _sqlviz_meta VALUES ('app',     'sqlviz');
INSERT OR IGNORE INTO _sqlviz_meta VALUES ('version', '0.1.0');
INSERT OR IGNORE INTO _sqlviz_meta VALUES ('created', '2026-06-08T00:00:00Z');
```

### Validation

```python
def is_sqlviz_project(path: Path) -> bool:
    if path.suffix != '.sqlviz':
        return False
    try:
        conn = duckdb.connect(str(path), read_only=True)
        row = conn.execute(
            "SELECT value FROM _sqlviz_meta WHERE key = 'app'"
        ).fetchone()
        conn.close()
        return row is not None and row[0] == 'sqlviz'
    except Exception:
        return False
```

### The .sqlviz schema

```sql
-- Project signature
CREATE TABLE _sqlviz_meta (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL
);

-- Admin credentials
CREATE TABLE _sqlviz_auth (
    password_hash VARCHAR NOT NULL,
    session_secret VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL,
    updated_at VARCHAR NOT NULL
);

-- External connections
CREATE TABLE connections (
    id          VARCHAR PRIMARY KEY,
    name        VARCHAR NOT NULL,    -- user-defined name e.g. "analytics"
    type        VARCHAR NOT NULL,    -- "postgresql" | "mysql" | "sqlite"
    config      VARCHAR NOT NULL,    -- JSON with host, port, database
    created_at  VARCHAR NOT NULL
);
-- Credentials stored in DuckDB Secrets, not here

-- Folders
CREATE TABLE folders (
    id         VARCHAR PRIMARY KEY,
    name       VARCHAR NOT NULL,
    parent_id  VARCHAR,
    sort_order INTEGER DEFAULT 0,
    created_at VARCHAR NOT NULL
);

-- Dashboards
CREATE TABLE dashboards (
    id            VARCHAR PRIMARY KEY,
    name          VARCHAR NOT NULL,
    folder_id     VARCHAR,
    connection_id VARCHAR,           -- which connection this dashboard uses
    sql_content   VARCHAR DEFAULT '', -- the SQL file content (queries separated by ;)
    sort_order    INTEGER DEFAULT 0,
    created_at    VARCHAR NOT NULL,
    updated_at    VARCHAR NOT NULL
);

-- Sharing
CREATE TABLE shares (
    id           VARCHAR PRIMARY KEY,
    dashboard_id VARCHAR NOT NULL,
    token        VARCHAR NOT NULL,   -- SHA256 hash
    mode         VARCHAR NOT NULL,   -- 'private' | 'password' | 'public'
    password_hash VARCHAR,           -- only for mode='password'
    created_at   VARCHAR NOT NULL,
    revoked      BOOLEAN DEFAULT false
);

-- Filter memory
CREATE TABLE filter_memory (
    dashboard_id VARCHAR NOT NULL,
    variable     VARCHAR NOT NULL,
    value        VARCHAR,
    updated_at   VARCHAR NOT NULL,
    PRIMARY KEY (dashboard_id, variable)
);

-- Settings
CREATE TABLE settings (
    key        VARCHAR PRIMARY KEY,
    value      VARCHAR NOT NULL,
    updated_at VARCHAR NOT NULL
);
```

---

## 5. Admin Access

### Login

The admin accesses SQLviz at `http://localhost:4000`.
A login screen appears before anything else.

```
SQLviz
──────────────────────
Admin password
[________________]
[    Sign in     ]
```

### Password setup

Password is set when the project is created:

```bash
$ sqlviz my_project
Set admin password: ****
Confirm password:   ****
```

Password is stored as a bcrypt hash in `_sqlviz_auth`.
Never stored in plain text.

### Password change

Via Settings → Security → Change admin password.

### What admin can do

```
✅ Create, edit, delete dashboards
✅ Write SQL queries
✅ Configure external connections
✅ Share dashboards (generate links)
✅ Revoke shared links
✅ See active viewers
✅ Change admin password
```

---

## 6. Viewer Access — Shared Links

### How sharing works

```
1. Admin clicks "Share" on a dashboard
2. SQLviz shows sharing options:

   Share: Revenue Analysis
   ─────────────────────────────────────
   Mode:
   ○ Private    — link only, no password
   ○ Password   — link + password required
   ○ Public     — anyone with the link

   [Generate Link]

3. SQLviz generates a hashed link
4. Admin copies and sends the link
5. Viewer opens the link — sees the dashboard directly
```

### The three sharing modes

**Private (default):**
```
→ Hashed link only
→ Works on local network
→ No password required from viewer
→ Secure enough for internal sharing
→ Revoke by regenerating the session secret
   (all existing links become invalid)

URL: http://192.168.1.100:4000/view/a3f8c2d1e9b4
```

**Password protected:**
```
→ Hashed link + password
→ Admin sets a password per dashboard
→ Viewer needs both link AND password
→ For sensitive data
→ Can be shared outside local network safely

URL: http://192.168.1.100:4000/view/a3f8c2d1e9b4
Viewer sees: password prompt before dashboard
```

**Public:**
```
→ Hashed link only
→ Anyone with the link can view
→ No password required
→ For non-sensitive reports
→ Can be embedded or shared widely

URL: http://192.168.1.100:4000/view/a3f8c2d1e9b4
Viewer sees: dashboard directly, no prompt
```

### Link generation

```python
import hashlib
import secrets

def generate_share_token(dashboard_id: str, secret: str) -> str:
    """Generate a secure hashed token for sharing."""
    payload = f"{dashboard_id}:{secret}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]

def generate_share_link(
    dashboard_id: str,
    secret: str,
    host: str,
    port: int
) -> str:
    token = generate_share_token(dashboard_id, secret)
    return f"http://{host}:{port}/view/{token}"

def verify_share_token(
    token: str,
    dashboard_id: str,
    secret: str
) -> bool:
    expected = generate_share_token(dashboard_id, secret)
    return secrets.compare_digest(token, expected)
```

### Revoking links

```
Revoke ALL links at once:
→ Settings → Security → Regenerate secret
→ All existing share links become invalid immediately
→ New links can be generated with the new secret

Revoke a specific link:
→ Dashboard → Shares → Revoke
→ That specific token is marked as revoked
→ Other links remain valid
```

### What viewers see

```
Viewer opens: http://192.168.1.100:4000/view/a3f8c2d1e9b4

Private mode:
→ Dashboard loads directly
→ No login, no SQLviz UI
→ Just the dashboard with filters
→ Read-only

Password mode:
→ Password prompt appears
→ Viewer enters password
→ Dashboard loads

Public mode:
→ Dashboard loads directly
→ Same as private but can be shared anywhere
```

---

## 7. Concurrency — Admin + Viewers

Quack handles all concurrency between admin and viewers.

```
Without Quack:
→ DuckDB allows only one writer at a time
→ Admin editing + viewer reading = potential conflict

With Quack:
→ Quack exposes DuckDB via HTTP server
→ Admin connects read/write
→ All viewers connect read-only
→ Multiple simultaneous viewers — no conflicts
→ No extra code needed in SQLviz
```

```
Admin:    write/read  via Quack → DuckDB
Viewer 1: read-only   via Quack → DuckDB
Viewer 2: read-only   via Quack → DuckDB
Viewer 3: read-only   via Quack → DuckDB
                    ↓
              Quack serializes
              all writes
              reads are concurrent
```

---

## 8. Dashboard SQL File

Each dashboard has one SQL file.
Queries are separated by `;`.
Each query becomes one panel.

```sql
-- Revenue dashboard SQL

SELECT SUM(revenue) AS total_revenue
FROM sales;

SELECT month, SUM(revenue) AS revenue
FROM sales
GROUP BY month
ORDER BY month;

WITH top_products AS (
    SELECT product, SUM(revenue) AS revenue
    FROM sales
    GROUP BY product
    ORDER BY revenue DESC
    LIMIT 10
)
SELECT * FROM top_products;
```

```
Panel 1 → KPI: total_revenue
Panel 2 → Line chart: revenue by month
Panel 3 → Bar horizontal: top 10 products
```

SQLviz splits by `;`, executes each query,
and infers the chart type for each result.

---

## Appendix — Port Reference

```
4000  → FastAPI (SQLviz UI)
quack → Quack HTTP server (DuckDB core extension, v1.5.3+)
```

---

*SQLviz Modes & CLI — v0.2.0*
*"One command. One file. Everything works."*
