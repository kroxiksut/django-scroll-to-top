# Demo Site

This directory contains a standalone Django project for local demo work.

## Run

```console
python demo/manage.py migrate
python demo/manage.py runserver
```

The first migrate seeds:

- a working `admin` / `admin` superuser;
- a published default scroll-to-top configuration for the public site;
- a published default scroll-to-top configuration for the Django admin.

## Demo Content

- Public pages are English-only.
- The Django admin uses Django's built-in English and Russian localization.
- The demo database creates a superuser with `admin` / `admin` credentials on
  first migrate.
- The demo content is original and intended for local scroll and layout
  testing.
- The cookie module is installed from `pip` as `django-cookies-152fz` and is
  wired into the demo with an English default preset, a themed preferences
  page, and a site-matched visual palette.
- The `Obstacles` page (`/obstacles/`) demonstrates the collision engine and the
  optional obstacle adapter: a bottom-right cookie banner with open/collapse/
  close controls, a chat widget, a toast, and a sticky mobile navigation bar as
  simultaneous obstacles. Use the "Toggle collision debug" button to visualize
  obstacle rectangles.

## Admin Language Switcher

The demo admin includes a compact English/Russian switcher in the branding
area.

- It uses Django's standard `set_language` endpoint, so no custom auth or URL
  logic is required.
- The control is styled with a dedicated demo stylesheet instead of raw default
  admin buttons.
- The active language is highlighted and a short locale hint is shown so the
  current state is easy to read.
- This is only for the demo project; the package itself still relies on
  Django's normal localization behavior.

## Scroll-To-Top Defaults

The demo seeds two published configuration profiles for the package:

- both the public `site` profile and the `admin` profile start with the same
  teal button, filled arrow, and contrast settings so the admin button matches
  what the public site shows by default;
- saving a published `admin` revision immediately copies the visual fields to
  the public `site` profile, so the backend becomes a live preview of the same
  control;
- the demo keeps the two profiles as separate records so the package contract
  remains intact, but the demo wiring makes them behave like one synchronized
  configuration.

This keeps the demo realistic without making the public site and admin drift
apart during the walkthrough.

## Cookie Module Defaults

The cookie module is configured to behave like a first-class part of the demo
site:

- `django_cookies_152fz` is installed as a normal app dependency and bootstraps
  its default data on `migrate`;
- the banner starts with the English-balanced preset so the public site stays
  English by default;
- the preferences page uses the demo shell and the same green/cream palette as
  the rest of the site;
- the cookie launcher and preferences link are enabled so the module is easy to
  discover during the walkthrough.
