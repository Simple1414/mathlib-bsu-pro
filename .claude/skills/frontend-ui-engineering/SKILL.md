---
name: frontend-ui-engineering
description: Django-template frontend, design system and responsive web development for MathLib BSU Pro. Use when creating or restyling templates, editing static/css/style.css, building UI components (cards, tables, forms, dashboards), defining design tokens, or making pages responsive. For bold visual direction, combine with the frontend-design plugin skill.
---

# Frontend, UI/UX Design System & Responsive Development

## When to activate
- Any change to `templates/**` or `static/**`.
- New pages, dashboard widgets, forms, navigation.

## Design system
- Define tokens once in `:root` of `static/css/style.css`: `--color-primary`, `--color-surface`, `--color-text`, `--color-muted`, `--color-danger`, `--space-1..8` (4px scale), `--radius`, `--shadow`, `--font-sans`, type scale (`--fs-sm/base/lg/xl/2xl`).
- Components reuse tokens; no hardcoded hex values in component rules.
- Academic, trustworthy tone: restrained palette, clear hierarchy, generous whitespace. Typography must support Tajik Cyrillic (ҳ ҷ ӣ ӯ қ ғ) — verify the chosen font has these glyphs.
- Component inventory: buttons (primary/outline/danger/small), cards (`templates/library/partials/book_card.html`), tables, form fields (`templates/includes/form.html`), messages, pagination, empty states, badges for status (pending/approved).

## Responsive rules
- Mobile-first: base styles for ~360px, enhance with `@media (min-width: 640px | 1024px)`.
- Layout with CSS Grid/Flexbox; `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))` for book grids.
- Fluid type with `clamp()`; images `max-width: 100%; height: auto`; covers use `aspect-ratio` + `object-fit: cover` to prevent layout shift.
- Tables: wrap in `overflow-x: auto` container or stack to cards on small screens.
- Touch targets ≥ 44×44px.

## Template rules
- Extend `base.html`; blocks for `title`, `content`, `extra_head`.
- Reuse partials/includes; no copy-pasted markup between role dashboards.
- State-changing actions are `<form method="post">{% csrf_token %}` buttons, not links.
- Show role-appropriate actions, but never rely on hiding as security.
- No inline `<script>` with user data; if JS needs data use `{{ data|json_script:"id" }}`.

## UX workflow
1. Identify the user role and their primary task on the page.
2. Sketch hierarchy: one primary action per view.
3. Build with existing components; add a new component only if reused ≥2 times.
4. Check states: empty, loading/long text, error, success message, permission denied.
5. Verify at 360 / 768 / 1280 px (Playwright MCP screenshots: `browser_resize`, `browser_take_screenshot`).
6. Run the `accessibility-seo` checklist.

## Security considerations
- Auto-escaping on; never `|safe` on user content (titles, comments, descriptions).
- External assets only from trusted CDNs with SRI, or self-host.

## Testing requirements
- View tests assert key content renders for each role; Playwright smoke check for critical flows (login, search, book detail, upload form) before release.

## Checklist
- [ ] Tokens used; no stray hex/px magic values
- [ ] Works at 360/768/1280 px, no horizontal scroll
- [ ] All states designed (empty/error/success)
- [ ] Forms POST with CSRF; Tajik copy consistent
- [ ] Accessibility checklist passed
