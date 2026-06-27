# Quick start

- [Back to documentation index](../README.md)
- [Overview and current status](./overview.md)

This guide takes `django-scroll-to-top` from an empty install to a rendered
scroll-to-top control on the site and in the standard Django Admin. For the full
settings reference and admin configuration, see the
[configuration](./configuration.md) and [admin](./operations-admin.md) pages and
the [project overview](../../README.md).

> **Beta (`0.x`).** Published as a `0.x` beta — usable and tested, but the public
> API may still change between minor releases before `1.0.0`.

## 1. Install

```console
python -m pip install django-scroll-to-top
```

Compatibility target: Python 3.10+ and Django 4.2 LTS, 5.x, and 6.x
(`Django>=4.2,<7`).

## 2. Enable the app

Add the app to `INSTALLED_APPS`. When admin integration is enabled, place
`django_scroll_to_top` **before** `django.contrib.admin` so the package's
`admin/base_site.html` footer override is selected through normal template
resolution:

```python
INSTALLED_APPS = [
    "django_scroll_to_top",   # before django.contrib.admin
    # ...
    "django.contrib.admin",
]
```

## 3. Configure (settings own install/infrastructure only)

Configuration is provided through the `DJANGO_SCROLL_TO_TOP` dictionary. Every
key is optional; the defaults below are the built-in values:

```python
DJANGO_SCROLL_TO_TOP = {
    "SITE_ENABLED": True,              # render via {% scroll_to_top %}
    "ADMIN_ENABLED": True,             # inject into the standard Django Admin
    "SITES_FRAMEWORK_ENABLED": False,  # opt into per-Site profiles
    "CSP_MODE": "external",            # "external" | "nonce"
    "ADMIN_SHOW_ON_AUTH_PAGES": False, # show on admin login / password reset
    "DEFAULT_COLLISION_POLICY": "ignore",  # ignore | shift | fallback_corner | hide
}
```

Appearance and behavior are **not** configured here — they live in
database-backed configuration edited through Django Admin (see step 7).

## 4. Wire the URLs

Include the package URLConf so the control can load its versioned same-origin
stylesheet endpoint (required for the strict-CSP path):

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path(
        "scroll-to-top/",
        include(
            ("django_scroll_to_top.urls", "django_scroll_to_top"),
            namespace="django_scroll_to_top",
        ),
    ),
]
```

## 5. Migrate

```console
python manage.py migrate
```

## 6. Render the control

Load the tag library and render the control once near the end of your shared
base template:

```django
{% load scroll_to_top %}

<!-- Page content -->

{% scroll_to_top %}
```

With no database configuration yet, the tag renders from safe built-in defaults.
The no-JavaScript baseline is a plain top-of-document link in the configured
corner; collision avoidance, theming, and dismissal are progressive
enhancements.

For a custom `AdminSite` or an overridden `admin/base_site.html`, add the admin
control explicitly in the footer block:

```django
{% extends "admin/base.html" %}
{% load i18n scroll_to_top %}

{% block footer %}
  {{ block.super }}
  {% scroll_to_top scope="admin" %}
{% endblock %}
```

## 7. Customize through Django Admin

Open the Django Admin and edit the scroll-to-top configuration:

- Site and admin scopes are independent; configure each separately.
- Edit the draft revision, preview it live, then publish. Publishing archives the
  previous published revision; you can roll back or clone a revision into a new
  draft.
- Desktop values are primary; each mobile-capable field explicitly inherits the
  desktop value or stores an override.

## 8. Verify the deployment

```console
python manage.py scroll_to_top_diagnose        # resolved config per scope, no secrets
python manage.py scroll_to_top_check_contrast  # non-zero exit if a published revision fails
```

System checks (`dstt.W001`–`dstt.W010`) report common misconfigurations such as
unapplied migrations, a missing URLConf, an unsupported `CSP_MODE`, or
`django_scroll_to_top` ordered after `django.contrib.admin`.

## Next steps

- [Overview and current status](./overview.md)
- [Configuration reference](./configuration.md)
- [Admin: profiles, revisions, publish and rollback](./operations-admin.md)
- [Presentation: templates, colors, sizing, and icons](./presentation.md)
- [Behavior and runtime](./runtime.md)
