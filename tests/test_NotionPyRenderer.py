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
    assert isinstance(output, object)
    if headerLevel > 3: #Should print error
        assert re.search(r"not support", captured.out, re.I) #Should print out warning
    if headerLevel == 1:
        assert output['type'] == notion.block.HeaderBlock
    elif headerLevel == 2:
        assert output['type'] == notion.block.SubheaderBlock
    else:
        assert output['type'] == notion.block.SubsubheaderBlock
    assert output['title'] == "Owo what's this?"

def test_imageInLink(capsys):
    '''it should succeed but print error when encountering image in link'''
    #arrange/act
    output = mistletoe.markdown("[![](https://via.placeholder.com/500)](https://cobertos.com)", NotionPyRenderer)
    output = output[0]
    captured = capsys.readouterr()

    #assert
    assert isinstance(output, object) #Should be a TextBlock, but the image will fail
    assert re.search(r"not support", captured.out, re.I) #Should print out warning
    assert output['type'] == notion.block.TextBlock
