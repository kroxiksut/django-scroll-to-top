// Public type declarations for the django-scroll-to-top browser runtime.
//
// Ambient global typings for the `window.djstt` API and the `djstt:*` DOM
// events — the documented public contract (see ARCHITECTURE.md). The runtime
// ships as vanilla ES5 and is not built from these types; this file exists so
// integrators (and future `tsc --checkJs` work) have a typed contract to build
// on. Keep it in sync with `scroll-to-top.js`.

/** A scope passed to the API: an element/document subtree, or omitted for the
 *  whole document. */
type DjsttRoot = Document | Element;

interface DjsttApi {
  /** Contract version string (currently "1"). */
  readonly version: string;
  /** Initialize every control within `root` (default: whole document). Idempotent. */
  init(root?: DjsttRoot): void;
  /** Re-measure and re-evaluate visibility; initializes any not-yet-initialized control. */
  refresh(root?: DjsttRoot): void;
  /** Tear down controls within `root`, removing listeners and observers. */
  destroy(root?: DjsttRoot): void;
  /** Programmatically dismiss matching controls (honours the configured storage). */
  dismiss(root?: DjsttRoot): void;
  /** Restore previously dismissed controls. */
  restore(root?: DjsttRoot): void;
  /** Toggle collision debug overlays for matching controls. */
  debug(enabled: boolean, root?: DjsttRoot): void;
}

/** `detail` payload of `djstt:show` / `djstt:hide`. */
interface DjsttVisibilityDetail {
  visible: boolean;
}

/** `detail` payload of `djstt:scroll-start` / `djstt:scroll-end`. */
interface DjsttScrollDetail {
  top: number;
}

/** `detail` payload of `djstt:dismiss`. */
interface DjsttDismissDetail {
  dismissed: boolean;
  storage: string;
}

/** `detail` payload of `djstt:restore`. */
interface DjsttRestoreDetail {
  dismissed: boolean;
}

/** The namespaced CustomEvents the runtime dispatches. They bubble from the
 *  `.dstt-control-wrap` element, so they can be observed on the element, on
 *  `document`, or on `window`. */
interface DjsttEventMap {
  "djstt:show": CustomEvent<DjsttVisibilityDetail>;
  "djstt:hide": CustomEvent<DjsttVisibilityDetail>;
  "djstt:scroll-start": CustomEvent<DjsttScrollDetail>;
  "djstt:scroll-end": CustomEvent<DjsttScrollDetail>;
  "djstt:dismiss": CustomEvent<DjsttDismissDetail>;
  "djstt:restore": CustomEvent<DjsttRestoreDetail>;
}

interface Window {
  /** Present once the runtime script has loaded. */
  djstt: DjsttApi;
}

interface WindowEventMap extends DjsttEventMap {}
interface DocumentEventMap extends DjsttEventMap {}
interface HTMLElementEventMap extends DjsttEventMap {}
