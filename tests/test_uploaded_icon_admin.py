# ruff: noqa: I001

from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.urls import reverse

from django_scroll_to_top.admin import ScrollTopUploadedIconAdmin
from django_scroll_to_top.icons.sanitizer import MAX_SVG_BYTES
from django_scroll_to_top.models import ScrollTopUploadedIcon


VALID_UPLOADED_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M12 4v16M7 9l5-5 5 5" fill="none" stroke="currentColor" stroke-width="2"/>
</svg>
""".strip()


def test_uploaded_icon_admin_creates_sanitized_icon(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "uploaded-arrow",
            "style_kind": "outline",
            "color_mode": "recolor",
            "stroke_width_override": "1.5",
            "author": "Example Author",
            "source_name": "Example Pack",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "license_url": "https://example.test/license",
            "copyright_notice": "Copyright Example Author",
            "attribution_text": "Example Author / Example Pack",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "uploaded-arrow.svg",
                VALID_UPLOADED_SVG,
                content_type="image/svg+xml",
            ),
            "_save": "Save",
        },
    )

    assert response.status_code == 302
    icon = ScrollTopUploadedIcon.objects.get(name="uploaded-arrow")
    assert icon.original_filename == "uploaded-arrow.svg"
    assert icon.supports_current_color is True
    assert icon.supports_stroke_width is True
    assert icon.color_mode == "recolor"
    assert str(icon.stroke_width_override) == "1.50"
    assert icon.source_name == "Example Pack"
    assert icon.license_url == "https://example.test/license"
    assert icon.attribution_text == "Example Author / Example Pack"
    assert icon.original_view_box == "0 0 24 24"
    assert icon.normalized_view_box == "0 0 24 24"
    assert icon.sanitized_svg.startswith("<svg")
    assert "<script" not in icon.sanitized_svg
    assert 'stroke-width="1.5"' in icon.renderable_svg()


def test_uploaded_icon_admin_rejects_missing_rights_confirmation(
    admin_client: Client,
) -> None:
    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "uploaded-arrow",
            "style_kind": "outline",
            "color_mode": "recolor",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "upload_svg": SimpleUploadedFile(
                "uploaded-arrow.svg",
                VALID_UPLOADED_SVG,
                content_type="image/svg+xml",
            ),
        },
    )

    assert response.status_code == 200
    assert ScrollTopUploadedIcon.objects.count() == 0
    content = response.content.decode("utf-8")
    assert "You must confirm the right to use this icon." in content


def test_uploaded_icon_admin_rejects_unsafe_svg(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "uploaded-arrow",
            "style_kind": "outline",
            "color_mode": "recolor",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "uploaded-arrow.svg",
                (
                    b'<svg xmlns="http://www.w3.org/2000/svg" '
                    b'viewBox="0 0 24 24"><script/></svg>'
                ),
                content_type="image/svg+xml",
            ),
        },
    )

    assert response.status_code == 200
    assert ScrollTopUploadedIcon.objects.count() == 0
    assert "forbidden markup" in response.content.decode("utf-8").lower()


def test_uploaded_multicolor_icon_forces_preserve_mode(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "uploaded-multicolor",
            "style_kind": "multicolor",
            "color_mode": "recolor",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "uploaded-multicolor.svg",
                (
                    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                    b'<path d="M0 0h24v24H0z" fill="#112233"/>'
                    b'<path d="M12 4v16" stroke="#ff6600"/></svg>'
                ),
                content_type="image/svg+xml",
            ),
        },
    )

    assert response.status_code == 200
    assert "must preserve their safe colors" in response.content.decode("utf-8")


def test_uploaded_icon_admin_rejects_oversized_svg_before_sanitizing(
    admin_client: Client,
) -> None:
    # Padded past the package byte limit *and* deliberately unsafe. The size guard
    # in clean_upload_svg() must reject it before the SVG is read and sanitized,
    # so the size error wins over the "forbidden markup" sanitizer error.
    oversized_unsafe = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        b"<script/>"
        b"<!--" + b"a" * (MAX_SVG_BYTES + 1) + b"-->"
        b"</svg>"
    )
    assert len(oversized_unsafe) > MAX_SVG_BYTES

    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "oversized",
            "style_kind": "outline",
            "color_mode": "recolor",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "oversized.svg",
                oversized_unsafe,
                content_type="image/svg+xml",
            ),
        },
    )

    assert response.status_code == 200
    assert ScrollTopUploadedIcon.objects.count() == 0
    content = response.content.decode("utf-8").lower()
    assert "exceeds the maximum allowed size" in content
    assert "forbidden markup" not in content


def test_attribution_export_neutralizes_formula_injection(
    admin_client: Client,
) -> None:
    # Create a real, sanitized icon through the admin add flow.
    admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "uploaded-arrow",
            "style_kind": "outline",
            "color_mode": "recolor",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "uploaded-arrow.svg",
                VALID_UPLOADED_SVG,
                content_type="image/svg+xml",
            ),
        },
    )
    # Stash spreadsheet-formula payloads in admin-editable text fields, bypassing
    # form validation the way stored data would.
    ScrollTopUploadedIcon.objects.filter(name="uploaded-arrow").update(
        name="=cmd_calc",
        author="+sum",
        copyright_notice="-danger",
        attribution_text="@formula",
    )

    model_admin = ScrollTopUploadedIconAdmin(ScrollTopUploadedIcon, AdminSite())
    request = RequestFactory().get("/")
    response = model_admin.export_attribution_report(
        request, ScrollTopUploadedIcon.objects.all()
    )

    body = response.content.decode("utf-8")
    # Every formula-leading cell is prefixed with an apostrophe so spreadsheets
    # treat it as literal text, and no bare formula cell remains.
    assert "'=cmd_calc" in body
    assert "'+sum" in body
    assert "'-danger" in body
    assert "'@formula" in body
    for raw in (",=cmd_calc", ",+sum", ",-danger", ",@formula"):
        assert raw not in body


def test_uploaded_icon_admin_rejects_stroke_override_for_fixed_stroke_icon(
    admin_client: Client,
) -> None:
    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_add"),
        data={
            "name": "filled-up",
            "style_kind": "filled",
            "color_mode": "preserve",
            "stroke_width_override": "1.25",
            "author": "Example Author",
            "source_url": "https://example.test/icon",
            "license_name": "MIT",
            "rights_confirmed": "on",
            "upload_svg": SimpleUploadedFile(
                "filled-up.svg",
                (
                    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
                    b'<path d="M12 4v16" fill="#112233"/></svg>'
                ),
                content_type="image/svg+xml",
            ),
        },
    )

    assert response.status_code == 200
    assert (
        "Only uploaded icons with explicit stroke-width attributes can use a "
        "stroke width override."
    ) in response.content.decode("utf-8")
