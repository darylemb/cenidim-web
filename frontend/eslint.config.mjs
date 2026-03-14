import js from "@eslint/js";
import reactPlugin from "eslint-plugin-react";
import globals from "globals";
import eslintConfigPrettier from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{js,jsx}"],
    plugins: {
      "react": reactPlugin,
      "prettier": prettierPlugin,
    },
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
        ecmaVersion: "latest",
        sourceType: "module",
      },
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
      }
    },
    settings: {
      react: { version: "19.2" }
    },
    rules: {
      ...reactPlugin.configs.recommended.rules,
      ...eslintConfigPrettier.rules,
      "react/prop-types": "off",
      "react/react-in-jsx-scope": "off",
      "prettier/prettier": "error"
    }
  }
];
