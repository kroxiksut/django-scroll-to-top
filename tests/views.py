from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.template import Context, Template


def sample_page(request: HttpRequest) -> HttpResponse:
    template = Template("{% load scroll_to_top %}{% scroll_to_top %}")
    rendered = template.render(
        Context(
            {
                "request": request,
                "csp_nonce": "nonce-123",
            }
        )
    )
    response = HttpResponse(rendered)
    response["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; script-src 'self' 'nonce-nonce-123'"
    )
    return response
