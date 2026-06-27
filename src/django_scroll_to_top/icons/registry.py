from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache, lru_cache
from importlib.resources import files
from typing import Any, Literal, cast

from django_scroll_to_top.icons.sanitizer import SanitizedSvg, sanitize_uploaded_svg

IconSource = Literal["builtin", "developer", "uploaded"]
IconStyle = Literal["outline", "filled"]

_TABLER_PACKAGE = "django_scroll_to_top.icons.tabler"


@dataclass(frozen=True, slots=True)
class IconDefinition:
    source: IconSource
    name: str
    style: IconStyle
    svg: str


@dataclass(frozen=True, slots=True)
class IconMetadata:
    display_name: str
    short_description: str
    tags: tuple[str, ...]
    admin_group: str
    supports_stroke_width: bool
    original_view_box: str
    normalized_view_box: str


@dataclass(frozen=True, slots=True)
class BuiltinIconAttribution:
    icon_name: str
    icon_style: IconStyle
    source_name: str
    source_homepage: str
    source_version: str
    license_name: str
    copyright_notice: str
    attribution_text: str


_developer_icons: dict[tuple[str, IconStyle], str] = {}
_developer_icon_metadata: dict[tuple[str, IconStyle], IconMetadata] = {}
_uploaded_icons: dict[tuple[str, IconStyle], SanitizedSvg] = {}


def register_developer_icon(
    *,
    name: str,
    style: IconStyle,
    svg: str,
    display_name: str | None = None,
    short_description: str | None = None,
    tags: tuple[str, ...] = (),
    admin_group: str = "Developer icons",
) -> None:
    """Register a trusted developer-provided icon variant."""

    _developer_icons[(name, style)] = svg
    _developer_icon_metadata[(name, style)] = IconMetadata(
        display_name=display_name or _humanize_icon_name(name),
        short_description=short_description
        or "Trusted project-provided icon registered in Python code.",
        tags=tags or _default_tags_for_name(name),
        admin_group=admin_group,
        supports_stroke_width="stroke-width" in svg,
        original_view_box=_extract_view_box(svg),
        normalized_view_box=_extract_view_box(svg),
    )


def developer_icon_names() -> dict[IconStyle, tuple[str, ...]]:
    grouped: dict[IconStyle, list[str]] = {"outline": [], "filled": []}
    for name, style in sorted(_developer_icons):
        grouped[style].append(name)
    return {
        "outline": tuple(grouped["outline"]),
        "filled": tuple(grouped["filled"]),
    }


def get_developer_icon_metadata(name: str, style: IconStyle) -> IconMetadata:
    metadata = _developer_icon_metadata.get((name, style))
    if metadata is None:
        return IconMetadata(
            display_name=_humanize_icon_name(name),
            short_description=(
                "Trusted project-provided icon registered in Python code."
            ),
            tags=_default_tags_for_name(name),
            admin_group="Developer icons",
            supports_stroke_width=False,
            original_view_box="0 0 24 24",
            normalized_view_box="0 0 24 24",
        )
    return metadata


def register_uploaded_icon(
    *,
    name: str,
    style: IconStyle,
    raw_svg: str,
) -> SanitizedSvg:
    """Sanitize and register an uploaded icon payload."""

    sanitized = sanitize_uploaded_svg(raw_svg)
    _uploaded_icons[(name, style)] = sanitized
    return sanitized


@lru_cache(maxsize=1)
def builtin_icon_names() -> dict[IconStyle, tuple[str, ...]]:
    manifest = _tabler_manifest()
    return {
        "outline": tuple(manifest["outline"]),
        "filled": tuple(manifest["filled"]),
    }


def get_builtin_icon_metadata(name: str) -> IconMetadata:
    manifest = _tabler_manifest()
    raw_metadata = cast(dict[str, Any] | None, manifest.get("metadata", {}).get(name))
    if raw_metadata is None:
        return IconMetadata(
            display_name=_humanize_icon_name(name),
            short_description="Built-in icon from the vendored Tabler subset.",
            tags=_default_tags_for_name(name),
            admin_group="Built-in Tabler icons",
            supports_stroke_width=False,
            original_view_box="0 0 24 24",
            normalized_view_box="0 0 24 24",
        )
    return IconMetadata(
        display_name=str(raw_metadata["display_name"]),
        short_description=str(raw_metadata["short_description"]),
        tags=tuple(str(tag) for tag in raw_metadata.get("tags", [])),
        admin_group=str(raw_metadata["admin_group"]),
        supports_stroke_width=bool(raw_metadata.get("supports_stroke_width", False)),
        original_view_box=str(raw_metadata.get("original_view_box", "0 0 24 24")),
        normalized_view_box=str(raw_metadata.get("normalized_view_box", "0 0 24 24")),
    )


def get_builtin_icon_attribution(
    name: str,
    style: IconStyle,
) -> BuiltinIconAttribution:
    manifest = _tabler_manifest()
    metadata = get_builtin_icon_metadata(name)
    source_name = str(manifest["source"])
    source_homepage = str(manifest["homepage"])
    source_version = str(manifest["version"])
    license_name = str(manifest["license"])
    copyright_notice = str(manifest["copyright"])
    attribution_text = (
        f"{metadata.display_name} ({style}) from {source_name} {source_version}. "
        f"{copyright_notice}. License: {license_name}. Source: {source_homepage}"
    )
    return BuiltinIconAttribution(
        icon_name=name,
        icon_style=style,
        source_name=source_name,
        source_homepage=source_homepage,
        source_version=source_version,
        license_name=license_name,
        copyright_notice=copyright_notice,
        attribution_text=attribution_text,
    )


@cache
def get_builtin_icon(name: str, style: IconStyle) -> IconDefinition:
    allowed_names = builtin_icon_names()[style]
    if name not in allowed_names:
        raise KeyError(f"Unknown builtin icon: {name!r} ({style})")

    icon_path = files(_TABLER_PACKAGE).joinpath(style).joinpath(f"{name}.svg")
    return IconDefinition(
        source="builtin",
        name=name,
        style=style,
        svg=icon_path.read_text(encoding="utf-8").strip(),
    )


@lru_cache(maxsize=1)
def _tabler_manifest() -> dict[str, Any]:
    manifest_path = files(_TABLER_PACKAGE).joinpath("manifest.json")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _humanize_icon_name(name: str) -> str:
    return name.replace("-", " ").title()


def _default_tags_for_name(name: str) -> tuple[str, ...]:
    return tuple(name.split("-"))


def _extract_view_box(svg: str) -> str:
    marker = 'viewBox="'
    start = svg.find(marker)
    if start == -1:
        return "0 0 24 24"
    end = svg.find('"', start + len(marker))
    if end == -1:
        return "0 0 24 24"
    return svg[start + len(marker) : end].strip()


def resolve_icon(
    *,
    name: str,
    style: IconStyle,
    source: IconSource = "builtin",
    fallback_name: str = "arrow-up",
) -> IconDefinition:
    if source == "developer":
        svg = _developer_icons.get((name, style))
        if svg is not None:
            return IconDefinition(source="developer", name=name, style=style, svg=svg)

    if source == "uploaded":
        sanitized = _uploaded_icons.get((name, style))
        if sanitized is not None:
            return IconDefinition(
                source="uploaded",
                name=name,
                style=style,
                svg=sanitized.svg,
            )
        raise KeyError(f"Unknown uploaded icon: {name!r} ({style})")

    try:
        return get_builtin_icon(name, style)
    except KeyError:
        return get_builtin_icon(fallback_name, style)
