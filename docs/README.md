# Documentation: django-scroll-to-top

[Русская версия](./README.ru.md)

`django-scroll-to-top` is a reusable Django application that renders one
accessible, configurable scroll-to-top control on application pages and in the
standard Django Admin. Appearance and behavior are stored in database-backed
configuration and edited through Django Admin; Django settings own only
installation and infrastructure choices.

![The default scroll-to-top control on the demo site](./assets/shared/default-button-demo-site.png)

> **Pre-release status.** The package code, data model, admin, runtime, and test
> suite are implemented in this repository, but the distribution is not published
> on PyPI yet. Installation commands describe the intended stable contract and
> may change before the first public release.

## Navigation

- [Project overview (root README)](../README.md)
- [Architecture and package boundaries](../ARCHITECTURE.md)
- [Repository structure](../STRUCTURE.md)

## Basic documents

- [Quick start](./en/quickstart.md) — from install to a rendered control.
- [Overview and current status](./en/overview.md) — what is implemented and validated.
- [Key invariants](./en/invariants.md) — constraints that must not be violated.
- [Configuration (settings and infrastructure)](./en/configuration.md) — the `DJANGO_SCROLL_TO_TOP` reference, CSP modes, and hooks.
- [Admin: profiles, revisions, publish and rollback](./en/operations-admin.md) — the configuration lifecycle.
- [Presentation: templates, colors, sizing, and icons](./en/presentation.md) — every visual field.
- [Behavior and runtime](./en/runtime.md) — visibility, scrolling, collision, dismissal, the JS API, and DOM events.
- [Accessibility](./en/accessibility.md) — the WCAG 2.2 AA contract and contrast policy.
- [Security, SVG sanitization, and CSP](./en/security-csp.md) — the SVG sanitizer and CSP guarantees.
- [Diagnostics and management commands](./en/diagnostics.md) — system checks and CLI tooling.
- [Testing the package](./en/testing.md) — pytest, lint, and type checks.
- [Type checking (Pyright)](./en/type-checking.md) — the typed contract.
- [Migration and upgrade notes](./en/migration.md) — applying migrations and upgrading.
- [Demo project](./en/demo.md) — the standalone demo Django project.

## Integration notes

- [Collision integration with django-cookies-152fz](./integration/django-cookies-152fz.md) — a worked example of avoiding a cookie banner.

## AI integration guides

English-only, agent-facing instructions for wiring the package into a downstream
project live in [docs/ai/](./ai/README.md).

**Connecting them to a modern AI:** they are plain Markdown. Point a terminal
agent (Claude Code, Codex) at `docs/ai/`, reference them from your project's
`AGENTS.md` / `CLAUDE.md` / `.cursor/rules`, or paste a single guide into a chat
assistant (Claude.ai, ChatGPT, Gemini) as context. See the
["How to connect"](./ai/README.md#how-to-connect-these-to-a-modern-ai) section
for per-tool steps.

## Localization

- [Translation workflow](./i18n/README.md)

## Contributing

- [Contributing (EN)](../CONTRIBUTING.md)
- [Участие в разработке (RU)](../CONTRIBUTING.ru.md)

## Security

- [Security policy and vulnerability reporting](../SECURITY.md)

## License

The package is licensed under MIT. See [LICENSE](../LICENSE). The vendored
Tabler icon subset retains its own MIT notice; see
[THIRD_PARTY_LICENSES.md](../THIRD_PARTY_LICENSES.md).
