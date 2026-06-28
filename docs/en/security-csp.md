# Security, SVG sanitization, and CSP

- [Back to documentation index](../README.md)
- [Security policy and vulnerability reporting](../../SECURITY.md)

## Principles

- No arbitrary HTML, JavaScript, or CSS is ever stored through admin forms.
- Production never renders an unsanitized uploaded SVG.
- No telemetry or external network calls are enabled by default, and the package
  never performs a server-side fetch of an arbitrary URL.
- Strict CSP support must not silently require `unsafe-inline`.
- Browser storage failures degrade safely without breaking the scroll action.

## Uploaded SVG sanitization

Administrator-uploaded SVG is never rendered directly. The sanitizer
(`icons/sanitizer.py`) parses the file as **XML** (never regex-sanitizes) and
rejects:

- DTDs and entities;
- scripts and event handlers;
- external resource references and embedded documents (`foreignObject`);
- unsafe namespaces;
- anything exceeding the explicit complexity limits below.

It allows only documented graphical elements and attributes, normalizes geometry
and `viewBox` data, and stores only the sanitized payload (with original and
sanitized checksums). Compatible icons support `currentColor` recoloring; safe
original colors are preserved only in an explicit multicolor/original mode.

The complexity limits are explicit constants in `icons/sanitizer.py`; exceeding
any of them rejects the upload rather than truncating it:

| Limit | Default |
| --- | --- |
| Maximum file size | 100 KB (`MAX_SVG_BYTES = 100_000`) |
| Maximum element/node count | 128 (`MAX_ELEMENT_COUNT`) |
| Maximum nesting depth | 8 (`MAX_XML_DEPTH`) |
| Maximum geometry data per attribute (`d`, `points`) | 20,000 chars (`MAX_PATH_DATA_LENGTH`) |
| Elements and attributes | strict allowlist (no `style`, `class`, `id`, `href`) |

### Sanitization is not a license

A file passing the sanitizer does not grant any right to use it. Each
`ScrollTopUploadedIcon` carries author, source, license, copyright, and
attribution metadata plus a mandatory `rights_confirmed` confirmation that the
project may use and distribute the file. The site operator remains responsible
for confirming usage and redistribution rights and keeping attribution accurate;
the admin can export an attribution report.

## Content Security Policy

Validated color and sizing values are delivered through a versioned same-origin
stylesheet endpoint, not an inline `style` attribute, so the strict-CSP path
never needs `unsafe-inline`.

- **`external`** (default) — same-origin `<link>` and `<script>`. Works with
  `default-src 'self'; style-src 'self'; script-src 'self';`.
- **`nonce`** — provide a nonce via `csp_nonce` in the template context or
  `request.csp_nonce`; the package adds it to its external script tag and keeps
  styles on the stylesheet endpoint.

See [configuration.md](./configuration.md) for CSP wiring details.

## Namespacing and isolation

Every CSS class, ID, data attribute, and DOM event is namespaced (`dstt` /
`djstt`). The package never styles global elements (`a`, `button`, `svg`,
`body`), uses no CDN, and has no runtime build step.

## Related sections

- [Configuration (settings and infrastructure)](./configuration.md)
- [Admin: profiles, revisions, publish and rollback](./operations-admin.md)
- [Security policy and vulnerability reporting](../../SECURITY.md)
