<p align="center">
    <a href="https://twitter.com/cobertos" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/twitter-%40cobertos-0084b4.svg"></a>
    <a href="https://cobertos.com" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/website-cobertos.com-888888.svg"></a>
</p>

# Markdown to Notion-py

An importer for Markdown files to [Notion.so](https://notion.so) using [`notion-py`](https://github.com/jamalex/notion-py)

It provides these features over Notion's Markdown importer:

* Picking a Notion.so page to upload to (instead of them all uploading to the root)
* Code fences keep their original language (or as close as we can match it)
* Code fences are formatted properly
* Inline HTML is preserved
* Markdown frontmatter is preserved
* Local image references will be uploaded from relative URLs
* Image alts are loaded as captions instead of as `TextBlock`s
* Among other improvements...

If you dislike the way this package implements a specific Markdown to Notion conversion or you need extra functionality (like uploading your images to personal Cloud hosting or something), you can subclass [`NotionPyRenderer`](https://github.com/Cobertos/md2notion/blob/master/md2notion/NotionPyRenderer) (a [`BaseRenderer` for `mistletoe`](https://github.com/miyuchina/mistletoe)) and change it or hook its behavior.

## Limitations

* Currently does not support tables/`CollectionViewBlocks`

## Usage with Python 3.6+

* `pip install md2notion`

* From the command link you can run `python -m md2notion.upload [token_v2] [page-url] [...markdown_path_globs]`

* OR In your Python file:
```python
from notion.client import NotionClient
from md2notion.upload import upload

# Follow the instructions at https://github.com/jamalex/notion-py#quickstart to setup Notion.py
client = NotionClient(token_v2="<token_v2>")
page = client.get_block("https://www.notion.so/myorg/Test-c0d20a71c0944985ae96e661ccc99821")

newPage = notionPage.children.add_new(PageBlock, title="TestMarkdown Upload")
upload("TestMarkdown.md", newPage) #Appends the contents of TestMarkdown.md to newPage
```

## Contributing
See [CONTRIBUTING.md](https://github.com/Cobertos/md2notion/blob/master/CONTRIBUTING.md)
