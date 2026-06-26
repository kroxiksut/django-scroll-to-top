# Icons Guide (AI)

## Scope

Use this guide to add or change the control's icon. Three sources exist
(`icon_source` on `ScrollTopRevision`): `builtin`, `developer`, `uploaded`.

## Built-in icons

The vendored Tabler subset under `icons/tabler/` (MIT). These already paint with
`currentColor`, so they recolor automatically. Select via the admin icon picker
(`icon_name` is set by the picker, not by hand); `icon_style` chooses
outline/filled where both exist. Keep `LICENSE.tabler.txt` and `manifest.json`.

## Developer icons

Register trusted, code-owned icons via the registry:

```python
from django_scroll_to_top.icons.registry import register_developer_icon
```

Use this for project icons that ship in code (not operator uploads). To recolor
with the configured color, the SVG must use `currentColor`.

## Uploaded icons (operator-provided)

Uploaded SVGs become `ScrollTopUploadedIcon` records and are **always sanitized**
before storage/render. Production never renders an unsanitized upload.

The sanitizer (`icons/sanitizer.py`) parses as **XML** (never regex) and rejects:
DTDs, entities, scripts, event handlers, external resource references, embedded
documents (`foreignObject`), unsafe namespaces, and excessively complex
documents. It allows only documented graphical elements/attributes, normalizes
geometry/`viewBox`, and stores only the sanitized payload (with checksums).

Color handling:
- `style_kind` `outline` / `filled` with `color_mode = recolor` → recolored via
  `currentColor`.
- `style_kind` `multicolor` / `original` → must use `color_mode = preserve`; they
  keep their own colors and ignore the color fields (enforced in `clean()`).

## Rights and attribution

Sanitizing a file grants **no usage right**. Each uploaded icon must carry
author, source, license, copyright, and attribution metadata plus
`rights_confirmed = True`. The uploaded-icon admin exposes an attribution-export
action. Keep attribution accurate.

## Guardrails

- Never bypass the sanitizer or render raw uploaded SVG.
- Never set `color_mode = recolor` for multicolor/original icons.
- For an icon to follow the configured color it must paint with `currentColor`
  (`fill`/`stroke`).
- Treating an upload as "free" because it passed the sanitizer is a defect — the
  operator confirms rights, not the parser.

## Reference

- [Presentation](../en/presentation.md) · [Security & SVG sanitization](../en/security-csp.md)
- [THIRD_PARTY_LICENSES.md](../../THIRD_PARTY_LICENSES.md)
