'''
Tests NotionPyRenderer parsing
'''
import re
import notion
from io import IOBase
from md2notion.upload import filesFromPathsUrls


def test_filesFromPathUrl_with_file():
    '''it can get a file name, path, and file object from a file'''
    #arrange/act
    filePath, fileName, file = next(filesFromPathsUrls(['tests/TEST.md']))

    #assert
    assert fileName == 'TEST.md'
    assert filePath == 'tests/TEST.md'
    assert isinstance(file, IOBase)

def test_filesFromPathUrl_with_glob():
    '''it can get a file name, path, and file object from a file'''
    #arrange/act
    tuples = list(filesFromPathsUrls(['tests/TES*.md']))

    #assert
    assert len(tuples) == 1

def test_filesFromPathUrl_with_url():
    '''it can get a file name, path, and file object from a file'''
    #arrange/act
    filePath, fileName, file = next(filesFromPathsUrls(['https://raw.githubusercontent.com/Cobertos/md2notion/master/README.md']))

    #assert
    assert fileName == 'README.md'
    assert filePath == 'https://raw.githubusercontent.com/Cobertos/md2notion/master/README.md'
    assert isinstance(file, IOBase)
