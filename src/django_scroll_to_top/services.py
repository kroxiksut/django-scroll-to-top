"""Configuration lifecycle services for scroll-to-top profiles and revisions.

These functions own the draft/publish/archive transitions described in the
roadmap. Publication and rollback are atomic. Draft and published revisions are
editable in place — editing a published revision updates the live configuration
directly; only archived revisions are immutable snapshots kept for rollback
(enforced in ``ScrollTopRevision.clean``). Every transition invalidates the
resolved-configuration cache through the resolver layer.

The live revision for a profile is derived from revision ``status`` (a profile's
published revision is the single ``ScrollTopRevision`` with
``status="published"`` for that profile), not from a stored pointer. A partial
unique constraint keeps at most one published revision per profile.

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
    # Archive any other currently-published revision for this profile first, so
    # the "one published revision per profile" constraint always holds and the
    # live configuration (derived from status) has a single source of truth.
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

    invalidate_site_config_cache(scope=profile.scope)
    return revision


# Human-readable default names for the starter profiles, kept in one place so
# the admin quick-start action and any callers stay consistent.
STARTER_PROFILES: tuple[tuple[str, str], ...] = (
    ("site", "Site default"),
    ("admin", "Admin default"),
)


@transaction.atomic
def create_starter_configuration(
    *,
    user: object | None = None,
) -> list[str]:
    """Create and publish a default profile + revision for any missing scope.

    Idempotent onboarding helper for the admin quick-start button: a fresh
    install renders the control from built-in defaults but shows an empty admin,
    which reads as "broken". This seeds a profile with one published revision
    (all built-in defaults) per scope that does not already have a published
    revision, so the admin mirrors the button that is already visible.

    Returns the names of the profiles that received a freshly published
    revision (empty when everything was already configured).
    """
    created: list[str] = []
    for scope, name in STARTER_PROFILES:
        profile = ScrollTopProfile.objects.filter(scope=scope, site_id=None).first()
        if profile is None:
            profile = ScrollTopProfile.objects.create(
                scope=scope,
                site_id=None,
                name=name,
                is_enabled=True,
            )
        already_published = ScrollTopRevision.objects.filter(
            profile=profile,
            status=ScrollTopRevision.STATUS_PUBLISHED,
        ).exists()
        if already_published:
            continue
        revision = ScrollTopRevision.objects.create(
            profile=profile,
            name=name,
            created_by=user if user is not None else None,
        )
        publish_revision(revision, user=user)
        created.append(profile.name)
    return created


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

    # A profile is only a resolution candidate when it actually has a published
    # revision (status is the source of truth now that the pointer is gone).
    base = ScrollTopProfile.objects.filter(
        scope=scope,
        is_enabled=True,
        revisions__status=ScrollTopRevision.STATUS_PUBLISHED,
    ).distinct()
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
    """Return the published revision for the resolved scope, if any.

    Site-specific first, then the global profile. For the common (no override
    hook) path this resolves in a single query by filtering revisions directly
    on their profile, so page rendering stays at one DB hit.
    """
    from django_scroll_to_top.settings import get_profile_resolver

    if get_profile_resolver() is not None:
        # A custom PROFILE_RESOLVER may return an arbitrary profile; honor it,
        # then read that profile's status-derived published revision.
        profile = resolve_profile(scope=scope, site_id=site_id)
        if profile is None:
            return None
        return (
            ScrollTopRevision.objects.filter(
                profile=profile,
                status=ScrollTopRevision.STATUS_PUBLISHED,
            )
            .select_related("uploaded_icon")
            .first()
        )

    base = ScrollTopRevision.objects.filter(
        status=ScrollTopRevision.STATUS_PUBLISHED,
        profile__is_enabled=True,
        profile__scope=scope,
    ).select_related("uploaded_icon", "profile")
    if site_id is not None:
        revision = base.filter(profile__site_id=site_id).first()
        if revision is not None:
            return revision
    return base.filter(profile__site_id__isnull=True).first()
