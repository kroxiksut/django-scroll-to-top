from __future__ import annotations

import re
from typing import Any, cast

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.contrast import (
    ColorValidationError,
    parse_hex_color,
)
from django_scroll_to_top.icons.registry import (
    builtin_icon_names,
    developer_icon_names,
)
from django_scroll_to_top.icons.sanitizer import MAX_SVG_BYTES
from django_scroll_to_top.models import CSS_CLASS_TOKENS_RE, ScrollTopUploadedIcon
from django_scroll_to_top.presentation import ResponsiveLength, VisualConfig
from django_scroll_to_top.settings import get_scroll_to_top_settings

_VALID_CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")
# Conservative allowlist of characters permitted in an obstacle CSS selector.
# Anything outside this set (notably <, >, {, }, ;, \) is rejected so the value
# is safe to serialize into a data attribute and pass to querySelectorAll.
_SELECTOR_SAFE_RE = re.compile(r"^[A-Za-z0-9 ._#>~+*\[\]=\"'^$|():,\-]+$")
_MAX_SELECTOR_LENGTH = 200


def _int_or_default(value: Any, default: int) -> int:
    return default if value is None else int(value)


def _float_or_default(value: Any, default: float) -> float:
    return default if value is None else float(value)


def parse_obstacle_selectors(value: object) -> list[str]:
    """Split a newline-separated obstacle selector blob into clean entries."""
    if not isinstance(value, str):
        return []
    selectors: list[str] = []
    for line in value.splitlines():
        candidate = line.strip()
        if candidate and candidate not in selectors:
            selectors.append(candidate)
    return selectors


def parse_fallback_corner_order(value: object) -> list[str]:
    """Parse an ordered, de-duplicated list of valid corners."""
    if not isinstance(value, str):
        return []
    corners: list[str] = []
    for token in re.split(r"[\s,]+", value.strip()):
        if token in _VALID_CORNERS and token not in corners:
            corners.append(token)
    return corners


def _available_icon_choice_list() -> list[tuple[str, str]]:
    names = (
        set(builtin_icon_names()["outline"])
        | set(builtin_icon_names()["filled"])
        | set(developer_icon_names()["outline"])
        | set(developer_icon_names()["filled"])
    )
    return [(name, name) for name in sorted(names)]


