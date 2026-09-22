module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended", "plugin:react-hooks/recommended"],
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint", "react-hooks"],
  ignorePatterns: ["dist", "playwright-report", "test-results"],
  rules: { "@typescript-eslint/no-explicit-any": "off" },
};
