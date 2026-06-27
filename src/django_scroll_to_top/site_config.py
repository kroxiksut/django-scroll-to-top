from __future__ import annotations

import logging
from dataclasses import dataclass

from django.apps import apps
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpRequest

from django_scroll_to_top.presentation import VisualConfig, default_visual_config
from django_scroll_to_top.settings import get_scroll_to_top_settings
from django_scroll_to_top.styles import build_style_token

_REQUEST_CACHE_ATTR = "_django_scroll_to_top_site_config_cache"
_SHARED_CACHE_KEY = "django_scroll_to_top:site:visual-config"
_LOGGED_CONFIG_ERRORS: set[str] = set()
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResolvedSiteConfig:
    scope: str
    site_id: int | None
    version: str
    visual_config: VisualConfig


def resolve_site_config(
    *,
    request: HttpRequest | None = None,
    scope: str = "site",
) -> ResolvedSiteConfig | None:
    if scope not in {"site", "admin"}:
        raise ValueError("Only scope='site' or scope='admin' is supported.")
    if not _scope_integration_enabled(scope=scope):
        return None
    if scope == "admin" and not _admin_page_is_enabled(request):
        return None

    site_id = _resolve_site_id(request) if scope == "site" else None
    request_cache = _request_cache(request)
    cache_key = (scope, site_id)
    cached = request_cache.get(cache_key)
    if cached is not None:
        return cached

    shared_key = _shared_cache_key(scope=scope, site_id=site_id)
    shared = cache.get(shared_key)
    if isinstance(shared, VisualConfig):
        resolved = ResolvedSiteConfig(
            scope=scope,
            site_id=site_id,
            version=build_style_token(shared),
            visual_config=shared,
        )
        request_cache[cache_key] = resolved
        return resolved

    try:
        # Imported lazily so the service layer can depend on this module's
        # cache-invalidation helper without an import cycle.
        from django_scroll_to_top.services import resolve_published_revision

        revision = resolve_published_revision(scope=scope, site_id=site_id)
        visual_config = (
            default_visual_config()
            if revision is None
            else revision.to_visual_config()
        )
    except (OperationalError, ProgrammingError, ValidationError) as exc:
        _log_config_error_once(exc)
        visual_config = default_visual_config()
    cache.set(shared_key, visual_config, timeout=None)
    resolved = ResolvedSiteConfig(
        scope=scope,
        site_id=site_id,
        version=build_style_token(visual_config),
        visual_config=visual_config,
    )
    request_cache[cache_key] = resolved
    return resolved


def invalidate_site_config_cache(*, scope: str = "site") -> None:
    # Bump a per-scope generation counter so every cached (scope, site)
    # combination is invalidated at once without enumerating sites.
    generation_key = _generation_cache_key(scope=scope)
    try:
        cache.incr(generation_key)
    except ValueError:
        cache.set(generation_key, 1, timeout=None)


def _request_cache(
    request: HttpRequest | None,
) -> dict[tuple[str, int | None], ResolvedSiteConfig]:
    if request is None:
        return {}
    cache_value = getattr(request, _REQUEST_CACHE_ATTR, None)
    if cache_value is None:
        cache_value = {}
        setattr(request, _REQUEST_CACHE_ATTR, cache_value)
    return cache_value


def _generation_cache_key(*, scope: str) -> str:
    return f"{_SHARED_CACHE_KEY}:generation:{scope}"


def _current_generation(*, scope: str) -> int:
    generation_key = _generation_cache_key(scope=scope)
    generation = cache.get(generation_key)
    if generation is None:
        cache.add(generation_key, 1, timeout=None)
        generation = cache.get(generation_key) or 1
    return int(generation)


def _shared_cache_key(*, scope: str, site_id: int | None) -> str:
    generation = _current_generation(scope=scope)
    site_token = "global" if site_id is None else str(site_id)
    return f"{_SHARED_CACHE_KEY}:{scope}:{site_token}:{generation}"


def _log_config_error_once(exc: Exception) -> None:
    key = exc.__class__.__name__
    if key in _LOGGED_CONFIG_ERRORS:
        return
    _LOGGED_CONFIG_ERRORS.add(key)
    logger.warning(
        "django-scroll-to-top fell back to the built-in default because site "
        "configuration could not be resolved: %s",
        exc,
    )


def _site_integration_enabled() -> bool:
    return get_scroll_to_top_settings().site_enabled


def _scope_integration_enabled(*, scope: str) -> bool:
    settings = get_scroll_to_top_settings()
    if scope == "site":
        return settings.site_enabled
    if scope == "admin":
        return settings.admin_enabled
    return False


def _admin_page_is_enabled(request: HttpRequest | None) -> bool:
    if request is None:
        return True

    settings = get_scroll_to_top_settings()
    if settings.admin_show_on_auth_pages:
        return True

    resolver_match = getattr(request, "resolver_match", None)
    url_name = getattr(resolver_match, "url_name", "")
    if not isinstance(url_name, str):
        return True
    if url_name not in {
        "login",
        "password_reset",
        "password_reset_done",
        "password_reset_confirm",
        "password_reset_complete",
    }:
        return True
    user = getattr(request, "user", None)
    return user is not None and bool(user.is_authenticated)


def _resolve_site_id(request: HttpRequest | None) -> int | None:
    # An explicit resolver hook takes precedence and works without the Sites
    # Framework installed (§34).
    from django_scroll_to_top.settings import get_site_id_resolver

    resolver = get_site_id_resolver()
    if resolver is not None:
        try:
            site_id = resolver(request)
        except Exception:  # noqa: BLE001 - a faulty hook must not break rendering
            return None
        return int(site_id) if site_id is not None else None

    if not get_scroll_to_top_settings().sites_framework_enabled:
        return None
    if not apps.is_installed("django.contrib.sites"):
        return None
    if request is None:
        return None

    from django.contrib.sites.shortcuts import get_current_site

    current_site = get_current_site(request)
    site_id = getattr(current_site, "pk", None)
    return int(site_id) if site_id is not None else None
