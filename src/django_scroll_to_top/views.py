from __future__ import annotations

from django.http import Http404, HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_GET

from django_scroll_to_top.site_config import resolve_site_config
from django_scroll_to_top.styles import build_component_stylesheet


@require_GET
def site_stylesheet(request: HttpRequest, version: str) -> HttpResponse:
    resolved = resolve_site_config(request=request)
    if resolved is None or resolved.version != version:
        raise Http404("No stylesheet is available for this version.")

    selector = f'.dstt-control-wrap[data-dstt-config="{resolved.version}"]'
    response = HttpResponse(
        build_component_stylesheet(
            config=resolved.visual_config,
            selector=selector,
        ),
        content_type="text/css; charset=utf-8",
    )
    patch_cache_control(response, public=True, max_age=31536000, immutable=True)
    return response
