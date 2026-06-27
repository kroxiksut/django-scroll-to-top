from pathlib import Path


def _css() -> str:
    return Path(
        "src/django_scroll_to_top/static/django_scroll_to_top/scroll-to-top.css"
    ).read_text(encoding="utf-8")


def test_css_uses_namespaced_selectors_and_no_global_element_rules() -> None:
    css = _css()

    assert ".dstt-control" in css
    assert "\nbutton {" not in css
    assert "\na {" not in css
    assert "\nsvg {" not in css
    assert "\nbody {" not in css


def test_css_uses_layer_and_namespaced_custom_properties() -> None:
    css = _css()

    assert "@layer dstt-base" in css
    assert "--dstt-theme-fg:" in css
    assert "var(--dstt-color-fg" in css


def test_css_provides_conservative_fallbacks_and_theme_inherit() -> None:
    css = _css()

    assert "var(--button-bg, #0f172a)" in css
    assert "var(--body-fg, #ffffff)" in css
    assert "var(--border-color, #cbd5e1)" in css
    assert "--dstt-admin-button-bg" in css
    assert "--dstt-admin-focus-ring" in css


def test_css_supports_django_admin_variable_families_and_custom_adapter_hooks() -> None:
    css = _css()

    assert "var(--primary, #0f172a)" in css
    assert "var(--secondary, #1e293b)" in css
    assert "var(--accent, #38bdf8)" in css
    assert "var(--dstt-admin-button-bg-dark" in css
    assert "var(--dstt-admin-border-color-dark" in css


def test_css_supports_color_scheme_forced_colors_reduced_motion_and_print() -> None:
    css = _css()

    assert "@media (prefers-color-scheme: dark)" in css
    assert "@media (forced-colors: active)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "@media print" in css


def test_css_avoids_framework_dependencies_and_important_flags() -> None:
    css = _css()

    assert "!important" not in css
    assert ".btn" not in css
    assert ".container" not in css
    assert ".tw-" not in css


def test_css_uses_fixed_overlay_contract_without_layout_shift() -> None:
    css = _css()

    assert "position: fixed;" in css
    assert "vertical-align: top;" in css
    assert "inline-size: auto;" in css
