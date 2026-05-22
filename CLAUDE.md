# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`flagme` is a feature flag service with a FastAPI HTTP layer, SQLite persistence, and a React + Vite + Tailwind admin UI in `frontend/`. Backend is Python 3.12, src-layout, hatchling build backend.

## Repo layout

- `src/flagme/models.py` — Pydantic models: `FlagInput`, `Flag` (`FlagInput` + uuid `id`), `EvaluationContext`, `Evaluation`. Cross-field validation lives here (matching `value_type` to `boolean_value`/`string_value`; rejecting `ends_at <= starts_at`).
- `src/flagme/storage.py` — `FlagStorage` wraps a `sqlite3.Connection` with `list/get/create/update/delete` plus `find_match()`, the scope+time-window resolver. Schema is created on construction with `CREATE TABLE IF NOT EXISTS`; no migration tool yet. DB path defaults to `./flagme.db`, overridable via the `FLAGME_DB` env var.
- `src/flagme/api.py` — FastAPI app. Storage is injected via the `get_storage` dependency so tests can swap in an in-memory store. Includes a permissive CORS allow-list for the Vite dev server (`http://localhost:5173`, `http://127.0.0.1:5173`).
- `src/flagme/__main__.py` — launches uvicorn (used by the `flagme` console script).
- `tests/conftest.py` — provides a per-test `:memory:` `FlagStorage` and a `TestClient` with the storage dependency overridden.
- `frontend/` — Vite + React + TypeScript + Tailwind v4 admin UI. See "Frontend" below.

## Data model

A flag is `(id, key, description, environment, user_id, starts_at, ends_at, value_type, boolean_value | string_value)`. Multiple flag rows can share a `key` and differ in scope.

- **Scope**: `environment` and `user_id` are independently nullable; `NULL` means *applies to all*.
- **Time window**: `starts_at`/`ends_at` are inclusive lower / exclusive upper bounds, both nullable. All datetimes are stored as ISO-8601 strings; naive datetimes are treated as UTC.
- **Value**: `value_type` is `"boolean"` or `"string"`. Exactly one of `boolean_value` / `string_value` must be populated — enforced by both the Pydantic validator and a SQLite `CHECK`.

### Evaluation algorithm

`POST /evaluate/{key}` body: optional `EvaluationContext` (`environment`, `user_id`, plus arbitrary extra fields). The resolver in `storage.find_match()`:

1. Loads all rows with that `key`.
2. Filters to those whose scope is compatible (`flag.environment` is NULL or matches the context; same for `user_id`) and whose time window contains `datetime.now(utc)`.
3. Picks the most specific candidate. Specificity score: `(env != NULL) * 2 + (user_id != NULL) * 1`. Exact env + exact user beats env-only beats user-only beats global. Ties shouldn't occur in well-formed data; if they do, `max()` picks one stably.

No matching flag → 404. Returned shape: `{key, value_type, value, matched_flag_id}`.

## Commands

Development uses a project-local `.venv/`. Activate with `source .venv/bin/activate`, or invoke binaries directly via `.venv/bin/<tool>`.

```
.venv/bin/pip install -e ".[dev]"              # install backend
.venv/bin/pytest                                # backend tests (uses :memory: SQLite)
.venv/bin/pytest tests/test_api.py::test_evaluation_prefers_exact_environment_then_global

.venv/bin/ruff check . && .venv/bin/ruff format .
.venv/bin/mypy src

FLAGME_DB=./flagme.db .venv/bin/flagme         # run server (defaults to ./flagme.db)
.venv/bin/uvicorn flagme.api:app --reload      # dev server with auto-reload
```

### Frontend

```
cd frontend
npm install
npm run dev        # vite dev server on http://localhost:5173, proxies /api -> :8000
npm run build      # tsc -b && vite build
```

The frontend reads `import.meta.env.VITE_API_URL`; if unset it talks to `/api`, which the Vite dev proxy forwards to `http://127.0.0.1:8000`. For production builds, set `VITE_API_URL` to the deployed backend origin.

**Pinned to Vite 7 + @vitejs/plugin-react 5** because Vite 8 uses rolldown and its native binding detection fails on Node 20.16 (gives `Cannot find module './rolldown-binding.darwin-universal.node'`). Upgrade Node to 20.19+ or 22.12+ before bumping Vite.

## API surface

| Method | Path                | Tag        | Purpose                              |
| ------ | ------------------- | ---------- | ------------------------------------ |
| GET    | `/`                 | (hidden)   | 307 redirect to `/docs`              |
| GET    | `/healthz`          | System     | Liveness probe                       |
| GET    | `/flags`            | Flags      | List, optional `?environment=&user_id=` filters (NULL-scoped flags always included) |
| POST   | `/flags`            | Flags      | Create; server assigns `id`          |
| GET    | `/flags/{flag_id}`  | Flags      | Read by id                           |
| PUT    | `/flags/{flag_id}`  | Flags      | Replace by id                        |
| DELETE | `/flags/{flag_id}`  | Flags      | Delete by id                         |
| POST   | `/evaluate/{key}`   | Evaluation | Resolve typed value for a context    |

Interactive docs at `/docs` (Swagger UI) and `/redoc`; OpenAPI 3 spec at `/openapi.json`. App `version` is sourced from `flagme.__version__`.

## Status

The backend is functional with persisted scope-aware evaluation; the frontend covers CRUD with a Tailwind-styled table, filter, and modal form. Out of scope so far: authentication, rate limiting, audit logging, percentage rollouts / targeting rules beyond exact scope match, multi-variant flags (only boolean and string today), and DB migration tooling.
