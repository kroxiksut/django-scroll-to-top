from tools.minify_assets import STATIC_DIR, _minify_css, _minify_js


def test_runtime_uses_vanilla_javascript_and_documented_global_api() -> None:
    source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "window.djstt" in source
    assert "function initAll" in source
    assert "const " not in source
    assert "eval(" not in source
    assert "new Function" not in source


def test_runtime_supports_idempotent_init_partial_navigation_and_cleanup() -> None:
    source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "instances.has(root)" in source
    assert '"htmx:afterSwap"' in source
    assert '"turbo:load"' in source
    assert "destroyRoot(root)" in source
    assert "removeEventListener" in source
    assert "MutationObserver" in source


def test_runtime_uses_raf_throttling_and_separate_state_buckets() -> None:
    source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "requestAnimationFrame" in source
    assert "setTimeout" in source
    assert "visibility:" in source
    assert "collision:" in source
    assert "dismissal:" in source
    assert "state.dismissal.dismissed" in source


def test_runtime_dispatches_documented_namespaced_events() -> None:
    source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")

    assert '"djstt:show"' in source
    assert '"djstt:hide"' in source
    assert '"djstt:scroll-start"' in source
    assert '"djstt:scroll-end"' in source
    assert '"djstt:dismiss"' in source


def test_runtime_uses_csp_friendly_external_script_patterns() -> None:
    source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")

    assert "onclick=" not in source
    assert "innerHTML" not in source
    assert "javascript:" not in source


def test_reproducible_minify_command_matches_committed_assets() -> None:
    css_source = (STATIC_DIR / "scroll-to-top.css").read_text(encoding="utf-8")
    js_source = (STATIC_DIR / "scroll-to-top.js").read_text(encoding="utf-8")
    css_min = (STATIC_DIR / "scroll-to-top.min.css").read_text(encoding="utf-8")
    js_min = (STATIC_DIR / "scroll-to-top.min.js").read_text(encoding="utf-8")

    assert css_min == _minify_css(css_source)
    assert js_min == _minify_js(js_source)
