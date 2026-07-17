# SQLviz — Technical Stack
**Version:** v0.2.3 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-07-03
**Changes from v0.2.2:** FastAPI 0.139.0 noted in Section 8 —
`router.frontend()` now accepts `dependencies=[Depends(require_admin)]`,
enabling frontend protection via the same cookie auth as the API
endpoints. Scheduled for Phase 7 before the v0.1.0 tag.
**Changes from v0.2.1:** Documented FastAPI v0.138.0 `app.frontend()`
(released 2026-06-20) as the official mechanism for serving the
SvelteKit SPA build — replaces the old `StaticFiles + mount` pattern.
Added rationale and usage note to Section 8.
**Changes from v0.2.0:** Fifth review pass — explicitly declared
Pydantic, PyYAML, uvicorn, pytest, ruff, mypy (all were already
used in code examples across DOC 5/7/8 but never listed here).
Confirmed Polars, PyArrow, and Passlib are NOT needed for V0.1,
with rationale (Section 11).
**Changes from v0.1.0:** DuckDB replaces SQLite completely. Quack for concurrency.
Engine roadmap simplified: V0.1=DuckDB only, V0.2=+ClickHouse.
MotherDuck and S3 are DuckDB native — not separate engines.

---

## 1. Overview

```
Layer                Tool              Purpose
──────────────────────────────────────────────────────────
CLI                  Python + uv       Entry point
SQL Parser           sqlglot           AST generation
Inference Engine     Python            Analytical brain
Rules Loading        PyYAML            Read inference rule files
HTTP Validation       Pydantic          Request/response models
                                       at the sqlviz-api boundary
Project Storage      DuckDB (.sqlviz)  All project data
Brain Storage        DuckDB (brain)    Learned patterns
Concurrency          Quack             Admin + viewer access
API                  FastAPI           HTTP interface
ASGI Server           uvicorn           Runs the FastAPI app
Auth                 bcrypt            Password hashing (DOC 7)
Frontend             SvelteKit+Svelte5 UI
SQL Editor           Monaco Editor     Code editing
Charts               ECharts           Visualizations (V0.1)
Charts               Plotly            Statistical charts (V0.2)
Styling              Tailwind CSS v4   UI design system
Event Bus            Python in-memory  Engine communication
Testing               pytest            Unit + benchmark tests
Linting/Formatting    ruff              Code style, single tool
Type Checking         mypy              Verify type hints in CI
```

---

## 2. DuckDB — The Only Database Engine

DuckDB is the foundation of SQLviz.
It replaces SQLite completely.
It is the only database technology in the stack.

### Why DuckDB replaces SQLite

```
SQLite was considered for project metadata storage.
DuckDB is better in every dimension for SQLviz:

✅ One engine for everything
   No sqlite3 + duckdb dual dependency
   One API, one mental model

✅ DuckDB Secrets
   Credentials stored securely inside .sqlviz
   Never exposed in SQL or config files

✅ ATTACH to external databases natively
   PostgreSQL, MySQL, SQLite
   The user's data stays where it is

✅ Quack compatibility
   DuckDB + Quack = concurrent admin/viewer access
   SQLite cannot do this

✅ Analytical power on project metadata
   Complex queries on dashboards, panels, shares
   DuckDB handles these faster than SQLite

✅ Same dialect everywhere
   Project metadata queries use DuckDB SQL
   User analytics queries use DuckDB SQL
   One dialect to learn and maintain
```

### DuckDB roles in SQLviz

```
Role 1 — Project storage (.sqlviz):
    Dashboards, panels, connections, shares,
    filter memory, settings, auth, secrets
    Lives in: my_project.sqlviz

Role 2 — Query executor:
    Executes user SQL queries
    Connects to external sources via ATTACH
    Returns results to the inference engine

Role 3 — Brain storage (brain.duckdb):
    Learned inference patterns
    Feature vectors, fingerprint history
    Correction tracking, accuracy statistics
    Lives in: ~/.sqlviz/brain.duckdb
```

### DuckDB Secrets — credential management

External database credentials never appear in SQL.
They are stored as DuckDB Secrets inside .sqlviz.

```sql
-- Admin configures once in Settings UI
-- SQLviz executes this internally — user never writes it

CREATE SECRET analytics_pg (
    TYPE postgresql,
    HOST 'db.company.com',
    PORT 5432,
    DATABASE 'analytics',
    USER 'readonly_user',
    PASSWORD 'secret_password'
);

-- Dashboard SQL uses the connection name — no credentials
ATTACH '' AS analytics (TYPE postgresql, SECRET analytics_pg);
SELECT * FROM analytics.sales;
```

