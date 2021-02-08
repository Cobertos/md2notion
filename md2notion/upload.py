import io
import requests
import os.path
import glob
import argparse
import sys
import re
from pathlib import Path
from urllib.parse import unquote, urlparse, ParseResult
import mistletoe
from notion.block import EmbedOrUploadBlock, CollectionViewBlock, PageBlock
from notion.client import NotionClient
from .NotionPyRenderer import NotionPyRenderer, addHtmlImgTagExtension, addLatexExtension


def relativePathForMarkdownUrl(url, mdFilePath):
    """
    Markdown images commonly referenence local files the URL portion but the URLs
    might not be valid file paths.
    Figure out the first valid file path by trying different permutations of the
    url parts
    @param {str} The url to parse
    @param {str} mdFilePath The path to the file we're parsing, for relative paths
    @returns {None|Path} None of the url is not a valid local file path or is
    an external URL (http/https). Path path if it's valid
    """

    if '://' in url:
        # Try stripping file:// and decoding
        urlNoScheme = url[url.index('://')+3:]
        paths = [ Path(mdFilePath).parent / Path(unquote(urlNoScheme)) ]
    else:
        # Try both the normal file, then the url decoded file
        paths = [
            Path(mdFilePath).parent / Path(url),
            Path(mdFilePath).parent / Path(unquote(url))
        ]

    for path in paths:
        # Test for validity (the try/except) and existance
        try:
            if path.exists():
                return path
            else:
                print(f"File not found '{path}'")
        except OSError as e:
            pass
    return None

def uploadBlock(blockDescriptor, blockParent, mdFilePath, imagePathFunc=None):
    """
    Uploads a single blockDescriptor for NotionPyRenderer as the child of another block
    and does any post processing for Markdown importing
    @param {dict} blockDescriptor A block descriptor, output from NotionPyRenderer
    @param {NotionBlock} blockParent The parent to add it as a child of
    @param {string} mdFilePath The path to the markdown file to find images with
    @param {callable|None) [imagePathFunc=None] See upload()

    @todo Make mdFilePath optional and don't do searching if not provided
    """
    blockClass = blockDescriptor["type"]
    del blockDescriptor["type"]
    if "schema" in blockDescriptor:
        collectionSchema = blockDescriptor["schema"]
        collectionRows = blockDescriptor["rows"]
        del blockDescriptor["schema"]
        del blockDescriptor["rows"]
    blockChildren = None
    if "children" in blockDescriptor:
        blockChildren = blockDescriptor["children"]
        del blockDescriptor["children"]
    newBlock = blockParent.children.add_new(blockClass, **blockDescriptor)
    # Upload images to Notion.so that have local file paths
    # most of the time, this will be a standard ImageBlock; however some markdown
    # generators use the image syntax for general purpose "embedded" files; hence we
    # check for any subclass of EmbedOrUploadBlock (which provides upload_file)
    if issubclass(blockClass, EmbedOrUploadBlock):
        imgRelSrc = blockDescriptor["source"]
        if re.search(r"(?<!file)://", imgRelSrc, re.I):
            return #Don't upload images that are external urls

        if imagePathFunc: #Transform by imagePathFunc insteadif provided
            imgSrc = imagePathFunc(imgRelSrc, mdFilePath)
        else:
            imgSrc = relativePathForMarkdownUrl(imgRelSrc, mdFilePath)
            if not imgSrc:
                print(f"ERROR: Local image '{imgRelSrc}' not found to upload. Skipping...")
                return

        print(f"Uploading file '{imgSrc}'")
        newBlock.upload_file(str(imgSrc))
    elif isinstance(newBlock, CollectionViewBlock):
        #We should have generated a schema and rows for this one
        notionClient = blockParent._client #Hacky internals stuff...
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
            uploadBlock(childBlock, newBlock, mdFilePath, imagePathFunc)


def convert(mdFile, notionPyRendererCls=NotionPyRenderer):
    """
    Converts a mdFile into an array of NotionBlock descriptors
    @param {file|string} mdFile The file handle to a markdown file, or a markdown string
    @param {NotionPyRenderer} notionPyRendererCls Class inheritting from the renderer
    incase you want to render the Markdown => Notion.so differently
    """
    return mistletoe.markdown(mdFile, notionPyRendererCls)

def upload(mdFile, notionPage, imagePathFunc=None, notionPyRendererCls=NotionPyRenderer):
    """
    Uploads a single markdown file at mdFilePath to Notion.so as a child of
    notionPage.
    @param {file} mdFile The file handle to a markdown file
    @param {NotionBlock} notionPage The Notion.so block to add the markdown to
    @param {callable|None) [imagePathFunc=None] Function taking image source and mdFilePath
    to transform the relative image paths by if necessary (useful if your images are stored in weird
    locations relative to your md file. Should return a pathlib.Path
    @param {NotionPyRenderer} notionPyRendererCls Class inheritting from the renderer
    incase you want to render the Markdown => Notion.so differently
    """
    # Convert the Markdown file
    rendered = convert(mdFile, notionPyRendererCls)

    # Upload all the blocks
    for idx, blockDescriptor in enumerate(rendered):
        pct = (idx+1)/len(rendered) * 100
        print(f"\rUploading {blockDescriptor['type'].__name__}, {idx+1}/{len(rendered)} ({pct:.1f}%)", end='')
        uploadBlock(blockDescriptor, notionPage, mdFile.name, imagePathFunc)


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
    parser.add_argument('--html-img', action='store_true', default=False,
                        help="Upload images in HTML <img> tags (disabled by default)")
    parser.add_argument('--latex', action='store_true', default=False,
                        help="Support for latex inline ($..$) and block ($$..$$) equations (disabled by default)")

    args = parser.parse_args(argv)

    notionPyRendererCls = NotionPyRenderer
    if args.html_img:
        notionPyRendererCls = addHtmlImgTagExtension(notionPyRendererCls)
    if args.latex:
        notionPyRendererCls = addLatexExtension(notionPyRendererCls)

    print("Initializing Notion.so client...")
    client = NotionClient(token_v2=args.token_v2)
    print("Getting target PageBlock...")
    page = client.get_block(args.page_url)
    uploadPage = page

    for mdPath, mdFileName, mdFile in filesFromPathsUrls(args.md_path_url):
        if args.mode == 'create' or args.mode == 'clear':
            # Clear any old pages if it's a PageBlock that has the same name
            if args.mode == 'clear':
                for child in [c for c in page.children if isinstance(c, PageBlock) and c.title == mdFileName]:
                    print(f"Removing previous {child.title}...")
                    child.remove()
            # Make the new page in Notion.so
            uploadPage = page.children.add_new(PageBlock, title=mdFileName)
        print(f"Uploading {mdPath} to Notion.so at page {uploadPage.title}...")
        upload(mdFile, uploadPage, None, notionPyRendererCls)


if __name__ == "__main__":
    cli(sys.argv[1:])
