# Configuration (settings and infrastructure)

- [Back to documentation index](./README.md)
- [Quick start](./quickstart.md)

Django settings own **installation and infrastructure** choices only. Normal
appearance and behavior live in database-backed configuration edited through
Django Admin — see [operations-admin.md](./operations-admin.md) and
[presentation.md](./presentation.md). Never duplicate appearance in settings.

All settings are read from the `DJANGO_SCROLL_TO_TOP` dictionary. Every key is
optional; unknown keys are reported by system check `dstt.W007` without breaking
forward-compatible additions.

## Settings reference

| Key | Type | Default | Purpose |
| --- | --- | --- | --- |
| `SITE_ENABLED` | bool | `True` | Render the control via `{% scroll_to_top %}` on the site. |
| `ADMIN_ENABLED` | bool | `True` | Inject the control into the standard Django Admin. |
| `SITES_FRAMEWORK_ENABLED` | bool | `False` | Opt into per-Site profiles via `django.contrib.sites`. |
| `CSP_MODE` | `"external"` \| `"nonce"` | `"external"` | How the runtime script tag is delivered under CSP. |
| `ADMIN_SHOW_ON_AUTH_PAGES` | bool | `False` | Show the control on admin login / password-reset pages. |
| `DEFAULT_COLLISION_POLICY` | `ignore` \| `shift` \| `fallback_corner` \| `hide` | `"ignore"` | Module default used by revisions whose collision policy is `inherit`. |
| `SITE_ID_RESOLVER` | dotted path or callable | — | `(request) -> int \| None`: resolve the current Site id without the Sites Framework. |
| `PROFILE_RESOLVER` | dotted path or callable | — | `(scope, site_id) -> ScrollTopProfile \| None`: override profile selection; `None` falls back. |
| `OBSTACLE_SELECTORS` | dotted path or callable | — | `() -> list[str]`: merge extra obstacle selectors into every control. |

Invalid values fall back to the documented default rather than raising: an
unsupported `CSP_MODE` falls back to `"external"` (and is reported by
`dstt.W003`); an unsupported `DEFAULT_COLLISION_POLICY` falls back to `"ignore"`
(reported by `dstt.W006`).

## INSTALLED_APPS ordering

When `ADMIN_ENABLED` is true, place `django_scroll_to_top` **before**
`django.contrib.admin` so the package's `admin/base_site.html` footer override is
selected through normal template resolution. System check `dstt.W005` flags the
wrong order.

## URLConf and the stylesheet endpoint

Validated color and sizing values are delivered through a versioned same-origin
stylesheet instead of an inline `style` attribute, so strict CSP never silently
requires `unsafe-inline`. Include the package URLConf to expose it:

```python
path(
    "scroll-to-top/",
    include(
        ("django_scroll_to_top.urls", "django_scroll_to_top"),
        namespace="django_scroll_to_top",
    ),
)
```

This registers the route `django_scroll_to_top:site-stylesheet`
(`styles/<version>.css`). System check `dstt.W004` warns when the URLConf is
missing while site rendering is enabled.

## Content Security Policy

- **`external`** (default) — the runtime is delivered with same-origin `<link>`
  and `<script>` tags. Works with a strict policy such as
  `default-src 'self'; style-src 'self'; script-src 'self';`.
- **`nonce`** — set `CSP_MODE = "nonce"` and provide a nonce through the template
  context (`csp_nonce`) or `request.csp_nonce`. The package adds that nonce to its
  external script tag while keeping styles on the same-origin stylesheet endpoint.

## Sites Framework

With `SITES_FRAMEWORK_ENABLED = True` (and `django.contrib.sites` installed), a
scope may have a Site-specific profile resolved before the global profile. The
package also works without the Sites Framework: profiles store `site_id` as a
plain integer, and `SITE_ID_RESOLVER` can supply the current Site id. System
check `dstt.W009` warns if the flag is set without the framework installed.

## Extension hooks

Hooks accept a dotted path or a callable. A faulty hook never breaks rendering —
exceptions and import errors fall back to built-in behavior:

- `SITE_ID_RESOLVER(request) -> int | None`
- `PROFILE_RESOLVER(scope, site_id) -> ScrollTopProfile | None`
- `OBSTACLE_SELECTORS() -> list[str]`

Developer icons are registered separately from settings via the icon registry
(`register_developer_icon(...)`); see [presentation.md](./presentation.md).

## Related sections

- [Admin: profiles, revisions, publish and rollback](./operations-admin.md)
- [Presentation: templates, colors, sizing, and icons](./presentation.md)
- [Security, SVG sanitization, and CSP](./security-csp.md)
- [Diagnostics and management commands](./diagnostics.md)
