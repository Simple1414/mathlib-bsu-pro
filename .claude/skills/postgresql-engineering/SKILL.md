---
name: postgresql-engineering
description: PostgreSQL schema design, Django migrations, indexing and query optimization. Use when designing models/relations, writing or reviewing migrations, adding indexes or constraints, diagnosing slow queries or N+1 problems, implementing search, or planning backups.
---

# PostgreSQL Engineering & Database Optimization

## When to activate
- New/changed models or relations; any migration.
- Slow pages, high query counts, search/filter features.
- Backup, restore, permissions, or connection settings.

## Schema design
- Normalize to 3NF; denormalize only with a measured reason (e.g. `downloads_count` cache — keep it updated with `F()`).
- Enforce invariants in the DB: `UniqueConstraint` (e.g. one rating per user per book), `CheckConstraint` (rating 1–5), `NOT NULL` where required.
- Choose `on_delete` deliberately: `PROTECT` for reference data (Category, Faculty), `CASCADE` for owned children (comments), `SET_NULL` for authorship history.
- Prefer soft delete (`is_deleted`) consistently and filter it in managers.

## Migrations
- One logical change per migration; descriptive names (`--name add_book_isbn_index`).
- Safe sequence for new required field on populated table: add nullable → data migration (`RunPython` with reverse) → `AlterField` to non-null.
- Large tables: `AddIndexConcurrently` / `RemoveIndexConcurrently` from `django.contrib.postgres.operations` with `atomic = False`.
- Always inspect: `python manage.py sqlmigrate app 000N` and `makemigrations --check --dry-run` in CI.
- Never edit applied migrations; never squash without coordination.

## Query optimization workflow
1. Measure: Django Debug Toolbar locally, or `django.db.connection.queries` / `assertNumQueries` in tests.
2. Fix N+1 with `select_related` (FK/one-to-one) and `prefetch_related` (M2M/reverse FK, e.g. `authors`).
3. Fetch less: `.only()`, `.values()`, `.exists()` instead of `.count() > 0`, `.count()` instead of `len(qs)`.
4. Index columns used in `filter`/`order_by` together: e.g. `Index(fields=['is_approved','is_active','is_deleted','-created_at'])`.
5. Verify with `EXPLAIN ANALYZE` (`qs.explain(analyze=True)`) on realistic data.
6. Search: `icontains` is fine for small data; for scale use `django.contrib.postgres.search` (`SearchVector`, GIN index) or `pg_trgm` trigram index. Tajik Cyrillic text: use the `simple` config, not `english`.

## Operations
- Connection: `CONN_MAX_AGE` (e.g. 60) and `CONN_HEALTH_CHECKS=True` in production.
- Least privilege: the app role owns its schema but is not superuser; separate read-only role for reporting/inspection.
- Backups: nightly `pg_dump -Fc`, retained off-server, **restore tested** regularly; media files backed up alongside.

## Security considerations
- Never interpolate user input into SQL; use ORM or `cursor.execute(sql, params)`.
- Credentials only from env; never in code, docs, or MCP config committed to the repo.
- Never run `migrate`, `flush`, `DROP`, `TRUNCATE` against shared/prod DBs without explicit approval.

## Testing requirements
- `assertNumQueries` tests for list/detail views after optimization.
- Data migrations tested forward and backward on a copy.

## Checklist
- [ ] Constraints express invariants
- [ ] Indexes match query patterns; verified with EXPLAIN
- [ ] Migration reversible and reviewed with sqlmigrate
- [ ] No N+1 in changed views
- [ ] No raw SQL formatting; no secrets
