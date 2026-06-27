from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ScrollToTopConfig(AppConfig):
    """Configure the scroll-to-top Django application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_scroll_to_top"
    verbose_name = _("Scroll-to-top button")

    def ready(self) -> None:
        from django_scroll_to_top import checks, signals  # noqa: F401
