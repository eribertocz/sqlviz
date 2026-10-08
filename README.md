# SQLviz

SQL-first dashboard authoring with automatic chart recommendations and visual
editing. Write queries, inspect the inference, adjust panels, and explore data
through interactive dashboards.

**Development status:** the latest repository release tag is `v0.2.11`; the
development branch contains later, unreleased changes. The project is under active development.

> **Security work in progress:** author routes now require authentication and
> viewer data requests validate the share's scope, password session and revocation.
> HTTP analytical queries now run in a separate catalog with execution budgets;
> external sources and local views require future dataset adapters. Use a controlled local
> environment and test data; do not expose this build to an untrusted network.
> The CLI now defaults to `127.0.0.1` and leaves Quack disabled.
> See the [implemented authorization policy](docs/architecture/sqlviz-authorization.md).
> See [analytical isolation, limits and compatibility](docs/architecture/sqlviz-analytical-execution.md).
> See [parameter contracts and quality checks](docs/architecture/sqlviz-parameters-and-quality.md).
> See the [audit](docs/architecture/sqlviz-audit-2026-10-05.md) and
> [remediation plan](docs/architecture/sqlviz-product-roadmap.md).

## Product direction

The next stage combines SQL authoring with visual dashboard design over reusable
datasets. A visual query builder, governed metrics, and team permissions are
planned capabilities, not features already delivered.

The accepted Studio direction provides three authoring levels on the same visual:
automatic inference, a Visual Builder, and expert native ECharts JSON options.
Dataset definitions, reusable visuals and dashboard panel instances will be
separate; the minimum dataset contract precedes the canvas. The expert editor
and reusable dataset persistence are planned, not implemented features.
See the [accepted authoring decision](docs/architecture/sqlviz-visual-authoring-decision.md).

Start with the [documentation index](docs/README.md),
[target architecture](docs/architecture/sqlviz-product-architecture.md), and
[current delivery plan](docs/architecture/sqlviz-product-roadmap.md).

Workspace navigation can be hidden completely, uses a modal on narrow screens,
and provides dashboard search. The editor exposes command search and focus mode.
Preview and workspace viewers switch from the dashboard title with integrated search,
without opening the sidebar or reducing the dashboard canvas. Filters are edited
in a temporary panel and applied together; failed updates retain confirmed data
and criteria. A compact logo button at the top left opens or closes the
library; appearance and secondary actions remain under view options.
The logo reveals the open/close icon on hover or keyboard focus; touch devices
keep that action icon visible in the same button.
See [implemented behavior and validation](docs/architecture/sqlviz-navigation.md).
See [reader context, architecture and limits](docs/architecture/sqlviz-reader-context.md).
Screen-fit page layouts and broader visual customization remain planned.

Dashboard deletion now removes its panels, share links and saved filters in one
transaction, with rollback and protection against concurrent child creation.
See [the implemented integrity policy](docs/architecture/sqlviz-dashboard-integrity.md).

Folder destinations are validated transactionally, including concurrent moves
and deletion. Explicit `null` detaches a folder or dashboard to root; omission
preserves placement. See [folder integrity](docs/architecture/sqlviz-folder-integrity.md).
The current explorer still displays flat groups.

Manual panel dimensions are validated before saving: 1–12 columns and
120–900 px. The editor displays confirmed sizes and preserves the chart when a
save is rejected. See [dimension contracts and learning limits](docs/architecture/sqlviz-panel-dimensions.md).

Dashboard composition now validates typed inference results before calling the
engine, rejects invalid requests with 422, and preserves presentation labels and
manual dimensions. See [the composition contract](docs/architecture/sqlviz-composition-contract.md).
Dashboard PATCH now validates strict fields, distinguishes omission from explicit
clearing, preserves exact SQL drafts, and commits all changes atomically.
See [the dashboard PATCH contract](docs/architecture/sqlviz-dashboard-patch.md).
Basic panel PATCH now validates name/SQL/order, preserves visual settings and
commits atomically. Panel and dashboard deletion also conflict with active panel
edits. See [the basic panel contract](docs/architecture/sqlviz-panel-patch.md).
Presentation PATCH now validates titles and axis labels and commits them atomically.
The editor confirms saved text and retains failed drafts for retry, including
axis labels edited on the chart. See [presentation contracts and reset behavior](docs/architecture/sqlviz-panel-presentation.md).
The remaining override review is the next E1 increment.

