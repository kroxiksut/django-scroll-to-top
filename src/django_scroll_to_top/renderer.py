from __future__ import annotations

import json
from dataclasses import dataclass

from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from django_scroll_to_top.icons.registry import resolve_icon
from django_scroll_to_top.presentation import VisualConfig, default_visual_config
from django_scroll_to_top.styles import build_style_token

_ALLOWED_SHAPES = {"circle", "square", "rounded-square", "pill"}
_ALLOWED_FILL_VARIANTS = {"outline", "solid", "soft", "ghost", "glass", "gradient"}
_ALLOWED_SHADOW_PRESETS = {"none", "small", "medium", "large"}
_ALLOWED_CORNERS = {"top-left", "top-right", "bottom-left", "bottom-right"}
_ALLOWED_HOT_ZONE_PLACEMENTS = {"none", "left", "right"}
_ALLOWED_HOT_ZONE_APPEARANCES = {"hover", "hidden", "visible"}
_ALLOWED_TEMPLATE_VARIANTS = {"icon-only", "icon-label"}
_ALLOWED_COLLISION_POLICIES = {"ignore", "shift", "fallback_corner", "hide"}
_ALLOWED_THRESHOLD_MODES = {"pixels", "viewport", "combined"}
_ALLOWED_VISIBILITY_DIRECTIONS = {
    "always",
    "scroll_up_only",
    "hide_on_scroll_down",
}
_ALLOWED_SCROLL_BEHAVIORS = {"smooth", "instant"}
_ALLOWED_DISMISSAL_STORAGE = {"local", "session", "cookie", "none"}
_ALLOWED_DISMISSAL_DURATIONS = {"persistent", "days"}
_CONTRACT_VERSION = "1"


@dataclass(frozen=True, slots=True)
class RenderPayload:
    contract_version: str
    scope: str
    site_id: str
    aria_label: str
    label_text: str
    template_variant: str
    shape: str
    fill_variant: str
    shadow_preset: str
    custom_css_class: str
    icon_name: str
    icon_style: str
    icon_source: str
    theme_mode: str
    icon_svg: str
    corner: str
    hot_zone_placement: str
    hot_zone_width: int
    hot_zone_appearance: str
    collision_policy: str
    obstacle_selectors_json: str
    obstacle_gap: int
    collision_max_shift: int
    fallback_corner_order_json: str
    style_token: str
    allow_user_dismissal: bool
    dismissal_storage: str
    dismissal_duration: str
    dismissal_days: int
    dismissal_requires_confirmation: bool
    dismissal_version: str
    dismiss_confirm_text: str
    dismiss_label_text: str
    threshold_mode: str
    show_after_px: int
    show_after_viewports: float
    min_document_height_px: int
    show_delay_ms: int
    hide_delay_ms: int
    visibility_direction: str
    scroll_target_selector: str
    scroll_offset_px: int
    fixed_header_selector: str
    scroll_behavior: str


@dataclass(frozen=True, slots=True)
class RenderContext:
    scroll_to_top: RenderPayload


