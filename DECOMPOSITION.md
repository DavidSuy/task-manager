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

**`pytest -q` result:**

**Fixes made in session:**

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

**`pytest -q` result:**

**Fixes made in session:**

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

**`pytest -q` result:**

**Fixes made in session:**

---

## Divergence

- **Did Claude follow the constraint field for every subagent?** If not, which constraint was violated and what did Claude do instead?
- **Did any subagent's output break the next subagent's assumption?** How did you recover?
- **Would you write the decomposition differently a second time?** What would you change?
