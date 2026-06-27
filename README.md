<p align="center">
  <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/django-scroll-to-top-logo.png" alt="django-scroll-to-top logo" width="180">
</p>

<h1 align="center">django-scroll-to-top</h1>

<p align="center">
  Accessible, configurable scroll-to-top control for Django sites and the Django Admin.
</p>

<p align="center">
  <a href="https://pypi.org/project/django-scroll-to-top/"><img src="https://img.shields.io/pypi/v/django-scroll-to-top.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/django-scroll-to-top/"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg" alt="Python versions"></a>
  <a href="https://www.djangoproject.com/"><img src="https://img.shields.io/badge/Django-4.2%20LTS%20%7C%205.x%20%7C%206.0-092E20.svg?logo=django&logoColor=white" alt="Django versions"></a>
</p>

<p align="center">
  <a href="https://github.com/kroxiksut/django-scroll-to-top/actions/workflows/ci.yml"><img src="https://github.com/kroxiksut/django-scroll-to-top/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Linted with Ruff"></a>
  <a href="https://microsoft.github.io/pyright/"><img src="https://microsoft.github.io/pyright/img/pyright_badge.svg" alt="Checked with pyright"></a>
</p>

<p align="center">
  <b>English</b> · <a href="README.ru.md">Русский</a>
</p>

> **Beta (`0.x`).** The package is feature-complete, tested, and builds clean
> distributions. While the version stays in the `0.x` series the public API may
> still change between minor releases before `1.0.0`.

`django-scroll-to-top` is a reusable Django application that adds an accessible,
configurable scroll-to-top control to application pages and the standard Django
Admin.

The developer experience is deliberately small:

1. Install the package and add its Django app.
2. Run migrations.
3. Add one template tag to the base site template.
4. Configure appearance and behavior through Django Admin.

No jQuery, external CDN, frontend framework, or mandatory frontend build step is
required.

## Why This Package

A basic scroll-to-top link is easy to write. A reusable production component
also needs to handle:

- separate desktop and mobile presentation;
- keyboard navigation, focus, contrast, and reduced motion;
- standard Django Admin integration;
- safe custom SVG icons;
- light and dark themes;
- cookie banners, chats, sticky navigation, and other fixed elements;
- user dismissal without breaking the primary scroll action;
- strict Content Security Policy deployments;
- caching, localization, packaging, and upgrade compatibility.

This package provides those behaviors while keeping page-template changes
minimal.

## Features

- One template tag for public site integration.
- Independent site and standard Django Admin configurations.
- Database-backed configuration managed through Django Admin.
- Draft, publish, rollback, and configuration-copy workflows.
- Explicit desktop values and per-field mobile inheritance/overrides.
- Top-left, top-right, bottom-left, and bottom-right placement.
- Circle, square, rounded-square, pill, and icon-with-label templates.
- Solid, outline, soft, ghost, glass, and controlled gradient variants.
- Configurable colors, borders, shadows, focus rings, spacing, and sizing.
- Built-in light/dark presets and theme inheritance.
- Live desktop/mobile preview using the production renderer.
- Built-in Tabler starter icons plus developer and administrator icon sources.
- Safe SVG upload, sanitization, preview, recoloring, and license metadata.
- Scroll thresholds, short-page detection, fixed-header offsets, and optional
  target selectors.
- Native smooth scrolling with `prefers-reduced-motion` support.
- Collision avoidance for banners, launchers, chats, toast containers, sticky
  navigation, and other floating controls.
- Local/session user dismissal with expiration, reset versions, and restore UX.
- Django i18n with English canonical strings and Russian as the first bundled
  translation.

## Installation

```console
python -m pip install django-scroll-to-top
python manage.py migrate
```

Add the application and enable the required integration scopes:

```python
INSTALLED_APPS = [
    # ...
    "django_scroll_to_top",
]

DJANGO_SCROLL_TO_TOP = {
    "SITE_ENABLED": True,
    "ADMIN_ENABLED": True,
}
```

Include the package URLConf so the public template tag can load its versioned
same-origin stylesheet endpoint in strict-CSP deployments:

```python
from django.urls import include, path

urlpatterns = [
    # ...
    path(
        "scroll-to-top/",
        include(
            ("django_scroll_to_top.urls", "django_scroll_to_top"),
            namespace="django_scroll_to_top",
        ),
    ),
]
```

The package supports and tests the standard Django Admin templates on the
documented Django compatibility matrix. The integration uses documented Django
extension points, preserves standard branding, and avoids monkeypatching private
Django APIs.

