## Goal

Audit every function in `$ARGUMENTS` and replace any raw exception that can escape it
(`KeyError`, `IndexError`, plain `Exception`, or any other unguarded builtin exception) with
the appropriate `AppError` subclass from `utils/errors.py`.

## Context

- `utils/errors.py` defines `NotFoundError(resource)` → 404 and `ValidationError(field, reason)` → 422.
- Follow `services/users.py` as the pattern to copy:
  - `get_user` for missing records (`if id not in DICT: raise NotFoundError("Task")`-style checks).
  - `create_user` for validating input before writing to the dict.
- Follow the CLAUDE.md conventions for any code you touch:
  - Type hints on all parameters and the return type.
  - Google-style docstrings with `Args:`, `Returns:`, `Raises:`.

## Constraints

- **Idempotency**: if a function already raises the correct `AppError` subclass on every
  failure path, skip it entirely — do not rewrite, reformat, or re-document it. Report it as
  "already compliant" in the final table.
- Do not change any function signature.
- Do not touch `utils/errors.py`, `tests/test_tasks.py`, or `routes/api.py`. Edit only
  `$ARGUMENTS`.

## Verification

- After every function you change, run `pytest -q` and `ruff check .` before moving on to the
  next function.
- `ruff check .` must still report exactly 6 errors — the starting baseline. Do not add new
  errors and do not run `--fix` on files outside `$ARGUMENTS`.
- If `pytest -q` fails, stop and report the failure — never edit a test to make it pass.
- Finish with a summary table with columns: `function | fixed / already compliant | exception raised`.
