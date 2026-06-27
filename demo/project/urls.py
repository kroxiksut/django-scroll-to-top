from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from demo.project.views import collection_detail, home, obstacles

urlpatterns = [
    path("", home, name="home"),
    path("obstacles/", obstacles, name="obstacles"),
    path("collections/<slug:slug>/", collection_detail, name="collection-detail"),
    path("", include("django_cookies_152fz.urls")),
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