The user only writes:
```sql
SELECT * FROM analytics.sales;
```

SQLviz injects the ATTACH automatically before executing.

---

## 3. Quack — Concurrency Layer

Quack is a DuckDB core extension (v1.5.3+) that exposes DuckDB via an HTTP server.
It is the concurrency solution for SQLviz.

### The problem Quack solves

```
DuckDB by default:
→ One writer at a time
→ Admin editing + viewer reading = potential conflict
→ Multiple simultaneous viewers = potential issues

With Quack:
→ DuckDB exposed as HTTP server
→ Quack manages all connections
→ Admin: read/write connection
→ Viewers: read-only connections
→ Unlimited simultaneous viewers
→ Zero conflicts
→ Zero extra code in SQLviz business logic
```

### Quack startup

```python
import duckdb

conn = duckdb.connect("my_project.sqlviz")

# Three SQL calls — full concurrency via DuckDB core extension
conn.execute("INSTALL quack FROM core_nightly")
conn.execute("LOAD quack")
conn.execute("CALL quack_serve('quack:localhost', token = 'token')")
```

### Quack + secret security

```
Quack starts with a session secret.
The secret is stored in _sqlviz_auth table.
Generated once when the project is created.

Admin connection:
→ Authenticated with admin password
→ Read/write access

Viewer connection:
→ Authenticated with share token (derived from secret)
→ Read-only access
→ Token verified against secret before access granted

Revoking all shares:
→ Regenerate session secret
→ All existing tokens become invalid
→ Quack rejects them immediately
```

---

## 4. External Connections — ATTACH Pattern

DuckDB's ATTACH is the only mechanism for external data sources in V0.1.
SQLviz makes this invisible to the user.

### How it works

```
1. User configures connection in Settings:
   Name: "analytics"
   Type: PostgreSQL
   Host: db.company.com
   Database: analytics
   User/Password: stored as DuckDB Secret

2. User creates dashboard:
   Name: "Revenue"
   Connection: "analytics"

3. User writes SQL:
   SELECT SUM(revenue) FROM sales;

4. SQLviz executes internally:
   ATTACH '' AS analytics (TYPE postgresql, SECRET analytics_pg);
   SELECT SUM(revenue) FROM analytics.sales;

5. User never sees the ATTACH.
   User never sees the credentials.
   User just writes SQL.
```

### Supported external sources in V0.1

```
Via DuckDB ATTACH (native, official):
✅ PostgreSQL   → ATTACH (TYPE postgresql)
✅ MySQL        → ATTACH (TYPE mysql)
✅ SQLite       → ATTACH (TYPE sqlite)

Via DuckDB native file reading:
✅ CSV          → read_csv('file.csv')
✅ Parquet      → read_parquet('file.parquet')
✅ JSON         → read_json('file.json')

All of the above are official DuckDB features.
No community extensions. No external dependencies.
```

### What is NOT in V0.1

```
❌ ClickHouse   → V0.2 (requires separate client)
❌ BigQuery     → future
❌ Snowflake    → future
❌ MongoDB      → future

Note on MotherDuck and S3:
MotherDuck is DuckDB in the cloud — ATTACH works natively.
S3/Parquet is DuckDB native — read_parquet('s3://...') works.
These are NOT separate engines.
They work through DuckDB's native capabilities.
They are available in V0.1 without extra configuration.
```

---

## 5. Engine Roadmap

### V0.1 — DuckDB only

```
One engine. Maximum simplicity.
DuckDB handles everything.
```

### V0.2 — ClickHouse as second engine

```
ClickHouse is genuinely a different engine:
→ Different dialect (toStartOfMonth vs DATE_TRUNC)
→ Requires its own client (clickhouse-connect)
→ Cannot be handled via DuckDB ATTACH natively
→ Designed for massive volume (billions of rows)

When to use ClickHouse:
→ Data volume that DuckDB cannot handle locally
→ Existing ClickHouse infrastructure
→ Real-time analytics at scale

Dashboard with ClickHouse:
→ User creates dashboard
→ Selects "ClickHouse - events" as connection
→ Writes ClickHouse SQL dialect
→ SQLviz executes via clickhouse-connect client
```

### V0.3+

```
Evaluate based on real user demand.
No speculative engines.
```

---

## 6. The Registry Pattern

Data sources and visualization engines
use the Registry Pattern from day one.
Adding a new source never requires changing core code.

### DataSource Registry

