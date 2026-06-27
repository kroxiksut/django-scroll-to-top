from django.core.exceptions import ValidationError

from django_scroll_to_top.admin_preview import render_admin_preview
from django_scroll_to_top.contrast import contrast_ratio
from django_scroll_to_top.forms import ScrollToTopPreviewForm


def _valid_preview_data() -> dict[str, object]:
    return {
        "theme_mode": "manual",
        "icon_source": "builtin",
        "shape": "circle",
        "fill_variant": "solid",
        "icon_name": "arrow-up",
        "uploaded_icon": "",
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
        "dark_background_color": "#020617",
        "dark_border_color": "#cbd5e1",
        "dark_hover_foreground_color": "#f8fafc",
        "dark_hover_background_color": "#1e293b",
        "dark_hover_border_color": "#e2e8f0",
        "dark_active_foreground_color": "#f8fafc",
        "dark_active_background_color": "#334155",
        "dark_active_border_color": "#f8fafc",
        "dark_focus_ring_color": "#7dd3fc",
        "size_desktop": 52,
        "size_mobile_inherit": "on",
        "size_mobile": 48,
        "icon_size_desktop": 24,
        "icon_size_mobile_inherit": "on",
        "icon_size_mobile": 22,
    }


def test_contrast_ratio_detects_strong_contrast() -> None:
    ratio = contrast_ratio("#ffffff", "#0f172a")

    assert ratio > 10


def test_preview_form_rejects_invalid_hex_color() -> None:
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "foreground_color": "white",
        }
    )

    assert form.is_valid() is False
    assert "foreground_color" in form.errors


def test_preview_form_allows_low_contrast_colors() -> None:
    # Contrast is no longer enforced; any valid colors are accepted.
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "foreground_color": "#222222",
            "background_color": "#333333",
            "border_color": "#333333",
            "dark_foreground_color": "#222222",
            "dark_background_color": "#333333",
            "hover_foreground_color": "#2a2a2a",
            "hover_background_color": "#333333",
        }
    )

    assert form.is_valid(), form.errors


def test_contrast_skipped_for_non_surface_fill() -> None:
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "fill_variant": "outline",
            "foreground_color": "#222222",
            "background_color": "#333333",
            "border_color": "#333333",
        }
    )

    assert form.is_valid(), form.errors


def test_icon_color_override_used_for_contrast() -> None:
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "fill_variant": "solid",
            "foreground_color": "#333334",
            "background_color": "#333333",
            "border_color": "#333333",
            "icon_color": "#ffffff",
        }
    )

    assert form.is_valid(), form.errors


def test_preview_form_serializes_explicit_mobile_override() -> None:
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "shape": "rounded-square",
            "fill_variant": "soft",
            "icon_name": "circle-arrow-up",
            "icon_style": "filled",
            "corner": "top-left",
            "size_desktop": 56,
            "size_mobile_inherit": "",
            "size_mobile": 42,
            "icon_size_desktop": 24,
            "icon_size_mobile_inherit": "",
            "icon_size_mobile": 18,
        }
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()

    assert config.size.desktop_px == 56
    assert config.size.mobile_px == 42
    assert config.icon_size.mobile_px == 18


def test_admin_preview_uses_shared_renderer_markup() -> None:
    form = ScrollToTopPreviewForm(data=_valid_preview_data())

    assert form.is_valid(), form.errors
    preview = render_admin_preview(form)

    # One compact live button plus the collapsed scenario buttons.
    assert preview.count('class="dstt-control"') == 18
    assert "data-dstt-live-preview" in preview
    assert "data-dstt-live-panel" in preview
    assert 'data-dstt-preview-theme="light"' in preview
    assert 'data-dstt-preview-theme="dark"' in preview
    assert 'data-dstt-preview-viewport="mobile"' in preview
    # Hover/active/focus are driven by the live preview toolbar toggles now.
    assert 'data-dstt-preview-value="hover"' in preview
    assert 'data-dstt-preview-value="active"' in preview
    assert 'data-dstt-preview-state="focus"' in preview
    assert 'data-dstt-preview-background="mixed"' in preview
    assert 'data-dstt-debug-rects="on"' in preview
    assert 'data-dstt-obstacle="cookie-right"' in preview
    assert 'data-dstt-obstacle="mobile-nav"' in preview
    assert 'data-dstt-icon-source="builtin"' in preview
    assert 'data-dstt-theme-mode="manual"' in preview
    assert "--dstt-color-bg: #0f172a;" in preview


def test_admin_preview_uses_inherited_admin_theme_contract() -> None:
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "theme_mode": "inherit_admin_theme",
        }
    )

    assert form.is_valid(), form.errors
    preview = render_admin_preview(form)

    assert 'data-dstt-theme-mode="inherit_admin_theme"' in preview
    assert "--dstt-color-bg:" not in preview
    assert "--dstt-size: 52px;" in preview
    assert "Reduced motion" in preview
    assert "After threshold" in preview


def test_preview_form_uses_uploaded_icon_svg_override(db) -> None:
    from django_scroll_to_top.models import ScrollTopUploadedIcon

    icon = ScrollTopUploadedIcon.objects.create(
        name="uploaded-arrow",
        style_kind="outline",
        color_mode="recolor",
        author="Example",
        source_url="https://example.test/icon",
        license_name="MIT",
        rights_confirmed=True,
        original_filename="uploaded-arrow.svg",
        original_checksum="a" * 64,
        sanitized_checksum="b" * 64,
        sanitized_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M12 4v16" stroke="#112233" /></svg>'
        ),
        supports_current_color=True,
    )
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "icon_source": "uploaded",
            "uploaded_icon": icon.pk,
        }
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()

    assert config.icon_source == "uploaded"
    assert config.icon_svg_override != icon.sanitized_svg
    assert 'stroke="currentColor"' in config.icon_svg_override


def test_preview_form_preserves_uploaded_multicolor_svg(db) -> None:
    from django_scroll_to_top.models import ScrollTopUploadedIcon

    icon = ScrollTopUploadedIcon.objects.create(
        name="uploaded-multi",
        style_kind="multicolor",
        color_mode="preserve",
        author="Example",
        source_url="https://example.test/icon",
        license_name="MIT",
        rights_confirmed=True,
        original_filename="uploaded-multi.svg",
        original_checksum="a" * 64,
        sanitized_checksum="b" * 64,
        sanitized_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M0 0h24v24H0z" fill="#112233" />'
            '<path d="M12 4v16" stroke="#ff6600" /></svg>'
        ),
        supports_current_color=False,
    )
    form = ScrollToTopPreviewForm(
        data={
            **_valid_preview_data(),
            "icon_source": "uploaded",
            "uploaded_icon": icon.pk,
        }
    )

    assert form.is_valid(), form.errors
    config = form.to_visual_config()

    assert '#112233' in config.icon_svg_override
    assert '#ff6600' in config.icon_svg_override


def test_admin_preview_requires_valid_form() -> None:
    form = ScrollToTopPreviewForm(data={"shape": "circle"})

    try:
        render_admin_preview(form)
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected preview rendering to require valid form data.")
