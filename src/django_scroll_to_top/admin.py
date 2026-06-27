from __future__ import annotations

import csv
from dataclasses import dataclass

from django import forms
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.admin_preview import render_admin_preview
from django_scroll_to_top.contrast import ColorValidationError, meets_minimum_contrast
from django_scroll_to_top.forms import (
    ScrollTopUploadedIconAdminForm,
    ScrollToTopPreviewForm,
)
from django_scroll_to_top.icons.registry import (
    builtin_icon_names,
    developer_icon_names,
    get_builtin_icon_metadata,
    get_developer_icon_metadata,
    resolve_icon,
)
from django_scroll_to_top.models import (
    ScrollTopProfile,
    ScrollTopRevision,
    ScrollTopUploadedIcon,
)
from django_scroll_to_top.services import (
    create_draft_from_revision,
    publish_revision,
    rollback_to_revision,
)
from django_scroll_to_top.site_config import invalidate_site_config_cache

# Translatable labels for the fixed icon catalog group headers, so built-in and
# developer groups localize consistently with the uploaded group. Unknown
# developer-provided groups fall through untranslated.
_ICON_GROUP_LABELS = {
    "Built-in Tabler icons": _("Built-in Tabler icons"),
    "Developer icons": _("Developer icons"),
    "Uploaded icons": _("Uploaded icons"),
}


def _translate_icon_group(group: str) -> str:
    return str(_ICON_GROUP_LABELS.get(group, group))


# Characters that spreadsheet software may treat as the start of a formula when a
# CSV cell begins with one of them (including the control characters that some
# importers strip back to a leading formula prefix).
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def _csv_safe_cell(value: object) -> object:
    """Neutralize spreadsheet formula injection for one exported CSV cell.

    Admin-editable text (icon name, author, attribution, …) is otherwise written
    verbatim. If such a value begins with a formula prefix, a spreadsheet may
    evaluate it on open; prefix it with an apostrophe so it is treated as literal
    text. Non-string values (counts, flags) are returned unchanged.
    """
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


@dataclass(frozen=True, slots=True)
class IconPickerItem:
    source: str
    value: str
    name: str
    style: str
    display_name: str
    short_description: str
    tags_label: str
    admin_group: str
    svg: str
    uploaded_icon_id: int | None = None