```python
# sqlviz-core/contracts/data_source.py

class DataSourceContract(Protocol):
    name: str

    def execute(self, sql: str, context: QueryContext) -> QueryResult: ...
    def schema(self, table: str) -> SchemaResult: ...
    def test_connection(self) -> bool: ...
    def describe(self, sql: str) -> list[ColumnSchema]: ...


# V0.1 — only DuckDB registered
DataSourceRegistry.register(DuckDBSource())

# V0.2 — ClickHouse added
# DataSourceRegistry.register(ClickHouseSource())
# No changes to core code
```

### VizEngine Registry

```python
# V0.1 — only ECharts registered
VizEngineRegistry.register(EChartsEngine())

# V0.2 — Plotly added for statistical charts
# VizEngineRegistry.register(PlotlyEngine())
# No changes to core code
```

---

## 7. Visualization Engines

### V0.1 — ECharts (8 chart types)

```
KPI             → single metric display
Line            → temporal trends
Bar             → categorical comparison
Bar Horizontal  → rankings
Pie             → composition
Scatter         → correlation
Table           → detail / fallback
Histogram       → distribution
```

### V0.2 — Plotly (statistical charts)

```
Boxplot         → statistical distribution
Heatmap         → two dimensions + metric
Waterfall       → cumulative changes
Funnel          → conversion analysis
Bubble          → scatter with size
Violin          → distribution comparison
```

---

## 8. Backend Stack

> **Correction (fifth review pass):** this section originally
> listed only `duckdb sqlglot fastapi uvicorn quack` and never
> named several dependencies that DOC 5, DOC 7, and DOC 8's code
> examples already use directly. This was an omission in this
> document, not a change in what gets built — every tool below
> was already implied by code shown elsewhere. Confirmed NOT
> needed during the same pass: **Polars** (DuckDB already is the
> dataframe/analytics engine — adding Polars would reintroduce
> the exact "two engines instead of one" problem Section 11
> already rejects for Pandas) and **PyArrow** (no documented V0.1
> flow exports to Arrow directly; DuckDB carries it transitively
> if ever needed internally — add it explicitly only if a real
> V0.2+ use case requires it). **Passlib** was also considered and
> rejected — DOC 7 Section 3.1's `hash_password`/`verify_password`
> are ~15 lines directly on `bcrypt`; an abstraction wrapper adds
> nothing per Section 12's "can we implement this ourselves"
> question.

### Python 3.12+ with uv

```bash
uv add duckdb sqlglot fastapi uvicorn quack pydantic pyyaml bcrypt
uv add --dev pytest ruff mypy
uv run sqlviz my_project
```

```
Runtime dependencies:
    duckdb     → DOC 3 Section 2 (storage + query engine)
    sqlglot    → DOC 3 Section 8 below (SQL parsing)
    fastapi    → DOC 3 Section 8 below (HTTP API)
    uvicorn    → the ASGI server that actually runs FastAPI;
                 every DOC 2/8 startup code example calls
                 uvicorn.run(app, ...) — FastAPI does not run
                 standalone without it, so it is a direct
                 dependency, not merely transitive
    quack      → DOC 2 Section 7, DOC 3 Section 3 (concurrency)
    pydantic   → request/response validation at the sqlviz-api
                 HTTP boundary ONLY (see "Pydantic vs dataclasses"
                 below — this does NOT replace the @dataclass
                 models already used throughout DOC 5 and DOC 7)
    pyyaml     → DOC 5 Section 13's yaml_loader.py already reads
                 the 7 rules files with `yaml.safe_load()`;
                 never previously declared here
    bcrypt     → DOC 7 Section 3.1 (password hashing)

Development dependencies:
    pytest     → DOC 8 Phase 0/2 already assumes `uv run pytest`
                 throughout the build phases; never previously
                 declared as an actual dependency here
    ruff       → linting AND formatting in one tool (replaces the
                 black+flake8+isort combination some projects use
                 three tools for) — chosen specifically because
                 it is a single fast dependency, consistent with
                 Section 12's "is it necessary" philosophy
    mypy       → DOC 5's code is written with type hints
                 throughout (list[float], RuntimeContext, etc.);
                 without a type checker those hints are unverified
                 documentation, not a checked contract. Run in CI
                 (DOC 8, Phase 0) alongside pytest.
```

### Pydantic vs dataclasses — where each is used

