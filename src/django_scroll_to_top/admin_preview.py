from __future__ import annotations

from dataclasses import replace

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from django_scroll_to_top.forms import ScrollToTopPreviewForm
from django_scroll_to_top.presentation import VisualConfig
from django_scroll_to_top.renderer import build_render_payload
from django_scroll_to_top.styles import build_component_stylesheet, build_style_token


def render_admin_preview(form: ScrollToTopPreviewForm) -> str:
    config = form.to_visual_config()
    style_token = build_style_token(config)
    # The compact live panel is the primary preview: a single button updated on
    # the fly by JS (CSS variables + data attributes) with theme/state/viewport
    # toggles. The richer scenario panels stay collapsed below.
    live_panel = _build_live_panel(config=config, style_token=style_token)
    panels = []
    panels.extend(
        [
            _build_four_corners_panel(
                viewport="desktop",
                theme="light",
                config=config,
                style_token=style_token,
            ),
            _build_four_corners_panel(
                viewport="mobile",
                theme="dark",
                config=config,
                style_token=style_token,
            ),
            _build_obstacle_panel(
                label=str(_("Cookie banner collision")),
                viewport="desktop",
                theme="light",
                background="surface",
                scenes=(
                    {
                        "label": str(_("Cookie banner on the right")),
                        "corner": "bottom-right",
                        "obstacles": ("cookie-right",),
                    },
                    {
                        "label": str(_("Cookie banner on the left")),
                        "corner": "bottom-left",
                        "obstacles": ("cookie-left",),
                    },
                ),
                config=config,
                style_token=style_token,
            ),
            _build_obstacle_panel(
                label=str(_("Mobile bottom navigation")),
                viewport="mobile",
                theme="light",
                background="app",
                scenes=(
                    {
                        "label": str(_("Sticky mobile navigation")),
                        "corner": "bottom-right",
                        "obstacles": ("mobile-nav",),
                    },
                ),
                config=config,
                style_token=style_token,
            ),
            _build_obstacle_panel(
                label=str(_("Chat widget and multiple obstacles")),
                viewport="desktop",
                theme="dark",
                background="dashboard",
                scenes=(
                    {
                        "label": str(_("Chat widget")),
                        "corner": "bottom-left",
                        "obstacles": ("chat-left",),
                    },
                    {
                        "label": str(_("Multiple obstacles")),
                        "corner": "bottom-right",
                        "obstacles": ("chat-right", "toast-stack", "cookie-right"),
                    },
                ),
                config=config,
                style_token=style_token,
            ),
            _build_scroll_behavior_panel(
                config=config,
                style_token=style_token,
            ),
            _build_reduced_motion_panel(
                config=config,
                style_token=style_token,
            ),
        ]
    )
    return render_to_string(
        "django_scroll_to_top/admin_preview.html",
        {
            "live_panel": live_panel,
            "panels": panels,
            "preview_stylesheet": build_component_stylesheet(
                config=config,
                selector=(
                    ".dstt-live-preview-fieldset .dstt-control-wrap"
                    f'[data-dstt-config="{style_token}"]'
                ),
            ),
        },
    )


def _build_live_panel(
    *,
    config: VisualConfig,
    style_token: str,
) -> dict[str, object]:
    payload = build_render_payload(config, style_token=style_token)
    return {
        "markup": render_to_string(
            "django_scroll_to_top/scroll_to_top.html",
            {"scroll_to_top": payload},
        ),
    }


def _build_four_corners_panel(
    *,
    viewport: str,
    theme: str,
    config: VisualConfig,
    style_token: str,
) -> dict[str, object]:
    scenes = []
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        scenes.append(
            _build_scene(
                config=replace(config, corner=corner),
                style_token=style_token,
                label=corner.replace("-", " ").title(),
                background="article" if corner.startswith("top") else "surface",
            )
        )
    return {
        "label": str(_("Four corners")),
        "viewport": viewport,
        "theme": theme,
        "state": "normal",
        "background": "mixed",
        "scenes": scenes,
    }


def _build_obstacle_panel(
    *,
    label: str,
    viewport: str,
    theme: str,
    background: str,
    scenes: tuple[dict[str, object], ...],
    config: VisualConfig,
    style_token: str,
) -> dict[str, object]:
    return {
        "label": label,
        "viewport": viewport,
        "theme": theme,
        "state": "normal",
        "background": background,
        "scenes": _build_obstacle_scenes(
            scenes=scenes,
            config=config,
            style_token=style_token,
            background=background,
        ),
    }


def _build_scroll_behavior_panel(
    *,
    config: VisualConfig,
    style_token: str,
) -> dict[str, object]:
    return {
        "label": str(_("Threshold and scroll behavior")),
        "viewport": "desktop",
        "theme": "light",
        "state": "runtime",
        "background": "article",
        "scenes": [
            _build_scene(
                config=config,
                style_token=style_token,
                label=str(_("Before threshold")),
                background="article",
                scene_classes=" dstt-preview-scene--before-threshold",
                canvas_classes=" dstt-preview-panel__canvas--scroll",
            ),
            _build_scene(
                config=config,
                style_token=style_token,
                label=str(_("After threshold")),
                background="article",
                scene_classes=" dstt-preview-scene--after-threshold",
                canvas_classes=" dstt-preview-panel__canvas--scroll",
            ),
        ],
    }


def _build_reduced_motion_panel(
    *,
    config: VisualConfig,
    style_token: str,
) -> dict[str, object]:
    return {
        "label": str(_("Reduced motion preview")),
        "viewport": "mobile",
        "theme": "dark",
        "state": "focus",
        "background": "app",
        "scenes": [
            _build_scene(
                config=config,
                style_token=style_token,
                label=str(_("Standard motion")),
                background="app",
            ),
            _build_scene(
                config=config,
                style_token=style_token,
                label=str(_("Reduced motion")),
                background="app",
                scene_classes=" dstt-preview-scene--reduced-motion",
            ),
        ],
    }


def _build_scene(
    *,
    config: VisualConfig,
    style_token: str,
    label: str,
    background: str,
    scene_classes: str = "",
    canvas_classes: str = "",
    obstacles: tuple[str, ...] = (),
    debug: bool = False,
) -> dict[str, object]:
    payload = build_render_payload(config, style_token=style_token)
    return {
        "label": label,
        "background": background,
        "scene_classes": scene_classes,
        "canvas_classes": canvas_classes,
        "markup": render_to_string(
            "django_scroll_to_top/scroll_to_top.html",
            {"scroll_to_top": payload},
        ),
        "obstacles": [
            {
                "kind": obstacle,
                "label": obstacle.replace("-", " "),
            }
            for obstacle in obstacles
        ],
        "debug": debug,
    }


def _build_obstacle_scenes(
    *,
    scenes: tuple[dict[str, object], ...],
    config: VisualConfig,
    style_token: str,
    background: str,
) -> list[dict[str, object]]:
    built_scenes: list[dict[str, object]] = []
    for scene in scenes:
        obstacles = scene["obstacles"]
        assert isinstance(obstacles, tuple)
        built_scenes.append(
            _build_scene(
                config=replace(config, corner=str(scene["corner"])),
                style_token=style_token,
                label=str(scene["label"]),
                background=background,
                obstacles=tuple(str(item) for item in obstacles),
                debug=len(obstacles) > 1,
            )
        )
    return built_scenes
