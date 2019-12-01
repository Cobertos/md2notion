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

This package aims to make bulk import much easier by solving the problems above. If you dislike the way this package implements a specific Markdown to Notion conversion or you need extra functionality (like uploading your images to Cloud hosting), you can always subclass [`NotionPyRenderer`](./md2notion/NotionPyRenderer) (a [`BaseRenderer` for `mistletoe`](https://github.com/miyuchina/mistletoe)) and change it or hook its behavior.

## Usage with Python 3.6+

* `pip install md2notion`

* In your Python file:
```python
from unitypackage_extractor.extractor import extractPackage

extractPackage("path/to/your/package.unitypackage", outputPath="optional/output/path")
```

## Contributing
#### Building (requires pyenv)
* `pyenv global 3.6.8-amd64`
 * Originally wasn't able to get this to run on Python 3.7 when it was new, but 3.6 is guarenteed to build the `.exe`
* `pyenv exec python -m venv venv64`
* `venv64\scripts\activate.bat` or `venv64/scripts/activate` for Linux
* `pip install -r requirements-dev.txt` (Installs `pyinstaller` and `pytest`)
* `python build_exe.py`
* `venv64\scripts\deactivate.bat` (or you'll use the wrong python when you make another `venv`)
* Do the same with `pyenv and 3.6.8` and make a folder called `venv32` instead

#### Testing
* `python -m venv venv`
* `venv\scripts\activate.bat` or `venv/scripts/activate` for Linux
* `pip install -r requirements-dev.txt` (Installs `pyinstaller` and `pytest`)
* `pytest -v -s` in the root directory

#### Releasing
Refer to [the python docs on packaging for clarification](https://packaging.python.org/tutorials/packaging-projects/).
Make sure you've updated `setup.py`, and have installed `twine`, `setuptools`, and `wheel`
`python3 setup.py sdist bdist_wheel` - Create a source distribution and a binary wheel distribution into `dist/`
`twine upload dist/unitypackage_extractor-x.x.x*` - Upload all `dist/` files to PyPI of a given version
Make sure to tag the commit you released
Make sure to update the README link tag too!