## Architecture today

Six packages in one monorepo:

| Package | Current responsibility |
| --- | --- |
| `sqlviz-core` | Shared domain types, source/rendering contracts, version lookup |
| `sqlviz-inference` | SQL analysis, recommendation pipeline, visual specs and layout |
| `sqlviz-storage` | DuckDB project files, migrations, overrides, auth/share helpers and learning persistence |
| `sqlviz-api` | FastAPI application factory, HTTP routes and SPA hosting |
| `sqlviz-cli` | Project creation/opening and local server startup |
| `sqlviz-web` | SvelteKit/Svelte 5 editor and viewers, ECharts rendering |

The API executes analytical queries through an app-local QueryService in a separate
DuckDB catalog. Legacy local data tables are projected without attaching the project
or migrating its file. Source contracts do not yet imply production-ready connectors.

## Requirements and installation

- Python **3.12+** (CI matrix: 3.12/3.13; local review: 3.13).
- Node.js **24.21.0** and npm (`.node-version`, shared by CI and local review).
- [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/eribertocz/sqlviz.git
cd sqlviz
uv sync --all-packages
cd packages/sqlviz-web
npm ci
```

This is a uv workspace. Use `uv sync --all-packages`; plain `uv sync` does not
install all five Python members required by the API and tests.

## Local development

From the repository root, start the demo API on the port expected by Vite:

```sh
uv run sqlviz --host 127.0.0.1 --port 4000 --no-browser
```

Demo mode uses an in-memory project and bypasses admin login. In a second terminal:

```sh
cd packages/sqlviz-web
npm run dev
```

Open `http://localhost:5173`. The frontend proxies `/api` to port **4000**.
`sqlviz_api.main` exposes `create_app(connection)`; it has no module-level `app`
for `uvicorn sqlviz_api.main:app`.

For a persistent **test** project, replace the API command with:

```sh
uv run sqlviz local-demo.sqlviz --host 127.0.0.1 --port 4000 --no-browser
```

The CLI prompts for an admin password when creating a project. Author API routes
require that login; shared viewers use credentials limited to their share.
Source adapters and operational hardening remain pending, as described above.

Both demo and persistent projects listen on `127.0.0.1` by default. LAN binding
requires an explicit `--host 0.0.0.0`; the security limitations above still
apply. Normal startup does not install extensions or start a Quack service.

Quack is a separate, optional database service enabled with `--quack`. It requires
a preinstalled compatible extension and `SQLVIZ_QUACK_TOKEN` with at least 32
characters after trimming surrounding whitespace. Its credential grants database
access independently of SQLviz login/share permissions. See the
[startup policy, configuration and verification](docs/architecture/sqlviz-local-startup.md).

## Build and verification

From `packages/sqlviz-web`:

```sh
npm run check
npm test
npm run build
```

The static build is written to `packages/sqlviz-api/src/sqlviz_api/static/dist`.
After building, the CLI serves the UI and API together at `http://127.0.0.1:4000`.

Build the frontend first: Python HTTP tests exercise the real login SPA and
static assets. CI builds it in the frontend job and passes that artifact to both
Python jobs, so a clean checkout does not depend on a local `dist` directory.

Then, from the repository root:

```sh
uv run pytest
uv run ruff check packages/
uv run mypy packages/sqlviz-core/src packages/sqlviz-inference/src packages/sqlviz-storage/src packages/sqlviz-api/src packages/sqlviz-cli/src
```

The [audit](docs/architecture/sqlviz-audit-2026-10-05.md) records the measured
baseline, including existing type errors and frontend warnings. Passing
functional tests does not establish the security of this build.

## API and versioning

The development API is at `http://127.0.0.1:4000/api/v1`; FastAPI exposes its
OpenAPI document at `/openapi.json` and interactive documentation at `/docs`.
Main resources include dashboards, panels, folders, authentication and shares.

Python distribution versions derive from git through hatch-vcs, but an already
installed editable environment can retain stale version metadata. The audit also
records hardcoded API/project versions that still need consolidation. Version of
the product, API contracts and project schema are separate concepts.

See [CHANGELOG.md](CHANGELOG.md) for delivered changes. Historical design plans
are not a substitute for release notes or the current code.
