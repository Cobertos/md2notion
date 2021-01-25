<p align="center">
    <a href="https://github.com/Cobertos/md2notion/actions" target="_blank"><img alt="build status" src="https://github.com/Cobertos/md2notion/workflows/Package%20Tests/badge.svg"></a>
    <a href="https://pypi.org/project/md2notion/" target="_blank"><img alt="pypi python versions" src="https://img.shields.io/pypi/pyversions/md2notion.svg"></a>
    <a href="https://twitter.com/cobertos" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/twitter-%40cobertos-0084b4.svg"></a>
    <a href="https://cobertos.com" target="_blank"><img alt="twitter" src="https://img.shields.io/badge/website-cobertos.com-888888.svg"></a>
</p>

# Notion.so Markdown Importer

An importer for Markdown files to [Notion.so](https://notion.so) using [`notion-py`](https://github.com/jamalex/notion-py)

It provides these features over Notion.so's Markdown importer:

* Picking a Notion.so page to upload to (instead of them all uploading to the root)
* Code fences keep their original language (or as close as we can match it)
* Code fences are formatted properly
* Inline HTML is preserved
* (Optionally) Upload images that are memtioned in the HTML `<img>` tags.
* Markdown frontmatter is preserved
* Local image references will be uploaded from relative URLs
* Image alts are loaded as captions instead of as `TextBlock`s
* Handles nested lists properly
* Among other improvements...

Supports Python 3.6+

## Usage from CLI

* `pip install md2notion`
* Then run like `python -m md2notion [token_v2] [page-url] [...markdown_path_glob_or_url]`
* The markdown at the given path will be added as a new child to the Notion.so note at `page-url`

There are also some configuration options:

* `--clear-previous`: If a child of the note at `page-url` has the same name as what you're uploading, it will first be removed.
* `--append`: Instead of making a new child, it will append the markdown contents to the note at `page-url`
* `--html-img`: Upload images that are memtioned in the HTML `<img>` tags.

## Usage from script

* `pip install md2notion`
* In your Python file:
```python
from notion.client import NotionClient
from notion.block import PageBlock
from md2notion.upload import upload

# Follow the instructions at https://github.com/jamalex/notion-py#quickstart to setup Notion.py
client = NotionClient(token_v2="<token_v2>")
page = client.get_block("https://www.notion.so/myorg/Test-c0d20a71c0944985ae96e661ccc99821")

with open("TestMarkdown.md", "r", encoding="utf-8") as mdFile:
    newPage = page.children.add_new(PageBlock, title="TestMarkdown Upload")
    upload(mdFile, newPage) #Appends the converted contents of TestMarkdown.md to newPage
```

If you need to process `notion-py` block descriptors after parsing from Markdown but before uploading, consider using `convert` and `uploadBlock` separately. Take a look at [`upload.py#upload()`](https://github.com/Cobertos/md2notion/blob/master/md2notion/upload.py) for more.

```python
from md2notion.upload import convert, uploadBlock

rendered = convert(mdFile)

# Process the rendered array of `notion-py` block descriptors here
# (just dicts with some properties to pass to `notion-py`)

# Upload all the blocks
for blockDescriptor in rendered:
    uploadBlock(blockDescriptor, page, mdFile.name)
```

If you need to parse Markdown differently from the default, consider subclassing [`NotionPyRenderer`](https://github.com/Cobertos/md2notion/blob/master/md2notion/NotionPyRenderer.py) (a [`BaseRenderer` for `mistletoe`](https://github.com/miyuchina/mistletoe)). You can then pass it to `upload(..., notionPyRendererCls=NotionPyRenderer)` as a parameter.

## Example, Custom Hexo Importer

Here's an example that imports a Hexo blog (slghtly hacky).

```python
import io
import os.path
import glob
from pathlib import Path
from notion.block import PageBlock
from notion.client import NotionClient
from md2notion.upload import upload

client = NotionClient(token_v2="<token_v2>")
page = client.get_block("https://www.notion.so/myorg/Test-c0d20a71c0944985ae96e661ccc99821")

for fp in glob.glob("../source/_posts/*.md", recursive=True):
    with open(fp, "r", encoding="utf-8") as mdFile:
        #Preprocess the Markdown frontmatter into yaml code fences
        mdStr = mdFile.read()
        mdChunks = mdStr.split("---")
        mdStr = \
f"""```yaml
{mdChunks[1]}
`` `

{'---'.join(mdChunks[2:])}
"""
        mdFile = io.StringIO(mdStr)
        mdFile.__dict__["name"] = fp #Set this so we can resolve images later

        pageName = os.path.basename(fp)[:40]
        newPage = page.children.add_new(PageBlock, title=pageName)
        print(f"Uploading {fp} to Notion.so at page {pageName}")
        #Get the image relative to the markdown file in the flavor that Hexo
        #stores its images (in a folder with the same name as the md file)
        def convertImagePath(imagePath, mdFilePath):
            return Path(mdFilePath).parent / Path(mdFilePath).stem / Path(imagePath)
        upload(mdFile, newPage, imagePathFunc=convertImagePath)
```

## Contributing
See [CONTRIBUTING.md](https://github.com/Cobertos/md2notion/blob/master/CONTRIBUTING.md)
