# Contributing

Here's how to run all the development stuff

#### Development Environment
* `pyenv global 3.6.8-amd64`
* `python -m venv venv`
* `venv\scripts\activate.bat` or `venv/scripts/activate` for Linux
* `pip install -r requirements-dev.txt` (Installs `pytest`, `twine`, `setuptools`, `wheel`)

#### Testing
* TODO: CURRENTLY NOT APPLICABLE TO THIS REPO
* `pytest -v -s` in the root directory

#### Releasing
Refer to [the python docs on packaging for clarification](https://packaging.python.org/tutorials/packaging-projects/).
* Make sure you've updated `setup.py`
* `python setup.py sdist bdist_wheel` - Create a source distribution and a binary wheel distribution into `dist/`
* `twine upload dist/md2notion-x.x.x*` - Upload all `dist/` files to PyPI of a given version
* Make sure to tag the commit you released!