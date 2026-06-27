from __future__ import annotations

from django.apps import apps
from django.contrib import admin
from django.urls import include, path

from demo.project.views import collection_detail, home, obstacles

urlpatterns = [
    path("", home, name="home"),
    path("obstacles/", obstacles, name="obstacles"),
    path("collections/<slug:slug>/", collection_detail, name="collection-detail"),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # Versioned same-origin stylesheet endpoint (strict-CSP color transport).
    path(
        "scroll-to-top/",
        include(
            ("django_scroll_to_top.urls", "django_scroll_to_top"),
            namespace="django_scroll_to_top",
        ),
    ),
]

# Optional: cookie banner routes are only added when django-cookies-152fz is
# installed, so the demo runs without it.
if apps.is_installed("django_cookies_152fz"):
    urlpatterns.append(path("", include("django_cookies_152fz.urls")))
