# SQLviz — Construction Plan
**Version:** v0.1.0 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-28
**Prerequisites:** DOC 1-5 (all prior documents)

---

## 0. Document Status — Frozen for V0.1

> A second external cross-architecture review (covering all 8
> documents together, not just DOC 5 in isolation) concluded the
> documentation set is internally consistent and ready for
> implementation, with one corrected inconsistency (DOC 4's Feature
> Vector dimension count, 35 → 38, now fixed to match DOC 5).
> This table is the explicit "stop revising, start building" marker
> requested by that review — it exists so documentation iteration
> does not continue indefinitely once implementation has begun.

```
Document                              Status              Frozen for
─────────────────────────────────────────────────────────────────
DOC 1 — Vision & Philosophy           Stable              V0.1
DOC 2 — Modes & CLI                    Stable              V0.1
DOC 3 — Technical Stack                Stable              V0.1
DOC 4 — Mathematical Foundations       Stable (38-dim       V0.1
                                       fix applied)
DOC 5 — Inference Engine Architecture  Stable              V0.1
DOC 6 — UI Design System               Stable              V0.1
DOC 7 — Security & Roles               Stable              V0.1
DOC 8 — Construction Plan (this doc)   Stable              V0.1
```

```
What "Frozen for V0.1" means:
    These documents are the source of truth for implementation.
    Changes during V0.1 construction should be RARE and must be
    logged as an explicit correction (the same way DOC 5 Section
    16 logs its own patch), never a silent rewrite.

    "Frozen" does NOT mean "perfect" — every document already
    contains its own "deferred to V0.2/V0.3" sections (DOC 5
    §16.3-16.4, DOC 6 §11, DOC 7 §7, DOC 8 §6). Those are
    intentional, tracked gaps, not violations of the freeze.
    The freeze means: no NEW undocumented gaps should appear
    once Phase 0 (DOC 8, Section 5) begins.
```

### 0.1 Review History

```
Round 1 (DOC 5 only):   Negative rules, fallback rules, YAML
                         structure, V0 chart count fixed to 8.
                         → DOC 4/5 patch v0.1.1-v0.1.2.

Round 2 (DOC 5 only):    RuntimeContext wording, trend_strength
                         vs trend_direction split (dim 38 added),
                         Section 16.1-16.4 logged.
                         → DOC 4/5 patch v0.1.3 / Section 16.

Phase 4.5 correction:    Quack wire-protocol server deferred
                         from Phase 4 to Phase 6. Phase 4
                         delivers QuackConnectionRouter
                         (routing logic, correct interface)
                         but NOT the Quack PostgreSQL server.
                         Reasons: (1) server startup belongs
                         to the CLI orchestration phase;
                         (2) DuckDB Python in-process API
                         already handles concurrent access
                         without a wire-protocol layer;
                         (3) viewer read-only isolation via
                         duckdb.connect(read_only=True) is
                         a Phase 6 upgrade to connection_
                         for_request(). Sections updated:
                         Phase 4 task 4, Phase 4 goal, Phase
                         4 exit criteria, Phase 6 tasks.
                         → This correction. 480 tests pass.

Round 3 (all 8 docs):    Cross-document consistency pass.
                         Found and fixed:
                           1. Feature vector miscounted as 38
                              instead of 39 after dim 38 was
                              added (DOC 4 + DOC 5).
                           2. DOC 8 still said DOC 6/7 "pending"
                              after both were completed.
                           3. Residual "never mutate" phrasing
                              in DOC 5 contradicting Section 16.1.
                           4. DOC 5 said "7 modules," actually
                              8 inference modules + 1 orchestrator.
                           5. DOC 6's KPI Renderer computed a
                              semantic trend label in the frontend,
                              violating DOC 6's own "frontend never
                              infers" rule — moved to DOC 5
                              (trend_direction_label field).
                           6. "Auto-layout" used ambiguously for
                              both V0.1's auto-placement (not
                              deferred) and V0.2's full no-modal
                              SQL-editing UX (deferred) — disambiguated.
                         → This pass. All 8 documents now at
                           their final v0.1.0 (or v0.1.3 for DOC 4)
                           versions, status: READY FOR IMPLEMENTATION.
```

