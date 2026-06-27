# Security Policy

## Supported versions

This project is in the `0.x` (beta) series. Security fixes are provided for the
latest published `0.x` release. Upgrade to the latest version to receive fixes.

| Version | Supported |
| --- | --- |
| 0.1.x | ✅ |
| < 0.1 | ❌ |

## Reporting a vulnerability

Please **do not** report security problems in a public issue.

Report privately through GitHub's **"Report a vulnerability"** flow on the
repository's **Security** tab:
<https://github.com/kroxiksut/django-scroll-to-top/security/advisories/new>.
This opens a private security advisory visible only to the maintainers. If you
cannot use that flow, email <fmalkov91@gmail.com> instead.

Please include the affected version(s), reproduction steps, and the impact you
observed. We aim to acknowledge a report within a few days and to coordinate a
fix and a disclosure timeline with you.

Relevant areas include SVG sanitization, admin authorization, template
rendering, dismissal storage, the same-origin stylesheet endpoint, and runtime
DOM hooks.

Russian version: [SECURITY.ru.md](./SECURITY.ru.md).
