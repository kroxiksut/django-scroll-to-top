(function () {
  "use strict";

  var ROOT_SELECTOR = ".dstt-control-wrap";
  var CONTRACT_VERSION = "1";
  var instances = new WeakMap();
  var globalApi = {
    version: CONTRACT_VERSION,
    init: initAll,
    refresh: refreshAll,
    destroy: destroyAll
  };

  function initAll(root) {
    var roots = root ? normalizeRoots(root) : document.querySelectorAll(ROOT_SELECTOR);
    Array.prototype.forEach.call(roots, initRoot);
  }

  function refreshAll(root) {
    var roots = root ? normalizeRoots(root) : document.querySelectorAll(ROOT_SELECTOR);
    Array.prototype.forEach.call(roots, function (node) {
      var instance = instances.get(node);
      if (instance) {
        instance.scheduleMeasure();
        instance.scheduleVisibility();
      } else {
        initRoot(node);
      }
    });
  }

  function destroyAll(root) {
    var roots = root ? normalizeRoots(root) : document.querySelectorAll(ROOT_SELECTOR);
    Array.prototype.forEach.call(roots, destroyRoot);
  }

  function normalizeRoots(root) {
    if (root.matches && root.matches(ROOT_SELECTOR)) {
      return [root];
    }
    return root.querySelectorAll ? root.querySelectorAll(ROOT_SELECTOR) : [];
  }

  function parseJsonList(raw) {
    if (!raw) {
      return [];
    }
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      return [];
    }
  }

  function isObstacleVisible(element) {
    if (!element || element.nodeType !== 1) {
      return false;
    }
    var style = window.getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden") {
      return false;
    }
    if (parseFloat(style.opacity) === 0) {
      return false;
    }
    var rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function rectInViewport(rect) {
    var vw = window.innerWidth || document.documentElement.clientWidth;
    var vh = window.innerHeight || document.documentElement.clientHeight;
    return rect.bottom > 0 && rect.top < vh && rect.right > 0 && rect.left < vw;
  }

  function rectsOverlap(a, b) {
    return (
      a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top
    );
  }

  // Collect obstacle elements from the shared marker plus configured selectors.
  // A broken selector is isolated so it cannot break the others.
  function collectObstacles(selectors, root) {
    var found = [];
    var seen = [];

    function add(nodeList) {
      Array.prototype.forEach.call(nodeList, function (element) {
        if (root.contains(element) || seen.indexOf(element) !== -1) {
          return;
        }
        seen.push(element);
        found.push(element);
      });
    }

    add(document.querySelectorAll("[data-scroll-top-obstacle]"));
    selectors.forEach(function (selector) {
      try {
        add(document.querySelectorAll(selector));
      } catch (error) {
        /* Ignore an invalid selector and keep the rest working. */
      }
    });
    return found;
  }

  // Expand an obstacle rect by the configured gap, allowing a per-obstacle
  // override via [data-scroll-top-obstacle-gap]. A marker may also declare a
  // [data-scroll-top-obstacle-priority] used for deterministic ordering.
  function obstacleBox(element, defaultGap) {
    var rect = element.getBoundingClientRect();
    var override = parseInt(
      element.getAttribute("data-scroll-top-obstacle-gap"),
      10
    );
    var gap = isNaN(override) ? defaultGap : override;
    var priority = parseInt(
      element.getAttribute("data-scroll-top-obstacle-priority"),
      10
    );
    return {
      left: rect.left - gap,
      right: rect.right + gap,
      top: rect.top - gap,
      bottom: rect.bottom + gap,
      priority: isNaN(priority) ? 0 : priority
    };
  }

  function initRoot(root) {
    if (!root || instances.has(root)) {
      return;
    }
    if (root.getAttribute("data-dstt-contract-version") !== CONTRACT_VERSION) {
      return;
    }
    var control = root.querySelector(".dstt-control");
    var dismissControl = root.querySelector("[data-dstt-dismiss-control]");
    if (!control) {
      return;
    }

    var state = {
      visibility: {
        belowThreshold: false,
        runtimeVisible: true
      },
      collision: {
        blocked: false,
        shiftX: 0,
        shiftY: 0,
        corner: root.getAttribute("data-dstt-corner") || "bottom-right"
      },
      dismissal: {
        dismissed: false
      }
    };
    var dismissalStorageMode = root.getAttribute("data-dstt-dismissal-storage") || "local";
    var allowUserDismissal = root.getAttribute("data-dstt-allow-dismissal") === "true";
    var dismissalDuration =
      root.getAttribute("data-dstt-dismissal-duration") || "persistent";
    var dismissalDays =
      parseInt(root.getAttribute("data-dstt-dismissal-days"), 10) || 0;
    var dismissalRequiresConfirmation =
      root.getAttribute("data-dstt-dismissal-confirm") === "true";
    var dismissConfirmText =
      root.getAttribute("data-dstt-dismiss-confirm-text") || "";

    var baseCorner = state.collision.corner;
    var collisionPolicy = root.getAttribute("data-dstt-collision-policy") || "ignore";
    var obstacleSelectors = parseJsonList(
      root.getAttribute("data-dstt-obstacle-selectors")
    );
    var fallbackCorners = parseJsonList(
      root.getAttribute("data-dstt-fallback-corners")
    );
    var obstacleGap = parseInt(root.getAttribute("data-dstt-obstacle-gap"), 10) || 0;
    var maxShift =
      parseInt(root.getAttribute("data-dstt-collision-max-shift"), 10) || 0;

    /* Optional full-height side click strip. Created on <body> because the wrap
       is transformed (which would contain a fixed child). Skipped inside the
       admin live preview so it never overlays the admin chrome. */
    var hotZonePlacement = root.getAttribute("data-dstt-hot-zone") || "none";
    var hotZoneAppearance =
      root.getAttribute("data-dstt-hot-zone-appearance") || "hover";
    var inPreview = !!(
      root.closest &&
      root.closest(
        "[data-dstt-live-preview], .dstt-preview-grid, .dstt-live-preview-fieldset"
      )
    );
    var hotZoneEl = null;

    // Visibility (§11) and scroll behavior (§12) configuration.
    var thresholdMode = root.getAttribute("data-dstt-threshold-mode") || "pixels";
    var showAfterPx = parseInt(root.getAttribute("data-dstt-show-after-px"), 10);
    if (isNaN(showAfterPx)) {
      showAfterPx = 240;
    }
    var showAfterViewports = parseFloat(
      root.getAttribute("data-dstt-show-after-viewports")
    );
    if (isNaN(showAfterViewports)) {
      showAfterViewports = 1;
    }
    var minDocumentHeight =
      parseInt(root.getAttribute("data-dstt-min-document-height"), 10) || 0;
    var showDelay = parseInt(root.getAttribute("data-dstt-show-delay"), 10) || 0;
    var hideDelay = parseInt(root.getAttribute("data-dstt-hide-delay"), 10) || 0;
    var visibilityDirection =
      root.getAttribute("data-dstt-visibility-direction") || "always";
    var scrollTargetSelector =
      root.getAttribute("data-dstt-scroll-target") || "";
    var scrollOffset =
      parseInt(root.getAttribute("data-dstt-scroll-offset"), 10) || 0;
    var fixedHeaderSelector = root.getAttribute("data-dstt-fixed-header") || "";
    var scrollBehavior =
      root.getAttribute("data-dstt-scroll-behavior") || "smooth";
    var lastScrollY = window.scrollY;
    var visibilityTimer = 0;
    var selfMutating = false;
    // Debug overlays draw obstacle rects; off in production, opt-in for preview
    // via an ancestor [data-dstt-collision-debug] or window.djstt.debug().
    var debugEnabled = !!(
      root.closest && root.closest("[data-dstt-collision-debug='true']")
    );
    var debugOverlays = [];

    var rafVisibility = 0;
    var rafMeasure = 0;
    var measureTimeout = 0;
    var rootObserver = new MutationObserver(function () {
      if (!document.documentElement.contains(root)) {
        destroyRoot(root);
      }
    });
    var resizeObserver =
      typeof window.ResizeObserver === "function"
        ? new window.ResizeObserver(function () {
            scheduleMeasure();
          })
        : null;
    var collisionObserver = new MutationObserver(function (mutations) {
      if (selfMutating) {
        return;
      }
      // Ignore mutations that only touch our own control subtree to avoid an
      // observer -> style -> observer feedback loop.
      for (var i = 0; i < mutations.length; i++) {
        if (!root.contains(mutations[i].target)) {
          scheduleMeasure();
          return;
        }
      }
    });

    function emit(name, detail) {
      root.dispatchEvent(
        new CustomEvent(name, {
          bubbles: true,
          detail: detail
        })
      );
    }

    // A minimal cookie-backed storage shim with the Web Storage interface so
    // the read/write helpers stay agnostic of the configured mechanism. Cookie
    // names cannot contain ":" so the namespaced key is sanitized.
    function cookieStorage() {
      function cookieName(key) {
        return key.replace(/[^A-Za-z0-9_-]/g, "_");
      }
      // Mark the functional dismissal cookie Secure on HTTPS. Left off for plain
      // HTTP so local and intranet deployments keep working.
      function secureFlag() {
        return window.location && window.location.protocol === "https:"
          ? "; Secure"
          : "";
      }
      return {
        getItem: function (key) {
          var name = cookieName(key) + "=";
          var parts = document.cookie ? document.cookie.split("; ") : [];
          for (var i = 0; i < parts.length; i++) {
            if (parts[i].indexOf(name) === 0) {
              return decodeURIComponent(parts[i].slice(name.length));
            }
          }
          return null;
        },
        setItem: function (key, value) {
          var maxAge = 31536000;
          if (dismissalDuration === "days" && dismissalDays > 0) {
            maxAge = dismissalDays * 86400;
          }
          document.cookie =
            cookieName(key) +
            "=" +
            encodeURIComponent(value) +
            "; path=/; max-age=" +
            maxAge +
            "; SameSite=Lax" +
            secureFlag();
        },
        removeItem: function (key) {
          document.cookie =
            cookieName(key) +
            "=; path=/; max-age=0; SameSite=Lax" +
            secureFlag();
        }
      };
    }

    function dismissalStorage() {
      try {
        if (dismissalStorageMode === "session") {
          return window.sessionStorage;
        }
        if (dismissalStorageMode === "local") {
          return window.localStorage;
        }
        if (dismissalStorageMode === "cookie") {
          return cookieStorage();
        }
      } catch (error) {
        return null;
      }
      return null;
    }

    function dismissalStorageKey() {
      return [
        "djstt",
        "dismissal",
        root.getAttribute("data-dstt-scope") || "site",
        root.getAttribute("data-dstt-site-id") || "global",
        root.getAttribute("data-dstt-config") || "default",
        root.getAttribute("data-dstt-dismissal-version") || "1"
      ].join(":");
    }

    function readDismissalState() {
      var storage = dismissalStorage();
      if (!storage) {
        return false;
      }
      try {
        var raw = storage.getItem(dismissalStorageKey());
        if (!raw) {
          return false;
        }
        // Day-based dismissals store an expiry timestamp and self-clear once
        // they lapse.
        if (raw.indexOf("until:") === 0) {
          var until = parseInt(raw.slice(6), 10);
          if (isNaN(until) || Date.now() > until) {
            storage.removeItem(dismissalStorageKey());
            return false;
          }
          return true;
        }
        return raw === "dismissed";
      } catch (error) {
        return false;
      }
    }

    function writeDismissalState(dismissed) {
      var storage = dismissalStorage();
      if (!storage) {
        return;
      }
      try {
        if (dismissed) {
          var value = "dismissed";
          if (dismissalDuration === "days" && dismissalDays > 0) {
            value = "until:" + (Date.now() + dismissalDays * 86400000);
          }
          storage.setItem(dismissalStorageKey(), value);
        } else {
          storage.removeItem(dismissalStorageKey());
        }
      } catch (error) {
        /* Persisting dismissal is best-effort: ignore storage failures (for
           example private mode or an exceeded quota). */
      }
    }

    function applyVisibility() {
      var shouldShow =
        state.visibility.belowThreshold &&
        !state.collision.blocked &&
        !state.dismissal.dismissed;
      if (state.visibility.runtimeVisible === shouldShow) {
        return;
      }
      state.visibility.runtimeVisible = shouldShow;
      root.hidden = !shouldShow;
      root.classList.toggle("dstt-is-hidden", !shouldShow);
      control.setAttribute("aria-hidden", shouldShow ? "false" : "true");
      if (hotZoneEl) {
        hotZoneEl.hidden = !shouldShow;
      }
      emit(shouldShow ? "djstt:show" : "djstt:hide", {
        visible: shouldShow
      });
    }

    function documentHeight() {
      return Math.max(
        document.documentElement.scrollHeight,
        document.body ? document.body.scrollHeight : 0
      );
    }

    // A page-level opt-out marker disables the control without removing it.
    function isDisabledByMarker() {
      return !!(
        document.body &&
        document.body.getAttribute("data-scroll-top") === "disabled"
      );
    }

    function thresholdReached() {
      if (minDocumentHeight > 0 && documentHeight() < minDocumentHeight) {
        return false;
      }
      var vh = window.innerHeight || document.documentElement.clientHeight;
      var y = window.scrollY;
      var pixelsReached = y > showAfterPx;
      var viewportReached = y > showAfterViewports * vh;
      if (thresholdMode === "viewport") {
        return viewportReached;
      }
      if (thresholdMode === "combined") {
        return pixelsReached && viewportReached;
      }
      return pixelsReached;
    }

    function computeShouldBeVisible() {
      if (isDisabledByMarker() || !thresholdReached()) {
        return false;
      }
      var y = window.scrollY;
      var movingDown = y > lastScrollY;
      var movingUp = y < lastScrollY;
      if (visibilityDirection === "hide_on_scroll_down" && movingDown) {
        return false;
      }
      if (visibilityDirection === "scroll_up_only") {
        if (movingDown) {
          return false;
        }
        // When idle and currently hidden, wait for an explicit upward scroll.
        if (!movingUp && !state.visibility.runtimeVisible) {
          return false;
        }
      }
      return true;
    }

    function applyDesiredVisibility(desired) {
      state.visibility.belowThreshold = desired;
      var delay = desired ? showDelay : hideDelay;
      if (visibilityTimer) {
        window.clearTimeout(visibilityTimer);
        visibilityTimer = 0;
      }
      if (delay > 0) {
        visibilityTimer = window.setTimeout(function () {
          visibilityTimer = 0;
          applyVisibility();
        }, delay);
      } else {
        applyVisibility();
      }
    }

    function scheduleVisibility() {
      if (rafVisibility) {
        return;
      }
      rafVisibility = window.requestAnimationFrame(function () {
        rafVisibility = 0;
        var desired = computeShouldBeVisible();
        lastScrollY = window.scrollY;
        applyDesiredVisibility(desired);
      });
    }

    function setCollisionShift(x, y) {
      state.collision.shiftX = x;
      state.collision.shiftY = y;
      root.style.setProperty("--dstt-collision-shift-x", x + "px");
      root.style.setProperty("--dstt-collision-shift-y", y + "px");
    }

    function setCollisionCorner(corner) {
      if (state.collision.corner === corner) {
        return;
      }
      state.collision.corner = corner;
      root.setAttribute("data-dstt-corner", corner);
    }

    // Recover the unshifted control box by subtracting the applied shift, so
    // repeated measurements never feed back on themselves.
    function baseControlRect() {
      var rect = control.getBoundingClientRect();
      return {
        left: rect.left - state.collision.shiftX,
        right: rect.right - state.collision.shiftX,
        top: rect.top - state.collision.shiftY,
        bottom: rect.bottom - state.collision.shiftY,
        width: rect.width,
        height: rect.height
      };
    }

    function viewportSize() {
      return {
        width: window.innerWidth || document.documentElement.clientWidth,
        height: window.innerHeight || document.documentElement.clientHeight
      };
    }

    // The pinned-edge distances of the base corner equal the configured offsets.
    function cornerInsets(rect, corner) {
      var vp = viewportSize();
      return {
        inline:
          corner === "top-right" || corner === "bottom-right"
            ? vp.width - rect.right
            : rect.left,
        block:
          corner === "bottom-left" || corner === "bottom-right"
            ? vp.height - rect.bottom
            : rect.top
      };
    }

    function predictRect(corner, insets, width, height) {
      var vp = viewportSize();
      var left =
        corner === "top-right" || corner === "bottom-right"
          ? vp.width - insets.inline - width
          : insets.inline;
      var top =
        corner === "bottom-left" || corner === "bottom-right"
          ? vp.height - insets.block - height
          : insets.block;
      return { left: left, right: left + width, top: top, bottom: top + height };
    }

    function obstacleBoxes() {
      var boxes = [];
      collectObstacles(obstacleSelectors, root).forEach(function (element) {
        if (!isObstacleVisible(element)) {
          return;
        }
        var box = obstacleBox(element, obstacleGap);
        if (rectInViewport(box)) {
          boxes.push(box);
        }
      });
      // Deterministic order: higher priority first, then by position.
      boxes.sort(function (a, b) {
        return b.priority - a.priority || a.top - b.top || a.left - b.left;
      });
      return boxes;
    }

    function intersectsAny(rect, boxes) {
      for (var i = 0; i < boxes.length; i++) {
        if (rectsOverlap(rect, boxes[i])) {
          return true;
        }
      }
      return false;
    }

    // Shift along the vertical edge away from obstacles overlapping the control
    // horizontally, bounded by the configured maximum displacement.
    function resolveShift(rect, boxes, corner) {
      var movingUp = corner === "bottom-left" || corner === "bottom-right";
      var movingDown = corner === "top-left" || corner === "top-right";
      if (!movingUp && !movingDown) {
        return 0;
      }
      var required = 0;
      for (var i = 0; i < boxes.length; i++) {
        var box = boxes[i];
        if (rect.left >= box.right || rect.right <= box.left) {
          continue;
        }
        if (!(box.top < rect.bottom && box.bottom > rect.top)) {
          continue;
        }
        required = movingUp
          ? Math.max(required, rect.bottom - box.top)
          : Math.max(required, box.bottom - rect.top);
      }
      if (required <= 0) {
        return 0;
      }
      var limited = Math.min(required, maxShift);
      return movingUp ? -limited : limited;
    }

    function removeDebugOverlays() {
      for (var i = 0; i < debugOverlays.length; i++) {
        if (debugOverlays[i].parentNode) {
          debugOverlays[i].parentNode.removeChild(debugOverlays[i]);
        }
      }
      debugOverlays = [];
    }

    function renderDebugOverlays(boxes) {
      removeDebugOverlays();
      if (!document.body) {
        return;
      }
      boxes.forEach(function (box) {
        var overlay = document.createElement("div");
        overlay.className = "dstt-obstacle-debug";
        overlay.setAttribute("aria-hidden", "true");
        overlay.style.left = box.left + "px";
        overlay.style.top = box.top + "px";
        overlay.style.width = Math.max(0, box.right - box.left) + "px";
        overlay.style.height = Math.max(0, box.bottom - box.top) + "px";
        document.body.appendChild(overlay);
        debugOverlays.push(overlay);
      });
    }

    function setDebug(enabled) {
      debugEnabled = !!enabled;
      scheduleMeasure();
    }

    function applyMeasureResult(blocked, shiftX, shiftY, corner, boxes) {
      selfMutating = true;
      setCollisionCorner(corner);
      setCollisionShift(shiftX, shiftY);
      state.collision.blocked = blocked;
      applyVisibility();
      if (debugEnabled) {
        renderDebugOverlays(boxes || []);
      } else {
        removeDebugOverlays();
      }
      window.requestAnimationFrame(function () {
        selfMutating = false;
      });
    }

    function measure() {
      var boxes =
        collisionPolicy !== "ignore" || debugEnabled ? obstacleBoxes() : [];
      if (collisionPolicy === "ignore") {
        applyMeasureResult(false, 0, 0, baseCorner, boxes);
        return;
      }
      if (!boxes.length) {
        applyMeasureResult(false, 0, 0, baseCorner, boxes);
        return;
      }
      var rect = baseControlRect();

      if (collisionPolicy === "hide") {
        applyMeasureResult(intersectsAny(rect, boxes), 0, 0, baseCorner, boxes);
        return;
      }

      if (collisionPolicy === "shift") {
        applyMeasureResult(
          false,
          0,
          resolveShift(rect, boxes, baseCorner),
          baseCorner,
          boxes
        );
        return;
      }

      if (collisionPolicy === "fallback_corner") {
        if (!intersectsAny(rect, boxes)) {
          applyMeasureResult(false, 0, 0, baseCorner, boxes);
          return;
        }
        var insets = cornerInsets(rect, baseCorner);
        for (var i = 0; i < fallbackCorners.length; i++) {
          var predicted = predictRect(
            fallbackCorners[i],
            insets,
            rect.width,
            rect.height
          );
          if (!intersectsAny(predicted, boxes)) {
            applyMeasureResult(false, 0, 0, fallbackCorners[i], boxes);
            return;
          }
        }
        applyMeasureResult(true, 0, 0, baseCorner, boxes);
        return;
      }

      applyMeasureResult(false, 0, 0, baseCorner, boxes);
    }

    function scheduleMeasure() {
      if (measureTimeout) {
        window.clearTimeout(measureTimeout);
      }
      measureTimeout = window.setTimeout(function () {
        if (rafMeasure) {
          return;
        }
        rafMeasure = window.requestAnimationFrame(function () {
          rafMeasure = 0;
          measureTimeout = 0;
          measure();
        });
      }, 40);
    }

    function onScroll() {
      scheduleVisibility();
      scheduleMeasure();
    }

    function onResize() {
      scheduleMeasure();
    }

    function queryFirst(selector) {
      if (!selector) {
        return null;
      }
      try {
        return document.querySelector(selector);
      } catch (error) {
        return null;
      }
    }

    // Move keyboard focus to the scroll target without scrolling again, using a
    // temporary tabindex that is cleared on blur so the DOM is left unchanged.
    function focusTarget(element) {
      var hadTabindex = element.hasAttribute("tabindex");
      if (!hadTabindex) {
        element.setAttribute("tabindex", "-1");
        element.addEventListener("blur", function handler() {
          element.removeAttribute("tabindex");
          element.removeEventListener("blur", handler);
        });
      }
      try {
        element.focus({ preventScroll: true });
      } catch (error) {
        element.focus();
      }
    }

    function resolveScrollTop(targetElement) {
      var top = 0;
      if (targetElement) {
        top = targetElement.getBoundingClientRect().top + window.scrollY;
      }
      var header = queryFirst(fixedHeaderSelector);
      if (header && isObstacleVisible(header)) {
        top -= header.getBoundingClientRect().height;
      }
      top -= scrollOffset;
      return top < 0 ? 0 : top;
    }

    function onClick(event) {
      if (event.defaultPrevented) {
        return;
      }
      event.preventDefault();
      var targetElement = queryFirst(scrollTargetSelector);
      var top = resolveScrollTop(targetElement);
      emit("djstt:scroll-start", {
        top: top
      });
      var reduceMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;
      if (scrollBehavior === "instant" || reduceMotion) {
        window.scrollTo(0, top);
      } else {
        window.scrollTo({
          top: top,
          behavior: "smooth"
        });
      }
      if (targetElement) {
        focusTarget(targetElement);
      }
      window.setTimeout(function () {
        emit("djstt:scroll-end", {
          top: window.scrollY
        });
      }, 250);
    }

    function dismiss() {
      if (!allowUserDismissal) {
        return;
      }
      if (
        dismissalRequiresConfirmation &&
        typeof window.confirm === "function" &&
        !window.confirm(dismissConfirmText || "Hide this button?")
      ) {
        return;
      }
      state.dismissal.dismissed = true;
      writeDismissalState(true);
      applyVisibility();
      emit("djstt:dismiss", {
        dismissed: true,
        storage: dismissalStorageMode
      });
    }

    function restore() {
      state.dismissal.dismissed = false;
      writeDismissalState(false);
      applyVisibility();
      emit("djstt:restore", {
        dismissed: false
      });
    }

    function onDismissClick(event) {
      event.preventDefault();
      event.stopPropagation();
      dismiss();
    }

    function createHotZone() {
      if (hotZonePlacement === "none" || inPreview || !document.body) {
        return;
      }
      hotZoneEl = document.createElement("div");
      hotZoneEl.className = "dstt-hot-zone";
      hotZoneEl.setAttribute("aria-hidden", "true");
      hotZoneEl.setAttribute("data-dstt-hot-zone-side", hotZonePlacement);
      hotZoneEl.setAttribute("data-dstt-hot-zone-appearance", hotZoneAppearance);
      var widthVar = window
        .getComputedStyle(root)
        .getPropertyValue("--dstt-hot-zone-width");
      hotZoneEl.style.width =
        widthVar && widthVar.trim() ? widthVar.trim() : "120px";
      hotZoneEl.hidden = !state.visibility.runtimeVisible;
      hotZoneEl.addEventListener("click", onClick);
      document.body.appendChild(hotZoneEl);
    }

    function destroyHotZone() {
      if (!hotZoneEl) {
        return;
      }
      hotZoneEl.removeEventListener("click", onClick);
      if (hotZoneEl.parentNode) {
        hotZoneEl.parentNode.removeChild(hotZoneEl);
      }
      hotZoneEl = null;
    }

    var instance = {
      destroy: function () {
        window.removeEventListener("scroll", onScroll, { passive: true });
        window.removeEventListener("resize", onResize, { passive: true });
        control.removeEventListener("click", onClick);
        if (dismissControl) {
          dismissControl.removeEventListener("click", onDismissClick);
        }
        rootObserver.disconnect();
        if (resizeObserver) {
          resizeObserver.disconnect();
        }
        collisionObserver.disconnect();
        removeDebugOverlays();
        destroyHotZone();
        if (rafVisibility) {
          window.cancelAnimationFrame(rafVisibility);
        }
        if (rafMeasure) {
          window.cancelAnimationFrame(rafMeasure);
        }
        if (measureTimeout) {
          window.clearTimeout(measureTimeout);
        }
        if (visibilityTimer) {
          window.clearTimeout(visibilityTimer);
        }
        instances.delete(root);
      },
      scheduleMeasure: scheduleMeasure,
      scheduleVisibility: scheduleVisibility,
      dismiss: dismiss,
      restore: restore,
      setDebug: setDebug
    };

    state.dismissal.dismissed = readDismissalState();
    instances.set(root, instance);
    rootObserver.observe(document.documentElement, {
      childList: true,
      subtree: true
    });
    if (collisionPolicy !== "ignore") {
      if (resizeObserver) {
        resizeObserver.observe(document.documentElement);
      }
      if (document.body) {
        collisionObserver.observe(document.body, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ["style", "class", "hidden"]
        });
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    control.addEventListener("click", onClick);
    if (dismissControl) {
      dismissControl.addEventListener("click", onDismissClick);
    }
    createHotZone();
    scheduleVisibility();
    scheduleMeasure();
  }

  function destroyRoot(root) {
    var instance = instances.get(root);
    if (instance) {
      instance.destroy();
    }
  }

  function bootstrap() {
    initAll();
  }

  function forEachInstance(root, callback) {
    var roots = root ? normalizeRoots(root) : document.querySelectorAll(ROOT_SELECTOR);
    Array.prototype.forEach.call(roots, function (node) {
      var instance = instances.get(node);
      if (instance) {
        callback(instance);
      }
    });
  }

  if (!window.djstt) {
    globalApi.dismiss = function (root) {
      forEachInstance(root, function (instance) {
        instance.dismiss();
      });
    };
    globalApi.restore = function (root) {
      forEachInstance(root, function (instance) {
        instance.restore();
      });
    };
    globalApi.debug = function (enabled, root) {
      forEachInstance(root, function (instance) {
        instance.setDebug(enabled);
      });
    };
    window.djstt = globalApi;
  }

  document.addEventListener("DOMContentLoaded", bootstrap, { once: true });
  document.addEventListener("htmx:afterSwap", function (event) {
    initAll(event.target);
  });
  document.addEventListener("turbo:load", function () {
    refreshAll();
  });
})();
