export default [
  {
    files: ["**/*.js", "**/*.cjs", "**/*.mjs"],
    ignores: ["node_modules/**"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true }
      }
    },
    rules: {}
  }
];
