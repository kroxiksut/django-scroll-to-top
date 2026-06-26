# Integration Guide (AI)

## Scope

Use this guide to wire `django-scroll-to-top` into a Django project. Goal: a
rendered, accessible scroll-to-top control on the site and in the standard Django
Admin, with no appearance logic in settings.

## Steps

1. Install: `pip install django-scroll-to-top` (until released, install the
   checkout with `pip install -e .`).
2. Add the app to `INSTALLED_APPS`. If admin integration is on, place
   `django_scroll_to_top` **before** `django.contrib.admin`.
3. Configure install/infrastructure only via the `DJANGO_SCROLL_TO_TOP` dict
   (all keys optional):
   - `SITE_ENABLED` (bool), `ADMIN_ENABLED` (bool)
   - `SITES_FRAMEWORK_ENABLED` (bool)
   - `CSP_MODE` (`"external"` | `"nonce"`)
   - `ADMIN_SHOW_ON_AUTH_PAGES` (bool)
   - `DEFAULT_COLLISION_POLICY` (`ignore` | `shift` | `fallback_corner` | `hide`)
   - hooks: `SITE_ID_RESOLVER`, `PROFILE_RESOLVER`, `OBSTACLE_SELECTORS`
4. Include the package URLConf under namespace `django_scroll_to_top`
   (`include(("django_scroll_to_top.urls", "django_scroll_to_top"), namespace=...)`).
   This serves the versioned same-origin stylesheet endpoint.
5. Run `python manage.py migrate`.
6. Render once in the base template, near `</body>`:
   `{% load scroll_to_top %}` then `{% scroll_to_top %}`.
7. Verify with `python manage.py check` and
   `python manage.py scroll_to_top_diagnose`.

## Admin scope

The control is injected into the standard admin via
`templates/admin/base_site.html` (normal template resolution — no middleware, no
`AdminSite` monkeypatching). For a custom `AdminSite` or an overridden
`base_site.html`, add `{% scroll_to_top scope="admin" %}` in the `footer` block
(after `{% load scroll_to_top %}`).

## Guardrails

- **No visual template-tag arguments.** The only argument is `scope="admin"`.
- Settings own install/infrastructure only — never appearance.
- Resolution is site-specific → global → safe built-in defaults. With no DB
  config, the tag still renders from defaults; do not create rows while
  rendering.
- Invalid `CSP_MODE` / `DEFAULT_COLLISION_POLICY` fall back to defaults and are
  flagged by system checks `dstt.W003` / `dstt.W006`; wrong app order is
  `dstt.W005`; a missing URLConf is `dstt.W004`.
- A faulty hook must never break rendering (exceptions/import errors fall back).

## Reference

- [Quick start](../en/quickstart.md) · [Configuration](../en/configuration.md)
- [Diagnostics](../en/diagnostics.md)
