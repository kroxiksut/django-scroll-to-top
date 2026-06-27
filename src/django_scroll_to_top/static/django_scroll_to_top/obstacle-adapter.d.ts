// Public type declarations for the optional obstacle adapter
// (`window.djsttObstacleAdapter`). Ambient globals; keep in sync with
// `obstacle-adapter.js`. Loading the adapter is optional and never makes any
// third-party widget a dependency.

/** A registration passed to `register()`. */
interface DjsttObstacleRegistration {
  /** One selector or a list of selectors to tag as collision obstacles. */
  selectors: string | string[];
  /** Per-obstacle gap in px (written as `data-scroll-top-obstacle-gap`). */
  gap?: number | null;
  /** Ordering hint (written as `data-scroll-top-obstacle-priority`). */
  priority?: number | null;
  /** Widget events that should trigger a re-tag and `refresh()`. */
  events?: string[];
}

/** A ready-made registration preset. */
interface DjsttObstaclePreset {
  selectors: string[];
  gap?: number;
  priority?: number;
  events?: string[];
}

interface DjsttObstacleAdapter {
  /** Tag matching markup as obstacles and bridge the given events to `refresh()`. */
  register(config: DjsttObstacleRegistration): void;
  /** Re-tag all registered selectors and recalculate placement. */
  refresh(): void;
  /** Ready-made registrations for common floating widgets. */
  readonly presets: {
    djangoCookies152fz: DjsttObstaclePreset;
    stickyBottomNavigation: DjsttObstaclePreset;
  };
}

interface Window {
  /** Present only when the optional obstacle-adapter script is loaded. */
  djsttObstacleAdapter?: DjsttObstacleAdapter;
}
