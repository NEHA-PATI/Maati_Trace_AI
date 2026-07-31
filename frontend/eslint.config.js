import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default [
  {
    ignores: [
      "dist/**",
      "coverage/**",
      "node_modules/**",
      "frontend_auth_phase3_backup_*/**",
    ],
  },

  js.configs.recommended,

  {
    files: ["**/*.{js,jsx}"],

    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",

      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },

      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.node,
      },
    },

    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },

    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",

      "react-refresh/only-export-components": [
        "warn",
        {
          allowConstantExport: true,
        },
      ],

      "no-unused-vars": [
        "error",
        {
          varsIgnorePattern: "^[A-Z_]",
          argsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],

      "no-undef": "error",
      "no-unreachable": "error",
      "no-constant-condition": [
        "error",
        {
          checkLoops: false,
        },
      ],
    },
  },

  {
    files: [
      "**/*.test.{js,jsx}",
      "**/*.spec.{js,jsx}",
      "src/test/**/*.{js,jsx}",
      "tests/**/*.{js,jsx}",
    ],

    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,

        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        beforeAll: "readonly",
        beforeEach: "readonly",
        afterAll: "readonly",
        afterEach: "readonly",
        vi: "readonly",
      },
    },
  },
];