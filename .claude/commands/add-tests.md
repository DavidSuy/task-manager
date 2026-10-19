# Use this command to add tests for an existing service function; don't use it when the function itself needs changing.

## Goal

Add tests for the function named in `$ARGUMENTS` (e.g. `create_tag` or `list_tasks`): a
happy-path test, a test for each error path, and tests for edge cases such as wrong input
types.

## Context

- Follow the CLAUDE.md test conventions.
- Service tests go in the `tests/test_<module>.py` file for the function's module:
  `tests/test_tasks.py`, `tests/test_users.py`, or a new `tests/test_tags.py`.
- Route tests go in `tests/test_api.py`, using its `client` fixture.
- Error tests assert the specific `AppError` subclass from `utils/errors.py`, e.g.
  `pytest.raises(ValidationError)` — never `pytest.raises(Exception)`.
- Tests create the data they need and do not rely on the shared `TASKS` contents staying
  fixed.

## Constraints

- Tests only. Do not edit anything in `services/`, `routes/` or `utils/`.
- If a test exposes a bug in the source, stop and report the bug with the failing input; do
  not fix the source and do not keep the failing test.
- Append new names to existing import lines; do not reformat them.
- Do not edit existing tests.

## Verification

- After each test you add, run `pytest -q`.
- At the end, run `ruff check .` — must still report exactly 6 errors.
- Finish with a list: test name | what it checks | pass / exposed bug.
