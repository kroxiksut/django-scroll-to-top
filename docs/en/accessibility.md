# Accessibility

- [Back to documentation index](./README.md)
- [Behavior and runtime](./runtime.md)

The control targets WCAG 2.2 AA within its scope. The structural contract below
is implemented and covered by tests (`tests/test_accessibility.py`).

## Implemented and tested

- A translatable **accessible name** on both the control and the close control,
  independent of icon or tooltip (`aria_label` overrides the translated default).
- A minimum **24×24 CSS px target floor**, regardless of configured size.
- A **no-JavaScript link fallback** — a plain top-of-document link.
- **No positive `tabindex`**, no keyboard trap, and no unexpected focus movement.
- Visible **`:focus-visible`** outlines (configurable focus-ring color, width, and
  offset).
- **`prefers-reduced-motion`**: reduced-motion users always get an instant jump,
  never a smooth animation, regardless of `scroll_behavior`.
- **Forced-colors / high-contrast** mode neutralizes every visual variant.
- **RTL-safe** logical properties for placement and spacing.
- Decorative SVG is hidden from accessibility APIs; the accessible name carries
  the meaning.

## Contrast: advisory, not enforced

Color contrast is **not** enforced at save time — operators may pick any colors.
Low-contrast combinations are surfaced as a non-blocking admin warning and can be
audited with:

```console
python manage.py scroll_to_top_check_contrast
```

The command exits non-zero if a published revision fails the contrast check, so
it can gate a deployment without blocking configuration.

## Tracked for later

A full WCAG 2.2 AA audit and zoom verification (200% / 400%) in real browsers are
tracked as a later stabilization step rather than part of the current automated
contract.

## Related sections

- [Presentation: templates, colors, sizing, and icons](./presentation.md)
- [Behavior and runtime](./runtime.md)
- [Diagnostics and management commands](./diagnostics.md)
