from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "src" / "django_scroll_to_top" / "static" / "django_scroll_to_top"


def _minify_css(value: str) -> str:
    lines = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lines.append(line)
    return "".join(lines) + "\n"


def _minify_js(value: str) -> str:
    lines = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        lines.append(line)
    return "".join(lines) + "\n"


def build() -> None:
    css_source = (STATIC_DIR / "scroll-to-top.css").read_text(encoding="utf-8")
    (STATIC_DIR / "scroll-to-top.min.css").write_text(
        _minify_css(css_source),
        encoding="utf-8",
    )
    for stem in ("scroll-to-top", "obstacle-adapter"):
        js_source = (STATIC_DIR / f"{stem}.js").read_text(encoding="utf-8")
        (STATIC_DIR / f"{stem}.min.js").write_text(
            _minify_js(js_source),
            encoding="utf-8",
        )


if __name__ == "__main__":
    build()