---

## 1. Purpose of This Document

This document answers one question:

> "In what exact order do we build SQLviz, and what
>  belongs in each version?"

Every other document (1-5, and future 6-7) describes
**what** SQLviz is and **how** each piece works internally.
This document describes **the build sequence** — the only
document whose job is to turn "we know what to build" into
"here is what we build this week."

```
DOC 1 → Vision & Philosophy        (why)
DOC 2 → Modes & CLI                 (how it runs)
DOC 3 → Technical Stack             (what tools)
DOC 4 → Mathematical Foundations    (the math)
DOC 5 → Inference Engine            (the brain, in code)
DOC 6 → UI Design System            (the face)         [complete]
DOC 7 → Security & Roles            (the lock)         [complete]
DOC 8 → Construction Plan           (the order)        [this document]
```

---

## 2. The Foundational Packages

Confirmed in prior conversation (rescued from the SQLviz v0.1
prototype lessons + the ChatGPT Architecture Handbook review).
SQLviz V0.1 builds a small number of packages — not the original
16-package proposal. Extra packages are deferred until actually
needed (Section 6).

**Correction from earlier planning:** DOC 5 already merged what
were originally going to be separate `sqlviz-parser` and
`sqlviz-runtime` packages into `sqlviz-inference` as internal
modules (DOC 5, Sections 4 and 12). This is intentional — they
have no reason to be separately versioned PyPI packages in V0.1.

```
sqlviz-core        kernel: contracts, RuntimeContext, registries
sqlviz-inference   the brain: DOC 5 in full (parser, features,
                   semantic, intent, chart, layout, filter,
                   title, dashboard engines + runtime pipeline)
sqlviz-storage     DuckDB project file (.sqlviz) + brain.duckdb
sqlviz-api         FastAPI — the door
sqlviz-web         SvelteKit + Svelte 5 — the face
sqlviz-cli         the `sqlviz` command itself

= 6 packages for V0.1
```

---

## 3. Monorepo Structure

```
sqlviz/
├── packages/
│   ├── sqlviz-core/
│   │   └── src/sqlviz_core/
│   │       ├── contracts/      DataSourceContract, VizEngineContract
│   │       │                   (DOC 3, Section 2)
│   │       ├── registry/       DataSourceRegistry, VizEngineRegistry
│   │       └── models/         shared dataclasses
│   │
│   ├── sqlviz-inference/
│   │   ├── rules/              7 YAML files (DOC 5, Section 13)
│   │   ├── src/
│   │   │   ├── parser/         DOC 5, Section 4
│   │   │   ├── features/       DOC 5, Section 5
│   │   │   ├── semantic/       DOC 5, Section 6
│   │   │   ├── intent/         DOC 5, Section 7
│   │   │   ├── chart/          DOC 5, Section 8
│   │   │   ├── layout/         DOC 5, Section 9
│   │   │   ├── filters/        DOC 5, Section 10
│   │   │   ├── title/          DOC 5, Section 11
│   │   │   ├── dashboard/      DOC 5, Section 15
│   │   │   ├── utils/          DOC 5, Section 5.6-5.7
│   │   │   ├── context.py      DOC 5, Section 3
│   │   │   ├── result.py       DOC 5, Section 12.4
│   │   │   └── pipeline.py     DOC 5, Section 12.3
│   │   └── tests/
│   │       └── benchmark/      DOC 5, Section 14
│   │
│   ├── sqlviz-storage/
│   │   └── src/sqlviz_storage/
│   │       ├── project_db.py   the .sqlviz DuckDB file (DOC 2)
│   │       ├── brain_db.py     ~/.sqlviz/brain.duckdb access
│   │       ├── schema.py       DOC 2, Section 4 — full schema
│   │       └── migrations.py   DOC 2, Section 4 lifecycle
│   │
│   ├── sqlviz-api/
│   │   └── src/sqlviz_api/
│   │       ├── main.py         FastAPI app, serves sqlviz-web build via app.frontend()
│   │       ├── routers/
│   │       │   ├── dashboards.py
│   │       │   ├── panels.py
│   │       │   ├── connections.py
│   │       │   ├── shares.py   DOC 2 Section 6 + DOC 7
│   │       │   └── auth.py     DOC 2 Section 5 + DOC 7
│   │       └── quack_server.py DOC 2, Section 7
│   │
│   ├── sqlviz-web/
│   │   └── src/                SvelteKit — structure per DOC 6
│   │
│   └── sqlviz-cli/
│       └── src/sqlviz_cli/
│           └── main.py         DOC 2, Section 2 — the `sqlviz` command
│
├── pyproject.toml               workspace root, uv workspace
└── README.md
```

