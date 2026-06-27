from django.contrib import admin
from django.urls import include, path

from tests.views import sample_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sample/", sample_page),
    path(
        "scroll-to-top/",
        include(
            ("django_scroll_to_top.urls", "django_scroll_to_top"),
            namespace="django_scroll_to_top",
        ),
    ),
]
