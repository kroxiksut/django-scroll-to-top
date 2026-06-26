# AI Integration Guides: django-scroll-to-top

This folder contains AI-facing integration instructions for
`django-scroll-to-top` — concise, imperative guidance written for an AI coding
agent that is wiring the package into a **downstream Django project**.

These documents are intentionally **English-only** to keep prompts, keywords, and
integration contracts consistent for AI tooling. The human documentation is
bilingual ([English](../README.md) / [Russian](../README.ru.md)); these guides
are not translated.

## How to connect these to a modern AI

These are plain Markdown files, so any current AI assistant can consume them.
Pick whichever path fits your tool:

- **Claude Code / Codex / other terminal agents** — point the agent at this
  folder: *"Read `docs/ai/` before integrating django-scroll-to-top."* Or copy
  the relevant guide into your repo and reference it from your project's
  `AGENTS.md` / `CLAUDE.md`.
- **Cursor / Windsurf / Copilot (IDE agents)** — add a rule in
  `.cursor/rules` / `.windsurfrules` / `.github/copilot-instructions.md` such as
  *"When touching the scroll-to-top control, follow `docs/ai/*.md`."* Keep the
  files in the workspace so the agent can open them on demand.
- **Chat assistants (Claude.ai, ChatGPT, Gemini)** — paste the specific guide
  (for example [integration.md](./integration.md)) into the conversation as
  context, then ask for the change. Each guide is short enough to fit in one
  prompt.
- **Retrieval / RAG setups** — index this folder. The guides are self-contained
  and cross-linked, so a single retrieved file is usually enough for one task.

For a downstream project, the simplest durable setup is to add one line to your
own `AGENTS.md`/`CLAUDE.md`:

```text
For the scroll-to-top control, follow the package guides in
docs/ai/ (or the installed package's documentation). Do not pass visual options
as template-tag arguments; configure appearance in the Django admin.
```

These guides are **opt-in context, not auto-loaded directives.** They never
override your project's own `AGENTS.md`/`CLAUDE.md` — they describe how to use
the package correctly.

## Hard rules an agent must not break

- One public site tag, `{% scroll_to_top %}` — **no visual template-tag
  arguments**. Appearance lives in the Django admin (database config), never in
  Django settings.
- Settings (`DJANGO_SCROLL_TO_TOP`) own **install/infrastructure only**.
- Production never renders an unsanitized uploaded SVG. Never bypass the
  sanitizer; never regex-sanitize SVG.
- Namespace everything (`dstt` / `djstt`); never style global elements
  (`a`, `button`, `svg`, `body`). No CDN, no runtime build step.
- Strict CSP must not require `unsafe-inline`. No telemetry; never fetch an
  arbitrary URL server-side.

The full list is in [invariants](../en/invariants.md).

## Type-checking policy for AI-driven changes

Use `pyright` as the primary static type checker. Run `python -m pyright` and
keep it clean; keep any suppressions local and explicit (no global ignore
switches). See [type-checking](../en/type-checking.md).

## Documents

- [integration.md](./integration.md) — install, enable, wire URLs, render the tag.
- [presentation.md](./presentation.md) — change appearance and behavior safely (admin DB config).
- [runtime.md](./runtime.md) — the browser runtime, `window.djstt`, DOM events, and SPA hooks.
- [icons.md](./icons.md) — built-in, developer, and uploaded icons; SVG safety and attribution.

## See also

- Human docs: [English](../README.md) · [Russian](../README.ru.md)
- [Architecture and package boundaries](../../ARCHITECTURE.md)