---

## 4. Dependency Graph — What Must Exist Before What

```
sqlviz-core
    │  (no dependencies — pure contracts and models)
    ▼
sqlviz-inference  ──depends on──▶  sqlviz-core
    │  (needs DataSourceContract, VizEngineContract)
    ▼
sqlviz-storage  ──depends on──▶  sqlviz-core
    │  (needs shared models for dashboards/panels)
    ▼
sqlviz-api  ──depends on──▶  sqlviz-core, sqlviz-inference, sqlviz-storage
    │  (orchestrates: receives SQL, calls inference,
    │   persists via storage, returns to web)
    ▼
sqlviz-web  ──depends on──▶  sqlviz-api (via HTTP, not Python import)
    │  (pure frontend, talks to API over REST/JSON)
    ▼
sqlviz-cli  ──depends on──▶  sqlviz-api, sqlviz-storage
       (starts everything: opens .sqlviz, starts Quack,
        starts FastAPI, opens browser)
```

This graph defines the **only valid build order**:
`core → inference + storage (parallel) → api → web → cli`.

---

## 5. Build Phases — V0.1

Each phase produces something runnable and testable.
No phase starts until the previous phase's exit criteria pass.

### Phase 0 — Workspace Setup

```
Goal:    A monorepo that installs and runs `pytest` with 0 tests,
         0 errors.

Tasks:
1. Create the directory structure (Section 3)
2. Root pyproject.toml configured as a uv workspace
3. Each package gets its own pyproject.toml
4. CI skeleton (GitHub Actions) that runs `uv run pytest`
   on every push — even with zero tests, prove the pipe works

Exit criteria:
✓ `uv sync` succeeds from repo root
✓ `uv run pytest` runs (even with 0 tests collected)
✓ CI is green on an empty test suite
```

### Phase 1 — sqlviz-core

```
Goal:    The kernel contracts exist and are importable.

Tasks:
1. DataSourceContract, VizEngineContract (DOC 3, Section 2)
2. DataSourceRegistry, VizEngineRegistry (DOC 3, Section 2)
3. Shared models used by storage + inference + api
   (ColumnSchema appears in both DOC 5 context.py and
   sqlviz-storage — it must be defined ONCE in sqlviz-core
   and imported by both, not duplicated)

Exit criteria:
✓ `from sqlviz_core.contracts import DataSourceContract` works
✓ Registry can register and retrieve a dummy source
✓ Unit tests for registry pass
```

**Correction needed when implementing DOC 5 against this plan:**
DOC 5's `context.py` (Section 3.2) defines `ColumnSchema` locally
inside `sqlviz-inference`. Per the dependency graph above, this
must move to `sqlviz-core/models` so `sqlviz-storage` can use the
same definition when reading DuckDB `DESCRIBE` results. This is
a placement fix, not a design fix — the dataclass itself
(DOC 5, Section 3.2) is correct and unchanged.

### Phase 2 — sqlviz-inference (the brain)

