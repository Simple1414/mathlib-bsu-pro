---
name: accessibility-seo
description: Accessibility (WCAG 2.2 AA) and SEO engineering for server-rendered Django pages. Use when building or auditing templates, forms, navigation, images, color/contrast, keyboard support, page titles, meta tags, sitemaps, robots.txt, or structured data for books.
---

# Accessibility & SEO Engineering

## When to activate
- New/changed templates, forms, or CSS affecting color/focus.
- Accessibility or SEO audits; public pages (home, book list/detail, article list/detail, about, contact).

## Accessibility (WCAG 2.2 AA)
- `<html lang="{{ LANGUAGE_CODE }}">` (tg/ru/en) — screen readers need correct language.
- Landmarks: one `<header>`, `<nav aria-label>`, `<main id="main">`, `<footer>`; "skip to content" link first in `<body>`.
- Headings: one `<h1>` per page, no skipped levels.
- Forms: every input has a `<label for>`; errors associated via `aria-describedby`; required fields marked in text, not color only; focus first invalid field.
- Images: meaningful `alt` (book covers: `alt="Муқоваи китоби {{ book.title }}"`); decorative images `alt=""`.
- Contrast ≥ 4.5:1 text, ≥ 3:1 large text and UI borders; visible `:focus-visible` outline (never `outline: none` without replacement).
- Keyboard: all actions reachable via Tab, Enter/Space; no keyboard traps; dropdowns/menus use buttons with `aria-expanded`.
- Messages (`django.contrib.messages`) in a `role="status"` (or `role="alert"` for errors) region.
- Tables: `<th scope>`, `<caption>`.
- Respect `prefers-reduced-motion`.
- Target size ≥ 24×24 CSS px (WCAG 2.2 SC 2.5.8).

## SEO
- Unique `<title>` per page: `{{ book.title }} — MathLib BSU`; `<meta name="description">` from book description (truncated ~155 chars, escaped).
- Canonical URLs (`<link rel="canonical">`), especially for filtered/paginated lists.
- `django.contrib.sitemaps` for approved, active, non-deleted books/articles only; `robots.txt` disallowing `/admin/`, `/accounts/`, `/dashboard/`, preview/download URLs.
- Open Graph tags for sharing; schema.org `Book` JSON-LD via `json_script`-safe rendering.
- `hreflang` alternates if language-specific URLs are introduced.
- Performance is SEO: optimized cover images, compressed static (WhiteNoise), no render-blocking extras.

## Audit workflow
1. Automated: run axe via Playwright MCP (`browser_evaluate` injecting axe-core) or Lighthouse on key pages.
2. Manual: keyboard-only pass; screen-reader spot check; zoom 200%.
3. SEO: view source for title/description/canonical; validate sitemap only lists public content.

## Security considerations
- Never include unapproved/private content in sitemaps, meta, or JSON-LD.
- Escape all meta content.

## Testing requirements
- View tests assert `<title>`, `lang`, and that sitemap excludes unapproved items.

## Checklist
- [ ] lang, landmarks, skip link, single h1
- [ ] Labels, alt text, contrast, focus visible
- [ ] Keyboard-only flow works
- [ ] Title/description/canonical per page
- [ ] Sitemap/robots expose public content only
