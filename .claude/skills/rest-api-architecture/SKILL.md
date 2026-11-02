---
name: rest-api-architecture
description: REST API design for exposing MathLib data (e.g. mobile app, search widget, integrations). Use when adding JSON endpoints, introducing Django REST Framework, designing resources, pagination, versioning, API authentication, throttling, or OpenAPI docs.
---

# REST API Architecture

The project is server-rendered today; there is no API. Use this skill when one is introduced.

## When to activate
- Any JSON endpoint, DRF adoption, or third-party integration.

## Decisions (ask before adding dependencies)
- Prefer **Django REST Framework** for >2 endpoints; plain `JsonResponse` for one-off internal endpoints.
- Version under `/api/v1/`. Separate `api/` app or `library/api/` package.
- Schema/docs: `drf-spectacular` → OpenAPI 3.

## Resource design
- Plural nouns: `/api/v1/books/`, `/api/v1/books/{id}/`, `/api/v1/categories/`, `/api/v1/me/favorites/`.
- Methods: GET (read), POST (create), PATCH (partial update), DELETE (soft delete). Actions as sub-resources: `POST /books/{id}/approval/`.
- Filtering/search/order via query params with allow-listed fields (`?category=3&language=tg&search=алгебра&ordering=-created_at`).
- Pagination: cursor or page-number with `count/next/previous/results`; enforce max page size.
- Consistent error body: `{"error": {"code": "permission_denied", "message": "...", "details": {...}}}`; correct status codes (400 validation, 401 unauthenticated, 403 forbidden, 404 hidden/not found, 409 conflict, 429 throttled).
- Return 404 (not 403) for content the user may not know exists (unapproved books).

## Security
- Auth: session auth for same-origin JS (CSRF enforced); token/JWT only for external clients, short-lived, stored securely.
- Permissions: reuse `library/permissions.py`; implement DRF `BasePermission` classes wrapping the same helpers; querysets scoped in `get_queryset()` with the same visibility rules as HTML views.
- Serializers list fields explicitly; read-only for `is_approved`, `uploaded_by`, `role`, counters.
- Throttling (`AnonRateThrottle`, `UserRateThrottle`), especially on search and downloads.
- CORS: deny by default; allow-list origins with `django-cors-headers` if needed.
- File downloads through the API still go through permission checks and `DownloadLog`.

## Testing requirements
- `APITestCase` per endpoint: role matrix, validation errors, pagination bounds, hidden content returns 404, throttling configured.
- Schema generation succeeds in CI.

## Checklist
- [ ] Versioned, plural, consistent resource URLs
- [ ] Explicit serializer fields; read-only sensitive fields
- [ ] Permissions + scoped querysets reuse existing rules
- [ ] Pagination, throttling, error format
- [ ] OpenAPI schema and tests
