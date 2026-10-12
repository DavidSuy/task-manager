# Subagent Decomposition — Task 2 (notification preferences)

Feature: users have a `notification_pref` of `"email"`, `"sms"` or `"none"` (default `"none"`).
`PATCH /api/users/<id>/notifications` updates it (invalid value → `ValidationError`, 422);
`GET /api/users/<id>/notifications` returns it; user list and user detail responses include it.

Design decisions made before running any subagent:
- There is no user list endpoint yet (only `GET /api/users/<id>`), so SA-3 adds `GET /api/users`.
- `"none"` is stored as the string `"none"`, not Python `None`. JSON `null` is rejected as invalid.
- Notification endpoints return `{"user_id": <id>, "notification_pref": <value>}`.
- New user service tests go in a new `tests/test_users.py`; API tests go in `tests/test_api.py` (per Task 1 Session 2).

Each subagent runs in a fresh session (`claude` relaunched, not `/clear`), gets the exact prompt below, and is followed by `pytest -q` before moving on.

---

## SA-1: Data layer

| Field | Value |
|---|---|
| Input | `services/users.py`, `CLAUDE.md` |
| Task | Add a `notification_pref` field (default `"none"`) to every user record and a constant listing the allowed values. |
| Output | `services/users.py` (modified) |
| Constraint | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`. Do not add or rename functions in `services/users.py`; do not change `get_user` or `create_user` signatures. |
| Hand-off | Every record in `USERS` (seed and `create_user`) has `"notification_pref": "none"`; constant `NOTIFICATION_PREFS = ("email", "sms", "none")` exists in `services/users.py`. |

**Prompt (exact):**
> In `services/users.py` only: add `"notification_pref": "none"` to both seed records in `USERS` and to the record `create_user` builds. Add a module-level constant `NOTIFICATION_PREFS = ("email", "sms", "none")`. Do not add, rename, or change the signature of any function. Do not modify any other file. Run `pytest -q` and `ruff check .` when done.

**`pytest -q` result:** 40 passed (same as before SA-1 — no regression; SA-1 adds no tests, so this does not prove the new field works). `ruff check .`: 6 errors, all pre-existing. Diff check: only `services/users.py` changed; `NOTIFICATION_PREFS` added; both seed records and `create_user`'s record have `"notification_pref": "none"`; no functions added or renamed; signatures unchanged. Constraint followed.

**Fixes made in session:** None needed.

---

## SA-2: Service layer

| Field | Value |
|---|---|
| Input | `services/users.py` (after SA-1), `utils/errors.py`, `CLAUDE.md` |
| Task | Add service functions to list users and to get and update a user's notification preference, with validation. |
| Output | `services/users.py` (modified) |
| Constraint | Do not touch `routes/api.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`. Do not change the `USERS` seed data, `NOTIFICATION_PREFS`, or the signatures of `get_user` / `create_user`. |
| Hand-off | `list_users() -> list[dict]`; `get_notification_pref(user_id: int) -> dict` and `update_notification_pref(user_id: int, pref: str) -> dict`, both returning `{"user_id": ..., "notification_pref": ...}`. Unknown user → `NotFoundError("User")`; invalid pref (anything not in `NOTIFICATION_PREFS`, including `None`) → `ValidationError("notification_pref", ...)`. |

**Prompt (exact):**
> In `services/users.py` only, add three functions following the conventions in `CLAUDE.md` (type hints, Google-style docstrings, `get_user` as the pattern): `list_users() -> list[dict]` returning all user records; `get_notification_pref(user_id: int) -> dict` and `update_notification_pref(user_id: int, pref: str) -> dict`, both returning `{"user_id": user_id, "notification_pref": <value>}`. Both must call `get_user(user_id)` first so an unknown user raises `NotFoundError("User")`. `update_notification_pref` must raise `ValidationError("notification_pref", ...)` for any value not in `NOTIFICATION_PREFS` (including `None`) before changing anything. Do not change `USERS`, `NOTIFICATION_PREFS`, or existing function signatures. Do not modify any other file. Run `pytest -q` and `ruff check .` when done.

**`pytest -q` result:** 40 passed (no regression; SA-2 adds no tests). `ruff check .`: 6 errors, all pre-existing. Diff check: only `services/users.py` changed; `list_users`, `get_notification_pref`, `update_notification_pref` added below `create_user`; `USERS`, `NOTIFICATION_PREFS` and existing signatures untouched; `get_user` called first in both pref functions; validation happens before the write. Constraint followed. Because no tests exist yet, I ran a manual check of the functions: default `"none"`, update to `"sms"` persisted, `"pigeon"` / `None` / `"EMAIL"` → `ValidationError` 422, unknown user → `NotFoundError` 404, every `list_users()` record has `notification_pref`. Notes for SA-3/SA-4: the error message prints the Python tuple, `must be one of ('email', 'sms', 'none')`, so it shows up as-is in API responses; `list_users()` returns the live `USERS` dicts (same as `get_user`), not copies.

**Fixes made in session:** None needed.

---

## SA-3: API layer

| Field | Value |
|---|---|
| Input | `routes/api.py`, `services/users.py` (after SA-2, read only), `CLAUDE.md` |
| Task | Add `GET /api/users`, `GET /api/users/<id>/notifications` and `PATCH /api/users/<id>/notifications` routes that only parse the request and call SA-2's functions. |
| Output | `routes/api.py` (modified) |
| Constraint | Do not touch `services/users.py`, `services/tasks.py`, `utils/errors.py`, or anything in `tests/`. No validation or business logic in `routes/api.py`. |
| Hand-off | Endpoints and contracts for SA-4: `GET /api/users` → 200, list of users; `GET /api/users/<id>/notifications` → 200 or 404; `PATCH /api/users/<id>/notifications` with JSON body `{"notification_pref": ...}` → 200, 404 (unknown user) or 422 (invalid, missing, or empty body). |

**Prompt (exact):**
> In `routes/api.py` only, add three routes that call the existing functions in `services/users.py`: `GET /users` → `list_users()`; `GET /users/<int:user_id>/notifications` → `get_notification_pref(user_id)`; `PATCH /users/<int:user_id>/notifications` → `update_notification_pref(user_id, data.get("notification_pref"))`, returning 200. Use `data.get(...)`, never `data[...]`, so a missing key reaches the service and becomes a 422. Routes must only parse the request and call the service — no validation in the route. Do not modify `services/`, `utils/`, or `tests/`. Run `pytest -q` and `ruff check .` when done.

**`pytest -q` result:** 40 passed (no regression; SA-3 adds no tests). `ruff check .`: 6 errors, all pre-existing. Diff check: only `routes/api.py` changed; the three new names were appended to the existing `from services.users import get_user` line (no reformatting); three thin routes with no validation; PATCH uses `data.get("notification_pref")`. Constraint followed. Manual check with the Flask test client: `GET /api/users` and `GET /api/users/1` include `notification_pref`; GET notifications → 200 `"none"`; PATCH `"email"` → 200 and a following GET returns `"email"`; PATCH `"pigeon"` → 422; PATCH `{}` → 422; unknown user → 404 on GET and PATCH. **Gap found:** a JSON body that isn't an object (e.g. `["email"]`) → `data.get` raises `AttributeError` → 500. SA-3 followed its prompt; the prompt (and the existing `POST`/`PATCH /tasks` routes) never covered non-object bodies. Left as is — fixing it is outside SA-3's prompt and SA-4 can't edit source.

**Fixes made in session:** None.

---

## SA-4: Tests

| Field | Value |
|---|---|
| Input | `services/users.py`, `routes/api.py`, `tests/test_api.py` (for the `client` fixture and style), `CLAUDE.md` |
| Task | Write service tests and API tests covering the full notification-preference feature and the user list/detail responses. |
| Output | `tests/test_users.py` (new), `tests/test_api.py` (appended) |
| Constraint | Do not touch `services/`, `routes/`, `utils/`, or `tests/test_tasks.py`. Do not edit existing tests in `tests/test_api.py`. If a test fails because of a bug in source code, stop and report it — do not edit source files. |
| Hand-off | Final artifact: `pytest -q` green with the new tests; any source bug found is recorded below instead of being silently fixed. |

**Prompt (exact):**
> Write tests for the notification preference feature. Service tests go in a new `tests/test_users.py`: `get_notification_pref` default `"none"`; `update_notification_pref` with `"email"` and `"sms"`; invalid value `"pigeon"` → `ValidationError`; `None` → `ValidationError`; unknown user → `NotFoundError` for both functions; `list_users()` includes `notification_pref` on every user. API tests are appended to `tests/test_api.py` using its existing `client` fixture: GET notifications → 200 with default `"none"`; PATCH `"email"` → 200 and a following GET returns `"email"`; PATCH `"pigeon"` → 422; PATCH `{}` → 422; PATCH unknown user → 404; `GET /api/users` → 200 and every user has `notification_pref`; `GET /api/users/1` includes `notification_pref`. Tests must create their own users with `create_user` rather than rely on (or permanently change) seed users 1 and 2. Use specific exception classes, never `pytest.raises(Exception)`. Do not modify `services/`, `routes/`, `utils/`, `tests/test_tasks.py` or existing tests; if a test fails because of a source bug, stop and report it. Run `pytest -q` and `ruff check .` when done.

**`pytest -q` result:** 55 passed (40 before + 8 in new `tests/test_users.py` + 7 appended to `tests/test_api.py`). `ruff check .`: 6 errors, all pre-existing (the new files add none). Diff check: no files in `services/`, `routes/`, `utils/` or `tests/test_tasks.py` changed; existing tests in `test_api.py` untouched; `from services.users import create_user` added to `test_api.py`'s imports so API tests create their own users (no POST /users route exists). Every test except the unknown-user (999) cases creates its own user. Constraint followed. One deviation from the prompt: it asked for "`GET /api/users/1` includes `notification_pref`", but the same prompt also said not to rely on seed users 1 and 2. Claude resolved the contradiction quietly by testing `GET /api/users/<created id>` instead, and did not mention it.

**Fixes made in session:** None — no test failed, so the "stop and report" rule was never triggered.

---

## Divergence

**Did Claude follow the constraint field for every subagent?**
Yes. All four stayed inside their Output files. The riskiest boundary was SA-1 vs SA-2, which both edit `services/users.py` (data vs functions in one file). SA-1 added no functions and SA-2 did not touch `USERS` or `NOTIFICATION_PREFS`. SA-3 added names to the existing `from services.users import get_user` line without reformatting it (unlike Task 1 Session 3, where Claude rewrote an import line it was only asked to extend). The closest thing to a violation was in SA-4, and the cause was my prompt, not Claude: the prompt asked for a test on seed user `GET /api/users/1` *and* told Claude not to rely on seed users. Claude picked the second rule and dropped the first without telling me. I only noticed by comparing the test list to the prompt line by line.

**Did any subagent's output break the next subagent's assumption?**
No hand-off broke. SA-2 used `NOTIFICATION_PREFS` exactly as SA-1 named it; SA-3 called SA-2's three functions with the agreed signatures; SA-4's tests matched SA-3's status codes (200/404/422) on the first run. Two things passed through the pipeline unchecked, though:
- SA-2's error message prints a Python tuple — `must be one of ('email', 'sms', 'none')` — and SA-3 passes it straight to API clients. No subagent owned "what the error text looks like".
- A JSON body that is valid but not an object (e.g. `["email"]`) makes `PATCH /api/users/<id>/notifications` return 500 (`AttributeError` on `data.get`). I found it with a manual test-client check after SA-3. SA-3 followed its prompt; SA-4's prompt was written before I knew about it, and SA-4 was not allowed to edit source anyway. I recorded it rather than fixing it outside the pipeline. The existing `POST /api/tasks` and `PATCH /api/tasks/<id>` routes have the same weakness.

**Would you write the decomposition differently a second time?**
1. **Give SA-1 to SA-3 a real check.** Running `pytest -q` after them only showed 40 passed, the same as before. That proved nothing old broke, not that the new code worked. I had to check SA-2 and SA-3 by hand. Next time each subagent should add tests for its own layer, or the Hand-off field should name a command that proves the hand-off (e.g. a one-line `python -c` check).
2. **Re-read prompts for contradictions before running them.** The SA-4 conflict ("test user 1" vs "don't rely on seed users") was in the plan from the start. Claude resolved it silently rather than asking.
3. **Put the malformed-input cases in the API prompt.** SA-3's prompt covered missing keys (`data.get`) but not non-object bodies, so the 500 was built in by design.
4. **Settle the SA-4 "stop and report" vs PA5 "fix in the same session" conflict up front.** It never triggered because nothing failed, but if it had I would have had to break either my constraint or the course rule.
5. **Consider merging SA-1 and SA-2.** The boundary held, but SA-1 was a 4-line change and the split mainly tested whether Claude respects a boundary inside one file.
