# ruff: noqa: I001

import pytest


VALID_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M12 4v16M7 9l5-5 5 5" fill="none" stroke="currentColor" stroke-width="2"/>
</svg>
""".strip()


@pytest.mark.parametrize(
    "payload",
    [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            "<script />"
            "</svg>"
        ),
        (
            "<!DOCTYPE svg>"
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"></svg>'
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            "<foreignObject />"
            "</svg>"
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path onclick="alert(1)" d="M0 0" />'
            "</svg>"
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path href="https://bad.test/x.svg" d="M0 0" />'
            "</svg>"
        ),
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path style="fill:red" d="M0 0" />'
            "</svg>"
        ),
    ],
)
def test_sanitize_uploaded_svg_rejects_forbidden_payloads(payload: str) -> None:
    sanitizer = __import__("importlib").import_module(
        "django_scroll_to_top.icons.sanitizer"
    )

    with pytest.raises(sanitizer.SvgSanitizationError):
        sanitizer.sanitize_uploaded_svg(payload)


def test_sanitize_uploaded_svg_normalizes_safe_payload() -> None:
    sanitizer = __import__("importlib").import_module(
        "django_scroll_to_top.icons.sanitizer"
    )

    sanitized_svg = sanitizer.sanitize_uploaded_svg(VALID_SVG)

    assert sanitized_svg.svg.startswith("<svg")
    assert 'xmlns="http://www.w3.org/2000/svg"' in sanitized_svg.svg
    assert "currentColor" in sanitized_svg.svg
    assert sanitized_svg.uses_current_color is True
    assert sanitized_svg.supports_stroke_width is True
    assert sanitized_svg.original_view_box == "0 0 24 24"
    assert sanitized_svg.normalized_view_box == "0 0 24 24"
    assert sanitized_svg.original_checksum != sanitized_svg.sanitized_checksum


def test_sanitize_uploaded_svg_normalizes_view_box() -> None:
    sanitizer = __import__("importlib").import_module(
        "django_scroll_to_top.icons.sanitizer"
    )

    sanitized_svg = sanitizer.sanitize_uploaded_svg(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0, 0, 24.0, 24">'
        '<path d="M12 4v16" stroke="currentColor" stroke-width="2"/>'
        "</svg>"
    )

    assert sanitized_svg.original_view_box == "0, 0, 24.0, 24"
    assert sanitized_svg.normalized_view_box == "0 0 24 24"
    assert 'viewBox="0 0 24 24"' in sanitized_svg.svg


def test_uploaded_icon_registry_returns_sanitized_svg_only() -> None:
    registry = __import__("importlib").import_module(
        "django_scroll_to_top.icons.registry"
    )

    registry.register_uploaded_icon(
        name="uploaded-up",
        style="outline",
        raw_svg=VALID_SVG,
    )

    icon = registry.resolve_icon(name="uploaded-up", style="outline", source="uploaded")

    assert icon.source == "uploaded"
    assert "<script" not in icon.svg
    assert "currentColor" in icon.svg


def test_recolor_svg_rewrites_visible_strokes_to_current_color() -> None:
    recolor = __import__("importlib").import_module(
        "django_scroll_to_top.icons.recolor"
    )

    result = recolor.recolor_svg(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M12 4v16" stroke="#112233" fill="none" stroke-width="2"/>'
            "</svg>"
        ),
        style_kind="outline",
    )

    assert 'stroke="currentColor"' in result
    assert 'fill="none"' in result
    assert "#112233" not in result


def test_recolor_svg_rewrites_visible_fills_to_current_color() -> None:
    recolor = __import__("importlib").import_module(
        "django_scroll_to_top.icons.recolor"
    )

    result = recolor.recolor_svg(
        (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M12 4v16" fill="#112233"/>'
            "</svg>"
        ),
        style_kind="filled",
    )

    assert 'fill="currentColor"' in result
    assert "#112233" not in result


def test_recolor_svg_rejects_outline_icon_without_visible_stroke() -> None:
    recolor = __import__("importlib").import_module(
        "django_scroll_to_top.icons.recolor"
    )

    with pytest.raises(recolor.SvgRecolorError):
        recolor.recolor_svg(
            (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                '<path d="M12 4v16" fill="#112233"/>'
                "</svg>"
            ),
            style_kind="outline",
        )
