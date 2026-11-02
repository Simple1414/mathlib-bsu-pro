---
name: docker-devops-deployment
description: Docker, CI/CD, and production deployment (gunicorn + nginx + PostgreSQL on Linux) for MathLib BSU Pro. Use when writing Dockerfiles/compose files, GitHub Actions workflows, systemd/nginx configs, environment variables, static/media handling, backups, logging/monitoring, or planning a deployment. Never deploy without explicit approval.
---

# Docker, DevOps & Deployment

## When to activate
- Changes under `deploy/`, new `Dockerfile`/`compose.yaml`, `.github/workflows/`, environment/config, release prep.

## Hard rule
**Do not deploy, push images, restart services, or touch servers without explicit user approval for that specific action.**

## Docker
- Multi-stage `Dockerfile`: builder installs deps into a venv; runtime `python:3.12-slim`, non-root user, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, no compilers, no secrets in layers.
- `.dockerignore`: `.git`, `.venv`, `.env`, `media/`, `staticfiles/`, `__pycache__`.
- `collectstatic` at build; `migrate` as a separate release step, not in container start.
- `compose.yaml` for local dev: `web`, `db` (`postgres:16`, named volume, healthcheck), env via `env_file: .env` (never committed).
- Pin base image tags (and ideally digests).

## CI (GitHub Actions) — recommended pipeline
1. Checkout, setup Python 3.12, cache pip.
2. `pip install -r requirements.txt`.
3. Lint: `ruff check .` and `ruff format --check .` (once adopted).
4. `python manage.py check` and `makemigrations --check --dry-run`.
5. Tests against a `postgres:16` service.
6. `python manage.py check --deploy` with production-like env (`DEBUG=False`, dummy strong key).
7. `pip-audit`.
Use least-privilege `permissions:` in workflows; secrets via GitHub Secrets; pin third-party actions to SHAs.

## Production (current target: systemd + gunicorn + nginx)
- `deploy/gunicorn.service.example`: add `EnvironmentFile=/etc/mathlib/env` (mode 600), `Restart=on-failure`, `--access-logfile -`.
- nginx: TLS (Let's Encrypt), HTTP→HTTPS redirect, `client_max_body_size` ≥ upload limit, `/static/` alias with long cache, **`/media/` protected files as `internal` location** used via `X-Accel-Redirect`, security headers, `proxy_set_header X-Forwarded-Proto $scheme` + `SECURE_PROXY_SSL_HEADER`.
- Release steps: backup DB → pull code → install deps → `migrate` → `collectstatic` → restart → smoke test → monitor logs. Have a rollback plan (previous release dir + DB restore point).

## Observability
- Django `LOGGING` to stdout/journald, JSON in production; level INFO; `django.security` at WARNING+.
- Error tracking (e.g. Sentry) with PII scrubbing — ask before adding.
- Health endpoint (`/healthz`) checking DB connectivity, excluded from auth.
- Backups: nightly `pg_dump -Fc` + media rsync, off-site, restore drill monthly.

## Security considerations
- Secrets only in server env files / CI secrets; never in repo, images, or logs.
- Run as unprivileged user; media directory not executable; nginx must never execute uploaded files.

## Testing requirements
- CI must be green before merge; container build tested in CI; smoke test after deploy.

## Checklist
- [ ] No secrets in images/repo
- [ ] Non-root, pinned images
- [ ] CI: check, migrations check, tests, deploy check, audit
- [ ] TLS, headers, protected media
- [ ] Backup + rollback plan
- [ ] Explicit approval obtained before any deploy
