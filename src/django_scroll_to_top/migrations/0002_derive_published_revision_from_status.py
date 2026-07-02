"""Remove the ScrollTopProfile.published_revision pointer.

The live revision is now derived from revision ``status`` (a profile's published
revision is the single ``ScrollTopRevision`` with ``status="published"`` for that
profile), removing the mutual profile<->revision link. A partial unique
constraint keeps at most one published revision per profile.

The data step reconciles status from the old pointer before the column is
dropped, so existing installs keep exactly the revision they had live. Both
profile uniqueness constraints also gain human-readable violation messages.
"""

from __future__ import annotations

from django.db import migrations, models

PUBLISHED = "published"
ARCHIVED = "archived"


def forwards_reconcile(apps, schema_editor) -> None:
    Profile = apps.get_model("django_scroll_to_top", "ScrollTopProfile")
    Revision = apps.get_model("django_scroll_to_top", "ScrollTopRevision")
    for profile in Profile.objects.all():
        pointer_id = profile.published_revision_id
        published = Revision.objects.filter(profile=profile, status=PUBLISHED)
        if pointer_id is not None:
            # Keep the pointed revision published; archive any stragglers.
            published.exclude(pk=pointer_id).update(status=ARCHIVED)
            Revision.objects.filter(pk=pointer_id).update(status=PUBLISHED)
        else:
            # No pointer: keep at most one published revision, archive the rest.
            keep = published.order_by("pk").first()
            if keep is not None:
                published.exclude(pk=keep.pk).update(status=ARCHIVED)


def backwards_reconcile(apps, schema_editor) -> None:
    # On downgrade the pointer column has just been re-added; repopulate it from
    # the status-derived live revision so old code keeps working.
    Profile = apps.get_model("django_scroll_to_top", "ScrollTopProfile")
    Revision = apps.get_model("django_scroll_to_top", "ScrollTopRevision")
    for profile in Profile.objects.all():
        revision = (
            Revision.objects.filter(profile=profile, status=PUBLISHED)
            .order_by("pk")
            .first()
        )
        profile.published_revision_id = None if revision is None else revision.pk
        profile.save(update_fields=["published_revision"])


class Migration(migrations.Migration):

    dependencies = [
        ("django_scroll_to_top", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards_reconcile, backwards_reconcile),
        migrations.AddConstraint(
            model_name="scrolltoprevision",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "published")),
                fields=("profile",),
                name="dstt_unique_published_per_profile",
                violation_error_message=(
                    "This profile already has a published revision. Publishing "
                    "another one archives the previous automatically, so you do "
                    "not need to unpublish first."
                ),
            ),
        ),
        migrations.RemoveField(
            model_name="scrolltopprofile",
            name="published_revision",
        ),
        migrations.RemoveConstraint(
            model_name="scrolltopprofile",
            name="dstt_unique_scope_site",
        ),
        migrations.AddConstraint(
            model_name="scrolltopprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("site_id__isnull", False)),
                fields=("scope", "site_id"),
                name="dstt_unique_scope_site",
                violation_error_message=(
                    "A scroll-to-top profile for this scope and Site already "
                    "exists. Edit that profile, pick a different Site, or clear "
                    "the Site ID to use the global profile."
                ),
            ),
        ),
        migrations.RemoveConstraint(
            model_name="scrolltopprofile",
            name="dstt_unique_scope_global",
        ),
        migrations.AddConstraint(
            model_name="scrolltopprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("site_id__isnull", True)),
                fields=("scope",),
                name="dstt_unique_scope_global",
                violation_error_message=(
                    "A global scroll-to-top profile for this scope already "
                    "exists. Edit the existing profile, or set a Site ID to "
                    "target a specific site."
                ),
            ),
        ),
    ]
