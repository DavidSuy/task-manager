---
description: Scaffold a new REST endpoint (route, service, schema) for a resource
argument-hint: <resource> <HTTP method>, e.g. tags POST
---

## Goal

Add a `$2` endpoint for the `$1` resource, using `$ARGUMENTS` to supply both values. This
requires creating or updating three files:

- The route in `routes/api.py`.
- The service in `services/$1.py`.
- The schema in `schemas/$1.py` — a `TypedDict` describing the `$1` record.

## Context

- The canonical pattern is `routes/tasks.py`. This repo has no `routes/tasks.py`; all task
  routes live in `routes/api.py`, so the task routes there (e.g. `create_task_route`) are that
  pattern.
- The canonical route/service pair is `update_notification_pref_route` in `routes/api.py` and
  `update_notification_pref` in `services/users.py`.
- Data lives in a module-level dict, like `TASKS` in `services/tasks.py`.
- Follow the CLAUDE.md conventions: type hints on all parameters and the return type,
  Google-style docstrings with `Args:`, `Returns:`, `Raises:`, and `AppError` subclasses from
  `utils/errors.py` for all errors.

## Constraints

- No business logic in the route handler. The route only parses the request
  (`request.get_json()`, `data.get(...)`) and calls one service function; all validation,
  defaults and error messages go in `services/$1.py`.
- Do not edit `utils/errors.py`, existing service functions, or existing tests.
- Add a new import line in `routes/api.py` for the new service; do not reformat existing
  import lines.

## Verification

- Add a happy-path test in `tests/test_api.py` using its `client` fixture, asserting the
  correct status code (201 for POST, 200 for GET/PATCH).
- Run `pytest -q` — all tests must pass.
- Run `ruff check .` — must still report exactly 6 errors.
