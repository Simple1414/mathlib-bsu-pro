---
name: django-development
description: Django 5.2 development conventions for MathLib BSU Pro. Use when adding or changing models, views, URLs, forms, templates, admin, management commands, context processors, settings, or i18n in this project.
---

# Django Development

## When to activate
Any change under `accounts/`, `library/`, `dashboard/`, `config/`, or `templates/` that involves Django APIs.

## Architecture in this repo
- Function-based views dominate `library/` and `dashboard/`; `accounts/` uses CBVs with `AdminRequiredMixin`. Follow the style of the file you are editing.
- Visibility rules: `BookQuerySet` / `ArticleQuerySet`, helpers `public_or_manageable_book/article` in `library/views.py`. Reuse them; do not re-implement filters.
- Auditing: `audit(request, action, object_name)` for important actions; downloads also write `DownloadLog`.
- Roles: `User.Role`, helpers in `library/permissions.py`.

## Feature workflow
1. **Model**: fields with `verbose_name` in Tajik, `help_text`, sensible `on_delete`, `Meta.ordering`, `indexes`, `constraints`, `__str__`, `get_absolute_url`.
2. **Migration**: `python manage.py makemigrations <app>` → inspect file → `python manage.py sqlmigrate <app> <n>`.
3. **Form**: `ModelForm` with explicit `fields` (never `__all__` / `exclude` on user-facing forms — mass-assignment risk, e.g. `role`, `is_approved`).
4. **View**: authenticate → load object with permission check → validate form → act (in `transaction.atomic()` if multi-write) → audit → `messages` → redirect (PRG pattern).
5. **URL**: namespaced (`app_name`), named, `<int:pk>` converters.
6. **Template**: extend `base.html`, use `{% url %}`, `{% csrf_token %}` in every POST form, Tajik copy.
7. **Admin**: `list_display`, `list_filter`, `search_fields`, `raw_id_fields`/`autocomplete_fields` for FKs.
8. **Tests** (see `django-testing`).

## Rules
- Mutations only on POST: decorate with `@require_POST` (or `@require_http_methods`). Links that change state must become forms.
- Use `get_object_or_404` + an ownership/role check, or a queryset scoped to the user.
- Use `F()` expressions and `update()` for counters to avoid race conditions.
- Pagination via `Paginator` for every list (`book_list`, `article_list`, user list).
- Settings: read from env with safe defaults for dev; production defaults must be secure.
- Django 5.1+ removed `STATICFILES_STORAGE`/`DEFAULT_FILE_STORAGE`; use `STORAGES = {"default": ..., "staticfiles": ...}`.
- Query docs with context7 (`/django/django`) when unsure of an API for 5.2.

## Security considerations
- Never expose `is_approved`, `role`, `is_staff`, `is_superuser`, `uploaded_by` in user-editable forms.
- File responses: serve via view after permission check; set `as_attachment` appropriately; sanitize filenames.
- `messages` and template output are auto-escaped; never `mark_safe` user data.

## Testing requirements
- For each new view: anonymous, each role, and owner/non-owner cases; POST-only verification (GET returns 405).

## Checklist
- [ ] Migration created and reviewed
- [ ] Explicit form fields; permission check on the object
- [ ] POST-only for mutations, CSRF token present
- [ ] `select_related`/`prefetch_related` on lists; pagination
- [ ] Audit log for privileged actions
- [ ] Tests added; `python manage.py check` clean
