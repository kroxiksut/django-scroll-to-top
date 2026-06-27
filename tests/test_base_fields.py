from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.template import Context, Template

from django_scroll_to_top.models import ScrollTopRevision
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload, render_scroll_to_top


def test_template_variant_and_label_render() -> None:
    rendered = render_scroll_to_top(
        VisualConfig(template_variant="icon-label", label_text="Back to top")
    )

    assert 'data-dstt-template="icon-label"' in rendered
    assert "Back to top" in rendered


def test_aria_label_override_is_used() -> None:
    rendered = render_scroll_to_top(VisualConfig(aria_label="Jump to top"))

    assert 'aria-label="Jump to top"' in rendered


def test_custom_css_class_is_added_to_wrapper() -> None:
    payload = build_render_payload(VisualConfig(custom_css_class="theme-x integration"))

    assert payload.custom_css_class == "theme-x integration"
    rendered = Template(
        "{% include 'django_scroll_to_top/scroll_to_top.html' %}"
    ).render(Context({"scroll_to_top": payload}))
    assert 'class="dstt-control-wrap theme-x integration"' in rendered


def test_renderer_drops_unsafe_custom_css_class() -> None:
    payload = build_render_payload(
        VisualConfig(custom_css_class="evil\" onload=alert(1)")
    )

    assert payload.custom_css_class == ""


def test_model_validates_custom_css_class(db) -> None:
    revision = ScrollTopRevision(name="bad", custom_css_class="<script>")
    with pytest.raises(ValidationError):
        revision.full_clean()


def test_model_accepts_safe_custom_css_class(db) -> None:
    revision = ScrollTopRevision.objects.create(
        name="ok",
        template_variant="icon-label",
        aria_label="Top",
        label_text="Top",
        custom_css_class="my-theme dstt-extra",
    )
    config = revision.to_visual_config()

    assert config.template_variant == "icon-label"
    assert config.aria_label == "Top"
    assert config.label_text == "Top"
    assert config.custom_css_class == "my-theme dstt-extra"


def test_empty_aria_label_falls_back_to_default(db) -> None:
    revision = ScrollTopRevision.objects.create(name="default-label")
    config = revision.to_visual_config()

    assert config.aria_label == VisualConfig().aria_label
