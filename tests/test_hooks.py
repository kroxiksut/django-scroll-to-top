from __future__ import annotations

from django.http import HttpRequest
from django.test.utils import override_settings

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload
from django_scroll_to_top.services import publish_revision, resolve_profile
from django_scroll_to_top.site_config import (
    invalidate_site_config_cache,
    resolve_site_config,
)


def _site_id_hook(request):
    return 42


def _failing_hook(request):
    raise RuntimeError("boom")


def _obstacle_hook():
    return [".hooked-obstacle", ".another"]


def test_site_id_resolver_hook_overrides_without_sites_framework(db) -> None:
    invalidate_site_config_cache()
    with override_settings(
        DJANGO_SCROLL_TO_TOP={"SITE_ENABLED": True, "SITE_ID_RESOLVER": _site_id_hook}
    ):
        resolved = resolve_site_config(request=HttpRequest())

    assert resolved is not None
    assert resolved.site_id == 42


def test_site_id_resolver_hook_failure_is_isolated(db) -> None:
    invalidate_site_config_cache()
    with override_settings(
        DJANGO_SCROLL_TO_TOP={"SITE_ENABLED": True, "SITE_ID_RESOLVER": _failing_hook}
    ):
        resolved = resolve_site_config(request=HttpRequest())

    assert resolved is not None
    assert resolved.site_id is None


def test_profile_resolver_hook_overrides_selection(db) -> None:
    # A disabled profile is normally skipped; the hook forces its selection.
    profile = ScrollTopProfile.objects.create(
        scope="site", name="Forced", is_enabled=False
    )
    publish_revision(
        ScrollTopRevision.objects.create(profile=profile, name="rev", shape="square")
    )
    assert resolve_profile(scope="site") is None  # disabled, default skips it

    def hook(*, scope, site_id):
        return profile

    with override_settings(DJANGO_SCROLL_TO_TOP={"PROFILE_RESOLVER": hook}):
        assert resolve_profile(scope="site") == profile


def test_obstacle_selectors_hook_merges_into_payload() -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"OBSTACLE_SELECTORS": _obstacle_hook}):
        payload = build_render_payload(
            VisualConfig(obstacle_selectors=(".cookie-banner",))
        )

    assert ".cookie-banner" in payload.obstacle_selectors_json
    assert ".hooked-obstacle" in payload.obstacle_selectors_json
    assert ".another" in payload.obstacle_selectors_json


def test_hooks_accept_dotted_path_strings(db) -> None:
    invalidate_site_config_cache()
    with override_settings(
        DJANGO_SCROLL_TO_TOP={
            "SITE_ENABLED": True,
            "SITE_ID_RESOLVER": "tests.test_hooks._site_id_hook",
        }
    ):
        resolved = resolve_site_config(request=HttpRequest())

    assert resolved is not None
    assert resolved.site_id == 42


def test_unknown_hook_keys_do_not_trip_settings_check(db) -> None:
    from django.core.checks import run_checks

    with override_settings(
        DJANGO_SCROLL_TO_TOP={"OBSTACLE_SELECTORS": _obstacle_hook}
    ):
        messages = run_checks(tags=["models"])

    assert not any(message.id == "dstt.W007" for message in messages)
