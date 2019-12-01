<p align="center">
    <a href="https://twitter.com/cobertos" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/twitter-%40cobertos-0084b4.svg"></a>
    <a href="https://cobertos.com" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/website-cobertos.com-888888.svg"></a>
</p>

# Markdown to Notion-py

A renderer and uploader for Markdown files to [Notion.so](https://notion.so) using [`notion-py`](https://github.com/jamalex/notion-py)

## Why use this package?

As of writing, Notion's Markdown importer has some problems:

* Code fences don't seem to retain their original language or format properly
* Inline HTML is removed, including iframes
* Markdown frontmatter is removed
* Local image references show up as blank images
* Image alts are loaded as `TextBlock`s instead of captions
* Among others...

This package aims to make bulk import much easier by solving the problems above. If you dislike the way this package implements a specific Markdown to Notion conversion or you need extra functionality (like uploading your images to Cloud hosting), you can always subclass [`NotionPyRenderer`](https://github.com/Cobertos/md2notion/md2notion/NotionPyRenderer) (a [`BaseRenderer` for `mistletoe`](https://github.com/miyuchina/mistletoe)) and change it or hook its behavior.

## Usage with Python 3.6+

* `pip install md2notion`

* In your Python file:
```python
from notion.client import NotionClient
from md2notion.convert import convert

# Follow the instructions at https://github.com/jamalex/notion-py#quickstart to setup Notion.py
client = NotionClient(token_v2="<token_v2>")
page = client.get_block("https://www.notion.so/myorg/Test-c0d20a71c0944985ae96e661ccc99821")

with open("TestMarkdown.md", "r") as f:
    convert(f.read(), page)
```

## Contributing
See [CONTRIBUTING.md](https://github.com/Cobertos/md2notion/CONTRIBUTING.md)
