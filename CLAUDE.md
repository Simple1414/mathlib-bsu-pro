# CLAUDE.md — MathLib BSU Pro

Electronic library for the Faculty of Mathematics, Bokhtar State University.
Stack: **Python 3.12+ · Django 5.2 · PostgreSQL · server-rendered templates · WhiteNoise · gunicorn + nginx**.
User-facing text is in **Tajik** (`LANGUAGE_CODE='tg'`); also `ru`, `en`. Keep UI strings in Tajik unless told otherwise.

## Project map

| Path | Responsibility |
|------|----------------|
| `config/` | settings (env-driven via `python-dotenv`), root URLs, WSGI/ASGI |
| `accounts/` | custom `User` (`AUTH_USER_MODEL='accounts.User'`), `University`/`Faculty`/`Specialty`, registration, role management |
| `library/` | `Book`, `Article`, `Author`, `Category`, comments, ratings, favorites, requests, `DownloadLog`, `AuditLog`; `permissions.py` (role helpers) |
| `dashboard/` | per-role dashboards |
| `templates/`, `static/css/style.css` | UI |
| `deploy/` | gunicorn systemd + nginx examples |
| `docs/` | technical spec, roadmap, security checklist |

## Domain rules (do not break)

- Roles: `ADMIN`, `LIBRARIAN`, `TEACHER`, `STUDENT`. New users are **always** `STUDENT`.
- Only an admin may change roles. Teachers may *submit* books; publication requires librarian/admin approval.
- Unapproved/inactive/soft-deleted (`is_deleted`) content must never be visible to people who cannot manage it.
- Downloads require login, respect `is_download_allowed`, and write a `DownloadLog` + `AuditLog` entry.
- Authorization lives server-side: `library/permissions.py` (`role_required`, `can_manage_books`, `can_submit_books`), model methods like `can_be_managed_by`. Never rely on hiding a button.

## Commands

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py check                 # always run after changes
python manage.py makemigrations --check --dry-run   # detect missing migrations
python manage.py test                  # test suite (to be built; see "Testing")
python manage.py check --deploy        # with production env vars
pyright accounts library dashboard config   # type check (pyright-lsp plugin uses this)
```

Secrets come from `.env` (gitignored). **Never read, print, or commit `.env`**; document new variables in `.env.example` with placeholder values.

## Engineering standards

**Workflow for any significant feature:** requirements → design (models, URLs, permissions, migrations) → plan → implement → tests → review → docs. For multi-step work use `superpowers:writing-plans`; for bugs use `superpowers:systematic-debugging` (root cause before fix).

**Code**
- Follow PEP 8, type-hint new/changed functions, prefer small functions with one responsibility. KISS and DRY, but no speculative abstraction.
- Business rules belong in models / model managers / service functions, not templates. Views orchestrate.
- Use `QuerySet` methods (`BookQuerySet`, `ArticleQuerySet`) for visibility filters so the rule exists in one place.
- Always `select_related` / `prefetch_related` in list views; avoid N+1 queries. Use `F()` for counters.
- Errors: raise `Http404` / `PermissionDenied`, never leak stack traces; log with `logging.getLogger(__name__)`, never log secrets or personal data beyond what is necessary.

**Security (OWASP)**
- State-changing views: `@require_POST` + CSRF token in a `<form method="post">`. Never mutate on GET.
- Every view that touches objects checks permissions on *that object* (IDOR protection).
- Uploads: extension **and** content validation, size limits, randomized storage names; protected files served through views (or nginx `X-Accel-Redirect`), not public `/media/`.
- No raw SQL with string formatting; use the ORM or parameterized queries.
- Templates auto-escape; never use `|safe` / `mark_safe` on user input.
- Production: `DEBUG=False`, strong `SECRET_KEY` from env, HTTPS, secure cookies, HSTS, `check --deploy` clean.

**Database**
- Every model change ships with a migration; review it with `sqlmigrate`. Migrations must be reversible and safe for existing data (add nullable → backfill → constrain).
- Never edit an applied migration. Never run `migrate`, `flush`, or destructive SQL against a shared/production DB without explicit approval.
- Add indexes for fields used in filters/ordering; use DB constraints (`UniqueConstraint`, `CheckConstraint`) for invariants.

**Frontend**
- Semantic HTML, mobile-first responsive CSS, WCAG 2.2 AA (labels, contrast ≥ 4.5:1, keyboard focus, `alt` text, `lang` attribute).
- Reuse `templates/includes/` and partials; keep design tokens (colors, spacing) as CSS custom properties.

**Testing**
- The repo currently has **no tests**. Any change to permissions, visibility, uploads, or downloads must add tests.
- Use Django `TestCase` (or `pytest-django` if adopted). Cover: each role × each protected view (allowed and denied), hidden content stays hidden, POST-only enforcement, upload validation.
- Do not claim a change works without running `python manage.py check` and the relevant tests; report failures honestly.

**Git**
- Small, focused commits; imperative subject ≤ 72 chars; body explains *why*.
- Never force-push shared branches, never commit secrets, media, `db.sqlite3`, or `staticfiles/`.

## Claude Code setup in this repo

- **Plugins** (`.claude/settings.json`, official marketplace): superpowers, frontend-design, code-review, pr-review-toolkit, code-simplifier, commit-commands, claude-code-setup, pyright-lsp, context7, playwright.
- **Skills** (`.claude/skills/`): project-tuned engineering guides — invoke the matching one before starting work in that area.
- **Agents** (`.claude/agents/`): specialists. Read-only reviewers (`security-auditor`, `code-reviewer`, `performance-engineer`, `principal-architect`) may run in parallel; agents that edit files must not touch the same files concurrently.
- Use **context7** for current Django/PostgreSQL docs instead of relying on memory.

## Known issues (open, as of 2026-11-02)

1. `approve_book`, `toggle_favorite`, `toggle_user_active` accept GET → CSRF-able state changes (`require_POST` imported, not applied).
2. `SERVE_MEDIA_FILES` defaults to `True`; `/media/` exposes book files regardless of login/approval/`is_download_allowed`.
3. `STATICFILES_STORAGE` is ignored since Django 5.1 — migrate to `STORAGES`.
4. `SECRET_KEY` falls back to a hardcoded default; should fail fast when `DEBUG=False`.
5. No test suite, no CI, no `.env.example` (README references it).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

### Claude Code add-ons (setup per machine)

- **Ponytail** and **Agent Skills** (addyosmani) are enabled in `.claude/settings.json`; Claude Code installs them from their marketplaces on first trust of this folder (Ponytail needs Node.js on PATH).
- **Graphify** hooks in `.claude/settings.json` call the `graphify` CLI. Install it once and build the graph locally (it is gitignored):
  `pip install graphifyy && graphify update .`
- **Design plugins** enabled in `.claude/settings.json`: UI UX Pro Max (needs Python), Taste (needs Node 22+ and Chrome/Chromium), Impeccable (runs a design-check hook on UI edits; downloads its engine to `~/.impeccable/bin/` on first use; turn telemetry off with `DO_NOT_TRACK=1`), PPT Master (run `pip install -r requirements.txt` in its plugin folder before generating decks).
- **Archify** (diagrams) is gitignored because of its size; `skills-lock.json` records it. Restore it with:
  `npx -y skills@latest add tt-a1i/archify --skill archify --agent claude-code --copy --yes`
