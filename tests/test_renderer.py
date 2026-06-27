from django.template import Context, Template

from django_scroll_to_top.presentation import ResponsiveLength, VisualConfig
from django_scroll_to_top.renderer import (
    build_render_context,
    build_render_payload,
    render_scroll_to_top,
)
from django_scroll_to_top.styles import build_component_stylesheet


def test_render_payload_decorates_svg_and_serializes_mobile_overrides() -> None:
    payload = build_render_payload(
        VisualConfig(
            shape="rounded-square",
            fill_variant="soft",
            icon_name="circle-arrow-up",
            icon_style="filled",
            corner="top-left",
            size=ResponsiveLength(desktop_px=56, mobile_px=44),
            icon_size=ResponsiveLength(desktop_px=24, mobile_px=20),
        )
    )

    assert payload.shape == "rounded-square"
    assert payload.fill_variant == "soft"
    assert payload.corner == "top-left"
    assert 'aria-hidden="true"' in payload.icon_svg
    assert len(payload.style_token) == 12
    assert payload.contract_version == "1"


def test_template_tag_includes_assets_only_once_per_template_render(db) -> None:
    template = Template(
        "{% load scroll_to_top %}{% scroll_to_top %}{% scroll_to_top %}"
    )

    rendered = template.render(Context({}))

    assert rendered.count("scroll-to-top.min.css") == 1
    assert rendered.count("/scroll-to-top/styles/") == 1
    assert rendered.count("scroll-to-top.min.js") == 1
    assert rendered.count('class="dstt-control"') == 1
    # No standalone HTML id attribute (data-*-id attributes are allowed).
    assert ' id="' not in rendered


def test_template_tag_renders_icon_and_accessible_name(db) -> None:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")

    rendered = template.render(Context({}))

    assert 'href="#"' in rendered
    assert 'aria-label="Scroll back to top"' in rendered
    assert 'data-dstt-contract-version="1"' in rendered
    assert 'data-dstt-shape="circle"' in rendered
    assert 'data-dstt-corner="bottom-right"' in rendered
    assert 'data-dstt-icon="arrow-up"' in rendered
    assert 'data-dstt-config="' in rendered
    assert "dstt-icon-svg" in rendered
    assert "javascript:" not in rendered
    assert "onclick=" not in rendered
    assert "tabindex=" not in rendered
    assert ' style="' not in rendered


def test_template_tag_library_can_be_loaded_explicitly() -> None:
    template = Template("{% load scroll_to_top %}")

    rendered = template.render(Context({}))

    assert rendered == ""


def test_template_tag_accepts_diagnostic_scope_keyword(db) -> None:
    template = Template('{% load scroll_to_top %}{% scroll_to_top scope="site" %}')

    rendered = template.render(Context({}))

    assert 'class="dstt-control"' in rendered


def test_template_tag_accepts_admin_scope_keyword(db) -> None:
    template = Template('{% load scroll_to_top %}{% scroll_to_top scope="admin" %}')

    rendered = template.render(
        Context(
            {
                "request": type(
                    "Request",
                    (),
                    {
                        "resolver_match": type(
                            "ResolverMatch",
                            (),
                            {"url_name": "index"},
                        )(),
                        "user": type(
                            "User",
                            (),
                            {"is_authenticated": True},
                        )(),
                    },
                )(),
            }
        )
    )

    assert 'class="dstt-control"' in rendered


def test_renderer_context_is_typed_and_supports_visible_label_variant() -> None:
    context = build_render_context(
        VisualConfig(
            template_variant="icon-label",
            label_text="Back to top",
        )
    )

    assert context.scroll_to_top.template_variant == "icon-label"
    assert context.scroll_to_top.label_text == "Back to top"


def test_renderer_normalizes_unchecked_values_before_data_attributes() -> None:
    payload = build_render_payload(
        VisualConfig(
            shape="triangle",  # type: ignore[arg-type]
            fill_variant="plaid",  # type: ignore[arg-type]
            corner="center",  # type: ignore[arg-type]
        )
    )

    assert payload.shape == "circle"
    assert payload.fill_variant == "solid"
    assert payload.corner == "bottom-right"


def test_renderer_supports_visible_label_markup() -> None:
    rendered = render_scroll_to_top(
        VisualConfig(
            template_variant="icon-label",
            label_text="Back to top",
        )
    )

    assert 'data-dstt-template="icon-label"' in rendered
    assert "Back to top" in rendered


def test_renderer_serializes_theme_mode_data_attribute() -> None:
    rendered = render_scroll_to_top(
        VisualConfig(
            theme_mode="inherit_admin_theme",
        )
    )

    assert 'data-dstt-theme-mode="inherit_admin_theme"' in rendered


def test_stylesheet_omits_saved_palette_when_inheriting_admin_theme() -> None:
    stylesheet = build_component_stylesheet(
        config=VisualConfig(theme_mode="inherit_admin_theme"),
        selector=".dstt-control",
    )

    assert "--dstt-size: 52px;" in stylesheet
    assert "--dstt-color-bg:" not in stylesheet


def test_css_keeps_visible_focus_outline() -> None:
    from pathlib import Path

    css = Path(
        "src/django_scroll_to_top/static/django_scroll_to_top/scroll-to-top.css"
    ).read_text(encoding="utf-8")

    assert ".dstt-control:focus-visible" in css
    assert "outline:" in css


def test_template_tag_adds_nonce_to_script_when_nonce_mode_is_enabled(db) -> None:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")

    rendered = template.render(
        Context({"csp_nonce": "nonce-123"}),
    )

    assert 'nonce="' not in rendered

    from django.test.utils import override_settings

    with override_settings(DJANGO_SCROLL_TO_TOP={"CSP_MODE": "nonce"}):
        rendered = template.render(Context({"csp_nonce": "nonce-123"}))

    assert 'nonce="nonce-123"' in rendered
