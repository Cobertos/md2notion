'''
Tests NotionPyRenderer parsing
'''
import pytest
from pathlib import Path
import re
import notion
import sys
from io import IOBase
from md2notion.upload import filesFromPathsUrls, uploadBlock, cli
from notion.block import TextBlock, ImageBlock, CollectionViewBlock, PageBlock
from unittest.mock import Mock, patch, call

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

def test_uploadBlock():
    '''uploads a simple block to Notion using add_new'''
    #arrange
    blockDescriptor = {
        'type': TextBlock,
        'title': 'This is a test of the test system'
    }
    notionBlock = Mock()
    notionBlock.children.add_new = Mock()

    #act
    uploadBlock(blockDescriptor, notionBlock, '')

    #assert
    notionBlock.children.add_new.assert_called_with(TextBlock, title='This is a test of the test system')

def test_uploadBlock_image():
    '''uploads an external image block to Notion without uploading'''
    #arrange
    blockDescriptor = {
        'type': ImageBlock,
        'title': 'test',
        'source': 'https://example.com'
    }
    notionBlock = Mock()
    newBlock = Mock(spec=blockDescriptor['type'])
    notionBlock.children.add_new = Mock(return_value=newBlock)

    #act
    uploadBlock(blockDescriptor, notionBlock, '')

    #assert
    notionBlock.children.add_new.assert_called_with(ImageBlock, title='test', source='https://example.com')
    newBlock.upload_file.assert_not_called()

def test_uploadBlock_image_local():
    '''uploads an Image block with local image to Notion'''
    #arrange
    blockDescriptor = {
        'type': ImageBlock,
        'title': 'test',
        'source': 'TEST_IMAGE.png'
    }
    notionBlock = Mock()
    notionBlock.children.add_new.return_value = newBlock = Mock(spec=blockDescriptor['type'])

    #act
    uploadBlock(blockDescriptor, notionBlock, 'tests/DUMMY.md')

    #assert
    notionBlock.children.add_new.assert_called_with(ImageBlock, title='test', source='TEST_IMAGE.png')
    newBlock.upload_file.assert_called_with(str(Path('tests/TEST_IMAGE.png')))

def test_uploadBlock_collection():
    #arrange
    blockDescriptor = {
        'type': CollectionViewBlock,
        'schema': {
            'J=}2': {
                'type': 'text',
                'name': 'Awoooo'
            },
            'J=}x': {
                'type': 'text',
                'name': 'Awooo'
            },
            'title': {
                'type': 'text',
                'name': 'Awoo'
            }
        },
        'rows': [
            ['Test100', 'Test200', 'Test300'],
            ['', 'Test400', '']
        ]
    }
    schema = blockDescriptor['schema']
    rows = blockDescriptor['rows']
    notionBlock = Mock()
    newBlock = Mock(spec=blockDescriptor['type'])
    notionBlock.children.add_new = Mock(return_value=newBlock)

    collection = Mock()
    notionBlock._client.create_record = Mock(return_value=collection)
    notionBlock._client.get_collection = Mock(return_value=collection)

    #act
    uploadBlock(blockDescriptor, notionBlock, '')

    #assert
    notionBlock.children.add_new.assert_called_with(CollectionViewBlock)
    notionBlock._client.create_record.assert_called_with("collection", parent=newBlock, schema=schema)
    notionBlock._client.get_collection.assert_called_with(collection)
    #TODO: This is incomplete...

def MockClient():
    #No-op, seal doesn't exist in Python 3.6
    if sys.version_info >= (3,7,0):
        from unittest.mock import seal
    else:
        seal = lambda x: x
    notionClient = Mock()
    notionClient.return_value = notionClient
    getBlock = Mock(spec=PageBlock)
    class MockNodeList(list):
        def add_new(self, t, title=None):
            m = Mock(spec=t)
            def remove():
                self.remove(m)
                return None
            m.remove = Mock(return_value=None, side_effect=remove)
            m.title = title
            seal(m)
            self.append(m)
            return m
    getBlock.children = MockNodeList()
    getBlock.title = Mock(return_value="")
    notionClient.get_block = Mock(return_value=getBlock)
    seal(getBlock)
    seal(notionClient)
    return notionClient

@patch('notion.client.NotionClient', new_callable=MockClient)
def test_cli_no_arguments(mockClient):
    '''should error when nothing is passed'''
    #act/assert
    with pytest.raises(SystemExit):
        cli([])

@patch('md2notion.upload.upload')
@patch('notion.client.NotionClient', new_callable=MockClient)
def test_cli_create_single_page(mockClient, upload):
    '''should create a single page'''
    #act
    cli(['token_v2', 'page_url', 'tests/TEST.md'])

    #assert
    #Should've been called with a file and the passed block
    args0, kwargs0 = upload.call_args
    assert isinstance(args0[0], IOBase)
    assert args0[0].name == 'tests/TEST.md'
    assert args0[1] == mockClient.get_block.return_value.children[0]
    assert args0[1].title == 'TEST.md'

@patch('md2notion.upload.upload')
@patch('notion.client.NotionClient', new_callable=MockClient)
def test_cli_create_multiple_pages(mockClient, upload):
    '''should create multiple pages'''
    #act
    cli(['token_v2', 'page_url', 'tests/TEST.md', 'tests/COMPREHENSIVE_TEST.md'])
    args0, kwargs0 = upload.call_args_list[0]
    assert isinstance(args0[0], IOBase)
    assert args0[0].name == 'tests/TEST.md'
    assert args0[1] == mockClient.get_block.return_value.children[0]
    assert args0[1].title == 'TEST.md'
    args1, kwargs1 = upload.call_args_list[1]
    assert isinstance(args1[0], IOBase)
    assert args1[0].name == 'tests/COMPREHENSIVE_TEST.md'
    assert args1[1] == mockClient.get_block.return_value.children[1]
    assert args1[1].title == 'COMPREHENSIVE_TEST.md'

@patch('md2notion.upload.upload')
@patch('notion.client.NotionClient', new_callable=MockClient)
def test_cli_append(mockClient, upload):
    '''should append when using that flag'''
    #act
    cli(['token_v2', 'page_url', 'tests/TEST.md', '--append'])

    #assert
    #Should've been called with a file and the passed block
    args0, kwargs0 = upload.call_args
    assert isinstance(args0[0], IOBase)
    assert args0[0].name == 'tests/TEST.md'
    assert args0[1] == mockClient.get_block.return_value

@patch('md2notion.upload.upload')
@patch('notion.client.NotionClient', new_callable=MockClient)
def test_cli_clear_previous(mockClient, upload):
    '''should clear previously title pages with the same name when passed that flag'''
    #arrange
    testNoBlock = mockClient.get_block().children.add_new(PageBlock, title='NO_TEST.md')
    testBlock = mockClient.get_block().children.add_new(PageBlock, title='TEST.md')

    #act
    cli(['token_v2', 'page_url', 'tests/TEST.md', '--clear-previous'])

    #assert
    testNoBlock.remove.assert_not_called()
    testBlock.remove.assert_called_with()
    args0, kwargs0 = upload.call_args
    assert isinstance(args0[0], IOBase)
    assert args0[0].name == 'tests/TEST.md'
    assert args0[1] == mockClient.get_block.return_value.children[1]
    assert args0[1].title == 'TEST.md'