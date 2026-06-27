from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, ProgrammingError

from django_scroll_to_top.services import resolve_published_revision
from django_scroll_to_top.settings import get_scroll_to_top_settings
from django_scroll_to_top.site_config import resolve_site_config


class Command(BaseCommand):
    help = (
        "Print the resolved scroll-to-top configuration for each scope without "
        "exposing secrets, to diagnose installation and resolution issues."
    )

    def handle(self, *args, **options) -> None:
        settings = get_scroll_to_top_settings()
        self.stdout.write("django-scroll-to-top diagnostics")
        self.stdout.write(f"  site_enabled: {settings.site_enabled}")
        self.stdout.write(f"  admin_enabled: {settings.admin_enabled}")
        self.stdout.write(
            f"  sites_framework_enabled: {settings.sites_framework_enabled}"
        )
        self.stdout.write(f"  csp_mode: {settings.csp_mode}")
        self.stdout.write(
            f"  default_collision_policy: {settings.default_collision_policy}"
        )

        for scope in ("site", "admin"):
            try:
                resolved = resolve_site_config(request=None, scope=scope)
                revision = (
                    None
                    if resolved is None
                    else resolve_published_revision(scope=scope)
                )
            except (OperationalError, ProgrammingError):
                self.stdout.write(
                    f"  [{scope}] database unavailable (run migrations first)"
                )
                continue
            if resolved is None:
                self.stdout.write(f"  [{scope}] integration disabled")
                continue
            source = (
                "published-revision" if revision is not None else "built-in-default"
            )
            site_label = "global" if resolved.site_id is None else resolved.site_id
            config = resolved.visual_config
            self.stdout.write(
                f"  [{scope}] source={source} site={site_label} "
                f"version={resolved.version}"
            )
            self.stdout.write(
                f"           shape={config.shape} fill={config.fill_variant} "
                f"icon={config.icon_name} theme_mode={config.theme_mode}"
            )
