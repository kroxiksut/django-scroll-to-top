from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from django_scroll_to_top.presentation import VisualConfig


def build_style_token(config: VisualConfig) -> str:
    payload = {
        "shape": config.shape,
        "fill_variant": config.fill_variant,
        "template_variant": config.template_variant,
        "icon_name": config.icon_name,
        "icon_style": config.icon_style,
        "icon_source": config.icon_source,
        "theme_mode": config.theme_mode,
        "corner": config.corner,
        "hot_zone_placement": config.hot_zone_placement,
        "hot_zone_width": config.hot_zone_width,
        "hot_zone_appearance": config.hot_zone_appearance,
        "collision_policy": config.collision_policy,
        "obstacle_selectors": list(config.obstacle_selectors),
        "obstacle_gap": config.obstacle_gap,
        "collision_max_shift": config.collision_max_shift,
        "fallback_corner_order": list(config.fallback_corner_order),
        "size_desktop": config.size.desktop_px,
        "size_mobile": config.size.mobile_or_desktop(),
        "icon_size_desktop": config.icon_size.desktop_px,
        "icon_size_mobile": config.icon_size.mobile_or_desktop(),
        "offset_x_desktop": config.offset_x.desktop_px,
        "offset_x_mobile": config.offset_x.mobile_or_desktop(),
        "offset_y_desktop": config.offset_y.desktop_px,
        "offset_y_mobile": config.offset_y.mobile_or_desktop(),
        "foreground_color": config.foreground_color,
        "icon_color": config.icon_color,
        "dark_icon_color": config.dark_icon_color,
        "background_color": config.background_color,
        "border_color": config.border_color,
        "hover_foreground_color": config.hover_foreground_color,
        "hover_background_color": config.hover_background_color,
        "hover_border_color": config.hover_border_color,
        "active_foreground_color": config.active_foreground_color,
        "active_background_color": config.active_background_color,
        "active_border_color": config.active_border_color,
        "shadow_color": config.shadow_color,
        "focus_ring_color": config.focus_ring_color,
        "dark_foreground_color": config.dark_foreground_color,
        "dark_background_color": config.dark_background_color,
        "dark_border_color": config.dark_border_color,
        "dark_hover_foreground_color": config.dark_hover_foreground_color,
        "dark_hover_background_color": config.dark_hover_background_color,
        "dark_hover_border_color": config.dark_hover_border_color,
        "dark_active_foreground_color": config.dark_active_foreground_color,
        "dark_active_background_color": config.dark_active_background_color,
        "dark_active_border_color": config.dark_active_border_color,
        "dark_shadow_color": config.dark_shadow_color,
        "dark_focus_ring_color": config.dark_focus_ring_color,
        "shadow_preset": config.shadow_preset,
        "opacity": config.opacity,
        "border_width": config.border_width,
        "focus_ring_width": config.focus_ring_width,
        "focus_ring_offset": config.focus_ring_offset,
        "gradient_start_color": config.gradient_start_color,
        "gradient_end_color": config.gradient_end_color,
        "gradient_angle": config.gradient_angle,
        "backdrop_blur": config.backdrop_blur,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return digest.hexdigest()[:12]


def build_component_stylesheet(*, config: VisualConfig, selector: str) -> str:
    variables = [
        ("--dstt-size", f"{config.size.desktop_px}px"),
        ("--dstt-size-mobile", f"{config.size.mobile_or_desktop()}px"),
        ("--dstt-icon-size", f"{config.icon_size.desktop_px}px"),
        ("--dstt-icon-size-mobile", f"{config.icon_size.mobile_or_desktop()}px"),
        ("--dstt-offset-inline", f"{config.offset_x.desktop_px}px"),
        ("--dstt-offset-inline-mobile", f"{config.offset_x.mobile_or_desktop()}px"),
        ("--dstt-offset-block", f"{config.offset_y.desktop_px}px"),
        ("--dstt-offset-block-mobile", f"{config.offset_y.mobile_or_desktop()}px"),
        ("--dstt-opacity", _format_number(config.opacity)),
        ("--dstt-border-width", f"{int(config.border_width)}px"),
        ("--dstt-focus-ring-width", f"{int(config.focus_ring_width)}px"),
        ("--dstt-focus-ring-offset", f"{int(config.focus_ring_offset)}px"),
        ("--dstt-gradient-start", config.gradient_start_color),
        ("--dstt-gradient-end", config.gradient_end_color),
        ("--dstt-gradient-angle", f"{int(config.gradient_angle)}deg"),
        ("--dstt-backdrop-blur", f"{int(config.backdrop_blur)}px"),
        ("--dstt-hot-zone-width", f"{int(config.hot_zone_width)}px"),
    ]
    if config.theme_mode != "inherit_admin_theme":
        variables.extend(
            [
                ("--dstt-color-fg", config.foreground_color),
                ("--dstt-color-bg", config.background_color),
                ("--dstt-color-border", config.border_color),
                ("--dstt-color-fg-hover", config.hover_foreground_color),
                ("--dstt-color-bg-hover", config.hover_background_color),
                ("--dstt-color-border-hover", config.hover_border_color),
                ("--dstt-color-fg-active", config.active_foreground_color),
                ("--dstt-color-bg-active", config.active_background_color),
                ("--dstt-color-border-active", config.active_border_color),
                ("--dstt-shadow-color", config.shadow_color),
                ("--dstt-focus-ring", config.focus_ring_color),
                ("--dstt-color-fg-dark", config.dark_foreground_color),
                ("--dstt-color-bg-dark", config.dark_background_color),
                ("--dstt-color-border-dark", config.dark_border_color),
                ("--dstt-color-fg-hover-dark", config.dark_hover_foreground_color),
                ("--dstt-color-bg-hover-dark", config.dark_hover_background_color),
                ("--dstt-color-border-hover-dark", config.dark_hover_border_color),
                ("--dstt-color-fg-active-dark", config.dark_active_foreground_color),
                ("--dstt-color-bg-active-dark", config.dark_active_background_color),
                ("--dstt-color-border-active-dark", config.dark_active_border_color),
                ("--dstt-shadow-color-dark", config.dark_shadow_color),
                ("--dstt-focus-ring-dark", config.dark_focus_ring_color),
            ]
        )
    # Optional icon color overrides apply regardless of theme mode; when empty
    # the icon inherits the foreground color via the CSS fallback.
    if config.icon_color:
        variables.append(("--dstt-icon-color", config.icon_color))
    if config.dark_icon_color:
        variables.append(("--dstt-icon-color-dark", config.dark_icon_color))
    base_variables = _iter_variables(variables)
    return f"{selector} {{{base_variables}}}\n"


def _iter_variables(variables: Iterable[tuple[str, str]]) -> str:
    return "".join(f"{name}: {value};" for name, value in variables)


def _format_number(value: float) -> str:
    text = f"{float(value):.4f}".rstrip("0").rstrip(".")
    return text or "0"
