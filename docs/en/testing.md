# Testing the package

- [Back to documentation index](../README.md)
- [Type checking (Pyright)](./type-checking.md)

The suite uses `pytest` with `pytest-django`. Tests configure Django themselves
through `tests/settings.py` (`DJANGO_SETTINGS_MODULE=tests.settings`, set in
`pyproject.toml`); there is no `manage.py` in the package repository.

## Running tests

```console
python -m pytest                                     # full suite
python -m pytest tests/test_renderer.py              # one module
python -m pytest tests/test_renderer.py::test_name   # one test
```

Lint and type-check alongside tests:

```console
python -m ruff check src tests
python -m pyright
```

## What the suite covers

The contracts described in this documentation are exercised across modules in
`tests/`, including:

- `test_renderer`, `test_site_config`, `test_lifecycle` — resolution, typed
  payload, and draft/publish/rollback transitions;
- `test_admin_integration`, `test_admin_preview`, `test_uploaded_icon_admin` —
  admin UX, live preview, and attribution;
- `test_styling`, `test_css_contract`, `test_base_fields` — presentation and the
  stylesheet contract;
- `test_visibility_scroll`, `test_collision_contract`, `test_dismissal`,
  `test_runtime_contract`, `test_obstacle_adapter` — runtime state machines and
  the JS/DOM contract;
- `test_svg_sanitizer`, `test_security`, `test_registry` — SVG safety and the
  icon catalog;
- `test_accessibility`, `test_diagnostics`, `test_hooks`, `test_localization`,
  `test_app` — the accessibility floor, system checks, extension hooks, i18n, and
  app wiring.

Test URLConfs `tests/urls.py` and `tests/urls_without_dstt.py` provide positive
and negative fixtures for the URLConf-related system checks.

## Asset and packaging checks

When templates, static assets, SVG, locale, migrations, licenses, or dependencies
change, rebuild the reproducible minified assets and the distribution:

```console
python tools/minify_assets.py        # rebuild *.min.css/js
python -m build                       # sdist + wheel
```

### `tools/minify_assets.py`

This is the project's reproducible asset minifier — a small standard-library
script (no external minifier, no Node, no runtime build step), kept deliberately
simple so its output is byte-stable and reviewable in diffs. It reads the source
assets under `src/django_scroll_to_top/static/django_scroll_to_top/` and rewrites
their minified siblings:

| Source | Minified output |
| --- | --- |
| `scroll-to-top.css` | `scroll-to-top.min.css` |
| `scroll-to-top.js` | `scroll-to-top.min.js` |
| `obstacle-adapter.js` | `obstacle-adapter.min.js` |

Minification is intentionally conservative and deterministic: it trims each line,
drops blank lines (CSS and JS) and full-line `//` comments (JS), and joins the
rest. There are no semantic transforms — the same input always yields the same
output, so a regenerated file only changes when its source did.

Run it whenever you edit a `.css` or `.js` source and commit the regenerated
`*.min.*` files in the **same** change set: the minified files are what ship in
the wheel and are served to browsers.

The script is also a test dependency, so it must not be deleted or moved:
`tests/test_runtime_contract.py` and `tests/test_obstacle_adapter.py` import
`STATIC_DIR`, `_minify_css`, and `_minify_js` from it and assert the committed
`*.min.*` exactly match a fresh minify of the sources. A stale minified asset
therefore fails the suite.

### `tools/smoke_install.py`

The pytest suite runs against `src/` (via `pythonpath`), so it cannot catch
packaging gaps — a template, static asset, locale catalog, or SVG that is missing
from `package-data` still passes every test. `tools/smoke_install.py` closes that
gap by exercising the **installed** wheel: it spins up a minimal in-memory Django
project and checks that the package imports from site-packages (not `src/`), its
migrations apply, the `{% scroll_to_top %}` tag renders for the `site` and `admin`
scopes (packaged SVG icon present, `*.min.*` wired, versioned stylesheet endpoint
reverses), the packaged `admin/base_site.html` override wins template resolution,
and the minified assets ship.

Run it in an environment where the wheel is installed — not in the dev tree:

```console
python -m build
python -m venv /tmp/smoke
/tmp/smoke/bin/python -m pip install dist/django_scroll_to_top-*.whl
/tmp/smoke/bin/python tools/smoke_install.py
```

It exits non-zero on the first failed check. CI runs this automatically in the
`build` job, so a `package-data` regression fails the pipeline on every push.

## Related sections

- [Type checking (Pyright)](./type-checking.md)
- [Diagnostics and management commands](./diagnostics.md)
- [Migration and upgrade notes](./migration.md)
