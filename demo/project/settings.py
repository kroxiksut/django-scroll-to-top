from __future__ import annotations

import importlib.util
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "demo-scroll-to-top-secret-key"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

# django-cookies-152fz is an OPTIONAL demo dependency: the demo runs without it.
# Install `django-cookies-152fz` to also see the cookie banner and the
# cookie-preferences page wired into the demo shell.
_HAS_COOKIES = importlib.util.find_spec("django_cookies_152fz") is not None

INSTALLED_APPS = [
    # Optional — only registered when django-cookies-152fz is installed.
    *(["django_cookies_152fz"] if _HAS_COOKIES else []),
    # Placed before django.contrib.admin so the admin base_site.html override
    # that injects the scroll-to-top control wins template resolution.
    "django_scroll_to_top",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "demo.library",
]

# Installation/infrastructure contract only. Visual configuration lives in the
# admin models. A non-ignore default makes the obstacle demo page visibly
# shift the control around cookie banners and other floating widgets.
DJANGO_SCROLL_TO_TOP = {
    "SITE_ENABLED": True,
    "ADMIN_ENABLED": True,
    "DEFAULT_COLLISION_POLICY": "shift",
}

# Only consumed when django-cookies-152fz is installed (see _HAS_COOKIES above).
DJANGO_COOKIES_152FZ = {
    "enable_cookies": True,
    "cookie_banner": {
        "bootstrap_initial_revision": True,
        "preferences_page_template": "demo/cookie_preferences.html",
        "text_preset": "en_balanced",
        "show_launcher": True,
        "show_preferences_link": True,
    },
    "cookie_runtime": {
        "custom_css_url": "/static/demo/cookie-module.css",
    },
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "demo.project.urls"
WSGI_APPLICATION = "demo.project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "demo.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("ru", "Russian"),
]

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "demo" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "demo.project.context_processors.cookies",
            ],
        },
    }
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
