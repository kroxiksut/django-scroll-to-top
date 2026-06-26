# Migration and upgrade notes

- [Back to documentation index](./README.md)
- [Admin: profiles, revisions, publish and rollback](./operations-admin.md)

The package ships its own Django migrations (`migrations/0001_initial` onward).
Apply them with the standard command:

```console
python manage.py migrate django_scroll_to_top
```

## Deterministic migrations

Migrations stay deterministic: they never inspect live pages, computed styles,
network resources, or deployment-specific files. Running them produces the same
schema regardless of environment, so they are safe to run in CI and automated
deploys.

## Upgrading

- New presentation/behavior fields are introduced through ordinary schema
  migrations; existing revisions keep their values, and new fields take their
  model defaults.
- Published and archived revisions are preserved across upgrades. Archived
  revisions are immutable snapshots, so a rollback after an upgrade restores the
  exact historical configuration.
- After upgrading, run `python manage.py migrate` and then
  `python manage.py check` so the `dstt.W001` / `dstt.W002` system checks confirm
  migrations are inspectable and applied.

## Data model recap

- `ScrollTopProfile` — scope, optional `site_id`, `is_enabled`, published-revision
  pointer.
- `ScrollTopRevision` — full visual/behavioral snapshot with
  `draft` / `published` / `archived` status.
- `ScrollTopUploadedIcon` — sanitized SVG plus license/attribution metadata.

See [operations-admin.md](./operations-admin.md) for the lifecycle and
[overview.md](./overview.md) for the full module map.

## Related sections

- [Admin: profiles, revisions, publish and rollback](./operations-admin.md)
- [Diagnostics and management commands](./diagnostics.md)
- [Testing the package](./testing.md)
