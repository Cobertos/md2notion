'''
Tests NotionPyRenderer parsing
'''
from pathlib import Path
import re
import notion
from io import IOBase
from md2notion.upload import filesFromPathsUrls, uploadBlock
from notion.block import TextBlock, ImageBlock, CollectionViewBlock
from unittest.mock import Mock


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
    newBlock = Mock(spec=blockDescriptor['type'])
    notionBlock.children.add_new = Mock(return_value=newBlock)

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