# Runtime Guide (AI)

## Scope

Use this guide to integrate with the browser runtime — single-page apps, fragment
navigation, floating-widget collisions, and DOM-event hooks. The runtime is
vanilla ES5; do not add a build step.

## Public API: `window.djstt`

| Method | Use when |
| --- | --- |
| `init(root?)` | A new control was injected (e.g. HTMX fragment). Idempotent. |
| `refresh(root?)` | Layout/obstacles changed; re-measure (e.g. after Turbo nav). |
| `destroy(root?)` | Removing a subtree; tear down listeners/observers. |
| `dismiss(root?)` / `restore(root?)` | Programmatic dismissal honoring storage. |
| `debug(enabled, root?)` | Toggle collision debug overlays. |

Contract `version` is `"1"`. Do not depend on internal payloads, private DOM
structure, or non-`djstt` globals.

## DOM events (bubble from `.dstt-control-wrap`)

- `djstt:show` / `djstt:hide` — `{ visible }`
- `djstt:scroll-start` / `djstt:scroll-end` — `{ top }`
- `djstt:dismiss` — `{ dismissed, storage }`
- `djstt:restore` — `{ dismissed }`

Observe on the element, `document`, or `window`. Keep this contract stable for
downstream hooks.

## Markup hooks

- `data-scroll-top="disabled"` on `<body>` — page-level opt-out.
- `data-scroll-top-obstacle` on a floating element — mark it as a collision
  obstacle (optionally `-gap` / `-priority`).
- `data-dstt-*` on the control wrapper — read-only state attributes.

## Collision & obstacle adapter

The runtime measures visible obstacle rectangles and applies the revision's
collision policy. For widgets that are hard to target with one selector, load the
optional `obstacle-adapter.js` (never a dependency) and call
`window.djsttObstacleAdapter.register({ selectors, gap, priority, events })`. It
tags matching markup and bridges open/close/collapse events to
`window.djstt.refresh()`. Presets: `djangoCookies152fz`, `stickyBottomNavigation`.

## Guardrails

- Keep visibility / scrolling / collision / dismissal as **separate state
  machines**; don't merge them.
- Reduced-motion always gets an instant jump regardless of `scroll_behavior`.
- Cross-origin iframe contents are never inspected; tagging an `<iframe>` treats
  its own rectangle as the obstacle.
- Storage access must tolerate denied/unavailable storage without breaking the
  scroll action.

## Reference

- [Behavior and runtime](../en/runtime.md) · [Demo project](../en/demo.md)
- Typed contracts: `scroll-to-top.d.ts`, `obstacle-adapter.d.ts`.
