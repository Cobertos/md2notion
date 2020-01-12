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
    captured = capsys.readouterr()

    #assert
    assert len(output) == 1
    output = output[0]
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

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.BulletedListBlock
    assert output['title'] == 'asdf'

def test_list_numbered():
    '''it should render a numbered list if given one'''
    #arrange/act
    output = mistletoe.markdown("1. asdf", NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.NumberedListBlock
    assert output['title'] == 'asdf'

def test_quote():
    '''it should render a numbered list if given one'''
    #arrange/act
    output = mistletoe.markdown("> Quoth thee 'Mr. Obama... Hewwo? MR OBAMA??'", NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.QuoteBlock
    assert output['title'] == "Quoth thee 'Mr. Obama... Hewwo? MR OBAMA??'"

def test_image():
    '''it should render an image'''
    #arrange/act
    output = mistletoe.markdown("![](https://via.placeholder.com/500)", NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.ImageBlock

def test_imageInLink():
    '''it should render an image in a link, but separately because notion doesnt support that'''
    #arrange/act
    output = mistletoe.markdown("[![](https://via.placeholder.com/500)](https://cobertos.com)", NotionPyRenderer)

    #assert
    assert len(output) == 2
    assert isinstance(output[0], dict)
    assert output[0]['type'] == notion.block.TextBlock
    assert output[0]['title'] == "[](https://cobertos.com)" #Should extract the image
    assert isinstance(output[1], dict) #The ImageBlock can't be in a link in Notion, so we get it outside
    assert output[1]['type'] == notion.block.ImageBlock

def test_imageBlockText():
    '''it should render an image in bold text'''
    #arrange/act
    output = mistletoe.markdown("**texttext![](https://via.placeholder.com/500)texttext**", NotionPyRenderer)

    #assert
    assert len(output) == 2
    assert isinstance(output[0], dict)
    assert output[0]['type'] == notion.block.TextBlock
    assert output[0]['title'] == "**texttexttexttext**" #Should extract the image
    assert isinstance(output[1], dict) #The ImageBlock can't be inline with anything else so it comes out
    assert output[1]['type'] == notion.block.ImageBlock

def test_escapeSequence():
    '''it should render out an escape sequence'''
    #arrange/act
    output = mistletoe.markdown("\\066", NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert output['type'] == notion.block.TextBlock
    assert output['title'] == "\\066"

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

    #assert
    assert len(output) == 1
    output = output[0]
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

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.BulletedListBlock
    assert output['title'] == 'Awoo'

    assert len(output['children']) == 1
    outputChild = output['children'][0]
    assert isinstance(outputChild, dict)
    assert outputChild['type'] == notion.block.BulletedListBlock
    assert outputChild['title'] == 'Hewwo'
