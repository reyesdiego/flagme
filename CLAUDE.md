# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`flagme` is a feature flag service. Python 3.12, src-layout, hatchling build backend. HTTP layer is FastAPI; the runtime entry point launches uvicorn.

## Commands

Development happens inside `.venv/` (created with `python3 -m venv .venv`). Activate it with `source .venv/bin/activate`, or invoke binaries directly via `.venv/bin/<tool>`.

Install (editable, with dev tools):
```
.venv/bin/pip install -e ".[dev]"
```

Test:
```
.venv/bin/pytest                          # full suite
.venv/bin/pytest tests/test_smoke.py::test_version_is_set   # single test
```

Lint / format / typecheck:
```
.venv/bin/ruff check .
.venv/bin/ruff format .
.venv/bin/mypy src
```

Run the service:
```
.venv/bin/flagme                              # installed console script -> uvicorn on 127.0.0.1:8000
.venv/bin/python -m flagme                    # same
.venv/bin/uvicorn flagme.api:app --reload     # dev mode with auto-reload
```

## Layout

- `src/flagme/api.py` — FastAPI app, Pydantic `Flag` model, and the in-memory `_store` dict that backs CRUD routes. Everything lives in one module on purpose; split when complexity earns it.
- `src/flagme/__main__.py` — `main()` calls `uvicorn.run("flagme.api:app", ...)`; this is what the `flagme` console script invokes.
- `tests/conftest.py` — autouse fixture that clears `_store` between tests so the in-memory state doesn't leak.
- `tests/` — pytest tests, configured via `[tool.pytest.ini_options]` in `pyproject.toml`.
- `.idea/` — stale IntelliJ config with Go support enabled; ignore, the project is Python.

## Status

The HTTP layer is a sketch backed by a process-local dict — no persistence, no auth, no flag-evaluation engine yet. Routes: `GET /healthz`, `GET /flags`, `GET/PUT/DELETE /flags/{key}`. PUT requires the body `key` to match the path key.