When `DJANGO_SCROLL_TO_TOP["ADMIN_ENABLED"]` is true, place
`"django_scroll_to_top"` before `"django.contrib.admin"` in `INSTALLED_APPS`
so the package's `admin/base_site.html` footer override is selected through the
normal Django template resolution rules.

Custom `AdminSite` instances, overridden base admin templates, and third-party
admin themes are best-effort integrations and are not yet covered by the
compatibility test matrix. Projects using them should verify the integration
locally and report incompatibilities so they can be investigated and fixed
collaboratively.

No separate admin-integration app is required for the current standard-admin
footer injection. If a future integration app becomes necessary, it should use
its own app label instead of overloading the main package label.

### Custom AdminSite Recipe

If a project overrides `admin/base_site.html` or uses a custom `AdminSite`
template tree, keep the normal branding blocks and add the package tag in the
footer block:

```django
{% extends "admin/base.html" %}
{% load i18n scroll_to_top %}

{% block branding %}
  {{ block.super }}
{% endblock %}

{% block footer %}
  {{ block.super }}
  {% scroll_to_top scope="admin" %}
{% endblock %}
```

The default admin policy hides the control on anonymous auth pages such as the
login and password-reset screens. Set
`DJANGO_SCROLL_TO_TOP["ADMIN_SHOW_ON_AUTH_PAGES"] = True` to opt into showing it
there as well.

## Template Usage

Add one tag near the end of the shared base template:

```django
{% load scroll_to_top %}

<!-- Page content -->

{% scroll_to_top %}
```

The tag resolves the published site configuration, renders the selected safe
icon and controlled template variant, and loads package assets. Ordinary visual
options are not passed as template-tag arguments. Dynamic color and sizing
variables are delivered through a versioned same-origin stylesheet rather than
an inline `style` attribute, so the one-tag contract remains intact without
silently requiring `unsafe-inline`.

Projects can override documented package templates through standard Django
template loaders.

## Configuration Model

Django settings own installation and infrastructure choices only. Normal
appearance and behavior are stored in database-backed configuration and edited
through Django Admin.

Configuration scopes:

| Scope | Purpose |
| --- | --- |
| `site` | Public and application pages using the template tag |
| `admin` | Standard Django Admin pages |

Django Sites integration is included. When `django.contrib.sites` is installed,
the current Site may have a Site-specific profile with a global fallback. The
package also remains usable without the Sites Framework. Site and admin
configurations remain independent but can be copied explicitly.

Desktop values are primary. Each mobile-capable field explicitly inherits its
desktop value or stores an override. The admin form shows this relationship
instead of hiding inheritance behind empty values.

### Visibility and Scrolling

Each revision configures when the control appears and where it scrolls:

- visibility threshold mode (`pixels`, `viewport`, or `combined`) with
  `show_after_px`, `show_after_viewports`, and a `min_document_height_px` floor
  so short pages never show the control;
- show/hide delays and a visibility direction (`always`, `scroll_up_only`, or
  `hide_on_scroll_down`);
- a page-level opt-out via a `data-scroll-top="disabled"` attribute on `<body>`;
- an optional scroll target selector with a vertical offset and an optional
  fixed-header selector whose height is subtracted, falling back to the top of
  the document when empty or not found;
- `smooth` or `instant` scrolling (reduced-motion users always get an instant
  jump), using native `window.scrollTo` without a custom animation loop.

### Visual Templates and Styling

Appearance is built from controlled package CSS classes, never arbitrary
templates stored in the database:

- shapes: `circle`, `square`, `rounded-square`, and `pill`;
- fill variants: `solid`, `outline`, `soft`, `ghost`, `glass` (translucent with
  a backdrop-blur fallback), and `gradient` (two configured colors and an angle);
- shadow presets (`none`/`small`/`medium`/`large`), opacity, border width,
  focus-ring width/offset, and a backdrop-blur amount for the glass variant.

The six fill variants, shown on the default circle shape:

| Fill | Preview | Description |
| --- | :---: | --- |
| `solid` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-solid.png" alt="Solid fill" width="96"> | Opaque background |
| `outline` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-outline.png" alt="Outline fill" width="96"> | Border only, no fill |
| `soft` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-soft.png" alt="Soft fill" width="96"> | Soft translucent background |
| `ghost` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-ghost.png" alt="Ghost fill" width="96"> | Transparent; background appears on hover |
| `glass` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-glass.png" alt="Glass fill" width="96"> | Glassy: translucent with a backdrop blur |
| `gradient` | <img src="https://raw.githubusercontent.com/kroxiksut/django-scroll-to-top/main/docs/assets/shared/7.2-fill-gradient.png" alt="Gradient fill" width="96"> | Gradient between two configured colors |

