from __future__ import annotations

from io import StringIO

import pytest
from django.core.checks import run_checks
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.services import publish_revision

_APPS_NO_ADMIN = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "django_scroll_to_top",
]


# --- System checks -----------------------------------------------------------


def test_check_reports_non_dict_settings(db) -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP=["not", "a", "dict"]):
        messages = run_checks(tags=["models"])
    assert any(message.id == "dstt.W007" for message in messages)


def test_check_reports_unknown_settings_key(db) -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"SITE_ENABLED": True, "BOGUS": 1}):
        messages = run_checks(tags=["models"])
    assert any(message.id == "dstt.W007" for message in messages)


def test_check_reports_admin_enabled_without_admin_app(db) -> None:
    with override_settings(
        INSTALLED_APPS=_APPS_NO_ADMIN,
        DJANGO_SCROLL_TO_TOP={"ADMIN_ENABLED": True},
    ):
        messages = run_checks(tags=["models"])
    assert any(message.id == "dstt.W008" for message in messages)


def test_check_reports_sites_enabled_without_sites_app(db) -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"SITES_FRAMEWORK_ENABLED": True}):
        messages = run_checks(tags=["models"])
    assert any(message.id == "dstt.W009" for message in messages)


def test_packaged_assets_check_does_not_false_positive(db) -> None:
    messages = run_checks(tags=["models"])
    assert not any(message.id == "dstt.W010" for message in messages)


# --- Management commands -----------------------------------------------------


def test_diagnose_command_reports_resolved_configuration(db) -> None:
    profile = ScrollTopProfile.objects.create(scope="site", name="Site")
    publish_revision(
        ScrollTopRevision.objects.create(profile=profile, name="rev", shape="square")
    )
    out = StringIO()

    call_command("scroll_to_top_diagnose", stdout=out)

    output = out.getvalue()
    assert "django-scroll-to-top diagnostics" in output
    assert "[site]" in output
    assert "source=published-revision" in output
    assert "shape=square" in output


def test_diagnose_command_reports_builtin_default(db) -> None:
    out = StringIO()

    call_command("scroll_to_top_diagnose", stdout=out)

    output = out.getvalue()
    assert "source=built-in-default" in output


def test_check_contrast_command_passes_for_valid_revision(db) -> None:
    profile = ScrollTopProfile.objects.create(scope="site", name="Site")
    publish_revision(ScrollTopRevision.objects.create(profile=profile, name="ok"))
    out = StringIO()

    call_command("scroll_to_top_check_contrast", stdout=out)

    assert "pass contrast checks" in out.getvalue()


def test_check_contrast_command_fails_for_bad_revision(db) -> None:
    profile = ScrollTopProfile.objects.create(scope="site", name="Site")
    # Identical foreground/background can never meet the contrast minimum.
    publish_revision(
        ScrollTopRevision.objects.create(
            profile=profile,
            name="bad",
            foreground_color="#333333",
            background_color="#333333",
        )
    )

    with pytest.raises(CommandError):
        call_command("scroll_to_top_check_contrast", stderr=StringIO())


def test_check_contrast_command_handles_no_published_revisions(db) -> None:
    out = StringIO()

    call_command("scroll_to_top_check_contrast", stdout=out)

    assert "No published revisions" in out.getvalue()
