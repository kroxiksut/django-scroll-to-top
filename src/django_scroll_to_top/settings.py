from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast

from django.conf import settings
from django.template import Context
from django.utils.module_loading import import_string

CspMode = Literal["external", "nonce"]
_ALLOWED_CSP_MODES = {"external", "nonce"}

CollisionPolicy = Literal["ignore", "shift", "fallback_corner", "hide"]
ALLOWED_COLLISION_POLICIES = ("ignore", "shift", "fallback_corner", "hide")
_DEFAULT_COLLISION_POLICY = "ignore"

# Recognized keys of the DJANGO_SCROLL_TO_TOP settings dict, used by system
# checks to flag typos without rejecting forward-compatible additions silently.
KNOWN_SETTING_KEYS = frozenset(
    {
        "SITE_ENABLED",
        "ADMIN_ENABLED",
        "SITES_FRAMEWORK_ENABLED",
        "CSP_MODE",
        "ADMIN_SHOW_ON_AUTH_PAGES",
        "DEFAULT_COLLISION_POLICY",
        # Extension-point hooks (§34): dotted path or callable.
        "SITE_ID_RESOLVER",
        "PROFILE_RESOLVER",
        "OBSTACLE_SELECTORS",
    }
)


@dataclass(frozen=True, slots=True)
class ScrollToTopSettings:
    site_enabled: bool
    admin_enabled: bool
    sites_framework_enabled: bool
    csp_mode: CspMode
    admin_show_on_auth_pages: bool
    default_collision_policy: CollisionPolicy


def _options() -> dict:
    raw = getattr(settings, "DJANGO_SCROLL_TO_TOP", {})
    return raw if isinstance(raw, dict) else {}


def get_scroll_to_top_settings() -> ScrollToTopSettings:
    options = _options()
    raw_csp_mode = options.get("CSP_MODE", "external")
    csp_mode = raw_csp_mode if raw_csp_mode in _ALLOWED_CSP_MODES else "external"
    raw_collision_policy = options.get(
        "DEFAULT_COLLISION_POLICY", _DEFAULT_COLLISION_POLICY
    )
    default_collision_policy = (
        raw_collision_policy
        if raw_collision_policy in ALLOWED_COLLISION_POLICIES
        else _DEFAULT_COLLISION_POLICY
    )
    return ScrollToTopSettings(
        site_enabled=bool(options.get("SITE_ENABLED", True)),
        admin_enabled=bool(options.get("ADMIN_ENABLED", True)),
        sites_framework_enabled=bool(options.get("SITES_FRAMEWORK_ENABLED", False)),
        csp_mode=cast(CspMode, csp_mode),
        admin_show_on_auth_pages=bool(options.get("ADMIN_SHOW_ON_AUTH_PAGES", False)),
        default_collision_policy=cast(CollisionPolicy, default_collision_policy),
    )


def get_configured_csp_mode() -> str:
    return str(_options().get("CSP_MODE", "external"))


def get_configured_default_collision_policy() -> str:
    return str(_options().get("DEFAULT_COLLISION_POLICY", _DEFAULT_COLLISION_POLICY))


def _resolve_callable(value: object) -> Callable | None:
    if value is None:
        return None
    if callable(value):
        return value
    if isinstance(value, str):
        try:
            return import_string(value)
        except ImportError:
            return None
    return None


def get_site_id_resolver() -> Callable | None:
    """Optional hook resolving the current Site id without the Sites Framework."""
    return _resolve_callable(_options().get("SITE_ID_RESOLVER"))


def get_profile_resolver() -> Callable | None:
    """Optional hook overriding profile/revision selection."""
    return _resolve_callable(_options().get("PROFILE_RESOLVER"))


def get_obstacle_selectors_hook() -> Callable | None:
    """Optional hook returning extra obstacle CSS selectors to merge in."""
    return _resolve_callable(_options().get("OBSTACLE_SELECTORS"))


def resolve_csp_nonce(context: Context) -> str:
    request = context.get("request")
    explicit_nonce = context.get("csp_nonce")
    if isinstance(explicit_nonce, str) and explicit_nonce:
        return explicit_nonce
    request_nonce = getattr(request, "csp_nonce", "")
    return request_nonce if isinstance(request_nonce, str) else ""
