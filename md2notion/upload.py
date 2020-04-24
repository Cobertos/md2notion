from pathlib import Path
import mistletoe
from notion.block import ImageBlock, CollectionViewBlock
from .NotionPyRenderer import NotionPyRenderer

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
    if isinstance(newBlock, ImageBlock):
        imgRelSrc = blockDescriptor["source"]
        if '://' in imgRelSrc:
            return #Don't upload images that are external urls

        if imagePathFunc: #Transform by imagePathFunc
            imgSrc = imagePathFunc(imgRelSrc, mdFilePath)
        else:
            imgSrc = Path(mdFilePath).parent / Path(imgRelSrc)

        if not imgSrc.exists():
            print(f"ERROR: Local image '{imgSrc}' not found to upload. Skipping...")
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
    locations relative to your md file.
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
    import io
    import requests
    import os.path
    import glob
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
            for path in glob.glob(path, recursive=True):
                with open(path, "r", encoding="utf-8") as file:
                    yield (path, os.path.basename(path), file)

if __name__ == "__main__":
    import argparse
    import sys
    from notion.block import PageBlock
    from notion.client import NotionClient

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
    parser.add_argument('--update', action='store_const', dest='mode', const='update',
                        help='Overwrites page instead of creating a child page')
    parser.set_defaults(mode='create')

    args = parser.parse_args(sys.argv[1:])

    print("Initializing Notion.so client...")
    client = NotionClient(token_v2=args.token_v2)
    print("Getting target PageBlock...")
    parentPage = client.get_block(args.page_url)

    for mdPath, mdFileName, mdFile in filesFromPathsUrls(args.md_path_url):
        if args.mode == 'create':
            # Make a new page in Notion.so
            pageName = mdFileName[:40]
            page = parentPage.children.add_new(PageBlock, title=pageName)
        else:
            # Modify the existing page
            pageName = args.page_url
            page = parentPage
        if args.mode == 'update':
            # First soft-remove all child nodes
            nchildren = len(page.children)
            for idx, child in enumerate(page.children):
                pct = (idx+1)/nchildren * 100
                print(f"\rSoft-removing existing children, {idx+1}/{nchildren} ({pct:.1f}%)", end='')
                child.remove()
            print()
        print(f"Uploading {mdPath} to Notion.so at page {pageName}...")
        upload(mdFile, page)
