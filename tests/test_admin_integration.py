
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from django_scroll_to_top.admin import ScrollTopRevisionAdminForm
from django_scroll_to_top.icons.registry import register_developer_icon
from django_scroll_to_top.models import (
    ScrollTopProfile,
    ScrollTopRevision,
    ScrollTopUploadedIcon,
)
from django_scroll_to_top.services import publish_revision


def _publish_admin_config(name: str) -> ScrollTopRevision:
    profile = ScrollTopProfile.objects.create(scope="admin", name=name)
    revision = ScrollTopRevision.objects.create(profile=profile, name=name)
    publish_revision(revision)
    return revision


def test_admin_change_form_renders_live_preview(admin_client: Client) -> None:
    config = ScrollTopRevision.objects.create(name="Default preview")

    response = admin_client.get(_change_url(config.pk))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Live preview" in content
    assert "Icon picker" in content
    assert 'data-dstt-preview-theme="light"' in content
    assert 'class="dstt-control"' in content
    assert "Four corners" in content
    assert "Cookie banner collision" in content
    assert "Reduced motion preview" in content
    assert "admin-icon-picker.js" in content
    assert "admin-icon-picker.css" in content
    assert 'data-dstt-picker-card' in content
    assert "Metadata" in content
    assert "Built-in Tabler icons" in content
    assert "Simple upward arrow with minimal chrome." in content
    assert "outline · arrow, up, minimal" in content
    assert "Created at" in content
    assert "Updated at" in content
    # Shape and fill are now compact native dropdowns rather than choice cards.
    assert 'data-dstt-live-preview' in content
    assert 'name="shape"' in content
    assert 'name="fill_variant"' in content


def test_admin_change_form_marks_selected_shape_and_fill_options(
    admin_client: Client,
) -> None:
    config = ScrollTopRevision.objects.create(
        name="Styled preview",
        shape="rounded-square",
        fill_variant="soft",
    )

    response = admin_client.get(_change_url(config.pk))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<option value="rounded-square" selected>' in content
    assert '<option value="soft" selected>' in content


def test_admin_change_form_renders_developer_icon_picker_card(
    admin_client: Client,
) -> None:
    register_developer_icon(
        name="brand-up",
        style="outline",
        svg='<svg viewBox="0 0 24 24"><path d="M12 3v18" /></svg>',
        display_name="Brand Up",
        short_description="Project-specific icon for branded surfaces.",
        tags=("brand", "custom", "up"),
        admin_group="Project icons",
    )
    config = ScrollTopRevision.objects.create(
        name="Developer preview",
        icon_source="developer",
        icon_name="brand-up",
        icon_style="outline",
    )

    response = admin_client.get(_change_url(config.pk))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-dstt-picker-source="developer"' in content
    assert 'data-dstt-picker-name="brand-up"' in content
    assert "Project icons" in content
    assert "Brand Up" in content
    assert "Project-specific icon for branded surfaces." in content
    assert "outline · brand, custom, up" in content
    assert "dstt-icon-picker__card--selected" in content


def test_preview_admin_form_marks_color_fields_for_local_widgets() -> None:
    form = ScrollTopRevisionAdminForm()

    assert (
        form.fields["foreground_color"].widget.attrs["data-dstt-color-field"]
        == "foreground_color"
    )
    assert (
        form.fields["dark_active_background_color"].widget.attrs[
            "data-dstt-color-field"
        ]
        == "dark_active_background_color"
    )
    assert "dstt-color-field" in form.fields["focus_ring_color"].widget.attrs["class"]


def test_admin_change_form_renders_uploaded_icon_picker_card(
    admin_client: Client,
) -> None:
    icon = ScrollTopUploadedIcon(
        name="custom-up",
        style_kind="outline",
        stroke_width_override="1.75",
        author="Example Author",
        source_name="Example Pack",
        source_url="https://example.com/custom-up",
        license_name="MIT",
        license_url="https://example.com/license",
        attribution_text="Example Author / Example Pack",
        rights_confirmed=True,
    )
    icon.apply_uploaded_svg(
        filename="custom-up.svg",
        raw_svg=(
            '<svg viewBox="0 0 24 24">'
            '<path d="M12 4v16M7 9l5-5 5 5" stroke="currentColor" stroke-width="2" />'
            "</svg>"
        ),
    )
    icon.save()
    config = ScrollTopRevision.objects.create(
        name="Uploaded preview",
        icon_source="uploaded",
        uploaded_icon=icon,
        icon_name=icon.name,
    )

    response = admin_client.get(_change_url(config.pk))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-dstt-picker-source="uploaded"' in content
    assert f'data-dstt-picker-value="{icon.pk}"' in content
    assert "custom-up" in content
    assert "uploaded, recolor, strokeWidth" in content
    assert "dstt-icon-picker__card--selected" in content


