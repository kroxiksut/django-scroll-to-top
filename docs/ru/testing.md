# Тестирование пакета

- [Назад к индексу документации](../README.ru.md)
- [Проверка типов (Pyright)](./type-checking.md)

Набор использует `pytest` с `pytest-django`. Тесты сами настраивают Django через
`tests/settings.py` (`DJANGO_SETTINGS_MODULE=tests.settings`, задано в
`pyproject.toml`); в репозитории пакета нет `manage.py`.

## Запуск тестов

```console
python -m pytest                                     # весь набор
python -m pytest tests/test_renderer.py              # один модуль
python -m pytest tests/test_renderer.py::test_name   # один тест
```

Линт и проверка типов рядом с тестами:

```console
python -m ruff check src tests
python -m pyright
```

## Что покрывает набор

Контракты, описанные в этой документации, проверяются модулями в `tests/`, среди
которых:

- `test_renderer`, `test_site_config`, `test_lifecycle` — разрешение,
  типизированный payload и переходы draft/publish/rollback;
- `test_admin_integration`, `test_admin_preview`, `test_uploaded_icon_admin` —
  UX админки, живой предпросмотр и атрибуция;
- `test_styling`, `test_css_contract`, `test_base_fields` — представление и
  контракт таблицы стилей;
- `test_visibility_scroll`, `test_collision_contract`, `test_dismissal`,
  `test_runtime_contract`, `test_obstacle_adapter` — машины состояний рантайма и
  контракт JS/DOM;
- `test_svg_sanitizer`, `test_security`, `test_registry` — безопасность SVG и
  каталог иконок;
- `test_accessibility`, `test_diagnostics`, `test_hooks`, `test_localization`,
  `test_app` — порог доступности, системные проверки, хуки расширения, i18n и
  подключение приложения.

Тестовые URLConf `tests/urls.py` и `tests/urls_without_dstt.py` дают
положительные и отрицательные фикстуры для системных проверок, связанных с
URLConf.

## Проверки ассетов и упаковки

Когда меняются шаблоны, статические ассеты, SVG, локаль, миграции, лицензии или
зависимости, пересоберите воспроизводимые минифицированные ассеты и дистрибутив:

```console
python tools/minify_assets.py        # пересборка *.min.css/js
python -m build                       # sdist + wheel
```

## Связанные разделы

- [Проверка типов (Pyright)](./type-checking.md)
- [Диагностика и management-команды](./diagnostics.md)
- [Заметки о миграции и обновлении](./migration.md)