```
Goal:    infer(sql) -> InferenceResult works end-to-end,
         benchmark passes the release gate.

This phase IS DOC 5, Sections 4-16, implemented in order:

2a. Parser module           (DOC 5, Section 4)
2b. Feature Engine          (DOC 5, Section 5)
2c. Semantic Engine         (DOC 5, Section 6)
2d. Intent Engine           (DOC 5, Section 7)
2e. Chart Engine            (DOC 5, Section 8)
2f. Layout Engine           (DOC 5, Section 9)
2g. Filter Engine           (DOC 5, Section 10)
2h. Title Engine            (DOC 5, Section 11)
2i. Runtime Pipeline        (DOC 5, Section 12)
2j. All 7 YAML rule files   (DOC 5, Section 13)
2k. Dashboard Engine        (DOC 5, Section 15)
2l. v0.1.1 patch (trend_direction,
    field-owned mutation wording)  (DOC 5, Section 16)

Exit criteria (THE release gate for this phase):
✓ All unit tests pass (one per module, per DOC 5 sections 4.5,
  5.9, 6.6, 7.4, 8.6, 9.4, 10.5, 11.4, 12.7, 15.6)
✓ Benchmark accuracy gate passes (DOC 5, Section 14.5):
    intent_accuracy   >= 0.85
    chart_accuracy    >= 0.85
    quality_pass_rate >= 0.80
✓ validate_rules_on_startup() (DOC 5, Section 13.8) returns
  zero errors
✓ The canonical first milestone test passes:

    result = infer(
        sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
        data=[...], schema=[...]
    )
    assert result.intent_winner == "trend"
    assert result.chart_winner  == "line"
    assert result.chart_quality == "high"
```

**This phase is the longest and must not be rushed.** Per the
"what is the hardest part of SQLviz" discussion earlier in this
project: the parser and inference engine are where ~60% of total
V0.1 development time is expected to go. Phase 2 alone may take
as long as all other phases combined.

### Phase 3 — sqlviz-storage

```
Goal:    A .sqlviz file can be created, opened, and migrated.
         brain.duckdb path resolves correctly across OS.

Tasks:
1. project_db.py — create/open .sqlviz, run schema (DOC 2,
   Section 4: _sqlviz_meta, _sqlviz_auth, connections,
   folders, dashboards, shares, filter_memory, settings)
2. is_sqlviz_project() validation (DOC 2, Section 4)
3. Migration runner (DOC 2, Section 4 lifecycle)
4. brain_db.py — resolve ~/.sqlviz/brain.duckdb path correctly
   on Linux/Mac (~/.sqlviz/) and Windows (C:\Users\{name}\.sqlviz\)
   per DOC 3, Section 2
5. DuckDB Secrets wrapper for external connections (DOC 3,
   Section 2 — credential management)

Exit criteria:
✓ Creating a new project produces a valid .sqlviz with correct
  signature
✓ Opening an invalid file (wrong signature) raises the correct
  error per DOC 2, Section 2 CLI decision tree
✓ brain.duckdb is created once at ~/.sqlviz/ and reused across
  multiple project opens (proves the "global brain" design,
  DOC 3 Section 2, actually persists)
```

### Phase 4 — sqlviz-api

```
Goal:    A running FastAPI server that connects storage and
         inference, with QuackConnectionRouter in place and the
         routing interface ready for Phase 6 wire-protocol
         isolation.

Tasks:
1. routers/dashboards.py, panels.py, connections.py
   — CRUD endpoints backed by sqlviz-storage
2. routers/auth.py — admin login (DOC 2, Section 5;
   full design in DOC 7)
3. routers/shares.py — share link generation/verification
   (DOC 2, Section 6; full design in DOC 7)
4. quack_server.py — implements QuackConnectionRouter
   (DOC 7, Section 5): routing logic that determines which
   DuckDB connection to use per request (is_admin(),
   connection_for_request()). The real Quack wire-protocol
   PostgreSQL server — providing true read-only isolation for
   viewer connections — is built in Phase 6, alongside the
   CLI that orchestrates the full startup sequence.
   (DOC 2, Section 7; DOC 3, Section 3; DOC 7, Section 5)
5. Wire panel execution: SQL in → DataSourceRegistry.get("duckdb")
   .execute() → sqlviz_inference.infer() → response out
6. Serve sqlviz-web SPA build in main.py:
     app.frontend("/", directory="dist")
   API routes defined before this call always take priority.
   Automatic index.html fallback handles SvelteKit client-side
   routing (e.g. /dashboard/123 → index.html → Svelte router).
   See DOC 3 Section 8 for rationale vs. old StaticFiles pattern.

Exit criteria:
✓ POST a dashboard's SQL, get back panels with chart_type,
  layout, title — i.e. Phase 2's infer() is now reachable
  over HTTP
✓ Admin login works; wrong password is rejected
✓ A generated share link, opened without credentials, returns
  read-only dashboard data
✓ QuackConnectionRouter is wired into app.state with the
  correct interface: is_admin() correctly identifies admin
  vs. viewer requests; connection_for_request() returns the
  appropriate connection. The routing logic is in place;
  wire-protocol read-only isolation for viewers is Phase 6
  (DOC 3 Section 3, DOC 7 Section 5)
```

