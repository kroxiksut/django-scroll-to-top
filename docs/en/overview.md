# Overview and current status

- [Back to documentation index](../README.md)
- [Project overview (root README)](../../README.md)

## Purpose

This document records:

- what is already implemented in the package;
- which invariants must not be violated while developing it further;
- which extension points are available to host projects.

`django-scroll-to-top` renders exactly one scroll-to-top control. Its single
public site contract is the inclusion tag `{% scroll_to_top %}`; everything
visual or behavioral is resolved from database-backed configuration, never from
template-tag arguments.

![The default circular control injected into the standard Django Admin](../assets/shared/default-button-admin.png)

## Request-to-render flow

```
Django settings (install / infrastructure modes)
  -> resolved DB configuration (per scope: "site" or "admin")
  -> immutable typed renderer payload  (renderer.py — not an ORM object)
  -> Django template + one sanitized SVG + namespaced assets
  -> browser runtime: visibility / scroll / collision / dismissal state machines
```

Configuration is resolved at most once per request (site-specific → global →
safe built-in defaults) and cached per scope. With no database configuration the
control still renders from safe built-in defaults.

## What has been implemented

- **Public site contract** — the inclusion tag `{% scroll_to_top %}` (and
  `{% scroll_to_top scope="admin" %}`) in `templatetags/scroll_to_top.py`. No
  visual template-tag arguments.
- **Data model** (`models.py`) — `ScrollTopProfile` (scope `site`/`admin`,
  optional Sites Framework `site_id`, `is_enabled`; the live revision is derived
  from revision status, not a stored pointer), `ScrollTopRevision` (full
  visual/behavioral snapshot with `draft`/`published`/`archived` status), and
  `ScrollTopUploadedIcon`.
- **Lifecycle services** (`services.py`) — atomic `publish_revision`,
  `create_draft_from_revision`, `rollback_to_revision`, and profile/published
  revision resolution.
- **Per-request resolution and cache** (`site_config.py`) — site-specific then
  global lookup with a per-scope cache generation counter.
- **Single renderer** (`renderer.py`) — returns a typed, serialization-friendly
  `RenderPayload`/`RenderContext` shared by site rendering, admin injection, and
  the admin live preview. Never an ORM object.
- **Standard Django Admin integration** — configuration UX (`admin.py`,
  `forms.py`), live preview (`admin_preview.py`), and footer injection via
  `templates/admin/base_site.html` through normal template resolution (no
  middleware or `AdminSite` monkeypatching).
- **Icon catalog** (`icons/`) — strict XML SVG `sanitizer.py`, `recolor.py`,
  `registry.py` (builtin / developer / uploaded sources), and a vendored Tabler
  subset under `icons/tabler/` (MIT, with `LICENSE.tabler.txt` and `manifest.json`).
- **Strict-CSP styling path** (`styles.py`, `views.py`, `urls.py`) — a versioned
  same-origin stylesheet endpoint that transports validated color and sizing
  values without `unsafe-inline`.
- **Browser runtime** (`static/django_scroll_to_top/`) — `scroll-to-top.{css,js}`
  plus reproducibly minified `*.min.*`, exposing `window.djstt.{init,refresh,destroy}`
  and `djstt:*` DOM events, with an optional `obstacle-adapter.js` for floating
  widgets.
- **System checks and diagnostics** (`checks.py`) — `dstt.W001`–`dstt.W010`,
  plus the `scroll_to_top_diagnose` and `scroll_to_top_check_contrast` management
  commands.
- **Contrast helpers** (`contrast.py`) — advisory only; contrast is reported, not
  enforced.
- **Localization** — English canonical source strings and a bundled Russian
  gettext catalog (`locale/ru/LC_MESSAGES/`).

## Validation on the demo project

A standalone demo Django project lives under `demo/` (a small `library` app with
seeded content and a configured base template). It is used to validate, end to
end:

- adding the app to an already running site;
- a single tag insertion into the base template;
- including the package URLConf for the strict-CSP stylesheet endpoint;
- regression of ordinary pages and the admin panel after configuration changes.

## Test coverage

The `tests/` suite exercises the contracts above across modules including
`test_renderer`, `test_lifecycle`, `test_site_config`, `test_admin_integration`,
`test_admin_preview`, `test_styling`, `test_css_contract`, `test_visibility_scroll`,
`test_collision_contract`, `test_dismissal`, `test_runtime_contract`,
`test_svg_sanitizer`, `test_registry`, `test_security`, `test_accessibility`,
`test_diagnostics`, `test_hooks`, and `test_localization`.

Run the full suite with:

```console
python -m pytest
```

## Feedback and current limitations

This is an early (`0.x` beta) release. The following areas are explicitly
best-effort and benefit from real-world reports via
[GitHub issues](https://github.com/kroxiksut/django-scroll-to-top/issues):

- **Admin integration** — only the standard Django Admin templates are covered by
  the compatibility test matrix. Custom `AdminSite` instances, overridden base
  admin templates, and third-party admin themes are best-effort; report what
  works and what does not.
- **Frontend behavior** — collision avoidance with real floating widgets (cookie
  banners, chat launchers, sticky navigation, toast stacks), placement across
  viewport sizes and safe-area insets, strict-CSP delivery, theme inheritance
  with custom admin themes, and partial-navigation layers (HTMX, Turbo).
- **Accessibility in real browsers** — a full WCAG 2.2 AA audit and zoom
  (200%/400%) verification in real browsers are tracked as later stabilization
  steps (see the root README roadmap).

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for how to file an effective report.

## Related sections

- [Quick start](./quickstart.md)
- [Architecture and package boundaries](../../ARCHITECTURE.md)
- [Translation workflow](../i18n/README.md)
