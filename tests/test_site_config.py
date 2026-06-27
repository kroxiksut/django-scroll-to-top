from __future__ import annotations

from unittest.mock import Mock, patch

from django.core.checks import run_checks
from django.db import connection
from django.db.utils import OperationalError
from django.http import HttpRequest
from django.template import Context, Template
from django.test import Client
from django.test.utils import CaptureQueriesContext, override_settings

from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.services import (
    create_draft_from_revision,
    publish_revision,
)
from django_scroll_to_top.site_config import (
    _LOGGED_CONFIG_ERRORS,
    invalidate_site_config_cache,
    resolve_site_config,
)


def _publish_config(
    *,
    scope: str = "site",
    site_id: int | None = None,
    name: str = "Primary",
    **revision_fields: object,
) -> tuple[ScrollTopProfile, ScrollTopRevision]:
    """Create a profile with one published revision for resolver tests."""
    profile = ScrollTopProfile.objects.create(
        scope=scope,
        site_id=site_id,
        name=name,
    )
    revision = ScrollTopRevision.objects.create(
        profile=profile,
        name=f"{name} revision",
        **revision_fields,
    )
    publish_revision(revision)
    return profile, revision


def test_resolve_site_config_uses_request_local_cache(db) -> None:
    _publish_config(shape="square")
    request = HttpRequest()
    invalidate_site_config_cache()

    with CaptureQueriesContext(connection) as queries:
        first = resolve_site_config(request=request)
        second = resolve_site_config(request=request)

    assert first is not None
    assert second is not None
    assert first.visual_config.shape == "square"
    assert second.visual_config.shape == "square"
    assert len(first.version) == 12
    assert len(queries) == 1


def test_resolve_site_config_uses_shared_cache_across_requests(db) -> None:
    _publish_config(shape="rounded-square")
    invalidate_site_config_cache()

    with CaptureQueriesContext(connection) as first_queries:
        first = resolve_site_config(request=HttpRequest())
    with CaptureQueriesContext(connection) as second_queries:
        second = resolve_site_config(request=HttpRequest())

    assert first is not None
    assert second is not None
    assert first.visual_config.shape == "rounded-square"
    assert second.visual_config.shape == "rounded-square"
    assert len(first_queries) == 1
    assert len(second_queries) == 0


def test_resolve_site_config_invalidates_shared_cache_after_publish(db) -> None:
    _profile, revision = _publish_config(shape="circle")
    invalidate_site_config_cache()

    first = resolve_site_config(request=HttpRequest())
    assert first is not None
    assert first.visual_config.shape == "circle"

    # Real lifecycle: edit a fresh draft, then publish it.
    draft = create_draft_from_revision(revision)
    draft.shape = "square"
    draft.save()
    publish_revision(draft)

    with CaptureQueriesContext(connection) as queries:
        refreshed = resolve_site_config(request=HttpRequest())

    assert refreshed is not None
    assert refreshed.visual_config.shape == "square"
    assert len(queries) == 1


def test_template_tag_returns_empty_string_when_site_integration_disabled() -> None:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")

    with override_settings(DJANGO_SCROLL_TO_TOP={"SITE_ENABLED": False}):
        rendered = template.render(Context({}))

    assert rendered.strip() == ""


def test_site_is_resolved_only_when_sites_framework_is_enabled(db) -> None:
    _publish_config()
    request = HttpRequest()
    fake_site = Mock(pk=7)

    with patch(
        "django_scroll_to_top.site_config.apps.is_installed",
        return_value=True,
    ):
        with patch(
            "django.contrib.sites.shortcuts.get_current_site",
            return_value=fake_site,
        ) as getter:
            resolve_site_config(request=request)
            getter.assert_not_called()

    with override_settings(
        DJANGO_SCROLL_TO_TOP={
            "SITE_ENABLED": True,
            "SITES_FRAMEWORK_ENABLED": True,
        }
    ):
        with patch(
            "django_scroll_to_top.site_config.apps.is_installed",
            return_value=True,
        ):
            with patch(
                "django.contrib.sites.shortcuts.get_current_site",
                return_value=fake_site,
            ) as getter:
                resolved = resolve_site_config(request=request)

    assert resolved is not None
    assert resolved.site_id == 7
    getter.assert_called_once_with(request)


