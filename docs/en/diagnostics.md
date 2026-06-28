# Diagnostics and management commands

- [Back to documentation index](../README.md)
- [Configuration (settings and infrastructure)](./configuration.md)

## System checks

The package registers Django system checks (`checks.py`) with stable ids and
actionable hints. They run with `python manage.py check` and during normal
startup:

| Id | Reports |
| --- | --- |
| `dstt.W001` | Migrations cannot be inspected. |
| `dstt.W002` | Migrations are unapplied. |
| `dstt.W003` | Unsupported `CSP_MODE`. |
| `dstt.W004` | Package URLConf is missing while site rendering is enabled. |
| `dstt.W005` | `django_scroll_to_top` is ordered after `django.contrib.admin`. |
| `dstt.W006` | Unsupported `DEFAULT_COLLISION_POLICY`. |
| `dstt.W007` | `DJANGO_SCROLL_TO_TOP` is not a dict or has unknown keys. |
| `dstt.W008` | `ADMIN_ENABLED` is set but `django.contrib.admin` is not installed. |
| `dstt.W009` | `SITES_FRAMEWORK_ENABLED` is set but `django.contrib.sites` is not installed. |
| `dstt.W010` | Packaged templates or minified static assets are missing. |

The following are **database** checks (registered under `Tags.database`), so they
do not run on a plain `manage.py check`; they run with `manage.py migrate` and
`manage.py check --database default`:

| Id | Reports |
| --- | --- |
| `dstt.W011` | A profile references a Sites Framework id that no longer exists. |
| `dstt.W012` | A profile is enabled but has no published revision (info). |

## Management commands

```console
python manage.py scroll_to_top_diagnose
```

Prints the resolved configuration per scope (no secrets) — useful for confirming
which profile and revision a deployment resolves to.

```console
python manage.py scroll_to_top_check_contrast
```

Exits non-zero if a published revision fails the advisory contrast check, so it
can gate a deployment in CI without blocking admin configuration.

## Related sections

- [Configuration (settings and infrastructure)](./configuration.md)
- [Accessibility](./accessibility.md)
- [Testing the package](./testing.md)
