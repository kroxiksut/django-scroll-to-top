from __future__ import annotations

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.contrast import (
    ColorValidationError,
    parse_hex_color,
)
from django_scroll_to_top.icons.recolor import (
    SvgRecolorError,
    analyze_recolor_support,
    apply_stroke_width,
    recolor_svg,
)
from django_scroll_to_top.icons.sanitizer import (
    SvgSanitizationError,
    sanitize_uploaded_svg,
)
from django_scroll_to_top.presentation import VisualConfig

# A conservative allowlist for integration CSS class tokens: space-separated
# words of letters, digits, hyphens, and underscores only.
CSS_CLASS_TOKENS_RE = re.compile(r"^[A-Za-z0-9_-]+(?: [A-Za-z0-9_-]+)*$")

SCOPE_SITE = "site"
SCOPE_ADMIN = "admin"
SCOPE_CHOICES = (
    (SCOPE_SITE, _("Site")),
    (SCOPE_ADMIN, _("Django Admin")),
)


class ScrollTopProfile(models.Model):
    """One configuration profile per (scope, optional Site).

    A profile is a stable coordination record: it owns the scope, an optional
    Sites Framework ``site_id`` and a pointer to the currently published
    revision. Visual and behavioral values live on :class:`ScrollTopRevision`.
    """

    scope = models.CharField(
        max_length=16,
        choices=SCOPE_CHOICES,
        default=SCOPE_SITE,
        verbose_name=_("Scope"),
    )
    # Stored as a plain integer instead of a hard FK so the package keeps
    # working without ``django.contrib.sites`` installed.
    site_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Site ID"),
        help_text=_(
            "Optional Sites Framework site id. Leave empty for the global "
            "profile that applies when no site-specific profile exists."
        ),
    )
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled"),
        help_text=_("Business decision to show the control for this scope now."),
    )
    published_revision = models.ForeignKey(
        "django_scroll_to_top.ScrollTopRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("Published revision"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Scroll-to-top profile")
        verbose_name_plural = _("Scroll-to-top profiles")
        constraints = [
            models.UniqueConstraint(
                fields=["scope", "site_id"],
                condition=Q(site_id__isnull=False),
                name="dstt_unique_scope_site",
            ),
            models.UniqueConstraint(
                fields=["scope"],
                condition=Q(site_id__isnull=True),
                name="dstt_unique_scope_global",
            ),
        ]

    def __str__(self) -> str:
        target = _("global") if self.site_id is None else f"site {self.site_id}"
        return f"{self.name} ({self.scope}, {target})"


