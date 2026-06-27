from __future__ import annotations

from django.contrib import admin

from demo.library.models import ReadingCollection, ReadingEntry


class ReadingEntryInline(admin.StackedInline):
    model = ReadingEntry
    extra = 0
    fields = ("title", "slug", "excerpt", "body", "sort_order", "featured")
    show_change_link = True


@admin.register(ReadingCollection)
class ReadingCollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "slug")
    list_editable = ("sort_order",)
    list_filter = ("sort_order",)
    search_fields = ("title", "slug", "summary", "notes")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ReadingEntryInline]
    fieldsets = (
        (
            "Content",
            {
                "fields": ("title", "slug", "summary", "notes"),
            },
        ),
        (
            "Display",
            {
                "fields": ("sort_order",),
            },
        ),
    )


@admin.register(ReadingEntry)
class ReadingEntryAdmin(admin.ModelAdmin):
    list_display = ("title", "collection", "sort_order", "featured")
    list_editable = ("sort_order", "featured")
    list_filter = ("collection", "featured")
    search_fields = ("title", "slug", "excerpt", "body", "collection__title")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (
            "Content",
            {
                "fields": ("collection", "title", "slug", "excerpt", "body"),
            },
        ),
        (
            "Display",
            {
                "fields": ("sort_order", "featured"),
            },
        ),
    )

