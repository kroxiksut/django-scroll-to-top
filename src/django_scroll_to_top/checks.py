from __future__ import annotations

from django.apps import apps
from django.conf import settings
from django.core.checks import Tags, Warning, register
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
