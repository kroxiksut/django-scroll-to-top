from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.core.checks import Info, Tags, Warning, register
from django.core.exceptions import ImproperlyConfigured
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import OperationalError, ProgrammingError
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.settings import (
    ALLOWED_COLLISION_POLICIES,
    KNOWN_SETTING_KEYS,
    get_configured_csp_mode,
    get_configured_default_collision_policy,
    get_scroll_to_top_settings,
)


@register(Tags.models)
def django_scroll_to_top_checks(app_configs, **kwargs):
    messages = []
    database_alias = kwargs.get("database", DEFAULT_DB_ALIAS)
    try:
        executor = MigrationExecutor(connections[database_alias])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    except (OperationalError, ProgrammingError):
        messages.append(
            Warning(
                str(_("django-scroll-to-top migrations could not be inspected.")),
                hint=str(
                    _(
                    "Run migrations for django-scroll-to-top before relying on the "
                    "public template tag."
                    )
                ),
                id="dstt.W001",
            )
        )
        return messages

    if any(migration.app_label == "django_scroll_to_top" for migration, _ in plan):
        messages.append(
            Warning(
                str(_("django-scroll-to-top has unapplied migrations.")),
                hint=str(
                    _(
                    "Run `python manage.py migrate django_scroll_to_top` to make "
                    "renderer configuration checks reliable."
                    )
                ),
                id="dstt.W002",
            )
        )

    configured_mode = get_configured_csp_mode()
    if configured_mode not in {"external", "nonce"}:
        messages.append(
            Warning(
                str(_("django-scroll-to-top CSP mode is not supported.")),
                hint=str(
                    _(
                        "Set DJANGO_SCROLL_TO_TOP['CSP_MODE'] to 'external' or "
                        "'nonce'."
                    )
                ),
                id="dstt.W003",
            )
        )

    configured_collision_policy = get_configured_default_collision_policy()
    if configured_collision_policy not in ALLOWED_COLLISION_POLICIES:
        messages.append(
            Warning(
                str(
                    _(
                        "django-scroll-to-top default collision policy is not "
                        "supported."
                    )
                ),
                hint=str(
                    _(
                        "Set DJANGO_SCROLL_TO_TOP['DEFAULT_COLLISION_POLICY'] to one "
                        "of 'ignore', 'shift', 'fallback_corner', or 'hide'."
                    )
                ),
                id="dstt.W006",
            )
        )

    messages.extend(_check_settings_dict())

    normalized_settings = get_scroll_to_top_settings()

    if normalized_settings.admin_enabled and not apps.is_installed(
        "django.contrib.admin"
    ):
        messages.append(
            Warning(
                str(
                    _(
                        "django-scroll-to-top admin integration is enabled but "
                        "django.contrib.admin is not installed."
                    )
                ),
                hint=str(
                    _(
                        "Add 'django.contrib.admin' to INSTALLED_APPS or set "
                        "DJANGO_SCROLL_TO_TOP['ADMIN_ENABLED'] to False."
                    )
                ),
                id="dstt.W008",
            )
        )

    if normalized_settings.sites_framework_enabled and not apps.is_installed(
        "django.contrib.sites"
    ):
        messages.append(
            Warning(
                str(
                    _(
                        "django-scroll-to-top Sites Framework integration is "
                        "enabled but django.contrib.sites is not installed."
                    )
                ),
                hint=str(
                    _(
                        "Add 'django.contrib.sites' to INSTALLED_APPS or set "
                        "DJANGO_SCROLL_TO_TOP['SITES_FRAMEWORK_ENABLED'] to False."
                    )
                ),
                id="dstt.W009",
            )
        )

    messages.extend(_check_package_data())

    if normalized_settings.site_enabled:
        try:
            reverse(
                "django_scroll_to_top:site-stylesheet",
                kwargs={"version": "contract"},
            )
        except NoReverseMatch:
            messages.append(
                Warning(
                    str(
                        _(
                            "django-scroll-to-top stylesheet URLs are not included in "
                            "the project URLConf."
                        )
                    ),
                    hint=str(
                        _(
                            "Include `django_scroll_to_top.urls` with the "
                            "`django_scroll_to_top` namespace to support strict CSP "
                            "without `unsafe-inline`."
                        )
                    ),
                    id="dstt.W004",
                )
            )

    if normalized_settings.admin_enabled:
        installed_apps = list(getattr(settings, "INSTALLED_APPS", []))
        try:
            dstt_index = installed_apps.index("django_scroll_to_top")
            admin_index = installed_apps.index("django.contrib.admin")
        except ValueError:
            dstt_index = -1
            admin_index = -1
        if dstt_index > admin_index >= 0:
            messages.append(
                Warning(
                    str(
                        _(
                            "django-scroll-to-top admin template overrides may not "
                            "win because django.contrib.admin is installed earlier."
                        )
                    ),
                    hint=str(
                        _(
                            "Place 'django_scroll_to_top' before "
                            "'django.contrib.admin' in INSTALLED_APPS when "
                            "ADMIN_ENABLED is true."
                        )
                    ),
                    id="dstt.W005",
                )
            )

    return messages


