# Repository Structure for `django-scroll-to-top`

## Current Tree

```text
django-scroll-to-top/
|-- demo/                           # standalone demo Django project and seeded content
|-- docs/
|   |-- README.md                   # documentation entry index (EN); README.ru.md is the RU index
|   |-- ai/                         # English-only AI-agent integration guides
|   |-- assets/                     # documentation images and logo
|   |-- recipes/                    # task-oriented how-to guides (e.g. floating-widget collision)
|   |-- en/                         # canonical user documentation (topic pages)
|   |-- i18n/                       # translation workflow notes
|   `-- ru/                         # maintained Russian translation (topic pages)
|-- tools/                          # dev helpers: reproducible asset build + clean-install smoke test
|-- src/django_scroll_to_top/
|   |-- migrations/                 # Django migrations
|   `-- templatetags/               # public template-tag namespace
|-- tests/                          # pytest/pytest-django test harness
|-- ARCHITECTURE.md                 # canonical architecture and boundaries
|-- CHANGELOG.md                    # canonical English changelog
|-- CHANGELOG.ru.md                 # Russian changelog translation
|-- conda.txt                       # local Conda environment name
|-- CONTRIBUTING.md                 # canonical English contributor guide
|-- CONTRIBUTING.ru.md              # Russian contributor guide
|-- LICENSE                         # project license
|-- README.md                       # canonical English project overview
|-- README.ru.md                    # maintained Russian translation
|-- SECURITY.md                     # canonical English security policy
|-- SECURITY.ru.md                  # Russian security policy
|-- STRUCTURE.md                    # this file
|-- THIRD_PARTY_LICENSES.md         # vendored asset notices and upstream licenses
|-- pyproject.toml                  # packaging and tool configuration
`-- pyrightconfig.json              # package-local pyright defaults
```

## Planned Additions

```text
django-scroll-to-top/
|-- .github/workflows/ci.yml        # CI matrix (Django 4.2/5.2/6.0) + lint/build
|-- tox.ini                         # local multi-Django compatibility matrix
`-- src/django_scroll_to_top/
    |-- models.py                  # ScrollTopProfile, ScrollTopRevision, ScrollTopUploadedIcon
    |-- services.py                # publish/rollback/draft lifecycle + profile resolution
    |-- management/commands/        # scroll_to_top_diagnose + scroll_to_top_check_contrast
    |-- locale/ru/LC_MESSAGES/      # Russian gettext catalog (django.po/.mo)
    |-- site_config.py             # request-local/shared site config resolution and cache
    |-- settings.py                # normalized package settings and CSP mode accessors
    |-- styles.py                  # versioned stylesheet serialization helpers
    |-- urls.py                    # package URLConf for public stylesheet delivery
    |-- views.py                   # same-origin stylesheet endpoint
    |-- signals.py                 # cache invalidation hooks for direct-config milestone
    |-- icons/tabler/               # vendored built-in Tabler SVG subset + manifest
    |-- admin_preview.py            # shared admin live-preview renderer
    |-- contrast.py                 # color parsing and contrast validation helpers
    |-- forms.py                    # admin-facing preview/configuration forms
    |-- icons/registry.py           # unified builtin/developer/uploaded icon lookup
    |-- static/django_scroll_to_top/scroll-to-top.js      # readable runtime source asset
    |-- static/django_scroll_to_top/scroll-to-top.min.js  # reproducibly minified runtime asset
    |-- static/django_scroll_to_top/scroll-to-top.min.css # reproducibly minified stylesheet asset
    |-- templates/admin/base_site.html # standard-admin footer injection via documented template override
    |-- templates/django_scroll_to_top/includes/
    |   `-- scroll_to_top_tag.html  # inclusion-tag wrapper for one-time asset/control render
    |-- icons/sanitizer.py          # strict XML sanitizer for uploaded SVG
    |-- locale/                     # gettext catalogs
    |-- static/django_scroll_to_top/# CSS, JavaScript, and static assets
    |   |-- admin-icon-picker.css   # admin icon-picker presentation
    |   `-- admin-icon-picker.js    # admin icon-picker filtering/sync
    `-- templates/django_scroll_to_top/ # component and admin templates
|-- tests/urls.py                   # test URLConf including package namespace
|-- tests/urls_without_dstt.py      # negative URLConf fixture for system checks
`-- tests/views.py                  # page-level CSP contract fixtures
```

Do not create empty implementation layers before a task introduces their
contract.

## Update Rule

Update this document in the same change set when significant files or
directories are added, removed, moved, or renamed. When project skills change,
update both this document and `AGENTS.md`.