**Note:** Phase 4 implements auth/shares per DOC 7 (Security &
Roles) directly — Section 3 (admin auth, bcrypt, session
tokens) and Section 4 (the three sharing modes, token
generation/verification) are now both finalized. Implement
against DOC 7 as written; no interim design is needed.

### Phase 5 — sqlviz-web

```
Goal:    A user can open the browser, write SQL, and see a
         dashboard appear — the core promise, end to end.

Note: The compiled SvelteKit output (`dist/`) is served by
`app.frontend("/", directory="dist")` wired in Phase 4 task 6
(DOC 3 Section 8). Phase 5 builds the SPA; Phase 4 wires it in.

Tasks: (full detail per DOC 6 — UI Design System)
1. SQL editor (Monaco, per DOC 3 Section 3) wired to
   POST /panels endpoint
2. Dashboard renderer consuming InferenceResult.col_span /
   row_span / chart_winner to build the 12-column CSS Grid
   (DOC 5 Section 9, DOC 5 Section 15 Dashboard Engine output)
3. ECharts renderer for the 8 V0.1 chart types
4. Filter controls — render the 8 control types from
   FilterEngine output (DOC 5, Section 10.2)
5. Admin login screen, viewer share-link screen
   (per DOC 7, now finalized)

Exit criteria:
✓ Paste a SQL query with 3 statements separated by `;`,
  see 3 panels appear, arranged via Dashboard Engine output
  (this is the FIRST end-to-end proof of the whole philosophy:
  "the user writes SQL, SQLviz infers everything else")
✓ Changing a $variable filter re-queries and updates the panel
✓ Dark/light theme toggle works
```

### Phase 6 — sqlviz-cli

```
Goal:    `sqlviz` and `sqlviz my_project` work exactly as
         specified in DOC 2.

Tasks:
1. Implement the CLI decision tree (DOC 2, Section 2)
2. Wire startup sequence: open .sqlviz -> start Quack
   PostgreSQL wire-protocol server -> start FastAPI ->
   open browser (DOC 2, Section 3)
3. Start the real Quack wire-protocol server as part of
   the startup sequence (completes the Phase 4.5 deferred
   isolation mechanism):
   - One admin connection: read/write (same conn as Phase 4)
   - Read-only viewer connections: one per active viewer,
     opened via duckdb.connect(path, read_only=True)
   - QuackConnectionRouter.connection_for_request() returns
     the correct type: admin conn for authenticated admin
     requests, read-only conn for viewer share-link requests
   (DOC 2, Section 7; DOC 3, Section 3; DOC 7, Section 5)
4. Demo mode singleton connection (DOC 2, Section 5 —
   this was the actual bug fixed in the v0.1 prototype;
   do not regress it)

Exit criteria:
✓ `sqlviz` with no args starts demo mode, no files created
✓ `sqlviz my_project` creates my_project.sqlviz, prompts for
  password, opens browser
✓ `sqlviz my_project` a second time opens the existing project
✓ `sqlviz some_invalid.sqlviz` shows the error and exits cleanly
  (DOC 2, Section 2 — no menu, no auto-demo, exits as decided)
```