Unknown shapes, fills, or shadows fall back to safe defaults, forced-colors mode
neutralizes every variant, and projects can still override the package template
through standard Django template resolution.

## Placement and Floating-Element Collisions

Both desktop and mobile modes support all four viewport corners, independent
offsets, safe-area insets, bounded `z-index`, obstacle spacing, and
fallback-corner order.

Host elements can declare themselves as obstacles:

```html
<div data-scroll-top-obstacle>
  <!-- Cookie banner, chat launcher, sticky action, and so on -->
</div>
```

Administrators may also configure validated CSS selectors. The browser runtime
measures visible rectangles and applies one of these policies:

- ignore obstacles;
- shift along the selected edge;
- try configured fallback corners;
- hide the control when no safe placement exists.

Cookie and chat packages remain optional. They do not become dependencies of
`django-scroll-to-top`.

### Optional Obstacle Adapter

For cookie banners and other floating widgets that are not easy to target with a
single static selector, an optional adapter ships at
`django_scroll_to_top/obstacle-adapter.js`. It is never loaded by the
`{% scroll_to_top %}` tag; include it only where you need it:

```html
<script src="{% static 'django_scroll_to_top/obstacle-adapter.min.js' %}" defer></script>
<script>
  document.addEventListener("DOMContentLoaded", function () {
    // Generic registration: tag selectors and recalculate on widget events.
    window.djsttObstacleAdapter.register({
      selectors: [".chat-widget", ".sticky-bottom-nav", ".toast-stack"],
      gap: 12,
      priority: 5,
      events: ["my-widget:open", "my-widget:close"]
    });

    // Or reuse the bundled django-cookies-152fz preset (panel + launcher).
    window.djsttObstacleAdapter.register(
      window.djsttObstacleAdapter.presets.djangoCookies152fz
    );
  });
</script>
```

The adapter tags matching markup with `data-scroll-top-obstacle` (including
elements inserted later, such as a compact launcher that appears after the
banner closes), and bridges the configured open/close/collapse events to
`window.djstt.refresh()`. The cookie banner panel and its compact launcher are
listed as separate selectors so each is measured on its own bounding rectangle
while visible. Cross-origin iframe contents are never inspected; tagging an
`<iframe>` makes the engine treat the iframe rectangle itself as an obstacle.

Collision avoidance and theme-aware enhancements are progressive enhancement
behaviors. The no-JavaScript baseline remains a plain top-of-document link in
the configured corner with the conservative built-in preset.

## Icons

The unified icon catalog has three sources:

- `builtin`: vendored Tabler starter icons;
- `developer`: icons registered by trusted project code;
- `uploaded`: SVG files uploaded and approved through Django Admin.

