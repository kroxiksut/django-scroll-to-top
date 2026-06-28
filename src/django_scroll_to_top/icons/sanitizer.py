from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Final
from xml.etree import ElementTree

SVG_NS: Final[str] = "http://www.w3.org/2000/svg"
XML_NS: Final[str] = "http://www.w3.org/XML/1998/namespace"
XLINK_NS: Final[str] = "http://www.w3.org/1999/xlink"

MAX_SVG_BYTES: Final[int] = 100_000
MAX_ELEMENT_COUNT: Final[int] = 128
MAX_XML_DEPTH: Final[int] = 8
# Per-attribute cap on geometry payloads (path ``d`` and polyline/polygon
# ``points``) so a single element cannot smuggle a pathological coordinate blob
# that still fits inside the overall file-size budget.
MAX_PATH_DATA_LENGTH: Final[int] = 20_000

_GEOMETRY_DATA_ATTRIBUTES: Final[frozenset[str]] = frozenset({"d", "points"})

_FORBIDDEN_RAW_MARKERS: Final[tuple[str, ...]] = (
    "<!DOCTYPE",
    "<!ENTITY",
    "<script",
    "<style",
    "<foreignObject",
    "<iframe",
    "<object",
    "<embed",
)

_ALLOWED_ELEMENTS: Final[dict[str, frozenset[str]]] = {
    "svg": frozenset({"viewBox", "fill", "stroke", "stroke-width"}),
    "g": frozenset(
        {
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "fill-rule",
            "clip-rule",
            "opacity",
            "transform",
        }
    ),
    "path": frozenset(
        {
            "d",
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "fill-rule",
            "clip-rule",
            "opacity",
            "transform",
        }
    ),
    "circle": frozenset(
        {"cx", "cy", "r", "fill", "stroke", "stroke-width", "opacity", "transform"}
    ),
    "ellipse": frozenset(
        {
            "cx",
            "cy",
            "rx",
            "ry",
            "fill",
            "stroke",
            "stroke-width",
            "opacity",
            "transform",
        }
    ),
    "rect": frozenset(
        {
            "x",
            "y",
            "width",
            "height",
            "rx",
            "ry",
            "fill",
            "stroke",
            "stroke-width",
            "opacity",
            "transform",
        }
    ),
    "line": frozenset(
        {
            "x1",
            "y1",
            "x2",
            "y2",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "opacity",
            "transform",
        }
    ),
    "polyline": frozenset(
        {
            "points",
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "opacity",
            "transform",
        }
    ),
    "polygon": frozenset(
        {
            "points",
            "fill",
            "stroke",
            "stroke-width",
            "stroke-linecap",
            "stroke-linejoin",
            "fill-rule",
            "opacity",
            "transform",
        }
    ),
}


class SvgSanitizationError(ValueError):
    """Raised when an uploaded SVG violates the sanitizer contract."""


@dataclass(frozen=True, slots=True)
class SanitizedSvg:
    svg: str
    original_checksum: str
    sanitized_checksum: str
    uses_current_color: bool
    supports_stroke_width: bool
    original_view_box: str
    normalized_view_box: str


def sanitize_uploaded_svg(raw_svg: str) -> SanitizedSvg:
    _validate_raw_svg(raw_svg)
    root = _parse_xml(raw_svg)
    _validate_tree(root)
    original_view_box = root.attrib.get("viewBox")
    if original_view_box is None:
        raise SvgSanitizationError("Uploaded SVG must provide a viewBox.")
    normalized_view_box = _normalize_view_box(original_view_box)

    sanitized_root = _sanitize_element(root, depth=1)
    sanitized_root.set("xmlns", SVG_NS)
    sanitized_root.set("viewBox", normalized_view_box)
    sanitized_root.attrib.pop("width", None)
    sanitized_root.attrib.pop("height", None)
    sanitized_svg = ElementTree.tostring(
        sanitized_root,
        encoding="unicode",
        short_empty_elements=True,
    )
    sanitized_svg = sanitized_svg.strip()

    if not sanitized_svg.startswith("<svg"):
        raise SvgSanitizationError("Sanitized payload must remain an SVG root.")

    return SanitizedSvg(
        svg=sanitized_svg,
        original_checksum=_checksum(raw_svg),
        sanitized_checksum=_checksum(sanitized_svg),
        uses_current_color="currentColor" in sanitized_svg,
        supports_stroke_width="stroke-width" in sanitized_svg,
        original_view_box=original_view_box.strip(),
        normalized_view_box=normalized_view_box,
    )


