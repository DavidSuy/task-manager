# Iteration Log

## Session 1 — 2026-10-05

### Prompt used
Add error handling to the get_task function in @services/tasks.py. Do not change the function signature. Run pytest -v when done.

### What Claude did
Read services/tasks.py and services/users.py, then added `if task_id not in TASKS: raise NotFoundError("Task")` and a Google-style docstring (Args/Returns/Raises) to get_task, plus `from utils.errors import NotFoundError`. Signature unchanged, no other functions or files touched. Ran pytest -v: 4 passed. Did not run ruff check. Corrections needed: 0.

### Observation
The Conventions rules ("raise NotFoundError ... never let a raw KeyError escape", "check `if id not in DICT` like get_user") and the canonical-example rule pointing at services/users.py were followed exactly. Claude even said it was matching get_user's pattern. Two gaps: (1) Claude skipped `ruff check .` because CLAUDE.md lists the lint command without saying when to run it, unlike the test command; (2) "4 passed" is not evidence of correctness, because test_get_task_invalid uses `pytest.raises(Exception)`, which also passed before the change when get_task raised a raw KeyError (ruff flags this as B017).

### CLAUDE.md update
Changed: `- Lint: ruff check .`
To: `- Lint: ruff check . — run before finishing every task; the starting code has 6 errors, do not add new ones and do not --fix files outside the task`
I added this because Claude ran pytest -v but never ran ruff check in Session 1, since only the test command said when to run it.