```
sqlviz-inference (DOC 5)  → @dataclass everywhere (RuntimeContext,
                            InferenceResult, FilterControl, etc.)
                            Internal to the engine. No HTTP
                            boundary crosses here directly.
                            Kept as dataclasses — already written,
                            consistent, no validation-at-the-edge
                            need internally.

sqlviz-storage (DOC 2/7)  → @dataclass for the same reason
                            (ColumnSchema, ConnectionConfig, etc.)

sqlviz-api (DOC 8 Phase 4) → Pydantic BaseModel for every request/
                            response model. This is the ONE layer
                            where untrusted external input (HTTP
                            request bodies) needs runtime
                            validation, not just static type hints.
                            FastAPI uses Pydantic for this natively —
                            fighting that and writing manual
                            validation would violate Section 12's
                            "is it necessary" test in the other
                            direction (reinventing what the
                            framework already does correctly).
```

```python
# sqlviz-api/src/sqlviz_api/routers/panels.py — Pydantic at the boundary

from pydantic import BaseModel

class InferRequest(BaseModel):
    sql: str
    dashboard_id: str

class InferResponse(BaseModel):
    chart_winner: str
    title: str
    col_span: int
    # ... mirrors the relevant subset of DOC 5's InferenceResult

@router.post("/api/v1/infer")
async def infer(request: InferRequest) -> InferResponse:
    # sqlviz-inference's RuntimeContext (a dataclass) is
    # constructed and used INTERNALLY — Pydantic never crosses
    # into sqlviz-inference, it only validates the HTTP edge
    context = RuntimeContext(sql=request.sql)
    context = await runtime.execute(context)
    result = InferenceResult.from_context(context)
    return InferResponse(
        chart_winner=result.chart_winner,
        title=result.title,
        col_span=result.col_span,
    )
```

### sqlglot — SQL Parser

```python
import sqlglot

ast = sqlglot.parse_one(sql, dialect="duckdb")
has_group_by = ast.find(sqlglot.exp.Group) is not None
```

Why sqlglot:
```
✅ Proper AST — not fragile regex
✅ DuckDB dialect support native
✅ Pure Python — no external dependencies
✅ Foundation of fingerprinting and rewriting
```

### FastAPI + uvicorn

Rule: FastAPI is only a door. No business logic in routers.
uvicorn is the ASGI server process that actually serves it
(DOC 2 Section 3, DOC 8 Phase 4 startup sequence).

```python
@router.post("/api/v1/infer")
async def infer(request: InferRequest) -> InferResponse:
    context = RuntimeContext(sql=request.sql)
    context = await runtime.execute(context)
    return InferResponse.from_context(context)
```

```python
# How sqlviz-cli actually starts the server (DOC 2 Section 3,
# DOC 8 Phase 6) — uvicorn called directly, not implied
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=4000)
```

#### Serving the SvelteKit SPA — app.frontend() (FastAPI v0.138.0+)

FastAPI v0.138.0 (released 2026-06-20) added official first-party
support for serving Single-Page Applications:

```python
# main.py — Phase 4 wiring (DOC 8 Phase 4, task 6)
app.frontend("/", directory="dist")
```

This replaces the old pattern that required manual workarounds:

```python
# OLD pattern — do NOT use
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="dist", html=True))
# ^ required a separate catch-all route to handle SPA navigation
# because StaticFiles returns 404 for unknown paths like /dashboard/123
```

Why `app.frontend()` is the correct choice for SQLviz:

```
Behavior                        app.frontend()    StaticFiles(html=True)
──────────────────────────────────────────────────────────────────────
SPA route fallback to index.html  ✅ automatic      ❌ manual catch-all
API routes take priority          ✅ always          ⚠️  mount order dependent
Official FastAPI support          ✅ first-party     ❌ workaround pattern
```

The `router.frontend()` form is also available if the SPA mount
needs to live inside a sub-router, but for SQLviz the top-level
`app.frontend("/", directory="dist")` in `main.py` is sufficient.
`dist/` is the Vite/SvelteKit build output directory (DOC 8 Phase 5).

#### FastAPI 0.139.0 — router.frontend() with dependencies (Phase 7)

FastAPI 0.139.0 adds dependency support on `router.frontend()`,
enabling the SPA itself to be protected by the same `require_admin`
dependency that already guards the API endpoints:

```python
# Phase 7 upgrade — replaces the Phase 4 app.frontend() call
from sqlviz_api.routers.auth import require_admin
from fastapi import Depends

app.frontend("/", directory="dist",
             dependencies=[Depends(require_admin)])
```

