# SQLviz

SQL-first dashboard compiler. Write SQL queries, get intelligent dashboards.
The inference engine picks chart types, layout, and structure automatically.

## Architecture

Six packages, one monorepo:

| Package | Role |
|---|---|
| `sqlviz-core` | Shared models (`ColumnSchema`, `InferenceResult`, etc.) |
| `sqlviz-inference` | Inference pipeline — intent → constraints → scoring → layout |
| `sqlviz-storage` | DuckDB persistence — panels, dashboards, feedback patterns |
| `sqlviz-api` | FastAPI REST API (`/api/v1/`) |
| `sqlviz-cli` | Command-line interface |
| `sqlviz-web` | SvelteKit frontend |

## Requirements

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Installation

```bash
# Clone
git clone https://github.com/eribertocz/sqlviz.git
cd sqlviz

# Install all Python packages (editable)
uv sync --all-packages

# Install frontend dependencies
cd packages/sqlviz-web
npm install
```

## Running locally

```bash
# Terminal 1 — API server
uv run uvicorn sqlviz_api.main:app --reload --port 8000

# Terminal 2 — Frontend dev server
cd packages/sqlviz-web
npm run dev
```

Open http://localhost:5173 in your browser.

## Running tests

```bash
# All Python tests
uv run pytest

# Lint
uv run ruff check packages/

# Type check
uv run mypy packages/

# Frontend build check
cd packages/sqlviz-web && npm run build
```

## API

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/meta` | Version, build info, feature flags |
| GET | `/dashboards` | List all dashboards |
| POST | `/dashboards` | Create dashboard |
| GET | `/dashboards/{id}` | Get dashboard |
| PATCH | `/dashboards/{id}` | Update dashboard |
| DELETE | `/dashboards/{id}` | Delete dashboard |
| GET | `/panels` | List panels (filter by `dashboard_id`) |
| POST | `/panels` | Create panel |
| POST | `/panels/{id}/execute` | Execute panel SQL and run inference |
| PATCH | `/panels/{id}/override` | Apply user override (chart type, layout) |

## Version

Current: **v0.2.1** — see [CHANGELOG.md](CHANGELOG.md) for history.
