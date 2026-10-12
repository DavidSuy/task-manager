# Task Manager

Flask API for tasks and users. In-memory data, no database.

## Commands
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Always `source .venv/bin/activate` before running anything
- Test: `pytest -q` — run before finishing every task (use `-q`, not `-v`, in plans and verification steps)
- Lint: `ruff check .` — run before finishing every task; the starting code has 6 errors,
  do not add new ones and do not `--fix` files outside the task

## Architecture
- Request flow: `app.py` → `routes/api.py` (Blueprint at `/api`) → `services/*.py`
- Routes only parse the request and call a service — no business logic in `routes/api.py`
- Data lives in module-level dicts: `TASKS` in `services/tasks.py`, `USERS` in `services/users.py`
- `AppError` is converted to a JSON response by `handle_app_error` in `routes/api.py`
- Canonical example: `services/users.py` — copy its structure for any service function
- Layer boundary: `routes/api.py` only parses input (`request.get_json()`, `data.get(...)`, `int()` on query args) and calls a `services/` function — all validation, defaults and error wording live in `services/`; canonical pair: `update_notification_pref` in `services/users.py` and `update_notification_pref_route` in `routes/api.py`

## Conventions
- Every function has type hints on all parameters and the return type
- Every function has a Google-style docstring with `Args:`, `Returns:`, `Raises:` (see `get_user`)
- Errors: raise `NotFoundError(resource)` or `ValidationError(field, reason)` from
  `utils/errors.py` — never let a raw `KeyError` escape, never raise plain `Exception`
- Missing records: check `if id not in DICT: raise NotFoundError("Task")` like `get_user`
- Input validation: follow `create_user` — validate before writing to the dict
- Any service function that takes a `user_id` must call `get_user(user_id)` from
  `services/users.py` first, so an unknown user raises `NotFoundError("User")` —
  never store or look up tasks for a user that doesn't exist in `USERS`
- New tests go in `tests/test_tasks.py` (task services), `tests/test_users.py` (user services)
  or `tests/test_api.py` (routes, via its `client` fixture); error tests assert the specific subclass,
  e.g. `pytest.raises(NotFoundError)` — never `pytest.raises(Exception)` (ruff B017)
- Tests must not rely on the shared `TASKS` contents staying fixed — `process_order` and
  `create_task` mutate it; create the data a test needs inside the test

## Do not touch
- `utils/errors.py` — the error classes and status codes (404, 422) are fixed
- Existing function signatures in `services/` — routes depend on them
- Existing tests in `tests/test_tasks.py` — never edit a test to make it pass
- `DRILL_PROMPTS.md` — course material, not project code
- `USERS` seed records and `NOTIFICATION_PREFS` in `services/users.py` — do not change them when adding
  or editing functions in that file (SA-1/SA-2 shared this file)
- `services/*.py` when changing `routes/api.py` — a route change must not edit or add service code (SA-3)
- `services/`, `routes/` and `utils/` when writing tests — if a test exposes a source bug, stop and
  report it; never edit source to make a test pass (SA-4)
- Existing import lines in `tests/test_tasks.py`, `tests/test_api.py` and `routes/api.py` — append new
  names to the existing line; do not reformat or restructure it
