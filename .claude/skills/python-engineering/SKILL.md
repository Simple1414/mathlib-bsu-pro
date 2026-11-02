---
name: python-engineering
description: Python engineering and refactoring standards for this codebase. Use when writing or refactoring Python modules, adding type hints, restructuring functions/classes, extracting services, handling errors/logging, or reducing complexity in accounts/, library/, dashboard/, or config/.
---

# Python Engineering & Refactoring

## When to activate
- Writing new Python code or changing existing functions/classes.
- Refactoring: long views (>40 lines), duplicated logic, deep nesting, unclear names.
- Adding typing, logging, or error handling.

## Standards
- Python 3.12+. PEP 8, 4-space indent, max line ~100.
- Type-hint every new or modified function signature. Use `from __future__ import annotations` only if needed; prefer built-in generics (`list[str]`, `dict[str, int]`, `X | None`).
- For Django models in annotations use the class directly; for request use `django.http.HttpRequest`.
- Names: verbs for functions (`record_unique_book_view`), nouns for data, `is_/has_/can_` for booleans.
- One responsibility per function. Extract a **service function** (e.g. `library/services.py`) when a view does more than validate → act → respond, or when two views share logic.
- Never catch bare `except:`; catch specific exceptions, and never swallow them silently — log with `logger = logging.getLogger(__name__)`.
- Use `pathlib`, f-strings, `enumerate`, comprehensions where they improve clarity — not for cleverness.
- Constants in UPPER_CASE at module top; no magic numbers (file size limits, page sizes).

## Refactoring workflow
1. Confirm behavior is covered by tests. If not, write characterization tests first (see `django-testing`).
2. Make one mechanical change at a time (rename, extract, inline, move).
3. Run `python manage.py check` and tests after each step.
4. Keep public interfaces (URL names, template context keys, model fields) stable unless the task is to change them.
5. Commit refactors separately from behavior changes.

## Type checking
- `pyright accounts library dashboard config` (pyright-lsp plugin surfaces diagnostics while editing).
- Django's dynamic attributes produce false positives; prefer `django-stubs` if strictness is adopted, and use targeted `# type: ignore[code]` with a reason, never blanket ignores.

## Security considerations
- Never `eval`/`exec`, `pickle.loads` untrusted data, or `subprocess` with `shell=True` and user input.
- Never log passwords, tokens, session keys, or full file paths of protected media.
- Read config only via `os.getenv` in `config/settings.py`; never hardcode secrets.

## Testing requirements
- Every extracted function gets a direct unit test.
- Refactors must leave the existing test suite green with no test edits other than imports.

## Checklist
- [ ] Type hints on changed signatures
- [ ] No duplicated logic introduced; no dead code left behind
- [ ] Specific exceptions, logged appropriately
- [ ] `python manage.py check` passes; tests pass
- [ ] Diff is minimal and focused
