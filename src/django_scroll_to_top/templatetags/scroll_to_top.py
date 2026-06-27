from __future__ import annotations

from django import template
from django.template import TemplateSyntaxError
from django.templatetags.static import static
from django.urls import reverse

from django_scroll_to_top.renderer import render_scroll_to_top
from django_scroll_to_top.settings import (
    get_scroll_to_top_settings,
    resolve_csp_nonce,
)
from django_scroll_to_top.site_config import resolve_site_config

register = template.Library()

_ASSET_CONTEXT_KEY = "django_scroll_to_top_assets_rendered"
_CONTROL_CONTEXT_KEY = "django_scroll_to_top_control_rendered"


@register.inclusion_tag(
    "django_scroll_to_top/includes/scroll_to_top_tag.html",
    takes_context=True,
)
def scroll_to_top(
    context: template.Context,
    scope: str = "site",
) -> dict[str, str]:
    render_context = context.render_context
    if render_context.get(_CONTROL_CONTEXT_KEY, False):
        return {"stylesheet_url": "", "script_url": "", "rendered_markup": ""}

    render_context[_CONTROL_CONTEXT_KEY] = True
    stylesheet_url = ""
    dynamic_stylesheet_url = ""
    script_url = ""
    script_nonce = ""
    if not render_context.get(_ASSET_CONTEXT_KEY, False):
        render_context[_ASSET_CONTEXT_KEY] = True
        stylesheet_url = static("django_scroll_to_top/scroll-to-top.min.css")
        script_url = static("django_scroll_to_top/scroll-to-top.min.js")
        if get_scroll_to_top_settings().csp_mode == "nonce":
            script_nonce = resolve_csp_nonce(context)

    request = context.get("request") or getattr(context, "request", None)
    try:
        resolved = resolve_site_config(request=request, scope=scope)
    except ValueError as exc:
        raise TemplateSyntaxError(str(exc)) from exc
    if resolved is None:
        return {
            "stylesheet_url": "",
            "dynamic_stylesheet_url": "",
            "script_url": "",
            "script_nonce": "",
            "rendered_markup": "",
        }

    dynamic_stylesheet_url = reverse(
        "django_scroll_to_top:site-stylesheet",
        kwargs={"version": resolved.version},
    )
    return {
        "stylesheet_url": stylesheet_url,
        "dynamic_stylesheet_url": dynamic_stylesheet_url,
        "script_url": script_url,
        "script_nonce": script_nonce,
        "rendered_markup": render_scroll_to_top(
            resolved.visual_config,
            style_token=resolved.version,
            scope=resolved.scope,
            site_id=resolved.site_id,
        ),
    }
