# Testing the package

- [Back to documentation index](./README.md)
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

## Related sections

- [Type checking (Pyright)](./type-checking.md)
- [Diagnostics and management commands](./diagnostics.md)
- [Migration and upgrade notes](./migration.md)