This means any browser navigation to the dashboard (not just API
calls) will be rejected with 401 if no valid `sqlviz_session` cookie
is present — the browser receives a redirect to `/login` rather than
the SPA HTML. No separate middleware or catch-all route is needed.

Action: upgrade from 0.138.0 to 0.139.0 in Phase 7 (DOC 8 Phase 7,
task 3), before the v0.1.0 tag. The Phase 4 `app.frontend()` call
(no `dependencies=`) remains valid until then and does not block
any earlier phase.

---

## 9. Frontend Stack

### SvelteKit + Svelte 5

```
Rule: Frontend never infers. Frontend only renders.
All inference happens in the backend.
Frontend receives complete DashboardResponse and renders it.
```

### Monaco Editor

```
Why Monaco and not CodeMirror:
SQLviz users write complex SQL with CTEs,
window functions, multiple JOINs.
Monaco is designed for complex code editing.
It is the editor that powers VS Code.
Maintained by Microsoft.
```

### ECharts + Plotly (frontend)

Both engines registered in the frontend.
Backend sends ChartSpec with engine name.
Frontend routes to correct renderer.

```svelte
{#if chart_spec.engine === 'echarts'}
    <EChartsRenderer spec={chart_spec} />
{:else if chart_spec.engine === 'plotly'}
    <PlotlyRenderer spec={chart_spec} />
{/if}
```

### Tailwind CSS v4

```css
:root {
  --sqlviz-primary:    #6366f1;
  --sqlviz-bg:         #0f172a;
  --sqlviz-bg-surface: #1e293b;
  --sqlviz-border:     #334155;
  --sqlviz-text:       #f1f5f9;
  --sqlviz-text-muted: #94a3b8;
  --sqlviz-radius:     6px;
}
```

---

## 10. Storage Architecture

```
~/.sqlviz/
└── brain.duckdb
    ├── sql_patterns         ← learned fingerprint → chart mappings
    ├── layout_patterns      ← learned layout preferences
    ├── semantic_dict        ← learned column semantics
    ├── corrections          ← user correction history
    └── learning_stats       ← inference accuracy over time

    Scope: global to the user
    Persists across: virtual environments, upgrades, project deletions
    Belongs to: SQLviz installation, not any project


my_project.sqlviz (DuckDB)
    ├── _sqlviz_meta         ← project signature
    ├── _sqlviz_auth         ← admin password hash + session secret
    ├── dashboards           ← name, connection_id, sql_content
    ├── folders              ← folder organization
    ├── connections          ← external connection configs
    │                           credentials in DuckDB Secrets
    ├── shares               ← share tokens, modes, revocation
    ├── filter_memory        ← last used filter values
    └── settings             ← theme, preferences

    Scope: per project
    Belongs to: the user
    Can be: shared, deleted, moved, committed to Git
```

---

## 11. What We Explicitly Avoid

```
Tool            Reason rejected
──────────────────────────────────────────────────────────
SQLite          Replaced by DuckDB completely
                Two engines is more complex than one
                Cannot store DuckDB Secrets

Kafka           Requires server — violates Principle 5
Redis           Same reasons as Kafka
Kubernetes      DevOps overhead
LLMs / GPT API  External API, costs money, works offline
Pandas          DuckDB is faster — one less dependency
Polars          Same reasoning as Pandas — DuckDB is already
                the dataframe/analytics engine. Adding Polars
                would reintroduce a second engine for the exact
                role DuckDB fills (DOC 1, "DuckDB as the only
                ATTACH-capable engine" decision)
PyArrow         No V0.1 flow exports to or consumes Arrow
                directly. DuckDB carries it transitively if
                ever needed internally. Add explicitly only
                if a real V0.2+ use case requires it — not
                speculatively now
SQLAlchemy      Overkill — DuckDB Python API is sufficient
Passlib         A thin wrapper around bcrypt. DOC 7 Section
                3.1's hash_password/verify_password are ~15
                lines directly on bcrypt — the wrapper adds
                an abstraction layer with no functional gain
React/Vue       Svelte 5 is simpler, smaller bundle
CodeMirror      Not suitable for complex SQL — Monaco wins
Community extensions  Not maintained by DuckDB core team
                      Unpredictable stability
```

---

## 12. Dependency Philosophy

Every dependency must answer yes to all:

```
1. Is it necessary?
2. Is it maintained by the official team?
3. Does it work offline?
4. Is it sustainable by one person?
5. Does it have a stable API?
```

---

*SQLviz Technical Stack — v0.2.3*
*"DuckDB for everything. Quack for concurrency."*
*"One engine. Maximum simplicity."*
