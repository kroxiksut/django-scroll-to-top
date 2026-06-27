# Avoiding third-party floating widgets (collision)

- [Back to documentation index](../README.md)
- [Behavior and runtime](../en/runtime.md)

The scroll-to-top control can move out of the way of other floating UI — cookie
banners, chat launchers, sticky bars, toast stacks — so they do not overlap. This
page is a worked example using [`django-cookies-152fz`][cookies] as a concrete
third-party widget, but **nothing here is a dependency**: the same approach works
for any floating element. The cookie module is simply what this collision
behavior was tested against.

[cookies]: https://pypi.org/project/django-cookies-152fz/

## How collision avoidance works

Collision avoidance is **opt-in**: the runtime only shifts the control around
obstacles it is told about, through any of:

- the `data-scroll-top-obstacle` marker on the widget's element;
- the revision's **Obstacle selectors** (admin) — validated CSS selectors;
- the `OBSTACLE_SELECTORS` settings hook;
- the optional `obstacle-adapter.js`, which tags markup by selector and bridges a
  widget's open/close/collapse events to `window.djstt.refresh()`.

The collision policy (`ignore` / `shift` / `fallback_corner` / `hide`) is set per
revision, with a module-wide default in
`DJANGO_SCROLL_TO_TOP["DEFAULT_COLLISION_POLICY"]`.

Two controls overlap by default only when they pin to the **same corner** (for
example both bottom-right) and nothing registers one as an obstacle for the other,
so the `shift` policy has nothing to act on. Telling the control about the widget
(any mechanism above) resolves it.

## Worked example: avoiding a cookie banner (admin GUI, no code)

`django-cookies-152fz` renders its banner and launcher in the bottom-right corner
by default — the same corner as a default control — so they overlap until the
control is told about the banner.

The markup it exposes (from its `cookie_banner.html` / `cookie_banner.js`):

- launcher pill: `[data-cookie-banner-launcher]`
- open panel: `[data-cookie-banner-panel]`
- banner root: `[data-cookie-banner-root]`
- lifecycle events (bubbling, namespaced): `dz152fz:cookie-banner:opened` /
  `:closed` / `:custom-opened` / `:action-submitted`.

Resolve the overlap entirely from the scroll-to-top admin — no code, works on
every page, no JavaScript:

1. Django admin → **Scroll-to-top revisions** → open the published revision.
2. In **Collision avoidance** → **Obstacle selectors**, add one per line:

   ```text
   [data-cookie-banner-launcher]
   [data-cookie-banner-panel]
   ```

3. Leave **Collision policy** as *Inherit module default* (or pick *Shift along
   edge*); optionally set **Obstacle gap** to `16`. Save — editing a published
   revision updates the live site and clears the cache.

Before — the cookie banner overlaps the control:

![Cookie banner overlapping the scroll-to-top control](../assets/shared/19.1-cookie-overlap-before.png)

After — the control rides up above the cookie launcher:

![Control lifted above the cookie launcher](../assets/shared/19.2-obstacle-selectors-after.png)

## Alternative: the obstacle adapter and the bundled preset

Instead of admin selectors you can load the optional adapter and register a
widget by selectors + events:

```html
<script src="{% static 'django_scroll_to_top/obstacle-adapter.min.js' %}" defer></script>
<script>
  window.djsttObstacleAdapter.register({
    selectors: [".my-widget", ".my-widget__launcher"],
    events: ["my-widget:open", "my-widget:close"],
    gap: 12,
  });
</script>
```

As a convenience, the adapter ships a ready-made `djangoCookies152fz` preset
(targeting the real selectors and events listed above), so you can register it
without writing per-project selectors:

```js
window.djsttObstacleAdapter.register(
  window.djsttObstacleAdapter.presets.djangoCookies152fz
);
```

The preset is just a shortcut for one specific widget; any other widget works the
same way through your own selectors and events.

## Using a different module

There is nothing cookie-specific in the engine. To avoid any other floating
widget, point one of the mechanisms above at its element(s): add
`data-scroll-top-obstacle` to its markup, list its selector in the revision's
**Obstacle selectors**, or register it through the adapter with its own
open/close events.
