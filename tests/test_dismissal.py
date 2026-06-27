from __future__ import annotations

from pathlib import Path

from django.template import Context, Template

from django_scroll_to_top.forms import ScrollToTopPreviewForm
from django_scroll_to_top.models import ScrollTopRevision
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload

_STATIC = Path("src/django_scroll_to_top/static/django_scroll_to_top")


def _base_form_data(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "theme_mode": "manual",
        "icon_source": "builtin",
        "shape": "circle",
        "fill_variant": "solid",
        "icon_name": "arrow-up",
        "icon_style": "outline",
        "corner": "bottom-right",
        "foreground_color": "#ffffff",
        "background_color": "#0f172a",
        "border_color": "#0f172a",
        "hover_foreground_color": "#ffffff",
        "hover_background_color": "#1e293b",
        "hover_border_color": "#1e293b",
        "active_foreground_color": "#ffffff",
        "active_background_color": "#334155",
        "active_border_color": "#334155",
        "focus_ring_color": "#38bdf8",
        "dark_foreground_color": "#f8fafc",
        "dark_background_color": "#0f172a",
        "dark_border_color": "#cbd5e1",
        "dark_hover_foreground_color": "#f8fafc",
        "dark_hover_background_color": "#1e293b",
        "dark_hover_border_color": "#e2e8f0",
        "dark_active_foreground_color": "#f8fafc",
        "dark_active_background_color": "#334155",
        "dark_active_border_color": "#f8fafc",
        "dark_focus_ring_color": "#7dd3fc",
        "size_desktop": 52,
        "size_mobile_inherit": True,
        "size_mobile": 48,
        "icon_size_desktop": 24,
        "icon_size_mobile_inherit": True,
        "icon_size_mobile": 22,
    }
    data.update(overrides)
    return data


def test_payload_serializes_dismissal_fields() -> None:
    payload = build_render_payload(
        VisualConfig(
            allow_user_dismissal=True,
            dismissal_storage="cookie",
            dismissal_duration="days",
            dismissal_days=14,
            dismissal_requires_confirmation=True,
            dismissal_version="3",
        )
    )

    assert payload.dismissal_storage == "cookie"
    assert payload.dismissal_duration == "days"
    assert payload.dismissal_days == 14
    assert payload.dismissal_requires_confirmation is True
    assert payload.dismissal_version == "3"
    assert payload.dismiss_confirm_text


def test_payload_falls_back_on_invalid_dismissal_enums() -> None:
    payload = build_render_payload(
        VisualConfig(
            dismissal_storage="floppy",  # type: ignore[arg-type]
            dismissal_duration="forever",  # type: ignore[arg-type]
        )
    )

    assert payload.dismissal_storage == "local"
    assert payload.dismissal_duration == "persistent"


def _render_payload(payload) -> str:
    return Template(
        "{% include 'django_scroll_to_top/scroll_to_top.html' %}"
    ).render(Context({"scroll_to_top": payload}))


def test_template_renders_dismissal_attributes_and_control() -> None:
    rendered = _render_payload(
        build_render_payload(VisualConfig(allow_user_dismissal=True))
    )

    assert 'data-dstt-allow-dismissal="true"' in rendered
    assert 'data-dstt-dismissal-storage="local"' in rendered
    assert 'data-dstt-dismissal-duration="persistent"' in rendered
    assert "data-dstt-dismissal-days=" in rendered
    assert "data-dstt-dismiss-confirm-text=" in rendered
    assert "data-dstt-dismiss-control" in rendered


def test_dismiss_control_is_off_by_default() -> None:
    rendered = _render_payload(build_render_payload(VisualConfig()))

    assert 'data-dstt-allow-dismissal="false"' in rendered
    assert "data-dstt-dismiss-control" not in rendered


def test_template_hides_control_when_dismissal_disabled(db) -> None:
    revision = ScrollTopRevision.objects.create(
        name="no-dismiss",
        allow_user_dismissal=False,
    )
    payload = build_render_payload(revision.to_visual_config())
    rendered = Template(
        "{% include 'django_scroll_to_top/scroll_to_top.html' %}"
    ).render(Context({"scroll_to_top": payload}))

    assert 'data-dstt-allow-dismissal="false"' in rendered
    assert "data-dstt-dismiss-control" not in rendered


def test_form_round_trips_dismissal_fields(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(
            allow_user_dismissal=True,
            dismissal_storage="cookie",
            dismissal_duration="days",
            dismissal_days=21,
            dismissal_requires_confirmation=True,
            dismissal_version="7",
        )
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()
    assert config.allow_user_dismissal is True
    assert config.dismissal_storage == "cookie"
    assert config.dismissal_duration == "days"
    assert config.dismissal_days == 21
    assert config.dismissal_requires_confirmation is True
    assert config.dismissal_version == "7"


def test_model_to_visual_config_round_trips_dismissal_fields(db) -> None:
    revision = ScrollTopRevision.objects.create(
        name="dismiss",
        dismissal_storage="session",
        dismissal_duration="days",
        dismissal_days=10,
        dismissal_requires_confirmation=True,
        dismissal_version="2",
    )

    config = revision.to_visual_config()

    assert config.dismissal_storage == "session"
    assert config.dismissal_duration == "days"
    assert config.dismissal_days == 10
    assert config.dismissal_requires_confirmation is True
    assert config.dismissal_version == "2"


# --- Runtime JS contract -----------------------------------------------------


def test_runtime_supports_cookie_storage_and_expiry() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "cookieStorage" in source
    assert 'dismissalStorageMode === "cookie"' in source
    assert "until:" in source
    assert "data-dstt-dismissal-days" in source
    assert "SameSite=Lax" in source


def test_runtime_supports_dismissal_confirmation_and_restore() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "dismissalRequiresConfirmation" in source
    assert "window.confirm" in source
    assert "function restore" in source
    assert '"djstt:dismiss"' in source
    assert '"djstt:restore"' in source


def test_runtime_dismissal_key_is_namespaced_and_storage_failsafe() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "dismissalStorageKey" in source
    assert "data-dstt-dismissal-version" in source
    # Storage access is wrapped so SecurityError/denied storage cannot break it.
    assert "catch (error)" in source
