import globals from 'globals'
import vueParser from 'vue-eslint-parser'
import eslintPluginVue from 'eslint-plugin-vue'
import eslintConfigPrettier from 'eslint-config-prettier'
import prettierPlugin from 'eslint-plugin-prettier'
import tseslint from '@typescript-eslint/parser'

export default [
  {
    files: ['**/*.vue'],
    plugins: {
      vue: eslintPluginVue,
      prettier: prettierPlugin,
    },
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      ...eslintPluginVue.configs['vue3-recommended']?.rules ?? {},
      'prettier/prettier': 'off',
      'vue/no-v-html': 'off',
      'vue/require-default-event': 'off',
      'vue/require-explicit-emits': 'off',
      'vue/multi-word-component-names': 'off',
      'vue/attributes-order': 'off',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/*.ts', '**/*.tsx'],
    plugins: {
      prettier: prettierPlugin,
    },
    languageOptions: {
      parser: tseslint,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
      },
    },
    rules: {
      ...eslintConfigPrettier.rules,
      'prettier/prettier': 'error',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
  {
    files: ['**/*.js', '**/*.jsx'],
    plugins: {
      prettier: prettierPlugin,
    },
    languageOptions: {
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.jest,
        ...globals.node,
      },
    },
    rules: {
      ...eslintConfigPrettier.rules,
      'prettier/prettier': 'error',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    },
  },
  // Test files commonly import helpers (vi, async, etc.) and pass
  // typed functions as mocks whose signatures look unused to the
  // no-unused-vars rule. Relax the checks there so test files don't
  // need to be linted-to-shape.
  {
    files: [
      '**/__tests__/**',
      'src/test/**',
      'src/**/*.spec.ts',
      'src/**/*.test.ts',
    ],
    rules: {
      'no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      'no-unused-expressions': 'off',
    },
  },
]