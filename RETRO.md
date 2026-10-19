# PA6 Task 3A — Retro

**1. Slash command value.** `/scaffold-endpoint` (COMMAND_LOG.md row 3, `tags POST`) saved the
most prompt-writing effort of the three. The equivalent ad-hoc prompt would have had to spell
out, every time: "create `schemas/tags.py` as a `TypedDict`; create `services/tags.py` with a
`create_tag` function that validates input before writing to a module-level `TAGS` dict and
raises `NotFoundError`/`ValidationError` from `utils/errors.py`; add a route in `routes/api.py`
that only parses `request.get_json()`/`data.get(...)` and calls one service function, with no
business logic in the route; follow `update_notification_pref_route`/`update_notification_pref`
as the canonical route/service pair since there is no `routes/tasks.py`; give every function
type hints and a Google-style docstring with `Args:`/`Returns:`/`Raises:`; append the new import
to the existing import line in `routes/api.py` without reformatting it; don't touch
`utils/errors.py` or existing tests; add a happy-path test in `tests/test_api.py` using its
`client` fixture asserting 201; then run `pytest -q` and `ruff check .` and confirm it's still 6
errors." That is the entire `scaffold-endpoint.md` Goal/Context/Constraints/Verification
re-typed by hand, and any omitted clause (e.g. forgetting "no business logic in the route") is a
rule violation that only gets caught after the fact. The command replaces all of that with two
words, `tags POST`, and the COMMAND_LOG row shows it stayed in scope on the first try — the only
gap it left (`create_tag` accepting `{"name": 5}`) was a genuinely new finding, not a forgotten
instruction, and it fed directly into the next two rows (`/add-tests create_tag`,
`/audit-errors services/tags.py`).

**2. Hook reliability.** Both Part B vectors show that registering a hook in `.claude/settings.json`
only guarantees the hook *runs* for a tool, not that its internal logic *covers* every way that
tool can reach a protected path. Vector 1 (HOOK_LOG.md, "Vector 1: Case sensitivity") got through:
`Write` to `Utils/errors.py` exited 0 before the fix, because `check_write_like` did an exact,
case-sensitive `rel_path in BLOCKED_PATHS` comparison, so the capitalized path simply didn't
match the string `"utils/errors.py"`; because this filesystem is case-sensitive, `Write` didn't
just fail to recognize the same file — it created a separate shadow file, `Utils/errors.py`,
containing a `ConflictError` module that imported from `utils.errors`, sitting right next to the
protected one, exactly as the `git status --untracked-files=all` output in HOOK_LOG.md's attempt
2 shows. Vector 1's first attempt (`Edit`) never actually exercised the hook at all — the `Edit`
tool's own file-exists check failed before the hook ran (HOOK_LOG.md, "Result (attempt 1)"), so
that "no change" result by itself proved nothing about whether `guard_writes.py` would have
blocked it; only attempt 2's `Write` call, which did reach the hook, demonstrated the real
bypass. Vector 2 ("Vector 2: Bash indirect write") also got
through: `echo "# vector 2 test" >> utils/errors.py` via the Bash tool exited 0, because
`check_bash` only ran `BASH_PATTERNS` (SQL/`rm -rf`/`git push --force`) and never checked the
Bash command's write target against `BLOCKED_PATHS` at all — the matcher
`"Write|Edit|MultiEdit|Bash"` in `.claude/settings.json` was already correct and unchanged
through both fixes (commits `57ebb28` and `3ee773b`); what was missing was logic inside
`guard_writes.py` itself. In both cases the rule "protect `utils/errors.py`" was fully wired into
the hook configuration from commit `b19aba9` onward, and still failed in practice until the
underlying comparison (case-insensitive matching, then command-target extraction) was fixed and
re-verified against the exact same bypass command. That's the gap: "the rule is in
`settings.json`" means the hook is invoked; "the rule is enforced" requires the hook's code to
actually recognize every path and tool-call shape that reaches the protected resource, which has
to be demonstrated vector by vector, not assumed from the matcher string.

**3. Advisory vs. deterministic.** The "Do not touch" rule "Existing tests in
`tests/test_tasks.py` — never edit a test to make it pass" (CLAUDE.md) stays advisory because the
hook can only make path-level and regex-level decisions (which file, which literal pattern) in
`check_write_like`/`check_bash`, and this rule isn't path-level — it has to distinguish a
legitimate *addition* (new tests go in `tests/test_tasks.py` per the Conventions section, and
`/add-tests` targets exactly these files) from a destructive *edit* to an existing test's body,
which requires comparing the proposed new content against the current on-disk file line-by-line,
not just matching a path or a connection-string regex the way the `services/tasks.py` guard
does. The trigger that would move me to act: the first time a `git diff` review shows any
changed or removed line inside an existing `def test_` function in `tests/test_tasks.py`.
Measurable condition for promoting it into `guard_writes.py` from there: add a content guard for
`tests/test_tasks.py` (parallel to the existing `services/tasks.py` connection-string check) that
reads the file's current content via `project_dir`, and blocks the `Edit`/`MultiEdit`/`Write`
call if any line that falls within an *existing* `def test_` function's body (from its `def` line
to the next top-level `def` or EOF) is removed or changed in the proposed new content — i.e. the
diff may only add new lines after the last existing function, never remove or alter one. Once
that line-level diff check is written and passes a new regression pair in
`tests/test_guard_writes.py` (one case that edits an existing assertion → blocked, one that
appends a new `def test_` → allowed) without any false positive on a real `/add-tests` run, it
moves from CLAUDE.md into the hook.

**4. Limits of hooks.** I wanted to enforce "a write to `utils/errors.py` is blocked no matter how
the shell gets there," but a `cd`-prefixed command defeats it: feeding
`cd utils && echo "# cd bypass" >> errors.py` directly to `.claude/hooks/guard_writes.py` (same
stdin-JSON method HOOK_LOG.md uses for its "Direct test of the hook script" checks, not run
through the real Bash tool, so nothing was actually written) exits 0 — `check_bash`'s
`targets_in_segment` finds the redirection target `errors.py` and calls
`relative_path("errors.py", project_dir)`, which resolves it against the *project root*, not
against the working directory the preceding `cd utils` would actually leave the shell in, so it
never normalizes to `utils/errors.py` and never matches `BLOCKED_PATHS`. PreToolUse is the wrong
mechanism for this, not just the wrong event: it receives one static command string and has to
pattern-match/tokenize it without actually interpreting shell state (`cd`, variable expansion,
subshells, aliases) — closing this hole in the hook would mean re-implementing a shell
interpreter in Python, and even a correct one would just invite the next unmodeled construct. The
right mechanism is enforcement at the OS/filesystem layer instead of the command-text layer: make
`utils/errors.py` genuinely unwritable to the process running the Bash tool (e.g. `chmod 444
utils/errors.py`, or a read-only bind-mount over that path) so the write fails regardless of
which directory the shell is in or how the command is phrased, with `guard_writes.py` left to
catch tool calls (`Write`/`Edit`) that never go through a shell at all.