def test_uploaded_icon_admin_change_form_shows_license_notice(
    admin_client: Client,
) -> None:
    icon = ScrollTopUploadedIcon.objects.create(
        name="licensed-up",
        style_kind="outline",
        color_mode="recolor",
        author="Example Author",
        source_name="Example Pack",
        source_url="https://example.test/icon",
        license_name="MIT",
        license_url="https://example.test/license",
        attribution_text="Example Author / Example Pack",
        rights_confirmed=True,
        original_filename="licensed-up.svg",
        original_checksum="a" * 64,
        sanitized_checksum="b" * 64,
        sanitized_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M12 4v16" stroke="currentColor" stroke-width="2" /></svg>'
        ),
        supports_current_color=True,
        supports_stroke_width=True,
        stroke_width_override="1.5",
    )

    response = admin_client.get(
        reverse(
            "admin:django_scroll_to_top_scrolltopuploadedicon_change",
            args=[icon.pk],
        )
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Source name" in content
    assert "License URL" in content
    assert "Attribution text" in content
    assert "does not mark it as free or open content" in content


def test_uploaded_icon_admin_exports_attribution_report(admin_client: Client) -> None:
    icon = ScrollTopUploadedIcon.objects.create(
        name="report-up",
        style_kind="outline",
        color_mode="recolor",
        author="Example Author",
        source_name="Example Pack",
        source_url="https://example.test/icon",
        license_name="MIT",
        license_url="https://example.test/license",
        copyright_notice="Copyright Example",
        attribution_text="Example Author / Example Pack",
        rights_confirmed=True,
        original_filename="report-up.svg",
        original_checksum="a" * 64,
        sanitized_checksum="b" * 64,
        sanitized_svg=(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
            '<path d="M12 4v16" stroke="currentColor" stroke-width="2" /></svg>'
        ),
        supports_current_color=True,
        supports_stroke_width=True,
    )
    ScrollTopRevision.objects.create(
        name="Report preview",
        icon_source="uploaded",
        uploaded_icon=icon,
        icon_name=icon.name,
    )

    response = admin_client.post(
        reverse("admin:django_scroll_to_top_scrolltopuploadedicon_changelist"),
        data={
            "action": "export_attribution_report",
            "_selected_action": [str(icon.pk)],
        },
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    content = response.content.decode("utf-8")
    assert "usage_count" in content
    assert "report-up" in content
    assert "Example Pack" in content
    assert "Example Author / Example Pack" in content
    assert ",1," in content


def test_admin_change_form_uses_posted_values_for_preview(admin_client: Client) -> None:
    config = ScrollTopRevision.objects.create(name="Default preview")
    url = _change_url(config.pk)

    response = admin_client.post(
        url,
        data={
            "name": "Default preview",
            "icon_source": "builtin",
            "theme_mode": "manual",
            "shape": "rounded-square",
            "fill_variant": "soft",
            "icon_name": "circle-arrow-up",
            "uploaded_icon": "",
            "icon_style": "filled",
            "corner": "top-left",
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
            "size_desktop": 56,
            "size_mobile_inherit": "",
            "size_mobile": 42,
            "icon_size_desktop": 24,
            "icon_size_mobile_inherit": "",
            "icon_size_mobile": 18,
            "_save": "Save",
        },
    )

    assert response.status_code == 302
    config.refresh_from_db()
    assert config.shape == "rounded-square"
    assert config.icon_name == "circle-arrow-up"


def test_admin_change_form_saves_developer_icon_selection(
    admin_client: Client,
) -> None:
    register_developer_icon(
        name="code-up",
        style="outline",
        svg='<svg viewBox="0 0 24 24"><path d="M5 15l7-7 7 7" /></svg>',
    )
    config = ScrollTopRevision.objects.create(name="Developer save preview")
    url = _change_url(config.pk)

    response = admin_client.post(
        url,
        data={
            "name": "Developer save preview",
            "icon_source": "developer",
            "theme_mode": "manual",
            "shape": "circle",
            "fill_variant": "solid",
            "icon_name": "code-up",
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
            "_save": "Save",
        },
    )

    assert response.status_code == 302
    config.refresh_from_db()
    assert config.icon_source == "developer"
    assert config.icon_name == "code-up"


def test_admin_change_form_hides_preview_for_invalid_post(admin_client: Client) -> None:
    config = ScrollTopRevision.objects.create(name="Default preview")
    url = _change_url(config.pk)

    response = admin_client.post(
        url,
        data={
            "name": "Default preview",
            "icon_source": "builtin",
            "shape": "circle",
            "fill_variant": "solid",
            "icon_name": "arrow-up",
            "uploaded_icon": "",
            "icon_style": "outline",
            "corner": "bottom-right",
            "foreground_color": "white",
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
        },
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert (
        "Preview becomes available when the current form values are valid."
        in content
    )


def test_standard_admin_pages_render_scroll_to_top_for_staff(
    admin_client: Client,
) -> None:
    config = _publish_admin_config("Admin integration config")
    page_urls = [
        reverse("admin:index"),
        reverse("admin:app_list", kwargs={"app_label": "django_scroll_to_top"}),
        reverse("admin:django_scroll_to_top_scrolltoprevision_changelist"),
        _change_url(config.pk),
        reverse(
            "admin:django_scroll_to_top_scrolltoprevision_history",
            args=[config.pk],
        ),
        reverse("admin:password_change"),
    ]

    for url in page_urls:
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert 'class="dstt-control"' in content
        assert "/scroll-to-top/styles/" in content
        assert 'data-dstt-icon="arrow-up"' in content


def test_admin_and_site_scopes_render_independent_configurations(
    admin_client: Client,
) -> None:
    site_profile = ScrollTopProfile.objects.create(scope="site", name="Site")
    publish_revision(
        ScrollTopRevision.objects.create(
            profile=site_profile, name="site-rev", shape="square"
        )
    )
    admin_profile = ScrollTopProfile.objects.create(scope="admin", name="Admin")
    publish_revision(
        ScrollTopRevision.objects.create(
            profile=admin_profile, name="admin-rev", shape="rounded-square"
        )
    )

    admin_response = admin_client.get(reverse("admin:index"))
    assert admin_response.status_code == 200
    assert 'data-dstt-shape="rounded-square"' in admin_response.content.decode("utf-8")

    site_response = Client().get("/sample/")
    assert site_response.status_code == 200
    assert 'data-dstt-shape="square"' in site_response.content.decode("utf-8")


def test_admin_login_page_hides_scroll_to_top_by_default(db) -> None:
    ScrollTopRevision.objects.create(name="Admin integration config")
    client = Client()

    response = client.get(reverse("admin:login"))

    assert response.status_code == 200
    assert 'class="dstt-control"' not in response.content.decode("utf-8")


def test_admin_login_page_can_opt_in_to_scroll_to_top(db) -> None:
    _publish_admin_config("Admin integration config")
    client = Client()

    with override_settings(
        DJANGO_SCROLL_TO_TOP={
            "ADMIN_ENABLED": True,
            "ADMIN_SHOW_ON_AUTH_PAGES": True,
        }
    ):
        response = client.get(reverse("admin:login"))

    assert response.status_code == 200
    assert 'class="dstt-control"' in response.content.decode("utf-8")


def test_profile_changelist_shows_starter_button(admin_client: Client) -> None:
    response = admin_client.get(
        reverse("admin:django_scroll_to_top_scrolltopprofile_changelist")
    )

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Create starter configuration" in content
    assert (
        reverse("admin:django_scroll_to_top_scrolltopprofile_create_starter")
        in content
    )


def test_create_starter_view_seeds_published_config(admin_client: Client) -> None:
    from django_scroll_to_top.services import resolve_published_revision

    url = reverse("admin:django_scroll_to_top_scrolltopprofile_create_starter")

    response = admin_client.post(url)

    assert response.status_code == 302
    assert resolve_published_revision(scope="site") is not None
    assert resolve_published_revision(scope="admin") is not None


def test_create_starter_view_ignores_get(admin_client: Client) -> None:
    url = reverse("admin:django_scroll_to_top_scrolltopprofile_create_starter")

    response = admin_client.get(url)

    assert response.status_code == 302
    assert not ScrollTopProfile.objects.exists()


def test_admin_index_includes_nav_enhancement_asset(admin_client: Client) -> None:
    response = admin_client.get(reverse("admin:index"))

    assert response.status_code == 200
    assert "admin-enhancements.js" in response.content.decode("utf-8")


def _change_url(pk: int) -> str:
    return reverse(
        "admin:django_scroll_to_top_scrolltoprevision_change",
        args=[pk],
    )