def test_resolve_site_config_uses_builtin_default_without_admin_record(db) -> None:
    invalidate_site_config_cache()

    resolved = resolve_site_config(request=HttpRequest())

    assert resolved is not None
    assert resolved.visual_config.icon_name == "arrow-up"
    assert resolved.visual_config.shape == "circle"


def test_configuration_error_is_logged_only_once(db, caplog) -> None:
    _publish_config(name="Broken", foreground_color="nope")
    _LOGGED_CONFIG_ERRORS.clear()

    with caplog.at_level("WARNING"):
        first = resolve_site_config(request=HttpRequest())
        second = resolve_site_config(request=HttpRequest())

    assert first is not None
    assert second is not None
    assert first.visual_config.shape == "circle"
    assert len(caplog.records) == 1


def test_system_check_reports_pending_migrations() -> None:
    with patch(
        "django_scroll_to_top.checks.MigrationExecutor",
    ) as executor_cls:
        executor = executor_cls.return_value
        migration = Mock(app_label="django_scroll_to_top")
        executor.loader.graph.leaf_nodes.return_value = [
            ("django_scroll_to_top", "0010")
        ]
        executor.migration_plan.return_value = [(migration, False)]

        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W002" for message in messages)


def test_system_check_reports_migration_inspection_failures() -> None:
    with patch(
        "django_scroll_to_top.checks.MigrationExecutor",
        side_effect=OperationalError("missing table"),
    ):
        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W001" for message in messages)


def test_system_check_reports_invalid_csp_mode(db) -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"CSP_MODE": "broken"}):
        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W003" for message in messages)


def test_system_check_reports_missing_package_urlconf(db) -> None:
    with override_settings(ROOT_URLCONF="tests.urls_without_dstt"):
        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W004" for message in messages)


def test_system_check_reports_admin_template_override_ordering(db) -> None:
    with override_settings(
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.messages",
            "django.contrib.sessions",
            "django.contrib.staticfiles",
            "django_scroll_to_top",
        ],
        DJANGO_SCROLL_TO_TOP={"ADMIN_ENABLED": True},
    ):
        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W005" for message in messages)


def test_admin_scope_uses_shared_config_and_respects_auth_page_policy(db) -> None:
    _publish_config(scope="admin", name="Admin config", shape="square")
    request = HttpRequest()
    request.user = Mock(is_authenticated=True)
    request.resolver_match = Mock(url_name="index")

    resolved = resolve_site_config(request=request, scope="admin")

    assert resolved is not None
    assert resolved.scope == "admin"
    assert resolved.site_id is None
    assert resolved.visual_config.shape == "square"

    hidden_request = HttpRequest()
    hidden_request.user = Mock(is_authenticated=False)
    hidden_request.resolver_match = Mock(url_name="login")

    hidden = resolve_site_config(request=hidden_request, scope="admin")

    assert hidden is None


def test_dynamic_stylesheet_endpoint_returns_versioned_css(db) -> None:
    _publish_config(background_color="#112233")
    client = Client()
    resolved = resolve_site_config(request=HttpRequest())

    assert resolved is not None
    response = client.get(f"/scroll-to-top/styles/{resolved.version}.css")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/css")
    assert "public" in response["Cache-Control"]
    assert "immutable" in response["Cache-Control"]
    body = response.content.decode("utf-8")
    assert f'[data-dstt-config="{resolved.version}"]' in body
    assert "--dstt-color-bg: #112233;" in body
    assert "query string" not in body


def test_dynamic_stylesheet_endpoint_rejects_unknown_versions(db) -> None:
    _publish_config()
    client = Client()

    response = client.get("/scroll-to-top/styles/unknown.css?css=body{display:none}")

    assert response.status_code == 404


def test_public_page_contract_is_compatible_with_strict_csp_headers(db) -> None:
    _publish_config()
    client = Client()

    response = client.get("/sample/")

    assert response.status_code == 200
    assert "style-src 'self'" in response["Content-Security-Policy"]
    body = response.content.decode("utf-8")
    assert ' style="' not in body
    assert "/scroll-to-top/styles/" in body
    assert 'nonce="' not in body


def test_public_page_contract_supports_nonce_mode(db) -> None:
    _publish_config()
    client = Client()

    with override_settings(DJANGO_SCROLL_TO_TOP={"CSP_MODE": "nonce"}):
        response = client.get("/sample/")

    assert response.status_code == 200
    body = response.content.decode("utf-8")
    assert 'nonce="nonce-123"' in body
