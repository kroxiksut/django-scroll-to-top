"""Configuration lifecycle services for scroll-to-top profiles and revisions.

These functions own the draft/publish/archive transitions described in the
roadmap. Publication and rollback are atomic. Draft and published revisions are
editable in place — editing a published revision updates the live configuration
directly; only archived revisions are immutable snapshots kept for rollback
(enforced in ``ScrollTopRevision.clean``). Every transition invalidates the
resolved-configuration cache through the resolver layer.

Known limitation (0.x): because the published revision is editable, a change to
it goes live immediately with no separate draft step. This is intentional for
now and slated for review before 1.0 (make published immutable + always edit a
draft cloned via ``create_draft_from_revision``). See ARCHITECTURE.md.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.site_config import invalidate_site_config_cache

# Snapshot fields copied when cloning a revision into a new draft. Lifecycle and
# bookkeeping fields (pk, status, profile, author, timestamps) are intentionally
# excluded and re-derived by the clone.
_LIFECYCLE_FIELDS = frozenset(
    {
        "id",
        "profile",
        "status",
        "created_by",
        "published_at",
        "created_at",
        "updated_at",
    }
)


def _snapshot_field_names() -> list[str]:
    return [
        field.name
        for field in ScrollTopRevision._meta.concrete_fields
        if field.name not in _LIFECYCLE_FIELDS
    ]


@transaction.atomic
def publish_revision(
    revision: ScrollTopRevision,
    *,
    user: object | None = None,
) -> ScrollTopRevision:
    """Publish ``revision`` atomically and archive the previous published one."""
    profile = revision.profile
    if profile is None:
        raise ValueError("A revision must belong to a profile before publishing.")

    now = timezone.now()
    ScrollTopRevision.objects.filter(
        profile=profile,
        status=ScrollTopRevision.STATUS_PUBLISHED,
    ).exclude(pk=revision.pk).update(status=ScrollTopRevision.STATUS_ARCHIVED)

    revision.status = ScrollTopRevision.STATUS_PUBLISHED
    if revision.published_at is None:
        revision.published_at = now
    if user is not None and revision.created_by is None:
        revision.created_by = user
    revision.save(
        update_fields=["status", "published_at", "created_by", "updated_at"]
    )

    profile.published_revision = revision
    profile.save(update_fields=["published_revision", "updated_at"])

    invalidate_site_config_cache(scope=profile.scope)
    return revision


@transaction.atomic
def create_draft_from_revision(
    revision: ScrollTopRevision,
    *,
    user: object | None = None,
) -> ScrollTopRevision:
    """Clone ``revision`` snapshot fields into a fresh editable draft."""
    draft = ScrollTopRevision(
        profile=revision.profile,
        status=ScrollTopRevision.STATUS_DRAFT,
        created_by=user,
    )
    source = ScrollTopRevision.objects.get(pk=revision.pk)
    for field_name in _snapshot_field_names():
        setattr(draft, field_name, getattr(source, field_name))
    draft.save()
    return draft


@transaction.atomic
def rollback_to_revision(
    revision: ScrollTopRevision,
    *,
    user: object | None = None,
) -> ScrollTopRevision:
    """Roll back by re-publishing an existing (typically archived) revision."""
    return publish_revision(revision, user=user)


def resolve_profile(
    *,
    scope: str,
    site_id: int | None = None,
) -> ScrollTopProfile | None:
    """Resolve the effective profile: site-specific first, then global.

    An optional ``PROFILE_RESOLVER`` hook may override selection; returning
    ``None`` falls through to the built-in resolution.
    """
    from django_scroll_to_top.settings import get_profile_resolver

    resolver = get_profile_resolver()
    if resolver is not None:
        try:
            override = resolver(scope=scope, site_id=site_id)
        except Exception:  # noqa: BLE001 - a faulty hook must not break rendering
            override = None
        if override is not None:
            return override

    base = ScrollTopProfile.objects.filter(
        scope=scope,
        is_enabled=True,
        published_revision__isnull=False,
    ).select_related("published_revision")
    if site_id is not None:
        site_profile = base.filter(site_id=site_id).first()
        if site_profile is not None:
            return site_profile
    return base.filter(site_id__isnull=True).first()


def resolve_published_revision(
    *,
    scope: str,
    site_id: int | None = None,
) -> ScrollTopRevision | None:
    """Return the published revision for the resolved profile, if any."""
    profile = resolve_profile(scope=scope, site_id=site_id)
    return None if profile is None else profile.published_revision
