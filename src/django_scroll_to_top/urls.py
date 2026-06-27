from __future__ import annotations

from django.urls import path

from django_scroll_to_top.views import site_stylesheet

app_name = "django_scroll_to_top"

urlpatterns = [
    path("styles/<str:version>.css", site_stylesheet, name="site-stylesheet"),
]
