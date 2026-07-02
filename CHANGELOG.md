# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
While the version stays in the `0.x` series, the public API may still change
between minor releases.

## [Unreleased]

## [0.3.0] - 2026-07-01

### Added

- Admin **Create starter configuration** button on the scroll-to-top profiles
  list: one click creates and publishes a default profile plus revision for the
  site and admin scopes, so a fresh install no longer shows three empty admin
  sections next to a button that is already visible on the page. The action is
  idempotent and only fills scopes that have nothing published yet.
- A **collapsible admin menu**: the scroll-to-top group in the admin's left
  navigation sidebar can be folded away with a small toggle (its three items
  only — other apps and the footer control are untouched), and the collapsed
  state is remembered in the browser. Progressive enhancement only — it reads
  the standard admin DOM and never restyles global admin elements.
- Human-readable messages when a uniqueness rule would be violated instead of a
  raw `Constraint "…" is violated` error: for duplicate profiles (one global
  profile per scope, one profile per scope and Site) and for a second published
  revision on the same profile.
- Supply-chain hardening for CI: a Dependabot config (pip, npm, and GitHub
  Actions, weekly) plus every GitHub Action pinned to a commit SHA with a
  version comment, so action updates are reviewed rather than floating on a
  mutable tag.

### Changed

- The live revision is now derived from revision **status** (a single source of
  truth) instead of a stored `ScrollTopProfile.published_revision` pointer,
  removing the mutual profile↔revision link. Publishing a revision with the
  **Publish selected revision** action is the only step needed to make it live;
  you no longer edit the profile to attach a revision by hand. A data migration
  preserves each existing installation's currently-live revision, and a partial
  unique constraint enforces at most one published revision per profile.
- The profile add form no longer shows an unusable, always-empty "Published
  revision" field; the live revision appears as a read-only link derived from
  status.

## [0.2.0] - 2026-06-28

### Added

- Documented limits for uploaded SVG icons: up to 100 KB per file, 128 elements,
  8 levels of nesting, and 20,000 characters of path data per shape. Bigger files
  are rejected instead of being trimmed.
- Extra configuration warnings: when a profile points at a site that no longer
  exists, or is turned on but has nothing published yet.
- Security scanning in CI (code analysis and pull-request dependency review).
- Minor PyPI page improvements (release-notes link, OS-independent marker).

### Changed

- Expanded the tested Django matrix to 4.2 LTS, 5.0, 5.1, 5.2 LTS, and 6.0, so
  every supported version is both installable and covered by CI.
- Softer, more accurate accessibility wording (designed to meet WCAG 2.2 AA; a
  full independent audit is still planned).
- Friendlier README quick start: install, migrate, add one tag — the admin is
  optional.

### Fixed

- Not all admin labels were marked as translatable, so some always showed in
  English regardless of the active language (uploaded-icon details and the
  created/updated timestamps). They are now translatable and translated to
  Russian, and the Russian catalog has been refreshed.

## [0.1.0] - 2026-06-27

Initial public release (beta) of **django-scroll-to-top** — a reusable Django app
that renders one accessible, configurable scroll-to-top control on site pages and
in the standard Django Admin.

For the full feature set and configuration, see the [README](README.md) and the
[documentation](docs/README.md). From this release onward, this file records
changes between versions rather than restating what the package does.

[Unreleased]: https://github.com/kroxiksut/django-scroll-to-top/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/kroxiksut/django-scroll-to-top/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kroxiksut/django-scroll-to-top/releases/tag/v0.1.0