class ScrollTopRevision(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = (
        (STATUS_DRAFT, _("Draft")),
        (STATUS_PUBLISHED, _("Published")),
        (STATUS_ARCHIVED, _("Archived")),
    )

    ICON_SOURCE_BUILTIN = "builtin"
    ICON_SOURCE_DEVELOPER = "developer"
    ICON_SOURCE_UPLOADED = "uploaded"
    ICON_SOURCE_CHOICES = (
        (ICON_SOURCE_BUILTIN, _("Built-in")),
        (ICON_SOURCE_DEVELOPER, _("Developer")),
        (ICON_SOURCE_UPLOADED, _("Uploaded")),
    )
    THEME_MODE_MANUAL = "manual"
    THEME_MODE_INHERIT_ADMIN = "inherit_admin_theme"
    THEME_MODE_CHOICES = (
        (THEME_MODE_MANUAL, _("Manual")),
        (THEME_MODE_INHERIT_ADMIN, _("Inherit admin theme")),
    )
    COLLISION_POLICY_INHERIT = "inherit"
    COLLISION_POLICY_IGNORE = "ignore"
    COLLISION_POLICY_SHIFT = "shift"
    COLLISION_POLICY_FALLBACK_CORNER = "fallback_corner"
    COLLISION_POLICY_HIDE = "hide"
    COLLISION_POLICY_CHOICES = (
        (COLLISION_POLICY_INHERIT, _("Inherit module default")),
        (COLLISION_POLICY_IGNORE, _("Ignore obstacles")),
        (COLLISION_POLICY_SHIFT, _("Shift along edge")),
        (COLLISION_POLICY_FALLBACK_CORNER, _("Try fallback corners")),
        (COLLISION_POLICY_HIDE, _("Hide when blocked")),
    )
    THRESHOLD_MODE_PIXELS = "pixels"
    THRESHOLD_MODE_VIEWPORT = "viewport"
    THRESHOLD_MODE_COMBINED = "combined"
    THRESHOLD_MODE_CHOICES = (
        (THRESHOLD_MODE_PIXELS, _("Pixels")),
        (THRESHOLD_MODE_VIEWPORT, _("Viewport heights")),
        (THRESHOLD_MODE_COMBINED, _("Combined")),
    )
    VISIBILITY_DIRECTION_ALWAYS = "always"
    VISIBILITY_DIRECTION_SCROLL_UP_ONLY = "scroll_up_only"
    VISIBILITY_DIRECTION_HIDE_ON_SCROLL_DOWN = "hide_on_scroll_down"
    VISIBILITY_DIRECTION_CHOICES = (
        (VISIBILITY_DIRECTION_ALWAYS, _("Stay visible past threshold")),
        (VISIBILITY_DIRECTION_SCROLL_UP_ONLY, _("Show only when scrolling up")),
        (VISIBILITY_DIRECTION_HIDE_ON_SCROLL_DOWN, _("Hide while scrolling down")),
    )
    SCROLL_BEHAVIOR_SMOOTH = "smooth"
    SCROLL_BEHAVIOR_INSTANT = "instant"
    SCROLL_BEHAVIOR_CHOICES = (
        (SCROLL_BEHAVIOR_SMOOTH, _("Smooth")),
        (SCROLL_BEHAVIOR_INSTANT, _("Instant")),
    )
    DISMISSAL_STORAGE_LOCAL = "local"
    DISMISSAL_STORAGE_SESSION = "session"
    DISMISSAL_STORAGE_COOKIE = "cookie"
    DISMISSAL_STORAGE_NONE = "none"
    DISMISSAL_STORAGE_CHOICES = (
        (DISMISSAL_STORAGE_LOCAL, _("Local storage")),
        (DISMISSAL_STORAGE_SESSION, _("Session storage")),
        (DISMISSAL_STORAGE_COOKIE, _("Functional cookie")),
        (DISMISSAL_STORAGE_NONE, _("Do not persist")),
    )
    SHADOW_PRESET_NONE = "none"
    SHADOW_PRESET_SMALL = "small"
    SHADOW_PRESET_MEDIUM = "medium"
    SHADOW_PRESET_LARGE = "large"
    SHADOW_PRESET_CHOICES = (
        (SHADOW_PRESET_NONE, _("None")),
        (SHADOW_PRESET_SMALL, _("Small")),
        (SHADOW_PRESET_MEDIUM, _("Medium")),
        (SHADOW_PRESET_LARGE, _("Large")),
    )
    TEMPLATE_VARIANT_ICON_ONLY = "icon-only"
    TEMPLATE_VARIANT_ICON_LABEL = "icon-label"
    TEMPLATE_VARIANT_CHOICES = (
        (TEMPLATE_VARIANT_ICON_ONLY, _("Icon only")),
        (TEMPLATE_VARIANT_ICON_LABEL, _("Icon with label")),
    )
    DISMISSAL_DURATION_PERSISTENT = "persistent"
    DISMISSAL_DURATION_DAYS = "days"
    DISMISSAL_DURATION_CHOICES = (
        (DISMISSAL_DURATION_PERSISTENT, _("Until the revision or version changes")),
        (DISMISSAL_DURATION_DAYS, _("For a number of days")),
    )
    HOT_ZONE_PLACEMENT_NONE = "none"
    HOT_ZONE_PLACEMENT_BUTTON = "button"
    HOT_ZONE_PLACEMENT_LEFT = "left"
    HOT_ZONE_PLACEMENT_RIGHT = "right"
    HOT_ZONE_PLACEMENT_CHOICES = (
        (HOT_ZONE_PLACEMENT_NONE, _("Disabled")),
        (HOT_ZONE_PLACEMENT_BUTTON, _("Same side as the button")),
        (HOT_ZONE_PLACEMENT_LEFT, _("Left edge")),
        (HOT_ZONE_PLACEMENT_RIGHT, _("Right edge")),
    )
    HOT_ZONE_APPEARANCE_HOVER = "hover"
    HOT_ZONE_APPEARANCE_HIDDEN = "hidden"
    HOT_ZONE_APPEARANCE_VISIBLE = "visible"
    HOT_ZONE_APPEARANCE_CHOICES = (
        (HOT_ZONE_APPEARANCE_HOVER, _("Invisible, highlight on hover")),
        (HOT_ZONE_APPEARANCE_HIDDEN, _("Fully invisible")),
        (HOT_ZONE_APPEARANCE_VISIBLE, _("Always slightly visible")),
    )
    ADMIN_DEMO_CORNER_AUTO = "auto"
    ADMIN_DEMO_CORNER_CHOICES = (
        (ADMIN_DEMO_CORNER_AUTO, _("Auto (opposite the admin button)")),
        ("top-left", _("Top left")),
        ("top-right", _("Top right")),
        ("bottom-left", _("Bottom left")),
        ("bottom-right", _("Bottom right")),
    )

    profile = models.ForeignKey(
        "django_scroll_to_top.ScrollTopProfile",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="revisions",
        verbose_name=_("Profile"),
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name=_("Status"),
        help_text=_(
            "Draft and published revisions are editable; editing a published "
            "revision updates the live configuration directly. Archived "
            "revisions are immutable snapshots kept for rollback."
        ),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        editable=False,
        verbose_name=_("Created by"),
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Published at"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    shape = models.CharField(
        max_length=32,
        default="circle",
        verbose_name=_("Shape"),
    )
    fill_variant = models.CharField(
        max_length=32,
        default="solid",
        verbose_name=_("Fill variant"),
    )
    template_variant = models.CharField(
        max_length=16,
        choices=TEMPLATE_VARIANT_CHOICES,
        default=TEMPLATE_VARIANT_ICON_ONLY,
        verbose_name=_("Template variant"),
        help_text=_("Icon only, or an icon with a visible label."),
    )
    aria_label = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name=_("Accessible name"),
        help_text=_(
            "Optional accessible name override. Leave empty to use the safe "
            "translated default."
        ),
    )
    label_text = models.CharField(
        max_length=60,
        blank=True,
        default="",
        verbose_name=_("Visible label"),
        help_text=_(
            "Visible label text for the icon-with-label variant. Stored as-is and "
            "not auto-translated; leave empty to fall back to the translated "
            "accessible name, or use a per-site profile for multilingual sites."
        ),
    )
    custom_css_class = models.CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name=_("Custom CSS class"),
        help_text=_(
            "Optional space-separated CSS class tokens added to the control "
            "wrapper for project integration. Letters, digits, hyphen, underscore."
        ),
    )
    icon_name = models.CharField(
        max_length=64,
        default="arrow-up",
        verbose_name=_("Icon"),
        help_text=_("Set by the icon picker below; not edited by hand."),
    )
    icon_style = models.CharField(
        max_length=16,
        default="outline",
        verbose_name=_("Icon style"),
    )
    icon_source = models.CharField(
        max_length=16,
        choices=ICON_SOURCE_CHOICES,
        default=ICON_SOURCE_BUILTIN,
        verbose_name=_("Icon source"),
        help_text=_(
            "Built-in: vendored Tabler subset. Developer: icons registered in "
            "code. Uploaded: sanitized SVGs added in the admin."
        ),
    )
    theme_mode = models.CharField(
        max_length=32,
        choices=THEME_MODE_CHOICES,
        default=THEME_MODE_MANUAL,
        verbose_name=_("Theme mode"),
        help_text=_(
            "Use explicit colors, or inherit supported Django Admin theme "
            "variables with safe fallbacks."
        ),
    )
    uploaded_icon = models.ForeignKey(
        "django_scroll_to_top.ScrollTopUploadedIcon",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="revisions",
        verbose_name=_("Uploaded icon"),
    )
    corner = models.CharField(
        max_length=32,
        default="bottom-right",
        verbose_name=_("Button location"),
    )
    hot_zone_placement = models.CharField(
        max_length=8,
        choices=HOT_ZONE_PLACEMENT_CHOICES,
        default=HOT_ZONE_PLACEMENT_NONE,
        verbose_name=_("Side click zone"),
        help_text=_(
            "Optional full-height clickable strip along a screen edge that also "
            "scrolls to top. The button sits inside the strip."
        ),
    )
    hot_zone_width = models.PositiveIntegerField(
        default=120,
        verbose_name=_("Side click zone width (px)"),
    )
    hot_zone_appearance = models.CharField(
        max_length=8,
        choices=HOT_ZONE_APPEARANCE_CHOICES,
        default=HOT_ZONE_APPEARANCE_HOVER,
        verbose_name=_("Side click zone appearance"),
    )
    admin_demo_corner = models.CharField(
        max_length=16,
        choices=ADMIN_DEMO_CORNER_CHOICES,
        default=ADMIN_DEMO_CORNER_AUTO,
        verbose_name=_("Demo button location in admin"),
        help_text=_(
            "Where the floating demo button sits while editing in the admin. "
            "Does not affect the live site. Auto picks the corner opposite the "
            "admin's own button."
        ),
    )
    foreground_color = models.CharField(
        max_length=7,
        default="#ffffff",
        verbose_name=_("Foreground color"),
        help_text=_("Icon and label color (the SVG inherits it via currentColor)."),
    )
    icon_color = models.CharField(
        max_length=7,
        blank=True,
        default="",
        verbose_name=_("Icon color override"),
        help_text=_(
            "Optional color for the SVG icon only. Leave empty to use the "
            "foreground color. The icon must use currentColor to pick this up."
        ),
    )
    dark_icon_color = models.CharField(
        max_length=7,
        blank=True,
        default="",
        verbose_name=_("Dark icon color override"),
        help_text=_("Optional dark-theme icon color. Empty inherits the icon color."),
    )
    background_color = models.CharField(
        max_length=7,
        default="#0f172a",
        verbose_name=_("Background color"),
    )
    border_color = models.CharField(
        max_length=7,
        default="#0f172a",
        verbose_name=_("Border color"),
    )
    hover_foreground_color = models.CharField(
        max_length=7,
        default="#ffffff",
        verbose_name=_("Hover foreground color"),
    )
    hover_background_color = models.CharField(
        max_length=7,
        default="#1e293b",
        verbose_name=_("Hover background color"),
    )
    hover_border_color = models.CharField(
        max_length=7,
        default="#1e293b",
        verbose_name=_("Hover border color"),
    )
    active_foreground_color = models.CharField(
        max_length=7,
        default="#ffffff",
        verbose_name=_("Active foreground color"),
    )
    active_background_color = models.CharField(
        max_length=7,
        default="#334155",
        verbose_name=_("Active background color"),
    )
    active_border_color = models.CharField(
        max_length=7,
        default="#334155",
        verbose_name=_("Active border color"),
    )
    focus_ring_color = models.CharField(
        max_length=7,
        default="#38bdf8",
        verbose_name=_("Focus ring color"),
    )
    dark_foreground_color = models.CharField(
        max_length=7,
        default="#f8fafc",
        verbose_name=_("Dark foreground color"),
    )
    dark_background_color = models.CharField(
        max_length=7,
        default="#0f172a",
        verbose_name=_("Dark background color"),
    )
    dark_border_color = models.CharField(
        max_length=7,
        default="#cbd5e1",
        verbose_name=_("Dark border color"),
    )
    dark_hover_foreground_color = models.CharField(
        max_length=7,
        default="#f8fafc",
        verbose_name=_("Dark hover foreground color"),
    )
    dark_hover_background_color = models.CharField(
        max_length=7,
        default="#1e293b",
        verbose_name=_("Dark hover background color"),
    )
    dark_hover_border_color = models.CharField(
        max_length=7,
        default="#e2e8f0",
        verbose_name=_("Dark hover border color"),
    )
    dark_active_foreground_color = models.CharField(
        max_length=7,
        default="#f8fafc",
        verbose_name=_("Dark active foreground color"),
    )
    dark_active_background_color = models.CharField(
        max_length=7,
        default="#334155",
        verbose_name=_("Dark active background color"),
    )
    dark_active_border_color = models.CharField(
        max_length=7,
        default="#f8fafc",
        verbose_name=_("Dark active border color"),
    )
    dark_focus_ring_color = models.CharField(
        max_length=7,
        default="#7dd3fc",
        verbose_name=_("Dark focus ring color"),
    )
    shadow_preset = models.CharField(
        max_length=16,
        choices=SHADOW_PRESET_CHOICES,
        default=SHADOW_PRESET_MEDIUM,
        verbose_name=_("Shadow"),
    )
    opacity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_("Opacity"),
        help_text=_("Control opacity from 0 (transparent) to 1 (opaque)."),
    )
    border_width = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Border width (px)"),
    )
    focus_ring_width = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Focus ring width (px)"),
    )
    focus_ring_offset = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Focus ring offset (px)"),
    )
    gradient_start_color = models.CharField(
        max_length=7,
        default="#0f172a",
        verbose_name=_("Gradient start color"),
        help_text=_("Used by the gradient fill variant."),
    )
    gradient_end_color = models.CharField(
        max_length=7,
        default="#1e293b",
        verbose_name=_("Gradient end color"),
    )
    gradient_angle = models.PositiveIntegerField(
        default=135,
        verbose_name=_("Gradient angle (deg)"),
    )
    backdrop_blur = models.PositiveIntegerField(
        default=8,
        verbose_name=_("Backdrop blur (px)"),
        help_text=_("Used by the glass fill variant where the browser supports it."),
    )
    size_desktop = models.PositiveIntegerField(
        default=52,
        verbose_name=_("Desktop button size"),
    )
    size_mobile_inherit = models.BooleanField(
        default=True,
        verbose_name=_("Inherit mobile button size"),
    )
    size_mobile = models.PositiveIntegerField(
        default=48,
        verbose_name=_("Mobile button size"),
    )
    icon_size_desktop = models.PositiveIntegerField(
        default=24,
        verbose_name=_("Desktop icon size"),
    )
    icon_size_mobile_inherit = models.BooleanField(
        default=True,
        verbose_name=_("Inherit mobile icon size"),
    )
    icon_size_mobile = models.PositiveIntegerField(
        default=22,
        verbose_name=_("Mobile icon size"),
    )
    collision_policy = models.CharField(
        max_length=20,
        choices=COLLISION_POLICY_CHOICES,
        default=COLLISION_POLICY_INHERIT,
        verbose_name=_("Collision policy"),
        help_text=_(
            "How the control reacts when it overlaps a floating obstacle. "
            "Inherit uses DJANGO_SCROLL_TO_TOP['DEFAULT_COLLISION_POLICY']."
        ),
    )
    obstacle_selectors = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Obstacle selectors"),
        help_text=_(
            "Optional CSS selectors of floating obstacles, one per line. Elements "
            "marked with [data-scroll-top-obstacle] are always included."
        ),
    )
    obstacle_gap = models.PositiveIntegerField(
        default=12,
        verbose_name=_("Obstacle gap"),
        help_text=_("Minimum gap in pixels kept between the control and an obstacle."),
    )
    collision_max_shift = models.PositiveIntegerField(
        default=240,
        verbose_name=_("Maximum collision shift"),
        help_text=_("Maximum automatic displacement in pixels before giving up."),
    )
    fallback_corner_order = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name=_("Fallback corner order"),
        help_text=_(
            "Optional ordered corners tried by the fallback_corner policy, "
            "separated by spaces or commas (for example: bottom-left top-right)."
        ),
    )
    threshold_mode = models.CharField(
        max_length=16,
        choices=THRESHOLD_MODE_CHOICES,
        default=THRESHOLD_MODE_PIXELS,
        verbose_name=_("Threshold mode"),
        help_text=_(
            "Show the control after a pixel distance, a number of viewport "
            "heights, or both combined."
        ),
    )
    show_after_px = models.PositiveIntegerField(
        default=240,
        verbose_name=_("Show after scroll (px)"),
    )
    show_after_viewports = models.FloatField(
        default=1.0,
        verbose_name=_("Show after viewports"),
        help_text=_("Number of viewport heights scrolled before showing."),
    )
    min_document_height_px = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Minimum document height (px)"),
        help_text=_("Do not show the control on documents shorter than this."),
    )
    show_delay_ms = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Show delay (ms)"),
    )
    hide_delay_ms = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Hide delay (ms)"),
    )
    visibility_direction = models.CharField(
        max_length=20,
        choices=VISIBILITY_DIRECTION_CHOICES,
        default=VISIBILITY_DIRECTION_ALWAYS,
        verbose_name=_("Visibility direction"),
        help_text=_(
            "Stay visible past the threshold, show only while scrolling up, or "
            "hide while scrolling down."
        ),
    )
    scroll_target_selector = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name=_("Scroll target selector"),
        help_text=_(
            "Optional CSS selector to scroll to. Falls back to the top of the "
            "document when empty or not found."
        ),
    )
    scroll_offset_px = models.IntegerField(
        default=0,
        verbose_name=_("Scroll offset (px)"),
        help_text=_("Extra vertical offset applied to the scroll target."),
    )
    fixed_header_selector = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name=_("Fixed header selector"),
        help_text=_(
            "Optional CSS selector of a fixed header whose height is subtracted "
            "from the scroll position."
        ),
    )
    scroll_behavior = models.CharField(
        max_length=16,
        choices=SCROLL_BEHAVIOR_CHOICES,
        default=SCROLL_BEHAVIOR_SMOOTH,
        verbose_name=_("Scroll behavior"),
        help_text=_(
            "Native smooth scrolling or an instant jump. Reduced-motion users "
            "always get an instant jump."
        ),
    )
    allow_user_dismissal = models.BooleanField(
        default=False,
        verbose_name=_("Allow user dismissal"),
        help_text=_("Show a close control so visitors can hide the button."),
    )
    dismissal_storage = models.CharField(
        max_length=16,
        choices=DISMISSAL_STORAGE_CHOICES,
        default=DISMISSAL_STORAGE_LOCAL,
        verbose_name=_("Dismissal storage"),
        help_text=_(
            "Where an anonymous visitor's dismissal is remembered. Local/session "
            "storage and functional cookies stay client-side."
        ),
    )
    dismissal_duration = models.CharField(
        max_length=16,
        choices=DISMISSAL_DURATION_CHOICES,
        default=DISMISSAL_DURATION_PERSISTENT,
        verbose_name=_("Dismissal duration"),
    )
    dismissal_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Dismissal days"),
        help_text=_("Days a dismissal lasts when the duration is day-based."),
    )
    dismissal_requires_confirmation = models.BooleanField(
        default=False,
        verbose_name=_("Confirm before dismissing"),
        help_text=_("Ask the visitor to confirm before hiding the button."),
    )
    dismissal_version = models.CharField(
        max_length=32,
        default="1",
        verbose_name=_("Dismissal version"),
        help_text=_(
            "Bump this to intentionally re-show the button to visitors who "
            "previously dismissed it."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Scroll-to-top revision")
        verbose_name_plural = _("Scroll-to-top revisions")

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if self.pk is not None:
            persisted_status = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            # Archived revisions stay immutable so rollback keeps an exact
            # historical snapshot. Draft and published revisions are editable in
            # place: editing a published revision updates the live configuration
            # directly instead of forcing a draft clone.
            if persisted_status == self.STATUS_ARCHIVED:
                raise ValidationError(
                    _(
                        "Archived revisions are immutable. Create a new draft "
                        "from this revision to make changes."
                    )
                )
        if self.custom_css_class and not CSS_CLASS_TOKENS_RE.match(
            self.custom_css_class.strip()
        ):
            raise ValidationError(
                {
                    "custom_css_class": _(
                        "Custom CSS class must be space-separated tokens of "
                        "letters, digits, hyphens, and underscores."
                    )
                }
            )
        for field_name in (
            "foreground_color",
            "background_color",
            "border_color",
            "hover_foreground_color",
            "hover_background_color",
            "hover_border_color",
            "active_foreground_color",
            "active_background_color",
            "active_border_color",
            "focus_ring_color",
            "dark_foreground_color",
            "dark_background_color",
            "dark_border_color",
            "dark_hover_foreground_color",
            "dark_hover_background_color",
            "dark_hover_border_color",
            "dark_active_foreground_color",
            "dark_active_background_color",
            "dark_active_border_color",
            "dark_focus_ring_color",
            "gradient_start_color",
            "gradient_end_color",
        ):
            value = getattr(self, field_name)
            try:
                parse_hex_color(value)
            except ColorValidationError as exc:
                raise ValidationError({field_name: str(exc)}) from exc

        # Icon color overrides are optional; validate only when provided.
        for field_name in ("icon_color", "dark_icon_color"):
            value = getattr(self, field_name)
            if not value:
                continue
            try:
                parse_hex_color(value)
            except ColorValidationError as exc:
                raise ValidationError({field_name: str(exc)}) from exc

        # Color contrast is no longer enforced here: operators may pick any
        # colors. Low-contrast combinations are surfaced as a non-blocking admin
        # warning instead (see ScrollTopRevisionAdmin) and via the optional
        # scroll_to_top_check_contrast management command.

    def to_preview_data(self) -> dict[str, object]:
        return {
            "shape": self.shape,
            "fill_variant": self.fill_variant,
            "template_variant": self.template_variant,
            "aria_label": self.aria_label,
            "label_text": self.label_text,
            "custom_css_class": self.custom_css_class,
            "icon_source": self.icon_source,
            "theme_mode": self.theme_mode,
            "icon_name": self.icon_name,
            "uploaded_icon": (
                "" if self.uploaded_icon is None else self.uploaded_icon.pk
            ),
            "icon_style": self.icon_style,
            "corner": self.corner,
            "hot_zone_placement": self.hot_zone_placement,
            "hot_zone_width": self.hot_zone_width,
            "hot_zone_appearance": self.hot_zone_appearance,
            "foreground_color": self.foreground_color,
            "icon_color": self.icon_color,
            "dark_icon_color": self.dark_icon_color,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "hover_foreground_color": self.hover_foreground_color,
            "hover_background_color": self.hover_background_color,
            "hover_border_color": self.hover_border_color,
            "active_foreground_color": self.active_foreground_color,
            "active_background_color": self.active_background_color,
            "active_border_color": self.active_border_color,
            "focus_ring_color": self.focus_ring_color,
            "dark_foreground_color": self.dark_foreground_color,
            "dark_background_color": self.dark_background_color,
            "dark_border_color": self.dark_border_color,
            "dark_hover_foreground_color": self.dark_hover_foreground_color,
            "dark_hover_background_color": self.dark_hover_background_color,
            "dark_hover_border_color": self.dark_hover_border_color,
            "dark_active_foreground_color": self.dark_active_foreground_color,
            "dark_active_background_color": self.dark_active_background_color,
            "dark_active_border_color": self.dark_active_border_color,
            "dark_focus_ring_color": self.dark_focus_ring_color,
            "shadow_preset": self.shadow_preset,
            "opacity": self.opacity,
            "border_width": self.border_width,
            "focus_ring_width": self.focus_ring_width,
            "focus_ring_offset": self.focus_ring_offset,
            "gradient_start_color": self.gradient_start_color,
            "gradient_end_color": self.gradient_end_color,
            "gradient_angle": self.gradient_angle,
            "backdrop_blur": self.backdrop_blur,
            "size_desktop": self.size_desktop,
            "size_mobile_inherit": self.size_mobile_inherit,
            "size_mobile": self.size_mobile,
            "icon_size_desktop": self.icon_size_desktop,
            "icon_size_mobile_inherit": self.icon_size_mobile_inherit,
            "icon_size_mobile": self.icon_size_mobile,
            "collision_policy": self.collision_policy,
            "obstacle_selectors": self.obstacle_selectors,
            "obstacle_gap": self.obstacle_gap,
            "collision_max_shift": self.collision_max_shift,
            "fallback_corner_order": self.fallback_corner_order,
            "threshold_mode": self.threshold_mode,
            "show_after_px": self.show_after_px,
            "show_after_viewports": self.show_after_viewports,
            "min_document_height_px": self.min_document_height_px,
            "show_delay_ms": self.show_delay_ms,
            "hide_delay_ms": self.hide_delay_ms,
            "visibility_direction": self.visibility_direction,
            "scroll_target_selector": self.scroll_target_selector,
            "scroll_offset_px": self.scroll_offset_px,
            "fixed_header_selector": self.fixed_header_selector,
            "scroll_behavior": self.scroll_behavior,
            "allow_user_dismissal": self.allow_user_dismissal,
            "dismissal_storage": self.dismissal_storage,
            "dismissal_duration": self.dismissal_duration,
            "dismissal_days": self.dismissal_days,
            "dismissal_requires_confirmation": self.dismissal_requires_confirmation,
            "dismissal_version": self.dismissal_version,
        }

    def to_visual_config(self) -> VisualConfig:
        from django_scroll_to_top.forms import ScrollToTopPreviewForm

        form = ScrollToTopPreviewForm(data=self.to_preview_data())
        if not form.is_valid():
            raise ValidationError(form.errors)
        return form.to_visual_config()


class ScrollTopUploadedIcon(models.Model):
    STYLE_KIND_OUTLINE = "outline"
    STYLE_KIND_FILLED = "filled"
    STYLE_KIND_MULTICOLOR = "multicolor"
    STYLE_KIND_ORIGINAL = "original"
    COLOR_MODE_RECOLOR = "recolor"
    COLOR_MODE_PRESERVE = "preserve"
    STYLE_KIND_CHOICES = (
        (STYLE_KIND_OUTLINE, _("Outline")),
        (STYLE_KIND_FILLED, _("Filled")),
        (STYLE_KIND_MULTICOLOR, _("Multicolor")),
        (STYLE_KIND_ORIGINAL, _("Original")),
    )
    COLOR_MODE_CHOICES = (
        (COLOR_MODE_RECOLOR, _("Recolor")),
        (COLOR_MODE_PRESERVE, _("Preserve original colors")),
    )

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    style_kind = models.CharField(
        max_length=16,
        choices=STYLE_KIND_CHOICES,
        default=STYLE_KIND_OUTLINE,
        verbose_name=_("Style kind"),
    )
    color_mode = models.CharField(
        max_length=16,
        choices=COLOR_MODE_CHOICES,
        default=COLOR_MODE_RECOLOR,
        verbose_name=_("Color mode"),
        help_text=_(
            "Recolor outline and filled icons via currentColor, or preserve "
            "safe uploaded colors."
        ),
    )
    author = models.CharField(max_length=200, verbose_name=_("Author"))
    source_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name=_("Source name"),
    )
    source_url = models.URLField(verbose_name=_("Source URL"))
    license_name = models.CharField(max_length=200, verbose_name=_("License"))
    license_url = models.URLField(
        blank=True,
        default="",
        verbose_name=_("License URL"),
    )
    copyright_notice = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Copyright notice"),
    )
    attribution_text = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Attribution text"),
    )
    rights_confirmed = models.BooleanField(
        default=False,
        verbose_name=_("Rights confirmed"),
        help_text=_(
            "The uploader confirms that the project may use and distribute this "
            "icon. Uploading and sanitizing the file does not make it free to use."
        ),
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_("Original filename"),
    )
    original_view_box = models.CharField(max_length=100, editable=False, default="")
    normalized_view_box = models.CharField(max_length=100, editable=False, default="")
    original_checksum = models.CharField(max_length=64, editable=False)
    sanitized_checksum = models.CharField(max_length=64, editable=False)
    sanitized_svg = models.TextField(verbose_name=_("Sanitized SVG"))
    supports_current_color = models.BooleanField(default=False, editable=False)
    supports_stroke_width = models.BooleanField(default=False, editable=False)
    stroke_width_override = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Stroke width override"),
        help_text=_(
            "Optional normalized stroke width applied only to uploaded icons "
            "that already define stroke-width attributes."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Uploaded scroll-to-top icon")
        verbose_name_plural = _("Uploaded scroll-to-top icons")

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if not self.rights_confirmed:
            raise ValidationError(
                {"rights_confirmed": _("You must confirm the right to use this icon.")}
            )
        if self.stroke_width_override is not None and not self.supports_stroke_width:
            raise ValidationError(
                {
                    "stroke_width_override": _(
                        "Only uploaded icons with explicit stroke-width "
                        "attributes can use a stroke width override."
                    )
                }
            )
        if (
            self.style_kind in {self.STYLE_KIND_MULTICOLOR, self.STYLE_KIND_ORIGINAL}
            and self.color_mode == self.COLOR_MODE_RECOLOR
        ):
            raise ValidationError(
                {
                    "color_mode": _(
                        "Multicolor and original uploaded icons must preserve "
                        "their safe colors."
                    )
                }
            )
        requires_sanitized_svg = bool(self.original_filename) or not self._state.adding
        if requires_sanitized_svg and not self.sanitized_svg:
            raise ValidationError(
                {"sanitized_svg": _("A sanitized SVG payload is required.")}
            )
        if self.sanitized_svg and self.color_mode == self.COLOR_MODE_RECOLOR:
            try:
                recolor_svg(self.sanitized_svg, style_kind=self.style_kind)
            except SvgRecolorError as exc:
                raise ValidationError({"color_mode": str(exc)}) from exc

    def apply_uploaded_svg(
        self,
        *,
        filename: str,
        raw_svg: str,
        style_kind: str | None = None,
    ) -> None:
        try:
            sanitized = sanitize_uploaded_svg(raw_svg)
        except SvgSanitizationError as exc:
            raise ValidationError({"sanitized_svg": str(exc)}) from exc
        resolved_style_kind = style_kind or self.style_kind
        analysis = analyze_recolor_support(
            sanitized.svg,
            style_kind=resolved_style_kind,
        )

        self.original_filename = filename
        self.original_view_box = sanitized.original_view_box
        self.normalized_view_box = sanitized.normalized_view_box
        self.original_checksum = sanitized.original_checksum
        self.sanitized_checksum = sanitized.sanitized_checksum
        self.sanitized_svg = sanitized.svg
        self.supports_current_color = analysis.supports_recolor
        self.supports_stroke_width = sanitized.supports_stroke_width
        if resolved_style_kind in {
            self.STYLE_KIND_MULTICOLOR,
            self.STYLE_KIND_ORIGINAL,
        }:
            self.color_mode = self.COLOR_MODE_PRESERVE
        elif not self.color_mode:
            self.color_mode = self.COLOR_MODE_RECOLOR

    def renderable_svg(self) -> str:
        svg = self.sanitized_svg
        if self.color_mode == self.COLOR_MODE_RECOLOR:
            svg = recolor_svg(svg, style_kind=self.style_kind)
        if self.stroke_width_override is not None and self.supports_stroke_width:
            svg = apply_stroke_width(
                svg,
                stroke_width=f"{self.stroke_width_override:.2f}".rstrip("0").rstrip("."),
            )
        return svg
