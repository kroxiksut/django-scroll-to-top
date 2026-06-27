from django.apps import apps


def test_app_config_is_registered() -> None:
    config = apps.get_app_config("django_scroll_to_top")

    assert config.name == "django_scroll_to_top"
