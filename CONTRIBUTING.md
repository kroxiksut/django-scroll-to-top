# Contributing

Thanks for your interest in improving `django-scroll-to-top`.

## Reporting issues and proposing changes

- **Bugs and features:** open a GitHub issue with a clear description; for bugs,
  include a minimal reproduction and your Django and Python versions.
- **Security vulnerabilities:** do not open a public issue — follow
  [SECURITY.md](./SECURITY.md).
- **Pull requests:** keep them focused, describe the change, add tests for
  behavior changes, update the documentation, and add an entry under
  `## [Unreleased]` in [CHANGELOG.md](./CHANGELOG.md). Make sure lint, type
  checks, and tests pass.
- By participating you agree to the [Code of Conduct](./CODE_OF_CONDUCT.md).

## Development setup

```bash
python -m pip install -e ".[test,dev]"
python -m ruff check src tests
python -m pyright
python -m pytest
```

### JavaScript linting

The browser assets are linted with ESLint. Node is a dev-only tool — it is not a
runtime or packaged dependency.

```bash
npm ci           # one-time, installs ESLint + TypeScript into node_modules/ (git-ignored)
npm run lint     # lints the static JS (generated *.min.js are ignored)
npm run typecheck  # validates the public *.d.ts contract with tsc --noEmit
npm run check    # both of the above
```

`scroll-to-top.d.ts` / `obstacle-adapter.d.ts` declare the public JS contract
(`window.djstt`, `window.djsttObstacleAdapter`, and the `djstt:*` events). Keep
them in sync when you change that surface; `npm run typecheck` only checks the
declarations, not the ES5 implementation.

When you change `scroll-to-top.js` or `obstacle-adapter.js`, regenerate the
minified assets with `python tools/minify_assets.py` in the same change set.

Read `AGENTS.md` and `ARCHITECTURE.md` before changing public behavior. Keep
changes focused and add tests with behavior changes.

Author code, source strings, examples, and canonical documentation in English.
Wrap user-facing strings in Django i18n immediately. Then update the Russian
`.po` translation and compile `.mo` in the same completed change set. Update
English documentation first and synchronize its Russian translation.

Russian version: [CONTRIBUTING.ru.md](./CONTRIBUTING.ru.md).
