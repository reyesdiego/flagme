# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`flagme` is a feature flag service. Python 3.12, src-layout, hatchling build backend.

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

Run the package entry point:
```
.venv/bin/flagme         # installed console script
.venv/bin/python -m flagme
```

## Layout

- `src/flagme/` — package source (src-layout; the package is only importable after `pip install -e .`)
- `tests/` — pytest tests, configured via `[tool.pytest.ini_options]` in `pyproject.toml`
- `.idea/` — stale IntelliJ config with Go support enabled; ignore, the project is Python

## Status

Scaffolding only — `__main__.main` is a placeholder and there is no service code, HTTP layer, or storage yet. When real subsystems land (API server, flag evaluation engine, persistence), document the high-level architecture here.