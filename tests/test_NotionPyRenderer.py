'''
Tests NotionPyRenderer parsing
'''
import re
import mistletoe
import notion
from md2notion.NotionPyRenderer import NotionPyRenderer, addHtmlImgTagExtension, addLatexExtension

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

def test_list2():
    '''it should render a GFM list item'''
    #arrange/act
    output = mistletoe.markdown(\
"""
* [] Really
* [ ] big
* [x] uwu
""", NotionPyRenderer)

    #assert
    assert len(output) == 3
    assert isinstance(output[0], dict)
    assert output[0]['type'] == notion.block.BulletedListBlock
    assert output[0]['title'] == '[] Really'
    assert isinstance(output[1], dict)
    assert output[1]['type'] == notion.block.TodoBlock
    assert output[1]['title'] == 'big'
    assert output[1]['checked'] == False
    assert isinstance(output[2], dict)
    assert output[2]['type'] == notion.block.TodoBlock
    assert output[2]['title'] == 'uwu'
    assert output[2]['checked'] == True

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

def test_imageInHtml():
    '''it should render an image that is mentioned in the html <img> tag'''
    #arrange/act
    output = mistletoe.markdown("head<img src=\"https://via.placeholder.com/500\" />tail",
        addHtmlImgTagExtension(NotionPyRenderer))

    #assert
    assert len(output) == 2
    assert isinstance(output[0], dict)
    assert output[0]['type'] == notion.block.TextBlock
    assert output[0]['title'] == "headtail" #Should extract the image
    assert isinstance(output[1], dict) #The ImageBlock can't be inline with anything else so it comes out
    assert output[1]['type'] == notion.block.ImageBlock
    assert output[1]['caption'] is None

def test_imageInHtmlBlock():
    '''it should render an image that is mentioned in the html block'''
    output = mistletoe.markdown(\
"""
<div><img src="https://via.placeholder.com/500" alt="ImCaption"/>text in div</div>

tail
""", addHtmlImgTagExtension(NotionPyRenderer))

    #assert
    assert len(output) == 3
    assert isinstance(output[0], dict)
    assert output[0]['type'] == notion.block.TextBlock
    assert output[0]['title'] == "<div>text in div</div>" #Should extract the image
    assert isinstance(output[1], dict)
    assert output[1]['type'] == notion.block.ImageBlock
    assert output[1]['caption'] == "ImCaption"
    assert isinstance(output[2], dict)
    assert output[2]['type'] == notion.block.TextBlock
    assert output[2]['title'] == "tail"

def test_latex_inline():
    output = mistletoe.markdown(r"""
# Test for latex blocks
Text before $f(x) = \sigma(w \cdot x + b)$ Text after
""", addLatexExtension(NotionPyRenderer))

    assert output[1] is not None
    assert output[1]['type'] == notion.block.TextBlock
    assert output[1]['title'] == r'Text before $$f(x) = \sigma(w \cdot x + b)$$ Text after'

def test_latex_inline_with_underscores():
    '''it should render a latex block with underscores in it properly'''
    output = mistletoe.markdown(r'Text before $X^T=(X_1, X_2, \ldots, X_p)$ Text after', addLatexExtension(NotionPyRenderer))

    assert len(output) == 1
    output = output[0]
    assert output is not None
    assert output['type'] == notion.block.TextBlock
    assert output['title'] == r'Text before $$X^T=(X_1, X_2, \ldots, X_p)$$ Text after'

def test_latex_block():
    output = mistletoe.markdown(r"""
# Test for latex blocks
Text before

$$
f(x) = \sigma(w \cdot x + b)
$$

Text after
""", addLatexExtension(NotionPyRenderer))

    assert output[2] is not None
    assert output[2]['type'] == notion.block.EquationBlock
    assert output[2]['title_plaintext'] == 'f(x) = \\\\sigma(w \\\\cdot x + b)\n'

def test_latex_block_with_underscores():
    '''it should render a latex block with underscores in it properly'''
    output = mistletoe.markdown(r"""
$$
\hat{Y} = \hat{\beta}_0 + \sum_{j=1}^p X_j \hat{\beta}_j
$$""", addLatexExtension(NotionPyRenderer))

    assert len(output) == 1
    output = output[0]
    assert output is not None
    assert output['type'] == notion.block.EquationBlock
    assert output['title_plaintext'] == '\\\\hat{Y} = \\\\hat{\\\\beta}_0 + \\\\sum_{j=1}^p X_j \\\\hat{\\\\beta}_j\n'

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

def test_code_block_with_language():
    '''it should render a fenced code block with explicit language'''
    #arrange/act
    raw =\
"""\
```python
def get_favorite_fruit():
    return Watermelon
```"""
    expected = "def get_favorite_fruit():\n    return Watermelon\n"
    output = mistletoe.markdown(raw, NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.CodeBlock
    assert output['title_plaintext'] == expected
    assert output['language'] == 'Python'

def test_code_block_without_language():
    '''it should render a fenced code block with no language specified'''
    #arrange/act
    raw =\
"""\
```
(f_ my_made_up_language a b)!
```"""
    expected = "(f_ my_made_up_language a b)!\n"
    output = mistletoe.markdown(raw, NotionPyRenderer)

    #assert
    assert len(output) == 1
    output = output[0]
    assert isinstance(output, dict)
    assert output['type'] == notion.block.CodeBlock
    assert output['title_plaintext'] == expected
    assert output['language'] == "Plain Text"

def test_big_file():
    '''it should be able to render a full Markdown file'''
    #arrange/act
    #TODO: For now we just test that this doesn't file, not that it's correct
    mistletoe.markdown(open("tests/COMPREHENSIVE_TEST.md", "r", encoding="utf-8").read(), NotionPyRenderer)
