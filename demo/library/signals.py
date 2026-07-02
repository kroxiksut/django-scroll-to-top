from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.utils import timezone

from demo.library.models import ReadingCollection, ReadingEntry
from django_scroll_to_top.models import ScrollTopProfile, ScrollTopRevision
from django_scroll_to_top.services import publish_revision
from django_scroll_to_top.site_config import invalidate_site_config_cache


def _body(*paragraphs: str) -> str:
    return "\n\n".join(paragraphs)


DEMO_COLLECTIONS = [
    {
        "title": "Morning Notes",
        "slug": "morning-notes",
        "summary": (
            "A measured opening set of long-form notes for the public demo page."
        ),
        "notes": (
            "This collection is intentionally verbose so the page requires a real"
            " amount of scrolling before the footer appears."
        ),
        "sort_order": 10,
        "entries": [
            {
                "title": "Opening Brief",
                "slug": "opening-brief",
                "excerpt": (
                    "The opening notes establish the pace and give the first scroll"
                    " test a clean runway."
                ),
                "body": _body(
                    "The demo starts with deliberately original prose so the public"
                    " page stays free to reuse and still provides meaningful length.",
                    "Each section adds a different cadence, which keeps the page from"
                    " feeling like a repeated block of filler while still building"
                    " enough distance for scroll controls to matter.",
                    "Once the scroll-to-top control is connected, this paragraph block"
                    " will give it a clear, stable target to return to at the top of"
                    " the document.",
                ),
                "sort_order": 10,
                "featured": True,
            },
            {
                "title": "Reading Pace",
                "slug": "reading-pace",
                "excerpt": (
                    "The second note keeps the page moving without rushing through"
                    " the content."
                ),
                "body": _body(
                    "A useful demo page needs ordinary language that can be read"
                    " comfortably while still occupying enough vertical space to"
                    " exercise the viewport.",
                    "Short headings, balanced paragraphs, and a consistent rhythm make"
                    " it easy to judge whether the layout remains readable after the"
                    " scroll button is introduced.",
                    "The same page also doubles as a basic admin dataset, which means"
                    " the change list and change form can both demonstrate a long"
                    " surface in the Django backend.",
                ),
                "sort_order": 20,
                "featured": False,
            },
            {
                "title": "Spacing Study",
                "slug": "spacing-study",
                "excerpt": (
                    "More text here creates a realistic block for testing spacing and"
                    " readability."
                ),
                "body": _body(
                    "Spacing matters because a control that is visually present but"
                    " difficult to reach fails the purpose of the demo.",
                    "The sections below keep enough padding between ideas so the page"
                    " remains calm while still being long enough to scroll several"
                    " screenfuls.",
                    "That makes this collection useful even before the package button"
                    " is attached, because the page already behaves like a real"
                    " document rather than a placeholder.",
                ),
                "sort_order": 30,
                "featured": False,
            },
            {
                "title": "Return Path",
                "slug": "return-path",
                "excerpt": (
                    "This note closes the first collection with an explicit return"
                    " path back to the top."
                ),
                "body": _body(
                    "The end of the first collection should leave the reader with a"
                    " clear sense of where to go next and where to return from once"
                    " the page grows long.",
                    "In a later step the scroll-to-top control can live on top of this"
                    " structure without any extra scaffolding, because the demo page"
                    " already contains the necessary distance and visual variety.",
                    "Until then, the content is still useful as a plain reading sample"
                    " and as a quick way to make the public page feel complete.",
                ),
                "sort_order": 40,
                "featured": False,
            },
        ],
    },
    {
        "title": "Reference Shelf",
        "slug": "reference-shelf",
        "summary": (
            "A denser set of entries for the admin changelist and detail screens."
        ),
        "notes": (
            "This collection is slightly more structured so the admin form has"
            " multiple fields and inline entries to scroll through."
        ),
        "sort_order": 20,
        "entries": [
            {
                "title": "Index Cards",
                "slug": "index-cards",
                "excerpt": (
                    "A compact card set gives the admin list a second long page."
                ),
                "body": _body(
                    "The reference shelf is intentionally more structured than the"
                    " morning notes so the admin interface has enough material to"
                    " show nested records and long change forms.",
                    "This collection contains denser copy, but the language stays"
                    " simple and original so the content remains easy to understand.",
                    "That mix gives the demo a useful contrast between a lighter public"
                    " page and a more record-heavy administration surface.",
                ),
                "sort_order": 10,
                "featured": True,
            },
            {
                "title": "Field Record",
                "slug": "field-record",
                "excerpt": (
                    "The field record adds detail and gives the inline editor more"
                    " body text to carry."
                ),
                "body": _body(
                    "A long body field is especially helpful in admin because it forces"
                    " the page to stretch vertically in a way that mirrors real"
                    " editorial work.",
                    "The demo therefore includes paragraphs that are long enough to"
                    " require careful scrolling without becoming hard to read or"
                    " depending on any external source text.",
                    "When the scroll control is connected later, this will be one of"
                    " the cleanest places to verify that it remains available on a"
                    " full backend page.",
                ),
                "sort_order": 20,
                "featured": False,
            },
            {
                "title": "Margin Study",
                "slug": "margin-study",
                "excerpt": (
                    "A margin study makes the page feel editorial and stretches the"
                    " admin view further."
                ),
                "body": _body(
                    "The admin change screen has to support fieldsets, inlines, and"
                    " enough real data that the scroll button can be seen in context.",
                    "Longer copy in the body field helps prove that the page is a"
                    " genuine content surface rather than a synthetic control"
                    " panel.",
                    "That is especially useful for the demo because the user can"
                    " test both the public page and the backend in the same browser"
                    " session.",
                ),
                "sort_order": 30,
                "featured": False,
            },
            {
                "title": "Archive Cue",
                "slug": "archive-cue",
                "excerpt": (
                    "The archive cue keeps the collection long enough for multiple"
                    " screen heights."
                ),
                "body": _body(
                    "The final entry in this collection gives the admin and public"
                    " pages one more substantial block to render so the scroll state"
                    " feels natural.",
                    "It also keeps the data model small and understandable, which is"
                    " useful while the demo site is still being assembled.",
                    "A future step can wire in the actual package control without"
                    " changing any of this content structure.",
                ),
                "sort_order": 40,
                "featured": False,
            },
        ],
    },
    {
        "title": "Longform Archive",
        "slug": "longform-archive",
        "summary": (
            "A final long collection that keeps the public page comfortably tall."
        ),
        "notes": (
            "This set is intentionally the largest one so the admin changelist and"
            " detail page both have a lot of distance to cover."
        ),
        "sort_order": 30,
        "entries": [
            {
                "title": "Archive Opening",
                "slug": "archive-opening",
                "excerpt": (
                    "The archive opens with a broad overview and a long reading"
                    " surface."
                ),
                "body": _body(
                    "The archive collection extends the public page enough that a"
                    " back-to-top control will be immediately useful once it is"
                    " connected.",
                    "It also offers a simple administrative structure: a long list of"
                    " entries, each with enough text to make the changelist and form"
                    " pleasant to test by hand.",
                    "Because the text is original, the demo does not depend on any"
                    " external content source or license beyond the repository's own"
                    " terms.",
                ),
                "sort_order": 10,
                "featured": True,
            },
            {
                "title": "Section Review",
                "slug": "section-review",
                "excerpt": (
                    "A section review breaks the archive into readable chunks."
                ),
                "body": _body(
                    "Breaking the archive into sections helps keep the long page"
                    " manageable while still making the scroll length honest.",
                    "That balance is useful for a demo because it lets the admin and"
                    " public layouts feel like real pages rather than test fixtures.",
                    "The scroll control can later sit on top of this structure with no"
                    " additional content changes.",
                ),
                "sort_order": 20,
                "featured": False,
            },
            {
                "title": "Deep Scroll",
                "slug": "deep-scroll",
                "excerpt": (
                    "This entry is long enough to make the viewport move through"
                    " several distinct sections."
                ),
                "body": _body(
                    "A deep scroll test is easier to reason about when the page uses"
                    " natural English paragraphs instead of repeated filler text.",
                    "That way the demo still feels like a plausible local site even"
                    " before the package button is added.",
                    "The same structure also makes it simpler to inspect the admin"
                    " changelist, because the backend content is obvious and easy to"
                    " recognize.",
                ),
                "sort_order": 30,
                "featured": False,
            },
            {
                "title": "Closing Notes",
                "slug": "closing-notes",
                "excerpt": (
                    "The closing notes finish the archive with another substantial"
                    " block of text."
                ),
                "body": _body(
                    "The last block keeps the archive readable while preserving the"
                    " long page height needed for a convincing scroll demo.",
                    "Since the admin and public views both use the same records, the"
                    " demo site stays small enough to maintain but broad enough to"
                    " show a meaningful amount of structure.",
                    "That makes it a practical staging ground for the actual control"
                    " once you want to connect it in a follow-up step.",
                ),
                "sort_order": 40,
                "featured": False,
            },
        ],
    },
]


