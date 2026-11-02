---
name: performance-optimization
description: Performance engineering for the Django app — query optimization, caching, static/media delivery, gunicorn tuning, and front-end page weight. Use when pages are slow, query counts are high, before a release, or when adding list/search/dashboard features.
---

# Performance Optimization

## When to activate
- Slow page reports, dashboards with aggregates, search, large lists, image-heavy pages, pre-release checks.

## Principle
Measure → hypothesize → change one thing → measure again. No optimization without a number before and after.

## Backend
1. **Queries** (biggest win): count queries per view (`assertNumQueries`, Debug Toolbar). Fix N+1 with `select_related`/`prefetch_related`; aggregate in DB (`annotate(Count(...))`) instead of Python loops — dashboards and "popular" partials are prime suspects.
2. **Indexes**: see `postgresql-engineering`; verify with `EXPLAIN ANALYZE`.
3. **Pagination** on every list; never `list(qs)` on unbounded querysets.
4. **Caching**: per-view or fragment caching (`{% cache %}`) for public, rarely-changing blocks (categories, popular books) keyed by language; invalidate on save via signals or short TTL. Never cache per-user or permission-dependent content under a shared key. Use Redis/Memcached in production (ask before adding).
5. **Counters**: `F()` updates (already used for downloads); avoid write-per-view for analytics on hot paths — batch or debounce (`record_unique_book_view` is per-session, keep it so).
6. **Files**: serve large PDFs via nginx `X-Accel-Redirect` rather than streaming through gunicorn workers.
7. **Gunicorn**: workers ≈ 2×CPU+1; `--timeout` sized for uploads; `--max-requests` with jitter to bound memory.
8. **DB connections**: `CONN_MAX_AGE`, `CONN_HEALTH_CHECKS`.

## Frontend
- Covers: resize/compress on upload (Pillow; e.g. max 800px, WebP), `loading="lazy"`, explicit `width`/`height`.
- WhiteNoise compressed + hashed static files (configure via `STORAGES` in Django 5.1+), long cache headers.
- Minimal CSS/JS; no render-blocking third-party fonts without `font-display: swap`.
- Targets: LCP < 2.5s, CLS < 0.1, INP < 200ms on mid-range mobile.

## Security considerations
- Caches must not leak private data across users/roles.
- Rate-limit expensive endpoints (search, download) to prevent resource exhaustion.

## Testing requirements
- `assertNumQueries` regression tests for optimized views.
- Before/after numbers recorded in the PR description.

## Checklist
- [ ] Baseline measured
- [ ] Query count bounded and tested
- [ ] Indexes verified
- [ ] Caching safe across users
- [ ] Images/static optimized
- [ ] After-measurement shows improvement
