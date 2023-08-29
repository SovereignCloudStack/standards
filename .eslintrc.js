module.exports = {
  env: {
    browser: true,
    es2021: true
  },
  extends: ['plugin:react/recommended', 'standard-with-typescript'],
  overrides: [
    {
      files: 'docs/*.md',
      parser: 'eslint-plugin-markdownlint/parser',
      extends: 'plugin:markdownlint/recommended'
    }
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  plugins: ['react']
}
