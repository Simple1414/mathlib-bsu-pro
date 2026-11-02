---
name: auth-and-rbac
description: Authentication and role-based authorization for the Admin/Librarian/Teacher/Student model. Use when touching login, registration, passwords, sessions, role assignment, permission decorators/mixins, object-level access, or any view that must restrict who can see or change data.
---

# Authentication & Authorization (RBAC)

## When to activate
- Changes to `accounts/` views/forms, `library/permissions.py`, `AdminRequiredMixin`, `role_required`.
- Any new view or change in who can access existing content.

## Model
| Role | Can |
|------|-----|
| ADMIN (or superuser) | everything; assign roles; activate/deactivate users |
| LIBRARIAN | create/edit/approve books & articles; handle requests |
| TEACHER | submit books/articles (pending approval); edit own submissions if allowed by `can_be_managed_by` |
| STUDENT | browse approved content, download (if allowed), favorites, requests, comments/ratings |
| Anonymous | browse public approved content only |

## Rules
- **Deny by default.** New views start with `@login_required` or `role_required(...)`, then open up deliberately.
- Enforce at three layers: view decorator/mixin (coarse), object check (`can_be_managed_by`, ownership), queryset scoping (visibility). Templates only *hide* UI.
- Registration form must never accept `role`, `is_staff`, `is_superuser`, `is_active`. New users = STUDENT.
- Role changes: admin only, POST only, audited (`AuditLog`), cannot demote/deactivate yourself, last admin must not be removable.
- `role_required` redirects on failure; for non-HTML/API endpoints return 403 (`PermissionDenied`).
- Passwords: Django hashers (PBKDF2/Argon2), validators already configured (min length 8 — consider 10+). Use Django's built-in password reset/change views.
- Sessions: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` in prod; call `login()` (rotates session key) and consider `SESSION_COOKIE_AGE` limits for staff.
- Brute force: add rate limiting on login (e.g. `django-axes`) before production — ask before adding a dependency.
- Use `user.is_superuser or user.role in (...)` consistently through helpers; do not scatter string comparisons.

## Workflow for a new protected feature
1. Write the access matrix (roles × actions) in the PR/plan.
2. Implement helpers in `library/permissions.py` (single source of truth).
3. Apply decorator + object check + queryset scoping.
4. Write matrix tests (below).

## Security considerations
- IDOR: changing `pk` in the URL must not grant access. Test it.
- Privilege escalation via forms (mass assignment) — explicit `fields` only.
- Open redirects: validate `next` with `url_has_allowed_host_and_scheme`.
- Never reveal whether an email/username exists in error messages beyond Django defaults.

## Testing requirements
- Parametrized matrix: for each protected URL × {anon, student, teacher, librarian, admin} assert status/redirect.
- Owner vs non-owner tests for teacher-editable objects.
- Registration cannot set role (POST `role=ADMIN` → user is still STUDENT).

## Checklist
- [ ] Access matrix documented
- [ ] Decorator + object check + scoped queryset
- [ ] POST-only and audited for privileged mutations
- [ ] Matrix + IDOR + escalation tests pass
