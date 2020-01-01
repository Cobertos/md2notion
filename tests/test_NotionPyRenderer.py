'''
Tests NotionPyRenderer parsing
'''
import pytest
import re
import mistletoe
import notion
from md2notion.NotionPyRenderer import NotionPyRenderer


def test_header(capsys, headerLevel):
    '''it renders a range of headers, warns if it cant render properly'''
    #arrange/act
    output = mistletoe.markdown(f"{'#'*headerLevel} Owo what's this?", NotionPyRenderer)
    output = output[0]
    captured = capsys.readouterr()

    #assert
    assert isinstance(output, dict)
    if headerLevel > 3: #Should print error
        assert re.search(r"not support", captured.out, re.I) #Should print out warning
    if headerLevel == 1:
        assert output['type'] == notion.block.HeaderBlock
    elif headerLevel == 2:
        assert output['type'] == notion.block.SubheaderBlock
    else:
        assert output['type'] == notion.block.SubsubheaderBlock
    assert output['title'] == "Owo what's this?"

def test_list():
    '''it should render a normal list'''
    #arrange/act
    output = mistletoe.markdown("* asdf", NotionPyRenderer)
    output = output[0]

    #assert
    assert isinstance(output, dict)
    assert output['type'] == notion.block.BulletedListBlock
    assert output['title'] == 'asdf'

def test_list_numbered():
    '''it should render a numbered list if given one'''
    #arrange/act
    output = mistletoe.markdown("1. asdf", NotionPyRenderer)
    output = output[0]

    #assert
    assert isinstance(output, dict)
    assert output['type'] == notion.block.NumberedListBlock
    assert output['title'] == 'asdf'

def test_quote():
    '''it should render a numbered list if given one'''
    #arrange/act
    output = mistletoe.markdown("> Quoth thee 'Mr. Obama... Hewwo? MR OBAMA??'", NotionPyRenderer)
    output = output[0]

    #assert
    assert isinstance(output, dict)
    assert output['type'] == notion.block.QuoteBlock
    assert output['title'] == "Quoth thee 'Mr. Obama... Hewwo? MR OBAMA??'"

def test_imageInLink(capsys):
    '''it should succeed but print error when encountering image in link'''
    #arrange/act
    output = mistletoe.markdown("[![](https://via.placeholder.com/500)](https://cobertos.com)", NotionPyRenderer)
    output = output[0]
    captured = capsys.readouterr()

    #assert
    assert isinstance(output, dict) #Should be a TextBlock, but the image will fail
    assert re.search(r"not support", captured.out, re.I) #Should print out warning
    assert output['type'] == notion.block.TextBlock

def test_table():
    '''it should render a table'''
    #arrange/act
    output = mistletoe.markdown(\
"""
|  Awoo   |  Awooo  |  Awoooo |
|---------|---------|---------|
| Test100 | Test200 | Test300 |
|         | Test400 |         |
""", NotionPyRenderer)
    output = output[0]

    #assert
    assert isinstance(output, dict)
    assert output['type'] == notion.block.CollectionViewBlock

    assert isinstance(output['schema'], dict)
    assert len(output['schema']) == 3 #3 properties
    assert list(output['schema'].keys())[2] == 'title' #Last one is 'title'
    assert list(output['schema'].values())[0] == {
            'type': 'text',
            'name': 'Awoo'
        }
    assert list(output['schema'].values())[1] == {
            'type': 'text',
            'name': 'Awooo'
        }
    assert list(output['schema'].values())[2] == {
            'type': 'title',
            'name': 'Awoooo'
        }

    assert isinstance(output['rows'], list)
    assert len(output['rows']) == 2 #2 rows
    assert output['rows'][0] == ['Test100', 'Test200', 'Test300']
    assert output['rows'][1] == ['', 'Test400', '']

def test_nested_list():
    '''it should render nested lists'''
    #arrange/act
    output = mistletoe.markdown(\
"""
* Awoo
    * Hewwo
""", NotionPyRenderer)
    output = output[0]

    #assert
    assert isinstance(output, dict)
    assert output['type'] == notion.block.BulletedListBlock
    assert output['title'] == 'Awoo'

    assert len(output['children']) == 1
    outputChild = output['children'][0]
    assert isinstance(outputChild, dict)
    assert outputChild['type'] == notion.block.BulletedListBlock
    assert outputChild['title'] == 'Hewwo'
