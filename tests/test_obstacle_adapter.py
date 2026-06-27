from tools.minify_assets import STATIC_DIR, _minify_js


def _source() -> str:
    return (STATIC_DIR / "obstacle-adapter.js").read_text(encoding="utf-8")


def test_adapter_exposes_optional_global_api() -> None:
    source = _source()

    assert "window.djsttObstacleAdapter" in source
    assert "register:" in source
    assert "refresh:" in source
    assert "presets:" in source


def test_adapter_uses_vanilla_javascript() -> None:
    source = _source()

    assert "const " not in source
    assert "let " not in source
    assert "eval(" not in source
    assert "new Function" not in source
    assert "onclick=" not in source
    assert "innerHTML" not in source


def test_adapter_tags_generic_marker_and_bridges_refresh() -> None:
    source = _source()

    assert "data-scroll-top-obstacle" in source
    assert "data-scroll-top-obstacle-gap" in source
    assert "data-scroll-top-obstacle-priority" in source
    assert "window.djstt.refresh" in source
    assert "MutationObserver" in source


def test_adapter_never_inspects_cross_origin_iframe_contents() -> None:
    source = _source()

    assert "contentWindow" not in source
    assert "contentDocument" not in source


def test_adapter_ships_cookie_banner_preset_with_panel_and_launcher() -> None:
    source = _source()

    assert "djangoCookies152fz" in source
    # Match the real django-cookies-152fz markup (launcher pill + consent panel).
    assert "[data-cookie-banner-launcher]" in source
    assert "[data-cookie-banner-panel]" in source
    # Bridge the banner's real namespaced lifecycle events.
    assert "dz152fz:cookie-banner:opened" in source
    assert "dz152fz:cookie-banner:closed" in source
    # The earlier guessed markup/events must not come back.
    assert "data-django-cookies" not in source
    assert "django-cookies:open" not in source


def test_reproducible_minify_matches_committed_adapter_asset() -> None:
    source = _source()
    minified = (STATIC_DIR / "obstacle-adapter.min.js").read_text(encoding="utf-8")

    assert minified == _minify_js(source)
