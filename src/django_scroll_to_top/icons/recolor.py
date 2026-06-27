from __future__ import annotations

from dataclasses import dataclass
from xml.etree import ElementTree

SVG_NS = "http://www.w3.org/2000/svg"

_FILL_CAPABLE_ELEMENTS = {"path", "circle", "ellipse", "rect", "polygon"}
_STROKE_CAPABLE_ELEMENTS = _FILL_CAPABLE_ELEMENTS | {"line", "polyline"}


class SvgRecolorError(ValueError):
    """Raised when a sanitized SVG cannot satisfy the requested color mode."""


@dataclass(frozen=True, slots=True)
class SvgRecolorAnalysis:
    recolorable_fill_count: int
    recolorable_stroke_count: int

    @property
    def supports_recolor(self) -> bool:
        return self.recolorable_fill_count > 0 or self.recolorable_stroke_count > 0


def analyze_recolor_support(svg: str, *, style_kind: str) -> SvgRecolorAnalysis:
    root = _parse_svg(svg)
    fill_count = 0
    stroke_count = 0
    for element in root.iter():
        local_name = _local_name(element.tag)
        fill_value = element.attrib.get("fill")
        stroke_value = element.attrib.get("stroke")
        if local_name in _FILL_CAPABLE_ELEMENTS and _is_visible_fill(fill_value):
            fill_count += 1
        if local_name in _STROKE_CAPABLE_ELEMENTS and _is_visible_stroke(stroke_value):
            stroke_count += 1

    if style_kind == "outline":
        return SvgRecolorAnalysis(
            recolorable_fill_count=0,
            recolorable_stroke_count=stroke_count,
        )
    if style_kind == "filled":
        return SvgRecolorAnalysis(
            recolorable_fill_count=fill_count,
            recolorable_stroke_count=stroke_count,
        )
    return SvgRecolorAnalysis(recolorable_fill_count=0, recolorable_stroke_count=0)


def recolor_svg(svg: str, *, style_kind: str) -> str:
    root = _parse_svg(svg)
    analysis = analyze_recolor_support(svg, style_kind=style_kind)

    if style_kind == "outline":
        if analysis.recolorable_stroke_count == 0:
            raise SvgRecolorError(
                "Outline icons in recolor mode must define at least one visible stroke."
            )
    elif style_kind == "filled":
        if analysis.recolorable_fill_count == 0:
            raise SvgRecolorError(
                "Filled icons in recolor mode must define at least one visible fill."
            )
    else:
        raise SvgRecolorError(
            "Only outline and filled uploaded icons support recolor mode."
        )

    for element in root.iter():
        local_name = _local_name(element.tag)
        if local_name in _FILL_CAPABLE_ELEMENTS:
            fill_value = element.attrib.get("fill")
            if _is_visible_fill(fill_value):
                element.set("fill", "currentColor")
        if local_name in _STROKE_CAPABLE_ELEMENTS:
            stroke_value = element.attrib.get("stroke")
            if _is_visible_stroke(stroke_value):
                element.set("stroke", "currentColor")

    return ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)


def apply_stroke_width(svg: str, *, stroke_width: str | None) -> str:
    if stroke_width is None:
        return svg

    root = _parse_svg(svg)
    for element in root.iter():
        if "stroke-width" in element.attrib:
            element.set("stroke-width", stroke_width)
    return ElementTree.tostring(root, encoding="unicode", short_empty_elements=True)


def _parse_svg(svg: str) -> ElementTree.Element:
    ElementTree.register_namespace("", SVG_NS)
    try:
        return ElementTree.fromstring(svg)
    except ElementTree.ParseError as exc:
        raise SvgRecolorError("Sanitized SVG is not valid XML.") from exc


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[1]


def _is_visible_fill(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() != "none"


def _is_visible_stroke(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() != "none"
