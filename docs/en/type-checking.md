# Type checking (Pyright)

- [Back to documentation index](../README.md)
- [Testing the package](./testing.md)

The package is typed (`py.typed` is shipped, and the `Typing :: Typed` classifier
is declared). Pyright is the reference type checker; the public renderer payload,
settings accessors, and service signatures are all typed so integrators get a
stable, checkable contract.

## Running Pyright

```console
python -m pyright
```

Package-local defaults live in `pyrightconfig.json`. Install the dev extras to
get Pyright and the Django stubs:

```console
python -m pip install -e ".[dev]"
```

(`[dev]` provides `ruff`, `pyright`, `django-stubs`, `build`, and `twine`.)

## Why it is required

- The renderer returns a typed, serialization-friendly `RenderPayload` /
  `RenderContext` rather than an ORM object, so its shape must stay checkable.
- Settings accessors expose typed values (`CspMode`, `CollisionPolicy`, …) used by
  system checks and the renderer.
- The browser runtime ships a typed contract in `scroll-to-top.d.ts` and
  `obstacle-adapter.d.ts`, kept in sync with the vanilla-JS runtime.

## Related sections

- [Testing the package](./testing.md)
- [Behavior and runtime](./runtime.md)
