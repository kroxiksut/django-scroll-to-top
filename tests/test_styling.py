from __future__ import annotations

from pathlib import Path

from django.template import Context, Template

from django_scroll_to_top.forms import ScrollToTopPreviewForm
from django_scroll_to_top.models import ScrollTopRevision
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload
from django_scroll_to_top.styles import build_component_stylesheet, build_style_token

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


# --- Renderer ----------------------------------------------------------------


def test_payload_accepts_new_shapes_and_fills() -> None:
    payload = build_render_payload(
        VisualConfig(shape="pill", fill_variant="gradient", shadow_preset="large")
    )

    assert payload.shape == "pill"
    assert payload.fill_variant == "gradient"
    assert payload.shadow_preset == "large"


def test_payload_falls_back_on_invalid_shadow() -> None:
    payload = build_render_payload(VisualConfig(shadow_preset="huge"))  # type: ignore[arg-type]

    assert payload.shadow_preset == "medium"


def test_template_renders_shadow_attribute(db) -> None:
    rendered = Template("{% load scroll_to_top %}{% scroll_to_top %}").render(
        Context({})
    )

    assert 'data-dstt-shadow="medium"' in rendered


def test_payload_maps_hot_zone_fields() -> None:
    payload = build_render_payload(
        VisualConfig(
            hot_zone_placement="right",
            hot_zone_width=160,
            hot_zone_appearance="visible",
        )
    )

    assert payload.hot_zone_placement == "right"
    assert payload.hot_zone_width == 160
    assert payload.hot_zone_appearance == "visible"


def test_payload_falls_back_on_invalid_hot_zone_values() -> None:
    payload = build_render_payload(
        VisualConfig(
            hot_zone_placement="middle",  # type: ignore[arg-type]
            hot_zone_appearance="glow",  # type: ignore[arg-type]
        )
    )

    assert payload.hot_zone_placement == "none"
    assert payload.hot_zone_appearance == "hover"


def test_hot_zone_button_placement_resolves_to_corner_side() -> None:
    right = build_render_payload(
        VisualConfig(hot_zone_placement="button", corner="bottom-right")
    )
    left = build_render_payload(
        VisualConfig(hot_zone_placement="button", corner="top-left")
    )

    assert right.hot_zone_placement == "right"
    assert left.hot_zone_placement == "left"


def test_icon_color_override_emitted_only_when_set() -> None:
    with_override = build_component_stylesheet(
        config=VisualConfig(icon_color="#abcdef", dark_icon_color="#123456"),
        selector=".sel",
    )
    without_override = build_component_stylesheet(
        config=VisualConfig(),
        selector=".sel",
    )

    assert "--dstt-icon-color: #abcdef;" in with_override
    assert "--dstt-icon-color-dark: #123456;" in with_override
    assert "--dstt-icon-color:" not in without_override


def test_component_stylesheet_emits_hot_zone_width() -> None:
    css = build_component_stylesheet(
        config=VisualConfig(hot_zone_width=160),
        selector=".sel",
    )

    assert "--dstt-hot-zone-width: 160px;" in css


def test_template_renders_hot_zone_attributes(db) -> None:
    config = ScrollTopRevision.objects.create(
        name="Hot zone",
        hot_zone_placement="left",
        hot_zone_appearance="visible",
    )
    payload = config.to_visual_config()
    rendered = build_render_payload(payload)

    assert rendered.hot_zone_placement == "left"
    assert rendered.hot_zone_appearance == "visible"


# --- Stylesheet endpoint -----------------------------------------------------


def test_component_stylesheet_emits_styling_variables() -> None:
    css = build_component_stylesheet(
        config=VisualConfig(
            opacity=0.5,
            border_width=2,
            focus_ring_width=4,
            focus_ring_offset=5,
            gradient_start_color="#123456",
            gradient_end_color="#654321",
            gradient_angle=90,
            backdrop_blur=12,
        ),
        selector=".x",
    )

    assert "--dstt-opacity: 0.5;" in css
    assert "--dstt-border-width: 2px;" in css
    assert "--dstt-focus-ring-width: 4px;" in css
    assert "--dstt-focus-ring-offset: 5px;" in css
    assert "--dstt-gradient-start: #123456;" in css
    assert "--dstt-gradient-end: #654321;" in css
    assert "--dstt-gradient-angle: 90deg;" in css
    assert "--dstt-backdrop-blur: 12px;" in css


def test_style_token_changes_with_styling_fields() -> None:
    base = build_style_token(VisualConfig())
    assert base != build_style_token(VisualConfig(shadow_preset="large"))
    assert base != build_style_token(VisualConfig(opacity=0.4))
    assert base != build_style_token(VisualConfig(gradient_angle=10))


# --- CSS contract ------------------------------------------------------------


def test_css_styles_new_shapes_fills_and_shadows() -> None:
    css = (_STATIC / "scroll-to-top.css").read_text(encoding="utf-8")

    assert '[data-dstt-shape="pill"]' in css
    assert '[data-dstt-fill="ghost"]' in css
    assert '[data-dstt-fill="glass"]' in css
    assert '[data-dstt-fill="gradient"]' in css
    assert '[data-dstt-shadow="none"]' in css
    assert "linear-gradient(" in css
    assert "backdrop-filter" in css
    assert "var(--dstt-opacity" in css
    assert "var(--dstt-border-width" in css
    assert "var(--dstt-focus-ring-width" in css


# --- Form / model ------------------------------------------------------------


def test_form_round_trips_styling_fields(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(
            shape="pill",
            fill_variant="gradient",
            shadow_preset="large",
            opacity=0.8,
            border_width=2,
            focus_ring_width=4,
            focus_ring_offset=5,
            gradient_start_color="#112233",
            gradient_end_color="#445566",
            gradient_angle=200,
            backdrop_blur=14,
        )
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()
    assert config.shape == "pill"
    assert config.fill_variant == "gradient"
    assert config.shadow_preset == "large"
    assert config.opacity == 0.8
    assert config.border_width == 2
    assert config.gradient_start_color == "#112233"
    assert config.gradient_angle == 200
    assert config.backdrop_blur == 14


def test_form_rejects_invalid_gradient_color(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(fill_variant="gradient", gradient_start_color="nope")
    )

    assert not form.is_valid()
    assert "gradient_start_color" in form.errors


def test_model_round_trips_styling_fields(db) -> None:
    revision = ScrollTopRevision.objects.create(
        name="styled",
        shape="pill",
        fill_variant="glass",
        shadow_preset="small",
        opacity=0.9,
        border_width=3,
        gradient_start_color="#0a0a0a",
        gradient_end_color="#f0f0f0",
        backdrop_blur=20,
    )

    config = revision.to_visual_config()

    assert config.shape == "pill"
    assert config.fill_variant == "glass"
    assert config.shadow_preset == "small"
    assert config.opacity == 0.9
    assert config.border_width == 3
    assert config.backdrop_blur == 20
