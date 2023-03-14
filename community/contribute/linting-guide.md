# Linting Guide

In order to have a clean content repository regarding all markdown files we enforce linting on:

1. all staged files prior committing
2. all Pull Requests

## Pre Commit

Run markdownlint against staged git files with Husky git hook:

1. [lint-staged](https://github.com/okonet/lint-staged)
2. [husky](https://github.com/typicode/husky)

The rules are enforced on markdown files, for which we use:

1. [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) for markdownlint
2. [prettier](https://github.com/prettier/prettier) for code formatting

The markdownlint rules are defined in the configuration file `.markdownlint-cli2.jsonc`

Additionally we use [markdownlint-rule-search-replace](https://github.com/OnkarRuikar/markdownlint-rule-search-replace) for fixing

## Github Workflows

There are two actions running on every Pull Request on the `main` branch.

1. `link-validator.yml`is checking every link in markdown files.
2. `pr-markdownlint.yml`is checking all markdown files regarding to the rules defined within `.markdownlint-cli2.jsonc`
