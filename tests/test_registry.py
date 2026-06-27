from django_scroll_to_top.icons.registry import (
    builtin_icon_names,
    developer_icon_names,
    get_builtin_icon_attribution,
    get_builtin_icon_metadata,
    get_developer_icon_metadata,
    register_developer_icon,
    resolve_icon,
)


def test_builtin_registry_exposes_manifest_names() -> None:
    names = builtin_icon_names()

    assert "arrow-up" in names["outline"]
    assert "circle-arrow-up" in names["filled"]


def test_unknown_builtin_icon_falls_back_to_arrow_up() -> None:
    icon = resolve_icon(name="missing", style="outline")

    assert icon.name == "arrow-up"
    assert icon.source == "builtin"


def test_developer_icon_registry_overrides_builtin_lookup() -> None:
    register_developer_icon(
        name="brand-up",
        style="outline",
        svg='<svg viewBox="0 0 24 24"><path d="M12 3v18" /></svg>',
    )

    icon = resolve_icon(name="brand-up", style="outline", source="developer")

    assert icon.source == "developer"
    assert 'viewBox="0 0 24 24"' in icon.svg


def test_developer_registry_exposes_registered_names() -> None:
    register_developer_icon(
        name="custom-chevron-up",
        style="filled",
        svg='<svg viewBox="0 0 24 24"><path d="M6 14l6-6 6 6" /></svg>',
    )

    names = developer_icon_names()

    assert "custom-chevron-up" in names["filled"]


def test_builtin_registry_exposes_metadata() -> None:
    metadata = get_builtin_icon_metadata("arrow-up")

    assert metadata.display_name == "Arrow Up"
    assert "minimal" in metadata.tags
    assert metadata.admin_group == "Built-in Tabler icons"
    assert metadata.supports_stroke_width is True
    assert metadata.original_view_box == "0 0 24 24"
    assert metadata.normalized_view_box == "0 0 24 24"


def test_builtin_registry_builds_tabler_attribution_from_manifest() -> None:
    attribution = get_builtin_icon_attribution("arrow-up", "outline")

    assert attribution.icon_name == "arrow-up"
    assert attribution.icon_style == "outline"
    assert attribution.source_name == "Tabler Icons"
    assert attribution.source_version == "3.44.0"
    assert attribution.license_name == "MIT"
    assert "Pawe" in attribution.copyright_notice
    assert (
        "Arrow Up (outline) from Tabler Icons 3.44.0."
        in attribution.attribution_text
    )


def test_developer_registry_exposes_metadata() -> None:
    register_developer_icon(
        name="brand-arrow",
        style="outline",
        svg='<svg viewBox="0 0 24 24"><path d="M12 4v16" /></svg>',
        display_name="Brand Arrow",
        short_description="House style arrow used across the project.",
        tags=("brand", "custom", "up"),
        admin_group="Project icons",
    )

    metadata = get_developer_icon_metadata("brand-arrow", "outline")

    assert metadata.display_name == "Brand Arrow"
    assert metadata.short_description == "House style arrow used across the project."
    assert metadata.tags == ("brand", "custom", "up")
    assert metadata.admin_group == "Project icons"
    assert metadata.supports_stroke_width is False
    assert metadata.original_view_box == "0 0 24 24"
    assert metadata.normalized_view_box == "0 0 24 24"
