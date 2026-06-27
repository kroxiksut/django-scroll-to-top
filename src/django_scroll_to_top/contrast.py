from __future__ import annotations

from dataclasses import dataclass


class ColorValidationError(ValueError):
    """Raised when a color value is malformed for preview validation."""


@dataclass(frozen=True, slots=True)
class RgbColor:
    red: int
    green: int
    blue: int


def parse_hex_color(value: str) -> RgbColor:
    stripped = value.strip()
    if not stripped.startswith("#"):
        raise ColorValidationError("Colors must be provided in #RRGGBB format.")
    hex_value = stripped[1:]
    if len(hex_value) != 6:
        raise ColorValidationError("Colors must be provided in #RRGGBB format.")
    try:
        return RgbColor(
            red=int(hex_value[0:2], 16),
            green=int(hex_value[2:4], 16),
            blue=int(hex_value[4:6], 16),
        )
    except ValueError as exc:
        raise ColorValidationError("Colors must be valid hexadecimal values.") from exc


def contrast_ratio(foreground: str, background: str) -> float:
    foreground_rgb = parse_hex_color(foreground)
    background_rgb = parse_hex_color(background)
    foreground_luminance = _relative_luminance(foreground_rgb)
    background_luminance = _relative_luminance(background_rgb)
    lighter = max(foreground_luminance, background_luminance)
    darker = min(foreground_luminance, background_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def meets_minimum_contrast(
    foreground: str,
    background: str,
    *,
    minimum_ratio: float = 3.0,
) -> bool:
    return contrast_ratio(foreground, background) >= minimum_ratio


def _relative_luminance(color: RgbColor) -> float:
    channels = (color.red, color.green, color.blue)
    normalized = [_linearize(channel / 255) for channel in channels]
    return 0.2126 * normalized[0] + 0.7152 * normalized[1] + 0.0722 * normalized[2]


def _linearize(value: float) -> float:
    if value <= 0.03928:
        return value / 12.92
    return ((value + 0.055) / 1.055) ** 2.4
