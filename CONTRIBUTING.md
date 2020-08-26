# Contributing

Here's how to run all the development stuff.

## Setup Development Environment
* `pyenv global 3.6.8-amd64`
* `pipenv install --dev`

## Testing
* `pytest -v` in the root directory
* It's best to run a test against Notion's API as well with `pipenv run python -m md2notion.upload [token] https://www.notion.so/TestPage-8937635afd984d2f953a1750dfce4d26 tests/COMPREHENSIVE_TEST.md` with your token and page.
* To test coverage run `pipenv run coverage run -m pytest -v`
* Then run `pipenv run coverage report` or `pipenv run coverage html` and browser the coverage (TODO: Figure out a way to make a badge for this??)

## Releasing
Refer to [the python docs on packaging for clarification](https://packaging.python.org/tutorials/packaging-projects/).
* Make sure you've updated `setup.py`
* `python setup.py sdist bdist_wheel` - Create a source distribution and a binary wheel distribution into `dist/`
* `twine upload dist/md2notion-x.x.x*` - Upload all `dist/` files to PyPI of a given version
* Make sure to tag the commit you released!

## Useful tips
Mistletoe comes with a helpful tokenizing parser called `ASTRenderer`. This gives us great insight into what `NotionPyRenderer` is going to be seeing while rendering.

Example:
```
import mistletoe
from mistletoe.ast_renderer import ASTRenderer

print(mistletoe.markdown(f"#Owo what's this?", ASTRenderer))
```
outputs
```
{
  "type": "Document",
  "footnotes": {},
  "children": [
    {
      "type": "Paragraph",
      "children": [
        {
          "type": "RawText",
          "content": "#Owo what's this?"
        }
      ]
    }
  ]
}
```