Built-in examples include suitable arrow, chevron, caret, circle, badge,
bar, and square variants from [Tabler Icons](https://tabler.io/icons).

### Icon Color Requirements

The button reads its colors from the database configuration. For an icon to pick
up the configured color, its SVG must paint with `currentColor` rather than a
hard-coded color — that is, use `fill="currentColor"` (filled icons) or
`stroke="currentColor"` (outline icons). The control then applies, in priority
order:

1. **Icon color override** (`icon_color` / `dark_icon_color`) when set;
2. otherwise the **foreground color** (`foreground_color`), which is also the
   label color.

Multicolor/original uploaded icons keep their own colors and ignore these
fields (they do not use `currentColor`). Built-in Tabler icons already use
`currentColor`, so they recolor automatically.

Tabler Icons are distributed under the
[MIT License](https://github.com/tabler/tabler-icons/blob/main/LICENSE). That
license permits broad use, modification, and redistribution, including
commercial use, while requiring preservation of its copyright and license
notice. Release artifacts include the required notice and source/version
metadata.

### Uploaded SVG Safety

Administrator-uploaded SVG is not rendered directly. The pipeline:

- parses SVG as XML;
- rejects DTD, entities, scripts, event handlers, external resources, embedded
  documents, unsafe namespaces, and excessive complexity;
- allows only documented graphical elements and attributes;
- normalizes geometry and `viewBox` data;
- stores and renders only a sanitized payload;
- supports `currentColor` recoloring for compatible icons;
- preserves safe original colors only in an explicit multicolor mode.

Technical sanitization does not grant a right to use an icon. Uploaded icons
carry author, source, license, copyright, and attribution metadata, plus an
administrator confirmation that the project may use and distribute the file.

The package does not treat an uploaded SVG as free or open content merely
because the file was accepted by the sanitizer. The site operator remains
responsible for confirming usage and redistribution rights, keeping attribution
data accurate, and exporting icon-attribution records when the deployment needs
them.

## Themes and Colors

Administrator-configured colors are delivered through a versioned same-origin
stylesheet generated by the package, without storing arbitrary CSS or requiring
`unsafe-inline`. The stylesheet uses the same resolved Site/profile
configuration as the component renderer and remains effective without
JavaScript.

Manual and inherited color modes are supported. Standard Django Admin
configuration can inherit supported admin theme variables and react to
light/dark changes with safe fallbacks. The built-in `inherit_admin_theme`
mode prefers publicly observable Django Admin variables, falls back to a neutral
preset when they are absent, and also exposes namespaced `--dstt-admin-*`
adapter hooks for third-party admin themes.

Colors are otherwise configured manually per revision. (The earlier
browser-based page color analysis workflow was removed as unnecessary.)

## User Dismissal

Persistent user dismissal is separate from temporary runtime visibility and from
the administrative enable flag. Each revision configures dismissal:

- `allow_user_dismissal` renders a visible close control;
- the storage mechanism is `local`, `session`, a functional `cookie`, or `none`
  (in-memory only). The default `local` mode stores nothing until the visitor
  actually dismisses the control;
- the duration is either `persistent` (kept until the revision's configuration
  token or `dismissal_version` changes) or day-based via `dismissal_days`, which
  self-clears once it lapses;
- `dismissal_requires_confirmation` asks the visitor to confirm before hiding;
- `dismissal_version` is an explicit knob to intentionally re-show the control.

Storage keys are namespaced by scope, site, configuration token, and dismissal
version, and all storage access tolerates denied or unavailable storage without
breaking the scroll action. The control can be restored programmatically with
`window.djstt.restore()`. Triple-click dismissal remains experimental because
the first normal click starts scrolling and may hide the control immediately; it
is not enabled by default.

## Accessibility

The component targets WCAG 2.2 AA within its scope:

- accessible name independent of icon or tooltip;
- keyboard operation and visible focus;
- appropriate pointer target size;
- contrast validation for normal, hover, active, and focus states;
- `prefers-reduced-motion` support;
- forced-colors/high-contrast behavior;
- zoom and RTL support;
- no keyboard trap or unexpected focus movement;
- decorative SVG hidden from accessibility APIs.

The structural contract above is implemented and covered by tests: a translatable
accessible name on both the control and the close control, a minimum 24x24 CSS px
target floor, a no-JavaScript link fallback, no positive tabindex, visible
focus-visible outlines, forced-colors and reduced-motion handling, and RTL-safe
logical properties. A full WCAG 2.2 AA audit and zoom (200%/400%) verification in
real browsers are tracked as later stabilization steps (see [Roadmap](#roadmap)).

## Security, Privacy, and CSP

- No arbitrary HTML, JavaScript, or CSS is stored through admin forms.
- Production never renders an unsanitized original SVG upload.
- No telemetry or external network calls are enabled by default.
- Strict CSP support does not silently require `unsafe-inline`.
- Browser storage failures degrade safely.
- Cookie-based or authenticated database dismissal is optional and documented
  separately if enabled.

See [SECURITY.md](SECURITY.md) for the supported versions and how to report a
vulnerability.

### Minimal CSP Configuration

The default `DJANGO_SCROLL_TO_TOP["CSP_MODE"]` is `"external"`. In that mode,
the component uses same-origin `<link>` and `<script>` tags and works with a
policy such as:

```text
Content-Security-Policy:
  default-src 'self';
  style-src 'self';
  script-src 'self';
```

If the host project uses nonce-based script delivery, set
`DJANGO_SCROLL_TO_TOP["CSP_MODE"] = "nonce"` and provide `csp_nonce` in the
template context or `request.csp_nonce`. The package adds that nonce to its
external script tag while keeping style delivery on the same-origin stylesheet
endpoint.

## Runtime Events

The browser runtime uses one documented global entrypoint, `window.djstt`, with
`init(root?)`, `refresh(root?)`, and `destroy(root?)` helpers for progressive
enhancement and partial-navigation integrations.

The runtime dispatches these namespaced DOM events from each component root:

- `djstt:show`
- `djstt:hide`
- `djstt:scroll-start`
- `djstt:scroll-end`
- `djstt:dismiss`

HTMX-like fragment replacement may call `window.djstt.init(fragmentRoot)`. Turbo
and similar full-page navigation layers may call `window.djstt.refresh()`.

## Extension Points

Optional hooks are configured in `DJANGO_SCROLL_TO_TOP` as a dotted path or a
callable, and a faulty hook never breaks rendering:

- `SITE_ID_RESOLVER(request) -> int | None` — resolve the current Site id without
  depending on `django.contrib.sites`;
- `PROFILE_RESOLVER(scope, site_id) -> ScrollTopProfile | None` — override
  profile/revision selection; return `None` to fall back to built-in resolution;
- `OBSTACLE_SELECTORS() -> list[str]` — merge extra obstacle selectors into every
  rendered control.

Developer icons are registered through `register_developer_icon(...)`. The
stable public surface is `window.djstt` (`init`/`refresh`/`destroy`, `version`,
`dismiss`/`restore`/`debug`), the namespaced `djstt:*` DOM events, the
`data-dstt-*` attributes on the control wrapper, the `data-scroll-top-obstacle`
marker, and the `django_scroll_to_top/scroll_to_top.html` template. Internal
service and model APIs are not part of the public contract.

## Diagnostics

System checks report common misconfigurations with stable ids and actionable
hints:

- `dstt.W001`/`W002`: migrations cannot be inspected, or are unapplied.
- `dstt.W003`: unsupported `CSP_MODE`.
- `dstt.W004`: package URLConf is missing while site rendering is enabled.
- `dstt.W005`: `django_scroll_to_top` is ordered after `django.contrib.admin`.
- `dstt.W006`: unsupported `DEFAULT_COLLISION_POLICY`.
- `dstt.W007`: `DJANGO_SCROLL_TO_TOP` is not a dict or has unknown keys.
- `dstt.W008`: `ADMIN_ENABLED` is set but `django.contrib.admin` is not installed.
- `dstt.W009`: `SITES_FRAMEWORK_ENABLED` is set but `django.contrib.sites` is not
  installed.
- `dstt.W010`: packaged templates or minified static assets are missing.

Two management commands help diagnose a deployment:

```console
python manage.py scroll_to_top_diagnose        # resolved config per scope, no secrets
python manage.py scroll_to_top_check_contrast  # non-zero exit if a published revision fails
```

## Asset Build

Release assets are minified reproducibly with:

```console
python tools/minify_assets.py
```

## Compatibility

The support matrix covers Django 4.2 LTS, 5.x, and 6.x with the Python versions
supported by each selected Django release. Django 4 support is scoped to 4.2 LTS
rather than the entire 4.x line. The matrix is defined in `pyproject.toml` and
verified in CI (`tox.ini` mirrors it).

The base runtime dependency set is limited to Django.

## Feedback

This is an early (`0.x` beta) release, and real-world reports are especially
valuable. Bug reports and feedback are welcome via
[GitHub issues](https://github.com/kroxiksut/django-scroll-to-top/issues),
particularly on:

- **Admin integration** — the package is tested against the standard Django
  Admin templates. Custom `AdminSite` instances, overridden base admin
  templates, and third-party admin themes are best-effort and not yet in the
  compatibility test matrix; please report what works and what does not.
- **Frontend behavior** — collision avoidance with real cookie banners, chat
  launchers, sticky navigation, and toast stacks; placement across viewport
  sizes and safe-area insets; behavior under strict CSP; theme inheritance with
  custom admin themes; and partial-navigation layers such as HTMX and Turbo.
- **Accessibility in real browsers** — keyboard, focus, contrast, forced-colors,
  reduced motion, RTL, and zoom (200%/400%); see the [Roadmap](#roadmap) for the
  audits still in progress.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to file an effective report.

## Roadmap

Tracked for after the initial release:

- Full WCAG 2.2 AA audit and zoom (200%/400%) verification in real browsers.
- Optional authenticated database-backed dismissal endpoint.

## Project Documentation

- [Changelog](CHANGELOG.md)
- [Architecture](ARCHITECTURE.md)
- [Contributor guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Code of conduct](CODE_OF_CONDUCT.md)
- [Repository structure](STRUCTURE.md)

## License

The package is licensed under MIT. See [LICENSE](LICENSE).

Third-party assets retain their own licenses. The vendored Tabler subset and
its upstream MIT notice are documented in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
