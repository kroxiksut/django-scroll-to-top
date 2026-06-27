"""Clean-install smoke test for the built ``django-scroll-to-top`` wheel.

Unlike the pytest suite (which runs against ``src/`` via ``pythonpath``), this
script exercises the *installed* package, so it catches packaging gaps the suite
cannot — missing templates, static assets, locale, or SVG package-data. It must
therefore run in an environment where the wheel is installed, NOT in the dev tree.

Typical use (also suitable for CI after ``python -m build``):

    python -m venv /tmp/smoke
    /tmp/smoke/bin/python -m pip install dist/django_scroll_to_top-*.whl
    /tmp/smoke/bin/python tools/smoke_install.py

It configures a minimal Django project entirely in-memory, then checks that:
  1) the package imports from site-packages (not from a ``src`` tree);
  2) the migrations apply on a fresh database;
  3) the public ``{% scroll_to_top %}`` tag renders for the ``site`` and
     ``admin`` scopes (packaged SVG icon present, ``*.min.css/js`` wired, the
     versioned stylesheet endpoint reverses);
  4) the packaged ``admin/base_site.html`` override wins template resolution;
  5) the minified static assets ship inside the installed package.

Exit code is 0 on success (prints ``SMOKE OK``) and 1 on the first failed check.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import django
from django.conf import settings

FAILS: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))
    if not condition:
        FAILS.append(label)


def main() -> int:
    settings.configure(
        DEBUG=False,
        SECRET_KEY="smoke-test-only",
        ALLOWED_HOSTS=["testserver", "localhost"],
        ROOT_URLCONF="djstt_smoke_urls",
        INSTALLED_APPS=[
            # MUST precede django.contrib.admin so base_site.html wins resolution.
            "django_scroll_to_top",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        STATIC_URL="/static/",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "DIRS": [],
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.request",
                        "django.contrib.auth.context_processors.auth",
                        "django.contrib.messages.context_processors.messages",
                    ]
                },
            }
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()

    # Register the URLConf as an in-memory module so this stays a single file.
    from django.contrib import admin
    from django.urls import include, path

    urlconf = types.ModuleType("djstt_smoke_urls")
    urlconf.urlpatterns = [  # type: ignore[attr-defined]
        path("admin/", admin.site.urls),
        path("djstt/", include("django_scroll_to_top.urls")),
    ]
    sys.modules["djstt_smoke_urls"] = urlconf

    print("django-scroll-to-top wheel smoke test")

    # 1) Imported from the installed wheel, not from the src tree.
    import django_scroll_to_top as pkg

    pkg_path = Path(pkg.__file__).resolve()
    check(
        "package imported from the installed wheel (site-packages, not src)",
        "site-packages" in pkg_path.parts and "src" not in pkg_path.parts,
        str(pkg_path),
    )

    # 2) Migrations apply cleanly on a fresh database.
    from django.core.management import call_command
    from django.db import connection

    call_command("migrate", run_syncdb=True, verbosity=0)
    tables = connection.introspection.table_names()
    check(
        "package migrations created their tables",
        any(t.startswith("django_scroll_to_top_") for t in tables),
        ", ".join(t for t in tables if t.startswith("django_scroll_to_top_")),
    )

    # 3) Render the public template tag against built-in defaults.
    from django.template import Context, Template
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    tag_out = Template("{% load scroll_to_top %}{% scroll_to_top %}").render(
        Context({"request": request})
    )
    check("site tag renders non-empty output", len(tag_out.strip()) > 0, f"{len(tag_out)} chars")
    check("rendered control contains a packaged SVG icon", "<svg" in tag_out)
    check(
        "rendered control wires the minified static assets",
        "scroll-to-top.min.css" in tag_out and "scroll-to-top.min.js" in tag_out,
    )
    check(
        "rendered control reverses the versioned stylesheet endpoint",
        "/djstt/" in tag_out,
    )
    admin_out = Template(
        '{% load scroll_to_top %}{% scroll_to_top scope="admin" %}'
    ).render(Context({"request": request}))
    check("admin-scope tag renders non-empty output", len(admin_out.strip()) > 0)

    # 4) Admin footer-injection template ships and wins over admin's own.
    from django.template.loader import get_template

    base_site = get_template("admin/base_site.html")
    origin = Path(base_site.origin.name).resolve()
    check(
        "admin/base_site.html resolves to OUR packaged template",
        "django_scroll_to_top" in origin.parts and "site-packages" in origin.parts,
        str(origin),
    )
    base_site_src = origin.read_text(encoding="utf-8")
    check(
        "packaged base_site.html injects the scroll_to_top tag (admin scope)",
        "scroll_to_top" in base_site_src and "admin" in base_site_src,
    )

    # 5) Minified static assets are present inside the installed package.
    static_dir = pkg_path.parent / "static" / "django_scroll_to_top"
    for asset in ("scroll-to-top.min.css", "scroll-to-top.min.js", "obstacle-adapter.min.js"):
        check(f"packaged static asset present: {asset}", (static_dir / asset).is_file())

    print()
    if FAILS:
        print(f"SMOKE FAILED -- {len(FAILS)} check(s) failed: {FAILS}")
        return 1
    print("SMOKE OK -- wheel installs clean and renders the tag + admin integration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
