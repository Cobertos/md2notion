import io
import requests
import os.path
import glob
import argparse
import sys
import pprint
import copy
import hashlib

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
    def __init__(self, page_map_cache_filename = 'notion_cache.yml'):
        self.page_map_cache_filename = page_map_cache_filename

        self.image_file_names = {}
        self.page_map = {}
        if os.path.isfile(self.page_map_cache_filename):
            with open(self.page_map_cache_filename, 'r') as fd:
                self.page_map = load(fd.read(), Loader=Loader)

        if not self.page_map:
            self.page_map = {}

    def calc_block_hashes(self, blocks):
        for block in blocks:
            if 'source' in block['block_descriptor']:
                source_filename = block['block_descriptor']['source']
                if source_filename in self.image_file_names:
                    source_filename = self.image_file_names[source_filename]

                if not os.path.isfile(source_filename):
                    if source_filename.find("://") < 0:
                        print('Missing source_filename: %s' % source_filename)
                    continue

                with open(source_filename, 'rb') as sfd:
                    block['block_descriptor']['sha256'] = hashlib.sha256(sfd.read()).hexdigest()

    def calc_hashes(self, page_map):
        for id, page_data in page_map.items():
            self.calc_block_hashes(page_data['blocks'])

    def save_cache(self):
        self.calc_hashes(self.page_map)
        with open(self.page_map_cache_filename,  'w') as fd:
            fd.write(dump(self.page_map, Dumper = Dumper))

    def get_source_hashes(self):
        hashes = {}
        for id, page_data in self.page_map.items():
            for block in page_data['blocks']:
                if 'source' in block['block_descriptor'] and 'sha256' in block['block_descriptor']:
                    source_filename = block['block_descriptor']['source']
                    hashes[source_filename] = block['block_descriptor']['sha256']

        return hashes

    def convert(self, markdown_filename, notion_py_renderer_cls=NotionPyRenderer):
        """
        Converts a markdown_filename into an array of NotionBlock descriptors
        @param {file|string} markdown_filename The file handle to a markdown file, or a markdown string
        @param {NotionPyRenderer} notion_py_renderer_cls Class inheritting from the renderer
        incase you want to render the Markdown => Notion.so differently
        """
        return mistletoe.markdown(markdown_filename, notion_py_renderer_cls)

    def upload_block(self, block_descriptor, block_parent, markdown_filename_path, image_path_function=None):
        """
        Uploads a single block_descriptor for NotionPyRenderer as the child of another block
        and does any post processing for Markdown importing
        @param {dict} block_descriptor A block descriptor, output from NotionPyRenderer
        @param {NotionBlock} block_parent The parent to add it as a child of
        @param {string} markdown_filename_path The path to the markdown file to find images with
        @param {callable|None) [image_path_function=None] See upload()

        @todo Make markdown_filename_path optional and don't do searching if not provided
        """
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

        newBlock = block_parent.children.add_new(blockClass, **block_descriptor)
        # Upload images to Notion.so that have local file paths
        if isinstance(newBlock, ImageBlock):
            imgRelSrc = block_descriptor["source"]
            if '://' in imgRelSrc:
                return #Don't upload images that are external urls

            if image_path_function: #Transform by image_path_function
                imgSrc = image_path_function(imgRelSrc, markdown_filename_path)
            else:
                imgSrc = Path(markdown_filename_path).parent / Path(imgRelSrc)

            if not imgSrc.exists():
                print(f"ERROR: Local image '{imgSrc}' not found to upload. Skipping...")
                return
            print(f"Uploading file '{imgSrc}'")
            self.image_file_names[imgRelSrc] = str(imgSrc)
            newBlock.upload_file(str(imgSrc))
        elif isinstance(newBlock, CollectionViewBlock):
            #We should have generated a schema and rows for this one
            notionClient = block_parent._client #Hacky internals stuff...
            newBlock.collection = notionClient.get_collection(
                #Low-level use of the API
                #TODO: Update when notion-py provides a better interface for this
                notionClient.create_record("collection", parent=newBlock, schema=collectionSchema)
            )
            view = newBlock.views.add_new(view_type="table")
            for row in collectionRows:
                newRow = newBlock.collection.add_row()
                for idx, propName in enumerate(prop["name"] for prop in collectionSchema.values()):
                    # TODO: If rows aren't uploading, check to see if there's special
                    # characters that don't map to propName in notion-py
                    propName = propName.lower() #The actual prop name in notion-py is lowercase
                    propVal = row[idx]
                    setattr(newRow, propName, propVal)
        if blockChildren:
            for childBlock in blockChildren:
                self.upload_block(childBlock, newBlock, markdown_filename_path, image_path_function)

        return newBlock

    def upload_markdown(self, markdown_filename, notion_page, image_path_function = None, notion_py_renderer_cls = NotionPyRenderer):
        """
        Uploads a single markdown file at markdown_filename_path to Notion.so as a child of
        notion_page.
        @param {file} markdown_filename The file handle to a markdown file
        @param {NotionBlock} notion_page The Notion.so block to add the markdown to
        @param {callable|None) [image_path_function=None] Function taking image source and markdown_filename_path
        to transform the relative image paths by if necessary (useful if your images are stored in weird
        locations relative to your md file.
        @param {NotionPyRenderer} notion_py_renderer_cls Class inheritting from the renderer
        incase you want to render the Markdown => Notion.so differently
        """
        # Convert the Markdown file
        rendered = self.convert(markdown_filename, notion_py_renderer_cls)

        hashes = self.get_source_hashes()

        blocks = []
        for idx, block_descriptor in enumerate(rendered):
            blocks.append({'type': block_descriptor['type'].__name__, 'block_descriptor': block_descriptor, 'id': 0})

        """
        self.calc_block_hashes(blocks)

        if notion_page.id in self.page_map:
            orig_blocks = self.page_map[notion_page.id]['blocks']
            pprint.pprint(blocks)
            pprint.pprint(orig_blocks)

            new_blocks = []
            for idx, block_descriptor in enumerate(rendered):
                print(f"\rUpdating {block_descriptor['type'].__name__}")
                if block_descriptor[idx] != orig_blocks[idx]['block_descriptor']:
                    newBlock = self.upload_block(copy.deepcopy(block_descriptor), notion_page, markdown_filename.name, image_path_function)
                    #blocks.append({'type': block_descriptor['type'].__name__, 'block_descriptor': block_descriptor, 'id': newBlock.id})
        """

        # Upload all the blocks
        blocks = []
        for idx, block_descriptor in enumerate(rendered):
            pct = (idx+1)/len(rendered) * 100
            print(f"\rUploading {block_descriptor['type'].__name__}, {idx+1}/{len(rendered)} ({pct:.1f}%)")

            block = {'type': block_descriptor['type'].__name__, 'block_descriptor': block_descriptor}
            newBlock = self.upload_block(copy.deepcopy(block_descriptor), notion_page, markdown_filename.name, image_path_function)

            if newBlock:
                block['id'] = newBlock.id

            blocks.append(block)

        self.page_map[notion_page.id] = {'blocks': blocks}

    def upload(self,  page, filename, title = ''):
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