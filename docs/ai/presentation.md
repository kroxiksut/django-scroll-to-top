# Presentation Guide (AI)

## Scope

Use this guide to change the control's appearance and behavior. The rule is
simple: **appearance and behavior live in the database (admin), never in Django
settings or template-tag arguments.**

## Where to make changes

- **Preferred:** edit a `ScrollTopRevision` in the Django admin, then publish it.
  Editing the published revision updates the live site and invalidates the scope
  cache.
- **Programmatic seeding (fixtures, data migrations, tests):** create a
  `ScrollTopProfile` and a `ScrollTopRevision`, then call
  `django_scroll_to_top.services.publish_revision(revision, user=...)`. Use
  `create_draft_from_revision` / `rollback_to_revision` for the rest of the
  lifecycle. Do not flip status fields by hand.

## What is configurable

All on `ScrollTopRevision` (see [presentation](../en/presentation.md) for the
full field list):

- Template variant (`icon-only` / `icon-label`), shape, fill variant.
- Light and dark colors for normal/hover/active states + focus ring; `theme_mode`
  `manual` or `inherit_admin_theme`.
- Sizing: desktop is primary; each mobile field inherits (`*_mobile_inherit`) or
  overrides.
- Placement (`corner`), side click zone, shadows, opacity, borders, gradient,
  glass backdrop blur.
- Behavior: visibility threshold/direction, scroll target/offset/behavior,
  collision policy, dismissal — see [runtime](./runtime.md).

## Guardrails

- Appearance is built from **controlled package CSS classes**. Never store
  arbitrary CSS or HTML; the only free-form class field is `custom_css_class`
  (validated tokens: letters, digits, hyphen, underscore).
- Unknown shape/fill/shadow values fall back to safe defaults; forced-colors mode
  neutralizes variants. Don't add new variants client-side.
- Desktop values are primary — set mobile via inherit/override, not by guessing.
- Contrast is **advisory, not enforced**: do not block saving on contrast, but
  surface low-contrast warnings; `scroll_to_top_check_contrast` can gate CI.
- `label_text` is stored as-is and not auto-translated; for multilingual sites
  use a per-Site profile rather than hard-coding a language.

## Reference

- [Presentation](../en/presentation.md) · [Admin lifecycle](../en/operations-admin.md)
- [Accessibility](../en/accessibility.md)
