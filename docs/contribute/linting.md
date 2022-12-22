# Rules and Linting

## Rules for Markdown

We strongly recommend to make use of [markdownlint](https://github.com/DavidAnson/markdownlint) to format all markdown files to our common ruleset.
Within your root folder of your project create the following file inheriting the rules:

```json title=".markdownlint.json"
{
    "default": true,
    "MD013": {
        "line length": 140,
        "code_block_line_length": 300
    }
}
```
