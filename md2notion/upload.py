import io
import requests
import os.path
import glob
import argparse
import sys
import copy
import hashlib
import traceback
import pprint

from pathlib import Path
import mistletoe
from notion.block import ImageBlock, CollectionViewBlock, PageBlock, FileBlock
from notion.client import NotionClient
from .NotionPyRenderer import NotionPyRenderer

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class PageSyncer:
    def __init__(self):
        self.image_file_names = {}
        self.block_map = {}

    def calc_block_hash(self, block):
        if 'source' in block:
            source_filename = block['source']
            if source_filename in self.image_file_names:
                source_filename = self.image_file_names[source_filename]
            if source_filename.find("://") < 0 and os.path.isfile(source_filename):
                with open(source_filename, 'rb') as sfd:
                    return hashlib.sha256(sfd.read()).hexdigest()
        elif 'title' in block:
            return hashlib.sha256(block['title'].encode('utf-8')).hexdigest()
        return ''

    def convert(self, markdown_filename, notion_py_renderer_cls=NotionPyRenderer):
        return mistletoe.markdown(markdown_filename, notion_py_renderer_cls)

    def upload_block(self, block_descriptor, block_parent, markdown_filename_path, image_path_function=None, use_add_rows = False):
        blockClass = block_descriptor["type"]
        del block_descriptor["type"]
        if "schema" in block_descriptor:
            collectionSchema = block_descriptor["schema"]
            collectionRows = block_descriptor["rows"]
            del block_descriptor["schema"]
            del block_descriptor["rows"]
        blockChildren = None
        if "children" in block_descriptor:
            blockChildren = block_descriptor["children"]
            del block_descriptor["children"]

        new_block = block_parent.children.add_new(blockClass, **block_descriptor)
        if isinstance(new_block, ImageBlock):
            imgRelSrc = block_descriptor["source"]
            if '://' in imgRelSrc:
                return

            if image_path_function: #Transform by image_path_function
                imgSrc = image_path_function(imgRelSrc, markdown_filename_path)
            else:
                imgSrc = Path(markdown_filename_path).parent / Path(imgRelSrc)

            if not imgSrc.exists():
                print(f"ERROR: Local image '{imgSrc}' not found to upload. Skipping...")
                return
            print(f"Uploading file '{imgSrc}'")
            self.image_file_names[imgRelSrc] = str(imgSrc)
            new_block.upload_file(str(imgSrc))

        elif isinstance(new_block, CollectionViewBlock):
            notionClient = block_parent._client

            print('='*80)
            pprint.pprint(collectionSchema)

            reversedCollectionSchema = {}
            for k, v in collectionSchema.items():
                reversedCollectionSchema[k] = v

            pprint.pprint(reversedCollectionSchema)

            new_block.collection = notionClient.get_collection(notionClient.create_record("collection", parent=new_block, schema=reversedCollectionSchema))
            view = new_block.views.add_new(view_type = "table")


            view = new_block.views.add_new(view_type = "table")

            if use_add_rows:
                row_data = []
                for row in collectionRows:
                    kv_pair = {}
                    for idx, propName in enumerate(prop["name"] for prop in collectionSchema.values()):
                        propName = propName.lower()
                        propVal = row[idx]
                        kv_pair[propName] = propVal
                    row_data.append(kv_pair)
                newRow = new_block.collection.add_rows(row_data)
            else:
                for row in collectionRows:
                    kv_pair = {}
                    for idx, propName in enumerate(prop["name"] for prop in collectionSchema.values()):
                        propName = propName.lower()
                        propVal = row[idx]
                        kv_pair[propName] = propVal
                    newRow = new_block.collection.add_row(**kv_pair)

        if blockChildren:
            for childBlock in blockChildren:
                self.upload_block(childBlock, new_block, markdown_filename_path, image_path_function)

        return new_block

    def upload_markdown(self, markdown_filename, notion_page, image_path_function = None, notion_py_renderer_cls = NotionPyRenderer):
        rendered = self.convert(markdown_filename, notion_py_renderer_cls)
        blocks = []
        for idx, block_descriptor in enumerate(rendered):
            blocks.append({'type': block_descriptor['type'].__name__, 'block_descriptor': block_descriptor, 'id': 0})
        blocks = []
        for idx, block_descriptor in enumerate(rendered):
            pct = (idx+1)/len(rendered) * 100
            print(f"\rUploading {block_descriptor['type'].__name__}, {idx+1}/{len(rendered)} ({pct:.1f}%)")
            new_block = self.upload_block(copy.deepcopy(block_descriptor), notion_page, markdown_filename.name, image_path_function)
            if new_block:
                self.block_map[new_block.id] = {}
                for k, v in block_descriptor.items():
                    self.block_map[new_block.id][k] = v

                self.block_map[new_block.id]['type'] = str(block_descriptor['type']._type)
                self.block_map[new_block.id]['sha256'] = self.calc_block_hash(block_descriptor)
                self.block_map[new_block.id]['markdown_filename'] = markdown_filename.name

    def upload(self, page, filename, title = ''):
        new_block = page.children.add_new(FileBlock, title = os.path.basename(filename))
        new_block.upload_file(filename)

