# Command Log

| Command invoked | $ARGUMENTS | Stayed in scope? | What worked / what I changed |
|---|---|---|---|
| `/audit-errors` (run 1) | `services/tasks.py` | Yes | Fixed only `process_order` (raw `KeyError` → `NotFoundError("Task")` + docstring) and skipped the 6 compliant functions; pytest -q 55 passed, ruff 6 errors, but with just one function to fix the per-function pacing rule was never actually exercised. |
| `/audit-errors` (run 2) | `services/tasks.py` | Yes | Idempotency worked: all 7 functions reported "already compliant" and `git diff` was empty after the run. |
| `/scaffold-endpoint` | `tags POST` | Yes | Created `schemas/tags.py`, `services/tags.py` and a route in `routes/api.py` that only parses `name` and calls `create_tag` (no logic in the route), plus a 201 happy-path test (pytest 56 passed, ruff 6); the brief's `routes/tasks.py` doesn't exist here, so Context names it and points to `routes/api.py`. Gap: `create_tag` only checks for empty names, so `{"name": 5}` raises a raw `AttributeError` (500); next change is a Constraint to validate each input field's type. |
| `/add-tests` | `create_tag` | Yes | Added 5 passing tests to `tests/test_tags.py`, and when a non-string `name` (`123`) raised a raw `AttributeError` instead of `ValidationError`, stopped and reported the bug without editing `services/tags.py` or keeping the failing test, as the Constraints require. |
| `/audit-errors` | `services/tags.py` | Yes | Fixed the bug `/add-tests` reported by adding an `isinstance(name, str)` check to `create_tag` (pytest passed, ruff 6), but reused the "cannot be empty" message, so I changed the reason to "must be a non-empty string"; a re-run of `/add-tests create_tag` then kept a passing non-string test. |