@register(Tags.database)
def django_scroll_to_top_database_checks(app_configs, **kwargs):
    """Integrity checks that read profile/Site state from the database.

    Registered under ``Tags.database`` (not ``Tags.models``) so a plain
    ``manage.py check`` and most management commands do not query the database.
    These run with ``manage.py migrate`` and ``manage.py check --database``.
    """
    messages: list = []

    try:
        from django_scroll_to_top.models import ScrollTopProfile
    except (ModuleNotFoundError, ImproperlyConfigured):
        return messages

    try:
        profiles = list(
            ScrollTopProfile.objects.values(
                "scope",
                "site_id",
                "name",
                "is_enabled",
                "published_revision",
            )
        )
    except (OperationalError, ProgrammingError):
        # Tables are not migrated yet; dstt.W001/W002 already report that.
        return messages

    normalized_settings = get_scroll_to_top_settings()

    # dstt.W011: a profile points at a Sites Framework id that no longer exists.
    if normalized_settings.sites_framework_enabled and apps.is_installed(
        "django.contrib.sites"
    ):
        existing_site_ids: set[int] | None
        try:
            from django.contrib.sites.models import Site

            existing_site_ids = set(Site.objects.values_list("id", flat=True))
        except (OperationalError, ProgrammingError, ImproperlyConfigured):
            existing_site_ids = None
        if existing_site_ids is not None:
            dangling = sorted(
                str(profile["site_id"])
                for profile in profiles
                if profile["site_id"] is not None
                and profile["site_id"] not in existing_site_ids
            )
            if dangling:
                messages.append(
                    Warning(
                        str(
                            _(
                                "django-scroll-to-top profiles reference Site ids "
                                "that no longer exist: %(ids)s."
                            )
                            % {"ids": ", ".join(dangling)}
                        ),
                        hint=str(
                            _(
                                "Point each profile at an existing Site, clear its "
                                "Site id to make it the global profile, or delete it."
                            )
                        ),
                        id="dstt.W011",
                    )
                )

    # dstt.W012: a profile is enabled but has nothing published to render.
    unpublished = sorted(
        profile["name"]
        for profile in profiles
        if profile["is_enabled"] and profile["published_revision"] is None
    )
    if unpublished:
        messages.append(
            Info(
                str(
                    _(
                        "django-scroll-to-top has enabled profiles without a "
                        "published revision: %(names)s."
                    )
                    % {"names": ", ".join(unpublished)}
                ),
                hint=str(
                    _(
                        "Publish a revision for each profile or disable it. Until "
                        "then resolution falls back to the global profile or the "
                        "built-in defaults."
                    )
                ),
                id="dstt.W012",
            )
        )

    return messages


def _check_settings_dict() -> list[Warning]:
    raw = getattr(settings, "DJANGO_SCROLL_TO_TOP", {})
    if not isinstance(raw, dict):
        return [
            Warning(
                str(_("DJANGO_SCROLL_TO_TOP must be a dict.")),
                hint=str(
                    _(
                        "Define DJANGO_SCROLL_TO_TOP as a dictionary of installation "
                        "flags, for example {'SITE_ENABLED': True}."
                    )
                ),
                id="dstt.W007",
            )
        ]
    unknown = sorted(key for key in raw if key not in KNOWN_SETTING_KEYS)
    if unknown:
        return [
            Warning(
                str(
                    _("DJANGO_SCROLL_TO_TOP has unknown keys: %(keys)s.")
                    % {"keys": ", ".join(unknown)}
                ),
                hint=str(
                    _(
                        "Remove the unknown keys or check for typos. Known keys are: "
                        "%(known)s."
                    )
                    % {"known": ", ".join(sorted(KNOWN_SETTING_KEYS))}
                ),
                id="dstt.W007",
            )
        ]
    return []


def _check_package_data() -> list[Warning]:
    from importlib.resources import files

    required = (
        "templates/django_scroll_to_top/scroll_to_top.html",
        "static/django_scroll_to_top/scroll-to-top.min.js",
        "static/django_scroll_to_top/scroll-to-top.min.css",
    )
    try:
        root = files("django_scroll_to_top")
        missing = [name for name in required if not root.joinpath(name).is_file()]
    except (ModuleNotFoundError, FileNotFoundError, OSError):
        missing = list(required)
    if not missing:
        return []
    return [
        Warning(
            str(
                _("django-scroll-to-top packaged assets are missing: %(names)s.")
                % {"names": ", ".join(missing)}
            ),
            hint=str(
                _(
                    "Reinstall the package; the wheel must ship templates and "
                    "minified static assets."
                )
            ),
            id="dstt.W010",
        )
    ]
