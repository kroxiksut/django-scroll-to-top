# Конфигурация (настройки и инфраструктура)

- [Назад к индексу документации](./README.md)
- [Быстрый старт](./quickstart.md)

Настройки Django отвечают только за **установку и инфраструктуру**. Обычный
внешний вид и поведение хранятся в конфигурации на основе базы данных и
редактируются через админку Django — см. [operations-admin.md](./operations-admin.md)
и [presentation.md](./presentation.md). Никогда не дублируйте внешний вид в
настройках.

Все настройки читаются из словаря `DJANGO_SCROLL_TO_TOP`. Все ключи
необязательны; неизвестные ключи помечаются системной проверкой `dstt.W007`, не
ломая совместимые с будущим дополнения.

## Справочник настроек

| Ключ | Тип | По умолчанию | Назначение |
| --- | --- | --- | --- |
| `SITE_ENABLED` | bool | `True` | Отрисовка элемента через `{% scroll_to_top %}` на сайте. |
| `ADMIN_ENABLED` | bool | `True` | Внедрение элемента в стандартную админку Django. |
| `SITES_FRAMEWORK_ENABLED` | bool | `False` | Включить профили по Site через `django.contrib.sites`. |
| `CSP_MODE` | `"external"` \| `"nonce"` | `"external"` | Как доставляется тег скрипта при CSP. |
| `ADMIN_SHOW_ON_AUTH_PAGES` | bool | `False` | Показывать элемент на страницах входа / сброса пароля админки. |
| `DEFAULT_COLLISION_POLICY` | `ignore` \| `shift` \| `fallback_corner` \| `hide` | `"ignore"` | Значение модуля по умолчанию для ревизий с политикой `inherit`. |
| `SITE_ID_RESOLVER` | dotted-path или callable | — | `(request) -> int \| None`: определить id текущего Site без Sites Framework. |
| `PROFILE_RESOLVER` | dotted-path или callable | — | `(scope, site_id) -> ScrollTopProfile \| None`: переопределить выбор профиля; `None` — откат к встроенному. |
| `OBSTACLE_SELECTORS` | dotted-path или callable | — | `() -> list[str]`: добавить общие селекторы препятствий к каждому элементу. |

Некорректные значения не вызывают исключение, а откатываются к значению по
умолчанию: неподдерживаемый `CSP_MODE` откатывается к `"external"` (и
сообщается `dstt.W003`); неподдерживаемый `DEFAULT_COLLISION_POLICY` — к
`"ignore"` (сообщается `dstt.W006`).

## Порядок в INSTALLED_APPS

Когда `ADMIN_ENABLED` истинно, поместите `django_scroll_to_top` **перед**
`django.contrib.admin`, чтобы переопределение подвала `admin/base_site.html`
выбиралось обычным разрешением шаблонов. Системная проверка `dstt.W005`
помечает неправильный порядок.

## URLConf и эндпоинт таблицы стилей

Проверенные значения цвета и размеров доставляются через версионированную
таблицу стилей того же источника, а не через атрибут `style`, поэтому строгий
CSP никогда молча не требует `unsafe-inline`. Подключите URLConf пакета:

```python
path(
    "scroll-to-top/",
    include(
        ("django_scroll_to_top.urls", "django_scroll_to_top"),
        namespace="django_scroll_to_top",
    ),
)
```

Это регистрирует маршрут `django_scroll_to_top:site-stylesheet`
(`styles/<version>.css`). Системная проверка `dstt.W004` предупреждает, если
URLConf отсутствует, а отрисовка на сайте включена.

## Content Security Policy

- **`external`** (по умолчанию) — рантайм доставляется тегами `<link>` и
  `<script>` того же источника. Работает со строгой политикой вида
  `default-src 'self'; style-src 'self'; script-src 'self';`.
- **`nonce`** — задайте `CSP_MODE = "nonce"` и передайте nonce через контекст
  шаблона (`csp_nonce`) или `request.csp_nonce`. Пакет добавит этот nonce к
  своему внешнему тегу скрипта, оставив стили на эндпоинте таблицы стилей.

## Sites Framework

При `SITES_FRAMEWORK_ENABLED = True` (и установленном `django.contrib.sites`)
у области может быть профиль конкретного Site, который разрешается раньше
глобального. Пакет работает и без Sites Framework: профили хранят `site_id` как
обычное целое, а `SITE_ID_RESOLVER` может предоставить id текущего Site.
Системная проверка `dstt.W009` предупреждает, если флаг задан без установленного
фреймворка.

## Хуки расширения

Хуки принимают dotted-path или callable. Сбойный хук никогда не ломает
отрисовку — исключения и ошибки импорта откатываются к встроенному поведению:

- `SITE_ID_RESOLVER(request) -> int | None`
- `PROFILE_RESOLVER(scope, site_id) -> ScrollTopProfile | None`
- `OBSTACLE_SELECTORS() -> list[str]`

Иконки разработчика регистрируются отдельно от настроек через реестр иконок
(`register_developer_icon(...)`); см. [presentation.md](./presentation.md).

## Связанные разделы

- [Админка: профили, ревизии, публикация и откат](./operations-admin.md)
- [Представление: шаблоны, цвета, размеры и иконки](./presentation.md)
- [Безопасность, санитизация SVG и CSP](./security-csp.md)
- [Диагностика и management-команды](./diagnostics.md)