### Phase 7 — End-to-End Validation

```
Goal:    The example dashboard (4 panels, inline data) works
         in both demo and persistent mode — this is V0.1 "done."

Tasks:
1. Ship the example dashboard SQL (KPI, Line, Bar, Bar Horizontal
   — same 4-panel example built in the v0.1 prototype, this time
   generated automatically by the Dashboard Engine instead of
   manually laid out)
2. Full manual QA pass through every CLI + UI flow above
3. Actualizar FastAPI a 0.139.0 y aplicar router.frontend() con
   dependencies=[Depends(require_admin)] para proteger el frontend
   del dashboard con la misma cookie auth que ya existe en los
   endpoints de la API (DOC 3, Section 8 — FastAPI 0.139.0 note)
4. Tag v0.1.0 release

Exit criteria:
✓ Fresh `pip install` (or `uv tool install`) + `sqlviz demo_test`
  shows a working dashboard with zero manual configuration
✓ Demo mode and persistent mode produce identical UI behavior
  (this was explicitly broken once before — DOC 2 Section 5
  documents the singleton-connection fix; Phase 7 must include
  a regression test for it)
```

---

## 6. What Is Deferred — And When It Returns

This section exists for the same reason DOC 5's Extensibility
Roadmap exists: so nothing discussed and agreed upon during
planning is silently lost.

### Packages deferred beyond V0.1

```
Package            Why deferred                          Returns
─────────────────────────────────────────────────────────────────
sqlviz-sources     V0.1 ships DuckDB only (DOC 3, Section  V0.2
                   5). ClickHouse needs its own client
                   library and dialect handling — becomes
                   its own package when it exists, rather
                   than bloating sqlviz-core's registry
                   with a second contract implementation
                   before there is a second real consumer.

sqlviz-viz         V0.1 ships ECharts only. Plotly          V0.2
                   (DOC 3, Section 4) becomes its own
                   package when statistical chart types
                   are actually requested by the Chart
                   Engine (currently only 8 V0 chart
                   types, all ECharts-coverable per
                   DOC 5 Section 13.3).

sqlviz-benchmarks  V0.1 keeps benchmark_cases.yaml inside   V0.2
                   sqlviz-inference/tests/benchmark/
                   (DOC 5, Section 14.2). It becomes a
                   separate package only once the Gold
                   Dataset grows past ~300 cases and needs
                   its own versioning/release cadence
                   independent of the inference code.

sqlviz-security    V0.1 keeps auth/shares as routers        V0.2/
                   inside sqlviz-api (Section 5 above).      DOC 7
                   Becomes its own package only if/when
                   roles (not just admin/viewer) are
                   introduced — see DOC 7 when written.

sqlviz-plugins     No plugin system in V0.1. The Registry   V0.3
                   Pattern (DOC 3, Section 2) is the
                   prerequisite and already exists —
                   sqlviz-plugins would just be the
                   packaging convention for third-party
                   DataSourceContract/VizEngineContract
                   implementations once external
                   contributors exist to write them.

sqlviz-sdk         Needs sqlviz-plugins first. No reason     V0.3+
                   to design an SDK before there is a
                   plugin system to build SDK tooling
                   around.

sqlviz-cache       L1/L2/L3 cache (mentioned in the          V0.2
                   ChatGPT handbook review, "Performance
                   & Scaling") is not needed until real
                   usage shows the Fast Path (DOC 5,
                   Section 12.6, target <1s) is actually
                   too slow. Premature caching is
                   premature optimization — measure first.

sqlviz-events      DOC 5's pipeline (Section 12) is a        V0.3+
                   simple synchronous function-call chain,
                   not an event bus. An in-memory event
                   bus (per the ChatGPT handbook's "Event
                   System" chapter) only becomes necessary
                   once the Slow Path (Insight Engine,
                   Recommendation Engine — DOC 5 Section
                   12.6) needs to run multiple async
                   consumers off one trigger. Not needed
                   for V0.1's purely synchronous Fast Path.
```

