from __future__ import annotations

from django.apps import apps
from django.http import HttpRequest


def cookies(request: HttpRequest) -> dict[str, bool]:
    """Expose whether the optional django-cookies-152fz app is installed.

    Templates use ``cookies_enabled`` to guard the cookie banner, the
    cookie-preferences link, and the ``cookies_tags`` template library so the
    demo renders without the optional package installed.
    """
    return {"cookies_enabled": apps.is_installed("django_cookies_152fz")}
