# Key invariants

- [Back to documentation index](../README.md)
- [Architecture and package boundaries](../../ARCHITECTURE.md)

These invariants must hold while developing the package. They are the canonical
constraints from `AI_RULES.md`, `ARCHITECTURE.md`, and the core skill reference;
violating one is a regression even if tests still pass.

## Public contract

- One template tag is the entire public site API: `{% scroll_to_top %}` (with an
  optional `scope="admin"`). No visual template-tag arguments.
- The stable public surface is `window.djstt`, the `djstt:*` DOM events, the
  `data-dstt-*` attributes, the `data-scroll-top-obstacle` marker, and the
  `scroll_to_top.html` template. Internal service/model APIs are private.

## Configuration ownership

- Settings enable capabilities (install/infrastructure); database profiles own
  normal presentation and behavior. Never duplicate appearance in settings.
- Site and admin scopes are independent and never resolve through the same
  implicit record.
- Resolution order is site-specific → global → safe built-in defaults.
- Desktop values are primary; each mobile field explicitly inherits or overrides.

## Rendering and lifecycle

- The renderer returns typed, serialization-friendly data, never an ORM object.
- Configuration is resolved at most once per request; rendering never creates
  rows.
- Draft and published revisions are editable in place (editing a published
  revision updates live config and invalidates its scope cache); archived
  revisions are immutable snapshots.
- Publication, rollback, and cache invalidation are service operations.

## Security and isolation

- Production never renders an unsanitized uploaded SVG. Parse as XML, never
  regex-sanitize. Reject DTD/entities/scripts/events/external refs/`foreignObject`.
- Namespace every CSS class, ID, data attribute, and DOM event. Never style
  global elements (`a`, `button`, `svg`, `body`). No CDN, no runtime build step.
- No telemetry by default; never a server-side fetch of an arbitrary URL.
- Strict CSP must not silently require `unsafe-inline`.

## Runtime and migrations

- Keep visibility / collision / scrolling / dismissal as separate state machines.
- Migrations stay deterministic — no network, no live-page or computed-style
  analysis, no deployment-specific files.

## Related sections

- [Architecture and package boundaries](../../ARCHITECTURE.md)
- [Security, SVG sanitization, and CSP](./security-csp.md)
- [Behavior and runtime](./runtime.md)