### Features deferred beyond V0.1 (cross-referenced from prior docs)

> **Terminology disambiguation (third review round):** "auto-layout"
> was being used for two different things in this document, which
> read as a contradiction — the Definition of Done (Section 7)
> requires panels to be "auto-placed," while this table said
> "auto-layout" was deferred to V0.2. These are not the same
> feature:
>
> - **Auto-PLACEMENT (V0.1, already required, NOT deferred):** the
>   Dashboard Engine (DOC 5, Section 15) groups KPIs, orders panels
>   narratively, and packs them into rows automatically. This
>   exists in V0.1 and is exactly what Section 7's checklist tests.
> - **Auto-layout UX (V0.2, genuinely deferred):** DOC 1's vision
>   of removing the row/panel/drag affordances *entirely* from the
>   primary interaction model, replacing them with a single
>   dashboard-wide SQL editor where panels simply appear as
>   statements are added. DOC 6 (Section 3) already implements
>   most of this — manual row/drag controls are NOT the primary
>   flow even in V0.1 — but the very last mile (a true single
>   continuous SQL-to-dashboard editing experience with zero
>   "Edit SQL" modal indirection) is the part still deferred.
>
> The table row below now names the deferred part precisely.

```
Feature                          Source doc           Returns
─────────────────────────────────────────────────────────
Auto-layout UX, final mile        DOC 1 vision,         V0.2
 (single continuous SQL editor    DOC 6 Section 3
 with zero "Edit SQL" modal
 indirection — NOT the same as
 auto-placement, which is V0.1)
Filters without $variable         DOC 5 Section 16.3     V0.3
 (auto-inferred from columns)
Insight Engine                    DOC 5 Section 16.4     V0.3
Narrative Engine                  DOC 5 Section 16.4     V0.3
Semantic Engine V1 (embeddings)   DOC 5 Section 16.4     V0.3
Domain Dictionaries                DOC 5 Section 16.3     V0.3
Feature Registry (80-120 dims)     DOC 5 Section 16.3     V0.2
brain.duckdb full schema +         DOC 5 Section 16.4     V0.3
 learning (Bayesian/Thompson)
Cross-filtering between panels      DOC 5 Section 15.7      V0.2
Dashboard Composer                  DOC 5 Section 15.7      V0.3
 (missing-perspective detection)
Multi-source dashboards              earlier conversation    V0.3+
 (one dashboard, multiple
 connections — V0.1 is
 "one dashboard = one connection")
Cloud mode                           DOC 2 Section 1          V0.4
ClickHouse engine                    DOC 3 Section 5          V0.2
Plotly viz engine                     DOC 3 Section 7          V0.2
```

---

## 7. Definition of Done — V0.1

SQLviz V0.1 is complete when, and only when, all of the
following are simultaneously true:

```
[ ] uv tool install sqlviz (or local equivalent) works
[ ] `sqlviz` with no args opens a working demo dashboard
[ ] `sqlviz my_project` creates a real .sqlviz file
[ ] The example dashboard (4 panels) renders correctly in
    both modes, with charts auto-inferred (not hardcoded)
[ ] User can write a new SQL query and see a new panel appear,
    auto-placed by the Dashboard Engine
[ ] $variable filters work and update panels reactively
[ ] Admin can log in; viewer can open a share link without
    logging in (private mode at minimum — password/public
    modes depend on DOC 7 finalization)
[ ] DOC 5 benchmark gate passes (>= 85% intent, >= 85% chart,
    >= 80% quality pass rate) on the 30-case Gold Dataset
[ ] brain.duckdb is created at ~/.sqlviz/ and persists across
    multiple project sessions (proves the architecture, even
    though learning itself is V0.3)
[ ] Section 6 of this document accurately lists everything
    NOT in V0.1, so no scope-creep decisions get made silently
    during implementation
```

---

*SQLviz Construction Plan — v0.1.0 Draft*
*"From documents to a working release, in seven phases."*
