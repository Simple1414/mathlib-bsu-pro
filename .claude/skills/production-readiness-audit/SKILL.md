---
name: production-readiness-audit
description: End-to-end production readiness audit for MathLib BSU Pro before go-live or a major release. Use when asked whether the app is ready for production, before deployment, or for a full health check across security, data, testing, performance, accessibility, operations and documentation.
---

# Production Readiness Audit

## When to activate
- "Is this ready for production?", pre-release, post-incident review, periodic health check.

## Workflow
1. **Inventory**: `git log` since last release, `requirements.txt`, settings, URLs (`python manage.py show_urls` if available, else read `*/urls.py`).
2. **Run checks** (report exact output):
   - `python manage.py check`
   - `DEBUG=False SECRET_KEY=<dummy-50-chars> python manage.py check --deploy`
   - `python manage.py makemigrations --check --dry-run`
   - `python manage.py test`
   - `pip-audit -r requirements.txt` (if available)
3. **Review** each area below. Parallelize read-only review with agents: `security-auditor`, `performance-engineer`, `qa-automation-engineer`, `devops-engineer`, `code-reviewer`.
4. **Report**: table of area → status (PASS / FAIL / NOT VERIFIED) → evidence → fix. Never mark PASS without evidence.

## Gates
**Security** — DEBUG off; secret from env, fail-fast; HTTPS/HSTS/secure cookies; mutations POST-only; object-level permissions; protected media (`SERVE_MEDIA_FILES=False` + X-Accel-Redirect); upload content validation; login rate limiting; admin URL protected; dependencies audited; `docs/SECURITY_CHECKLIST.md` all checked.
**Data** — migrations applied cleanly on a prod copy; constraints/indexes; backups automated and a restore tested; least-privilege DB user.
**Quality** — test suite exists and passes; permission matrix tests; CI green; no critical review findings.
**Performance** — key pages bounded query counts; static compressed/hashed (`STORAGES`); images optimized; gunicorn tuned.
**Accessibility/SEO** — WCAG AA spot audit on key pages; titles/meta; sitemap public-only.
**Operations** — logging configured; error tracking; health check; runbooks for deploy/rollback/restore; monitoring/alerting owner named.
**Legal/Policy** (from README §9) — copyright policy, PDF permission policy, librarian responsibilities defined.

## Security considerations
- Run checks with dummy secrets, never real production values. Do not connect to production systems without explicit approval.

## Checklist
- [ ] All commands run and outputs captured
- [ ] Every gate marked with evidence
- [ ] Blockers listed first, with owners and fixes
- [ ] No claim of readiness while any blocker is open