class ScrollToTopPreviewForm(forms.Form):
    theme_mode = forms.ChoiceField(
        label=_("Theme mode"),
        choices=[
            ("manual", _("Manual")),
            ("inherit_admin_theme", _("Inherit admin theme")),
        ],
        initial="manual",
        required=False,
    )
    icon_source = forms.ChoiceField(
        label=_("Icon source"),
        choices=[
            ("builtin", _("Built-in")),
            ("developer", _("Developer")),
            ("uploaded", _("Uploaded")),
        ],
        initial="builtin",
    )
    shape = forms.ChoiceField(
        label=_("Shape"),
        choices=[
            ("circle", _("Circle")),
            ("square", _("Square")),
            ("rounded-square", _("Rounded square")),
            ("pill", _("Pill")),
        ],
        initial="circle",
    )
    fill_variant = forms.ChoiceField(
        label=_("Fill variant"),
        choices=[
            ("solid", _("Solid")),
            ("outline", _("Outline")),
            ("soft", _("Soft")),
            ("ghost", _("Ghost")),
            ("glass", _("Glass")),
            ("gradient", _("Gradient")),
        ],
        initial="solid",
    )
    template_variant = forms.ChoiceField(
        label=_("Template variant"),
        choices=[
            ("icon-only", _("Icon only")),
            ("icon-label", _("Icon with label")),
        ],
        initial="icon-only",
        required=False,
    )
    aria_label = forms.CharField(
        label=_("Accessible name"),
        max_length=120,
        required=False,
    )
    label_text = forms.CharField(
        label=_("Visible label"),
        max_length=60,
        required=False,
    )
    custom_css_class = forms.CharField(
        label=_("Custom CSS class"),
        max_length=120,
        required=False,
    )
    icon_name = forms.ChoiceField(
        label=_("Icon"),
        choices=_available_icon_choice_list(),
        initial="arrow-up",
    )
    uploaded_icon = forms.ModelChoiceField(
        label=_("Uploaded icon"),
        queryset=ScrollTopUploadedIcon.objects.order_by("name"),
        required=False,
        empty_label=_("Select an uploaded icon"),
    )
    icon_style = forms.ChoiceField(
        label=_("Icon style"),
        choices=[
            ("outline", _("Outline")),
            ("filled", _("Filled")),
        ],
        initial="outline",
    )
    corner = forms.ChoiceField(
        label=_("Button location"),
        choices=[
            ("top-left", _("Top left")),
            ("top-right", _("Top right")),
            ("bottom-left", _("Bottom left")),
            ("bottom-right", _("Bottom right")),
        ],
        initial="bottom-right",
    )
    hot_zone_placement = forms.ChoiceField(
        label=_("Side click zone"),
        choices=[
            ("none", _("Disabled")),
            ("button", _("Same side as the button")),
            ("left", _("Left edge")),
            ("right", _("Right edge")),
        ],
        required=False,
        initial="none",
    )
    hot_zone_width = forms.IntegerField(
        label=_("Side click zone width (px)"),
        required=False,
        min_value=0,
        initial=120,
    )
    hot_zone_appearance = forms.ChoiceField(
        label=_("Side click zone appearance"),
        choices=[
            ("hover", _("Invisible, highlight on hover")),
            ("hidden", _("Fully invisible")),
            ("visible", _("Always slightly visible")),
        ],
        required=False,
        initial="hover",
    )
    foreground_color = forms.CharField(label=_("Foreground color"), initial="#ffffff")
    icon_color = forms.CharField(
        label=_("Icon color override"), required=False, initial=""
    )
    dark_icon_color = forms.CharField(
        label=_("Dark icon color override"), required=False, initial=""
    )
    background_color = forms.CharField(label=_("Background color"), initial="#0f172a")
    border_color = forms.CharField(label=_("Border color"), initial="#0f172a")
    hover_foreground_color = forms.CharField(
        label=_("Hover foreground color"),
        initial="#ffffff",
    )
    hover_background_color = forms.CharField(
        label=_("Hover background color"),
        initial="#1e293b",
    )
    hover_border_color = forms.CharField(
        label=_("Hover border color"),
        initial="#1e293b",
    )
    active_foreground_color = forms.CharField(
        label=_("Active foreground color"),
        initial="#ffffff",
    )
    active_background_color = forms.CharField(
        label=_("Active background color"),
        initial="#334155",
    )
    active_border_color = forms.CharField(
        label=_("Active border color"),
        initial="#334155",
    )
    focus_ring_color = forms.CharField(label=_("Focus ring color"), initial="#38bdf8")
    dark_foreground_color = forms.CharField(
        label=_("Dark foreground color"),
        initial="#f8fafc",
    )
    dark_background_color = forms.CharField(
        label=_("Dark background color"),
        initial="#0f172a",
    )
    dark_border_color = forms.CharField(
        label=_("Dark border color"),
        initial="#cbd5e1",
    )
    dark_hover_foreground_color = forms.CharField(
        label=_("Dark hover foreground color"),
        initial="#f8fafc",
    )
    dark_hover_background_color = forms.CharField(
        label=_("Dark hover background color"),
        initial="#1e293b",
    )
    dark_hover_border_color = forms.CharField(
        label=_("Dark hover border color"),
        initial="#e2e8f0",
    )
    dark_active_foreground_color = forms.CharField(
        label=_("Dark active foreground color"),
        initial="#f8fafc",
    )
    dark_active_background_color = forms.CharField(
        label=_("Dark active background color"),
        initial="#334155",
    )
    dark_active_border_color = forms.CharField(
        label=_("Dark active border color"),
        initial="#f8fafc",
    )
    dark_focus_ring_color = forms.CharField(
        label=_("Dark focus ring color"),
        initial="#7dd3fc",
    )
    shadow_preset = forms.ChoiceField(
        label=_("Shadow"),
        choices=[
            ("none", _("None")),
            ("small", _("Small")),
            ("medium", _("Medium")),
            ("large", _("Large")),
        ],
        initial="medium",
        required=False,
    )
    opacity = forms.FloatField(
        label=_("Opacity"),
        initial=1.0,
        min_value=0,
        max_value=1,
        required=False,
    )
    border_width = forms.IntegerField(
        label=_("Border width (px)"),
        initial=1,
        min_value=0,
        max_value=12,
        required=False,
    )
    focus_ring_width = forms.IntegerField(
        label=_("Focus ring width (px)"),
        initial=3,
        min_value=0,
        max_value=12,
        required=False,
    )
    focus_ring_offset = forms.IntegerField(
        label=_("Focus ring offset (px)"),
        initial=3,
        min_value=0,
        max_value=12,
        required=False,
    )
    gradient_start_color = forms.CharField(
        label=_("Gradient start color"),
        initial="#0f172a",
        required=False,
    )
    gradient_end_color = forms.CharField(
        label=_("Gradient end color"),
        initial="#1e293b",
        required=False,
    )
    gradient_angle = forms.IntegerField(
        label=_("Gradient angle (deg)"),
        initial=135,
        min_value=0,
        max_value=360,
        required=False,
    )
    backdrop_blur = forms.IntegerField(
        label=_("Backdrop blur (px)"),
        initial=8,
        min_value=0,
        max_value=40,
        required=False,
    )
    size_desktop = forms.IntegerField(
        label=_("Desktop button size"),
        initial=52,
        min_value=36,
    )
    size_mobile_inherit = forms.BooleanField(
        label=_("Inherit mobile button size"),
        required=False,
        initial=True,
    )
    size_mobile = forms.IntegerField(
        label=_("Mobile button size"),
        initial=48,
        min_value=32,
    )
    icon_size_desktop = forms.IntegerField(
        label=_("Desktop icon size"),
        initial=24,
        min_value=14,
    )
    icon_size_mobile_inherit = forms.BooleanField(
        label=_("Inherit mobile icon size"),
        required=False,
        initial=True,
    )
    icon_size_mobile = forms.IntegerField(
        label=_("Mobile icon size"),
        initial=22,
        min_value=12,
    )
    collision_policy = forms.ChoiceField(
        label=_("Collision policy"),
        choices=[
            ("inherit", _("Inherit module default")),
            ("ignore", _("Ignore obstacles")),
            ("shift", _("Shift along edge")),
            ("fallback_corner", _("Try fallback corners")),
            ("hide", _("Hide when blocked")),
        ],
        initial="inherit",
        required=False,
    )
    obstacle_selectors = forms.CharField(
        label=_("Obstacle selectors"),
        required=False,
        initial="",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    obstacle_gap = forms.IntegerField(
        label=_("Obstacle gap"),
        initial=12,
        min_value=0,
        max_value=400,
        required=False,
    )
    collision_max_shift = forms.IntegerField(
        label=_("Maximum collision shift"),
        initial=240,
        min_value=0,
        max_value=2000,
        required=False,
    )
    fallback_corner_order = forms.CharField(
        label=_("Fallback corner order"),
        required=False,
        initial="",
    )
    threshold_mode = forms.ChoiceField(
        label=_("Threshold mode"),
        choices=[
            ("pixels", _("Pixels")),
            ("viewport", _("Viewport heights")),
            ("combined", _("Combined")),
        ],
        initial="pixels",
        required=False,
    )
    show_after_px = forms.IntegerField(
        label=_("Show after scroll (px)"),
        initial=240,
        min_value=0,
        max_value=100000,
        required=False,
    )
    show_after_viewports = forms.FloatField(
        label=_("Show after viewports"),
        initial=1.0,
        min_value=0,
        max_value=100,
        required=False,
    )
    min_document_height_px = forms.IntegerField(
        label=_("Minimum document height (px)"),
        initial=0,
        min_value=0,
        max_value=1000000,
        required=False,
    )
    show_delay_ms = forms.IntegerField(
        label=_("Show delay (ms)"),
        initial=0,
        min_value=0,
        max_value=10000,
        required=False,
    )
    hide_delay_ms = forms.IntegerField(
        label=_("Hide delay (ms)"),
        initial=0,
        min_value=0,
        max_value=10000,
        required=False,
    )
    visibility_direction = forms.ChoiceField(
        label=_("Visibility direction"),
        choices=[
            ("always", _("Stay visible past threshold")),
            ("scroll_up_only", _("Show only when scrolling up")),
            ("hide_on_scroll_down", _("Hide while scrolling down")),
        ],
        initial="always",
        required=False,
    )
    scroll_target_selector = forms.CharField(
        label=_("Scroll target selector"),
        required=False,
        initial="",
    )
    scroll_offset_px = forms.IntegerField(
        label=_("Scroll offset (px)"),
        initial=0,
        min_value=-10000,
        max_value=10000,
        required=False,
    )
    fixed_header_selector = forms.CharField(
        label=_("Fixed header selector"),
        required=False,
        initial="",
    )
    scroll_behavior = forms.ChoiceField(
        label=_("Scroll behavior"),
        choices=[
            ("smooth", _("Smooth")),
            ("instant", _("Instant")),
        ],
        initial="smooth",
        required=False,
    )
    allow_user_dismissal = forms.BooleanField(
        label=_("Allow user dismissal"),
        required=False,
        initial=False,
    )
    dismissal_storage = forms.ChoiceField(
        label=_("Dismissal storage"),
        choices=[
            ("local", _("Local storage")),
            ("session", _("Session storage")),
            ("cookie", _("Functional cookie")),
            ("none", _("Do not persist")),
        ],
        initial="local",
        required=False,
    )
    dismissal_duration = forms.ChoiceField(
        label=_("Dismissal duration"),
        choices=[
            ("persistent", _("Until the revision or version changes")),
            ("days", _("For a number of days")),
        ],
        initial="persistent",
        required=False,
    )
    dismissal_days = forms.IntegerField(
        label=_("Dismissal days"),
        initial=30,
        min_value=1,
        max_value=3650,
        required=False,
    )
    dismissal_requires_confirmation = forms.BooleanField(
        label=_("Confirm before dismissing"),
        required=False,
        initial=False,
    )
    dismissal_version = forms.CharField(
        label=_("Dismissal version"),
        initial="1",
        required=False,
    )

    def clean(self) -> dict[str, Any]:
        cleaned_data = cast(dict[str, Any], super().clean())
        self._validate_hex_color_field(cleaned_data, "foreground_color")
        self._validate_hex_color_field(cleaned_data, "icon_color")
        self._validate_hex_color_field(cleaned_data, "dark_icon_color")
        self._validate_hex_color_field(cleaned_data, "background_color")
        self._validate_hex_color_field(cleaned_data, "border_color")
        self._validate_hex_color_field(cleaned_data, "hover_foreground_color")
        self._validate_hex_color_field(cleaned_data, "hover_background_color")
        self._validate_hex_color_field(cleaned_data, "hover_border_color")
        self._validate_hex_color_field(cleaned_data, "active_foreground_color")
        self._validate_hex_color_field(cleaned_data, "active_background_color")
        self._validate_hex_color_field(cleaned_data, "active_border_color")
        self._validate_hex_color_field(cleaned_data, "focus_ring_color")
        self._validate_hex_color_field(cleaned_data, "dark_foreground_color")
        self._validate_hex_color_field(cleaned_data, "dark_background_color")
        self._validate_hex_color_field(cleaned_data, "dark_border_color")
        self._validate_hex_color_field(
            cleaned_data,
            "dark_hover_foreground_color",
        )
        self._validate_hex_color_field(
            cleaned_data,
            "dark_hover_background_color",
        )
        self._validate_hex_color_field(cleaned_data, "dark_hover_border_color")
        self._validate_hex_color_field(
            cleaned_data,
            "dark_active_foreground_color",
        )
        self._validate_hex_color_field(
            cleaned_data,
            "dark_active_background_color",
        )
        self._validate_hex_color_field(cleaned_data, "dark_active_border_color")
        self._validate_hex_color_field(cleaned_data, "dark_focus_ring_color")
        self._validate_hex_color_field(cleaned_data, "gradient_start_color")
        self._validate_hex_color_field(cleaned_data, "gradient_end_color")

        # Color contrast is intentionally not enforced; any colors are allowed.

        if (
            cleaned_data.get("icon_source") == "uploaded"
            and cleaned_data.get("uploaded_icon") is None
        ):
            self.add_error("uploaded_icon", _("Select an uploaded icon."))

        self._validate_obstacle_selectors(cleaned_data)
        self._validate_single_selector(cleaned_data, "scroll_target_selector")
        self._validate_single_selector(cleaned_data, "fixed_header_selector")

        custom_css = cleaned_data.get("custom_css_class")
        if (
            isinstance(custom_css, str)
            and custom_css.strip()
            and not CSS_CLASS_TOKENS_RE.match(custom_css.strip())
        ):
            self.add_error(
                "custom_css_class",
                _(
                    "Custom CSS class must be space-separated tokens of letters, "
                    "digits, hyphens, and underscores."
                ),
            )

        return cleaned_data

    def _validate_single_selector(
        self,
        cleaned_data: dict[str, Any],
        field_name: str,
    ) -> None:
        selector = cleaned_data.get(field_name)
        if not isinstance(selector, str) or not selector.strip():
            return
        candidate = selector.strip()
        if len(candidate) > _MAX_SELECTOR_LENGTH or not _SELECTOR_SAFE_RE.match(
            candidate
        ):
            self.add_error(
                field_name,
                _("Selector %(selector)s contains unsupported characters.")
                % {"selector": candidate},
            )

    def _validate_obstacle_selectors(self, cleaned_data: dict[str, Any]) -> None:
        raw_selectors = cleaned_data.get("obstacle_selectors")
        for selector in parse_obstacle_selectors(raw_selectors):
            if len(selector) > _MAX_SELECTOR_LENGTH or not _SELECTOR_SAFE_RE.match(
                selector
            ):
                self.add_error(
                    "obstacle_selectors",
                    _("Selector %(selector)s contains unsupported characters.")
                    % {"selector": selector},
                )

    def to_visual_config(self) -> VisualConfig:
        if not self.is_valid():
            raise ValidationError(_("Preview data must be valid before rendering."))

        cleaned_data = self.cleaned_data
        uploaded_icon = cleaned_data.get("uploaded_icon")
        if cleaned_data["icon_source"] == "uploaded" and uploaded_icon is None:
            raise ValidationError(
                _("Select an uploaded icon before rendering preview.")
            )
        resolved_uploaded_icon = cast(ScrollTopUploadedIcon | None, uploaded_icon)
        if cleaned_data["icon_source"] == "uploaded":
            assert resolved_uploaded_icon is not None
            resolved_icon_name = resolved_uploaded_icon.name
            resolved_icon_svg_override = resolved_uploaded_icon.renderable_svg()
        else:
            resolved_icon_name = cleaned_data["icon_name"]
            resolved_icon_svg_override = None
        configured_policy = cleaned_data.get("collision_policy") or "inherit"
        if configured_policy == "inherit":
            resolved_policy = get_scroll_to_top_settings().default_collision_policy
        else:
            resolved_policy = configured_policy
        defaults = VisualConfig()
        return VisualConfig(
            theme_mode=cleaned_data.get("theme_mode", "manual"),
            shape=cleaned_data["shape"],
            fill_variant=cleaned_data["fill_variant"],
            template_variant=cast(
                Any, cleaned_data.get("template_variant") or "icon-only"
            ),
            aria_label=(cleaned_data.get("aria_label") or "").strip()
            or defaults.aria_label,
            label_text=(cleaned_data.get("label_text") or "").strip()
            or defaults.label_text,
            custom_css_class=(cleaned_data.get("custom_css_class") or "").strip(),
            icon_name=resolved_icon_name,
            icon_style=cleaned_data["icon_style"],
            icon_source=cleaned_data["icon_source"],
            icon_svg_override=resolved_icon_svg_override,
            corner=cleaned_data["corner"],
            hot_zone_placement=cast(
                Any, cleaned_data.get("hot_zone_placement") or "none"
            ),
            hot_zone_width=(
                120
                if cleaned_data.get("hot_zone_width") is None
                else cleaned_data["hot_zone_width"]
            ),
            hot_zone_appearance=cast(
                Any, cleaned_data.get("hot_zone_appearance") or "hover"
            ),
            collision_policy=cast(Any, resolved_policy),
            obstacle_selectors=tuple(
                parse_obstacle_selectors(cleaned_data.get("obstacle_selectors"))
            ),
            obstacle_gap=(
                12
                if cleaned_data.get("obstacle_gap") is None
                else cleaned_data["obstacle_gap"]
            ),
            collision_max_shift=(
                240
                if cleaned_data.get("collision_max_shift") is None
                else cleaned_data["collision_max_shift"]
            ),
            fallback_corner_order=cast(
                Any,
                tuple(
                    parse_fallback_corner_order(
                        cleaned_data.get("fallback_corner_order")
                    )
                ),
            ),
            foreground_color=cleaned_data["foreground_color"],
            icon_color=(cleaned_data.get("icon_color") or "").strip(),
            dark_icon_color=(cleaned_data.get("dark_icon_color") or "").strip(),
            background_color=cleaned_data["background_color"],
            border_color=cleaned_data["border_color"],
            hover_foreground_color=cleaned_data["hover_foreground_color"],
            hover_background_color=cleaned_data["hover_background_color"],
            hover_border_color=cleaned_data["hover_border_color"],
            active_foreground_color=cleaned_data["active_foreground_color"],
            active_background_color=cleaned_data["active_background_color"],
            active_border_color=cleaned_data["active_border_color"],
            focus_ring_color=cleaned_data["focus_ring_color"],
            dark_foreground_color=cleaned_data["dark_foreground_color"],
            dark_background_color=cleaned_data["dark_background_color"],
            dark_border_color=cleaned_data["dark_border_color"],
            dark_hover_foreground_color=cleaned_data["dark_hover_foreground_color"],
            dark_hover_background_color=cleaned_data["dark_hover_background_color"],
            dark_hover_border_color=cleaned_data["dark_hover_border_color"],
            dark_active_foreground_color=cleaned_data["dark_active_foreground_color"],
            dark_active_background_color=cleaned_data["dark_active_background_color"],
            dark_active_border_color=cleaned_data["dark_active_border_color"],
            dark_focus_ring_color=cleaned_data["dark_focus_ring_color"],
            size=ResponsiveLength(
                desktop_px=cleaned_data["size_desktop"],
                mobile_px=(
                    None
                    if cleaned_data["size_mobile_inherit"]
                    else cleaned_data["size_mobile"]
                ),
            ),
            icon_size=ResponsiveLength(
                desktop_px=cleaned_data["icon_size_desktop"],
                mobile_px=(
                    None
                    if cleaned_data["icon_size_mobile_inherit"]
                    else cleaned_data["icon_size_mobile"]
                ),
            ),
            threshold_mode=cast(Any, cleaned_data.get("threshold_mode") or "pixels"),
            show_after_px=_int_or_default(cleaned_data.get("show_after_px"), 240),
            show_after_viewports=_float_or_default(
                cleaned_data.get("show_after_viewports"), 1.0
            ),
            min_document_height_px=_int_or_default(
                cleaned_data.get("min_document_height_px"), 0
            ),
            show_delay_ms=_int_or_default(cleaned_data.get("show_delay_ms"), 0),
            hide_delay_ms=_int_or_default(cleaned_data.get("hide_delay_ms"), 0),
            visibility_direction=cast(
                Any, cleaned_data.get("visibility_direction") or "always"
            ),
            scroll_target_selector=(
                cleaned_data.get("scroll_target_selector") or ""
            ).strip(),
            scroll_offset_px=_int_or_default(cleaned_data.get("scroll_offset_px"), 0),
            fixed_header_selector=(
                cleaned_data.get("fixed_header_selector") or ""
            ).strip(),
            scroll_behavior=cast(Any, cleaned_data.get("scroll_behavior") or "smooth"),
            allow_user_dismissal=bool(cleaned_data.get("allow_user_dismissal")),
            dismissal_storage=cast(
                Any, cleaned_data.get("dismissal_storage") or "local"
            ),
            dismissal_duration=cast(
                Any, cleaned_data.get("dismissal_duration") or "persistent"
            ),
            dismissal_days=_int_or_default(cleaned_data.get("dismissal_days"), 30),
            dismissal_requires_confirmation=bool(
                cleaned_data.get("dismissal_requires_confirmation")
            ),
            dismissal_version=(cleaned_data.get("dismissal_version") or "1").strip()
            or "1",
            shadow_preset=cast(Any, cleaned_data.get("shadow_preset") or "medium"),
            opacity=_float_or_default(cleaned_data.get("opacity"), 1.0),
            border_width=_int_or_default(cleaned_data.get("border_width"), 1),
            focus_ring_width=_int_or_default(cleaned_data.get("focus_ring_width"), 3),
            focus_ring_offset=_int_or_default(
                cleaned_data.get("focus_ring_offset"), 3
            ),
            gradient_start_color=cleaned_data.get("gradient_start_color")
            or "#0f172a",
            gradient_end_color=cleaned_data.get("gradient_end_color") or "#1e293b",
            gradient_angle=_int_or_default(cleaned_data.get("gradient_angle"), 135),
            backdrop_blur=_int_or_default(cleaned_data.get("backdrop_blur"), 8),
        )

    def _validate_hex_color_field(
        self,
        cleaned_data: dict[str, Any],
        field_name: str,
    ) -> None:
        value = cleaned_data.get(field_name)
        if not isinstance(value, str) or not value:
            return
        try:
            parse_hex_color(value)
        except ColorValidationError as exc:
            self.add_error(field_name, str(exc))

class ScrollTopUploadedIconAdminForm(forms.ModelForm):
    upload_svg = forms.FileField(
        label=_("SVG upload"),
        required=False,
        help_text=_(
            "Upload an SVG file. Only the sanitized payload is stored for rendering."
        ),
    )
    source_url = forms.URLField(
        label=_("Source URL"),
        assume_scheme="https",
    )
    license_url = forms.URLField(
        label=_("License URL"),
        required=False,
        assume_scheme="https",
    )

    class Meta:
        model = ScrollTopUploadedIcon
        fields = [
            "name",
            "style_kind",
            "color_mode",
            "stroke_width_override",
            "author",
            "source_name",
            "source_url",
            "license_name",
            "license_url",
            "copyright_notice",
            "attribution_text",
            "rights_confirmed",
            "upload_svg",
        ]

    def clean_upload_svg(self):
        uploaded_file = self.cleaned_data.get("upload_svg")
        if uploaded_file is None and self.instance.pk is None:
            raise ValidationError(_("An SVG upload is required when creating an icon."))
        if uploaded_file is None:
            return None
        if not uploaded_file.name.lower().endswith(".svg"):
            raise ValidationError(_("Only SVG uploads are supported."))
        # Reject oversized uploads before reading the whole file into memory.
        # The sanitizer enforces the same byte limit as defense in depth.
        size = getattr(uploaded_file, "size", None)
        if size is not None and size > MAX_SVG_BYTES:
            raise ValidationError(_("Uploaded SVG exceeds the maximum allowed size."))
        return uploaded_file

    def clean(self) -> dict[str, Any]:
        cleaned_data = cast(dict[str, Any], super().clean())
        uploaded_file = cleaned_data.get("upload_svg")
        if uploaded_file is not None:
            try:
                raw_svg = uploaded_file.read().decode("utf-8")
                uploaded_file.seek(0)
                self.instance.apply_uploaded_svg(
                    filename=uploaded_file.name,
                    raw_svg=raw_svg,
                    style_kind=cleaned_data.get("style_kind"),
                )
            except ValidationError as exc:
                messages = exc.message_dict.get("sanitized_svg", exc.messages)
                for message in messages:
                    self.add_error("upload_svg", message)
        return cleaned_data

    def save(self, commit: bool = True) -> ScrollTopUploadedIcon:
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance
