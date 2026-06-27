(function () {
  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
      return;
    }
    callback();
  }

  // Localized UI strings injected by the change form (json_script:"dstt-ui-labels").
  // Populated in ready(); uiLabel falls back to English when a key is missing.
  var UI_LABELS = {};

  function uiLabel(key, fallback) {
    var value = UI_LABELS[key];
    return value ? value : fallback;
  }

  // Map admin form field ids to the component CSS variables / data attributes so
  // the live preview can be updated on the fly, reusing the production component
  // stylesheet instead of reimplementing it. Mirrors build_component_stylesheet
  // and the scroll_to_top.html data attributes.
  var COLOR_VAR_MAP = {
    id_icon_color: "--dstt-icon-color",
    id_dark_icon_color: "--dstt-icon-color-dark",
    id_foreground_color: "--dstt-color-fg",
    id_background_color: "--dstt-color-bg",
    id_border_color: "--dstt-color-border",
    id_hover_foreground_color: "--dstt-color-fg-hover",
    id_hover_background_color: "--dstt-color-bg-hover",
    id_hover_border_color: "--dstt-color-border-hover",
    id_active_foreground_color: "--dstt-color-fg-active",
    id_active_background_color: "--dstt-color-bg-active",
    id_active_border_color: "--dstt-color-border-active",
    id_focus_ring_color: "--dstt-focus-ring",
    id_dark_foreground_color: "--dstt-color-fg-dark",
    id_dark_background_color: "--dstt-color-bg-dark",
    id_dark_border_color: "--dstt-color-border-dark",
    id_dark_hover_foreground_color: "--dstt-color-fg-hover-dark",
    id_dark_hover_background_color: "--dstt-color-bg-hover-dark",
    id_dark_hover_border_color: "--dstt-color-border-hover-dark",
    id_dark_active_foreground_color: "--dstt-color-fg-active-dark",
    id_dark_active_background_color: "--dstt-color-bg-active-dark",
    id_dark_active_border_color: "--dstt-color-border-active-dark",
    id_dark_focus_ring_color: "--dstt-focus-ring-dark",
    id_gradient_start_color: "--dstt-gradient-start",
    id_gradient_end_color: "--dstt-gradient-end",
  };

  var PX_VAR_MAP = {
    id_border_width: "--dstt-border-width",
    id_focus_ring_width: "--dstt-focus-ring-width",
    id_focus_ring_offset: "--dstt-focus-ring-offset",
    id_backdrop_blur: "--dstt-backdrop-blur",
    id_size_desktop: "--dstt-size",
    id_icon_size_desktop: "--dstt-icon-size",
  };

  var ATTR_MAP = {
    id_shape: "data-dstt-shape",
    id_fill_variant: "data-dstt-fill",
    id_shadow_preset: "data-dstt-shadow",
    id_corner: "data-dstt-corner",
    id_template_variant: "data-dstt-template",
    id_theme_mode: "data-dstt-theme-mode",
    id_icon_style: "data-dstt-icon-style",
    id_icon_source: "data-dstt-icon-source",
    id_icon_name: "data-dstt-icon",
  };

  function isHexColor(value) {
    return /^#[0-9a-fA-F]{6}$/.test(value);
  }

  function fieldValue(id) {
    var el = document.getElementById(id);
    return el ? el.value || "" : "";
  }

  function fieldChecked(id) {
    var el = document.getElementById(id);
    return el ? !!el.checked : false;
  }

  function initializeLivePreview() {
    var root = document.querySelector("[data-dstt-live-preview]");
    if (!root) {
      return null;
    }
    var panel = root.querySelector("[data-dstt-live-panel]");
    var wrap = root.querySelector(".dstt-control-wrap");
    if (!panel || !wrap) {
      return null;
    }

    var rafId = 0;

    function setNumberVar(id, varName, suffix) {
      var raw = fieldValue(id).trim();
      if (raw === "") {
        return;
      }
      var parsed = parseFloat(raw);
      if (!isNaN(parsed)) {
        wrap.style.setProperty(varName, parsed + suffix);
      }
    }

    function updateLabel() {
      var link = wrap.querySelector(".dstt-control");
      if (!link) {
        return;
      }
      var isLabel = fieldValue("id_template_variant") === "icon-label";
      var labelEl = link.querySelector(".dstt-control__label");
      if (isLabel) {
        if (!labelEl) {
          labelEl = document.createElement("span");
          labelEl.className = "dstt-control__label";
          link.appendChild(labelEl);
        }
        labelEl.textContent = fieldValue("id_label_text");
      } else if (labelEl) {
        labelEl.parentNode.removeChild(labelEl);
      }
    }

    function updateDismiss() {
      var checkbox = document.getElementById("id_allow_user_dismissal");
      var enabled = checkbox ? !!checkbox.checked : false;
      var existing = wrap.querySelector("[data-dstt-dismiss-control]");
      if (enabled && !existing) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "dstt-control__dismiss";
        btn.setAttribute("data-dstt-dismiss-control", "");
        btn.setAttribute("aria-label", "×");
        var span = document.createElement("span");
        span.setAttribute("aria-hidden", "true");
        span.textContent = "×";
        btn.appendChild(span);
        wrap.appendChild(btn);
      } else if (!enabled && existing) {
        existing.parentNode.removeChild(existing);
      }
    }

    function apply() {
      rafId = 0;

      Object.keys(COLOR_VAR_MAP).forEach(function (id) {
        var value = fieldValue(id).trim();
        if (isHexColor(value)) {
          wrap.style.setProperty(COLOR_VAR_MAP[id], value);
        } else {
          // Empty optional colors (e.g. icon color override) revert to inherit.
          wrap.style.removeProperty(COLOR_VAR_MAP[id]);
        }
      });

      Object.keys(PX_VAR_MAP).forEach(function (id) {
        setNumberVar(id, PX_VAR_MAP[id], "px");
      });

      var sizeMobile = fieldChecked("id_size_mobile_inherit")
        ? fieldValue("id_size_desktop")
        : fieldValue("id_size_mobile");
      if (sizeMobile.trim() !== "" && !isNaN(parseFloat(sizeMobile))) {
        wrap.style.setProperty("--dstt-size-mobile", parseFloat(sizeMobile) + "px");
      }

      var iconMobile = fieldChecked("id_icon_size_mobile_inherit")
        ? fieldValue("id_icon_size_desktop")
        : fieldValue("id_icon_size_mobile");
      if (iconMobile.trim() !== "" && !isNaN(parseFloat(iconMobile))) {
        wrap.style.setProperty(
          "--dstt-icon-size-mobile",
          parseFloat(iconMobile) + "px"
        );
      }

      var opacity = fieldValue("id_opacity").trim();
      if (opacity !== "" && !isNaN(parseFloat(opacity))) {
        wrap.style.setProperty("--dstt-opacity", String(parseFloat(opacity)));
      }

      setNumberVar("id_gradient_angle", "--dstt-gradient-angle", "deg");

      Object.keys(ATTR_MAP).forEach(function (id) {
        var el = document.getElementById(id);
        if (el && el.value) {
          wrap.setAttribute(ATTR_MAP[id], el.value);
        }
      });

      updateLabel();
      updateDismiss();

      var link = wrap.querySelector(".dstt-control");
      var aria = fieldValue("id_aria_label").trim();
      if (link && aria) {
        link.setAttribute("aria-label", aria);
      }

      syncFloat();
    }

    // Floating demo button overlaid on the admin page so the designer sees the
    // real placement. Purely visual (pointer-events disabled, not runtime-init).
    var floatWrap = null;
    var floatDismissed = false;
    var demoRestoreBtn = null;
    var FLOAT_ATTRS = [
      "data-dstt-shape",
      "data-dstt-fill",
      "data-dstt-shadow",
      "data-dstt-template",
      "data-dstt-theme-mode",
      "data-dstt-icon-style",
    ];

    function ensureDemoRestore() {
      if (demoRestoreBtn || !document.body) {
        return;
      }
      demoRestoreBtn = document.createElement("button");
      demoRestoreBtn.type = "button";
      demoRestoreBtn.className = "dstt-admin-demo-restore";
      demoRestoreBtn.hidden = true;
      demoRestoreBtn.textContent = uiLabel("show_demo", "Show demo button again");
      demoRestoreBtn.addEventListener("click", showDemoFloat);
      document.body.appendChild(demoRestoreBtn);
    }

    function showDemoFloat() {
      floatDismissed = false;
      if (floatWrap) {
        floatWrap.hidden = false;
      }
      if (demoRestoreBtn) {
        demoRestoreBtn.hidden = true;
      }
    }

    function dismissDemoFloat() {
      floatDismissed = true;
      if (floatWrap) {
        floatWrap.hidden = true;
      }
      ensureDemoRestore();
      if (demoRestoreBtn) {
        demoRestoreBtn.hidden = false;
      }
    }

    function demoCorner() {
      var selected = fieldValue("id_admin_demo_corner") || "auto";
      if (selected !== "auto") {
        return selected;
      }
      var adminWrap = document.querySelector(
        '.dstt-control-wrap[data-dstt-scope="admin"]'
      );
      var adminCorner = adminWrap
        ? adminWrap.getAttribute("data-dstt-corner") || "bottom-right"
        : "bottom-right";
      return adminCorner.indexOf("bottom") === 0
        ? adminCorner.replace("bottom", "top")
        : adminCorner.replace("top", "bottom");
    }

    function syncFloat() {
      if (!document.body) {
        return;
      }
      if (!floatWrap) {
        floatWrap = wrap.cloneNode(true);
        floatWrap.classList.add("dstt-admin-demo-float");
        floatWrap.classList.remove("dstt-is-hidden");
        floatWrap.setAttribute("data-dstt-admin-demo", "true");
        floatWrap.removeAttribute("data-dstt-contract-version");
        floatWrap.removeAttribute("hidden");
        floatWrap.addEventListener("click", function (event) {
          event.preventDefault();
        });
        document.body.appendChild(floatWrap);
      }
      floatWrap.style.cssText = wrap.style.cssText;
      FLOAT_ATTRS.forEach(function (attr) {
        var value = wrap.getAttribute(attr);
        if (value !== null) {
          floatWrap.setAttribute(attr, value);
        }
      });
      floatWrap.setAttribute("data-dstt-corner", demoCorner());
      var srcIcon = wrap.querySelector(".dstt-control__icon");
      var dstIcon = floatWrap.querySelector(".dstt-control__icon");
      if (srcIcon && dstIcon) {
        dstIcon.textContent = "";
        Array.prototype.forEach.call(srcIcon.childNodes, function (node) {
          dstIcon.appendChild(node.cloneNode(true));
        });
      }
      var srcLink = wrap.querySelector(".dstt-control");
      var dstLink = floatWrap.querySelector(".dstt-control");
      if (srcLink && dstLink) {
        var srcLabel = srcLink.querySelector(".dstt-control__label");
        var dstLabel = dstLink.querySelector(".dstt-control__label");
        if (srcLabel && !dstLabel) {
          dstLink.appendChild(srcLabel.cloneNode(true));
        } else if (!srcLabel && dstLabel) {
          dstLabel.parentNode.removeChild(dstLabel);
        } else if (srcLabel && dstLabel) {
          dstLabel.textContent = srcLabel.textContent;
        }
      }
      // Mirror the dismiss (×) button onto the float and make it actually hide
      // the demo overlay, revealing the "show demo again" control.
      var srcDismiss = wrap.querySelector("[data-dstt-dismiss-control]");
      var dstDismiss = floatWrap.querySelector("[data-dstt-dismiss-control]");
      if (srcDismiss && !dstDismiss) {
        dstDismiss = srcDismiss.cloneNode(true);
        dstDismiss.addEventListener("click", function (event) {
          event.preventDefault();
          event.stopPropagation();
          dismissDemoFloat();
        });
        floatWrap.appendChild(dstDismiss);
      } else if (!srcDismiss && dstDismiss) {
        dstDismiss.parentNode.removeChild(dstDismiss);
        // No dismiss affordance remains, so never leave the demo hidden.
        showDemoFloat();
      }
      floatWrap.hidden = floatDismissed;
    }

    function schedule() {
      if (rafId) {
        return;
      }
      rafId = window.requestAnimationFrame(apply);
    }

    function setIconFromCard(card) {
      var sourceSvg = card.querySelector(".dstt-icon-picker__thumb svg");
      var iconHost = wrap.querySelector(".dstt-control__icon");
      if (!sourceSvg || !iconHost) {
        return;
      }
      var clone = sourceSvg.cloneNode(true);
      clone.classList.remove("dstt-icon-picker__svg");
      clone.classList.add("dstt-icon-svg");
      iconHost.textContent = "";
      iconHost.appendChild(clone);
    }

    return {
      panel: panel,
      schedule: schedule,
      setIconFromCard: setIconFromCard,
    };
  }

  function initializePreviewToolbar(live) {
    if (!live) {
      return;
    }
    var groups = document.querySelectorAll(
      "[data-dstt-live-preview] [data-dstt-preview-control]"
    );
    groups.forEach(function (group) {
      var control = group.getAttribute("data-dstt-preview-control");
      var attr = "data-dstt-preview-" + control;
      group.addEventListener("click", function (event) {
        var button = event.target.closest("[data-dstt-preview-value]");
        if (!button || !group.contains(button)) {
          return;
        }
        var value = button.getAttribute("data-dstt-preview-value") || "";
        live.panel.setAttribute(attr, value);
        group
          .querySelectorAll("[data-dstt-preview-value]")
          .forEach(function (other) {
            other.classList.toggle("is-active", other === button);
          });
      });
    });
  }

  function initializePicker(root, live) {
    var grid = root.querySelector("[data-dstt-picker-grid]");
    var search = root.querySelector("[data-dstt-picker-search]");
    var empty = root.querySelector("[data-dstt-picker-empty]");
    var iconSource = document.getElementById("id_icon_source");
    var iconName = document.getElementById("id_icon_name");
    var iconStyle = document.getElementById("id_icon_style");
    var uploadedIcon = document.getElementById("id_uploaded_icon");

    if (
      !grid ||
      !search ||
      !empty ||
      !iconSource ||
      !iconName ||
      !iconStyle ||
      !uploadedIcon
    ) {
      return;
    }

    function selectedState() {
      return {
        source: iconSource.value || "builtin",
        name: iconName.value || "",
        style: iconStyle.value || "outline",
        uploaded: uploadedIcon.value || "",
      };
    }

    function syncSelectionClasses() {
      var state = selectedState();
      var cards = grid.querySelectorAll("[data-dstt-picker-card]");
      cards.forEach(function (card) {
        var source = card.getAttribute("data-dstt-picker-source");
        var isSelected = false;

        if (source === "builtin" || source === "developer") {
          isSelected =
            state.source === source &&
            card.getAttribute("data-dstt-picker-name") === state.name &&
            card.getAttribute("data-dstt-picker-style") === state.style;
        } else if (source === "uploaded") {
          isSelected =
            state.source === "uploaded" &&
            card.getAttribute("data-dstt-picker-value") === state.uploaded;
        }

        card.classList.toggle("dstt-icon-picker__card--selected", isSelected);
      });
    }

    function applyFilters() {
      var state = selectedState();
      var query = (search.value || "").trim().toLowerCase();
      var visibleCount = 0;
      var cards = grid.querySelectorAll("[data-dstt-picker-card]");

      cards.forEach(function (card) {
        var source = card.getAttribute("data-dstt-picker-source") || "";
        var searchText = (card.textContent || "").toLowerCase();
        var style = card.getAttribute("data-dstt-picker-style") || "";
        var matchesQuery = query === "" || searchText.indexOf(query) !== -1;
        var matchesSource = source === state.source;
        var matchesStyle =
          (source !== "builtin" && source !== "developer") || style === state.style;
        var isVisible = matchesQuery && matchesSource && matchesStyle;

        card.hidden = !isVisible;
        if (isVisible) {
          visibleCount += 1;
        }
      });

      empty.hidden = visibleCount !== 0;
      syncSelectionClasses();
    }

    grid.addEventListener("click", function (event) {
      var card = event.target.closest("[data-dstt-picker-card]");
      if (!card) {
        return;
      }

      var source = card.getAttribute("data-dstt-picker-source");
      iconSource.value = source || "builtin";

      if (source === "builtin" || source === "developer") {
        iconName.value = card.getAttribute("data-dstt-picker-name") || iconName.value;
        iconStyle.value =
          card.getAttribute("data-dstt-picker-style") || iconStyle.value;
        uploadedIcon.value = "";
      } else if (source === "uploaded") {
        uploadedIcon.value = card.getAttribute("data-dstt-picker-value") || "";
      }

      applyFilters();
      if (live) {
        live.setIconFromCard(card);
        live.schedule();
      }
    });

    [iconSource, iconName, iconStyle, uploadedIcon].forEach(function (field) {
      field.addEventListener("change", applyFilters);
    });
    search.addEventListener("input", applyFilters);

    applyFilters();
  }

  function initializeColorWidgets(live) {
    document.querySelectorAll("[data-dstt-color-field]").forEach(function (input) {
      if (input.dataset.dsttColorEnhanced === "true") {
        return;
      }

      // Optional overrides (icon color / dark icon color) may be empty, meaning
      // "inherit". Those get a clear button and an explicit empty swatch state so
      // a reset is visibly reflected instead of leaving a stale color.
      var clearable = !input.required;

      var wrapper = document.createElement("div");
      wrapper.className = "dstt-color-widget";

      var swatch = document.createElement("span");
      swatch.className = "dstt-color-widget__swatch";

      var picker = document.createElement("input");
      picker.type = "color";
      picker.className = "dstt-color-widget__picker";
      picker.setAttribute("aria-label", input.getAttribute("aria-label") || input.name);

      var none = document.createElement("span");
      none.className = "dstt-color-widget__none";
      none.setAttribute("aria-hidden", "true");

      swatch.appendChild(picker);
      swatch.appendChild(none);

      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(swatch);
      wrapper.appendChild(input);

      var clearBtn = null;
      if (clearable) {
        clearBtn = document.createElement("button");
        clearBtn.type = "button";
        clearBtn.className = "dstt-color-widget__clear";
        clearBtn.setAttribute(
          "aria-label",
          uiLabel("clear_color", "Clear color override")
        );
        var clearGlyph = document.createElement("span");
        clearGlyph.setAttribute("aria-hidden", "true");
        clearGlyph.textContent = "×";
        clearBtn.appendChild(clearGlyph);
        wrapper.appendChild(clearBtn);
      }

      function updateFromText() {
        var current = (input.value || "").trim();
        if (/^#[0-9a-fA-F]{6}$/.test(current)) {
          picker.value = current;
          wrapper.classList.remove("dstt-color-widget--empty");
        } else {
          // Empty value: reflect "no override" on the swatch. A non-empty but
          // still-incomplete value (mid-typing) leaves the swatch untouched.
          wrapper.classList.toggle("dstt-color-widget--empty", current === "");
        }
      }

      picker.addEventListener("input", function () {
        input.value = picker.value;
        wrapper.classList.remove("dstt-color-widget--empty");
        if (live) {
          live.schedule();
        }
      });
      input.addEventListener("input", function () {
        updateFromText();
        if (live) {
          live.schedule();
        }
      });
      input.addEventListener("change", function () {
        updateFromText();
        if (live) {
          live.schedule();
        }
      });
      if (clearBtn) {
        clearBtn.addEventListener("click", function () {
          input.value = "";
          updateFromText();
          input.dispatchEvent(new Event("input", { bubbles: true }));
          input.dispatchEvent(new Event("change", { bubbles: true }));
          if (live) {
            live.schedule();
          }
        });
      }

      input.dataset.dsttColorEnhanced = "true";
      updateFromText();
    });
  }

  // Insert "Light theme" / "Dark theme" column headers into the two-column
  // Colors grid (layout in admin-icon-picker.css). Degrades gracefully: without
  // this the grid still renders light on the left and dark on the right.
  function initializeColorsGrid() {
    var grid = document.querySelector("fieldset.dstt-colors-grid");
    if (!grid) {
      return;
    }
    var heading = grid.querySelector("h2");
    var light = document.createElement("p");
    light.className = "dstt-colors-grid__col-label";
    light.textContent = uiLabel("colors_light", "Light theme");
    var dark = document.createElement("p");
    dark.className = "dstt-colors-grid__col-label";
    dark.textContent = uiLabel("colors_dark", "Dark theme");
    var anchor = heading ? heading.nextSibling : grid.firstChild;
    grid.insertBefore(dark, anchor);
    grid.insertBefore(light, dark);
  }

  // Warn (and clamp on blur) when an icon size is typed larger than its button
  // size, for both the desktop and mobile pairs.
  function initializeSizeGuards(live) {
    var pairs = [
      { icon: "id_icon_size_desktop", button: "id_size_desktop" },
      {
        icon: "id_icon_size_mobile",
        button: "id_size_mobile",
        iconInherit: "id_icon_size_mobile_inherit",
        buttonInherit: "id_size_mobile_inherit",
      },
    ];

    pairs.forEach(function (pair) {
      var iconEl = document.getElementById(pair.icon);
      var buttonEl = document.getElementById(pair.button);
      if (!iconEl || !buttonEl) {
        return;
      }

      var warning = document.createElement("p");
      warning.className = "dstt-size-warning";
      warning.hidden = true;
      var row = iconEl.closest(".form-row") || iconEl.parentNode;
      if (row && row.parentNode) {
        row.parentNode.insertBefore(warning, row.nextSibling);
      }

      function effectiveButtonSize() {
        if (pair.buttonInherit) {
          var bInherit = document.getElementById(pair.buttonInherit);
          if (bInherit && bInherit.checked) {
            var desktop = document.getElementById("id_size_desktop");
            return desktop ? parseFloat(desktop.value) : NaN;
          }
        }
        return parseFloat(buttonEl.value);
      }

      function iconInherited() {
        if (!pair.iconInherit) {
          return false;
        }
        var el = document.getElementById(pair.iconInherit);
        return !!(el && el.checked);
      }

      function validate() {
        if (iconInherited()) {
          warning.hidden = true;
          return;
        }
        var iconVal = parseFloat(iconEl.value);
        var buttonVal = effectiveButtonSize();
        if (isNaN(iconVal) || isNaN(buttonVal) || iconVal <= buttonVal) {
          warning.hidden = true;
          return;
        }
        warning.textContent = uiLabel(
          "icon_size_exceeds",
          "Icon size {icon} px is larger than the button size {button} px; it may overflow the button."
        )
          .replace("{icon}", String(iconVal))
          .replace("{button}", String(buttonVal));
        warning.hidden = false;
      }

      function clampOnBlur() {
        if (iconInherited()) {
          return;
        }
        var iconVal = parseFloat(iconEl.value);
        var buttonVal = effectiveButtonSize();
        if (isNaN(iconVal) || isNaN(buttonVal) || iconVal <= buttonVal) {
          return;
        }
        iconEl.value = String(buttonVal);
        iconEl.dispatchEvent(new Event("input", { bubbles: true }));
        if (live) {
          live.schedule();
        }
        warning.textContent = uiLabel(
          "icon_size_clamped",
          "Icon size reduced to the button size ({button} px)."
        ).replace("{button}", String(buttonVal));
        warning.hidden = false;
      }

      iconEl.addEventListener("input", validate);
      iconEl.addEventListener("change", clampOnBlur);
      buttonEl.addEventListener("input", validate);
      buttonEl.addEventListener("change", validate);
      var desktopButton = document.getElementById("id_size_desktop");
      if (desktopButton && desktopButton !== buttonEl) {
        desktopButton.addEventListener("input", validate);
      }
      [pair.iconInherit, pair.buttonInherit].forEach(function (id) {
        if (!id) {
          return;
        }
        var el = document.getElementById(id);
        if (el) {
          el.addEventListener("change", validate);
        }
      });

      validate();
    });
  }

  function initializeFieldListeners(live) {
    if (!live) {
      return;
    }
    var ids = {};
    Object.keys(COLOR_VAR_MAP).forEach(function (id) {
      ids[id] = true;
    });
    Object.keys(PX_VAR_MAP).forEach(function (id) {
      ids[id] = true;
    });
    Object.keys(ATTR_MAP).forEach(function (id) {
      ids[id] = true;
    });
    [
      "id_opacity",
      "id_gradient_angle",
      "id_size_mobile",
      "id_size_mobile_inherit",
      "id_icon_size_mobile",
      "id_icon_size_mobile_inherit",
      "id_label_text",
      "id_aria_label",
      "id_uploaded_icon",
      "id_admin_demo_corner",
      "id_allow_user_dismissal",
    ].forEach(function (id) {
      ids[id] = true;
    });

    Object.keys(ids).forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) {
        return;
      }
      el.addEventListener("input", live.schedule);
      el.addEventListener("change", live.schedule);
    });
  }

  function setFieldValue(el, value) {
    if (el.type === "checkbox") {
      el.checked = !!value;
    } else {
      el.value = value === null || value === undefined ? "" : String(value);
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // Per-section "reset to defaults" and "restore last saved (DB)" controls.
  function initializeSectionResets(live) {
    var defaults = {};
    var labels = { reset: "Reset to defaults", saved: "Restore last saved" };
    var defaultsEl = document.getElementById("dstt-field-defaults");
    var labelsEl = document.getElementById("dstt-reset-labels");
    if (defaultsEl) {
      try {
        defaults = JSON.parse(defaultsEl.textContent);
      } catch (error) {
        defaults = {};
      }
    }
    if (labelsEl) {
      try {
        labels = JSON.parse(labelsEl.textContent);
      } catch (error) {
        /* keep fallback labels */
      }
    }

    document.querySelectorAll("fieldset.module").forEach(function (fs) {
      if (fs.classList.contains("dstt-live-preview-fieldset")) {
        return;
      }
      var fields = [];
      fs.querySelectorAll("input[name], select[name], textarea[name]").forEach(
        function (el) {
          if (el.type !== "hidden" && el.name.charAt(0) !== "_") {
            fields.push(el);
          }
        }
      );
      if (!fields.length) {
        return;
      }
      var saved = fields.map(function (el) {
        return el.type === "checkbox" ? el.checked : el.value;
      });

      var bar = document.createElement("span");
      bar.className = "dstt-section-reset";
      var resetBtn = document.createElement("button");
      resetBtn.type = "button";
      resetBtn.className = "dstt-section-reset__btn";
      resetBtn.textContent = labels.reset || "Reset to defaults";
      var savedBtn = document.createElement("button");
      savedBtn.type = "button";
      savedBtn.className = "dstt-section-reset__btn";
      savedBtn.textContent = labels.saved || "Restore last saved";
      bar.appendChild(resetBtn);
      bar.appendChild(savedBtn);

      var heading = fs.querySelector("h2");
      if (heading) {
        heading.appendChild(bar);
      } else {
        fs.insertBefore(bar, fs.firstChild);
      }

      resetBtn.addEventListener("click", function () {
        fields.forEach(function (el) {
          if (Object.prototype.hasOwnProperty.call(defaults, el.name)) {
            setFieldValue(el, defaults[el.name]);
          }
        });
        if (live) {
          live.schedule();
        }
      });
      savedBtn.addEventListener("click", function () {
        fields.forEach(function (el, index) {
          setFieldValue(el, saved[index]);
        });
        if (live) {
          live.schedule();
        }
      });
    });
  }

  ready(function () {
    var labelsEl = document.getElementById("dstt-ui-labels");
    if (labelsEl) {
      try {
        UI_LABELS = JSON.parse(labelsEl.textContent) || {};
      } catch (error) {
        UI_LABELS = {};
      }
    }
    var live = initializeLivePreview();
    document.querySelectorAll("[data-dstt-icon-picker]").forEach(function (root) {
      initializePicker(root, live);
    });
    initializeColorWidgets(live);
    initializeColorsGrid();
    initializeFieldListeners(live);
    initializePreviewToolbar(live);
    initializeSectionResets(live);
    initializeSizeGuards(live);
    if (live) {
      live.schedule();
    }
  });
})();
