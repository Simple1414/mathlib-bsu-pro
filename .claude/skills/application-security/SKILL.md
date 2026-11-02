---
name: application-security
description: Application security and OWASP Top 10 practices for this Django app. Use when handling file uploads/downloads, user input, CSRF, XSS, injection, secrets, security headers, dependency updates, or performing a security review or threat model.
---

# Application Security (OWASP)

## When to activate
- Uploads/downloads, forms, templates rendering user content, settings/security headers, dependencies, any security review.

## OWASP Top 10 mapped to this project
| Risk | Where it bites here | Control |
|------|---------------------|---------|
| A01 Broken Access Control | approval bypass, IDOR on books/articles, `/media/` direct access, GET mutations | object checks, scoped querysets, protected file serving, `@require_POST` |
| A02 Cryptographic Failures | default `SECRET_KEY`, no HTTPS | env-only secret (fail fast in prod), HTTPS + HSTS, secure cookies |
| A03 Injection | search/filter params, raw SQL | ORM only, parameterized SQL, validate filter choices against allow-lists |
| A04 Insecure Design | teacher self-approval, mass assignment | explicit form fields, approval workflow tests |
| A05 Misconfiguration | `DEBUG=True`, `SERVE_MEDIA_FILES=True`, missing headers | `check --deploy` clean, secure defaults |
| A06 Vulnerable Components | unpinned requirements | pin versions, `pip-audit` in CI |
| A07 Auth Failures | brute force on login | rate limiting, strong password validators |
| A08 Integrity Failures | malicious uploads | content-type sniffing, size limits |
| A09 Logging Failures | missing audit trail | `AuditLog` for privileged actions, no secrets in logs |
| A10 SSRF | (no outbound fetches today) | allow-list if URL fetching is ever added |

## File upload/download rules
- Validate extension **and** magic bytes (PDF starts with `%PDF-`; DOCX is a ZIP with `[Content_Types].xml`; legacy DOC is OLE `D0 CF 11 E0`). Images: verify with Pillow (`Image.verify()`).
- Enforce size (`validate_file_size`) and `FILE_UPLOAD_MAX_MEMORY_SIZE`.
- Store under randomized names (`upload_to` callables); never trust client filename for paths.
- Serve protected files only through permission-checked views; in production use nginx `internal` location + `X-Accel-Redirect`. Set `SERVE_MEDIA_FILES=False` by default.
- Send `Content-Disposition` with a sanitized filename and `X-Content-Type-Options: nosniff`.

## Required production settings
`DEBUG=False`, `SECRET_KEY` from env (raise `ImproperlyConfigured` if missing when not DEBUG), `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` (start 3600, then 31536000), `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER` (behind nginx), `SECURE_REFERRER_POLICY='same-origin'`, CSP (Django 6 native or `django-csp`).

## Security review workflow
1. Scope the diff; list entry points (URLs, forms, uploads).
2. For each: who can reach it, what input, what it changes, what it returns.
3. Check against the table above; try the abuse case mentally (and in a test).
4. Run `python manage.py check --deploy` with production-like env, and `pip-audit -r requirements.txt` if available.
5. Report findings with severity, file:line, exploit scenario, fix. Built-in `/security-review` complements this.

## Secrets
- Never read or print `.env`. Never commit keys, DB passwords, tokens. If one leaks: rotate first, then purge history.

## Testing requirements
- Tests for: GET on mutating URL → 405; unapproved book file not downloadable by students; upload with `.pdf` extension but non-PDF content rejected; registration can't set role.

## Checklist
- [ ] Access control at object level
- [ ] Mutations POST-only with CSRF
- [ ] Uploads validated by content, size, name
- [ ] No `|safe`/`mark_safe` on user data
- [ ] `check --deploy` clean; deps audited
- [ ] No secrets in code/logs