def seed_demo_content() -> None:
    user_model = get_user_model()
    admin_user, _ = user_model.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "first_name": "Demo",
            "last_name": "Admin",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    admin_user.email = "admin@example.com"
    admin_user.first_name = "Demo"
    admin_user.last_name = "Admin"
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.set_password("admin")
    admin_user.save()

    for collection_data in DEMO_COLLECTIONS:
        entries = collection_data["entries"]
        collection, _ = ReadingCollection.objects.update_or_create(
            slug=collection_data["slug"],
            defaults={
                "title": collection_data["title"],
                "summary": collection_data["summary"],
                "notes": collection_data["notes"],
                "sort_order": collection_data["sort_order"],
            },
        )
        for entry_data in entries:
            ReadingEntry.objects.update_or_create(
                collection=collection,
                slug=entry_data["slug"],
                defaults={
                    "title": entry_data["title"],
                    "excerpt": entry_data["excerpt"],
                    "body": entry_data["body"],
                    "sort_order": entry_data["sort_order"],
                    "featured": entry_data["featured"],
                },
            )

    _seed_scroll_to_top_defaults(admin_user=admin_user)


def _seed_scroll_to_top_defaults(*, admin_user) -> None:
    defaults = (("site", "Public default"), ("admin", "Admin default"))
    for scope, name in defaults:
        profile, _ = ScrollTopProfile.objects.get_or_create(
            scope=scope,
            site_id=None,
            defaults={
                "name": name,
                "is_enabled": True,
            },
        )
        updates: list[str] = []
        if profile.name != name:
            profile.name = name
            updates.append("name")
        if not profile.is_enabled:
            profile.is_enabled = True
            updates.append("is_enabled")
        if updates:
            profile.save(update_fields=updates)
        revision_defaults = _scroll_to_top_revision_defaults(name=name)
        # The live revision is derived from status, not a stored pointer.
        revision = profile.revisions.filter(status="published").first()
        if revision is not None:
            revision_updates: list[str] = []
            for field_name, value in revision_defaults.items():
                if getattr(revision, field_name) != value:
                    setattr(revision, field_name, value)
                    revision_updates.append(field_name)
            if revision_updates:
                revision.save(update_fields=revision_updates)
            continue
        revision = ScrollTopRevision.objects.create(
            profile=profile,
            created_by=admin_user,
            **revision_defaults,
        )
        publish_revision(revision, user=admin_user)


