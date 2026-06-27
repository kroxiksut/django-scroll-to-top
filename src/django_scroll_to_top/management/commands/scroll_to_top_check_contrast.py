from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from django_scroll_to_top.contrast import ColorValidationError, meets_minimum_contrast
from django_scroll_to_top.models import ScrollTopRevision

# Foreground/background pairs that must meet the minimum contrast ratio.
_CONTRAST_PAIRS = (
    ("foreground_color", "background_color"),
    ("hover_foreground_color", "hover_background_color"),
    ("active_foreground_color", "active_background_color"),
    ("dark_foreground_color", "dark_background_color"),
    ("dark_hover_foreground_color", "dark_hover_background_color"),
    ("dark_active_foreground_color", "dark_active_background_color"),
)


class Command(BaseCommand):
    help = (
        "Check the foreground/background contrast of every published revision "
        "and exit non-zero if any pair fails."
    )

    def handle(self, *args, **options) -> None:
        published = ScrollTopRevision.objects.filter(
            status=ScrollTopRevision.STATUS_PUBLISHED
        ).order_by("pk")
        if not published:
            self.stdout.write("No published revisions to check.")
            return

        failures = 0
        for revision in published:
            for foreground_field, background_field in _CONTRAST_PAIRS:
                foreground = getattr(revision, foreground_field)
                background = getattr(revision, background_field)
                try:
                    passes = meets_minimum_contrast(foreground, background)
                except ColorValidationError:
                    passes = False
                if not passes:
                    failures += 1
                    self.stderr.write(
                        f"FAIL revision {revision.pk} ({revision.name}): "
                        f"{foreground_field}/{background_field}"
                    )

        if failures:
            raise CommandError(
                f"{failures} contrast check(s) failed across published revisions."
            )
        self.stdout.write(
            f"All {published.count()} published revision(s) pass contrast checks."
        )