def build_render_payload(
    config: VisualConfig | None = None,
    *,
    style_token: str | None = None,
    scope: str = "site",
    site_id: int | None = None,
) -> RenderPayload:
    resolved_config = config or default_visual_config()
    shape = _safe_value(resolved_config.shape, _ALLOWED_SHAPES, "circle")
    fill_variant = _safe_value(
        resolved_config.fill_variant,
        _ALLOWED_FILL_VARIANTS,
        "solid",
    )
    corner = _safe_value(
        resolved_config.corner,
        _ALLOWED_CORNERS,
        "bottom-right",
    )
    template_variant = _safe_value(
        resolved_config.template_variant,
        _ALLOWED_TEMPLATE_VARIANTS,
        "icon-only",
    )
    collision_policy = _safe_value(
        resolved_config.collision_policy,
        _ALLOWED_COLLISION_POLICIES,
        "ignore",
    )
    fallback_corner_order = tuple(
        corner
        for corner in resolved_config.fallback_corner_order
        if corner in _ALLOWED_CORNERS
    )
    obstacle_selectors = _merge_obstacle_selectors(resolved_config.obstacle_selectors)
    custom_css_class = _safe_css_class(resolved_config.custom_css_class)

    # Resolve the "same side as the button" hot-zone option to a concrete edge so
    # the runtime and CSS only ever see none/left/right.
    if resolved_config.hot_zone_placement == "button":
        hot_zone_placement = "left" if corner.endswith("left") else "right"
    else:
        hot_zone_placement = _safe_value(
            resolved_config.hot_zone_placement,
            _ALLOWED_HOT_ZONE_PLACEMENTS,
            "none",
        )
    if resolved_config.icon_svg_override is None:
        icon = resolve_icon(
            name=resolved_config.icon_name,
            style=resolved_config.icon_style,
            source=resolved_config.icon_source,
        )
        icon_name = icon.name
        icon_style = icon.style
        icon_svg = _decorate_svg(icon.svg)
    else:
        icon_name = resolved_config.icon_name
        icon_style = resolved_config.icon_style
        icon_svg = _decorate_svg(resolved_config.icon_svg_override)

    return RenderPayload(
        contract_version=_CONTRACT_VERSION,
        scope=scope,
        site_id="" if site_id is None else str(site_id),
        aria_label=resolved_config.aria_label,
        label_text=resolved_config.label_text,
        template_variant=template_variant,
        shape=shape,
        fill_variant=fill_variant,
        shadow_preset=_safe_value(
            resolved_config.shadow_preset, _ALLOWED_SHADOW_PRESETS, "medium"
        ),
        custom_css_class=custom_css_class,
        icon_name=icon_name,
        icon_style=icon_style,
        icon_source=resolved_config.icon_source,
        theme_mode=resolved_config.theme_mode,
        icon_svg=icon_svg,
        corner=corner,
        hot_zone_placement=hot_zone_placement,
        hot_zone_width=int(resolved_config.hot_zone_width),
        hot_zone_appearance=_safe_value(
            resolved_config.hot_zone_appearance,
            _ALLOWED_HOT_ZONE_APPEARANCES,
            "hover",
        ),
        collision_policy=collision_policy,
        obstacle_selectors_json=json.dumps(
            obstacle_selectors, separators=(",", ":")
        ),
        obstacle_gap=int(resolved_config.obstacle_gap),
        collision_max_shift=int(resolved_config.collision_max_shift),
        fallback_corner_order_json=json.dumps(
            list(fallback_corner_order), separators=(",", ":")
        ),
        style_token=style_token or build_style_token(resolved_config),
        allow_user_dismissal=resolved_config.allow_user_dismissal,
        dismissal_storage=_safe_value(
            resolved_config.dismissal_storage, _ALLOWED_DISMISSAL_STORAGE, "local"
        ),
        dismissal_duration=_safe_value(
            resolved_config.dismissal_duration,
            _ALLOWED_DISMISSAL_DURATIONS,
            "persistent",
        ),
        dismissal_days=int(resolved_config.dismissal_days),
        dismissal_requires_confirmation=(
            resolved_config.dismissal_requires_confirmation
        ),
        dismissal_version=resolved_config.dismissal_version,
        dismiss_confirm_text=str(_("Hide the scroll-to-top button?")),
        dismiss_label_text=str(_("Hide the scroll-to-top button")),
        threshold_mode=_safe_value(
            resolved_config.threshold_mode, _ALLOWED_THRESHOLD_MODES, "pixels"
        ),
        show_after_px=int(resolved_config.show_after_px),
        show_after_viewports=float(resolved_config.show_after_viewports),
        min_document_height_px=int(resolved_config.min_document_height_px),
        show_delay_ms=int(resolved_config.show_delay_ms),
        hide_delay_ms=int(resolved_config.hide_delay_ms),
        visibility_direction=_safe_value(
            resolved_config.visibility_direction,
            _ALLOWED_VISIBILITY_DIRECTIONS,
            "always",
        ),
        scroll_target_selector=resolved_config.scroll_target_selector,
        scroll_offset_px=int(resolved_config.scroll_offset_px),
        fixed_header_selector=resolved_config.fixed_header_selector,
        scroll_behavior=_safe_value(
            resolved_config.scroll_behavior, _ALLOWED_SCROLL_BEHAVIORS, "smooth"
        ),
    )


def build_render_context(
    config: VisualConfig | None = None,
    *,
    style_token: str | None = None,
    scope: str = "site",
    site_id: int | None = None,
) -> RenderContext:
    return RenderContext(
        scroll_to_top=build_render_payload(
            config,
            style_token=style_token,
            scope=scope,
            site_id=site_id,
        )
    )


def render_scroll_to_top(
    config: VisualConfig | None = None,
    *,
    style_token: str | None = None,
    scope: str = "site",
    site_id: int | None = None,
) -> str:
    context = build_render_context(
        config,
        style_token=style_token,
        scope=scope,
        site_id=site_id,
    )
    return render_to_string(
        "django_scroll_to_top/scroll_to_top.html",
        {"scroll_to_top": context.scroll_to_top},
    )


def _safe_css_class(value: str) -> str:
    """Return the value only if it is safe space-separated class tokens."""
    from django_scroll_to_top.models import CSS_CLASS_TOKENS_RE

    candidate = (value or "").strip()
    if candidate and CSS_CLASS_TOKENS_RE.match(candidate):
        return candidate
    return ""


def _merge_obstacle_selectors(configured: tuple[str, ...]) -> list[str]:
    """Merge configured obstacle selectors with the optional developer hook."""
    from django_scroll_to_top.settings import get_obstacle_selectors_hook

    merged = list(configured)
    hook = get_obstacle_selectors_hook()
    if hook is not None:
        try:
            extra = hook() or []
        except Exception:  # noqa: BLE001 - a faulty hook must not break rendering
            extra = []
        for selector in extra:
            if isinstance(selector, str) and selector and selector not in merged:
                merged.append(selector)
    return merged


def _decorate_svg(svg: str) -> str:
    if "aria-hidden=" not in svg:
        svg = svg.replace("<svg", '<svg aria-hidden="true" focusable="false"', 1)
    if 'class="' in svg:
        svg = svg.replace('class="', 'class="dstt-icon-svg ', 1)
    else:
        svg = svg.replace("<svg", '<svg class="dstt-icon-svg"', 1)
    return svg

def _safe_value(value: str, allowed: set[str], fallback: str) -> str:
    return value if value in allowed else fallback
