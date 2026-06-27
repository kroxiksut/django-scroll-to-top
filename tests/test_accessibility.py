from __future__ import annotations

from pathlib import Path

from django.template import Context, Template

from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import render_scroll_to_top

_STATIC = Path("src/django_scroll_to_top/static/django_scroll_to_top")


def _render(**overrides) -> str:
    return render_scroll_to_top(VisualConfig(**overrides))


def test_control_has_accessible_name_independent_of_icon() -> None:
    rendered = _render(aria_label="Back to the top")

    assert 'aria-label="Back to the top"' in rendered


def test_decorative_icon_is_hidden_from_assistive_tech() -> None:
    rendered = _render()

    assert 'aria-hidden="true"' in rendered
    assert 'focusable="false"' in rendered


def test_dismiss_control_has_distinct_localized_accessible_name() -> None:
    rendered = _render(allow_user_dismissal=True)

    assert "data-dstt-dismiss-control" in rendered
    # The close control carries its own accessible name from the renderer
    # payload (translatable), distinct from the main control's label.
    assert 'aria-label="Hide the scroll-to-top button"' in rendered


def test_no_javascript_fallback_is_a_real_link() -> None:
    rendered = _render()

    assert 'class="dstt-control"' in rendered
    assert 'href="#"' in rendered
    assert "javascript:" not in rendered


def test_markup_uses_no_positive_tabindex(db) -> None:
    rendered = Template("{% load scroll_to_top %}{% scroll_to_top %}").render(
        Context({})
    )

    assert "tabindex=" not in rendered


def test_css_provides_visible_focus_and_target_floor() -> None:
    css = (_STATIC / "scroll-to-top.css").read_text(encoding="utf-8")

    assert ".dstt-control:focus-visible" in css
    assert "outline:" in css
    assert "min-inline-size: 24px;" in css
    assert "min-block-size: 24px;" in css


def test_css_honors_forced_colors_reduced_motion_and_rtl_logical_props() -> None:
    css = (_STATIC / "scroll-to-top.css").read_text(encoding="utf-8")

    assert "@media (forced-colors: active)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    # Logical properties keep the control correct under RTL.
    assert "inset-inline-end" in css
    assert "padding-inline" in css


def test_runtime_focus_does_not_move_to_body_and_honors_reduced_motion() -> None:
    source = (_STATIC / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "prefers-reduced-motion" in source
    assert "preventScroll" in source
    # Focus is only moved to a resolved target, never forced onto the body.
    assert "document.body.focus" not in source
