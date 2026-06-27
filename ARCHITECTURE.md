# Architecture of `django-scroll-to-top`

## Status

This document defines the intended architecture for the pre-alpha package.
Items not yet implemented are contracts to preserve while the roadmap is built
incrementally. The detailed implementation backlog is tracked in the project
planning documentation.

## Package Boundary

The package owns:

- database-backed site/admin presentation and behavior configuration;
- publication and resolution of validated configuration;
- one site template tag and a shared server renderer;
- templates, CSS, JavaScript, built-in icons, and safe custom icon handling;
- standard Django Admin configuration and live preview;
- scroll, visibility, collision, obstacle, and dismissal browser behavior.

The package does not own host-page layout, cookie consent, chat state, legal
policy, analytics, or third-party widget internals. Integrations use generic
markers, selectors, and optional adapters.

## Public Site Contract

```django
{% load scroll_to_top %}
{% scroll_to_top %}
```

The tag resolves one published site configuration, renders one component, and
loads package assets without requiring visual arguments. Repeated calls must not
duplicate IDs or assets. A project may override documented package templates.

## Configuration Layers

1. Django settings enable site/admin capabilities and infrastructure modes.
2. When the Sites Framework is installed, a Site-specific published profile
   overrides the global profile.
3. A global published profile configures one scope.
4. Built-in defaults guarantee safe rendering when no profile exists.

Visual settings are not duplicated in Django settings. Resolution returns an
immutable typed payload, not an ORM object as a public renderer contract.

## Planned Data Model

- `ScrollTopProfile`: scope, optional Site, stable identity, and published
  revision reference.
- `ScrollTopRevision`: snapshot of display, behavior, responsive, collision, and
  dismissal policy. Draft and published revisions are editable in place; editing
  a published revision updates the live configuration. Archived revisions are
  immutable so rollback restores an exact snapshot.
- `ScrollTopIcon`: metadata for uploaded icons and references to sanitized
  normalized payloads; built-in/developer sources share the catalog contract.

Draft/publish/rollback must be transactional. A simpler direct configuration
model may be used for an early internal milestone only if it retains a migration
path to revisions.

## Rendering

The renderer consumes normalized configuration and selects a controlled template
variant and one safe icon. It emits namespaced markup and a useful no-JavaScript
fallback. CSS provides base presentation and placement. External JavaScript adds
thresholds, motion, collision handling, and persistence.

Site, Django Admin, and live preview use the same renderer contract. Preview may
add controls and simulated obstacles around the component but must not maintain a
separate implementation of the button.

## Responsive Contract

Desktop values are primary. Every mobile-capable field explicitly inherits or
overrides its desktop value. The resolved payload contains concrete values;
templates and runtime do not repeatedly reinterpret inheritance.

Both modes support four corners, logical offsets, safe-area insets, bounded
z-index, obstacle spacing, maximum displacement, fallback-corner order, and a
policy for no available placement.

## Browser State

The runtime maintains independent state for:

- threshold/page-length/direction visibility;
- scrolling and user interruption;
- collision geometry and selected placement;
- persistent user dismissal.

Observers trigger bounded recalculation. Scroll events do not perform unthrottled
layout measurement. Runtime state is represented through namespaced classes,
attributes, and CSS custom properties.

## Collision Protocol

Host elements opt in through `[data-scroll-top-obstacle]`; administrators may
add validated selectors. The runtime measures visible bounding rectangles and
applies the configured `ignore`, `shift`, `fallback_corner`, or `hide` policy.

`ResizeObserver` and `MutationObserver` support changing banners and widgets,
with event-based fallbacks. Cross-origin iframe contents are never inspected;
the iframe rectangle may be treated as an obstacle.

## Icon Architecture

One catalog exposes:

- `builtin`: vendored Tabler starter icons with a manifest and license notice;
- `developer`: icons registered by trusted project code;
- `uploaded`: administrator files accepted only after strict sanitization.

Uploaded SVG is parsed as XML. The sanitizer rejects executable/embedded
content, external references, unsafe namespaces, and excessive complexity. Only
the sanitized normalized payload reaches preview or production. Recolorable
icons use `currentColor`; multicolor icons explicitly preserve safe colors.

Licensing metadata is stored independently from technical safety. Sanitization
does not prove a right to use an icon.

## Django Admin Integration

The first release supports and tests the standard Django Admin templates across
the documented Django compatibility matrix. Integration must use documented
template extension points, must not monkeypatch private Django APIs, and should
preserve standard branding.

The standard-admin path uses a small `admin/base_site.html` footer override
selected through normal Django template resolution, not middleware rewriting or
`AdminSite` monkeypatching. The package therefore relies on `django_scroll_to_top`
appearing before `django.contrib.admin` in `INSTALLED_APPS` when admin
integration is enabled.

Custom `AdminSite` instances, overridden base admin templates, and third-party
admin themes are best-effort integrations in the first release. They are not
part of the tested compatibility contract and may require an explicit include
recipe or adapter. Projects should verify them locally and report incompatibilities
so support can be improved collaboratively.

The configuration admin owns forms, icon selection, desktop/mobile inheritance,
contrast validation, preview, publication, copying between scopes, and theme
analysis controls.

## Theme Colors

Colors are configured manually per revision, or inherited from the admin theme.
(The earlier browser-based page color analysis workflow was removed.)

For the standard Django Admin scope, `inherit_admin_theme` prefers publicly
observable admin CSS variables, falls back to a neutral preset when those
variables are absent, and allows third-party admin themes to expose compatible
colors through namespaced `--dstt-admin-*` adapter variables instead of forcing
database copies of framework colors.

## Dismissal

Default anonymous dismissal uses local/session storage and remains functional
when storage is unavailable. Cookie and authenticated database persistence are
optional integrations. Storage keys include profile/site and dismissal version.

Triple-click dismissal is experimental because a normal first click immediately
starts scrolling and can hide the control. It must not be enabled by default or
delay primary behavior without an explicit accepted UX design.

## CSP

The package must support a documented strict-CSP mode without silently requiring
`unsafe-inline`. Administrator-configured colors are part of the MVP and are
transported through a versioned, same-origin CSS endpoint. The endpoint emits
only namespaced CSS custom properties generated from validated configuration
fields; it never accepts or stores arbitrary CSS. The same resolved Site/profile
configuration drives component markup, preview, and generated CSS.

The external stylesheet works without JavaScript and is cacheable by published
configuration version. Installation therefore includes the package URLConf when
site rendering is enabled. A nonce-based script mode may add a context-provided
nonce to the external runtime script without changing stylesheet delivery. The
contract must be verified in real browsers with strict CSP headers.

## Caching

Configuration is resolved at most once per request and may use a shared cache
keyed by scope, Site, and published revision. Publication and rollback invalidate
the relevant keys through the service layer. A cache failure falls back to DB
resolution without changing behavior.

## Extension Points

Planned stable extension points include profile selection, Site resolution,
developer icon registration, obstacle selectors, template overrides, runtime
refresh, and namespaced DOM events. Internal ORM/queryset details are not public
contracts.

## Language and Packaging

English is canonical for code, source strings, architecture, examples, and
primary documentation. Russian is maintained through gettext and parallel docs.
Wheel and sdist include templates, static assets, migrations, typing markers,
locale files, built-in SVG, and third-party licenses.