def _validate_raw_svg(raw_svg: str) -> None:
    if len(raw_svg.encode("utf-8")) > MAX_SVG_BYTES:
        raise SvgSanitizationError("Uploaded SVG exceeds the maximum allowed size.")

    lowered = raw_svg.lower()
    for marker in _FORBIDDEN_RAW_MARKERS:
        if marker.lower() in lowered:
            raise SvgSanitizationError("Uploaded SVG contains forbidden markup.")


def _parse_xml(raw_svg: str) -> ElementTree.Element:
    try:
        parser = ElementTree.XMLParser()
        return ElementTree.fromstring(raw_svg, parser=parser)
    except ElementTree.ParseError as exc:
        raise SvgSanitizationError("Uploaded SVG is not valid XML.") from exc


def _validate_tree(root: ElementTree.Element) -> None:
    if _local_name(root.tag) != "svg":
        raise SvgSanitizationError("Uploaded payload must have an <svg> root.")

    count = 0
    stack: list[tuple[ElementTree.Element, int]] = [(root, 1)]
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > MAX_ELEMENT_COUNT:
            raise SvgSanitizationError("Uploaded SVG exceeds the element limit.")
        if depth > MAX_XML_DEPTH:
            raise SvgSanitizationError("Uploaded SVG exceeds the depth limit.")
        for child in list(node):
            stack.append((child, depth + 1))


def _sanitize_element(
    element: ElementTree.Element,
    *,
    depth: int,
) -> ElementTree.Element:
    local_name = _local_name(element.tag)
    allowed_attributes = _ALLOWED_ELEMENTS.get(local_name)
    if allowed_attributes is None:
        raise SvgSanitizationError("Uploaded SVG uses a forbidden element.")

    sanitized = ElementTree.Element(local_name)
    for attr_name, attr_value in element.attrib.items():
        local_attr = _local_name(attr_name)
        namespace = _namespace(attr_name)

        if namespace not in {"", SVG_NS}:
            raise SvgSanitizationError("Uploaded SVG uses an unsafe namespace.")
        if local_attr.startswith("on"):
            raise SvgSanitizationError("Uploaded SVG uses event handlers.")
        if local_attr in {"href", "style", "class", "id"}:
            raise SvgSanitizationError("Uploaded SVG uses a forbidden attribute.")
        if namespace == XLINK_NS:
            raise SvgSanitizationError("Uploaded SVG uses xlink references.")
        if local_attr not in allowed_attributes:
            continue
        if _looks_like_external_reference(attr_value):
            raise SvgSanitizationError("Uploaded SVG references an external resource.")
        if (
            local_attr in _GEOMETRY_DATA_ATTRIBUTES
            and len(attr_value) > MAX_PATH_DATA_LENGTH
        ):
            raise SvgSanitizationError(
                "Uploaded SVG path data exceeds the maximum allowed length."
            )
        sanitized.set(local_attr, attr_value.strip())

    if local_name == "svg":
        view_box = sanitized.get("viewBox")
        if view_box is None:
            raise SvgSanitizationError("Uploaded SVG must provide a viewBox.")
        sanitized.set("viewBox", _normalize_view_box(view_box))

    for child in list(element):
        sanitized.append(_sanitize_element(child, depth=depth + 1))

    return sanitized


def _looks_like_external_reference(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered.startswith("http:")
        or lowered.startswith("https:")
        or lowered.startswith("//")
        or lowered.startswith("data:")
        or "url(" in lowered
        or lowered.startswith("#") is False
        and ("href" in lowered or ".svg" in lowered)
    )


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[1]


def _namespace(tag: str) -> str:
    if "}" not in tag or not tag.startswith("{"):
        return ""
    return tag[1:].split("}", 1)[0]


def _checksum(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _normalize_view_box(value: str) -> str:
    raw_parts = value.replace(",", " ").split()
    if len(raw_parts) != 4:
        raise SvgSanitizationError("Uploaded SVG must provide a valid viewBox.")
    try:
        numbers = [float(part) for part in raw_parts]
    except ValueError as exc:
        raise SvgSanitizationError(
            "Uploaded SVG must provide a valid viewBox."
        ) from exc
    return " ".join(_format_view_box_number(number) for number in numbers)


def _format_view_box_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
