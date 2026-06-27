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


# --- Renderer / template -----------------------------------------------------


def test_payload_serializes_visibility_and_scroll_fields() -> None:
    payload = build_render_payload(
        VisualConfig(
            threshold_mode="combined",
            show_after_px=300,
            show_after_viewports=1.5,
            min_document_height_px=800,
            show_delay_ms=120,
            hide_delay_ms=60,
            visibility_direction="hide_on_scroll_down",
            scroll_target_selector="#main",
            scroll_offset_px=24,
            fixed_header_selector=".site-header",
            scroll_behavior="instant",
        )
    )

    assert payload.threshold_mode == "combined"
    assert payload.show_after_px == 300
    assert payload.show_after_viewports == 1.5
    assert payload.min_document_height_px == 800
    assert payload.show_delay_ms == 120
    assert payload.hide_delay_ms == 60
    assert payload.visibility_direction == "hide_on_scroll_down"
    assert payload.scroll_target_selector == "#main"
    assert payload.scroll_offset_px == 24
    assert payload.fixed_header_selector == ".site-header"
    assert payload.scroll_behavior == "instant"


def test_payload_falls_back_on_invalid_enum_values() -> None:
    payload = build_render_payload(
        VisualConfig(
            threshold_mode="bogus",  # type: ignore[arg-type]
            visibility_direction="nope",  # type: ignore[arg-type]
            scroll_behavior="warp",  # type: ignore[arg-type]
        )
    )

    assert payload.threshold_mode == "pixels"
    assert payload.visibility_direction == "always"
    assert payload.scroll_behavior == "smooth"


def test_template_renders_visibility_and_scroll_data_attributes(db) -> None:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")

    rendered = template.render(Context({}))

    assert 'data-dstt-threshold-mode="pixels"' in rendered
    assert 'data-dstt-show-after-px="240"' in rendered
    assert "data-dstt-show-after-viewports=" in rendered
    assert 'data-dstt-visibility-direction="always"' in rendered
    assert 'data-dstt-scroll-behavior="smooth"' in rendered
    assert "data-dstt-scroll-offset=" in rendered


# --- Form / model ------------------------------------------------------------


def test_form_round_trips_visibility_and_scroll_fields(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(
            threshold_mode="viewport",
            show_after_px=320,
            show_after_viewports=2,
            min_document_height_px=600,
            show_delay_ms=80,
            hide_delay_ms=40,
            visibility_direction="scroll_up_only",
            scroll_target_selector="#content",
            scroll_offset_px=16,
            fixed_header_selector=".header",
            scroll_behavior="instant",
        )
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()
    assert config.threshold_mode == "viewport"
    assert config.show_after_px == 320
    assert config.show_after_viewports == 2
    assert config.min_document_height_px == 600
    assert config.visibility_direction == "scroll_up_only"
    assert config.scroll_target_selector == "#content"
    assert config.scroll_offset_px == 16
    assert config.fixed_header_selector == ".header"
    assert config.scroll_behavior == "instant"


def test_form_rejects_unsafe_scroll_target_selector(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(scroll_target_selector="<script>alert(1)</script>")
    )

    assert not form.is_valid()
    assert "scroll_target_selector" in form.errors


def test_form_defaults_apply_when_visibility_fields_omitted(db) -> None:
    data = _base_form_data()
    for field in (
        "threshold_mode",
        "show_after_px",
        "show_after_viewports",
        "visibility_direction",
        "scroll_behavior",
    ):
        data.pop(field, None)
    form = ScrollToTopPreviewForm(data=data)

    assert form.is_valid(), form.errors
    config = form.to_visual_config()
    assert config.threshold_mode == "pixels"
    assert config.show_after_px == 240
    assert config.scroll_behavior == "smooth"


def test_model_to_visual_config_round_trips_visibility_fields(db) -> None:
    revision = ScrollTopRevision.objects.create(
        name="vis",
        threshold_mode="combined",
        show_after_px=280,
        visibility_direction="hide_on_scroll_down",
        scroll_target_selector="#top",
        scroll_behavior="instant",
    )

    config = revision.to_visual_config()

    assert config.threshold_mode == "combined"
    assert config.show_after_px == 280
    assert config.visibility_direction == "hide_on_scroll_down"
    assert config.scroll_target_selector == "#top"
    assert config.scroll_behavior == "instant"


# --- Runtime JS contract -----------------------------------------------------


def test_runtime_uses_configurable_threshold_not_hardcoded() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "scrollY > 120" not in source
    assert "data-dstt-show-after-px" in source
    assert "data-dstt-threshold-mode" in source
    assert "thresholdReached" in source
    assert "computeShouldBeVisible" in source


def test_runtime_supports_direction_delays_and_page_marker() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "data-dstt-visibility-direction" in source
    assert "hide_on_scroll_down" in source
    assert "scroll_up_only" in source
    assert "data-dstt-show-delay" in source
    assert 'getAttribute("data-scroll-top") === "disabled"' in source


def test_runtime_scrolls_to_configurable_target_and_behavior() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "data-dstt-scroll-target" in source
    assert "data-dstt-scroll-offset" in source
    assert "data-dstt-fixed-header" in source
    assert "resolveScrollTop" in source
    assert 'scrollBehavior === "instant"' in source
    assert "focusTarget" in source
