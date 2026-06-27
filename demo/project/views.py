from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from demo.library.models import ReadingCollection


def home(request: HttpRequest) -> HttpResponse:
    collections = (
        ReadingCollection.objects.prefetch_related("entries")
        .order_by("sort_order", "title")
    )
    return render(
        request,
        "demo/home.html",
        {
            "collections": collections,
        },
    )


def obstacles(request: HttpRequest) -> HttpResponse:
    return render(request, "demo/obstacles.html")


def collection_detail(request: HttpRequest, slug: str) -> HttpResponse:
    collection = get_object_or_404(
        ReadingCollection.objects.prefetch_related("entries").order_by(
            "sort_order", "title"
        ),
        slug=slug,
    )
    return render(
        request,
        "demo/collection_detail.html",
        {
            "collection": collection,
        },
    )

