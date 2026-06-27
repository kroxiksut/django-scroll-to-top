from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.services import (
    create_draft_from_revision,
    publish_revision,
    resolve_profile,
    resolve_published_revision,
    rollback_to_revision,
)


def _profile(scope: str = "site", site_id: int | None = None, name: str = "P"):
    return ScrollTopProfile.objects.create(scope=scope, site_id=site_id, name=name)


def _draft(profile, **fields) -> ScrollTopRevision:
    return ScrollTopRevision.objects.create(
        profile=profile,
        name=fields.pop("name", "rev"),
        **fields,
    )


def test_publish_sets_pointer_status_and_timestamp(db) -> None:
    profile = _profile()
    revision = _draft(profile, shape="square")

    publish_revision(revision)

    revision.refresh_from_db()
    profile.refresh_from_db()
    assert revision.status == ScrollTopRevision.STATUS_PUBLISHED
    assert revision.published_at is not None
    assert profile.published_revision_id == revision.pk


def test_publishing_archives_previous_published_revision(db) -> None:
    profile = _profile()
    first = _draft(profile, shape="circle")
    publish_revision(first)

    second = create_draft_from_revision(first)
    second.shape = "square"
    second.save()
    publish_revision(second)

    first.refresh_from_db()
    profile.refresh_from_db()
    assert first.status == ScrollTopRevision.STATUS_ARCHIVED
    assert profile.published_revision_id == second.pk


def test_create_draft_clones_snapshot_fields(db) -> None:
    profile = _profile()
    source = _draft(profile, shape="square", background_color="#112233")
    publish_revision(source)

    draft = create_draft_from_revision(source)

    assert draft.pk != source.pk
    assert draft.status == ScrollTopRevision.STATUS_DRAFT
    assert draft.published_at is None
    assert draft.profile_id == profile.pk
    assert draft.shape == "square"
    assert draft.background_color == "#112233"


def test_published_revision_is_editable_in_place(db) -> None:
    profile = _profile()
    revision = _draft(profile)
    publish_revision(revision)

    revision.shape = "square"
    revision.full_clean()
    revision.save()

    revision.refresh_from_db()
    assert revision.shape == "square"
    assert revision.status == ScrollTopRevision.STATUS_PUBLISHED


def test_archived_revision_is_immutable(db) -> None:
    profile = _profile()
    original = _draft(profile, shape="circle")
    publish_revision(original)

    newer = create_draft_from_revision(original)
    publish_revision(newer)

    original.refresh_from_db()
    assert original.status == ScrollTopRevision.STATUS_ARCHIVED
    original.shape = "square"
    with pytest.raises(ValidationError):
        original.full_clean()


def test_rollback_republishes_archived_revision(db) -> None:
    profile = _profile()
    original = _draft(profile, shape="circle")
    publish_revision(original)

    newer = create_draft_from_revision(original)
    newer.shape = "square"
    newer.save()
    publish_revision(newer)

    rollback_to_revision(original)

    original.refresh_from_db()
    newer.refresh_from_db()
    profile.refresh_from_db()
    assert original.status == ScrollTopRevision.STATUS_PUBLISHED
    assert newer.status == ScrollTopRevision.STATUS_ARCHIVED
    assert profile.published_revision_id == original.pk


def test_resolve_profile_prefers_site_specific_over_global(db) -> None:
    global_profile = _profile(name="global")
    publish_revision(_draft(global_profile, shape="circle"))
    site_profile = _profile(site_id=5, name="site-5")
    publish_revision(_draft(site_profile, shape="square"))

    assert resolve_profile(scope="site", site_id=5) == site_profile
    assert resolve_profile(scope="site", site_id=99) == global_profile
    assert resolve_profile(scope="site", site_id=None) == global_profile


def test_resolve_skips_disabled_profile(db) -> None:
    profile = _profile()
    publish_revision(_draft(profile, shape="square"))
    profile.is_enabled = False
    profile.save()

    assert resolve_published_revision(scope="site") is None


def test_unique_global_profile_per_scope(db) -> None:
    _profile(name="first")
    with pytest.raises(IntegrityError), transaction.atomic():
        _profile(name="second")
