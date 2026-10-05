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

## Session 2 — 2026-10-05

### Prompt used
Refactor create_task in @services/tasks.py to match the style of get_user in @services/users.py exactly. Run pytest -v when done.

### What Claude did
Added a Google-style docstring (Args/Returns/Raises) to create_task, added `if not title or not title.strip(): raise ValidationError("title", "cannot be empty")` copied from create_user, imported ValidationError, and collapsed the TASKS write onto one line. Signature unchanged, no other files touched. Ran pytest -v (4 passed) and this time also ran `ruff check .`, reporting the same 6 pre-existing errors and none new. Corrections needed: 0.
What was wrong: create_task still accepts any user_id. `create_task("x", 999)` stores a task for a user that doesn't exist, and POST /api/tasks with an unknown user_id returns 201.

### Observation
Update 1 worked: Claude ran ruff unprompted and explicitly compared against the 6-error baseline from CLAUDE.md. The "follow create_user — validate before writing" rule was followed for title. Honest failure: CLAUDE.md did not prevent the unvalidated user_id. The validation rule pointed at create_user, which only validates its own fields and never references another service, so the pattern Claude was told to copy contains no example of checking a foreign key. Nothing in CLAUDE.md said tasks must belong to a user in USERS. pytest could not catch this either, since no test calls create_task.

### CLAUDE.md update
Added to Conventions:
`- Any service function that takes a user_id must call get_user(user_id) from services/users.py first, so an unknown user raises NotFoundError("User") — never store or look up tasks for a user that doesn't exist in USERS`
I added this because Claude validated title but let create_task store a task for nonexistent user 999 in Session 2, since the create_user pattern it was told to follow has no cross-service check.