def filesFromPathsUrls(paths):
    """
    Takes paths or URLs and yields file (path, fileName, file) tuples for 
    them
    """
    for path in paths:
        if '://' in path:
            r = requests.get(path)
            if not r.status_code < 300: #TODO: Make this better..., should only accept success
                raise RuntimeError(f'Could not get file {path}, HTTP {r.status_code}')
            fileName = path.split('?')[0]
            fileName = fileName.split('/')[-1]
            fileLike = io.StringIO(r.text)
            fileLike.name = path
            yield (path, fileName, fileLike)
        else:
            globPaths = glob.glob(path, recursive=True)
            if not globPaths:
                raise RuntimeError(f'No file found for glob {path}')
            for path in globPaths:
                with open(path, "r", encoding="utf-8") as file:
                    yield (path, os.path.basename(path), file)

def cli(argv):
    parser = argparse.ArgumentParser(description='Uploads Markdown files to Notion.so')
    parser.add_argument('token_v2', type=str,
                        help='the token for your Notion.so session')
    parser.add_argument('page_url', type=str,
                        help='the url of the Notion.so page you want to upload your Markdown files to')
    parser.add_argument('md_path_url', type=str, nargs='+',
                        help='A path, glob, or url to the Markdown file you want to upload')
    parser.add_argument('--create', action='store_const', dest='mode', const='create',
                        help='Create a new child page (default)')
    parser.add_argument('--append', action='store_const', dest='mode', const='append',
                        help='Append to page instead of creating a child page')
    parser.add_argument('--clear-previous', action='store_const', dest='mode', const='clear',
                        help='Clear a previous child page with the same name if it exists')
    parser.set_defaults(mode='create')

    args = parser.parse_args(argv)

    print("Initializing Notion.so client...")
    client = NotionClient(token_v2=args.token_v2)
    print("Getting target PageBlock...")
    page = client.get_block(args.page_url)
    uploadPage = page

    for mdPath, markdown_filenameName, markdown_filename in filesFromPathsUrls(args.md_path_url):
        if args.mode == 'create' or args.mode == 'clear':
            # Clear any old pages if it's a PageBlock that has the same name
            if args.mode == 'clear':
                for child in [c for c in page.children if isinstance(c, PageBlock) and c.title == markdown_filenameName]:
                    print(f"Removing previous {child.title}...")
                    child.remove()
            # Make the new page in Notion.so
            uploadPage = page.children.add_new(PageBlock, title=markdown_filenameName)
        print(f"Uploading {mdPath} to Notion.so at page {uploadPage.title}...")
        upload(markdown_filename, uploadPage)

if __name__ == "__main__":
    cli(sys.argv[1:])