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

### `tools/minify_assets.py`

Это воспроизводимый минификатор ассетов проекта — небольшой скрипт на стандартной
библиотеке (без внешнего минификатора, без Node, без шага сборки в рантайме),
намеренно простой, чтобы его вывод был побайтово стабильным и читаемым в diff. Он
читает исходные ассеты в `src/django_scroll_to_top/static/django_scroll_to_top/`
и перезаписывает их минифицированные пары:

| Источник | Минифицированный вывод |
| --- | --- |
| `scroll-to-top.css` | `scroll-to-top.min.css` |
| `scroll-to-top.js` | `scroll-to-top.min.js` |
| `obstacle-adapter.js` | `obstacle-adapter.min.js` |

Минификация намеренно консервативна и детерминирована: обрезает каждую строку,
убирает пустые строки (CSS и JS) и строки-комментарии `//` целиком (JS), а
остальное склеивает. Семантических преобразований нет — одинаковый вход всегда
даёт одинаковый выход, поэтому пересобранный файл меняется, только если изменился
его источник.

Запускайте его при каждом изменении исходника `.css` или `.js` и коммитьте
пересобранные `*.min.*` в **том же** change set: именно минифицированные файлы
попадают в колесо и отдаются браузерам.

Скрипт также является зависимостью тестов, поэтому его нельзя удалять или
перемещать: `tests/test_runtime_contract.py` и `tests/test_obstacle_adapter.py`
импортируют из него `STATIC_DIR`, `_minify_css` и `_minify_js` и проверяют, что
закоммиченные `*.min.*` точно совпадают со свежей минификацией исходников.
Поэтому устаревший минифицированный ассет роняет набор тестов.

### `tools/smoke_install.py`

Набор pytest гоняется по `src/` (через `pythonpath`), поэтому пропуски в упаковке
он поймать не может — отсутствующие в `package-data` шаблон, статика, каталог
локали или SVG всё равно пройдут все тесты. `tools/smoke_install.py` закрывает
этот разрыв, проверяя **установленное** колесо: поднимает минимальный
in-memory-проект Django и убеждается, что пакет импортируется из site-packages (а
не из `src/`), его миграции применяются, тег `{% scroll_to_top %}` рендерится в
областях `site` и `admin` (упакованная SVG-иконка на месте, `*.min.*` подключены,
версионный endpoint стилей реверсится), переопределение `admin/base_site.html` из
пакета выигрывает резолвинг шаблонов, а минифицированная статика поставляется.

Запускайте его в окружении с установленным колесом — не в dev-дереве:

```console
python -m build
python -m venv /tmp/smoke
/tmp/smoke/bin/python -m pip install dist/django_scroll_to_top-*.whl
/tmp/smoke/bin/python tools/smoke_install.py
```

Скрипт завершается ненулевым кодом на первой непройденной проверке. CI запускает
его автоматически в job `build`, поэтому регрессия `package-data` роняет пайплайн
на каждом push.

## Связанные разделы

- [Проверка типов (Pyright)](./type-checking.md)
- [Диагностика и management-команды](./diagnostics.md)
- [Заметки о миграции и обновлении](./migration.md)
