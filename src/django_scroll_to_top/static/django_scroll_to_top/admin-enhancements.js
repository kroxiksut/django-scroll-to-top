/*
 * Admin enhancements for django-scroll-to-top.
 *
 * Progressive enhancement only: reads the standard admin DOM and adds a
 * collapse toggle to this app's own group in the left navigation sidebar
 * (`#nav-sidebar`) so its three menu items can be folded away and stay folded
 * across pages. The collapsed state is remembered in localStorage. Nothing
 * else is touched: only this app's sidebar group is affected (other apps, the
 * main content, and the footer control are left alone), everything is scoped
 * to `#nav-sidebar .app-django_scroll_to_top` and namespaced with `dstt-`.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "dstt-nav-collapsed";
  var APP_SELECTOR = "#nav-sidebar .app-django_scroll_to_top";
  var COLLAPSED_CLASS = "dstt-nav-collapsed";

  function readState() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) === "1";
    } catch (e) {
      return false;
    }
  }

  function writeState(collapsed) {
    try {
      window.localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
    } catch (e) {
      /* storage unavailable (private mode / disabled); degrade gracefully. */
    }
  }

  function apply(collapsed) {
    var containers = document.querySelectorAll(APP_SELECTOR);
    for (var i = 0; i < containers.length; i++) {
      containers[i].classList.toggle(COLLAPSED_CLASS, collapsed);
      var toggle = containers[i].querySelector(".dstt-nav-toggle");
      if (toggle) {
        toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
      }
    }
  }

  function enhance(container) {
    if (container.getAttribute("data-dstt-nav-enhanced")) {
      return;
    }
    var caption = container.querySelector("caption");
    if (!caption) {
      return;
    }
    container.setAttribute("data-dstt-nav-enhanced", "1");

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "dstt-nav-toggle";
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", caption.textContent.trim());
    toggle.addEventListener("click", function (event) {
      event.preventDefault();
      var collapsed = !container.classList.contains(COLLAPSED_CLASS);
      writeState(collapsed);
      apply(collapsed);
    });
    caption.appendChild(toggle);
  }

  function run() {
    var containers = document.querySelectorAll(APP_SELECTOR);
    for (var i = 0; i < containers.length; i++) {
      enhance(containers[i]);
    }
    apply(readState());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