def _scroll_to_top_revision_defaults(*, name: str) -> dict[str, object]:
    # The demo uses one public-looking palette for both scopes so the admin
    # button starts as a faithful preview of the public control. Changing the
    # admin revision then immediately syncs the public site to the same values.
    return {
        "name": name,
        "theme_mode": ScrollTopRevision.THEME_MODE_MANUAL,
        "icon_name": "arrow-big-up",
        "icon_style": "filled",
        "icon_source": ScrollTopRevision.ICON_SOURCE_BUILTIN,
        "shape": "circle",
        "fill_variant": "solid",
        "template_variant": ScrollTopRevision.TEMPLATE_VARIANT_ICON_ONLY,
        "corner": "bottom-right",
        "foreground_color": "#f8fafc",
        "background_color": "#0f766e",
        "border_color": "#115e59",
        "hover_foreground_color": "#ffffff",
        "hover_background_color": "#115e59",
        "hover_border_color": "#115e59",
        "active_foreground_color": "#ffffff",
        "active_background_color": "#134e4a",
        "active_border_color": "#134e4a",
        "focus_ring_color": "#f59e0b",
        "dark_foreground_color": "#f8fafc",
        "dark_background_color": "#0f766e",
        "dark_border_color": "#99f6e4",
        "dark_hover_foreground_color": "#ffffff",
        "dark_hover_background_color": "#115e59",
        "dark_hover_border_color": "#99f6e4",
        "dark_active_foreground_color": "#ffffff",
        "dark_active_background_color": "#134e4a",
        "dark_active_border_color": "#99f6e4",
        "dark_focus_ring_color": "#fde68a",
        "allow_user_dismissal": False,
        "shadow_preset": "large",
        "opacity": 1.0,
        "border_width": 2,
        "focus_ring_width": 3,
        "focus_ring_offset": 3,
        "gradient_start_color": "#0f766e",
        "gradient_end_color": "#115e59",
        "gradient_angle": 135,
        "backdrop_blur": 8,
    }


