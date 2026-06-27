from __future__ import annotations

from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import render_scroll_to_top


def test_admin_supplied_text_is_html_escaped() -> None:
    rendered = render_scroll_to_top(
        VisualConfig(
            aria_label='"><script>alert(1)</script>',
            template_variant="icon-label",
            label_text="<b>x</b>",
        )
    )

    assert "<script>alert(1)</script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "<b>x</b>" not in rendered
    assert "&lt;b&gt;x&lt;/b&gt;" in rendered


def test_unsafe_custom_css_class_cannot_break_out_of_attribute() -> None:
    rendered = render_scroll_to_top(
        VisualConfig(custom_css_class='" onmouseover="alert(1)')
    )

    assert "onmouseover" not in rendered
    # The wrapper keeps only its base class when the value is unsafe.
    assert 'class="dstt-control-wrap"' in rendered


def test_no_inline_event_or_style_attributes_in_markup() -> None:
    rendered = render_scroll_to_top(VisualConfig())

    assert "onclick=" not in rendered
    assert "onload=" not in rendered
    assert ' style="' not in rendered
    assert "javascript:" not in rendered
