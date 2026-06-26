# Collision integration with django-cookies-152fz

This note records how the scroll-to-top control coexists with the
`django-cookies-152fz` cookie banner/launcher, the current state in the demo, and
the follow-ups that came out of investigating an overlap between the two floating
controls.

## The finding (is it a bug?)

**It is not a rendering/collision bug in `django-scroll-to-top`.** Collision
avoidance is opt-in: the runtime shifts the control only around obstacles it is
told about — elements marked `data-scroll-top-obstacle`, the revision's
`obstacle_selectors`, the `OBSTACLE_SELECTORS` settings hook, or the optional
`obstacle-adapter.js`.

In the demo the two controls overlap because:

1. The seeded scroll-to-top revision uses `corner = "bottom-right"`, and the
   cookie banner's default `desktop_position` is `bottom_right` — the **same
   corner**.
2. The demo `base.html` renders the real banner (`{% render_cookie_banner %}`)
   but does **not** load the obstacle adapter; only `/obstacles/` does, and that
   page registers against hand-faked markup.
3. Nothing registers the real cookie launcher as an obstacle on ordinary pages,
   so the `shift` policy has no obstacle to act on → no movement → overlap.

So the overlap is a configuration/wiring gap, plus a stale convenience preset
(below) — not a defect in how the control renders or avoids collisions.

## The real django-cookies-152fz markup contract (verified)

From `django-cookies-152fz` `includes/cookie_banner.html` and `cookie_banner.js`:

- Banner root: `.dz152fz-cookie-banner` / `[data-cookie-banner-root]`
- Launcher pill: `.dz152fz-cookie-banner__launcher` / `[data-cookie-banner-launcher]`
- Open panel: `[data-cookie-banner-panel]`
- Position: `data-cookie-banner-desktop-position` / `-mobile-position`
  (default `bottom_right`; configurable per banner revision)
- Lifecycle events: the banner JS dispatches bubbling, namespaced `CustomEvent`s
  — `dz152fz:cookie-banner:opened` / `:closed` / `:custom-opened` /
  `:action-submitted` (and `dz152fz:cookie-runtime:applied` / `:cleanup-applied`).
  These can be bridged to a placement recalc.

## How to wire it today (no module changes required)

- **Banner side** — set the banner revision's desktop/mobile position to a
  non-conflicting corner (for example `bottom_left`) in the cookie admin. Zero
  effort; simply separates the two controls.
- **scroll-to-top admin (recommended for a real integration)** — set the
  revision's `obstacle_selectors` to the real launcher/panel and keep a moving
  collision policy (`shift` / `fallback_corner` / `hide`):

  ```text
  [data-cookie-banner-launcher]
  [data-cookie-banner-panel]
  ```

  Pure configuration, works on every page, no JavaScript.
- **Demo template** — load `obstacle-adapter.js` in `base.html` and register the
  real selectors (see follow-up below).

### Worked example: the demo site (admin GUI, no code)

What was changed for the demo, and where:

1. Django admin → **Scroll-to-top revisions** → open the published revision.
2. **Collision avoidance** section → **Obstacle selectors** (one per line):

   ```text
   [data-cookie-banner-launcher]
   [data-cookie-banner-panel]
   ```

   Leave **Collision policy** as *Inherit module default* (the demo default is
   `shift`) or pick *Shift along edge*; optionally set **Obstacle gap** to `16`.
3. Save. Editing a published revision updates the live site and clears the cache.

Before — the cookie banner overlaps the control:

![Cookie banner overlapping the scroll-to-top control](../assets/shared/19.1-cookie-overlap-before.png)

After — the control rides up above the cookie launcher:

![Control lifted above the cookie launcher](../assets/shared/19.2-obstacle-selectors-after.png)

## Follow-ups — django-scroll-to-top (this package)

1. **Fix the bundled `djangoCookies152fz` obstacle-adapter preset.** *(Done.)* The
   preset previously targeted `[data-django-cookies-banner]` /
   `[data-django-cookies-launcher]` and events `django-cookies:open|close|collapse`,
   none of which the real module emits. It now targets the real markup
   (`[data-cookie-banner-launcher]`, `[data-cookie-banner-panel]`) and bridges the
   real events
   (`dz152fz:cookie-banner:opened|closed|custom-opened|action-submitted`), so
   loading `obstacle-adapter.js` and registering the preset avoids the real banner
   with no per-project selectors. The demo `/obstacles/` page and
   `tests/test_obstacle_adapter.py` were updated to match.
2. **Make the demo show real collision avoidance.** The intended path is the
   admin GUI, not code: the revision's **Collision avoidance** section already
   exposes *Collision policy*, *Obstacle selectors*, *Obstacle gap*, *Maximum
   collision shift*, and *Fallback corner order*. Set *Obstacle selectors* to
   `[data-cookie-banner-launcher]` / `[data-cookie-banner-panel]` and save — the
   `shift` policy then lifts the control above the cookie launcher. No code or
   module change is required (the GUI is complete). The adapter-in-`base.html`
   route remains a valid alternative once the bundled preset (follow-up 1) is
   corrected.
3. **Document the supported selectors** as the integration contract once the
   preset is corrected (presentation/runtime docs + AI guide `runtime.md`).

## Follow-ups — django-cookies-152fz (cookie module)

**None of these are required.** The integration already works end to end from the
scroll-to-top admin (the obstacle-selectors example above), with no change to
`django-cookies-152fz`. The items below are *optional* convenience enhancements
that would make third-party floating-widget collision integration more turn-key:

1. **Publish a stable obstacle/integration contract** — document the markup hooks
   (`[data-cookie-banner-root|launcher|panel]`), the position attributes, and the
   already-emitted lifecycle events (`dz152fz:cookie-banner:*`) as a supported
   public surface, so integrators target them without reading the source. (The
   events already exist and are now bridged by the preset — this is about
   *documenting* them as stable.)
2. **(Optional) Verify the banner root's measured rectangle** is meaningful for
   rect-based collision (the visible launcher/panel should be the measured
   boxes; a full-viewport invisible wrapper would mislead measurement).

## Status

Two shipping ways to avoid the cookie launcher: (1) configure *Obstacle selectors*
in the admin GUI (no code), or (2) load the optional `obstacle-adapter.js` and
register the now-corrected `djangoCookies152fz` preset (real selectors + real
events). The only open item is the optional cookie-module documentation
enhancement above; no cookie-module code change is needed.
