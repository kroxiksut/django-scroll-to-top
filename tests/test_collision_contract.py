from __future__ import annotations

from pathlib import Path

from django.core.checks import run_checks
from django.template import Context, Template
from django.test.utils import override_settings

from django_scroll_to_top.forms import (
    ScrollToTopPreviewForm,
    parse_fallback_corner_order,
    parse_obstacle_selectors,
)
from django_scroll_to_top.models import ScrollTopRevision
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload
from django_scroll_to_top.settings import get_scroll_to_top_settings

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


# --- Renderer / template contract -------------------------------------------


def test_payload_serializes_collision_fields() -> None:
    payload = build_render_payload(
        VisualConfig(
            collision_policy="shift",
            obstacle_selectors=(".cookie-banner", "#chat"),
            obstacle_gap=20,
            collision_max_shift=180,
            fallback_corner_order=("bottom-left", "top-right"),
        )
    )

    assert payload.collision_policy == "shift"
    assert payload.obstacle_selectors_json == '[".cookie-banner","#chat"]'
    assert payload.obstacle_gap == 20
    assert payload.collision_max_shift == 180
    assert payload.fallback_corner_order_json == '["bottom-left","top-right"]'


def test_default_payload_ignores_collisions() -> None:
    payload = build_render_payload()

    assert payload.collision_policy == "ignore"
    assert payload.obstacle_selectors_json == "[]"
    assert payload.fallback_corner_order_json == "[]"


def test_unknown_policy_falls_back_to_ignore() -> None:
    payload = build_render_payload(VisualConfig(collision_policy="bogus"))  # type: ignore[arg-type]

    assert payload.collision_policy == "ignore"


def test_invalid_fallback_corner_is_dropped_from_payload() -> None:
    payload = build_render_payload(
        VisualConfig(fallback_corner_order=("bottom-left", "nope"))  # type: ignore[arg-type]
    )

    assert payload.fallback_corner_order_json == '["bottom-left"]'


def test_template_renders_collision_data_attributes(db) -> None:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")

    rendered = template.render(Context({}))

    assert 'data-dstt-collision-policy="ignore"' in rendered
    assert 'data-dstt-obstacle-gap="12"' in rendered
    assert 'data-dstt-collision-max-shift="240"' in rendered
    # JSON list is HTML-escaped inside the attribute.
    assert "data-dstt-obstacle-selectors=" in rendered
    assert "data-dstt-fallback-corners=" in rendered


# --- Form validation and resolution -----------------------------------------


@override_settings(DJANGO_SCROLL_TO_TOP={"DEFAULT_COLLISION_POLICY": "shift"})
def test_form_resolves_inherit_to_module_default(db) -> None:
    form = ScrollToTopPreviewForm(data=_base_form_data(collision_policy="inherit"))

    assert form.is_valid(), form.errors
    assert form.to_visual_config().collision_policy == "shift"


def test_form_explicit_policy_overrides_module_default(db) -> None:
    form = ScrollToTopPreviewForm(data=_base_form_data(collision_policy="hide"))

    assert form.is_valid(), form.errors
    assert form.to_visual_config().collision_policy == "hide"


def test_form_rejects_unsafe_obstacle_selector(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(obstacle_selectors="<script>alert(1)</script>")
    )

    assert not form.is_valid()
    assert "obstacle_selectors" in form.errors


def test_form_accepts_and_parses_safe_selectors(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(obstacle_selectors=".cookie-banner\n#chat\n.cookie-banner")
    )

    assert form.is_valid(), form.errors
    assert form.to_visual_config().obstacle_selectors == (".cookie-banner", "#chat")


def test_form_parses_fallback_corner_order_dedupes_and_filters(db) -> None:
    form = ScrollToTopPreviewForm(
        data=_base_form_data(
            collision_policy="fallback_corner",
            fallback_corner_order="bottom-left, bogus top-right bottom-left",
        )
    )

    assert form.is_valid(), form.errors
    assert form.to_visual_config().fallback_corner_order == (
        "bottom-left",
        "top-right",
    )


def test_model_to_visual_config_round_trips_collision_fields(db) -> None:
    config = ScrollTopRevision.objects.create(
        name="with-collision",
        collision_policy="shift",
        obstacle_selectors=".cookie-banner\n#chat",
        obstacle_gap=18,
        collision_max_shift=160,
        fallback_corner_order="top-right",
    )

    visual = config.to_visual_config()

    assert visual.collision_policy == "shift"
    assert visual.obstacle_selectors == (".cookie-banner", "#chat")
    assert visual.obstacle_gap == 18
    assert visual.collision_max_shift == 160
    assert visual.fallback_corner_order == ("top-right",)


def test_selector_parser_strips_and_dedupes() -> None:
    assert parse_obstacle_selectors("  .a \n\n .b \n.a ") == [".a", ".b"]


def test_fallback_corner_parser_keeps_only_valid_corners() -> None:
    assert parse_fallback_corner_order("top-left x bottom-right top-left") == [
        "top-left",
        "bottom-right",
    ]


# --- Settings and system checks ---------------------------------------------


def test_default_collision_policy_defaults_to_ignore() -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={}):
        assert get_scroll_to_top_settings().default_collision_policy == "ignore"


def test_invalid_default_collision_policy_falls_back_to_ignore() -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"DEFAULT_COLLISION_POLICY": "bogus"}):
        assert get_scroll_to_top_settings().default_collision_policy == "ignore"


def test_system_check_reports_invalid_default_collision_policy(db) -> None:
    with override_settings(DJANGO_SCROLL_TO_TOP={"DEFAULT_COLLISION_POLICY": "bogus"}):
        messages = run_checks(tags=["models"])

    assert any(message.id == "dstt.W006" for message in messages)


# --- CSS and JS asset contract ----------------------------------------------


def test_css_applies_collision_shift_variables() -> None:
    css = (_STATIC / "scroll-to-top.css").read_text(encoding="utf-8")

    assert "--dstt-collision-shift-x:" in css
    assert "--dstt-collision-shift-y:" in css
    assert "transform: translate(" in css


def test_runtime_implements_collision_detection_and_observers() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "collectObstacles" in source
    assert "[data-scroll-top-obstacle]" in source
    assert "getBoundingClientRect" in source
    assert "ResizeObserver" in source
    assert "fallback_corner" in source
    # Guards against the observer -> style -> observer feedback loop.
    assert "selfMutating" in source


def test_runtime_supports_marker_priority_and_gap_overrides() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "data-scroll-top-obstacle-gap" in source
    assert "data-scroll-top-obstacle-priority" in source
    # Deterministic ordering by priority.
    assert "b.priority - a.priority" in source


def test_runtime_supports_collision_debug_overlays() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "renderDebugOverlays" in source
    assert "dstt-obstacle-debug" in source
    assert "data-dstt-collision-debug" in source
    assert "globalApi.debug" in source


def test_css_styles_collision_debug_overlay() -> None:
    css = (_STATIC / "scroll-to-top.css").read_text(encoding="utf-8")

    assert ".dstt-obstacle-debug" in css
    assert "pointer-events: none;" in css
