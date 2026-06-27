// Dev-only ESLint config for the django-scroll-to-top browser assets.
//
// Node/ESLint are NOT runtime or packaged dependencies; this only lints the
// vanilla ES5 static JS: the window.djstt runtime, the optional obstacle
// adapter, and the admin icon picker. The shipped runtime is intentionally
// ES5 (a contract test forbids `const`), so this config does not push ES6
// idioms (no prefer-const / no-var). Generated *.min.js files are ignored.
import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: ["**/*.min.js", "node_modules/**"],
  },
  {
    files: ["src/django_scroll_to_top/static/django_scroll_to_top/**/*.js"],
    languageOptions: {
      ecmaVersion: 2019,
      sourceType: "script",
      globals: {
        ...globals.browser,
      },
    },
    rules: {
      ...js.configs.recommended.rules,
      // Unused arguments are commonly kept for signature clarity (event
      // handlers, observer callbacks) and catch bindings document intent;
      // still flag unused variables and dead function declarations (e.g. a
      // helper that is never wired up).
      "no-unused-vars": ["error", { args: "none", caughtErrors: "none" }],
    },
  },
];