@receiver(post_save, sender=ScrollTopRevision)
def _sync_admin_revision_to_site(
    sender,
    instance: ScrollTopRevision,
    created: bool,
    **kwargs,
) -> None:
    profile = instance.profile
    if profile is None or profile.scope != "admin":
        return
    if instance.status != "published":
        return

    site_profile, _ = ScrollTopProfile.objects.get_or_create(
        scope="site",
        site_id=None,
        defaults={
            "name": "Public default",
            "is_enabled": True,
        },
    )
    # The live revision is derived from status now, not a stored pointer.
    site_revision = site_profile.revisions.filter(status="published").first()
    if site_revision is None:
        site_revision = ScrollTopRevision.objects.create(
            profile=site_profile,
            status="published",
            published_at=instance.published_at or timezone.now(),
            created_by=instance.created_by,
        )

    synced_fields = [
        field.name
        for field in ScrollTopRevision._meta.concrete_fields
        if field.editable
        and field.name
        not in {
            "id",
            "name",
            "profile",
            "status",
            "created_by",
            "published_at",
            "created_at",
            "updated_at",
        }
    ]
    updates: list[str] = []
    for field_name in synced_fields:
        value = getattr(instance, field_name)
        if getattr(site_revision, field_name) != value:
            setattr(site_revision, field_name, value)
            updates.append(field_name)
    if site_revision.status != "published":
        site_revision.status = "published"
        updates.append("status")
    if site_revision.published_at is None:
        site_revision.published_at = instance.published_at or timezone.now()
        updates.append("published_at")
    if updates:
        site_revision.save(update_fields=updates)
        invalidate_site_config_cache(scope="site")


@receiver(post_migrate)
def _seed_library(sender, **kwargs) -> None:
    existing_tables = set(connection.introspection.table_names())
    required_tables = {
        ReadingCollection._meta.db_table,
        ReadingEntry._meta.db_table,
        ScrollTopProfile._meta.db_table,
        ScrollTopRevision._meta.db_table,
    }
    if not required_tables.issubset(existing_tables):
        return
    seed_demo_content()