class ScrollTopRevisionAdminForm(forms.ModelForm):
    COLOR_FIELD_NAMES = (
        "foreground_color",
        "icon_color",
        "dark_icon_color",
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
    )

    # Compact native dropdowns for closed enumerations that the model stores as
    # plain CharFields without choices. The visual icon picker still drives
    # icon_source/icon_name; these selects keep shape/fill/corner/style readable
    # and feed the live preview directly.
    SHAPE_CHOICES = (
        ("circle", _("Circle")),
        ("square", _("Square")),
        ("rounded-square", _("Rounded square")),
        ("pill", _("Pill")),
    )
    FILL_VARIANT_CHOICES = (
        ("solid", _("Solid")),
        ("outline", _("Outline")),
        ("soft", _("Soft")),
        ("ghost", _("Ghost")),
        ("glass", _("Glass")),
        ("gradient", _("Gradient")),
    )
    CORNER_CHOICES = (
        ("bottom-right", _("Bottom right")),
        ("bottom-left", _("Bottom left")),
        ("top-right", _("Top right")),
        ("top-left", _("Top left")),
    )

    shape = forms.ChoiceField(choices=SHAPE_CHOICES, label=_("Shape"))
    fill_variant = forms.ChoiceField(
        choices=FILL_VARIANT_CHOICES, label=_("Fill variant")
    )
    corner = forms.ChoiceField(choices=CORNER_CHOICES, label=_("Button location"))

    # Fields that carry model defaults, so omitting them (for example from an
    # external integration POST) keeps the configured default rather than
    # raising "this field is required".
    COLLISION_DEFAULTS = {
        "template_variant": ScrollTopRevision.TEMPLATE_VARIANT_ICON_ONLY,
        "collision_policy": ScrollTopRevision.COLLISION_POLICY_INHERIT,
        "obstacle_gap": 12,
        "collision_max_shift": 240,
        "threshold_mode": ScrollTopRevision.THRESHOLD_MODE_PIXELS,
        "show_after_px": 240,
        "show_after_viewports": 1.0,
        "min_document_height_px": 0,
        "show_delay_ms": 0,
        "hide_delay_ms": 0,
        "visibility_direction": ScrollTopRevision.VISIBILITY_DIRECTION_ALWAYS,
        "scroll_offset_px": 0,
        "scroll_behavior": ScrollTopRevision.SCROLL_BEHAVIOR_SMOOTH,
        "dismissal_storage": ScrollTopRevision.DISMISSAL_STORAGE_LOCAL,
        "dismissal_duration": ScrollTopRevision.DISMISSAL_DURATION_PERSISTENT,
        "dismissal_days": 30,
        "dismissal_version": "1",
        "shadow_preset": ScrollTopRevision.SHADOW_PRESET_MEDIUM,
        "opacity": 1.0,
        "border_width": 1,
        "focus_ring_width": 3,
        "focus_ring_offset": 3,
        "gradient_start_color": "#0f172a",
        "gradient_end_color": "#1e293b",
        "gradient_angle": 135,
        "backdrop_blur": 8,
        "hot_zone_placement": ScrollTopRevision.HOT_ZONE_PLACEMENT_NONE,
        "hot_zone_width": 120,
        "hot_zone_appearance": ScrollTopRevision.HOT_ZONE_APPEARANCE_HOVER,
        "admin_demo_corner": ScrollTopRevision.ADMIN_DEMO_CORNER_AUTO,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field_name in self.COLOR_FIELD_NAMES:
            # Published/archived revisions render every field read-only, so the
            # editable color widgets may be absent from the form.
            if field_name not in self.fields:
                continue
            field = self.fields[field_name]
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs.update(
                {
                    "class": f"{existing_class} dstt-color-field".strip(),
                    "data-dstt-color-field": field_name,
                    "autocomplete": "off",
                    "spellcheck": "false",
                    "inputmode": "text",
                }
            )
        for field_name in self.COLLISION_DEFAULTS:
            if field_name in self.fields:
                self.fields[field_name].required = False
        # icon_name and icon_style are driven by the visual icon picker, not
        # edited by hand. Keep them submitting (readonly, unlike disabled) but
        # block manual typing.
        for picker_field in ("icon_name", "icon_style"):
            if picker_field in self.fields:
                self.fields[picker_field].widget.attrs["readonly"] = True
        if "opacity" in self.fields:
            self.fields["opacity"].widget.attrs.update(
                {"min": "0", "max": "1", "step": "0.05"}
            )

    def clean(self):
        cleaned_data = super().clean() or {}
        for field_name, default in self.COLLISION_DEFAULTS.items():
            value = cleaned_data.get(field_name)
            if value in (None, ""):
                cleaned_data[field_name] = default
        return cleaned_data

    class Meta:
        model = ScrollTopRevision
        fields = [
            "name",
            "profile",
            "custom_css_class",
            "icon_source",
            "theme_mode",
            "shape",
            "fill_variant",
            "template_variant",
            "aria_label",
            "label_text",
            "icon_name",
            "uploaded_icon",
            "icon_style",
            "corner",
            "hot_zone_placement",
            "hot_zone_width",
            "hot_zone_appearance",
            "admin_demo_corner",
            "foreground_color",
            "icon_color",
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
            "dark_icon_color",
            "dark_background_color",
            "dark_border_color",
            "dark_hover_foreground_color",
            "dark_hover_background_color",
            "dark_hover_border_color",
            "dark_active_foreground_color",
            "dark_active_background_color",
            "dark_active_border_color",
            "dark_focus_ring_color",
            "shadow_preset",
            "opacity",
            "border_width",
            "focus_ring_width",
            "focus_ring_offset",
            "gradient_start_color",
            "gradient_end_color",
            "gradient_angle",
            "backdrop_blur",
            "size_desktop",
            "size_mobile_inherit",
            "size_mobile",
            "icon_size_desktop",
            "icon_size_mobile_inherit",
            "icon_size_mobile",
            "collision_policy",
            "obstacle_selectors",
            "obstacle_gap",
            "collision_max_shift",
            "fallback_corner_order",
            "threshold_mode",
            "show_after_px",
            "show_after_viewports",
            "min_document_height_px",
            "show_delay_ms",
            "hide_delay_ms",
            "visibility_direction",
            "scroll_target_selector",
            "scroll_offset_px",
            "fixed_header_selector",
            "scroll_behavior",
            "allow_user_dismissal",
            "dismissal_storage",
            "dismissal_duration",
            "dismissal_days",
            "dismissal_requires_confirmation",
            "dismissal_version",
        ]


@admin.register(ScrollTopRevision)
class ScrollTopRevisionAdmin(admin.ModelAdmin):
    form = ScrollTopRevisionAdminForm
    list_display = (
        "name",
        "profile",
        "status",
        "theme_mode",
        "shape",
        "fill_variant",
        "icon_name",
        "updated_at",
    )
    list_filter = ("status", "profile")
    actions = (
        "publish_selected_revisions",
        "create_draft_from_selected",
        "rollback_to_selected_revision",
    )
    readonly_fields = (
        "status",
        "published_at",
        "created_by",
        "created_at",
        "updated_at",
    )
    change_form_template = (
        "admin/django_scroll_to_top/scrolltoprevision/change_form.html"
    )
    class Media:
        css = {"all": ("django_scroll_to_top/admin-icon-picker.css",)}
        js = ("django_scroll_to_top/admin-icon-picker.js",)

    fieldsets = (
        (
            _("Identity"),
            {"fields": ("name", "profile", "custom_css_class")},
        ),
        (
            _("Visual style"),
            {
                "fields": (
                    "icon_source",
                    "theme_mode",
                    "shape",
                    "fill_variant",
                    "template_variant",
                    "aria_label",
                    "label_text",
                    "icon_name",
                    "uploaded_icon",
                    "icon_style",
                    "corner",
                )
            },
        ),
        (
            _("Placement and side click zone"),
            {
                "fields": (
                    "hot_zone_placement",
                    "hot_zone_width",
                    "hot_zone_appearance",
                    "admin_demo_corner",
                )
            },
        ),
        (
            _("Colors"),
            {
                # Interleaved light/dark pairs so the two-column grid (see
                # admin-icon-picker.css) renders light theme on the left and the
                # matching dark-theme override directly to its right.
                "classes": ("dstt-colors-grid",),
                "fields": (
                    "foreground_color",
                    "dark_foreground_color",
                    "icon_color",
                    "dark_icon_color",
                    "background_color",
                    "dark_background_color",
                    "border_color",
                    "dark_border_color",
                    "hover_foreground_color",
                    "dark_hover_foreground_color",
                    "hover_background_color",
                    "dark_hover_background_color",
                    "hover_border_color",
                    "dark_hover_border_color",
                    "active_foreground_color",
                    "dark_active_foreground_color",
                    "active_background_color",
                    "dark_active_background_color",
                    "active_border_color",
                    "dark_active_border_color",
                    "focus_ring_color",
                    "dark_focus_ring_color",
                )
            },
        ),
        (
            _("Styling"),
            {
                "fields": (
                    "shadow_preset",
                    "opacity",
                    "border_width",
                    "focus_ring_width",
                    "focus_ring_offset",
                    "gradient_start_color",
                    "gradient_end_color",
                    "gradient_angle",
                    "backdrop_blur",
                )
            },
        ),
        (
            _("Responsive sizing"),
            {
                "fields": (
                    "size_desktop",
                    "size_mobile_inherit",
                    "size_mobile",
                    "icon_size_desktop",
                    "icon_size_mobile_inherit",
                    "icon_size_mobile",
                )
            },
        ),
        (
            _("Collision avoidance"),
            {
                "fields": (
                    "collision_policy",
                    "obstacle_selectors",
                    "obstacle_gap",
                    "collision_max_shift",
                    "fallback_corner_order",
                )
            },
        ),
        (
            _("Visibility"),
            {
                "fields": (
                    "threshold_mode",
                    "show_after_px",
                    "show_after_viewports",
                    "min_document_height_px",
                    "show_delay_ms",
                    "hide_delay_ms",
                    "visibility_direction",
                )
            },
        ),
        (
            _("Scrolling"),
            {
                "fields": (
                    "scroll_target_selector",
                    "scroll_offset_px",
                    "fixed_header_selector",
                    "scroll_behavior",
                )
            },
        ),
        (
            _("User dismissal"),
            {
                "fields": (
                    "allow_user_dismissal",
                    "dismissal_storage",
                    "dismissal_duration",
                    "dismissal_days",
                    "dismissal_requires_confirmation",
                    "dismissal_version",
                )
            },
        ),
        (
            _("Lifecycle"),
            {
                "fields": (
                    "status",
                    "published_at",
                    "created_by",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Archived revisions are immutable snapshots kept for rollback: lock
        # every editable field so admins create a new draft instead. Draft and
        # published revisions stay editable in place.
        if obj is not None and obj.status == ScrollTopRevision.STATUS_ARCHIVED:
            editable = [
                field.name
                for field in self.model._meta.fields
                if field.editable and field.name != "id"
            ]
            for field_name in editable:
                if field_name not in readonly:
                    readonly.append(field_name)
        return tuple(readonly)

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        self._warn_low_contrast(request, obj)
        # Editing a published revision in place changes the live configuration,
        # so invalidate the resolved-config cache for its scope. Publishing goes
        # through services and invalidates on its own.
        if (
            obj.status == ScrollTopRevision.STATUS_PUBLISHED
            and obj.profile_id is not None
        ):
            invalidate_site_config_cache(scope=obj.profile.scope)

    def _warn_low_contrast(self, request, obj: ScrollTopRevision) -> None:
        # Non-blocking accessibility hint. Only meaningful for fills where the
        # background color is the actual surface.
        if obj.fill_variant not in {"solid", "soft"}:
            return
        light_fg = obj.icon_color or obj.foreground_color
        dark_fg = obj.dark_icon_color or obj.dark_foreground_color
        try:
            low = not meets_minimum_contrast(
                light_fg, obj.background_color
            ) or not meets_minimum_contrast(dark_fg, obj.dark_background_color)
        except ColorValidationError:
            return
        if low:
            self.message_user(
                request,
                _(
                    "Heads up: the icon/foreground and background colors are below "
                    "a 3:1 contrast ratio, which can hurt legibility. Saved anyway."
                ),
                level="warning",
            )

    @admin.action(description=_("Publish selected revision"))
    def publish_selected_revisions(self, request, queryset):
        published = 0
        for revision in queryset:
            if revision.profile_id is None:
                self.message_user(
                    request,
                    _("Skipped %(name)s: assign a profile before publishing.")
                    % {"name": revision.name},
                    level="warning",
                )
                continue
            publish_revision(revision, user=request.user)
            published += 1
        if published:
            self.message_user(
                request,
                _("Published %(count)d revision(s).") % {"count": published},
            )

    @admin.action(description=_("Create draft from selected revision"))
    def create_draft_from_selected(self, request, queryset):
        created = 0
        for revision in queryset:
            create_draft_from_revision(revision, user=request.user)
            created += 1
        self.message_user(
            request,
            _("Created %(count)d draft revision(s).") % {"count": created},
        )

    @admin.action(description=_("Roll back by re-publishing selected revision"))
    def rollback_to_selected_revision(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                _("Select exactly one revision to roll back to."),
                level="warning",
            )
            return
        revision = queryset.first()
        if revision.profile_id is None:
            self.message_user(
                request,
                _("Assign a profile before rolling back."),
                level="warning",
            )
            return
        rollback_to_revision(revision, user=request.user)
        self.message_user(request, _("Rolled back to the selected revision."))

    def render_change_form(
        self,
        request: HttpRequest,
        context,
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: ScrollTopRevision | None = None,
    ) -> HttpResponse:
        if (
            obj is not None
            and request.method == "GET"
            and obj.status == ScrollTopRevision.STATUS_PUBLISHED
        ):
            messages.info(
                request,
                _(
                    "This revision is published. Saving changes here updates the "
                    "live configuration directly. Use “Create draft from selected "
                    "revision” first if you would rather stage changes."
                ),
            )
        elif (
            obj is not None
            and request.method == "GET"
            and obj.status == ScrollTopRevision.STATUS_ARCHIVED
        ):
            messages.warning(
                request,
                _(
                    "This archived revision is read-only. To reuse it, select it "
                    "in the revision list and run “Create draft from selected "
                    "revision”, edit the new draft, then publish it."
                ),
            )
        picker_state = self._picker_state(request, obj)
        context["preview_html"] = self._build_preview_html(request, obj)
        context["icon_picker_items"] = self._icon_picker_items()
        context["icon_picker_state"] = picker_state
        context["dstt_field_defaults"] = self._form_field_defaults()
        context["dstt_reset_labels"] = {
            "reset": str(_("Reset section to defaults")),
            "saved": str(_("Restore last saved")),
        }
        context["dstt_ui_labels"] = {
            "icon_size_exceeds": str(
                _(
                    "Icon size {icon} px is larger than the button size {button} px; "
                    "it may overflow the button."
                )
            ),
            "icon_size_clamped": str(
                _("Icon size reduced to the button size ({button} px).")
            ),
            "show_demo": str(_("Show demo button again")),
            "clear_color": str(_("Clear color override")),
            "colors_light": str(_("Light theme")),
            "colors_dark": str(_("Dark theme")),
        }
        return super().render_change_form(
            request,
            context,
            add=add,
            change=change,
            form_url=form_url,
            obj=obj,
        )

    def _build_preview_html(
        self,
        request,
        obj: ScrollTopRevision | None,
    ) -> str:
        if request.method == "POST":
            preview_form = ScrollToTopPreviewForm(data=request.POST)
            if not preview_form.is_valid():
                # A failed save should not blank the preview: fall back to the
                # last saved configuration (or defaults) so it stays visible.
                fallback = (
                    obj.to_preview_data()
                    if obj is not None
                    else self._default_preview_data()
                )
                preview_form = ScrollToTopPreviewForm(data=fallback)
        elif obj is not None:
            preview_form = ScrollToTopPreviewForm(data=obj.to_preview_data())
        else:
            preview_form = ScrollToTopPreviewForm(data=self._default_preview_data())

        if not preview_form.is_valid():
            return ""
        return render_admin_preview(preview_form)

    def _default_preview_data(self) -> dict[str, object]:
        return ScrollTopRevision(name="Preview").to_preview_data()

    def _picker_state(
        self,
        request: HttpRequest,
        obj: ScrollTopRevision | None,
    ) -> dict[str, str]:
        if request.method == "POST":
            data = request.POST
            return {
                "icon_source": data.get("icon_source", "builtin"),
                "icon_name": data.get("icon_name", "arrow-up"),
                "icon_style": data.get("icon_style", "outline"),
                "uploaded_icon": data.get("uploaded_icon", ""),
                "shape": data.get("shape", "circle"),
                "fill_variant": data.get("fill_variant", "solid"),
            }

        preview_data = (
            obj.to_preview_data() if obj is not None else self._default_preview_data()
        )
        return {
            "icon_source": str(preview_data["icon_source"]),
            "icon_name": str(preview_data["icon_name"]),
            "icon_style": str(preview_data["icon_style"]),
            "uploaded_icon": str(preview_data["uploaded_icon"]),
            "shape": str(preview_data["shape"]),
            "fill_variant": str(preview_data["fill_variant"]),
        }

    def _icon_picker_items(self) -> list[IconPickerItem]:
        items: list[IconPickerItem] = []
        for style, names in builtin_icon_names().items():
            for name in names:
                metadata = get_builtin_icon_metadata(name)
                items.append(
                    IconPickerItem(
                        source="builtin",
                        value=name,
                        name=name,
                        style=style,
                        display_name=metadata.display_name,
                        short_description=metadata.short_description,
                        tags_label=", ".join(metadata.tags),
                        admin_group=_translate_icon_group(metadata.admin_group),
                        svg=self._picker_svg(resolve_icon(name=name, style=style).svg),
                    )
                )

        for style, names in developer_icon_names().items():
            for name in names:
                metadata = get_developer_icon_metadata(name, style)
                items.append(
                    IconPickerItem(
                        source="developer",
                        value=name,
                        name=name,
                        style=style,
                        display_name=metadata.display_name,
                        short_description=metadata.short_description,
                        tags_label=", ".join(metadata.tags),
                        admin_group=_translate_icon_group(metadata.admin_group),
                        svg=self._picker_svg(
                            resolve_icon(name=name, style=style, source="developer").svg
                        ),
                    )
                )

        for icon in ScrollTopUploadedIcon.objects.order_by("name"):
            items.append(
                IconPickerItem(
                    source="uploaded",
                    value=str(icon.pk),
                    name=icon.name,
                    style=icon.style_kind,
                    display_name=icon.name,
                    short_description=str(
                        _("Uploaded icon provided by %(author)s.")
                        % {"author": icon.author}
                    ),
                    tags_label=", ".join(
                        [
                            icon.style_kind,
                            "uploaded",
                            icon.color_mode,
                            "strokeWidth"
                            if icon.supports_stroke_width
                            else "fixedStroke",
                        ]
                    ),
                    admin_group=_translate_icon_group("Uploaded icons"),
                    svg=self._picker_svg(icon.renderable_svg()),
                    uploaded_icon_id=icon.pk,
                )
            )
        return items

    def _picker_svg(self, svg: str) -> str:
        safe_svg = svg
        if "aria-hidden=" not in safe_svg:
            safe_svg = safe_svg.replace(
                "<svg",
                '<svg aria-hidden="true" focusable="false"',
                1,
            )
        if 'class="' in safe_svg:
            safe_svg = safe_svg.replace('class="', 'class="dstt-icon-picker__svg ', 1)
        else:
            safe_svg = safe_svg.replace("<svg", '<svg class="dstt-icon-picker__svg"', 1)
        return mark_safe(safe_svg)

    def _form_field_defaults(self) -> dict[str, object]:
        """Model defaults for editable fields, for the per-section reset buttons."""
        defaults: dict[str, object] = {}
        for field in ScrollTopRevision._meta.concrete_fields:
            if not field.editable or field.name == "id":
                continue
            default = field.get_default()
            if callable(default):
                continue
            defaults[field.name] = default
        return defaults

@admin.register(ScrollTopUploadedIcon)
class ScrollTopUploadedIconAdmin(admin.ModelAdmin):
    form = ScrollTopUploadedIconAdminForm
    list_display = (
        "name",
        "style_kind",
        "color_mode",
        "supports_current_color",
        "supports_stroke_width",
        "stroke_width_override",
        "original_filename",
        "updated_at",
    )
    actions = ("export_attribution_report",)
    readonly_fields = (
        "original_filename",
        "original_view_box",
        "normalized_view_box",
        "original_checksum",
        "sanitized_checksum",
        "supports_current_color",
        "supports_stroke_width",
        "rights_notice",
        "sanitized_svg_preview",
    )
    fieldsets = (
        (
            _("Identity"),
            {
                "fields": (
                    "name",
                    "style_kind",
                    "color_mode",
                    "stroke_width_override",
                )
            },
        ),
        (
            _("Source metadata"),
            {
                "fields": (
                    "author",
                    "source_name",
                    "source_url",
                    "license_name",
                    "license_url",
                    "copyright_notice",
                    "attribution_text",
                    "rights_confirmed",
                    "rights_notice",
                )
            },
        ),
        (
            _("Upload"),
            {
                "fields": (
                    "upload_svg",
                    "original_filename",
                    "original_view_box",
                    "normalized_view_box",
                    "supports_current_color",
                    "supports_stroke_width",
                    "original_checksum",
                    "sanitized_checksum",
                    "sanitized_svg_preview",
                )
            },
        ),
    )

    @admin.display(description=_("Sanitized preview"))
    def sanitized_svg_preview(self, obj: ScrollTopUploadedIcon) -> str:
        if not obj.sanitized_svg:
            return ""
        return (
            '<div class="dstt-uploaded-icon-preview" '
            'style="max-width: 6rem; padding: 0.75rem; border: 1px solid #cbd5e1;">'
            f"{obj.renderable_svg()}"
            "</div>"
        )

    @admin.display(description=_("License notice"))
    def rights_notice(self, obj: ScrollTopUploadedIcon | None = None) -> str:
        return str(
            _(
                "Uploading and sanitizing an SVG does not mark it as free or "
                "open content. The site operator remains responsible for having "
                "the right to use and distribute the icon."
            )
        )

    @admin.action(description=_("Export icon attribution report"))
    def export_attribution_report(
        self,
        request: HttpRequest,
        queryset,
    ) -> HttpResponse:
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = (
            'attachment; filename="scroll-to-top-icon-attribution.csv"'
        )
        writer = csv.writer(response)
        writer.writerow(
            [
                "name",
                "style_kind",
                "color_mode",
                "usage_count",
                "author",
                "source_name",
                "source_url",
                "license_name",
                "license_url",
                "copyright_notice",
                "attribution_text",
                "rights_confirmed",
            ]
        )
        for icon in queryset.order_by("name"):
            writer.writerow(
                [
                    _csv_safe_cell(icon.name),
                    _csv_safe_cell(icon.style_kind),
                    _csv_safe_cell(icon.color_mode),
                    icon.revisions.count(),
                    _csv_safe_cell(icon.author),
                    _csv_safe_cell(icon.source_name),
                    _csv_safe_cell(icon.source_url),
                    _csv_safe_cell(icon.license_name),
                    _csv_safe_cell(icon.license_url),
                    _csv_safe_cell(icon.copyright_notice),
                    _csv_safe_cell(icon.attribution_text),
                    "yes" if icon.rights_confirmed else "no",
                ]
            )
        return response


@admin.register(ScrollTopProfile)
class ScrollTopProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "scope",
        "site_id",
        "is_enabled",
        "published_revision",
        "updated_at",
    )
    list_filter = ("scope", "is_enabled")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Identity"),
            {"fields": ("name", "scope", "site_id", "is_enabled")},
        ),
        (
            _("Publication"),
            {"fields": ("published_revision",)},
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at")},
        ),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Only revisions belonging to this profile are valid publish targets.
        if db_field.name == "published_revision":
            match = request.resolver_match
            object_id = match.kwargs.get("object_id") if match else None
            if object_id is not None:
                kwargs["queryset"] = ScrollTopRevision.objects.filter(
                    profile_id=object_id
                )
            else:
                kwargs["queryset"] = ScrollTopRevision.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
