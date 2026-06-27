from __future__ import annotations

from django.db import migrations, transaction
from django.utils import timezone

SITE_PROFILE_NAME = "Public default"
ADMIN_PROFILE_NAME = "Admin default"

SHARED_REVISION_DEFAULTS = {
    "theme_mode": "manual",
    "icon_name": "arrow-big-up",
    "icon_style": "filled",
    "icon_source": "builtin",
    "shape": "circle",
    "fill_variant": "solid",
    "template_variant": "icon-only",
    "corner": "bottom-right",
    "foreground_color": "#f8fafc",
    "background_color": "#0f766e",
    "border_color": "#115e59",
    "hover_foreground_color": "#ffffff",
    "hover_background_color": "#115e59",
    "hover_border_color": "#115e59",
    "active_foreground_color": "#ffffff",
    "active_background_color": "#134e4a",
    "active_border_color": "#134e4a",
    "focus_ring_color": "#f59e0b",
    "dark_foreground_color": "#f8fafc",
    "dark_background_color": "#0f766e",
    "dark_border_color": "#99f6e4",
    "dark_hover_foreground_color": "#ffffff",
    "dark_hover_background_color": "#115e59",
    "dark_hover_border_color": "#99f6e4",
    "dark_active_foreground_color": "#ffffff",
    "dark_active_background_color": "#134e4a",
    "dark_active_border_color": "#99f6e4",
    "dark_focus_ring_color": "#fde68a",
    "allow_user_dismissal": False,
    "shadow_preset": "large",
    "opacity": 1.0,
    "border_width": 2,
    "focus_ring_width": 3,
    "focus_ring_offset": 3,
    "gradient_start_color": "#0f766e",
    "gradient_end_color": "#115e59",
    "gradient_angle": 135,
    "backdrop_blur": 8,
}


@transaction.atomic
def forwards(apps, schema_editor) -> None:
    ScrollTopProfile = apps.get_model("django_scroll_to_top", "ScrollTopProfile")
    ScrollTopRevision = apps.get_model("django_scroll_to_top", "ScrollTopRevision")
    published_status = "published"

    for scope, profile_name in (
        ("site", SITE_PROFILE_NAME),
        ("admin", ADMIN_PROFILE_NAME),
    ):
        profile, _ = ScrollTopProfile.objects.update_or_create(
            scope=scope,
            site_id=None,
            defaults={"name": profile_name, "is_enabled": True},
        )
        revision = profile.published_revision
        if revision is None:
            revision = ScrollTopRevision.objects.create(
                profile=profile,
                status=published_status,
                published_at=timezone.now(),
                name=profile_name,
                **SHARED_REVISION_DEFAULTS,
            )
            profile.published_revision = revision
            profile.save(update_fields=["published_revision"])
            continue

        changed_fields: list[str] = []
        if revision.name != profile_name:
            revision.name = profile_name
            changed_fields.append("name")
        for field_name, value in SHARED_REVISION_DEFAULTS.items():
            if getattr(revision, field_name) != value:
                setattr(revision, field_name, value)
                changed_fields.append(field_name)
        if revision.status != published_status:
            revision.status = published_status
            changed_fields.append("status")
        if revision.published_at is None:
            revision.published_at = timezone.now()
            changed_fields.append("published_at")
        if changed_fields:
            revision.save(update_fields=changed_fields)
        if profile.published_revision_id != revision.pk:
            profile.published_revision = revision
            profile.save(update_fields=["published_revision"])


def backwards(apps, schema_editor) -> None:
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("library", "0002_tune_site_scroll_to_top_default"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
