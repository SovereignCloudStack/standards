# Styleguide

## Admonitions

We adopt the default Admonition colors for Note, Tip, Info, Caution, Danger by docusaurus:

[Docusaurus Admonitons](https://docusaurus.io/docs/2.0.1/markdown-features/admonitions)

:::note

Some **content** with _Markdown_ `syntax`.

:::

:::tip

Some **content** with _Markdown_ `syntax`.

:::

:::info

Some **content** with _Markdown_ `syntax`.

:::

:::caution

Some **content** with _Markdown_ `syntax`.

:::

:::danger

Some **content** with _Markdown_ `syntax`.

:::

## Blockquotes

Blockquotes should be handled with standard markdown `>`

Example Blockquote:

> The raw data format is really the only sensible format option to use with RBD. asdasdasdasd asd asd a
> Technically, you could use other QEMU-supported formats
> (such as qcow2 or vmdk), but doing so would add additional overhead, and would
> also render the volume unsafe for virtual machine live
> migration when caching (see below) is enabled.

## Codeblocks

We support markdown language features for Codeblocks.
It is mandatory to define the language to be quoted, when using codeblocks.
Syntax Highlighting is also supported by [Docusaurus via Prism](https://docusaurus.io/docs/2.0.1/markdown-features/code-blocks#supported-languages).
We are using the GitHub language themeing as default.

```python title="Python example"
def code_block():
  # Everything in this function is part of the same code block
  print (1)
  print (2)

for i in range(4):
  # Everyting in this loop is part of the same code block
  print (i)
```

```javascript title="Javascript example"
const code_block = () => {
    console.log("inside code_block");
};
```

```yaml title="YAML example"
---
doe: "a deer, a female deer"
ray: "a drop of golden sun"
pi: 3.14159
xmas: true
french-hens: 3
calling-birds:
    - huey
    - dewey
    - louie
    - fred
```

```ruby title="Ruby example"
require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html
```
