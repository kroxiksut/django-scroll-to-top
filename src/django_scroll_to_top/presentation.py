from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.icons.registry import IconSource, IconStyle

Shape = Literal["circle", "square", "rounded-square", "pill"]
FillVariant = Literal["outline", "solid", "soft", "ghost", "glass", "gradient"]
ShadowPreset = Literal["none", "small", "medium", "large"]
Corner = Literal["top-left", "top-right", "bottom-left", "bottom-right"]
TemplateVariant = Literal["icon-only", "icon-label"]
ThemeMode = Literal["manual", "inherit_admin_theme"]
DismissalStorage = Literal["local", "session", "cookie", "none"]
DismissalDuration = Literal["persistent", "days"]
HotZonePlacement = Literal["none", "left", "right"]
HotZoneAppearance = Literal["hover", "hidden", "visible"]
CollisionPolicy = Literal["ignore", "shift", "fallback_corner", "hide"]
ThresholdMode = Literal["pixels", "viewport", "combined"]
VisibilityDirection = Literal["always", "scroll_up_only", "hide_on_scroll_down"]
ScrollBehavior = Literal["smooth", "instant"]


@dataclass(frozen=True, slots=True)
class ResponsiveLength:
    desktop_px: int
    mobile_px: int | None = None

    def mobile_or_desktop(self) -> int:
        return self.desktop_px if self.mobile_px is None else self.mobile_px


@dataclass(frozen=True, slots=True)
class VisualConfig:
    aria_label: str = field(default_factory=lambda: str(_("Scroll back to top")))
    label_text: str = field(default_factory=lambda: str(_("Back to top")))
    shape: Shape = "circle"
    fill_variant: FillVariant = "solid"
    template_variant: TemplateVariant = "icon-only"
    icon_name: str = "arrow-up"
    icon_style: IconStyle = "outline"
    icon_source: IconSource = "builtin"
    icon_svg_override: str | None = None
    custom_css_class: str = ""
    theme_mode: ThemeMode = "manual"
    corner: Corner = "bottom-right"
    hot_zone_placement: HotZonePlacement = "none"
    hot_zone_width: int = 120
    hot_zone_appearance: HotZoneAppearance = "hover"
    collision_policy: CollisionPolicy = "ignore"
    obstacle_selectors: tuple[str, ...] = ()
    obstacle_gap: int = 12
    collision_max_shift: int = 240
    fallback_corner_order: tuple[Corner, ...] = ()
    size: ResponsiveLength = ResponsiveLength(desktop_px=52, mobile_px=48)
    icon_size: ResponsiveLength = ResponsiveLength(desktop_px=24, mobile_px=22)
    offset_x: ResponsiveLength = ResponsiveLength(desktop_px=24, mobile_px=16)
    offset_y: ResponsiveLength = ResponsiveLength(desktop_px=24, mobile_px=16)
    foreground_color: str = "#ffffff"
    icon_color: str = ""
    dark_icon_color: str = ""
    background_color: str = "#0f172a"
    border_color: str = "#0f172a"
    hover_foreground_color: str = "#ffffff"
    hover_background_color: str = "#1e293b"
    hover_border_color: str = "#1e293b"
    active_foreground_color: str = "#ffffff"
    active_background_color: str = "#334155"
    active_border_color: str = "#334155"
    shadow_color: str = "rgba(15, 23, 42, 0.25)"
    focus_ring_color: str = "#38bdf8"
    dark_foreground_color: str = "#f8fafc"
    dark_background_color: str = "#0f172a"
    dark_border_color: str = "#cbd5e1"
    dark_hover_foreground_color: str = "#f8fafc"
    dark_hover_background_color: str = "#1e293b"
    dark_hover_border_color: str = "#e2e8f0"
    dark_active_foreground_color: str = "#f8fafc"
    dark_active_background_color: str = "#334155"
    dark_active_border_color: str = "#f8fafc"
    dark_shadow_color: str = "rgba(2, 6, 23, 0.5)"
    dark_focus_ring_color: str = "#7dd3fc"
    # Styling (§17)
    shadow_preset: ShadowPreset = "medium"
    opacity: float = 1.0
    border_width: int = 1
    focus_ring_width: int = 3
    focus_ring_offset: int = 3
    gradient_start_color: str = "#0f172a"
    gradient_end_color: str = "#1e293b"
    gradient_angle: int = 135
    backdrop_blur: int = 8
    allow_user_dismissal: bool = False
    dismissal_storage: DismissalStorage = "local"
    dismissal_duration: DismissalDuration = "persistent"
    dismissal_days: int = 30
    dismissal_requires_confirmation: bool = False
    dismissal_version: str = "1"
    # Visibility (§11)
    threshold_mode: ThresholdMode = "pixels"
    show_after_px: int = 240
    show_after_viewports: float = 1.0
    min_document_height_px: int = 0
    show_delay_ms: int = 0
    hide_delay_ms: int = 0
    visibility_direction: VisibilityDirection = "always"
    # Scroll behavior (§12)
    scroll_target_selector: str = ""
    scroll_offset_px: int = 0
    fixed_header_selector: str = ""
    scroll_behavior: ScrollBehavior = "smooth"


def default_visual_config() -> VisualConfig:
    return VisualConfig()
