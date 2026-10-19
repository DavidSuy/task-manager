# Task Manager

Flask API for tasks and users. In-memory data, no database.

## Commands
- Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Always `source .venv/bin/activate` before running anything
- Test: `pytest -q` — run before finishing every task (use `-q`, not `-v`, in plans and verification steps)
- Lint: `ruff check .` — run before finishing every task; the starting code has 6 errors,
  do not add new ones and do not `--fix` files outside the task
- `/audit-errors <service file>`: use when a service file has raw exceptions (`KeyError`,
  plain `Exception`, etc.) that should be replaced with `AppError` subclasses
- `/scaffold-endpoint <resource> <METHOD>`: use when adding a brand-new REST endpoint
  (route, service and schema) for a resource that doesn't have one yet
- `/add-tests <function>`: use to add tests for an existing service function, without
  changing the function itself

## Hooks

`guard_writes.py` is a PreToolUse hook registered in `.claude/settings.json` for the
`Write|Edit|MultiEdit|Bash` matcher; it blocks a call by printing a reason to stderr and
exiting 2, and allows it by exiting 0. It protects the paths in `BLOCKED_PATHS` (currently
`utils/errors.py` and `DRILL_PROMPTS.md`), matched case-insensitively against the normalized
path — for `Bash`, this includes indirect write targets such as `>`/`>>`/`2>` redirections,
`tee`, `cp`/`mv`/`install`, `sed -i`, and `git checkout --`/`git restore --`. It also blocks
any Bash command matching `BASH_PATTERNS` (destructive `DROP`/`TRUNCATE TABLE`, `rm` with both
`-r` and `-f`, and `git push --force`/`-f`), and blocks any `Write`/`Edit`/`MultiEdit` to
`services/tasks.py` whose new content contains a hardcoded `postgresql://` or `sqlite:///`
connection string. To add a rule, add a path to `BLOCKED_PATHS` or a `(regex, reason)` pair to
`BASH_PATTERNS`, add both a blocked case and a near-miss allowed case to
`tests/test_guard_writes.py`, run `pytest -q`, and restart `claude` so the hook reloads.

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
- Existing function signatures in `services/` — routes depend on them
- Existing tests in `tests/test_tasks.py` — never edit a test to make it pass
- `USERS` seed records and `NOTIFICATION_PREFS` in `services/users.py` — do not change them when adding
  or editing functions in that file (SA-1/SA-2 shared this file)
- `services/*.py` when changing `routes/api.py` — a route change must not edit or add service code (SA-3)
- `services/`, `routes/` and `utils/` when writing tests — if a test exposes a source bug, stop and
  report it; never edit source to make a test pass (SA-4)
- Existing import lines in `tests/test_tasks.py`, `tests/test_api.py` and `routes/api.py` — append new
  names to the existing line; do not reformat or restructure it
