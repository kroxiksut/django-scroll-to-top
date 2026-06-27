from __future__ import annotations

from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "demo.library"
    verbose_name = "Demo library"

    def ready(self) -> None:
        from . import signals  # noqa: F401

