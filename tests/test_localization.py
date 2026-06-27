from __future__ import annotations

from importlib.resources import files

from django.utils import translation
from django.utils.translation import gettext


def test_russian_catalog_translates_core_strings() -> None:
    with translation.override("ru"):
        assert gettext("Back to top") == "Наверх"
        assert gettext("Scroll back to top") == "Прокрутить к началу"
        assert gettext("Published revision") == "Опубликованная ревизия"
        assert gettext("Hide the scroll-to-top button") == (
            "Скрыть кнопку прокрутки наверх"
        )


def test_russian_avoids_scroll_to_top_anglicism() -> None:
    with translation.override("ru"):
        assert gettext("Scroll-to-top revision") == "Ревизия кнопки прокрутки наверх"
        assert gettext("Scroll-to-top button") == "Кнопка прокрутки наверх"
        assert gettext("Local storage") == "Локальное хранилище"
        assert "scroll-to-top" not in gettext("Scroll-to-top profile").lower()


def test_english_is_unchanged_source() -> None:
    with translation.override("en"):
        assert gettext("Back to top") == "Back to top"


def test_russian_catalog_preserves_named_placeholders() -> None:
    with translation.override("ru"):
        template = gettext("Published %(count)d revision(s).")
        assert "%(count)d" in template
        assert (template % {"count": 3}) == "Опубликовано ревизий: 3."


def test_russian_mo_is_packaged() -> None:
    root = files("django_scroll_to_top")
    assert root.joinpath("locale/ru/LC_MESSAGES/django.mo").is_file()
